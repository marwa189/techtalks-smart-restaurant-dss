from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
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
app.include_router(recommendations.ai_router)


@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(
    _request: Request,
    _exception: SQLAlchemyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database connection is unavailable"},
    )


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": "Smart Restaurant DSS API is running"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database", tags=["Health"])
def database_health() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT DATABASE()")
            ).scalar()

        return {
            "status": "ok",
            "database": str(database_name),
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection is unavailable",
        )
