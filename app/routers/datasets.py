from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import DatasetProfile
from app.services.dataset_service import dataset_store


router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetProfile)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetProfile:
    content = await file.read()
    try:
        return dataset_store.load_csv(content=content, source_name=file.filename or "uploaded.csv")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/load-sample", response_model=DatasetProfile)
def load_sample_dataset() -> DatasetProfile:
    try:
        return dataset_store.load_sample()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Sample dataset was not found. Upload a CSV or place it in data/.",
        ) from exc


@router.get("/profile", response_model=DatasetProfile)
def get_dataset_profile() -> DatasetProfile:
    return dataset_store.profile()
