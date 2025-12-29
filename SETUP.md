# Development Setup

This guide explains how to set up the Cabide AI project for development using `uv`.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Sync dependencies

This automatically creates a virtual environment and installs all dependencies:

```bash
uv sync
```

This command:
- Creates a `.venv` directory with a virtual environment
- Installs all dependencies from `pyproject.toml`
- Installs the `cabide-ai` package in editable mode
- Makes absolute imports like `from src.engine import FashionEngine` work properly

### 3. Set up environment variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Running the Application

**IMPORTANT:** Always use `uv run` to execute commands. This ensures:
- The correct virtual environment is used
- All imports work properly
- No `ModuleNotFoundError` issues

### Streamlit UI (Frontend)

```bash
uv run streamlit run src/app.py
```

### FastAPI Backend

```bash
uv run uvicorn src.api:app --reload --port 8000
```

### Batch Processing CLI

```bash
uv run python -m src.main --env forest
```

## Running Tests

```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov=src

# Run tests without coverage
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_api.py -v
```

## Adding New Dependencies

```bash
# Add a production dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

## Docker Build

The Dockerfiles are configured to use `uv` and install the package properly:

```bash
# Build frontend
docker build -f Dockerfile.frontend -t cabide-frontend .

# Build backend
docker build -f Dockerfile.backend -t cabide-backend .
```

## Project Structure

```
cabide-ai/
├── src/
│   ├── __init__.py         # Makes src a Python package
│   ├── api.py              # FastAPI backend
│   ├── app.py              # Streamlit frontend
│   ├── engine.py           # Core AI engine
│   ├── config.py           # Configuration management
│   ├── api_client.py       # API client for frontend
│   ├── driver_service.py   # Google Drive integration
│   └── main.py             # CLI batch processor
├── tests/
│   ├── test_api.py
│   └── test_config.py
├── pyproject.toml          # Project metadata and dependencies
├── pytest.ini              # Pytest configuration
├── uv.lock                 # Lockfile for reproducible builds
└── .env.example            # Example environment variables
```

## How UV Works

`uv` is a fast Python package manager that:
- Automatically manages virtual environments
- Uses a lockfile (`uv.lock`) for reproducible builds
- Makes the project installable as a package (editable mode)
- Ensures absolute imports like `from src.engine import ...` work correctly

When you run `uv sync`, it:
1. Creates a `.venv` directory if it doesn't exist
2. Installs all dependencies from `pyproject.toml`
3. Installs your project in editable mode
4. Makes the `src` package importable

## Troubleshooting

### ModuleNotFoundError: No module named 'src'

**Solution:** Always use `uv run` before your commands:
```bash
# ❌ Wrong
streamlit run src/app.py

# ✅ Correct
uv run streamlit run src/app.py
```

### Tests pass but application fails to import

**Solution:** Make sure you're using `uv run` to execute the application.

### Import errors in Docker

**Solution:** The Dockerfiles already include the proper `uv` setup. Rebuild your containers if needed.

### Want to use the virtual environment directly?

If you prefer to activate the virtual environment:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
# Now you can run commands without 'uv run'
streamlit run src/app.py
```
