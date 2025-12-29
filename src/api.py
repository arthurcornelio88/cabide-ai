import os
import shutil
import uuid
import logging
from typing import Annotated

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import google.generativeai as genai

from src.engine import FashionEngine
from src.config import get_settings, Settings

logger = logging.getLogger(__name__)

# --- Schemas ---
class HealthResponse(BaseModel):
    status: str
    model: str
    storage_mode: str
    version: str = "1.1.0"

# --- Initialization ---
app = FastAPI(title="Cabide AI API - Brazil/France Hybrid")

# Prepare directories for local mode
_init_settings = get_settings()
os.makedirs(_init_settings.temp_upload_dir, exist_ok=True)
os.makedirs(_init_settings.output_dir, exist_ok=True)

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
    Generate lifestyle photo from garment image.

    Args:
        file: Uploaded garment photo
        env: Environment setting (beach, forest, urban street, etc.)
        settings: Application settings

    Returns:
        JSON with URL (prod mode) or FileResponse (local mode)

    Raises:
        HTTPException: On validation or processing errors
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.png', '.jpg', '.jpeg']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Use PNG, JPG, or JPEG."
        )

    job_id = str(uuid.uuid4())
    temp_path = os.path.join(settings.temp_upload_dir, f"{job_id}{file_ext}")

    try:
        # Save upload to temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file is a real image
        try:
            from PIL import Image
            img = Image.open(temp_path)
            img.verify()  # Verify it's a valid image
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )

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
                "region": "southamerica-east1",
                "environment": env
            })

        # Return file for local mode
        if not os.path.exists(result_path_or_url):
            raise HTTPException(
                status_code=500,
                detail="Generated image file not found"
            )

        return FileResponse(
            path=result_path_or_url,
            media_type="image/png",
            filename=f"cabide_{job_id}.png"
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Generation failed for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Engine Error: {str(e)}"
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check with actual connectivity verification.
    Tests Gemini API and GCS if in prod mode.
    """
    checks = {"gemini": False, "storage": False}

    # Check Gemini API
    try:
        genai.configure(api_key=settings.gemini_api_key)
        # Quick test - just check if we can list models
        list(genai.list_models())
        checks["gemini"] = True
    except Exception as e:
        logger.warning(f"Gemini health check failed: {e}")

    # Check Storage
    if settings.storage_mode == "prod":
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(settings.gcs_bucket_name)
            bucket.exists()  # Verify bucket is accessible
            checks["storage"] = True
        except Exception as e:
            logger.warning(f"GCS health check failed: {e}")
    else:
        checks["storage"] = True  # Local mode always "healthy"

    status = "healthy" if all(checks.values()) else "degraded"

    return HealthResponse(
        status=status,
        model="gemini-3-pro-image-preview",
        storage_mode=settings.storage_mode
    )
