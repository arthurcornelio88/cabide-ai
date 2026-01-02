# Cabide AI

[![CI](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/ci.yml)
[![Deploy](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/deploy.yml/badge.svg)](https://github.com/arthurcornelio88/cabide-ai/actions/workflows/deploy.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered professional fashion catalog generator using Google Gemini 3 Pro Image Preview. Upload clothing photos and generate professional model images with customizable environments and poses.

## ✨ Features

- **AI-Powered Image Generation**: Uses Google Gemini 3 Pro Image Preview (`gemini-3-pro-image-preview`) with optimized image processing
- **Cost-Optimized**: Automatic image preprocessing (1536px MEDIUM, JPEG 90%) reduces API costs by ~60%
- **Flexible Environments**: Street, park, beach, forest, office, congress hall, medical office, luxury hotel
- **Customizable Poses**: Walking, checking phone, holding coffee, smiling, presenting, attending clients
- **OAuth Authentication**: Secure Google OAuth 2.0 integration
- **Google Drive Backup**: Automatic upload of generated images to Google Drive
- **Cloud-Native**: Backend on Cloud Run (São Paulo), Frontend on Streamlit Cloud
- **Local Testing**: Development endpoint `/generate/test` for testing without OAuth

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

# Optional (for Google Drive integration):
GDRIVE_FOLDER_ID=your_folder_id_here

# Optional (for local testing without OAuth):
ENABLE_TEST_ENDPOINT=true
```

See [Environment Variables Guide](#-environment-variables) for detailed configuration.

#### 3. Set Up OAuth (Required for Google Drive)

**Create OAuth 2.0 Credentials:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable required APIs:
   - Google Drive API
   - Google+ API (for user info)
3. Configure OAuth Consent Screen:
   - User Type: External
   - App name: `Cabide AI`
   - Add scopes: `drive.file`, `userinfo.email`, `userinfo.profile`
   - Add test users (your email and users who will access the app)
4. Create OAuth Client ID:
   - Application type: **Web application** (important!)
   - Name: `Cabide AI Web`
   - Authorized redirect URIs:
     - `http://localhost:8080` (for local development)
     - `https://your-backend.run.app/oauth/callback` (for production)
5. Download JSON and save as `client_secret.json` in project root

**For Streamlit Cloud deployment:**
- Add the entire content of `client_secret.json` as a secret named `CLIENT_SECRET_JSON`
- Format: Single-line JSON string (see [Streamlit Cloud section](#2-configure-secrets))

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

### Local Testing Without OAuth

For quick local testing without OAuth authentication, use the `/generate/test` endpoint:

```bash
# Enable test endpoint in .env
echo "ENABLE_TEST_ENDPOINT=true" >> .env

# Test with curl
curl -X POST "http://localhost:8000/generate/test" \
  -F "files=@path/to/image.jpg" \
  -F "env=beach" \
  -F "garment_number=1" \
  -F "garment_type=camisa" \
  -o output.png
```

**⚠️ Security Note**: The `/generate/test` endpoint is **disabled by default** in production. It should only be enabled for local development.

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
| `ENABLE_TEST_ENDPOINT` | No | Enable `/generate/test` endpoint (dev only) | `true` |

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

## 🛠️ Utility Scripts

The project includes helpful scripts in the `scripts/` directory:

### `scripts/setup_brazil_infra.sh`

Sets up complete GCP infrastructure optimized for Brazil (São Paulo region).

**What it does:**
- Enables required Google Cloud APIs (Cloud Run, Artifact Registry)
- Creates Artifact Registry repository for Docker images
- Deploys initial Cloud Run service with proper configuration
- Sets up IAM permissions for public OAuth callback access
- Configures environment variables

**Usage:**
```bash
# Make sure you're authenticated with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Run the script
bash scripts/setup_brazil_infra.sh
```

**Requirements:**
- `gcloud` CLI installed
- Active GCP project with billing enabled
- Service account JSON file: `gcp-service-account.json`

### `scripts/sync-secrets.sh`

Synchronizes environment variables from `.env` to GitHub repository secrets.

**What it does:**
- Reads variables from your local `.env` file
- Uploads them as GitHub Secrets using `gh` CLI
- Handles both string values and JSON file contents
- Useful for keeping CI/CD secrets in sync

**Usage:**
```bash
# Make sure GitHub CLI is authenticated
gh auth login

# Run the script
bash scripts/sync-secrets.sh
```

**Requirements:**
- `gh` CLI installed ([installation guide](https://cli.github.com/))
- `.env` file with required variables
- `gcp-service-account.json` file (for GCP_SERVICE_ACCOUNT secret)

### `scripts/create-release.sh`

Creates a new semantic version release with automatic version bumping.

**What it does:**
- Validates semantic versioning format (MAJOR.MINOR.PATCH)
- Updates version in `pyproject.toml` and `src/config.py`
- Creates annotated git tag
- Provides instructions for pushing and triggering deployment

**Usage:**
```bash
# Create a new release
./scripts/create-release.sh 1.2.0 "Add new features and improvements"

# Push to trigger GitHub Actions release workflow
git push origin main && git push origin v1.2.0
```

**What happens after push:**
- GitHub Actions creates a release with changelog
- Builds and pushes Docker image with version tag
- Deploys backend to Cloud Run with version label

## 🧪 Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v
pytest tests/test_config.py -v

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
│   ├── test_config.py      # Configuration tests
│   └── conftest.py         # Pytest fixtures
├── scripts/
│   ├── setup_brazil_infra.sh   # GCP infrastructure setup
│   ├── sync-secrets.sh         # GitHub secrets synchronization
│   └── create-release.sh       # Release version management
├── .github/workflows/
│   ├── ci.yml              # Tests, linting, security scanning
│   ├── deploy.yml          # Cloud Run deployment
│   └── release.yml         # Automated releases with tags
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

- **Backend**: FastAPI, Pydantic v2, google-genai SDK v1.55.0
- **Frontend**: Streamlit, OAuth 2.0
- **AI**: Google Gemini 3 Pro Image Preview (`gemini-3-pro-image-preview`)
- **Image Processing**: PIL/Pillow with HEIC support, automatic optimization (1536px MEDIUM, JPEG 90%)
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
- `/generate/test`: Disabled in production (enabled only with `ENABLE_TEST_ENDPOINT=true`)

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
| Gemini API | Pay-per-use | $3-6/month* |
| Artifact Registry | Storage | < $1/month |
| **Total** | | **$8-17/month** |

*After v1.2.0 image optimization: ~60% reduction in Gemini API costs through automatic image preprocessing (1536px MEDIUM resolution, JPEG quality 90%).

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

### Common Issues

**OAuth Authentication Problems:**
- See detailed setup in [OAuth Setup section](#3-set-up-oauth-required-for-google-drive)
- For local testing without OAuth, use `/generate/test` endpoint (see [Local Testing section](#local-testing-without-oauth))

**Deployment Issues:**
- Verify all GitHub Secrets are configured: `GCP_PROJECT_ID`, `GCP_SERVICE_ACCOUNT`, `GEMINI_API_KEY`
- Check Cloud Run logs: `gcloud run logs read cabide-api --region=southamerica-east1`

**Local Development:**
- Ensure `.env` file exists with `GEMINI_API_KEY` and `ENABLE_TEST_ENDPOINT=true`
- Install dependencies: `uv sync`

### Getting Help

- 📝 Open an [issue on GitHub](https://github.com/arthurcornelio88/cabide-ai/issues)
- 📖 Review the [OAuth Setup section](#3-set-up-oauth-required-for-google-drive)
- 🛠️ Check the [Utility Scripts section](#%EF%B8%8F-utility-scripts) for deployment tools
- 📊 Monitor Cloud Run metrics in [GCP Console](https://console.cloud.google.com/run)
