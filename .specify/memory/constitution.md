# Telegram Home Sensors Bot Constitution

## Core Principles

### I. Handler-First Architecture
Every bot feature must be implemented as an independent handler function. Handlers must:
- Be independently testable with mock Telegram updates
- Have clear, single responsibility (one command/callback = one handler)
- Follow async/await patterns for all I/O operations
- Include proper error handling with user-friendly error messages
- Be registered explicitly in the bot's dispatcher/router

### II. Environment-Driven Configuration
All configuration must be externalized and never hardcoded:
- Telegram bot token, API keys, and secrets in `.env` file (never committed)
- Environment-specific settings (dev/staging/prod) via environment variables
- Use `pydantic-settings` for type-safe configuration management
- Provide `.env.example` template with all required variables documented
- Fail fast on startup if required configuration is missing

### III. Test-First Development (NON-NEGOTIABLE)
TDD is mandatory for all bot functionality:
- Tests written first → User approved → Tests fail → Then implement
- Red-Green-Refactor cycle strictly enforced
- Use `pytest` with `pytest-asyncio` for async handler testing
- Mock Telegram API calls using `pytest-mock` or similar
- Minimum 80% code coverage for handlers and business logic
- Test both happy paths and error conditions

### IV. Dependency Management with uv
Use `uv` as the exclusive package manager:
- Initialize projects with `uv init` and manage dependencies via `uv add`
- Never use `pip` directly - all installs through `uv`
- Lock dependencies with `uv lock` before committing
- Use `uv sync` for installing from lock file in CI/CD
- Organize dependencies: production, dev, and test groups
- Keep `pyproject.toml` as the single source of truth

### V. Observability and Error Handling
Comprehensive logging and monitoring:
- Structured logging with `structlog` or Python's `logging` module
- Log all user interactions (user_id, command, timestamp)
- Separate log levels: DEBUG for development, INFO for production
- Catch and log all exceptions with context
- Send critical errors to admin via Telegram notifications
- Never expose internal errors to end users

## Technical Requirements

### Python Version and Stack
- **Python**: 3.11+ (leverage modern async features)
- **Bot Framework**: `python-telegram-bot` (v20+) or `aiogram` (v3+)
- **Package Manager**: `uv` exclusively
- **Configuration**: `pydantic` and `pydantic-settings`
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`
- **Code Quality**: `ruff` for linting and formatting
- **Type Checking**: `mypy` with strict mode enabled

### Security Standards
- Never commit `.env` files or secrets
- Use `.gitignore` to exclude sensitive files
- Validate all user inputs before processing
- Rate limit handler calls to prevent abuse
- Use Telegram's built-in security features (callback data validation)
- Sanitize data before logging to avoid leaking sensitive information

### Project Structure
```
src/
├── bot/
│   ├── handlers/         # Command and callback handlers
│   ├── services/         # Business logic
│   ├── models/           # Data models (Pydantic)
│   └── utils/            # Helper functions
├── config.py             # Configuration management
└── main.py               # Bot entry point

tests/
├── unit/                 # Unit tests for services
├── integration/          # Integration tests for handlers
└── fixtures/             # Test fixtures and mocks

.env.example              # Environment template
pyproject.toml            # uv configuration
uv.lock                   # Locked dependencies
```

## Development Workflow

### Setup Process
1. Clone repository
2. Copy `.env.example` to `.env` and fill in values
3. Run `uv sync` to install dependencies
4. Run tests with `uv run pytest`
5. Start bot with `uv run python src/main.py`

### Code Quality Gates
- All code must pass `ruff check .` (no warnings)
- Format code with `ruff format .` before committing
- Type check with `mypy src/` (strict mode)
- Tests must pass with `pytest` before merging
- Coverage must not decrease below current threshold

### Adding New Commands
1. Write test for handler in `tests/integration/test_handlers.py`
2. Verify test fails (red)
3. Implement handler in `src/bot/handlers/`
4. Register handler in dispatcher
5. Verify test passes (green)
6. Refactor if needed
7. Update documentation

## Governance

This constitution supersedes all other practices. Any violations must be explicitly documented and justified in feature plans under "Complexity Tracking" section.

Amendments to this constitution require:
1. Documentation of rationale
2. Team/stakeholder approval
3. Migration plan for existing code
4. Update to `.specify/memory/constitution.md`

All feature specifications must verify compliance with these principles during the "Constitution Check" phase. Use `.specify/templates/plan-template.md` for development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-01-29 | **Last Amended**: 2026-01-29
