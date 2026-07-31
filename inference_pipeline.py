# =============================================================================
# inference_pipeline.py
# Smart Restaurant DSS — Preprocessing, Prediction & Recommendation Pipeline
# Version 4 — Corrected multi-factor logic:
#              Quadrant shapes message & urgency
#              Today's predicted waste ratio gates the ACTION
# =============================================================================

import joblib
import pandas as pd
import numpy as np
import os

# -----------------------------------------------------------------------------
# 1. LOAD MODEL & ENCODERS
# -----------------------------------------------------------------------------

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, 'rf_waste_model.pkl')
ENCODERS_PATH = os.path.join(BASE_DIR, 'label_encoders.pkl')

model          = joblib.load(MODEL_PATH)
label_encoders = joblib.load(ENCODERS_PATH)

FEATURE_COLS = [
    'actual_selling_price', 'quantity_sold', 'has_promotion', 'special_event',
    'day_of_week', 'month', 'quarter', 'week_of_year', 'is_weekend',
    'menu_item_name_enc', 'meal_type_enc', 'weather_condition_enc',
]

CAT_COLS = ['menu_item_name', 'meal_type', 'weather_condition']


# -----------------------------------------------------------------------------
# 2. THRESHOLDS & HISTORICAL DISH DATA
# -----------------------------------------------------------------------------

HIGH_WASTE_THRESHOLD  = 0.12   # above this → today is a high-waste day
LOW_WASTE_THRESHOLD   = 0.05   # below this → risk of running short
ADJUSTMENT_PERCENTAGE = 0.15   # reduce/increase prep by this fraction
TREND_THRESHOLD       = 0.03   # flag if predicted waste is 3pp above historical avg

# Median splits for revenue and waste cost classification
REVENUE_MEDIAN    = 713781
WASTE_COST_MEDIAN = 20333

# Per-dish historical metrics from the Food Stall training dataset
DISH_METRICS = {
    "Tandoori Chicken": {"revenue": 2208932, "waste_cost": 61880,  "avg_quantity_sold": 260, "ingredient_cost": 7.00, "average_waste_ratio": 0.10},
    "Kaya Toast Set"  : {"revenue": 2204396, "waste_cost": 29814,  "avg_quantity_sold": 779, "ingredient_cost": 2.80, "average_waste_ratio": 0.04},
    "Cendol"          : {"revenue": 946290,  "waste_cost": 35500,  "avg_quantity_sold": 437, "ingredient_cost": 2.00, "average_waste_ratio": 0.12},
    "Teh Tarik"       : {"revenue": 848146,  "waste_cost": 20389,  "avg_quantity_sold": 953, "ingredient_cost": 0.90, "average_waste_ratio": 0.07},
    "Beef Rendang"    : {"revenue": 760739,  "waste_cost": 20277,  "avg_quantity_sold": 73,  "ingredient_cost": 9.00, "average_waste_ratio": 0.09},
    "Roti Canai"      : {"revenue": 666823,  "waste_cost": 10987,  "avg_quantity_sold": 820, "ingredient_cost": 0.80, "average_waste_ratio": 0.05},
    "Laksa"           : {"revenue": 663238,  "waste_cost": 21011,  "avg_quantity_sold": 135, "ingredient_cost": 4.50, "average_waste_ratio": 0.10},
    "Nasi Lemak"      : {"revenue": 646514,  "waste_cost": 16870,  "avg_quantity_sold": 250, "ingredient_cost": 2.50, "average_waste_ratio": 0.08},
    "Char Kway Teow"  : {"revenue": 443331,  "waste_cost": 12565,  "avg_quantity_sold": 81,  "ingredient_cost": 5.00, "average_waste_ratio": 0.09},
    "Chicken Rice"    : {"revenue": 428128,  "waste_cost": 9456,   "avg_quantity_sold": 99,  "ingredient_cost": 4.00, "average_waste_ratio": 0.07},
}

