# =============================================================================
# inference_pipeline.py
# Smart Restaurant DSS — Preprocessing, Prediction & Recommendation Pipeline
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

HIGH_WASTE_THRESHOLD  = 0.12
LOW_WASTE_THRESHOLD   = 0.05
ADJUSTMENT_PERCENTAGE = 0.15


# -----------------------------------------------------------------------------
# 3. CONTEXTUAL REASON ENGINE
# -----------------------------------------------------------------------------
# Each dish has its own profile — its nature (hot/cold, heavy/light, drink etc.)
# Combined with weather and meal type to produce a human-readable explanation.

# Dish profiles — describes the nature of each dish
DISH_PROFILES = {
    "Beef Rendang": {
        "type"       : "heavy",
        "temperature": "hot",
        "category"   : "main",
        "description": "rich slow-cooked beef curry"
    },
    "Cendol": {
        "type"       : "light",
        "temperature": "cold",
        "category"   : "dessert",
        "description": "cold sweet dessert with coconut milk and pandan jelly"
    },
    "Char Kway Teow": {
        "type"       : "medium",
        "temperature": "hot",
        "category"   : "noodles",
        "description": "stir-fried flat rice noodles"
    },
    "Chicken Rice": {
        "type"       : "medium",
        "temperature": "warm",
        "category"   : "main",
        "description": "steamed or roasted chicken with fragrant rice"
    },
    "Kaya Toast Set": {
        "type"       : "light",
        "temperature": "warm",
        "category"   : "breakfast",
        "description": "toasted bread with kaya jam, eggs and coffee or tea"
    },
    "Laksa": {
        "type"       : "heavy",
        "temperature": "hot",
        "category"   : "soup noodles",
        "description": "spicy coconut milk noodle soup"
    },
    "Nasi Lemak": {
        "type"       : "medium",
        "temperature": "warm",
        "category"   : "main",
        "description": "coconut rice with sambal, egg and anchovies"
    },
    "Roti Canai": {
        "type"       : "light",
        "temperature": "warm",
        "category"   : "bread",
        "description": "flaky flatbread served with curry dipping sauce"
    },
    "Tandoori Chicken": {
        "type"       : "heavy",
        "temperature": "hot",
        "category"   : "main",
        "description": "marinated grilled chicken cooked in a tandoor oven"
    },
    "Teh Tarik": {
        "type"       : "light",
        "temperature": "hot",
        "category"   : "drink",
        "description": "pulled milk tea — a classic Malaysian staple"
    },
}


