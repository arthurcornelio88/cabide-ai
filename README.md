# Cabide AI

AI-powered fashion catalog generator for Cabide da Ieie using Google Gemini 3 Pro.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud Project with billing enabled
- Docker (for local testing)
- GitHub CLI (optional, for secrets management)

### Local Development

```bash
# Install dependencies with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e .

# Copy .env.example to .env and fill in your credentials
cp .env.example .env

# Run the API locally
uvicorn src.api:app --reload

# Run the Streamlit UI locally
streamlit run src/app.py
```

## 📦 Deployment

### Infrastructure Setup

```bash
# Run the infrastructure setup script (creates GCP resources)
bash scripts/setup_brazil_infra.sh
```

This script will:
- ✅ Enable required Google Cloud APIs
- ✅ Create Artifact Registry repository in São Paulo region
- ✅ Create Cloud Run service for the backend
- ✅ Set up proper IAM permissions

### Secrets Management

```bash
# Sync secrets from .env to GitHub repository secrets
bash scripts/sync-secrets.sh
```

This automatically syncs:
- `GEMINI_API_KEY` - Google AI Studio API key
- `GDRIVE_FOLDER_ID` - Google Drive folder for catalog storage
- `GCP_PROJECT_ID` - Google Cloud project ID
- `GCP_SERVICE_ACCOUNT` - Service account JSON (from file)

### Architecture

- **Backend:** FastAPI on Cloud Run (São Paulo region)
- **Frontend:** Streamlit Cloud (free tier)
- **Storage:** Local filesystem + Google Drive backup
- **CI/CD:** GitHub Actions with automatic deployment

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Lint code
uv run ruff check .
uv run ruff format .

# Security scan
bandit -r src/
safety check
```

### Local CI Testing with Act

```bash
# Install act
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI jobs locally
act pull_request -j test
act pull_request -j lint
act pull_request -j security
```

## 📁 Project Structure

```
cabide-ai/
├── src/                    # Source code
│   ├── api.py             # FastAPI backend
│   ├── app.py             # Streamlit frontend
│   ├── engine.py          # Gemini AI engine
│   └── config.py          # Configuration management
├── scripts/               # Utility scripts
│   ├── setup_brazil_infra.sh   # GCP infrastructure setup
│   └── sync-secrets.sh         # GitHub secrets sync
├── tests/                 # Test suite
├── .github/workflows/     # CI/CD pipelines
│   ├── ci.yml            # Tests, lint, security
│   └── deploy.yml        # Cloud Run deployment
└── deploy.md             # Deployment checklist

```

## 🔐 Security

- OAuth 2.0 authentication for API endpoints
- Service account for Google Drive integration
- Secrets managed via GitHub Secrets (repo) and Streamlit Cloud (app)
- Security scanning with Bandit and Safety in CI

## 📝 Documentation

- [Deployment Guide](deploy.md) - Complete deployment checklist
- [Deployment Plan](DEPLOY_PLAN.md) - Architecture migration guide
- [TODO](TODO.md) - Project tasks and progress

## 🛠️ Scripts

### `scripts/setup_brazil_infra.sh`
Sets up complete GCP infrastructure in São Paulo region:
- Enables required APIs
- Creates Artifact Registry for Docker images
- Deploys initial Cloud Run service
- Idempotent (safe to run multiple times)

### `scripts/sync-secrets.sh`
Synchronizes environment variables from `.env` to GitHub repository secrets:
- Reads values from `.env` file
- Uploads to GitHub using `gh` CLI
- Handles both string and JSON file secrets
- Useful for keeping secrets in sync

## 🌍 Region & Performance

Optimized for Brazil:
- **Cloud Run:** `southamerica-east1` (São Paulo)
- **Artifact Registry:** `southamerica-east1`
- **Latency:** < 50ms for Brazilian users

## 💰 Cost Optimization

- Frontend on Streamlit Cloud (free)
- Backend on Cloud Run (pay-per-use)
- No GCS bucket costs (uses local + Drive)
- **Estimated:** $5-15/month

## 🤝 Contributing

1. Create a feature branch
2. Make changes and test locally
3. Run CI checks: `pytest && ruff check . && bandit -r src/`
4. Submit PR (CI must pass)

## 📄 License

Private project - All rights reserved.
