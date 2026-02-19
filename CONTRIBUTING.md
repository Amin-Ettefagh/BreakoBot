# Contributing

Thanks for your interest in contributing.

## Quick Start
1. Fork the repo and create your branch from `main`.
2. Create a virtual environment and install dependencies:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
3. Run formatting and linting:
```
ruff format .
ruff check .
```
4. Run tests:
```
pytest
```
5. Open a PR with a clear description of your changes.

## Code Style
- Follow Ruff formatting and linting rules.
- Keep functions small and testable.
- Add docstrings to public functions/classes.

## Reporting Bugs
Open an issue with steps to reproduce, expected behavior, and actual behavior.

## Security Issues
Please do not open public issues for security vulnerabilities.
Follow the guidance in `SECURITY.md`.
