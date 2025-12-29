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
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("CabideEngine")

class EngineSettings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    storage_mode: str = "local"
    gdrive_folder_id: str = "your_shared_folder_id_here"
    gcp_service_account_json: str = os.getenv("GCP_SERVICE_ACCOUNT_JSON", "{}")
    gcs_bucket_name: str = "cabide-catalog-br"
    output_dir: Path = Path("outputs")
    templates_file: Path = Path("PROMPT_TEMPLATES.md")

    # Global random pools for batch processing
    environments: List[str] = ["forest", "park", "beach", "urban street", "luxury hotel"]
    activities: List[str] = ["walking", "checking phone", "holding a coffee", "smiling at the camera"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class FashionEngine:
    def __init__(self):
        self.settings = EngineSettings()
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

    # TODO: complexify parameters. garment_path could be a list of garments path.
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

        # TODO: needs to load "PROMPT_TEMPLATES.md" and parse it
        raw_template = self._load_template(ref_filename)
        formatted_prompt = raw_template.replace("{{environment}}", final_env).replace("{{activity}}", final_act)

        # Multimodal call
        content_parts = [formatted_prompt] + garment_images
        response = self.model.generate_content(content_parts)

        output_filename = f"cabide_{uuid.uuid4().hex[:8]}.png"
        generated_pil = response.candidates[0].image

        return self._save_image(generated_pil, output_filename)