def get_contextual_reason(
    menu_item     : str,
    weather       : str,
    meal_type     : str,
    action        : str,
    waste_percent : str,
    has_promotion : bool,
    special_event : bool
) -> str:
    """
    Generates a plain English explanation for the recommendation
    based on the dish profile, weather, meal type and prediction.

    Returns a 2-sentence human readable reason the manager can
    understand without knowing anything about the ML model.
    """

    profile     = DISH_PROFILES.get(menu_item, None)
    dish_temp   = profile["temperature"] if profile else "warm"
    dish_type   = profile["type"] if profile else "medium"
    dish_cat    = profile["category"] if profile else "dish"
    dish_desc   = profile["description"] if profile else menu_item

    reasons = []

    # ── Weather-based reasons ──────────────────────────────────────────────

    if weather == "Rainy":
        if dish_temp == "cold":
            reasons.append(
                f"On rainy days customers tend to avoid cold items like {menu_item} "
                f"and gravitate toward hot comfort food instead."
            )
        elif dish_temp == "hot" and dish_type == "heavy":
            reasons.append(
                f"While rainy weather usually boosts appetite for hot food, "
                f"heavy dishes like {menu_item} ({dish_desc}) see reduced foot traffic "
                f"overall as fewer customers venture out in the rain."
            )
        elif dish_cat == "drink" and dish_temp == "hot":
            reasons.append(
                f"Hot drinks like {menu_item} are popular on rainy days "
                f"but overall stall footfall drops in wet weather."
            )
        elif dish_cat == "soup noodles":
            reasons.append(
                f"Rainy weather typically boosts demand for hot soups like {menu_item} "
                f"({dish_desc}), but reduced foot traffic at the stall can offset this."
            )
        else:
            reasons.append(
                f"Rainy weather reduces overall walk-in traffic at food stalls, "
                f"which tends to increase waste across most items including {menu_item}."
            )

    elif weather == "Sunny":
        if dish_temp == "cold":
            reasons.append(
                f"Sunny weather drives strong demand for cold items like {menu_item} "
                f"({dish_desc}) — customers actively seek refreshing options."
            )
        elif dish_temp == "hot" and dish_type == "heavy":
            reasons.append(
                f"On hot sunny days customers tend to avoid heavy hot dishes like "
                f"{menu_item} ({dish_desc}), preferring lighter or cooler options."
            )
        elif dish_cat == "drink" and dish_temp == "hot":
            reasons.append(
                f"Hot drinks like {menu_item} see softer demand on sunny days "
                f"as customers prefer cold beverages in warm weather."
            )
        elif dish_cat == "breakfast":
            reasons.append(
                f"Sunny mornings bring higher foot traffic which boosts demand "
                f"for breakfast staples like {menu_item}."
            )
        else:
            reasons.append(
                f"Sunny weather brings higher customer footfall to the stall, "
                f"which generally keeps waste low for popular items like {menu_item}."
            )

    elif weather == "Cloudy":
        reasons.append(
            f"Cloudy conditions produce average foot traffic — "
            f"demand for {menu_item} is expected to follow typical patterns."
        )

    elif weather == "Windy":
        if dish_cat in ["drink", "soup noodles"]:
            reasons.append(
                f"Windy conditions can deter customers from open-air stalls, "
                f"and hot items like {menu_item} may cool too quickly, reducing appeal."
            )
        else:
            reasons.append(
                f"Windy weather slightly reduces outdoor dining comfort, "
                f"which can dampen demand at the stall for items like {menu_item}."
            )

    # ── Meal type based reasons ────────────────────────────────────────────

    if meal_type == "Dinner":
        if dish_cat == "breakfast":
            reasons.append(
                f"{menu_item} is primarily a breakfast item — "
                f"dinner service demand is naturally lower, leading to higher waste risk."
            )
        elif dish_type == "heavy":
            reasons.append(
                f"Dinner service sees stronger demand for hearty items like {menu_item}, "
                f"but late evening footfall at food stalls can be unpredictable."
            )
        else:
            reasons.append(
                f"Dinner service at food stalls typically sees varied demand — "
                f"historical data shows {menu_item} trends toward higher waste in evening service."
            )

    elif meal_type == "Breakfast":
        if dish_cat == "breakfast":
            reasons.append(
                f"{menu_item} is a breakfast staple — morning demand is strong "
                f"and consistent, keeping waste typically low."
            )
        elif dish_type == "heavy":
            reasons.append(
                f"Heavy dishes like {menu_item} are less popular at breakfast — "
                f"most customers prefer lighter options in the morning."
            )
        else:
            reasons.append(
                f"Breakfast service demand for {menu_item} is moderate — "
                f"morning customers tend to favour familiar lighter options."
            )

    elif meal_type == "Lunch":
        if dish_type == "heavy":
            reasons.append(
                f"Lunch is peak service time for hearty dishes like {menu_item} — "
                f"office workers and students drive strong midday demand."
            )
        elif dish_cat == "breakfast":
            reasons.append(
                f"Demand for {menu_item} drops significantly by lunch as "
                f"customers shift to fuller meal options."
            )
        else:
            reasons.append(
                f"Lunch service typically drives the highest volume at food stalls — "
                f"demand for {menu_item} is expected to be steady."
            )

    # ── Promotion and event modifiers ──────────────────────────────────────

    if has_promotion and action == "KEEP":
        reasons.append(
            f"An active promotion is helping clear {menu_item} efficiently — "
            f"current prep quantity is well-matched to promoted demand."
        )
    elif has_promotion and action == "DECREASE":
        reasons.append(
            f"Even with a promotion running, predicted waste remains high — "
            f"consider a more targeted promotion specifically for {menu_item}."
        )

    if special_event and action == "INCREASE":
        reasons.append(
            f"A special event is expected to drive higher than usual footfall — "
            f"increase prep to meet the extra demand."
        )
    elif special_event and action == "DECREASE":
        reasons.append(
            f"Despite the special event, historical data suggests {menu_item} "
            f"does not benefit significantly from event-driven demand at this stall."
        )

    # ── Action summary sentence ────────────────────────────────────────────

    if action == "DECREASE":
        reasons.append(
            f"With {waste_percent} waste predicted, reducing tomorrow's prep "
            f"will cut food costs and minimise leftovers."
        )
    elif action == "INCREASE":
        reasons.append(
            f"With only {waste_percent} waste predicted, increasing prep "
            f"ensures you won't run short during service."
        )
    else:
        reasons.append(
            f"At {waste_percent} predicted waste, current prep quantity "
            f"strikes a good balance between supply and demand."
        )

    # Return the two most relevant sentences
    return " ".join(reasons[:2])


# -----------------------------------------------------------------------------
# 4. PREPROCESSING
# -----------------------------------------------------------------------------

def preprocess(input_data: dict) -> pd.DataFrame:
    df = pd.DataFrame([input_data])

    df['date']         = pd.to_datetime(df['date'])
    df['day_of_week']  = df['date'].dt.dayofweek
    df['month']        = df['date'].dt.month
    df['quarter']      = df['date'].dt.quarter
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['is_weekend']   = (df['day_of_week'] >= 5).astype(int)

    df['has_promotion'] = df['has_promotion'].astype(int)
    df['special_event'] = df['special_event'].astype(int)

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
# 5. RECOMMENDATION ENGINE
# -----------------------------------------------------------------------------

