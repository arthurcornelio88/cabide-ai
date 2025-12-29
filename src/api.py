import os
import shutil
import uuid
from typing import Annotated

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from engine import FashionEngine

# --- Configuration Management ---
class Settings(BaseSettings):
    """
    Handles global config. Toggles between 'local' and 'prod' (GCS in Brazil).
    """
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    storage_mode: str = "local"  # Toggle: 'local' (France/Dev) or 'prod' (Brazil/GCS)
    gcs_bucket_name: str = "cabide-catalog-br"
    temp_upload_dir: str = "temp/uploads"
    output_dir: str = "outputs"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Dependency to provide settings singleton
def get_settings():
    return Settings()

# --- Schemas ---
class HealthResponse(BaseModel):
    status: str
    model: str
    storage_mode: str
    version: str = "1.1.0"

# --- Initialization ---
app = FastAPI(title="Cabide AI API - Brazil/France Hybrid")
settings = get_settings()

# Prepare directories for local mode
os.makedirs(settings.temp_upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)

# Initialize Engine (Engine logic now handles GCS vs Local internally)
engine = FashionEngine()

# --- Endpoints ---

@app.post("/generate")
async def generate_model_photo(
    file: Annotated[UploadFile, File(description="Garment photo")],
    env: str = "street",
    settings: Settings = Depends(get_settings)
):
    """
    Logic:
    1. Save input locally for processing.
    2. Engine generates and saves result to GCS (Brazil) or Local (France).
    3. Return URL (Cloud) or File (Local).
    """
    job_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    temp_path = os.path.join(settings.temp_upload_dir, f"{job_id}{file_ext}")

    try:
        # Save upload to temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate using Engine
        result_path_or_url = engine.generate_lifestyle_photo(
            temp_path,
            environment=env,
            activity="posing for a lifestyle catalog"
        )

        # Response based on Storage Mode
        if settings.storage_mode == "prod":
            return JSONResponse(content={
                "job_id": job_id,
                "url": result_path_or_url,
                "region": "southamerica-east1"
            })

        return FileResponse(
            path=result_path_or_url,
            media_type="image/png",
            filename=f"cabide_{job_id}.png"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    return HealthResponse(
        status="online",
        model="gemini-3-pro-image-preview",
        storage_mode=settings.storage_mode
    )
