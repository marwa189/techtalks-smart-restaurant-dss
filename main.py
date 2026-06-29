# =============================================================================
# main.py
# Smart Restaurant DSS — FastAPI Backend
# =============================================================================
#
# WHAT IS FASTAPI?
# ----------------
# FastAPI is a Python framework for building APIs (Application Programming
# Interfaces). An API is essentially a door your software opens so other
# systems can talk to it. Your frontend (the restaurant manager's screen)
# sends a request through that door, and this file handles what happens next.
#
# Think of it like a waiter at a restaurant:
#   - Frontend (customer) places an order (sends a request)
#   - FastAPI (waiter) takes the order to the kitchen
#   - inference_pipeline.py (kitchen) prepares the prediction
#   - FastAPI (waiter) brings the result back to the customer
#
# HOW TO RUN THIS LOCALLY:
# -------------------------
#   pip install fastapi uvicorn joblib scikit-learn pandas numpy
#   uvicorn main:app --reload
#
# Then open your browser at: http://127.0.0.1:8000/docs
# FastAPI automatically generates an interactive page where you can
# test every endpoint without writing any code.
#
# FILE STRUCTURE REQUIRED:
# -------------------------
#   project/
#   ├── main.py                  ← this file
#   ├── inference_pipeline.py    ← preprocessing + prediction logic
#   ├── rf_waste_model.pkl       ← trained model from notebook
#   └── label_encoders.pkl       ← encoders from notebook
# =============================================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
import traceback

from inference_pipeline import predict_waste_ratio, label_encoders


# -----------------------------------------------------------------------------
# 1. CREATE THE APP
# -----------------------------------------------------------------------------
# This one line creates your entire API application.
# The title and description show up in the auto-generated docs page.

app = FastAPI(
    title="Smart Restaurant DSS — Waste Prediction API",
    description="""
    Predicts the expected waste ratio for a Food Stall menu item
    given operational conditions known before service starts.

    **Output:** waste_ratio (e.g. 0.08 = expect 8% of prep to be wasted)
    and a recommended preparation quantity.
    """,
    version="1.0.0"
)


# -----------------------------------------------------------------------------
# 2. CORS MIDDLEWARE
# -----------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) controls which frontends are allowed
# to talk to this API. Without this, your React/Vue frontend will get blocked
# by the browser when it tries to call the API.
# During development, we allow everything ("*").
# In production, replace "*" with your actual frontend URL.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Replace with ["https://yourapp.com"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# 3. REQUEST & RESPONSE MODELS
# -----------------------------------------------------------------------------
# Pydantic models define the exact shape of data coming IN and going OUT.
# FastAPI uses these to:
#   - Automatically validate incoming requests (wrong type = instant error)
#   - Generate the interactive docs page
#   - Give clear error messages when something is missing

class PredictionRequest(BaseModel):
    """
    Data the frontend must send to get a prediction.
    All fields are required unless marked Optional.
    """
    date: date = Field(
        ...,
        description="Date of service",
        example="2024-11-15"
    )
    menu_item_name: str = Field(
        ...,
        description="Name of the menu item",
        example="Char Kway Teow"
    )
    meal_type: str = Field(
        ...,
        description="Service period",
        example="Dinner"
    )
    weather_condition: str = Field(
        ...,
        description="Weather during service",
        example="Rainy"
    )
    actual_selling_price: float = Field(
        ...,
        gt=0,
        description="Selling price of the item in currency units",
        example=8.50
    )
    quantity_sold: int = Field(
        ...,
        gt=0,
        description="Number of portions sold (used as demand baseline)",
        example=120
    )
    has_promotion: bool = Field(
        ...,
        description="Whether a promotion is running today",
        example=False
    )
    special_event: bool = Field(
        ...,
        description="Whether a special event is happening today",
        example=False
    )

    # Validator: make sure menu_item_name is a known item
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
            raise ValueError(f"Unknown weather '{v}'. Known conditions: {known}")
        return v


