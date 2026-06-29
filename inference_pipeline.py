# =============================================================================
# inference_pipeline.py
# Smart Restaurant DSS — Preprocessing & Prediction Pipeline
# =============================================================================
#
# WHAT THIS FILE DOES:
# --------------------
# When the model was trained, raw data went through a series of
# transformations before the model ever saw it:
#   - dates were broken into day_of_week, month, quarter etc.
#   - strings like "Rainy" were converted to integers
#   - booleans were converted to 0/1
#
# This file recreates EXACTLY those same transformations so that when
# new data comes in from your app, it gets prepared the same way.
# The model will then understand it and return a prediction.
#
# Think of it as a translator: raw input → language the model speaks.
#
# HOW TO USE:
# -----------
# from inference_pipeline import predict_waste_ratio
#
# result = predict_waste_ratio({
#     "date": "2024-11-15",
#     "menu_item_name": "Char Kway Teow",
#     "meal_type": "Dinner",
#     "weather_condition": "Rainy",
#     "actual_selling_price": 8.50,
#     "quantity_sold": 120,
#     "has_promotion": False,
#     "special_event": False
# })
# print(result)
# → { "waste_ratio": 0.082, "recommended_prep": 131, "waste_percent": "8.2%" }
# =============================================================================

import joblib
import pandas as pd
import numpy as np
import os

# -----------------------------------------------------------------------------
# 1. LOAD THE MODEL AND ENCODERS
# -----------------------------------------------------------------------------
# These two files are produced by the notebook when training is complete.
# They must be in the same folder as this file when deployed.
# The model is loaded ONCE at startup (not on every request) for performance.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH    = os.path.join(BASE_DIR, 'rf_waste_model.pkl')
ENCODERS_PATH = os.path.join(BASE_DIR, 'label_encoders.pkl')

model          = joblib.load(MODEL_PATH)
label_encoders = joblib.load(ENCODERS_PATH)

# The exact feature columns the model was trained on — ORDER MATTERS
# The model expects columns in this exact sequence
FEATURE_COLS = [
    'actual_selling_price',
    'quantity_sold',
    'has_promotion',
    'special_event',
    'day_of_week',
    'month',
    'quarter',
    'week_of_year',
    'is_weekend',
    'menu_item_name_enc',
    'meal_type_enc',
    'weather_condition_enc',
]

# Categorical columns that need label encoding
# These must match exactly what was encoded during training
CAT_COLS = ['menu_item_name', 'meal_type', 'weather_condition']


# -----------------------------------------------------------------------------
# 2. PREPROCESSING FUNCTION
# -----------------------------------------------------------------------------
# Takes raw input (the way it comes from your app or database)
# and transforms it into the numeric format the model understands.

def preprocess(input_data: dict) -> pd.DataFrame:
    """
    Transform raw input into model-ready numeric features.

    Args:
        input_data: dict with keys:
            date, menu_item_name, meal_type, weather_condition,
            actual_selling_price, quantity_sold, has_promotion, special_event

    Returns:
        pd.DataFrame with exactly the columns the model expects
    """

    df = pd.DataFrame([input_data])

    # --- Date → numeric features ---
    # The model doesn't understand "2024-11-15" as a date string.
    # We break it apart into numbers it can use as signals.
    df['date']         = pd.to_datetime(df['date'])
    df['day_of_week']  = df['date'].dt.dayofweek       # 0=Monday, 6=Sunday
    df['month']        = df['date'].dt.month            # 1–12
    df['quarter']      = df['date'].dt.quarter          # 1–4
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_weekend']   = (df['day_of_week'] >= 5).astype(int)  # 1 if Sat/Sun

    # --- Boolean → integer ---
    # scikit-learn needs numbers, not True/False
    df['has_promotion'] = df['has_promotion'].astype(int)
    df['special_event'] = df['special_event'].astype(int)

    # --- String categories → integers ---
    # We use the SAME LabelEncoders from training so the mapping is identical.
    # e.g. if "Dinner" = 2 during training, it must still = 2 here.
    for col in CAT_COLS:
        if col not in label_encoders:
            raise ValueError(f"No encoder found for column: {col}")

        val = df[col].iloc[0]
        known_classes = list(label_encoders[col].classes_)

        # Guard against unseen labels (new items not in training data)
        if val not in known_classes:
            raise ValueError(
                f"Unknown value '{val}' for '{col}'. "
                f"Known values are: {known_classes}. "
                f"Retrain the model to include this new category."
            )

        df[col + '_enc'] = label_encoders[col].transform(df[col])

    # --- Return only the columns the model needs, in the right order ---
    return df[FEATURE_COLS]


# -----------------------------------------------------------------------------
# 3. PREDICTION FUNCTION
# -----------------------------------------------------------------------------
# This is the main function your FastAPI endpoint calls.
# It runs preprocessing and returns a clean, actionable result.

def predict_waste_ratio(input_data: dict) -> dict:
    """
    Predict waste ratio for a given set of conditions.

    Args:
        input_data: dict with raw restaurant operation data

    Returns:
        dict with:
            waste_ratio        — predicted fraction e.g. 0.082
            waste_percent      — human-readable e.g. "8.2%"
            recommended_prep   — how many portions to prepare
            quantity_sold      — the input quantity (echo back for clarity)
    """

    # Validate required fields are present
    required_fields = [
        'date', 'menu_item_name', 'meal_type', 'weather_condition',
        'actual_selling_price', 'quantity_sold', 'has_promotion', 'special_event'
    ]
    missing = [f for f in required_fields if f not in input_data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Validate quantity_sold is positive
    if input_data['quantity_sold'] <= 0:
        raise ValueError("quantity_sold must be greater than 0.")

    # Run preprocessing
    features = preprocess(input_data)

    # Get prediction from model
    waste_ratio = float(model.predict(features)[0])

    # Clamp to [0, 1] — predictions should never go outside this range
    # but we guard against floating point edge cases
    waste_ratio = max(0.0, min(1.0, waste_ratio))

    # Calculate recommended preparation quantity
    # Logic: if 8% will be wasted, prepare quantity / (1 - 0.08)
    # so that after waste you still have enough to cover demand
    quantity_sold = input_data['quantity_sold']
    recommended_prep = int(np.ceil(quantity_sold / (1 - waste_ratio)))

    return {
        "waste_ratio"      : round(waste_ratio, 4),
        "waste_percent"    : f"{waste_ratio * 100:.1f}%",
        "recommended_prep" : recommended_prep,
        "quantity_sold"    : quantity_sold,
    }
