# Cabide AI

[![CI](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/ci.yml)
[![Deploy](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/deploy.yml/badge.svg)](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/deploy.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered professional fashion catalog generator using Google Gemini 3 Pro Vision. Upload clothing photos and generate professional model images with customizable environments and poses.

## ✨ Features

- **AI-Powered Image Generation**: Uses Google Gemini 3 Pro Vision to generate professional model photos
- **Flexible Environments**: Street, park, beach, forest, office, congress hall, medical office, luxury hotel
- **Customizable Poses**: Walking, checking phone, holding coffee, smiling, presenting, attending clients
- **OAuth Authentication**: Secure Google OAuth 2.0 integration
- **Google Drive Backup**: Automatic upload of generated images to Google Drive
- **Cloud-Native**: Backend on Cloud Run (São Paulo), Frontend on Streamlit Cloud

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with billing enabled
- Google Gemini API Key ([Get here](https://aistudio.google.com/app/apikey))
- uv package manager ([Install guide](https://docs.astral.sh/uv/))

### Local Development Setup

#### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/arthurcornelio88/cabide-ai.git
cd cabide-ai

# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

#### 2. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
# Minimum required:
GEMINI_API_KEY=your_api_key_here
STORAGE_MODE=local
GDRIVE_FOLDER_ID=your_folder_id_here  # Optional
```

See [Environment Variables Guide](#-environment-variables) for detailed configuration.

#### 3. Set Up OAuth (Required for Google Drive)

Download OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Create OAuth 2.0 Client ID (Web application type)
2. Add authorized redirect URIs:
   - `http://localhost:8080` (for local development)
   - `https://your-backend.run.app/oauth/callback` (for production)
3. Download JSON and save as `client_secret.json` in project root

See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed OAuth setup instructions.

#### 4. Run Locally

**Option A: Run frontend and backend separately**

```bash
# Terminal 1: Run backend API
uvicorn src.api:app --reload --port 8000

# Terminal 2: Run frontend UI
streamlit run src/app.py
```

**Option B: Run with Docker Compose**

```bash
# Build and start all services
docker-compose up --build

# Access:
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 📦 Production Deployment

### Backend (Cloud Run - São Paulo Region)

#### 1. Set Up GCP Infrastructure

```bash
# Run the automated setup script
bash scripts/setup_brazil_infra.sh
```

This script:
- ✅ Enables required Google Cloud APIs
- ✅ Creates Artifact Registry in `southamerica-east1` (São Paulo)
- ✅ Deploys Cloud Run service
- ✅ Configures public access for OAuth callback endpoint
- ✅ Sets up IAM permissions

#### 2. Configure GitHub Secrets

```bash
# Sync secrets to GitHub (requires GitHub CLI)
bash scripts/sync-secrets.sh
```

Required GitHub Secrets:
- `GEMINI_API_KEY`
- `GDRIVE_FOLDER_ID`
- `GCP_PROJECT_ID`
- `GCP_SERVICE_ACCOUNT` (JSON content from `gcp-service-account.json`)

#### 3. Deploy via GitHub Actions

Push to `main` branch to trigger automatic deployment:

```bash
git push origin main
```

The [deploy workflow](.github/workflows/deploy.yml) will:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Inject environment variables

### Frontend (Streamlit Cloud)

#### 1. Create Streamlit Cloud App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set main file path: `src/app.py`
4. Set Python version: `3.11`

#### 2. Configure Secrets

Add to Streamlit Cloud > Settings > Secrets:

```toml
# Required
GEMINI_API_KEY = "your_api_key"
BACKEND_URL = "https://your-backend.run.app"

# OAuth credentials (content of client_secret.json)
CLIENT_SECRET_JSON = '{"web":{"client_id":"...","client_secret":"...","redirect_uris":[...]}}'

# Optional: Google Drive integration
GDRIVE_FOLDER_ID = "your_folder_id"
GCP_SERVICE_ACCOUNT_JSON = '{"type":"service_account",...}'
```

#### 3. Deploy

Click "Deploy" in Streamlit Cloud dashboard. The app will be live at:
```
https://your-app-name.streamlit.app
```

## 🔐 Environment Variables

### Local Development (.env file)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio API key | `AIza...` |
| `STORAGE_MODE` | No | Storage mode (always `local`) | `local` |
| `GDRIVE_FOLDER_ID` | No | Google Drive folder for backups | `1UmBY12N...` |
| `GCP_SERVICE_ACCOUNT_JSON` | No | Service account JSON (or use file) | `{"type":"service_account",...}` |
| `GDRIVE_USER_EMAIL` | No | Email for domain-wide delegation | `user@example.com` |
| `BACKEND_URL` | No | Backend API URL (for production) | `https://api.run.app` |

**Note**: Instead of `GCP_SERVICE_ACCOUNT_JSON`, you can save credentials to `gcp-service-account.json` file (auto-detected).

### Streamlit Cloud (Secrets)

| Secret | Required | Description |
|--------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio API key |
| `BACKEND_URL` | ✅ Yes | Cloud Run backend URL |
| `CLIENT_SECRET_JSON` | ✅ Yes | OAuth client secret (JSON content) |
| `GDRIVE_FOLDER_ID` | No | Google Drive folder ID |
| `GCP_SERVICE_ACCOUNT_JSON` | No | Service account JSON for Drive |

### GitHub Secrets (CI/CD)

| Secret | Required | Description |
|--------|----------|-------------|
| `GCP_PROJECT_ID` | ✅ Yes | Google Cloud project ID |
| `GCP_SERVICE_ACCOUNT` | ✅ Yes | Service account JSON (entire file) |
| `GEMINI_API_KEY` | ✅ Yes | Gemini API key |
| `GDRIVE_FOLDER_ID` | No | Google Drive folder ID |

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_engine.py -v

# Run linting
uv run ruff check .
uv run ruff format .

# Run security scan
bandit -r src/
safety check
```

### Local CI Testing with Act

Test GitHub Actions workflows locally:

```bash
# Install act
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run specific jobs
act pull_request -j test
act pull_request -j lint
act pull_request -j security
```

## 📁 Project Structure

```
cabide-ai/
├── src/
│   ├── api.py              # FastAPI backend with OAuth protection
│   ├── app.py              # Streamlit frontend UI
│   ├── auth_ui.py          # OAuth authentication UI components
│   ├── oauth_helper.py     # OAuth token management
│   ├── engine.py           # Gemini AI image generation engine
│   ├── driver_service.py   # Google Drive upload service
│   ├── api_client.py       # Backend API client
│   └── config.py           # Centralized configuration (Pydantic)
├── tests/
│   ├── test_api.py         # API endpoint tests
│   ├── test_engine.py      # AI engine tests
│   └── test_config.py      # Configuration tests
├── scripts/
│   ├── setup_brazil_infra.sh  # GCP infrastructure setup
│   └── sync-secrets.sh        # GitHub secrets synchronization
├── .github/workflows/
│   ├── ci.yml              # Tests, linting, security scanning
│   └── deploy.yml          # Cloud Run deployment
├── Dockerfile.backend      # Backend container image
├── Dockerfile.frontend     # Frontend container image (Docker Compose)
├── docker-compose.yml      # Local development with Docker
├── pyproject.toml          # Python dependencies (uv format)
├── .env.example            # Environment variables template
└── PROMPT_TEMPLATES.md     # AI prompt templates
```

## 🏗️ Architecture

```
┌─────────────────────┐
│  Streamlit Cloud    │  Frontend (Free Tier)
│  (Frontend UI)      │  - OAuth authentication
│                     │  - Image upload interface
└──────────┬──────────┘  - Result display
           │
           │ HTTPS
           │
┌──────────▼──────────┐
│   Cloud Run API     │  Backend (São Paulo)
│   (FastAPI)         │  - OAuth token validation
│                     │  - Image generation
└──────────┬──────────┘  - Google Drive upload
           │
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌────▼─────┐
│ Gemini │   │  Google  │
│   AI   │   │  Drive   │
└────────┘   └──────────┘
```

### Technology Stack

- **Backend**: FastAPI, Pydantic v2, Google Gemini SDK
- **Frontend**: Streamlit, OAuth 2.0
- **AI**: Google Gemini 3 Pro Vision (gemini-1.5-pro)
- **Storage**: Local filesystem + Google Drive backup
- **Infrastructure**: Cloud Run (São Paulo), Streamlit Cloud
- **CI/CD**: GitHub Actions, Docker, Artifact Registry

## 🔐 Security

### OAuth 2.0 Authentication

- All `/generate` endpoints protected with OAuth token validation
- Tokens validated against Google's API on every request
- Only authorized test users can generate images (configured in Google Console)

### Public Endpoint Security

- `/oauth/callback`: Public (required for OAuth flow)
- `/health`: Public (no sensitive data)
- `/generate`: Protected (requires valid Bearer token)

### Best Practices

- ✅ Secrets stored in GitHub Secrets and Streamlit Cloud Secrets
- ✅ No credentials in source code or `.env` committed
- ✅ Security scanning with Bandit and Safety in CI
- ✅ Token validation on every protected request

## 🌍 Optimized for Brazil

- **Cloud Run Region**: `southamerica-east1` (São Paulo)
- **Artifact Registry**: `southamerica-east1`
- **Expected Latency**: < 50ms for Brazilian users

## 💰 Cost Estimation

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Streamlit Cloud | Free | $0 |
| Cloud Run | Pay-per-use | $5-10/month |
| Gemini API | Pay-per-use | $5-10/month |
| Artifact Registry | Storage | < $1/month |
| **Total** | | **$10-20/month** |

## 📝 Additional Documentation

- [Prompt Templates](PROMPT_TEMPLATES.md) - AI prompt customization
- [License](LICENSE) - MIT License details

## 🚀 Releases

This project uses semantic versioning (MAJOR.MINOR.PATCH). To create a new release:

```bash
# Create a new release tag
./scripts/create-release.sh 1.2.0 "Add new features"

# Push to trigger deployment
git push origin main && git push origin v1.2.0
```

The release workflow will automatically:
- Create a GitHub Release with changelog
- Build and push Docker image with version tag
- Deploy backend to Cloud Run with version label

View all releases: [Releases Page](https://github.com/arthurcornelio88/cabide-ai/releases)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test locally
4. Run tests and linting: `pytest && ruff check .`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check [OAUTH_SETUP.md](OAUTH_SETUP.md) for authentication problems
- Review Cloud Run logs: `gcloud run logs read cabide-api --region=southamerica-east1`
