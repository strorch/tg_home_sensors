# Tasks: Arduino Sensor Monitoring Bot

**Input**: Design documents from `/specs/001-arduino-sensor-monitoring/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Following constitution's TDD mandate - tests written first for all functionality.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths follow plan.md structure with `src/bot/` organization

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize Python project with uv in repository root (run `uv init`)
- [X] T002 Create pyproject.toml with project metadata and Python 3.11+ requirement
- [X] T003 [P] Add core dependencies via uv: python-telegram-bot>=20.0, pyserial>=3.5, pydantic>=2.0, pydantic-settings>=2.0
- [X] T004 [P] Add development dependencies via uv: pytest>=8.0, pytest-asyncio>=0.23, pytest-mock>=3.12, pytest-cov>=4.1, ruff>=0.1, mypy>=1.8
- [X] T005 [P] Add SQLite async support: aiosqlite>=0.19
- [X] T006 Create directory structure: src/bot/{handlers,services,models,utils}/, tests/{unit,integration,fixtures}/
- [X] T007 Create .gitignore (include .env, __pycache__, *.pyc, uv.lock, data/, .pytest_cache/, .mypy_cache/, .coverage)
- [X] T008 Create .env.example with documented configuration variables (TELEGRAM_BOT_TOKEN, SERIAL_PORT, SERIAL_BAUD_RATE, DATABASE_PATH, LOG_LEVEL, defaults)
- [X] T009 [P] Create README.md with quickstart instructions from quickstart.md
- [X] T010 [P] Configure ruff in pyproject.toml (line-length=100, target-version=py311)
- [X] T011 [P] Configure mypy in pyproject.toml (strict=true, python_version=3.11)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T012 Create configuration management in src/config.py using pydantic-settings BaseSettings with all .env variables
- [X] T013 Implement database initialization in src/bot/services/database.py with SQLite schema creation (users and alert_states tables)
- [X] T014 [P] Write unit test for config.py in tests/unit/test_config.py (validates required fields, defaults, type coercion)
- [X] T015 [P] Write unit test for database.py in tests/unit/test_database.py (schema creation, table existence)
- [X] T016 Create logging setup in src/bot/utils/logger.py with structured logging configuration (JSON format, log levels)
- [X] T017 Implement SensorReading model in src/bot/models/sensor_reading.py with Pydantic validation per data-model.md
- [X] T018 [P] Implement User model in src/bot/models/user.py with Pydantic validation per data-model.md
- [X] T019 [P] Implement AlertState model in src/bot/models/alert_state.py with state transition logic per data-model.md
- [X] T020 [P] Implement SerialConnection model in src/bot/models/serial_connection.py with backoff logic per data-model.md
- [X] T021 [P] Write unit tests for all models in tests/unit/test_models.py (validation rules, edge cases, state transitions)
- [X] T022 Create bot entry point in src/main.py with basic bot initialization and graceful shutdown

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Query Current Sensor Readings (Priority: P1) 🎯 MVP

**Goal**: Users can request current sensor readings via /sensors or /status commands

**Independent Test**: Send /sensors command and receive formatted sensor data with timestamp

### Tests for User Story 1

> **TDD: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US1] Write integration test for /start handler in tests/integration/test_start_handler.py (user initialization, welcome message, default thresholds)
- [X] T024 [P] [US1] Write integration test for /help handler in tests/integration/test_help_handler.py (help message content, formatting)
- [X] T025 [P] [US1] Write integration test for /sensors handler in tests/integration/test_sensors_handler.py (3 acceptance scenarios from spec.md)
- [X] T026 [P] [US1] Write unit test for data parser in tests/unit/test_data_parser.py (valid format, malformed data, edge cases)
- [X] T027 [P] [US1] Write unit test for serial reader in tests/unit/test_serial_reader.py (connection, reading, disconnection, reconnection)
- [X] T028 [P] [US1] Write test fixtures for Telegram mocks in tests/fixtures/telegram_mocks.py (Update objects, Message objects, User objects)

### Implementation for User Story 1

- [X] T029 [P] [US1] Implement data parser service in src/bot/services/data_parser.py (regex parsing of Arduino format per research.md)
- [X] T030 [P] [US1] Implement serial reader service in src/bot/services/serial_reader.py (async serial reading, connection management, reconnection with exponential backoff)
- [X] T031 [US1] Implement user settings service in src/bot/services/user_settings.py (database operations for User and AlertState tables)
- [X] T032 [US1] Implement /start handler in src/bot/handlers/start.py (user initialization, welcome message per contracts/bot-commands.md)
- [X] T033 [P] [US1] Implement /help handler in src/bot/handlers/start.py (help message formatting per contracts/bot-commands.md)
- [X] T034 [US1] Implement rate limiter utility in src/bot/utils/rate_limiter.py (decorator pattern per research.md decision 5)
- [X] T035 [US1] Implement /sensors and /status handlers in src/bot/handlers/sensors.py (fetch latest reading, format output, rate limiting per contracts/bot-commands.md)
- [X] T036 [US1] Wire up handlers in src/main.py (register /start, /help, /sensors, /status handlers with dispatcher)
- [X] T037 [US1] Add error handling for Arduino disconnection in sensors handler (return "Sensor unavailable" message per contracts)
- [X] T038 [US1] Run all User Story 1 tests and verify they pass

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can query sensors via Telegram.

---

## Phase 4: User Story 2 - Automatic Humidity Alerts (Priority: P2)

**Goal**: Bot automatically sends alerts when humidity exceeds user thresholds with 5-minute cooldown

**Independent Test**: Set humidity thresholds, simulate threshold breach, verify alert message sent automatically

### Tests for User Story 2

> **TDD: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T039 [P] [US2] Write unit test for alert manager in tests/unit/test_alert_manager.py (threshold detection, cooldown logic, state transitions)
- [ ] T040 [P] [US2] Write integration test for alert flow in tests/integration/test_alert_flow.py (4 acceptance scenarios from spec.md: high alert, low alert, cooldown, recovery)
- [ ] T041 [P] [US2] Write test for multi-user alert isolation in tests/integration/test_alert_flow.py (each user receives only their own alerts)

### Implementation for User Story 2

- [ ] T042 [P] [US2] Implement alert manager service in src/bot/services/alert_manager.py (threshold monitoring, cooldown checking, state management per data-model.md AlertState)
- [ ] T043 [US2] Integrate alert manager with serial reader in src/bot/services/serial_reader.py (check each reading against thresholds, trigger alerts)
- [ ] T044 [US2] Implement high humidity alert message formatting in alert_manager.py (per contracts/bot-commands.md automatic alerts section)
- [ ] T045 [P] [US2] Implement low humidity alert message formatting in alert_manager.py (per contracts/bot-commands.md automatic alerts section)
- [ ] T046 [P] [US2] Implement recovery notification message formatting in alert_manager.py (per contracts/bot-commands.md automatic alerts section)
- [ ] T047 [US2] Implement alert state persistence in user_settings.py (update AlertState in database after sending alert)
- [ ] T048 [US2] Add background task for continuous monitoring in src/main.py (run serial reader and alert manager concurrently with bot)
- [ ] T049 [US2] Implement connection lost/restored notifications in serial_reader.py (notify users on disconnect/reconnect per contracts)
- [ ] T050 [US2] Run all User Story 2 tests and verify they pass

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Bot monitors and alerts automatically.

---

## Phase 5: User Story 3 - Configure Alert Thresholds (Priority: P3)

**Goal**: Users can customize humidity thresholds via /settings, /set_humidity_min, /set_humidity_max commands

**Independent Test**: Send threshold configuration commands, verify settings update and alerts trigger at new levels

### Tests for User Story 3

> **TDD: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T051 [P] [US3] Write integration test for /settings handler in tests/integration/test_settings_handler.py (display current thresholds)
- [ ] T052 [P] [US3] Write integration test for /set_humidity_min in tests/integration/test_settings_handler.py (4 acceptance scenarios from spec.md: valid, out of range, > max, missing param)
- [ ] T053 [P] [US3] Write integration test for /set_humidity_max in tests/integration/test_settings_handler.py (4 acceptance scenarios from spec.md: valid, out of range, < min, missing param)
- [ ] T054 [P] [US3] Write test for threshold validation in tests/unit/test_user_settings.py (min < max constraint, range validation)

### Implementation for User Story 3

- [ ] T055 [P] [US3] Implement /settings handler in src/bot/handlers/settings.py (fetch and display user thresholds per contracts/bot-commands.md)
- [ ] T056 [P] [US3] Implement /set_humidity_min handler in src/bot/handlers/settings.py (parse value, validate, update database per contracts/bot-commands.md)
- [ ] T057 [P] [US3] Implement /set_humidity_max handler in src/bot/handlers/settings.py (parse value, validate, update database per contracts/bot-commands.md)
- [ ] T058 [US3] Add input validation in settings handlers (range checks, min < max validation, error messages per contracts)
- [ ] T059 [US3] Wire up settings handlers in src/main.py (register /settings, /set_humidity_min, /set_humidity_max with dispatcher)
- [ ] T060 [US3] Apply rate limiting to settings handlers (use rate_limiter decorator per research.md)
- [ ] T061 [US3] Run all User Story 3 tests and verify they pass

**Checkpoint**: All user stories should now be independently functional. Users can query, receive alerts, and configure thresholds.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, error handling, logging, and production readiness

- [ ] T062 [P] Add comprehensive error logging throughout all services (use logger.py, log all exceptions with context)
- [ ] T063 [P] Add user interaction logging (log all commands received with user_id, command, timestamp)
- [ ] T064 [P] Add sensor data logging (log readings with configurable frequency to prevent log spam)
- [ ] T065 Implement graceful shutdown in src/main.py (close serial connection, close database, stop bot cleanly)
- [ ] T066 Add type hints to all functions and methods (run mypy to verify)
- [ ] T067 [P] Format all code with ruff (run `uv run ruff format .`)
- [ ] T068 [P] Lint all code with ruff (run `uv run ruff check .` and fix issues)
- [ ] T069 Run full test suite with coverage (target 80%+ per constitution)
- [ ] T070 Create .env file from .env.example for local testing (not committed)
- [ ] T071 Test bot end-to-end with real Arduino connected (manual testing against quickstart.md scenarios)
- [ ] T072 [P] Update README.md with troubleshooting section from quickstart.md
- [ ] T073 Lock dependencies with uv (run `uv lock` and commit uv.lock)
- [ ] T074 Final constitution compliance check (verify all 5 principles satisfied)

---

## Dependencies Between User Stories

### Story Completion Order

```
Setup (Phase 1)
    ↓