DISH_PROFILES = {
    "Beef Rendang"    : {"temperature": "hot",  "type": "heavy",  "category": "main",      "description": "rich slow-cooked beef curry"},
    "Cendol"          : {"temperature": "cold", "type": "light",  "category": "dessert",   "description": "cold sweet dessert with coconut milk and pandan jelly"},
    "Char Kway Teow"  : {"temperature": "hot",  "type": "medium", "category": "noodles",   "description": "stir-fried flat rice noodles"},
    "Chicken Rice"    : {"temperature": "warm", "type": "medium", "category": "main",      "description": "steamed or roasted chicken with fragrant rice"},
    "Kaya Toast Set"  : {"temperature": "warm", "type": "light",  "category": "breakfast", "description": "toasted bread with kaya jam, eggs and coffee or tea"},
    "Laksa"           : {"temperature": "hot",  "type": "heavy",  "category": "soup",      "description": "spicy coconut milk noodle soup"},
    "Nasi Lemak"      : {"temperature": "warm", "type": "medium", "category": "main",      "description": "coconut rice with sambal, egg and anchovies"},
    "Roti Canai"      : {"temperature": "warm", "type": "light",  "category": "bread",     "description": "flaky flatbread served with curry dipping sauce"},
    "Tandoori Chicken": {"temperature": "hot",  "type": "heavy",  "category": "main",      "description": "marinated grilled chicken cooked in a tandoor oven"},
    "Teh Tarik"       : {"temperature": "hot",  "type": "light",  "category": "drink",     "description": "pulled milk tea — a classic Malaysian staple"},
}


# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def classify_dish(menu_item: str) -> dict:
    metrics = DISH_METRICS.get(menu_item, {})
    if not metrics:
        return {"is_high_revenue": False, "is_high_waste": False, "metrics": {}}
    return {
        "is_high_revenue": metrics["revenue"]    > REVENUE_MEDIAN,
        "is_high_waste"  : metrics["waste_cost"] > WASTE_COST_MEDIAN,
        "metrics"        : metrics,
    }


def estimate_tomorrow_waste_cost(waste_ratio, quantity_sold, ingredient_cost):
    return round(waste_ratio * quantity_sold * ingredient_cost, 2)


def get_confidence(menu_item: str) -> str:
    avg_qty = DISH_METRICS.get(menu_item, {}).get("avg_quantity_sold", 0)
    if avg_qty >= 400:
        return "High"
    elif avg_qty >= 100:
        return "Medium"
    return "Low"


def build_context_notes(menu_item, weather, meal_type, has_promotion, special_event):
    profile   = DISH_PROFILES.get(menu_item, {})
    dish_temp = profile.get("temperature", "warm")
    dish_type = profile.get("type", "medium")
    dish_cat  = profile.get("category", "dish")
    notes = []

    if weather == "Rainy":
        if dish_temp == "cold":
            notes.append(f"Rainy conditions typically reduce demand for cold items like {menu_item}.")
        elif dish_cat == "soup":
            notes.append(f"Rainy weather can boost demand for hot soups like {menu_item}, though overall foot traffic may be lower.")
        else:
            notes.append(f"Rainy weather typically reduces walk-in traffic at the stall.")
    elif weather == "Sunny":
        if dish_temp == "cold":
            notes.append(f"Sunny weather drives strong demand for cold items like {menu_item}.")
        elif dish_type == "heavy":
            notes.append(f"Customers tend to avoid heavy dishes on hot sunny days.")
        else:
            notes.append(f"Sunny weather brings higher foot traffic to the stall.")
    elif weather == "Cloudy":
        notes.append(f"Cloudy conditions produce average foot traffic.")

    if meal_type == "Breakfast" and dish_type == "heavy":
        notes.append(f"Heavy dishes like {menu_item} see lower demand at breakfast service.")
    elif meal_type == "Dinner" and dish_cat == "breakfast":
        notes.append(f"{menu_item} is primarily a breakfast item — dinner demand is naturally lower.")

    if has_promotion:
        notes.append("An active promotion may increase demand today.")
    if special_event:
        notes.append("A special event is expected to drive higher than usual footfall.")

    return " ".join(notes)


