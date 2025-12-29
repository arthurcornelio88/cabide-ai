import os
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import pillow_heif

# Enregistrement du support HEIF pour les photos iPhone
pillow_heif.register_heif_opener()

def extract_caption(image_path):
    """Extrait la description/légende des métadonnées EXIF."""
    try:
        img = Image.open(image_path)
        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                # Le champ "Légende" iOS est généralement mappé sur ImageDescription
                if tag_name == "ImageDescription":
                    return str(value).strip().replace(" ", "_")
    except Exception as e:
        print(f"Erreur lecture metadata pour {image_path}: {e}")
    return "sans_nom"

def process_images(input_dir, output_dir):
    # Setup des chemins
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    print(f"🚀 Début du traitement de : {input_path}")

    for file_path in input_path.iterdir():
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
            # 1. Extraction de la légende
            caption = extract_caption(file_path)

            # 2. Construction du nouveau nom
            # Format: {Legende}_{Timestamp}_{NomOriginal}.{Extension}
            new_name = f"{caption}_{timestamp}{file_path.suffix}"
            dest_path = output_path / new_name

            # 3. Copie du fichier
            shutil.copy2(file_path, dest_path)
            print(f"✅ {file_path.name} -> {new_name}")

if __name__ == "__main__":
    # Configure tes dossiers ici
    input_folder = "img/raw_images/input"
    output_folder = "img/raw_images/output"

    process_images(input_folder, output_folder)
