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
    "vestido com modelo": "vestidocommodelo",
    "saia": "saia",
    "calça": "calca",
    "calca": "calca",
    "camisa": "camisa",
    "blusa": "blusa",
    "colar": "colar",
    "sapato": "sapato",
    "chaussure": "sapato",
    "conjunto": "conjunto"
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
        if filename == "conjunto":
            template_name = "Virtual Model Conjunto"
        elif filename == "background_replacement":
            template_name = "Background Replacement"
        elif "vestidodefesta" in filename.lower():
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
        position: str = None,
        conjunto_pieces: dict = None,
        model_attributes: dict = None,
        feedback: str = None
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

        # Load appropriate template
        if garment_type and garment_type.lower() == "conjunto":
            raw_template = self._load_template("conjunto")
        elif garment_type and garment_type.lower() == "vestido com modelo":
            raw_template = self._load_template("background_replacement")
        else:
            raw_template = self._load_template(ref_filename)

        formatted_prompt = (raw_template
                           .replace("{{environment}}", final_env)
                           .replace("{{activity}}", final_act)
                           .replace("{{garment_type}}", normalized_type))

        # Add conjunto-specific hints
        conjunto_hint = ""
        if garment_type and garment_type.lower() == "conjunto" and conjunto_pieces:
            piece1 = conjunto_pieces.get("piece1_type", "")
            piece2 = conjunto_pieces.get("piece2_type", "")
            piece3 = conjunto_pieces.get("piece3_type", "")

            conjunto_hint = f"\n\nCONJUNTO COMPOSITION: Image 1 = {piece1}, Image 2 = {piece2}"
            if piece3:
                conjunto_hint += f", Image 3 = {piece3}"
            conjunto_hint += ". You must combine ALL these separate garment pieces into ONE coordinated outfit on the model."

        # Add position hint if provided and multiple images (for non-conjunto)
        position_hint = ""
        if not conjunto_hint:  # Only for non-conjunto items
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

        # Add model attributes hint if provided
        model_hint = ""
        if model_attributes:
            attr_parts = []

            # Map Portuguese to English for the AI
            attr_mapping = {
                "Baixa": "short height",
                "Média": "average height",
                "Alta": "tall height",
                "Esguia": "slender body type",
                "Plus Size": "plus size body type",
                "Pele Clara": "fair skin tone",
                "Pele Média": "medium skin tone",
                "Pele Morena": "tan skin tone",
                "Pele Escura": "dark skin tone",
                "Pele Negra": "black skin tone",
                "Curto": "short hair",
                "Médio": "medium-length hair",
                "Longo": "long hair",
                "Liso": "straight hair",
                "Ondulado": "wavy hair",
                "Cacheado": "curly hair",
                "Crespo": "coily/kinky hair",
                "Loiro": "blonde hair",
                "Castanho": "brown hair",
                "Ruivo": "red hair",
                "Preto": "black hair",
                "Grisalho": "gray hair",
                "Solto": "hair down",
                "Preso": "hair tied up",
                "Coque": "hair in a bun",
                "Rabo de Cavalo": "hair in a ponytail"
            }

            for key, value in model_attributes.items():
                if value:  # Only include non-empty attributes
                    english_value = attr_mapping.get(value, value.lower())
                    attr_parts.append(english_value)

            if attr_parts:
                model_hint = "\n\nMODEL ATTRIBUTES: " + ", ".join(attr_parts) + "."

        final_prompt = formatted_prompt + conjunto_hint + position_hint + model_hint

        # Add user feedback if provided (for regeneration/improvement)
        if feedback:
            if conjunto_pieces:
                # For conjunto with feedback, emphasize it's ONE person wearing ALL pieces
                feedback_instruction = f"\n\nUSER FEEDBACK FOR IMPROVEMENT: {feedback}\nIMPORTANT: Generate ONE SINGLE PERSON wearing ALL the garment pieces shown (upper piece, lower piece, and shoes if provided) in a complete outfit. Incorporate the feedback while maintaining garment fidelity and quality."
            else:
                feedback_instruction = f"\n\nUSER FEEDBACK FOR IMPROVEMENT: {feedback}\nPlease incorporate this feedback while maintaining all other quality requirements and garment fidelity."
            final_prompt = final_prompt + feedback_instruction

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

        # Special filename format for conjunto
        if garment_type.lower() == "conjunto" and conjunto_pieces:
            piece1 = self._normalize_garment_type(conjunto_pieces.get("piece1_type", ""))
            piece2 = self._normalize_garment_type(conjunto_pieces.get("piece2_type", ""))
            piece3 = conjunto_pieces.get("piece3_type")

            # Format: cabide_conjunto_100-camisa-27-calca-18-veste.png
            filename_parts = [f"cabide_conjunto_{garment_number}-{piece1}"]

            # For now, using same number for all pieces (can be enhanced later)
            filename_parts.append(f"-{garment_number}-{piece2}")

            if piece3:
                piece3_norm = self._normalize_garment_type(piece3)
                filename_parts.append(f"-{garment_number}-{piece3_norm}")

            output_filename = "".join(filename_parts) + ".png"
        else:
            normalized_type = self._normalize_garment_type(garment_type)
            output_filename = f"cabide_{garment_number}_{normalized_type}.png"

        logger.info(f"Output filename: {output_filename}")

        result_path = self._save_image(generated_pil, output_filename)
        logger.info(f"Image saved successfully: {result_path}")
        return result_path
