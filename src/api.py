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

# --- Helper Functions ---

def _extract_metadata_from_filename(filename: str) -> tuple[str | None, str | None]:
    """
    Extract garment_number and garment_type from filename.

    Expected format: <number>_<type>_<rest>.ext
    Examples:
        - 47_pantalon_20251229-195429.HEIC -> ("47", "pantalon")
        - 42_saia_20251229.HEIC -> ("42", "saia")
        - 100_vestidofesta_front_20251229.HEIC -> ("100", "vestidofesta")
        - 12_front_20251229.HEIC -> ("12", None) - type missing (front/back are ignored)
        - 33_back_20251229.HEIC -> ("33", None) - type missing

    Returns:
        tuple: (garment_number, garment_type) or (None, None) if extraction fails
    """
    import re

    # Remove file extension
    name_without_ext = os.path.splitext(filename)[0]

    # Words to ignore (these are not garment types)
    ignore_words = {'front', 'back', 'frente', 'costas'}

    # Pattern: starts with digits, followed by underscore, then text (type), then underscore or end
    # This handles: 47_pantalon_..., 100_vestidofesta_..., etc.
    pattern = r'^(\d+)_([a-zA-Zàéèêç]+)(?:_|$)'
    match = re.match(pattern, name_without_ext)

    if match:
        number = match.group(1)
        garment_type = match.group(2).lower()

        # Skip if it's a position indicator, not a garment type
        if garment_type in ignore_words:
            return (number, None)

        return (number, garment_type)

    # Fallback: try to extract just the number if format is different
    number_match = re.match(r'^(\d+)', name_without_ext)
    if number_match:
        return (number_match.group(1), None)

    return (None, None)

# --- Endpoints ---

@app.post("/generate")
async def generate_model_photo(
    file: Annotated[UploadFile, File(description="Garment photo")],
    env: str = "street",
    garment_number: str | None = None,
    garment_type: str | None = None,
    position: str | None = None,
    feedback: str | None = None,
    settings: Settings = Depends(get_settings)
):
    """
    Generate lifestyle photo from garment image.

    Args:
        file: Uploaded garment photo
        env: Environment setting (beach, forest, urban street, etc.)
        garment_number: Garment number (extracted from filename if not provided)
        garment_type: Garment type (extracted from filename if not provided)
        settings: Application settings

    Returns:
        JSON with URL (prod mode) or FileResponse (local mode)

    Raises:
        HTTPException: On validation or processing errors
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Extract garment_number and garment_type from filename if not provided
    if not garment_number or not garment_type:
        extracted_number, extracted_type = _extract_metadata_from_filename(file.filename)
        garment_number = garment_number or extracted_number
        garment_type = garment_type or extracted_type

    # Validate that we have both number and type
    if not garment_number or not garment_type:
        raise HTTPException(
            status_code=400,
            detail="garment_number and garment_type are required. Either provide them explicitly or use a filename with format: <number>_<type>_<rest>.ext (e.g., 42_pantalon_20251229.HEIC)"
        )

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.png', '.jpg', '.jpeg', '.heic', '.heif']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Use PNG, JPG, JPEG, HEIC, or HEIF."
        )

    job_id = str(uuid.uuid4())
    temp_path = os.path.join(settings.temp_upload_dir, f"{job_id}{file_ext}")

    try:
        # Save upload to temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert HEIC to PNG if needed
        if file_ext in ['.heic', '.heif']:
            try:
                from PIL import Image
                from pillow_heif import register_heif_opener

                register_heif_opener()
                img = Image.open(temp_path)

                # Convert to PNG for processing
                png_path = os.path.join(settings.temp_upload_dir, f"{job_id}.png")
                img.save(png_path, format='PNG')

                # Remove original HEIC file and use PNG
                os.remove(temp_path)
                temp_path = png_path
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to convert HEIC image: {str(e)}"
                )

        # Validate file is a real image
        try:
            from PIL import Image
            with Image.open(temp_path) as img:
                img.verify()  # Verify it's a valid image
            # Note: verify() invalidates the image, so we don't keep it open
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )

        # Generate using Engine
        result_path_or_url = engine.generate_lifestyle_photo(
            temp_path,
            environment=env,
            activity="posing for a lifestyle catalog",
            garment_number=garment_number,
            garment_type=garment_type,
            position=position,
            feedback=feedback
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
