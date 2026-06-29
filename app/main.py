from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analytics, datasets, recommendations


app = FastAPI(
    title="Smart Restaurant Sales & Waste Analyzer API",
    description="APIs for sales analytics, waste analysis, forecasting, and recommendations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": "Smart Restaurant DSS API is running"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
