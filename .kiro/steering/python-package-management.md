---
inclusion: always
---

# Python Package Management Guidelines

## Package Installation

**ALWAYS use `uv pip install` instead of `pip install` for this project.**

This project uses `uv` as the Python package manager for faster and more reliable dependency management.

### Correct Commands:
- ✅ `uv pip install package-name`
- ✅ `uv pip install "package-name[extras]"`
- ✅ `uv pip install -r requirements.txt`

### Incorrect Commands:
- ❌ `pip install package-name`
- ❌ `python -m pip install package-name`

### Examples:
```bash
# Install a single package
uv pip install fastapi

# Install with extras
uv pip install "pydantic[email]"

# Install from requirements
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -r requirements-dev.txt
```

## Why uv?
- Faster package resolution and installation
- Better dependency conflict resolution
- More reliable virtual environment management
- Compatible with pip but with improved performance

## Virtual Environment
The project uses a virtual environment managed by uv. Always ensure you're in the correct environment before installing packages.