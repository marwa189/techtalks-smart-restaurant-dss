# =============================================================================
# inference_pipeline.py
# Smart Restaurant DSS — Preprocessing, Prediction & Recommendation Pipeline
# =============================================================================
#
# WHAT THIS FILE DOES:
# --------------------
# 1. Loads the trained model and label encoders once at startup
# 2. Transforms raw input into numeric features the model understands
# 3. Runs the prediction
# 4. Passes the predicted waste_ratio into a recommendation engine
#    that decides whether to increase, decrease or keep prep quantity
#
# VERSION 2 — adds dish-level recommendation on top of waste prediction
# =============================================================================

import joblib
import pandas as pd
import numpy as np
import os

# -----------------------------------------------------------------------------
# 1. LOAD MODEL & ENCODERS
# -----------------------------------------------------------------------------

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH     = os.path.join(BASE_DIR, 'rf_waste_model.pkl')
ENCODERS_PATH  = os.path.join(BASE_DIR, 'label_encoders.pkl')

model          = joblib.load(MODEL_PATH)
label_encoders = joblib.load(ENCODERS_PATH)

# Exact feature columns in the exact order the model was trained on
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

CAT_COLS = ['menu_item_name', 'meal_type', 'weather_condition']


# -----------------------------------------------------------------------------
# 2. RECOMMENDATION THRESHOLDS
# -----------------------------------------------------------------------------
# These three zones define what action to take based on predicted waste ratio.
# They can be adjusted per restaurant preference — these are sensible defaults.
#
#   waste_ratio > HIGH_WASTE_THRESHOLD  →  decrease prep (too much being wasted)
#   waste_ratio < LOW_WASTE_THRESHOLD   →  increase prep (risk of running short)
#   anything in between                 →  prep looks right, keep it
#
# Adjustment percentage controls how much to change the quantity.
# e.g. 0.15 means recommend 15% fewer/more portions than current.

HIGH_WASTE_THRESHOLD  = 0.12   # above 12% waste → decrease
LOW_WASTE_THRESHOLD   = 0.05   # below 5% waste  → increase
ADJUSTMENT_PERCENTAGE = 0.15   # adjust by 15% when a change is recommended


# -----------------------------------------------------------------------------
# 3. PREPROCESSING
# -----------------------------------------------------------------------------

def preprocess(input_data: dict) -> pd.DataFrame:
    """
    Transform raw input dict into a numeric DataFrame the model can consume.
    Applies the exact same transformations used during training.
    """

    df = pd.DataFrame([input_data])

    # Date → numeric time features
    df['date']         = pd.to_datetime(df['date'])
    df['day_of_week']  = df['date'].dt.dayofweek
    df['month']        = df['date'].dt.month
    df['quarter']      = df['date'].dt.quarter
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_weekend']   = (df['day_of_week'] >= 5).astype(int)

    # Boolean → integer
    df['has_promotion'] = df['has_promotion'].astype(int)
    df['special_event'] = df['special_event'].astype(int)

    # String categories → integers using the same encoders from training
    for col in CAT_COLS:
        val           = df[col].iloc[0]
        known_classes = list(label_encoders[col].classes_)

        if val not in known_classes:
            raise ValueError(
                f"Unknown value '{val}' for '{col}'. "
                f"Known values: {known_classes}. "
                f"Retrain the model to include this new category."
            )

        df[col + '_enc'] = label_encoders[col].transform(df[col])

    return df[FEATURE_COLS]


# -----------------------------------------------------------------------------
# 4. RECOMMENDATION ENGINE
# -----------------------------------------------------------------------------