Foundational (Phase 2)
    ↓
    ├─→ User Story 1 (P1) - Independent, can complete alone ← MVP
    ↓
    ├─→ User Story 2 (P2) - Depends on US1 (needs serial reader and data parser)
    ↓
    └─→ User Story 3 (P3) - Independent of US2, depends on US1 (needs user settings)
```

### Parallel Execution Opportunities

**After Phase 2 completes:**

**User Story 1** can be fully implemented:
- Parallel: T023-T028 (all tests can be written simultaneously)
- Parallel: T029, T030, T034 (data parser, serial reader, rate limiter are independent)
- Sequential: T031-T038 (handlers depend on services)

**After US1 completes:**

**User Story 2 and User Story 3 can proceed in parallel:**
- US2 tasks (T039-T050) can run concurrently with US3 tasks (T051-T061)
- US2 extends serial reader, US3 extends user settings - different files
- No blocking dependencies between US2 and US3

---

## Implementation Strategy

### MVP-First Approach

**Minimum Viable Product**: User Story 1 only
- Delivers: Remote sensor querying via Telegram
- Value: Users can check sensors from anywhere
- Deployable: Yes, provides standalone value
- Tasks: Setup + Foundational + Phase 3 (T001-T038)

**Incremental Delivery**:
1. **MVP** (US1): Query sensors ← Deploy first
2. **MVP + Monitoring** (US1+US2): Automatic alerts ← Deploy second
3. **Full Feature** (US1+US2+US3): Customizable alerts ← Deploy third

### Task Execution Tips

1. **Follow TDD strictly**: Write tests before implementation (constitution requirement)
2. **Run tests frequently**: After each implementation task, run corresponding tests
3. **Use parallel markers**: Tasks marked [P] can be worked on simultaneously
4. **Validate incrementally**: Run `ruff check` and `mypy` after each file creation
5. **Commit per user story**: Commit after completing each phase checkpoint

---

## Test Coverage Goals

Per constitution mandate: **Minimum 80% code coverage**

### Target Coverage by Component:

| Component | Target | Rationale |
|-----------|--------|-----------|
| Handlers | 90% | Critical user-facing logic, well-defined contracts |
| Services | 85% | Core business logic, essential for reliability |
| Models | 95% | Simple validation logic, must be bulletproof |
| Utils | 80% | Helper functions, some may be simple |
| Overall | 80%+ | Constitution requirement |

### Coverage Command:
```bash
uv run pytest --cov=src --cov-report=html --cov-report=term
```

---

## Task Summary

**Total Tasks**: 74
- Setup: 11 tasks
- Foundational: 11 tasks (blocking)
- User Story 1 (P1 - MVP): 16 tasks
- User Story 2 (P2): 12 tasks
- User Story 3 (P3): 11 tasks
- Polish: 13 tasks

**Parallel Opportunities**: 42 tasks marked [P] (56% parallelizable)

**User Story Distribution**:
- US1: 16 tasks (MVP-critical)
- US2: 12 tasks (monitoring)
- US3: 11 tasks (customization)

**Independent Test Criteria**:
- US1: Send /sensors → receive formatted data
- US2: Simulate threshold breach → receive alert
- US3: Send /set_humidity_min 30 → verify threshold updated

**Estimated Complexity**: ~2000 lines of code across 74 tasks

---

## Next Steps

1. Start with Phase 1 (Setup): T001-T011
2. Proceed to Phase 2 (Foundational): T012-T022 - MUST complete before user stories
3. Implement MVP (User Story 1): T023-T038
4. Test MVP deployment, gather feedback
5. Add monitoring (User Story 2): T039-T050
6. Add customization (User Story 3): T051-T061 (can parallel with US2)
7. Polish and deploy: T062-T074

**Success Metrics** (from spec.md success criteria):
- ✅ 2-second command response time (95%)
- ✅ 5-second alert detection
- ✅ 24+ hour continuous operation
- ✅ 30-second reconnection after disconnect
- ✅ No alert spam (5-minute cooldown)
- ✅ 80%+ test coverage
