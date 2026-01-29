# Implementation Plan: Arduino Sensor Monitoring Bot

**Branch**: `001-arduino-sensor-monitoring` | **Date**: 2026-01-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-arduino-sensor-monitoring/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Telegram bot that monitors Arduino sensor data via serial connection, providing on-demand sensor readings through bot commands and automatic humidity threshold alerts. The bot continuously reads sensor data (humidity, temperatures) from Arduino serial output, responds to user queries, and proactively notifies users when humidity exceeds configurable thresholds. Technical approach uses Python's async I/O for concurrent serial monitoring and Telegram bot operations, with persistent storage for user preferences.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: python-telegram-bot (v20+) or aiogram (v3+), pyserial (serial communication), pydantic/pydantic-settings (config), structlog (logging)  
**Storage**: SQLite or JSON file for user settings persistence (humidity thresholds, alert states)  
**Testing**: pytest, pytest-asyncio, pytest-mock, pytest-cov  
**Target Platform**: Linux/macOS/Windows (any platform with Python 3.11+ and serial port access)  
**Project Type**: single (standalone bot application)  
**Performance Goals**: Process 1 sensor reading/second, respond to commands within 2 seconds, detect threshold breaches within 5 seconds  
**Constraints**: Must handle continuous serial I/O without blocking Telegram operations, memory-efficient for 24+ hour operation, graceful reconnection on serial disconnect  
**Scale/Scope**: Support 5-10 concurrent users, ~2000 lines of code, 4 core handlers, single Arduino connection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Handler-First Architecture ✅ PASS
- **Requirement**: Independent handler functions with single responsibility
- **Compliance**: Spec defines 4 distinct commands (/start, /help, /sensors, /settings) plus threshold configuration handlers - each maps to independent handler function
- **Verification**: Each user story translates to dedicated handlers with clear boundaries

### Environment-Driven Configuration ✅ PASS
- **Requirement**: All config in .env, never hardcoded, fail fast on missing config
- **Compliance**: FR-008 explicitly requires serial port/baud rate configurable via .env; spec includes Telegram bot token, threshold defaults, all sensitive data externalized
- **Verification**: Configuration management with pydantic-settings ensures type-safe loading and startup validation

### Test-First Development (TDD) ✅ PASS
- **Requirement**: Tests written first, user approved, then implement
- **Compliance**: Spec provides detailed acceptance scenarios for each user story with Given-When-Then format, enabling test-first approach
- **Verification**: 12 acceptance scenarios defined across 3 user stories provide clear test cases before implementation

### Dependency Management with uv ✅ PASS
- **Requirement**: Use uv exclusively for package management
- **Compliance**: User explicitly specified "package manager uv" in requirements
- **Verification**: Project will use pyproject.toml with uv for all dependency management

### Observability and Error Handling ✅ PASS
- **Requirement**: Structured logging, error handling, no internal errors to users
- **Compliance**: FR-012 requires logging of all sensor readings, alerts, and interactions; edge cases document error handling strategies
- **Verification**: Spec explicitly addresses error scenarios (disconnection, malformed data, reconnection) with user-friendly messaging

**Overall Gate Status**: ✅ **PASS** - All constitutional requirements satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-arduino-sensor-monitoring/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── bot/
│   ├── handlers/         # Telegram command handlers
│   │   ├── __init__.py
│   │   ├── start.py      # /start and /help handlers
│   │   ├── sensors.py    # /sensors and /status handlers
│   │   └── settings.py   # /settings, /set_humidity_min, /set_humidity_max handlers
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── serial_reader.py      # Arduino serial communication
│   │   ├── data_parser.py        # Parse sensor data format
│   │   ├── alert_manager.py      # Threshold monitoring and alerts
│   │   └── user_settings.py      # User preference persistence
│   ├── models/           # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── sensor_reading.py     # SensorReading model
│   │   ├── user.py               # User model with thresholds
│   │   └── alert_state.py        # AlertState model
│   └── utils/            # Helper functions
│       ├── __init__.py
│       └── rate_limiter.py       # Rate limiting utilities
├── config.py             # Configuration management (pydantic-settings)
└── main.py               # Bot entry point

