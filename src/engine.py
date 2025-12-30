import os
import uuid
import logging
import re
import random
from pathlib import Path
from io import BytesIO
from typing import Union, List, Optional

from PIL import Image
from google.cloud import storage
import google.generativeai as genai

# Register HEIC support for PIL
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIC support not available

from src.config import get_settings, Settings

logger = logging.getLogger("CabideEngine")

# Type normalization mapping (French/Portuguese → Portuguese)
TYPE_NORMALIZATION = {
    "pantalon": "calca",
    "veste": "veste",
    "écharpe": "echarpe",
    "echarpe": "echarpe",
    "bracelete": "bracelete",
    "vestido de festa": "vestidodefesta",
    "vestidofesta": "vestidodefesta",
    "vestido": "vestido",
    "saia": "saia",
    "calça": "calca",
    "calca": "calca",
    "camisa": "camisa",
    "sapato": "sapato",
    "chaussure": "sapato"
}

class FashionEngine:
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-3-pro-image-preview')

        if self.settings.storage_mode == "prod":
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.settings.gcs_bucket_name)
            logger.info("FashionEngine initialized in PROD mode with GCS")
        else:
            self.settings.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"FashionEngine initialized in LOCAL mode, output_dir={self.settings.output_dir}")

    def _normalize_garment_type(self, garment_type: Optional[str]) -> str:
        """Normalize garment type to Portuguese."""
        if not garment_type:
            return "piece"
        normalized = TYPE_NORMALIZATION.get(garment_type.lower(), garment_type.lower())
        logger.debug(f"Normalized garment type: '{garment_type}' → '{normalized}'")
        return normalized

    def _load_template(self, filename: str) -> str:
        """Determines template based on file content/name."""
        template_name = "Virtual Model Quotidien"
        if "vestidodefesta" in filename.lower():
            template_name = "Virtual Model Party"

        content = self.settings.templates_file.read_text()
        pattern = rf"## Template: {template_name}\n(.*?)(?=\n##|$)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _save_image(self, pil_image: Image.Image, filename: str) -> str:
        if self.settings.storage_mode == "prod":
            blob = self.bucket.blob(f"generated/{filename}")
            img_byte_arr = BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            blob.upload_from_string(img_byte_arr.getvalue(), content_type='image/png')
            return blob.public_url
        else:
            local_path = self.settings.output_dir / filename
            pil_image.save(local_path)
            return str(local_path.absolute())

    def generate_lifestyle_photo(
        self,
        garment_path: Union[str, List[str]],
        environment: str = None,
        activity: str = None,
        garment_number: str = None,
        garment_type: str = None,
        position: str = None
    ) -> str:
        # Handle single or list (front/back)
        paths = [garment_path] if isinstance(garment_path, str) else garment_path

        # Open images - handle both file paths and BytesIO objects
        garment_images = []
        for p in paths:
            if isinstance(p, (str, Path)):
                garment_images.append(Image.open(p))
            else:
                # Assume it's a file-like object (BytesIO)
                p.seek(0)  # Reset position to start
                garment_images.append(Image.open(p))

        # Check filename of the first image for "vestidodefesta" logic
        # Use default filename if input is not a path
        if isinstance(paths[0], (str, Path)):
            ref_filename = Path(paths[0]).name
        else:
            ref_filename = "garment.jpg"  # Default filename for BytesIO

        # Logic for random variables if not provided (Local/Batch mode)
        final_env = environment or random.choice(self.settings.environments)
        final_act = activity or random.choice(self.settings.activities)

        # Normalize and prepare garment type for template
        normalized_type = self._normalize_garment_type(garment_type) if garment_type else "garment"

        # Override environment if it's a party dress
        if "vestidodefesta" in ref_filename.lower() and not environment:
            final_env = "a gala ballroom"
            final_act = "holding a champagne glass"

        raw_template = self._load_template(ref_filename)
        formatted_prompt = (raw_template
                           .replace("{{environment}}", final_env)
                           .replace("{{activity}}", final_act)
                           .replace("{{garment_type}}", normalized_type))

        # Add position hint if provided and multiple images
        position_hint = ""
        if position and len(garment_images) > 1:
            if position.lower() in ["ambos", "both"]:
                position_hint = "\n\nNote: Image 1 shows the front view, Image 2 shows the back view."
        elif position and len(garment_images) == 1:
            position_map = {
                "frente": "front view",
                "costas": "back view"
            }
            view = position_map.get(position.lower(), "")
            if view:
                position_hint = f"\n\nNote: The image shows the {view} of the garment."

        final_prompt = formatted_prompt + position_hint

        # Multimodal call
        content_parts = [final_prompt] + garment_images

        try:
            logger.info("Calling Gemini API for image generation", extra={
                "environment": final_env,
                "activity": final_act,
                "garment_number": garment_number,
                "garment_type": garment_type
            })

            response = self.model.generate_content(content_parts)

            # Validate response
            if not response.candidates:
                logger.error("Gemini returned no candidates - response may have been blocked")
                raise ValueError("Gemini returned no candidates. Response may have been blocked.")

            candidate = response.candidates[0]
            logger.debug(f"Gemini response finish_reason: {candidate.finish_reason}")

            # Check if response has image attribute (old format)
            if hasattr(candidate, 'image') and candidate.image is not None:
                logger.info("Image received via legacy image attribute")
                generated_pil = candidate.image
            # Check if response has parts with inline_data (new format)
            elif hasattr(candidate.content, 'parts') and candidate.content.parts:
                # Extract image data from the response
                import base64
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        mime_type = getattr(part.inline_data, 'mime_type', 'unknown')
                        logger.debug(f"Found inline_data with mime_type: {mime_type}")

                        # The data is already in bytes format in the google.generativeai library
                        if isinstance(part.inline_data.data, bytes):
                            image_data = part.inline_data.data
                        elif isinstance(part.inline_data.data, str):
                            logger.debug("Decoding base64 string data")
                            image_data = base64.b64decode(part.inline_data.data)
                        else:
                            # Protobuf bytes field
                            logger.debug(f"Converting protobuf data type: {type(part.inline_data.data)}")
                            image_data = bytes(part.inline_data.data)

                        logger.info(f"Image received: {len(image_data)} bytes, mime_type={mime_type}")
                        image_buffer = BytesIO(image_data)
                        image_buffer.seek(0)
                        generated_pil = Image.open(image_buffer)
                        logger.info(f"Image decoded successfully: {generated_pil.format} {generated_pil.size}")
                        break
                else:
                    logger.error(f"Gemini response missing image data: {response}")
                    raise ValueError(
                        "Gemini did not return an image. This may be due to safety filters "
                        "or content policy violations."
                    )
            else:
                # Log the full response for debugging
                logger.error(f"Gemini response missing image: {response}")
                raise ValueError(
                    "Gemini did not return an image. This may be due to safety filters "
                    "or content policy violations."
                )

        except Exception as e:
            logger.error(f"Image generation failed: {e}", extra={
                "garment_number": garment_number,
                "garment_type": garment_type,
                "error_type": type(e).__name__
            })
            raise RuntimeError(f"Failed to generate image: {str(e)}") from e

        # Generate output filename with metadata (both number and type are now required)
        if not garment_number or not garment_type:
            raise ValueError(
                f"Both garment_number and garment_type are required. "
                f"Got: garment_number={garment_number}, garment_type={garment_type}"
            )

        normalized_type = self._normalize_garment_type(garment_type)
        output_filename = f"cabide_{garment_number}_{normalized_type}.png"
        logger.info(f"Output filename: {output_filename}")

        result_path = self._save_image(generated_pil, output_filename)
        logger.info(f"Image saved successfully: {result_path}")
        return result_path
