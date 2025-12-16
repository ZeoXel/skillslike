# Repository Guidelines

## Project Structure & Module Organization
- `skillslike/`: Core package (API in `api/`, routing in `router/`, agent logic in `agent/`, executors/storage/registry for tool and state handling, shared models in `models/`).
- `skills/`: YAML skill definitions and docs (`quickstart.md`); extend here when adding new skills.
- `tests/`: Pytest suite; add new unit/integration tests alongside the module under test. Ad-hoc scripts `test_api_direct.py` and `test_image_gen.py` are kept at repo root.
- `docs/`, `SUMMARY.md`, `ARCHITECTURE_VISUAL.md`: Architecture notes and contributor guides; update when behavior changes.
- `static/`, `css/`, `data/`, `examples/`: Frontend/static assets, sample payloads (`examples/basic_usage.py`, `api_client.py`), and stored files (`data/files/`).

## Build, Test, and Development Commands
- Install: `make install` (uses `uv sync` with Python 3.11).
- Format/Lint: `make format` (ruff format + autofix) then `make lint` (ruff + mypy strict).
- Tests: `make test` → `uv run pytest tests/ -v --cov=skillslike --cov-report=term-missing`.
- Run API locally: `make run` (hot reload on port 8000); lighter reload: `make dev`.
- Direct usage without make: `uv run <command>` (e.g., `uv run pytest tests/router/test_router.py`).

## Coding Style & Naming Conventions
- Python only; type hints are required (mypy strict, no untyped defs). Target version: 3.11.
- Ruff formatting with 100-char line target; prefer keeping lines <=100 even though E501 is ignored.
- Naming: modules/vars/functions in `snake_case`; classes in `PascalCase`; constants in `UPPER_SNAKE`.
- Keep functions focused and documented with concise docstrings where behavior is non-obvious; prefer dependency injection over globals.

## Testing Guidelines
- Use pytest (async supported); place new tests under `tests/` mirroring the package path (`tests/router/test_router.py` for `skillslike/router/...`).
- Name files `test_*.py` and tests `test_*`; include fixtures for API clients and mock external providers.
- Cover new code paths and error cases; `--cov=skillslike` runs by default—keep coverage steady or rising.
- For API changes, add request/response examples in `examples/` when useful and assert JSON schemas in tests.

## Commit & Pull Request Guidelines
- History is minimal; follow short, imperative subjects with optional scope (e.g., `api: add routing guard`). Wrap body at ~72 chars, noting why + what changed.
- Ensure `make format lint test` pass before opening a PR; include outputs when failures are expected.
- PRs should describe intent, key changes, test evidence, and any new env vars or migration steps; add screenshots/log snippets for API or UI-visible changes.
- Update relevant docs (`README.md`, `QUICKSTART.md`, `FRONTEND_GUIDE.md`, architecture files) when behavior or structure shifts.

## Configuration & Security Notes
- Runtime config is loaded via `.env` (see `skillslike/config.py`); keys include `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, and routing/timeout flags. Do not commit secrets.
- `Settings.validate_paths()` creates `skills/` and `data/files/`; ensure these remain writable in local/dev containers (`Dockerfile`, `docker-compose.yml` are available for isolated runs).
