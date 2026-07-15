# =============================================================================
# app/routers/recommendations.py
# Smart Restaurant DSS — AI Recommendations Router
# =============================================================================
#
# WHAT THIS FILE DOES:
# --------------------
# Defines all AI-powered endpoints for the Smart Restaurant DSS.
# Plugs directly into the existing main.py via:
#   app.include_router(recommendations.router)
#
# Existing endpoints (upgraded with ML model):
#   GET /forecast/menu-items   → ML waste-based prep forecast per dish per day
#   GET /recommendations       → ML dish recommendations with contextual reasons
#
# New AI endpoints (added under /ai/ prefix):
#   GET  /ai/health            → confirms ML model is loaded and ready
#   GET  /ai/options           → returns valid dropdown values for the frontend
#   POST /ai/predict           → single dish waste prediction + recommendation
#   POST /ai/predict/batch     → all dishes at once, sorted by urgency
#
# IMPORTANT FOR BACKEND DEVELOPER:
# ---------------------------------
# 1. Place inference_pipeline.py in the project root (same level as main.py)
# 2. Place rf_waste_model.pkl and label_encoders.pkl in the project root
# 3. Add to requirements.txt: scikit-learn, joblib, pandas, numpy, gdown
# 4. No changes needed to main.py — this file is a drop-in replacement
# =============================================================================

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
import traceback

from app.schemas import ForecastPoint, Recommendation
from app.services.recommendation_service import recommendation_service

# Try importing ML pipeline — graceful degradation if unavailable
try:
    from inference_pipeline import (
        predict_and_recommend,
        predict_all_dishes,
        label_encoders,
        HIGH_WASTE_THRESHOLD,
        LOW_WASTE_THRESHOLD,
        ADJUSTMENT_PERCENTAGE,
    )
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False
    ML_ERROR     = str(e)


# -----------------------------------------------------------------------------
# ROUTER SETUP
# Two routers:
#   router     → existing endpoints (no prefix, keeps /forecast and /recommendations)
#   ai_router  → new ML endpoints under /ai/
# Both are exported and included in main.py
# -----------------------------------------------------------------------------

router    = APIRouter(tags=["AI Outputs"])
ai_router = APIRouter(prefix="/ai", tags=["AI Model"])


# -----------------------------------------------------------------------------
# REQUEST & RESPONSE MODELS
# -----------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """Input data for a single dish prediction."""
    date                 : date  = Field(..., example="2024-11-15")
    menu_item_name       : str   = Field(..., example="Char Kway Teow")
    meal_type            : str   = Field(..., example="Dinner")
    weather_condition    : str   = Field(..., example="Rainy")
    actual_selling_price : float = Field(..., gt=0, example=8.50)
    quantity_sold        : int   = Field(
        ..., gt=0, example=120,
        description="Yesterday's quantity sold — used as tomorrow's baseline"
    )
    has_promotion        : bool  = Field(..., example=False)
    special_event        : bool  = Field(..., example=False)

    @validator('menu_item_name')
    def validate_menu_item(cls, v):
        if not ML_AVAILABLE:
            return v
        known = list(label_encoders['menu_item_name'].classes_)
        if v not in known:
            raise ValueError(
                f"Unknown menu item '{v}'. Known items: {known}"
            )
        return v

    @validator('meal_type')
    def validate_meal_type(cls, v):
        if not ML_AVAILABLE:
            return v
        known = list(label_encoders['meal_type'].classes_)
        if v not in known:
            raise ValueError(
                f"Unknown meal type '{v}'. Known types: {known}"
            )
        return v

    @validator('weather_condition')
    def validate_weather(cls, v):
        if not ML_AVAILABLE:
            return v
        known = list(label_encoders['weather_condition'].classes_)
        if v not in known:
            raise ValueError(
                f"Unknown weather condition '{v}'. Known: {known}"
            )
        return v


class BatchPredictionRequest(BaseModel):
    """Shared conditions for predicting all dishes at once."""
    date                 : date           = Field(..., example="2024-11-15")
    meal_type            : str            = Field(..., example="Dinner")
    weather_condition    : str            = Field(..., example="Rainy")
    actual_selling_price : float          = Field(..., gt=0, example=8.50)
    quantity_sold        : int            = Field(..., gt=0, example=120)
    has_promotion        : bool           = Field(..., example=False)
    special_event        : bool           = Field(..., example=False)
    menu_items           : Optional[list] = Field(
        default=None,
        description="Dishes to predict for. Leave empty to predict for ALL known dishes."
    )


class PredictionResponse(BaseModel):
    """Full prediction + recommendation for a single dish."""
    waste_ratio      : float
    waste_percent    : str
    action           : str
    urgency          : str
    adjusted_prep    : int
    change_amount    : int
    reason           : str
    display_message  : str
    menu_item_name   : str
    meal_type        : str
    quantity_sold    : int
    date             : str


class BatchPredictionResponse(BaseModel):
    """All dishes predicted and sorted by urgency."""
    total_dishes   : int
    decrease_count : int
    increase_count : int
    keep_count     : int
    summary        : str
    predictions    : list


# -----------------------------------------------------------------------------
# EXISTING ENDPOINTS — upgraded with ML model
# -----------------------------------------------------------------------------

@router.get(
    "/forecast/menu-items",
    response_model=list[ForecastPoint],
    summary="Forecast prep quantities per dish using ML model",
    description="""
    Returns ML-predicted recommended preparation quantities per dish per day
    for the requested number of days ahead.

    Uses the trained Random Forest waste model to predict waste ratio,
    then calculates optimal prep quantity to minimise waste while meeting demand.

    Falls back to moving average baseline if the ML model is unavailable.
    """
)
def forecast_menu_items(
    days  : int = Query(7,  ge=1, le=30),
    limit : int = Query(10, ge=1, le=50),
) -> list[ForecastPoint]:
    return recommendation_service.simple_forecast(days=days, limit=limit)


