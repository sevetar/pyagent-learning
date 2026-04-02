# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project managed with uv, a fast Python package manager and project manager.

- Project name: pyagentdemo
- Python version: 3.12 (specified in `.python-version`)
- Package manager: uv
- Virtual environment: `.venv` (auto-created by uv)

## Development Setup

### Opening the project
Open the workspace file `pyAgentDemo.code-workspace` in VS Code to automatically:
- Use the correct Python interpreter from `.venv`
- Activate the virtual environment in terminals
- Apply project-specific settings

### First-time setup
```bash
uv sync  # Creates .venv and installs dependencies
```

## Common Commands

### Running the project
```bash
uv run main.py
```

### Managing dependencies
```bash
# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Sync dependencies (install/update based on pyproject.toml)
uv sync

# Remove a dependency
uv remove <package-name>
```

### Python environment
```bash
# Run a Python command in the project environment
uv run python <script.py>

# Run a Python module
uv run python -m <module>
```

## Project Structure

- `main.py` - Entry point of the application
- `pyproject.toml` - Project configuration and dependencies
- `.python-version` - Python version specification for uv
