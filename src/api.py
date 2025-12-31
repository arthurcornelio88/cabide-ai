import logging
import os
import shutil
import uuid
from typing import Annotated, Optional

import google.generativeai as genai
import requests
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import Settings, get_settings
from src.engine import FashionEngine

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


async def verify_oauth_token(authorization: Optional[str] = Header(None)):
    """
    Verify OAuth token by calling Google's userinfo endpoint.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User info dict if token is valid

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide Bearer token in Authorization header.",
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>",
        )

    token = parts[1]

    # Verify token with Google
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=401, detail="Invalid or expired OAuth token"
            )

        user_info = response.json()
        logger.info(f"Authenticated request from: {user_info.get('email', 'unknown')}")
        return user_info

    except requests.RequestException as e:
        logger.error(f"OAuth verification failed: {e}")
        raise HTTPException(status_code=401, detail="Failed to verify OAuth token")


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
    ignore_words = {"front", "back", "frente", "costas"}

    # Pattern: starts with digits, followed by underscore, then text (type), then underscore or end
    # This handles: 47_pantalon_..., 100_vestidofesta_..., etc.
    pattern = r"^(\d+)_([a-zA-Zàéèêç]+)(?:_|$)"
    match = re.match(pattern, name_without_ext)

    if match:
        number = match.group(1)
        garment_type = match.group(2).lower()

        # Skip if it's a position indicator, not a garment type
        if garment_type in ignore_words:
            return (number, None)

        return (number, garment_type)

    # Fallback: try to extract just the number if format is different
    number_match = re.match(r"^(\d+)", name_without_ext)
    if number_match:
        return (number_match.group(1), None)

    return (None, None)


# --- Endpoints ---


@app.post("/generate")
async def generate_model_photo(
    files: Annotated[list[UploadFile], File(description="Garment photo(s)")],
    env: Annotated[str, Form()] = "street",
    garment_number: Annotated[str | None, Form()] = None,
    garment_type: Annotated[str | None, Form()] = None,
    position: Annotated[str | None, Form()] = None,
    feedback: Annotated[str | None, Form()] = None,
    piece1_type: Annotated[str | None, Form()] = None,
    piece2_type: Annotated[str | None, Form()] = None,
    piece3_type: Annotated[str | None, Form()] = None,
    settings: Settings = Depends(get_settings),
    user_info: dict = Depends(verify_oauth_token),
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
    logger.info(
        f"Received request: env={env}, garment_number={garment_number}, garment_type={garment_type}, position={position}, feedback={feedback}, files={len(files)}"
    )

    # Validate we have at least one file
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file is required")

    # Extract garment_number and garment_type from first filename if not provided
    if not garment_number or not garment_type:
        extracted_number, extracted_type = _extract_metadata_from_filename(
            files[0].filename
        )
        garment_number = garment_number or extracted_number
        garment_type = garment_type or extracted_type

    # Validate that we have both number and type
    if not garment_number or not garment_type:
        raise HTTPException(
            status_code=400,
            detail="garment_number and garment_type are required. Either provide them explicitly or use a filename with format: <number>_<type>_<rest>.ext (e.g., 42_pantalon_20251229.HEIC)",
        )

    job_id = str(uuid.uuid4())
    temp_paths = []

    try:
        # Process all uploaded files
        for idx, file in enumerate(files):
            if not file.filename:
                raise HTTPException(
                    status_code=400, detail=f"Filename is required for file {idx}"
                )

            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in [".png", ".jpg", ".jpeg", ".heic", ".heif"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_ext}. Use PNG, JPG, JPEG, HEIC, or HEIF.",
                )

            temp_path = os.path.join(
                settings.temp_upload_dir, f"{job_id}_{idx}{file_ext}"
            )

            # Save upload to temp
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Convert HEIC to PNG if needed
            if file_ext in [".heic", ".heif"]:
                try:
                    from PIL import Image
                    from pillow_heif import register_heif_opener

                    register_heif_opener()
                    img = Image.open(temp_path)

                    # Convert to PNG for processing
                    png_path = os.path.join(
                        settings.temp_upload_dir, f"{job_id}_{idx}.png"
                    )
                    img.save(png_path, format="PNG")

                    # Remove original HEIC file and use PNG
                    os.remove(temp_path)
                    temp_path = png_path
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to convert HEIC image: {str(e)}",
                    )

            # Validate file is a real image
            try:
                from PIL import Image

                with Image.open(temp_path) as img:
                    img.verify()  # Verify it's a valid image
                # Note: verify() invalidates the image, so we don't keep it open
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid image file: {str(e)}"
                )

            temp_paths.append(temp_path)

        # For conjunto, prepare metadata
        conjunto_pieces = None
        if garment_type == "Conjunto":
            conjunto_pieces = {
                "piece1_type": piece1_type,
                "piece2_type": piece2_type,
                "piece3_type": piece3_type,
            }

        # Generate using Engine
        # If single file, pass as string; if multiple, pass as list
        input_paths = temp_paths[0] if len(temp_paths) == 1 else temp_paths

        result_path_or_url = engine.generate_lifestyle_photo(
            input_paths,
            environment=env,
            activity="posing for a lifestyle catalog",
            garment_number=garment_number,
            garment_type=garment_type,
            position=position,
            conjunto_pieces=conjunto_pieces,
            feedback=feedback,
        )

        # Always return file (GCS disabled - using Drive for permanent storage)
        if not os.path.exists(result_path_or_url):
            raise HTTPException(
                status_code=500, detail="Generated image file not found"
            )

        return FileResponse(
            path=result_path_or_url,
            media_type="image/png",
            filename=f"cabide_{job_id}.png",
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Generation failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Engine Error: {str(e)}")
    finally:
        # Clean up all temp files
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)


@app.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check with actual connectivity verification.
    Tests Gemini API only (GCS disabled - using Drive for storage).
    """
    checks = {"gemini": False, "storage": True}

    # Check Gemini API
    try:
        genai.configure(api_key=settings.gemini_api_key)
        # Quick test - just check if we can list models
        list(genai.list_models())
        checks["gemini"] = True
    except Exception as e:
        logger.warning(f"Gemini health check failed: {e}")

    # Storage check - always healthy (local + Drive)
    checks["storage"] = True

    status = "healthy" if all(checks.values()) else "degraded"

    return HealthResponse(
        status=status,
        model="gemini-3-pro-image-preview",
        storage_mode=settings.storage_mode,
    )