class PredictionResponse(BaseModel):
    """
    What the API sends back after a successful prediction.
    """
    waste_ratio: float = Field(..., description="Predicted waste ratio e.g. 0.082")
    waste_percent: str = Field(..., description="Human-readable e.g. '8.2%'")
    recommended_prep: int = Field(..., description="Recommended portions to prepare")
    quantity_sold: int = Field(..., description="Input quantity echoed back")
    message: str = Field(..., description="Plain English summary for the frontend")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    known_menu_items: list
    known_meal_types: list
    known_weather_conditions: list


class ErrorResponse(BaseModel):
    error: str
    detail: str


# -----------------------------------------------------------------------------
# 4. ENDPOINTS
# -----------------------------------------------------------------------------
# An endpoint is a URL your frontend calls. Each one does one specific thing.
# The decorator (@app.get, @app.post) defines the HTTP method and the URL path.

# --- Health Check ---
# Your frontend or DevOps team calls this to confirm the API is alive
# and the model loaded correctly.
# URL: GET http://127.0.0.1:8000/health

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Confirms the API is running and the model is loaded."
)
def health_check():
    return HealthResponse(
        status="ok",
        model_loaded=True,
        known_menu_items=list(label_encoders['menu_item_name'].classes_),
        known_meal_types=list(label_encoders['meal_type'].classes_),
        known_weather_conditions=list(label_encoders['weather_condition'].classes_),
    )


# --- Predict Waste Ratio ---
# The main endpoint. Frontend sends the conditions, gets back a prediction.
# URL: POST http://127.0.0.1:8000/predict

@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict waste ratio",
    description="""
    Given today's operational conditions, predicts the expected waste ratio
    for a menu item and returns a recommended preparation quantity.

    **Example use case:** Manager enters tomorrow's conditions before service.
    API returns how many portions to prepare so waste is minimised.
    """
)
def predict(request: PredictionRequest):
    """
    Steps:
    1. FastAPI validates the incoming JSON against PredictionRequest
    2. We convert the request to a plain dict
    3. inference_pipeline.py preprocesses it and runs the model
    4. We wrap the result in a PredictionResponse and send it back
    """
    try:
        # Convert Pydantic model to dict for inference_pipeline
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

        result = predict_waste_ratio(input_data)

        # Build a plain English message for the frontend to display
        message = (
            f"For {request.menu_item_name} at {request.meal_type} on {request.date}, "
            f"expect {result['waste_percent']} waste. "
            f"Recommended preparation: {result['recommended_prep']} portions."
        )

        return PredictionResponse(
            waste_ratio      = result['waste_ratio'],
            waste_percent    = result['waste_percent'],
            recommended_prep = result['recommended_prep'],
            quantity_sold    = result['quantity_sold'],
            message          = message,
        )

    except ValueError as e:
        # Known validation errors (unseen label, missing field etc.)
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        # Unexpected errors — log for debugging
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}\n{traceback.format_exc()}"
        )


# --- List Valid Input Options ---
# Utility endpoint so the frontend can populate dropdowns dynamically
# without hardcoding the list of menu items in the UI.
# URL: GET http://127.0.0.1:8000/options

@app.get(
    "/options",
    summary="Get valid input options",
    description="Returns all valid values for dropdown fields in the frontend."
)
def get_options():
    return {
        "menu_items"         : sorted(label_encoders['menu_item_name'].classes_.tolist()),
        "meal_types"         : sorted(label_encoders['meal_type'].classes_.tolist()),
        "weather_conditions" : sorted(label_encoders['weather_condition'].classes_.tolist()),
    }


# -----------------------------------------------------------------------------
# 5. RUN THE SERVER
# -----------------------------------------------------------------------------
# This block only runs if you execute this file directly:
#   python main.py
#
# In production you would use:
#   uvicorn main:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