def get_trend_sentence(waste_ratio, hist_ratio, hist_ratio_pct):
    diff = waste_ratio - hist_ratio
    if diff > TREND_THRESHOLD:
        return f"This is {diff * 100:.1f} percentage points above its historical average of {hist_ratio_pct}."
    elif diff < -TREND_THRESHOLD:
        return f"This is {abs(diff) * 100:.1f} percentage points below its historical average of {hist_ratio_pct}."
    else:
        return f"This is in line with its historical average of {hist_ratio_pct}."


# -----------------------------------------------------------------------------
# 4. CORRECTED MULTI-FACTOR RECOMMENDATION ENGINE
# -----------------------------------------------------------------------------
# Rule: Quadrant shapes the MESSAGE and URGENCY.
#       Today's predicted waste_ratio GATES the ACTION.
#
# This prevents a high-revenue dish from being told DECREASE when today's
# waste is perfectly fine, and ensures a strong dish still gets DECREASE
# on days when predicted waste is genuinely high.
# -----------------------------------------------------------------------------

def get_recommendation(
    menu_item, waste_ratio, quantity_sold,
    weather, meal_type, has_promotion, special_event
):
    classification  = classify_dish(menu_item)
    is_high_revenue = classification["is_high_revenue"]
    is_high_waste   = classification["is_high_waste"]
    hist            = classification["metrics"]

    waste_percent    = f"{waste_ratio * 100:.1f}%"
    hist_ratio       = hist.get("average_waste_ratio", waste_ratio)
    hist_ratio_pct   = f"{hist_ratio * 100:.1f}%"
    ingredient_cost  = hist.get("ingredient_cost", 0)
    confidence       = get_confidence(menu_item)
    est_waste_cost   = estimate_tomorrow_waste_cost(waste_ratio, quantity_sold, ingredient_cost)
    est_waste_str    = f"RM {est_waste_cost:.2f}"
    rev_str          = f"RM {hist.get('revenue', 0):,.0f}"
    wcost_str        = f"RM {hist.get('waste_cost', 0):,.0f}"
    context          = build_context_notes(menu_item, weather, meal_type, has_promotion, special_event)
    trend            = get_trend_sentence(waste_ratio, hist_ratio, hist_ratio_pct)
    ratio_diff       = waste_ratio - hist_ratio

    # ── Determine adjusted prep quantities ────────────────────────────────────
    prep_decrease = int(np.floor(quantity_sold * (1 - ADJUSTMENT_PERCENTAGE)))
    prep_increase = int(np.ceil(quantity_sold  * (1 + ADJUSTMENT_PERCENTAGE)))
    prep_normal   = int(np.ceil(quantity_sold  / (1 - waste_ratio)))

    change_decrease = quantity_sold - prep_decrease
    change_increase = prep_increase - quantity_sold
    change_normal   = prep_normal   - quantity_sold

    # ══════════════════════════════════════════════════════════════════════════
    # QUADRANT 1 — High revenue + High historical waste cost
    # Strong earner but historically wasteful. Action depends on today.
    # ══════════════════════════════════════════════════════════════════════════
    if is_high_revenue and is_high_waste:

        if waste_ratio > HIGH_WASTE_THRESHOLD:
            # Today IS a high waste day — reduce prep but keep the item
            action        = "DECREASE"
            urgency       = "HIGH" if waste_ratio > 0.15 else "MEDIUM"
            adjusted_prep = prep_decrease
            change_amount = change_decrease
            reason = (
                f"{menu_item} is a high-revenue item ({rev_str}) with a historically high waste cost ({wcost_str}). "
                f"Today's predicted waste is {waste_percent} — estimated to cost {est_waste_str}. "
                f"{trend} "
                f"Keep this item on the menu — it earns well — but reduce prep by {change_amount} portions "
                f"to cut today's waste cost. {context}"
            )
            display_message = (
                f"⚠️  {menu_item} brings high revenue but today's waste is high. "
                f"Keep it — reduce prep by {change_amount} portions. Est. waste cost: {est_waste_str}."
            )

        else:
            # Today is a normal or low waste day — no action needed
            action        = "KEEP"
            urgency       = "LOW"
            adjusted_prep = prep_normal
            change_amount = change_normal
            reason = (
                f"{menu_item} is a high-revenue item ({rev_str}) and today's predicted waste "
                f"is {waste_percent} — within the normal range. "
                f"{trend} "
                f"Waste is under control today. Maintain current preparation. {context}"
            )
            display_message = (
                f"✅  {menu_item} is performing well today — high revenue, waste under control. "
                f"Prepare {adjusted_prep} portions. Est. waste cost: {est_waste_str}."
            )

    # ══════════════════════════════════════════════════════════════════════════
    # QUADRANT 2 — High revenue + Low historical waste cost
    # Strong performer with efficient prep. Action still depends on today.
    # ══════════════════════════════════════════════════════════════════════════
    elif is_high_revenue and not is_high_waste:

        if waste_ratio > HIGH_WASTE_THRESHOLD:
            # Unusual bad day for a normally efficient dish — flag and reduce
            action        = "DECREASE"
            urgency       = "MEDIUM"
            adjusted_prep = prep_decrease
            change_amount = change_decrease
            reason = (
                f"{menu_item} is normally a strong efficient performer ({rev_str} revenue, "
                f"low waste cost of {wcost_str}). "
                f"However today's predicted waste is {waste_percent} — unusually high for this dish. "
                f"{trend} "
                f"Reduce prep by {change_amount} portions today. Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"⚠️  {menu_item} is usually efficient but today's predicted waste is high ({waste_percent}). "
                f"Reduce prep by {change_amount} portions. Est. waste cost: {est_waste_str}."
            )

        elif waste_ratio < LOW_WASTE_THRESHOLD:
            # Very low waste — risk of running short
            action        = "INCREASE"
            urgency       = "MEDIUM"
            adjusted_prep = prep_increase
            change_amount = change_increase
            reason = (
                f"{menu_item} is a strong performer ({rev_str} revenue) with very low predicted waste "
                f"of {waste_percent} today. {trend} "
                f"Risk of running short — increase prep by {change_amount} portions to meet demand. "
                f"Est. waste cost even after increase: {est_waste_str}. {context}"
            )
            display_message = (
                f"⬆️  {menu_item} is in high demand — only {waste_percent} predicted waste. "
                f"Increase prep by {change_amount} portions to avoid running short."
            )

        else:
            # Normal day for a strong dish
            action        = "KEEP"
            urgency       = "LOW"
            adjusted_prep = prep_normal
            change_amount = change_normal
            reason = (
                f"{menu_item} is a strong performer ({rev_str} revenue, low waste cost of {wcost_str}). "
                f"Today's predicted waste is {waste_percent} — normal range. "
                f"{trend} "
                f"Maintain current preparation. Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"✅  {menu_item} is performing well — high revenue and manageable waste. "
                f"Prepare {adjusted_prep} portions. Est. waste cost: {est_waste_str}."
            )

    # ══════════════════════════════════════════════════════════════════════════
    # QUADRANT 3 — Low revenue + High historical waste cost
    # Poor performer. Even on normal days consider reducing.
    # ══════════════════════════════════════════════════════════════════════════
    elif not is_high_revenue and is_high_waste:

        if waste_ratio > HIGH_WASTE_THRESHOLD:
            # Bad day for an already poor performer — reduce urgently
            action        = "DECREASE"
            urgency       = "HIGH"
            adjusted_prep = prep_decrease
            change_amount = change_decrease
            reason = (
                f"{menu_item} has below-average revenue ({rev_str}) and a high historical waste cost ({wcost_str}). "
                f"Today's predicted waste is {waste_percent} — above the high-waste threshold. "
                f"{trend} "
                f"Prepare less of this item — low sales combined with high waste means it is losing money. "
                f"Reduce prep by {change_amount} portions. Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"⬇️  Prepare less {menu_item} — low revenue and today's waste is high ({waste_percent}). "
                f"Reduce prep by {change_amount} portions. Est. waste cost: {est_waste_str}."
            )

        else:
            # Normal waste day but historically this dish is still a problem
            action        = "DECREASE"
            urgency       = "MEDIUM"
            adjusted_prep = prep_decrease
            change_amount = change_decrease
            reason = (
                f"{menu_item} has below-average revenue ({rev_str}) and a high historical waste cost ({wcost_str}). "
                f"Today's predicted waste is {waste_percent} — within range, but this dish consistently underperforms. "
                f"{trend} "
                f"Consider reducing prep slightly and reviewing demand patterns. "
                f"Reduce by {change_amount} portions. Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"⬇️  {menu_item} historically underperforms — low revenue and high waste cost. "
                f"Reduce prep by {change_amount} portions even on a normal day. Est. waste cost: {est_waste_str}."
            )

    # ══════════════════════════════════════════════════════════════════════════
    # QUADRANT 4 — Low revenue + Low historical waste cost
    # Stable but not a priority. Only flag if today is unusually bad.
    # ══════════════════════════════════════════════════════════════════════════
    else:

        if waste_ratio > HIGH_WASTE_THRESHOLD:
            # Unusual bad day — flag it
            action        = "DECREASE"
            urgency       = "MEDIUM"
            adjusted_prep = prep_decrease
            change_amount = change_decrease
            reason = (
                f"{menu_item} is normally a stable low-waste item ({rev_str} revenue, {wcost_str} waste cost). "
                f"However today's predicted waste is {waste_percent} — above the normal threshold. "
                f"{trend} "
                f"Reduce prep by {change_amount} portions today. Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"⚠️  {menu_item} is normally stable but today's predicted waste is high ({waste_percent}). "
                f"Reduce prep by {change_amount} portions. Est. waste cost: {est_waste_str}."
            )

        elif ratio_diff > TREND_THRESHOLD:
            # Trending worse than usual — warn but keep
            action        = "KEEP"
            urgency       = "MEDIUM"
            adjusted_prep = prep_normal
            change_amount = change_normal
            reason = (
                f"{menu_item} is a stable item ({rev_str} revenue, low waste cost of {wcost_str}). "
                f"Today's predicted waste is {waste_percent}. "
                f"{trend} "
                f"No urgent action needed but waste is trending upward — monitor closely. "
                f"Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"📊  {menu_item} — waste is trending above average ({waste_percent} vs {hist_ratio_pct} historical). "
                f"Prepare {adjusted_prep} portions and monitor. Est. waste cost: {est_waste_str}."
            )

        elif waste_ratio < LOW_WASTE_THRESHOLD:
            # Very low waste — risk of running short
            action        = "INCREASE"
            urgency       = "LOW"
            adjusted_prep = prep_increase
            change_amount = change_increase
            reason = (
                f"{menu_item} has very low predicted waste of {waste_percent} today. "
                f"{trend} "
                f"Risk of running short — consider increasing prep by {change_amount} portions. "
                f"Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"⬆️  {menu_item} — very low predicted waste ({waste_percent}). "
                f"Increase prep by {change_amount} portions to avoid running short."
            )

        else:
            # Normal stable day — just maintain
            action        = "KEEP"
            urgency       = "LOW"
            adjusted_prep = prep_normal
            change_amount = change_normal
            reason = (
                f"{menu_item} is a stable item with below-average revenue ({rev_str}) "
                f"and a well-managed waste cost ({wcost_str}). "
                f"Today's predicted waste is {waste_percent}. {trend} "
                f"No action needed — maintain current preparation. Est. waste cost: {est_waste_str}. {context}"
            )
            display_message = (
                f"📊  {menu_item} is stable — waste and demand are normal. "
                f"Prepare {adjusted_prep} portions. Est. waste cost: {est_waste_str}."
            )

    return {
        "action"                 : action,
        "urgency"                : urgency,
        "adjusted_prep"          : adjusted_prep,
        "change_amount"          : change_amount,
        "reason"                 : reason.strip(),
        "display_message"        : display_message.strip(),
        "revenue_class"          : "high" if is_high_revenue else "low",
        "waste_class"            : "high" if is_high_waste   else "low",
        "estimated_waste_cost_rm": est_waste_cost,
        "historical_waste_ratio" : hist_ratio,
        "prediction_confidence"  : confidence,
    }


