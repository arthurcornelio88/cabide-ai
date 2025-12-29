import os
import uuid
import logging
import re
import random
from pathlib import Path
from io import BytesIO
from typing import Union, List

from PIL import Image
from google.cloud import storage
import google.generativeai as genai

from src.config import get_settings, Settings

logger = logging.getLogger("CabideEngine")

class FashionEngine:
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        genai.configure(api_key=self.settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-3-pro-image-preview')

        if self.settings.storage_mode == "prod":
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.settings.gcs_bucket_name)
        else:
            self.settings.output_dir.mkdir(parents=True, exist_ok=True)

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
        activity: str = None
    ) -> str:
        # Handle single or list (front/back)
        paths = [garment_path] if isinstance(garment_path, str) else garment_path
        garment_images = [Image.open(p) for p in paths]

        # Check filename of the first image for "vestidodefesta" logic
        ref_filename = Path(paths[0]).name

        # Logic for random variables if not provided (Local/Batch mode)
        final_env = environment or random.choice(self.settings.environments)
        final_act = activity or random.choice(self.settings.activities)

        # Override environment if it's a party dress
        if "vestidodefesta" in ref_filename.lower() and not environment:
            final_env = "a gala ballroom"
            final_act = "holding a champagne glass"

        raw_template = self._load_template(ref_filename)
        formatted_prompt = raw_template.replace("{{environment}}", final_env).replace("{{activity}}", final_act)

        # Multimodal call
        content_parts = [formatted_prompt] + garment_images

        try:
            response = self.model.generate_content(content_parts)

            # Validate response
            if not response.candidates:
                raise ValueError("Gemini returned no candidates. Response may have been blocked.")

            if not hasattr(response.candidates[0], 'image') or response.candidates[0].image is None:
                # Log the full response for debugging
                logger.error(f"Gemini response missing image: {response}")
                raise ValueError(
                    "Gemini did not return an image. This may be due to safety filters "
                    "or content policy violations."
                )

            generated_pil = response.candidates[0].image

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise RuntimeError(f"Failed to generate image: {str(e)}") from e

        output_filename = f"cabide_{uuid.uuid4().hex[:8]}.png"
        return self._save_image(generated_pil, output_filename)
