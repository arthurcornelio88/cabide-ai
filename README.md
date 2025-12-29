# 👗 Cabide AI: Professional Fashion Catalog Generator

A high-fidelity fashion image generation pipeline designed for professional clothing stores. This project uses **Gemini 3 Pro Image (Nano Banana Pro)** to transform simple product photos into professional editorial content.

## 🌍 Hybrid Architecture (France 🇫🇷 / Brazil 🇧🇷)
- **Engine:** Python-based multimodal processing.
- **Backend:** FastAPI with Pydantic V2 validation.
- **Frontend:** Streamlit optimized for mobile/desktop usage in Brazil.
- **Storage:** Hybrid logic (Local for Dev / GCS in `southamerica-east1` for Prod).
- **Drive Integration:** Automatic backup to Google Drive via Service Account.

## 🛠 Tech Stack
- **Language:** Python 3.11+
- **Dependency Manager:** `uv`
- **Linting:** `Ruff`
- **Image Support:** PNG, JPG, JPEG, HEIC, HEIF (auto-converted)
- **Infrastructure:** Docker, Google Cloud Run, GCS, Artifact Registry.
- **CI/CD:** GitHub Actions.

## 🚀 Quick Start (Local Dev)

1. **Install Dependencies:**
```bash
# Install package in editable mode (required for imports to work)
pip install -e .

# Or using uv
uv pip install -e .
```

2. **Configure Environment:**
Create a `.env` file:
```env
GEMINI_API_KEY=your_key
STORAGE_MODE=local
GCS_BUCKET_NAME=<your-bucket-name>

```

3. **Run Tests:**
```bash
pytest tests/ -v --cov=src
```

4. **Run Batch Processor:**
```bash
python -m src.main --env forest
```

5. **Run UI:**
```bash
streamlit run src/app.py
```

> **Note:** See [SETUP.md](SETUP.md) for detailed setup instructions and troubleshooting.

## 📦 Deployment to Brazil

The deployment is automated via GitHub Actions.

1. **GitHub Secrets Required:**
* `GCP_PROJECT_ID`: Your Google Cloud Project ID.
* `GCP_SA_KEY`: JSON Key of a Service Account with Storage/Run/Registry permissions.
* `GEMINI_API_KEY`: Your Google AI Studio API Key (Paid Tier).
* `GCP_SERVICE_ACCOUNT_JSON`: Minified JSON of the Service Account (for Drive/GCS access in production).
* `GDRIVE_FOLDER_ID`: Google Drive folder ID for automatic backup uploads (optional but recommended).


2. **Push to Main:**
```bash
git add .
git commit -m "Deploying to Brazil region"
git push origin main

```

## 📂 Project Structure

* `src/config.py`: Unified configuration management with Pydantic v2 settings.
* `src/engine.py`: Core AI logic & multimodal garment handling.
* `src/api.py`: FastAPI implementation.
* `src/api_client.py`: HTTP client for frontend-to-backend communication.
* `src/app.py`: Streamlit UI for the end-user (supports both direct engine and API modes).
* `src/driver_service.py`: Google Drive upload management.
* `PROMPT_TEMPLATES.md`: Source of truth for AI instructions.

## 📝 TODOs & Future Improvements

* [x] Complexify parameters for list of garments (front/back).
* [x] Implement "vestidodefesta" specific environment logic.
* [x] Integrate Google Drive Service Account upload.
* [ ] Implement OAuth2 for multi-user Drive access.
* [ ] Add Video generation support via Veo 3.1.
