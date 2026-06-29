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

## Initial Endpoints

```text
GET  /health
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