# -----------------------------------------------------------------------------
# 5. PREPROCESSING
# -----------------------------------------------------------------------------

def preprocess(input_data: dict) -> pd.DataFrame:
    df = pd.DataFrame([input_data])
    df['date']          = pd.to_datetime(df['date'])
    df['day_of_week']   = df['date'].dt.dayofweek
    df['month']         = df['date'].dt.month
    df['quarter']       = df['date'].dt.quarter
    df['week_of_year']  = df['date'].dt.isocalendar().week.astype(int)
    df['is_weekend']    = (df['day_of_week'] >= 5).astype(int)
    df['has_promotion'] = df['has_promotion'].astype(int)
    df['special_event'] = df['special_event'].astype(int)

    for col in CAT_COLS:
        val           = df[col].iloc[0]
        known_classes = list(label_encoders[col].classes_)
        if val not in known_classes:
            raise ValueError(
                f"Unknown value '{val}' for '{col}'. "
                f"Known values: {known_classes}."
            )
        df[col + '_enc'] = label_encoders[col].transform(df[col])

    return df[FEATURE_COLS]


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

    rec = get_recommendation(
        menu_item     = input_data['menu_item_name'],
        waste_ratio   = waste_ratio,
        quantity_sold = input_data['quantity_sold'],
        weather       = input_data['weather_condition'],
        meal_type     = input_data['meal_type'],
        has_promotion = input_data['has_promotion'],
        special_event = input_data['special_event'],
    )

    return {
        "waste_ratio"             : round(waste_ratio, 4),
        "waste_percent"           : f"{waste_ratio * 100:.1f}%",
        "historical_waste_ratio"  : round(rec["historical_waste_ratio"], 4),
        "historical_waste_percent": f"{rec['historical_waste_ratio'] * 100:.1f}%",
        "estimated_waste_cost_rm" : rec["estimated_waste_cost_rm"],
        "prediction_confidence"   : rec["prediction_confidence"],
        "action"                  : rec["action"],
        "urgency"                 : rec["urgency"],
        "adjusted_prep"           : rec["adjusted_prep"],
        "change_amount"           : rec["change_amount"],
        "reason"                  : rec["reason"],
        "display_message"         : rec["display_message"],
        "revenue_class"           : rec["revenue_class"],
        "waste_class"             : rec["waste_class"],
        "menu_item_name"          : input_data["menu_item_name"],
        "meal_type"               : input_data["meal_type"],
        "quantity_sold"           : input_data["quantity_sold"],
        "date"                    : str(input_data["date"]),
    }


# -----------------------------------------------------------------------------
# 7. BATCH PREDICTION — uses per-dish historical avg_quantity_sold as baseline
# -----------------------------------------------------------------------------

def predict_all_dishes(base_input: dict, menu_items: list) -> list:
    if menu_items is None:
        menu_items = sorted(label_encoders['menu_item_name'].classes_.tolist())

    results = []
    for item in menu_items:
        try:
            hist_qty   = DISH_METRICS.get(item, {}).get(
                "avg_quantity_sold", base_input.get("quantity_sold", 100)
            )
            input_data = {**base_input, "menu_item_name": item, "quantity_sold": hist_qty}
            results.append(predict_and_recommend(input_data))
        except ValueError as e:
            results.append({"menu_item_name": item, "error": str(e)})

    urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    action_order  = {"DECREASE": 0, "INCREASE": 1, "KEEP": 2}

    results.sort(key=lambda x: (
        urgency_order.get(x.get("urgency", "LOW"), 2),
        action_order.get(x.get("action",  "KEEP"), 2)
    ))
    return results
