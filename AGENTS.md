# Repository Guidelines

## Project Structure & Module Organization
Core application code lives under `src/`. Use `src/main.py` as the runtime entry point and `main.py` only as a thin launcher. Command-facing behavior is in `src/bot/handlers/`, business logic and integrations are in `src/bot/services/`, domain/data entities are in `src/bot/models/`, and shared helpers are in `src/bot/utils/`.

Tests are split by intent: `tests/unit/` for isolated logic, `tests/integration/` for end-to-end bot flows, and `tests/fixtures/` for reusable mocks. Database migrations are in `alembic/versions/`. Arduino reference firmware is in `sketch/sketch.ino`. Product/design docs are in `specs/`.

## Build, Test, and Development Commands
- `uv sync`: install runtime and dev dependencies from `pyproject.toml`/`uv.lock`.
- `uv run python src/main.py`: run the bot locally.
- `uv run pytest --cov=src`: run full test suite with coverage.
- `uv run pytest tests/unit` or `uv run pytest tests/integration`: run a focused test layer.
- `uv run ruff check .` and `uv run ruff format .`: lint and format code.
- `uv run mypy src/`: strict type checking.
- `uv run alembic upgrade head`: apply latest DB migrations.
- `docker compose up --build`: run app + PostgreSQL via containers.

## Coding Style & Naming Conventions
Target Python 3.11+ with 4-space indentation. Ruff enforces style (line length 100), and MyPy runs in strict mode; add explicit type hints to public functions and service boundaries.

Use `snake_case` for modules/functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants/env keys. Follow existing handler naming by command intent (for example, `sensors.py`, `settings.py`).

## Testing Guidelines
Use `pytest`, `pytest-asyncio`, and `pytest-cov`. Name files `test_<module>.py` and test functions `test_<behavior>`. Keep parser/service unit tests deterministic and use fixtures/mocks from `tests/fixtures/` for Telegram interactions.

Maintain coverage at or above the documented 80% target. Example targeted run:
`uv run pytest tests/integration/test_sensors_handler.py::test_sensors_normal_reading`.

## Commit & Pull Request Guidelines
Current history uses short lowercase subjects (for example, `fix`, `finish`). Keep that brevity, but prefer clearer imperative messages with scope, such as `services: harden serial reconnect`.

PRs should include: change summary, linked issue/spec, migration notes (if schema changed), and test evidence (commands run + results). Include relevant logs or chat output snippets when user-visible bot behavior changes.

## Security & Configuration Tips
Never commit secrets. Start from `.env.example` and set `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, and `SERIAL_PORT` locally. Avoid hardcoding serial device paths; keep them environment-driven.
