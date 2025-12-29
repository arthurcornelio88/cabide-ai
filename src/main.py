import argparse
import logging
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from engine import FashionEngine

# --- Batch Settings ---
class BatchSettings(BaseSettings):
    input_dir: Path = Field(default=Path("inputs/clothes"))
    output_dir: Path = Field(default=Path("outputs"))
    storage_mode: str = "local" # Default to local for CLI usage

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CabideBatchCLI")

class BatchProcessor:
    def __init__(self, settings: BatchSettings):
        self.settings = settings
        self.engine = FashionEngine()
        if self.settings.storage_mode == "local":
            self.settings.output_dir.mkdir(parents=True, exist_ok=True)

    def process_all(self, environment: str):
        supported = (".png", ".jpg", ".jpeg")
        files = [f for f in self.settings.input_dir.iterdir() if f.suffix.lower() in supported]

        if not files:
            logger.warning("No images found to process.")
            return

        logger.info(f"Processing {len(files)} items in {self.settings.storage_mode} mode.")

        for garment in files:
            try:
                # The result will be a local path or a GCS URL
                result = self.engine.generate_lifestyle_photo(
                    str(garment),
                    environment=environment,
                    activity="walking in nature"
                )
                logger.info(f"Done [{garment.name}] -> {result}")
            except Exception as e:
                logger.error(f"Error processing {garment.name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cabide AI Batch Engine")
    parser.add_argument("--env", default="forest", help="Scene environment")
    args = parser.parse_args()

    # Load from .env or ENV VARS
    config = BatchSettings()
    processor = BatchProcessor(config)
    processor.process_all(environment=args.env)
