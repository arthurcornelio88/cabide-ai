import argparse
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

from src.config import Settings, get_settings
from src.engine import FashionEngine

# --- Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CabideBatchCLI")


def extract_metadata_from_filename(
    filename: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract garment number and type from filename.

    Examples:
        "100_20251229.HEIC" -> ("100", None)
        "45_pantalon_20251229.HEIC" -> ("45", "pantalon")
        "00_vestidofesta_back_20251229.HEIC" -> ("00", "vestidofesta")

    Returns:
        (garment_number, garment_type)
    """
    # Remove extension
    name = Path(filename).stem

    # Pattern: {number}_{type}_{position}_{timestamp} or variations
    # Match number at start (1-3 digits)
    number_match = re.match(r"^(\d+)_", name)
    if not number_match:
        return (None, None)

    garment_number = number_match.group(1)

    # Try to extract type (after number, before timestamp/position)
    # Known types: vestidofesta, vestido, calca, pantalon, saia, veste, echarpe, bracelete, sapato
    type_pattern = r"^\d+_(vestidofesta|vestido|calca|pantalon|saia|veste|echarpe|bracelete|sapato)"
    type_match = re.search(type_pattern, name.lower())

    garment_type = type_match.group(1) if type_match else None

    return (garment_number, garment_type)


class BatchProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = FashionEngine()
        if self.settings.storage_mode == "local":
            self.settings.output_dir.mkdir(parents=True, exist_ok=True)

    def process_all(self, environment: str):
        supported = (".png", ".jpg", ".jpeg", ".heic", ".heif")
        files = [
            f
            for f in self.settings.input_dir.iterdir()
            if f.suffix.lower() in supported
        ]

        if not files:
            logger.warning("No images found to process.")
            return

        logger.info(
            f"Processing {len(files)} items in {self.settings.storage_mode} mode."
        )

        for garment in files:
            try:
                # Extract metadata from filename
                garment_number, garment_type = extract_metadata_from_filename(
                    garment.name
                )
                logger.info(
                    f"Processing {garment.name} - Number: {garment_number}, Type: {garment_type}"
                )

                # Validate metadata before processing
                if not garment_number or not garment_type:
                    logger.error(
                        f"Skipping {garment.name}: Missing metadata (number={garment_number}, type={garment_type})"
                    )
                    continue

                # Generate with metadata
                result = self.engine.generate_lifestyle_photo(
                    str(garment),
                    environment=environment,
                    activity="walking in nature",
                    garment_number=garment_number,
                    garment_type=garment_type,
                )
                logger.info(f"Done [{garment.name}] -> {result}")
            except Exception as e:
                logger.error(f"Error processing {garment.name}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cabide AI Batch Engine")
    parser.add_argument("--env", default="forest", help="Scene environment")
    parser.add_argument(
        "--single", type=str, help="Process only a single image file (path to image)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: process only the first image found",
    )
    parser.add_argument(
        "--number", type=str, help="Garment number (optional, overrides auto-detection)"
    )
    parser.add_argument(
        "--type", type=str, help="Garment type (optional, overrides auto-detection)"
    )
    args = parser.parse_args()

    # Load from .env or ENV VARS
    config = get_settings()

    if args.single:
        # Process single specific file
        single_file = Path(args.single)
        if not single_file.exists():
            logger.error(f"File not found: {args.single}")
            exit(1)

        # Extract or use provided metadata
        if args.number and args.type:
            garment_number, garment_type = args.number, args.type
            logger.info(
                f"Using provided metadata - Number: {garment_number}, Type: {garment_type}"
            )
        else:
            garment_number, garment_type = extract_metadata_from_filename(
                single_file.name
            )
            logger.info(
                f"Extracted from filename - Number: {garment_number}, Type: {garment_type}"
            )

        logger.info(f"Processing single file: {single_file.name}")

        # Validate metadata
        if not garment_number or not garment_type:
            logger.error(
                f"Missing required metadata: number={garment_number}, type={garment_type}"
            )
            logger.error(
                "Please provide both --number and --type, or use a filename like: 42_pantalon_20251229.HEIC"
            )
            exit(1)

        engine = FashionEngine()
        try:
            result = engine.generate_lifestyle_photo(
                str(single_file),
                environment=args.env,
                activity="walking in nature",
                garment_number=garment_number,
                garment_type=garment_type,
            )
            logger.info(f"Done [{single_file.name}] -> {result}")
        except Exception as e:
            logger.error(f"Error processing {single_file.name}: {e}")
    elif args.test:
        # Test mode: process only first image
        supported = (".png", ".jpg", ".jpeg", ".heic", ".heif")
        files = [f for f in config.input_dir.iterdir() if f.suffix.lower() in supported]

        if not files:
            logger.warning("No images found to process.")
            exit(1)

        test_file = files[0]

        # Extract or use provided metadata
        if args.number and args.type:
            garment_number, garment_type = args.number, args.type
            logger.info(
                f"Using provided metadata - Number: {garment_number}, Type: {garment_type}"
            )
        else:
            garment_number, garment_type = extract_metadata_from_filename(
                test_file.name
            )
            logger.info(
                f"Extracted from filename - Number: {garment_number}, Type: {garment_type}"
            )

        logger.info(f"Test mode: Processing only first image: {test_file.name}")

        # Validate metadata
        if not garment_number or not garment_type:
            logger.error(
                f"Missing required metadata: number={garment_number}, type={garment_type}"
            )
            logger.error(
                "Please provide both --number and --type, or use a filename like: 42_pantalon_20251229.HEIC"
            )
            exit(1)

        engine = FashionEngine()
        try:
            result = engine.generate_lifestyle_photo(
                str(test_file),
                environment=args.env,
                activity="walking in nature",
                garment_number=garment_number,
                garment_type=garment_type,
            )
            logger.info(f"Done [{test_file.name}] -> {result}")
        except Exception as e:
            logger.error(f"Error processing {test_file.name}: {e}")
    else:
        # Batch mode: process all files
        processor = BatchProcessor(config)
        processor.process_all(environment=args.env)
