# CloudGuard API

The FastAPI service follows the required layering: route/controller → service → repository → data layer. Phase 1 exposes only the infrastructure health contract.

## Host development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
ruff check app tests
mypy app
```
