# UV Quick Reference

This project uses `uv` for all dependency management and execution.

## 🚀 Quick Start

```bash
# 1. Sync dependencies (first time setup)
uv sync

# 2. Run Streamlit UI
uv run streamlit run src/app.py

# 3. Run FastAPI backend
uv run uvicorn src.api:app --reload --port 8000

# 4. Run tests
uv run pytest tests/ -v --cov=src
```

## 📦 Dependency Management

```bash
# Add a production dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Update specific package
uv add package-name --upgrade
```

## 🧪 Testing

```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov=src

# Run specific test file
uv run pytest tests/test_api.py -v

# Run with less verbosity
uv run pytest tests/
```

## 🏃 Running Applications

```bash
# Streamlit frontend
uv run streamlit run src/app.py

# FastAPI backend (development)
uv run uvicorn src.api:app --reload --port 8000

# FastAPI backend (production)
uv run uvicorn src.api:app --host 0.0.0.0 --port 8000

# Batch processor CLI
uv run python -m src.main --env forest

# Python REPL with project context
uv run python
```

## 🔧 Other Useful Commands

```bash
# Show dependency tree
uv tree

# List installed packages
uv pip list

# Check for outdated packages
uv pip list --outdated

# Clean cache
uv cache clean

# Show UV version
uv --version
```

## ⚡ Why Always Use `uv run`?

Using `uv run` ensures:
- ✅ Correct virtual environment is activated
- ✅ All imports work (including `from src.engine import ...`)
- ✅ Dependencies are available
- ✅ No `ModuleNotFoundError` issues

## 🔄 Alternative: Activate Virtual Environment

If you prefer not to use `uv run` every time:

```bash
# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Now run commands normally
streamlit run src/app.py
pytest tests/ -v
uvicorn src.api:app --reload

# Deactivate when done
deactivate
```

## 🐛 Troubleshooting

### ModuleNotFoundError: No module named 'src'

```bash
# Make sure you're using uv run
uv run streamlit run src/app.py

# Or activate the virtual environment
source .venv/bin/activate
```

### Dependencies not found after adding them

```bash
# Re-sync dependencies
uv sync
```

### Virtual environment seems broken

```bash
# Remove and recreate
rm -rf .venv
uv sync
```