@app.get("/oauth/callback")
async def oauth_callback(
    code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None
):
    """
    OAuth callback endpoint for Google authentication.
    Redirects user with code to complete authentication in Streamlit app.
    """
    from fastapi.responses import HTMLResponse

    if error:
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <h1>❌ Erro na autenticação</h1>
                    <p>Erro: {error}</p>
                    <p>Feche esta janela e tente novamente.</p>
                </body>
            </html>
            """,
            status_code=400,
        )

    if not code:
        return HTMLResponse(
            content="""
            <html>
                <body>
                    <h1>❌ Código de autorização não encontrado</h1>
                    <p>Feche esta janela e tente novamente.</p>
                </body>
            </html>
            """,
            status_code=400,
        )

    # Show success page with code that user can copy
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>✅ Autenticação Bem-Sucedida</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 50px auto;
                        padding: 20px;
                        text-align: center;
                    }}
                    .code-box {{
                        background: #f5f5f5;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                        word-break: break-all;
                        font-family: monospace;
                        font-size: 14px;
                    }}
                    button {{
                        background: #4CAF50;
                        color: white;
                        padding: 15px 32px;
                        font-size: 16px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }}
                    button:hover {{
                        background: #45a049;
                    }}
                </style>
            </head>
            <body>
                <h1>✅ Autenticação Bem-Sucedida!</h1>
                <p>Copie o código abaixo e cole no app Cabide AI:</p>
                <div class="code-box" id="authCode">{code}</div>
                <button onclick="copyCode()">📋 Copiar Código</button>
                <p style="margin-top: 30px; color: #666;">Você pode fechar esta janela após copiar o código.</p>
                <script>
                    function copyCode() {{
                        const code = document.getElementById('authCode').textContent;
                        navigator.clipboard.writeText(code).then(function() {{
                            alert('✅ Código copiado!');
                        }}, function() {{
                            alert('❌ Erro ao copiar. Copie manualmente.');
                        }});
                    }}
                </script>
            </body>
        </html>
        """
    )
