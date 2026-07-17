
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date

from inference_pipeline import (
    predict_and_recommend,
    predict_all_dishes,
    label_encoders,
    HIGH_WASTE_THRESHOLD,
    LOW_WASTE_THRESHOLD,
    ADJUSTMENT_PERCENTAGE
)

app = FastAPI(
    title="Smart Restaurant DSS — Waste Prediction & Dish Recommendation API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    date                 : date
    menu_item_name       : str
    meal_type            : str
    weather_condition    : str
    actual_selling_price : float = Field(..., gt=0)
    quantity_sold        : int   = Field(..., gt=0)
    has_promotion        : bool
    special_event        : bool

    @field_validator("menu_item_name")
    @classmethod
    def validate_menu_item(cls, v):
        known = list(label_encoders["menu_item_name"].classes_)
        if v not in known:
            raise ValueError(f"Unknown menu item '{v}'. Known items: {known}")
        return v

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, v):
        known = list(label_encoders["meal_type"].classes_)
        if v not in known:
            raise ValueError(f"Unknown meal type '{v}'. Known: {known}")
        return v

    @field_validator("weather_condition")
    @classmethod
    def validate_weather(cls, v):
        known = list(label_encoders["weather_condition"].classes_)
        if v not in known:
            raise ValueError(f"Unknown weather '{v}'. Known: {known}")
        return v

class BatchPredictionRequest(BaseModel):
    date                 : date
    meal_type            : str
    weather_condition    : str
    actual_selling_price : float = Field(..., gt=0)
    quantity_sold        : int   = Field(..., gt=0)
    has_promotion        : bool
    special_event        : bool
    menu_items           : Optional[List[str]] = None

class PredictionResponse(BaseModel):
    waste_ratio     : float
    waste_percent   : str
    action          : str
    urgency         : str
    adjusted_prep   : int
    change_amount   : int
    reason          : str
    display_message : str
    menu_item_name  : str
    meal_type       : str
    quantity_sold   : int
    date            : str

class BatchPredictionResponse(BaseModel):
    total_dishes   : int
    decrease_count : int
    increase_count : int
    keep_count     : int
    summary        : str
    predictions    : List[dict]

class HealthResponse(BaseModel):
    status                   : str
    model_loaded             : bool
    known_menu_items         : list
    known_meal_types         : list
    known_weather_conditions : list
    thresholds               : dict

# ── Health & Options ──────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status                   = "ok",
        model_loaded             = True,
        known_menu_items         = sorted(label_encoders["menu_item_name"].classes_.tolist()),
        known_meal_types         = sorted(label_encoders["meal_type"].classes_.tolist()),
        known_weather_conditions = sorted(label_encoders["weather_condition"].classes_.tolist()),
        thresholds               = {
            "high_waste_threshold"  : HIGH_WASTE_THRESHOLD,
            "low_waste_threshold"   : LOW_WASTE_THRESHOLD,
            "adjustment_percentage" : ADJUSTMENT_PERCENTAGE,
        }
    )

@app.get("/options")
def get_options():
    return {
        "menu_items"        : sorted(label_encoders["menu_item_name"].classes_.tolist()),
        "meal_types"        : sorted(label_encoders["meal_type"].classes_.tolist()),
        "weather_conditions": sorted(label_encoders["weather_condition"].classes_.tolist()),
    }

@app.get("/ai/health")
def ai_health():
    return {
        "status"                  : "ok",
        "model_loaded"            : True,
        "known_menu_items"        : sorted(label_encoders["menu_item_name"].classes_.tolist()),
        "known_meal_types"        : sorted(label_encoders["meal_type"].classes_.tolist()),
        "known_weather_conditions": sorted(label_encoders["weather_condition"].classes_.tolist()),
    }

@app.get("/ai/options")
def ai_options():
    return {
        "menu_items"        : sorted(label_encoders["menu_item_name"].classes_.tolist()),
        "meal_types"        : sorted(label_encoders["meal_type"].classes_.tolist()),
        "weather_conditions": sorted(label_encoders["weather_condition"].classes_.tolist()),
        "thresholds": {
            "high_waste": HIGH_WASTE_THRESHOLD,
            "low_waste" : LOW_WASTE_THRESHOLD,
        }
    }

# ── Single Dish Prediction ────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictionResponse)
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
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/ai/predict", response_model=PredictionResponse)
def ai_predict(request: PredictionRequest):
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
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# ── Batch Prediction ──────────────────────────────────────────────────────────

@app.post("/predict/batch", response_model=BatchPredictionResponse)
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
        menu_items     = request.menu_items or sorted(label_encoders["menu_item_name"].classes_.tolist())
        results        = predict_all_dishes(base_input, menu_items)
        decrease_count = sum(1 for r in results if r.get("action") == "DECREASE")
        increase_count = sum(1 for r in results if r.get("action") == "INCREASE")
        keep_count     = sum(1 for r in results if r.get("action") == "KEEP")
        parts = []
        if decrease_count: parts.append(f"{decrease_count} dish(es) to decrease")
        if increase_count: parts.append(f"{increase_count} dish(es) to increase")
        if keep_count:     parts.append(f"{keep_count} dish(es) on track")
        summary = " | ".join(parts) if parts else "All dishes on track."
        return BatchPredictionResponse(
            total_dishes=len(results), decrease_count=decrease_count,
            increase_count=increase_count, keep_count=keep_count,
            summary=summary, predictions=results,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/ai/predict/batch", response_model=BatchPredictionResponse)
def ai_predict_batch(request: BatchPredictionRequest):
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
        menu_items     = request.menu_items or sorted(label_encoders["menu_item_name"].classes_.tolist())
        results        = predict_all_dishes(base_input, menu_items)
        decrease_count = sum(1 for r in results if r.get("action") == "DECREASE")
        increase_count = sum(1 for r in results if r.get("action") == "INCREASE")
        keep_count     = sum(1 for r in results if r.get("action") == "KEEP")
        parts = []
        if decrease_count: parts.append(f"{decrease_count} dish(es) to decrease")
        if increase_count: parts.append(f"{increase_count} dish(es) to increase")
        if keep_count:     parts.append(f"{keep_count} dish(es) on track")
        summary = " | ".join(parts) if parts else "All dishes on track."
        return BatchPredictionResponse(
            total_dishes=len(results), decrease_count=decrease_count,
            increase_count=increase_count, keep_count=keep_count,
            summary=summary, predictions=results,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

# ── Recommendations & Forecast ────────────────────────────────────────────────

@app.get("/recommendations")
def get_recommendations(limit: int = 10):
    from app.services.recommendation_service import recommendation_service
    return recommendation_service.generate_recommendations(limit=limit)

@app.get("/forecast/menu-items")
def forecast_menu_items(days: int = 7, limit: int = 10):
    from app.services.recommendation_service import recommendation_service
    return recommendation_service.simple_forecast(days=days, limit=limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