@router.get(
    "/recommendations",
    response_model=list[Recommendation],
    summary="Get ML-powered dish recommendations",
    description="""
    Returns dish-level recommendations based on predicted waste ratio
    from the trained Random Forest model.

    Each recommendation includes:
    - Action: DECREASE / INCREASE / KEEP
    - Severity: High / Medium / Low
    - Plain English reason explaining why

    Falls back to waste-cost based recommendations if ML model is unavailable.
    """
)
def get_recommendations(
    limit: int = Query(10, ge=1, le=50)
) -> list[Recommendation]:
    return recommendation_service.generate_recommendations(limit=limit)


# -----------------------------------------------------------------------------
# NEW AI ENDPOINTS — under /ai/ prefix
# -----------------------------------------------------------------------------

@ai_router.get(
    "/health",
    summary="Check ML model status",
    description="Confirms the ML model and encoders are loaded and ready."
)
def ai_health():
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"ML model is unavailable: {ML_ERROR}"
        )
    return {
        "status"                  : "ok",
        "model_loaded"            : True,
        "known_menu_items"        : sorted(label_encoders['menu_item_name'].classes_.tolist()),
        "known_meal_types"        : sorted(label_encoders['meal_type'].classes_.tolist()),
        "known_weather_conditions": sorted(label_encoders['weather_condition'].classes_.tolist()),
        "thresholds": {
            "high_waste_threshold"  : HIGH_WASTE_THRESHOLD,
            "low_waste_threshold"   : LOW_WASTE_THRESHOLD,
            "adjustment_percentage" : ADJUSTMENT_PERCENTAGE,
            "description"           : (
                f"waste > {HIGH_WASTE_THRESHOLD*100:.0f}% → DECREASE | "
                f"waste < {LOW_WASTE_THRESHOLD*100:.0f}% → INCREASE | "
                f"otherwise → KEEP"
            )
        }
    }


@ai_router.get(
    "/options",
    summary="Get valid input values for frontend dropdowns",
    description="Returns all valid values for menu items, meal types and weather conditions."
)
def ai_options():
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"ML model is unavailable: {ML_ERROR}"
        )
    return {
        "menu_items"         : sorted(label_encoders['menu_item_name'].classes_.tolist()),
        "meal_types"         : sorted(label_encoders['meal_type'].classes_.tolist()),
        "weather_conditions" : sorted(label_encoders['weather_condition'].classes_.tolist()),
        "thresholds": {
            "high_waste": HIGH_WASTE_THRESHOLD,
            "low_waste" : LOW_WASTE_THRESHOLD,
        }
    }


@ai_router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict waste + recommendation for a single dish",
    description="""
    Given tomorrow's conditions for one dish, returns:
    - Predicted waste ratio and percentage
    - Action: DECREASE / INCREASE / KEEP
    - Adjusted prep quantity for tomorrow
    - Plain English reason explaining the recommendation
    """
)
def ai_predict(request: PredictionRequest):
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"ML model is unavailable: {ML_ERROR}"
        )
    try:
        input_data = {
            "date"                 : str(request.date),
            "menu_item_name"       : request.menu_item_name,
            "meal_type"            : request.meal_type,
            "weather_condition"    : request.weather_condition,
            "actual_selling_price" : request.actual_selling_price,
            "quantity_sold"        : request.quantity_sold,
            "has_promotion"        : request.has_promotion,
            "special_event"        : request.special_event,
        }
        result = predict_and_recommend(input_data)
        return PredictionResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}\n{traceback.format_exc()}"
        )


@ai_router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Predict waste + recommend for ALL dishes at once",
    description="""
    Send tomorrow's shared conditions once and get recommendations for
    every dish sorted by urgency — most critical items appear first.

    Leave menu_items empty to predict for all known dishes automatically.

    Perfect for a daily dashboard view showing the full prep plan at a glance.
    """
)
def ai_predict_batch(request: BatchPredictionRequest):
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"ML model is unavailable: {ML_ERROR}"
        )
    try:
        base_input = {
            "date"                 : str(request.date),
            "meal_type"            : request.meal_type,
            "weather_condition"    : request.weather_condition,
            "actual_selling_price" : request.actual_selling_price,
            "quantity_sold"        : request.quantity_sold,
            "has_promotion"        : request.has_promotion,
            "special_event"        : request.special_event,
        }

        menu_items = request.menu_items or \
                     sorted(label_encoders['menu_item_name'].classes_.tolist())

        results        = predict_all_dishes(base_input, menu_items)
        decrease_count = sum(1 for r in results if r.get("action") == "DECREASE")
        increase_count = sum(1 for r in results if r.get("action") == "INCREASE")
        keep_count     = sum(1 for r in results if r.get("action") == "KEEP")

        parts = []
        if decrease_count:
            parts.append(f"{decrease_count} dish(es) to decrease")
        if increase_count:
            parts.append(f"{increase_count} dish(es) to increase")
        if keep_count:
            parts.append(f"{keep_count} dish(es) on track")
        summary = " | ".join(parts) if parts else "All dishes on track."

        return BatchPredictionResponse(
            total_dishes   = len(results),
            decrease_count = decrease_count,
            increase_count = increase_count,
            keep_count     = keep_count,
            summary        = summary,
            predictions    = results,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}\n{traceback.format_exc()}"
        )