def get_recommendation(waste_ratio: float, quantity_sold: int, menu_item: str) -> dict:
    """
    Takes a predicted waste ratio and returns a plain-English recommendation
    with an adjusted prep quantity for the next day.

    Args:
        waste_ratio  : predicted waste ratio e.g. 0.13
        quantity_sold: yesterday's quantity sold (used as tomorrow's baseline)
        menu_item    : name of the dish (for the message)

    Returns:
        dict with action, reason, adjusted_prep, change_amount, urgency
    """

    # --- HIGH WASTE: decrease prep ---
    if waste_ratio > HIGH_WASTE_THRESHOLD:
        adjusted_prep = int(np.floor(quantity_sold * (1 - ADJUSTMENT_PERCENTAGE)))
        change_amount = quantity_sold - adjusted_prep
        return {
            "action"       : "DECREASE",
            "urgency"      : "HIGH" if waste_ratio > 0.18 else "MEDIUM",
            "adjusted_prep": adjusted_prep,
            "change_amount": change_amount,
            "reason"       : (
                f"Predicted waste of {waste_ratio*100:.1f}% is above the "
                f"{HIGH_WASTE_THRESHOLD*100:.0f}% threshold. "
                f"Reduce tomorrow's prep by {change_amount} portions "
                f"to avoid over-preparation."
            ),
            "display_message": (
                f"⬇️  Decrease {menu_item} prep by {change_amount} portions tomorrow. "
                f"Expected waste: {waste_ratio*100:.1f}%."
            )
        }

    # --- LOW WASTE: increase prep ---
    elif waste_ratio < LOW_WASTE_THRESHOLD:
        adjusted_prep = int(np.ceil(quantity_sold * (1 + ADJUSTMENT_PERCENTAGE)))
        change_amount = adjusted_prep - quantity_sold
        return {
            "action"       : "INCREASE",
            "urgency"      : "MEDIUM",
            "adjusted_prep": adjusted_prep,
            "change_amount": change_amount,
            "reason"       : (
                f"Predicted waste of {waste_ratio*100:.1f}% is below the "
                f"{LOW_WASTE_THRESHOLD*100:.0f}% threshold — you may be "
                f"running short. Increase tomorrow's prep by {change_amount} "
                f"portions to meet demand."
            ),
            "display_message": (
                f"⬆️  Increase {menu_item} prep by {change_amount} portions tomorrow. "
                f"Risk of running short — expected waste only {waste_ratio*100:.1f}%."
            )
        }

    # --- NORMAL: keep current prep ---
    else:
        # Even in the normal zone, still recommend the optimal prep quantity
        # accounting for expected waste so they cover demand exactly
        adjusted_prep = int(np.ceil(quantity_sold / (1 - waste_ratio)))
        change_amount = adjusted_prep - quantity_sold
        return {
            "action"       : "KEEP",
            "urgency"      : "LOW",
            "adjusted_prep": adjusted_prep,
            "change_amount": change_amount,
            "reason"       : (
                f"Predicted waste of {waste_ratio*100:.1f}% is within the "
                f"normal range ({LOW_WASTE_THRESHOLD*100:.0f}%–"
                f"{HIGH_WASTE_THRESHOLD*100:.0f}%). "
                f"Prep quantity looks right for tomorrow."
            ),
            "display_message": (
                f"✅  {menu_item} prep looks good. "
                f"Prepare {adjusted_prep} portions to cover expected demand. "
                f"Expected waste: {waste_ratio*100:.1f}%."
            )
        }


# -----------------------------------------------------------------------------
# 5. MAIN PREDICTION + RECOMMENDATION FUNCTION
# -----------------------------------------------------------------------------

def predict_and_recommend(input_data: dict) -> dict:
    """
    Full pipeline: preprocess → predict → recommend.

    Args:
        input_data: dict with raw restaurant operation data

    Returns:
        dict with prediction results and dish recommendation
    """

    # Validate required fields
    required_fields = [
        'date', 'menu_item_name', 'meal_type', 'weather_condition',
        'actual_selling_price', 'quantity_sold', 'has_promotion', 'special_event'
    ]
    missing = [f for f in required_fields if f not in input_data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    if input_data['quantity_sold'] <= 0:
        raise ValueError("quantity_sold must be greater than 0.")

    # Step 1 — preprocess
    features = preprocess(input_data)

    # Step 2 — predict
    waste_ratio = float(model.predict(features)[0])
    waste_ratio = max(0.0, min(1.0, waste_ratio))  # clamp to [0, 1]

    # Step 3 — recommend
    recommendation = get_recommendation(
        waste_ratio   = waste_ratio,
        quantity_sold = input_data['quantity_sold'],
        menu_item     = input_data['menu_item_name']
    )

    # Step 4 — combine everything into one clean response
    return {
        # Prediction
        "waste_ratio"      : round(waste_ratio, 4),
        "waste_percent"    : f"{waste_ratio * 100:.1f}%",

        # Recommendation
        "action"           : recommendation["action"],         # DECREASE / INCREASE / KEEP
        "urgency"          : recommendation["urgency"],        # HIGH / MEDIUM / LOW
        "adjusted_prep"    : recommendation["adjusted_prep"],  # recommended portions
        "change_amount"    : recommendation["change_amount"],  # how many to add/remove
        "reason"           : recommendation["reason"],         # detailed explanation
        "display_message"  : recommendation["display_message"],# short UI message

        # Echo inputs back for frontend clarity
        "menu_item_name"   : input_data["menu_item_name"],
        "meal_type"        : input_data["meal_type"],
        "quantity_sold"    : input_data["quantity_sold"],
        "date"             : str(input_data["date"]),
    }


# -----------------------------------------------------------------------------
# 6. BATCH PREDICTION (all dishes for tomorrow at once)
# -----------------------------------------------------------------------------

def predict_all_dishes(base_input: dict, menu_items: list) -> list:
    """
    Run predictions for ALL dishes at once so the manager can see
    the full picture for tomorrow in a single request.

    Args:
        base_input : dict with shared conditions (date, meal_type,
                     weather_condition, actual_selling_price,
                     quantity_sold, has_promotion, special_event)
        menu_items : list of dish names to predict for

    Returns:
        list of prediction+recommendation dicts, sorted by urgency
              HIGH first, then MEDIUM, then LOW/KEEP
    """

    results = []
    for item in menu_items:
        try:
            input_data = {**base_input, "menu_item_name": item}
            result     = predict_and_recommend(input_data)
            results.append(result)
        except ValueError as e:
            results.append({
                "menu_item_name" : item,
                "error"          : str(e)
            })

    # Sort: DECREASE (HIGH urgency) first, then INCREASE, then KEEP
    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    action_order  = {"DECREASE": 0, "INCREASE": 1, "KEEP": 2}

    results.sort(key=lambda x: (
        urgency_order.get(x.get("urgency", "LOW"), 2),
        action_order.get(x.get("action", "KEEP"), 2)
    ))

    return results
