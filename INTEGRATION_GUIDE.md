# AI Model Integration Guide
## Smart Restaurant DSS — For Backend Developer

---

## What you're receiving

| File | Where to put it | What it does |
|---|---|---|
| `inference_pipeline.py` | Project root (next to `main.py`) | Loads model, preprocesses input, runs predictions |
| `app/routers/recommendations.py` | Replace existing file | Upgraded router with ML endpoints |
| `app/services/recommendation_service.py` | Replace existing file | ML-powered service replacing moving average baseline |
| `rf_waste_model.pkl` | Project root | Trained Random Forest model |
| `label_encoders.pkl` | Project root | String→integer encoders |

---

## Folder structure after integration

```
project/
├── main.py                                  ← NO CHANGES NEEDED
├── inference_pipeline.py                    ← NEW (place here)
├── rf_waste_model.pkl                       ← NEW (place here)
├── label_encoders.pkl                       ← NEW (place here)
├── app/
│   ├── database.py                          ← unchanged
│   ├── schemas.py                           ← unchanged
│   ├── routers/
│   │   ├── analytics.py                     ← unchanged
│   │   ├── datasets.py                      ← unchanged
│   │   └── recommendations.py              ← REPLACE with new version
│   └── services/
│       ├── analytics_service.py             ← unchanged
│       ├── dataset_service.py               ← unchanged
│       └── recommendation_service.py       ← REPLACE with new version
```

---

## One change required in main.py

The new recommendations router exports TWO routers instead of one.
Add the ai_router include alongside the existing one:

```python
# Current line (keep this)
from app.routers import analytics, datasets, recommendations

# Add this line below the existing include_router calls
app.include_router(recommendations.router)     # existing — keeps /forecast and /recommendations
app.include_router(recommendations.ai_router)  # new — adds /ai/* endpoints
```

That is the only change needed in main.py.

---

## Dependencies to add to requirements.txt

```
scikit-learn>=1.4.0
joblib>=1.4.0
pandas>=2.0.0
numpy>=1.26.0
gdown>=5.2.0
```

---

## Model files — how to get them

The .pkl files are NOT on GitHub (intentionally excluded via .gitignore).
They will be shared via Google Drive.

**Option A — Manual placement (simplest)**
Download both files from the shared Google Drive folder and place them
in the project root next to main.py.

**Option B — Auto-download on startup (recommended for deployment)**
Add this to the top of inference_pipeline.py (ML team will provide Drive IDs):

```python
import gdown, os

MODEL_DRIVE_ID    = "paste_model_file_id_here"
ENCODERS_DRIVE_ID = "paste_encoders_file_id_here"

if not os.path.exists('rf_waste_model.pkl'):
    gdown.download(
        f"https://drive.google.com/uc?id={MODEL_DRIVE_ID}",
        'rf_waste_model.pkl', quiet=False
    )

if not os.path.exists('label_encoders.pkl'):
    gdown.download(
        f"https://drive.google.com/uc?id={ENCODERS_DRIVE_ID}",
        'label_encoders.pkl', quiet=False
    )
```

---

## Endpoints added

### Upgraded existing endpoints
These keep the same URLs and schemas — no frontend changes needed:

| Method | Endpoint | Change |
|---|---|---|
| GET | `/forecast/menu-items` | Now uses ML model instead of moving average |
| GET | `/recommendations` | Now uses ML waste predictions instead of waste cost |

### New AI endpoints
| Method | Endpoint | Description |
|---|---|---|
| GET | `/ai/health` | ML model status + valid input values |
| GET | `/ai/options` | Dropdown values for frontend |
| POST | `/ai/predict` | Single dish prediction + recommendation |
| POST | `/ai/predict/batch` | All dishes at once, sorted by urgency |

---

## Graceful degradation

If the .pkl files are missing or fail to load:
- `/forecast/menu-items` automatically falls back to the original moving average
- `/recommendations` automatically falls back to the original waste-cost logic
- `/ai/*` endpoints return `503 Service Unavailable` with a clear error message

The app will never crash due to missing model files — it degrades gracefully.

---

## Testing after integration

```bash
# Start the server
uvicorn main:app --reload

# Test ML model is loaded
curl http://localhost:8000/ai/health

# Test upgraded forecast endpoint
curl "http://localhost:8000/forecast/menu-items?days=3&limit=5"

# Test upgraded recommendations endpoint
curl "http://localhost:8000/recommendations?limit=5"

# Test single dish prediction
curl -X POST http://localhost:8000/ai/predict \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-11-15",
    "menu_item_name": "Char Kway Teow",
    "meal_type": "Dinner",
    "weather_condition": "Rainy",
    "actual_selling_price": 8.50,
    "quantity_sold": 120,
    "has_promotion": false,
    "special_event": false
  }'

# Test batch prediction
curl -X POST http://localhost:8000/ai/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-11-15",
    "meal_type": "Dinner",
    "weather_condition": "Rainy",
    "actual_selling_price": 8.50,
    "quantity_sold": 100,
    "has_promotion": false,
    "special_event": false
  }'
```

---

## Interactive docs

Once running, visit:
```
http://localhost:8000/docs
```

FastAPI generates a full interactive testing page automatically.
Every endpoint can be tested there without writing any code.