def get_recommendation(
    waste_ratio   : float,
    quantity_sold : int,
    menu_item     : str,
    weather       : str,
    meal_type     : str,
    has_promotion : bool,
    special_event : bool
) -> dict:

    waste_percent = f"{waste_ratio * 100:.1f}%"

    if waste_ratio > HIGH_WASTE_THRESHOLD:
        adjusted_prep = int(np.floor(quantity_sold * (1 - ADJUSTMENT_PERCENTAGE)))
        change_amount = quantity_sold - adjusted_prep
        action        = "DECREASE"
        urgency       = "HIGH" if waste_ratio > 0.18 else "MEDIUM"
        display_message = (
            f"⬇️  Decrease {menu_item} prep by {change_amount} portions tomorrow. "
            f"Expected waste: {waste_percent}."
        )

    elif waste_ratio < LOW_WASTE_THRESHOLD:
        adjusted_prep = int(np.ceil(quantity_sold * (1 + ADJUSTMENT_PERCENTAGE)))
        change_amount = adjusted_prep - quantity_sold
        action        = "INCREASE"
        urgency       = "MEDIUM"
        display_message = (
            f"⬆️  Increase {menu_item} prep by {change_amount} portions tomorrow. "
            f"Risk of running short — expected waste only {waste_percent}."
        )

    else:
        adjusted_prep = int(np.ceil(quantity_sold / (1 - waste_ratio)))
        change_amount = adjusted_prep - quantity_sold
        action        = "KEEP"
        urgency       = "LOW"
        display_message = (
            f"✅  {menu_item} prep looks good. "
            f"Prepare {adjusted_prep} portions to cover expected demand. "
            f"Expected waste: {waste_percent}."
        )

    # Generate contextual reason
    reason = get_contextual_reason(
        menu_item     = menu_item,
        weather       = weather,
        meal_type     = meal_type,
        action        = action,
        waste_percent = waste_percent,
        has_promotion = has_promotion,
        special_event = special_event
    )

    return {
        "action"         : action,
        "urgency"        : urgency,
        "adjusted_prep"  : adjusted_prep,
        "change_amount"  : change_amount,
        "reason"         : reason,
        "display_message": display_message,
    }


# -----------------------------------------------------------------------------
# 6. MAIN PREDICTION + RECOMMENDATION FUNCTION
# -----------------------------------------------------------------------------

def predict_and_recommend(input_data: dict) -> dict:

    required_fields = [
        'date', 'menu_item_name', 'meal_type', 'weather_condition',
        'actual_selling_price', 'quantity_sold', 'has_promotion', 'special_event'
    ]
    missing = [f for f in required_fields if f not in input_data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    if input_data['quantity_sold'] <= 0:
        raise ValueError("quantity_sold must be greater than 0.")

    features    = preprocess(input_data)
    waste_ratio = float(model.predict(features)[0])
    waste_ratio = max(0.0, min(1.0, waste_ratio))

    recommendation = get_recommendation(
        waste_ratio   = waste_ratio,
        quantity_sold = input_data['quantity_sold'],
        menu_item     = input_data['menu_item_name'],
        weather       = input_data['weather_condition'],
        meal_type     = input_data['meal_type'],
        has_promotion = input_data['has_promotion'],
        special_event = input_data['special_event'],
    )

    return {
        "waste_ratio"    : round(waste_ratio, 4),
        "waste_percent"  : f"{waste_ratio * 100:.1f}%",
        "action"         : recommendation["action"],
        "urgency"        : recommendation["urgency"],
        "adjusted_prep"  : recommendation["adjusted_prep"],
        "change_amount"  : recommendation["change_amount"],
        "reason"         : recommendation["reason"],
        "display_message": recommendation["display_message"],
        "menu_item_name" : input_data["menu_item_name"],
        "meal_type"      : input_data["meal_type"],
        "quantity_sold"  : input_data["quantity_sold"],
        "date"           : str(input_data["date"]),
    }


# -----------------------------------------------------------------------------
# 7. BATCH PREDICTION
# -----------------------------------------------------------------------------

def predict_all_dishes(base_input: dict, menu_items: list) -> list:

    # If no menu items provided, use all known dishes from the encoder
    if menu_items is None:
        menu_items = sorted(label_encoders['menu_item_name'].classes_.tolist())

    results = []
    for item in menu_items:
        try:
            input_data = {**base_input, "menu_item_name": item}
            result     = predict_and_recommend(input_data)
            results.append(result)
        except ValueError as e:
            results.append({
                "menu_item_name": item,
                "error"         : str(e)
            })

    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    action_order  = {"DECREASE": 0, "INCREASE": 1, "KEEP": 2}

    results.sort(key=lambda x: (
        urgency_order.get(x.get("urgency", "LOW"), 2),
        action_order.get(x.get("action", "KEEP"), 2)
    ))

    return results
