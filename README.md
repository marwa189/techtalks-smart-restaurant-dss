# Smart Restaurant Sales & Waste Analyzer

FastAPI backend for restaurant sales analytics, waste analysis, simple forecasting, and recommendations.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Database

The analytics endpoints read from the MySQL database.

Before testing analytics APIs:

1. Start MySQL from XAMPP or your local MySQL service.
2. Import the populated `smart_restaurant_db.sql` file from the database branch.
3. Create a local `.env` file using `.env.example`.
4. Confirm the database connection:

```text
GET /health/database
```

Expected response:

```json
{
  "status": "ok",
  "database": "smart_restaurant_db"
}
```

## Initial Endpoints

```text
GET  /health
GET  /health/database
GET  /datasets/profile
POST /datasets/upload
POST /datasets/load-sample
GET  /analytics/summary
GET  /analytics/sales-trends?group_by=date
GET  /analytics/sales-trends?group_by=month
GET  /analytics/top-menu-items
GET  /analytics/waste/menu-items
GET  /analytics/waste/inventory-estimate
GET  /forecast/menu-items
GET  /recommendations
```
