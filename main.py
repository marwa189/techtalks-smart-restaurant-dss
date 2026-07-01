# =============================================================================
# main.py
# Smart Restaurant DSS — FastAPI Backend v2
# Adds dish recommendation endpoints on top of waste prediction
# =============================================================================
#
# ENDPOINTS:
#   GET  /health         → is the API alive?
#   GET  /options        → valid dropdown values for the frontend
#   POST /predict        → predict waste + get dish recommendation (single dish)
#   POST /predict/batch  → predict + recommend for ALL dishes at once
#
# HOW TO RUN:
#   pip install -r requirements.txt
#   uvicorn main:app --reload
#   then open http://127.0.0.1:8000/docs
# =============================================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
import traceback

from inference_pipeline import (
    predict_and_recommend,
    predict_all_dishes,
    label_encoders,
    HIGH_WASTE_THRESHOLD,
    LOW_WASTE_THRESHOLD,
    ADJUSTMENT_PERCENTAGE
)


# -----------------------------------------------------------------------------
# 1. APP SETUP
# -----------------------------------------------------------------------------

app = FastAPI(
    title="Smart Restaurant DSS — Waste Prediction & Dish Recommendation API",
    description="""
    Predicts expected waste ratio for Food Stall menu items and recommends
    whether to increase, decrease, or maintain prep quantity for the next day.

    **Two modes:**
    - `/predict` — single dish prediction + recommendation
    - `/predict/batch` — all dishes at once, sorted by urgency
    """,
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# 2. REQUEST & RESPONSE MODELS
# -----------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """Single dish prediction request."""
    date                 : date  = Field(..., example="2024-11-15")
    menu_item_name       : str   = Field(..., example="Char Kway Teow")
    meal_type            : str   = Field(..., example="Dinner")
    weather_condition    : str   = Field(..., example="Rainy")
    actual_selling_price : float = Field(..., gt=0, example=8.50)
    quantity_sold        : int   = Field(..., gt=0, example=120,
                                         description="Yesterday's quantity sold — used as tomorrow's baseline")
    has_promotion        : bool  = Field(..., example=False)
    special_event        : bool  = Field(..., example=False)

    @validator('menu_item_name')
    def validate_menu_item(cls, v):
        known = list(label_encoders['menu_item_name'].classes_)
        if v not in known:
            raise ValueError(f"Unknown menu item '{v}'. Known items: {known}")
        return v

    @validator('meal_type')
    def validate_meal_type(cls, v):
        known = list(label_encoders['meal_type'].classes_)
        if v not in known:
            raise ValueError(f"Unknown meal type '{v}'. Known types: {known}")
        return v

    @validator('weather_condition')
    def validate_weather(cls, v):
        known = list(label_encoders['weather_condition'].classes_)
        if v not in known:
            raise ValueError(f"Unknown weather '{v}'. Known: {known}")
        return v


class BatchPredictionRequest(BaseModel):
    """
    Batch prediction — shared conditions for all dishes.
    The API runs predictions for every known menu item automatically.
    """
    date                 : date  = Field(..., example="2024-11-15")
    meal_type            : str   = Field(..., example="Dinner")
    weather_condition    : str   = Field(..., example="Rainy")
    actual_selling_price : float = Field(..., gt=0, example=8.50)
    quantity_sold        : int   = Field(..., gt=0, example=120)
    has_promotion        : bool  = Field(..., example=False)
    special_event        : bool  = Field(..., example=False)
    menu_items           : Optional[List[str]] = Field(
        default=None,
        description="List of dishes to predict for. Leave empty to predict for ALL known dishes."
    )


class PredictionResponse(BaseModel):
    """Single dish prediction + recommendation response."""
    # Prediction
    waste_ratio       : float
    waste_percent     : str

    # Recommendation
    action            : str    # DECREASE / INCREASE / KEEP
    urgency           : str    # HIGH / MEDIUM / LOW
    adjusted_prep     : int    # recommended portions for tomorrow
    change_amount     : int    # how many portions to add or remove
    reason            : str    # detailed explanation
    display_message   : str    # short message for the UI

    # Echo
    menu_item_name    : str
    meal_type         : str
    quantity_sold     : int
    date              : str


class BatchPredictionResponse(BaseModel):
    """Batch prediction response — all dishes sorted by urgency."""
    total_dishes      : int
    decrease_count    : int
    increase_count    : int
    keep_count        : int
    summary           : str
    predictions       : List[dict]


class HealthResponse(BaseModel):
    status                  : str
    model_loaded            : bool
    known_menu_items        : list
    known_meal_types        : list
    known_weather_conditions: list
    thresholds              : dict


# -----------------------------------------------------------------------------
# 3. ENDPOINTS
# -----------------------------------------------------------------------------

# --- Health Check ---
@app.get("/health", response_model=HealthResponse,
         summary="Health check — confirms API is running and model is loaded")
def health_check():
    return HealthResponse(
        status                   = "ok",
        model_loaded             = True,
        known_menu_items         = sorted(label_encoders['menu_item_name'].classes_.tolist()),
        known_meal_types         = sorted(label_encoders['meal_type'].classes_.tolist()),
        known_weather_conditions = sorted(label_encoders['weather_condition'].classes_.tolist()),
        thresholds               = {
            "high_waste_threshold"  : HIGH_WASTE_THRESHOLD,
            "low_waste_threshold"   : LOW_WASTE_THRESHOLD,
            "adjustment_percentage" : ADJUSTMENT_PERCENTAGE,
            "description": (
                f"waste > {HIGH_WASTE_THRESHOLD*100:.0f}% → DECREASE | "
                f"waste < {LOW_WASTE_THRESHOLD*100:.0f}% → INCREASE | "
                f"otherwise → KEEP"
            )
        }
    )


# --- Options for frontend dropdowns ---
@app.get("/options",
         summary="Get all valid input values for frontend dropdowns")
def get_options():
    return {
        "menu_items"         : sorted(label_encoders['menu_item_name'].classes_.tolist()),
        "meal_types"         : sorted(label_encoders['meal_type'].classes_.tolist()),
        "weather_conditions" : sorted(label_encoders['weather_condition'].classes_.tolist()),
        "thresholds": {
            "high_waste" : HIGH_WASTE_THRESHOLD,
            "low_waste"  : LOW_WASTE_THRESHOLD,
        }
    }


# --- Single Dish Predict + Recommend ---
@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict waste + get recommendation for a single dish",
    description="""
    Given tomorrow's conditions for one dish, returns:
    - Predicted waste ratio
    - Whether to DECREASE, INCREASE or KEEP prep quantity
    - Exact adjusted prep quantity for tomorrow
    - Plain English explanation and display message

    **Action logic:**
    - `DECREASE` → predicted waste > 12% (too much will be wasted)
    - `INCREASE` → predicted waste < 5% (risk of running short)
    - `KEEP`     → predicted waste between 5–12% (normal range)
    """
)
def predict_single(request: PredictionRequest):
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
        raise HTTPException(status_code=500,
                            detail=f"Prediction failed: {str(e)}\n{traceback.format_exc()}")


# --- Batch Predict + Recommend (all dishes at once) ---
@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Predict waste + recommend for ALL dishes at once",
    description="""
    Send tomorrow's shared conditions once and get recommendations for
    every dish on the menu in a single response — sorted by urgency
    so the most critical items appear first.

    Leave `menu_items` empty to predict for all known dishes automatically.

    **Perfect for a daily dashboard view** showing the manager
    the full prep plan for tomorrow at a glance.
    """
)
def predict_batch(request: BatchPredictionRequest):
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

        # Use provided list or fall back to all known menu items
        menu_items = request.menu_items or \
                     sorted(label_encoders['menu_item_name'].classes_.tolist())

        results = predict_all_dishes(base_input, menu_items)

        # Count actions for the summary
        decrease_count = sum(1 for r in results if r.get("action") == "DECREASE")
        increase_count = sum(1 for r in results if r.get("action") == "INCREASE")
        keep_count     = sum(1 for r in results if r.get("action") == "KEEP")

        # Build a one-line summary for the dashboard header
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
        raise HTTPException(status_code=500,
                            detail=f"Batch prediction failed: {str(e)}\n{traceback.format_exc()}")


# -----------------------------------------------------------------------------
# 4. RUN
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