tests/
├── unit/                 # Unit tests for services
│   ├── test_data_parser.py
│   ├── test_alert_manager.py
│   └── test_user_settings.py
├── integration/          # Integration tests for handlers
│   ├── test_sensors_handler.py
│   ├── test_settings_handler.py
│   └── test_alert_flow.py
└── fixtures/             # Test fixtures and mocks
    ├── __init__.py
    └── telegram_mocks.py

.env.example              # Environment template
.env                      # Environment config (gitignored)
.gitignore                # Ignore .env, uv cache, __pycache__
pyproject.toml            # uv configuration
uv.lock                   # Locked dependencies
README.md                 # Setup and usage instructions
```

**Structure Decision**: Selected single project structure (Option 1) as this is a standalone bot application without frontend/backend separation. The structure follows the constitution's prescribed layout with `src/bot/` containing handlers, services, models, and utils, plus `tests/` with unit and integration test organization. All bot-specific code is under `src/bot/` to allow for potential future expansion of the project.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitutional requirements are satisfied by the feature design.

---

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design completion*

### Handler-First Architecture ✅ PASS
- **Design Verification**: data-model.md and contracts define clear handler boundaries
- **Compliance**: 7 command handlers designed (start, help, sensors, status, settings, set_humidity_min, set_humidity_max)
- **Independent Testing**: Each handler has defined contracts with test scenarios in contracts/bot-commands.md

### Environment-Driven Configuration ✅ PASS
- **Design Verification**: config.py designed with pydantic-settings BaseSettings
- **Compliance**: All 8 configuration parameters externalized in .env with validation
- **Security**: .env.example provided, actual .env in .gitignore, no hardcoded secrets

### Test-First Development (TDD) ✅ PASS
- **Design Verification**: contracts/bot-commands.md provides complete test specifications
- **Compliance**: 7 test dimensions defined per command (success, invalid input, missing params, rate limit, state changes, errors, concurrency)
- **Coverage**: data-model.md includes validation rules and state transitions for TDD

### Dependency Management with uv ✅ PASS
- **Design Verification**: pyproject.toml structure defined in research.md
- **Compliance**: All dependencies identified with version constraints (python-telegram-bot 20+, pyserial 3.5+, etc.)
- **Implementation**: quickstart.md uses `uv sync` and `uv run` exclusively

### Observability and Error Handling ✅ PASS
- **Design Verification**: research.md section 8 defines structured logging approach
- **Compliance**: All error scenarios have user-friendly messages in contracts
- **Monitoring**: Serial connection health monitoring and reconnection strategy designed

**Post-Design Status**: ✅ **PASS** - Design maintains constitutional compliance

---

## Phase Completion Summary

### ✅ Phase 0: Research (Completed)
- Resolved all technical unknowns
- Selected python-telegram-bot, pyserial, SQLite, pydantic-settings
- Documented 9 technical decisions with rationale
- Identified best practices and patterns
- Output: [research.md](research.md)

### ✅ Phase 1: Design & Contracts (Completed)
- Defined 4 core entities with validation rules
- Designed SQLite schema with constraints
- Specified 7 bot commands with full contracts
- Created quickstart guide for developers and users
- Updated agent context for GitHub Copilot
- Output: [data-model.md](data-model.md), [contracts/bot-commands.md](contracts/bot-commands.md), [quickstart.md](quickstart.md)

### ⏸️ Phase 2: Task Breakdown (Not Started)
**Next Step**: Run `/speckit.tasks` to generate detailed implementation tasks organized by user story

---

## Ready for Implementation

This plan is complete and ready for task generation. The implementation should follow this sequence:

1. Run `/speckit.tasks` to generate task breakdown
2. Follow TDD: Write tests first for each user story
3. Implement in priority order: P1 → P2 → P3
4. Each user story should be independently deployable

**Key Files Generated**:
- ✅ plan.md (this file)
- ✅ research.md
- ✅ data-model.md  
- ✅ contracts/bot-commands.md
- ✅ quickstart.md
- ⏸️ tasks.md (generate with `/speckit.tasks`)
