
# Playwright-e2e-framework
=======
# ClearGrid QA Automation

Unified Python-based automation framework for validating ClearGrid workflows across the UI, API, database, and load-testing layers.

## Purpose

This repository keeps quality automation in one stack instead of splitting coverage across unrelated tools. The framework is built around shared factories, typed API clients, Playwright page objects, pytest fixtures, and reporting hooks so new tests extend common abstractions instead of re-implementing setup logic.

## Current State

- Unit and smoke coverage already validates core framework wiring, configuration defaults, and execution context behavior.
- Browser, API, DB, and load-testing layers are scaffolded and ready to be extended with environment-specific selectors, endpoints, credentials, and data.
- CI already runs the smoke and API slices and uploads execution artifacts.

## Stack

- Python 3.12 recommended to match CI
- pytest, pytest-xdist, pytest-rerunfailures
- Playwright for browser automation
- httpx async clients and pydantic for API access and response modeling
- SQLAlchemy with psycopg for data-layer validation
- Locust for load scenarios
- Allure for artifact-rich reporting

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
pytest tests/unit -q
pytest -m smoke
```

`tests/unit` and `pytest -m smoke` are the cheapest local checks. They do not require a live ClearGrid environment when defaults are left in place.

Before running API, UI, E2E, or load coverage, create and export the environment variables documented in [SETUP.md](SETUP.md).

## Suite Commands

| Slice | Command | Notes |
| --- | --- | --- |
| Unit | `pytest tests/unit -q` | Fast framework checks with no external dependencies |
| Smoke | `pytest -m smoke` | Validates safe local defaults and test-context wiring |
| API | `pytest -m api` | Requires API base URL plus auth via token or login credentials |
| UI | `pytest -m ui` | Requires a running frontend, Playwright browser install, and working selectors |
| E2E | `pytest -m e2e` | Requires UI, API, and DB access for full-stack validation |
| CI-like local run | `pytest -m "smoke or api" --alluredir=artifacts/allure-results` | Mirrors the GitHub Actions quality gate |
| Load | `locust -f load_tests/settlement_load.py` | Uses Locust's synchronous, instrumented adapter; requires `CG_API_TOKEN` |

## Configuration

Runtime settings are loaded from environment variables in `src/config/settings.py`. The most important values are:

- `CG_ENVIRONMENT`, `CG_BASE_URL`, `CG_API_BASE_URL`, `CG_AUTH_BASE_URL`
- `CG_API_TOKEN` or both `CG_UI_USERNAME` and `CG_UI_PASSWORD`
- `CG_DB_DSN`
- `CG_BROWSER_NAME`, `CG_HEADLESS`, `CG_API_TIMEOUT_SECONDS`
- `CG_ARTIFACTS_DIR`, `CG_LOAD_BORROWER_ID`

The full variable reference, example `.env` block, setup flow, and troubleshooting notes live in [SETUP.md](SETUP.md).

## Repository Layout

```text
src/api/           HTTP client wrappers, auth, and client factories
src/config/        environment-driven settings
src/data_factory/  synthetic test data builders
src/db/            database connectivity and validation helpers
src/models/        typed request and response models
src/pages/         Playwright browser factory and page objects
src/services/      per-test context and traceable identifiers
tests/unit/        framework-level unit coverage
tests/smoke/       local-safe smoke validation
tests/api/         service and model validation
tests/ui/          browser-facing workflow coverage
tests/e2e/         full-stack workflow coverage
load_tests/        Locust entry points
artifacts/         screenshots, HTML, Allure output, and run artifacts
```

## Reporting And Artifacts

- `TestRun` creates one context and artifact directory per test, lazily opening
  only the browser or API client required by that workflow. It captures UI
  screenshots, page HTML, HAR, and Playwright traces on failure.
- Allure results can be written with `--alluredir=artifacts/allure-results` and rendered locally if the Allure CLI is installed.

## CI Workflow

The pull request quality gate in `.github/workflows/pr_quality_gate.yml` uses Python 3.12, installs Chromium for Playwright, runs `pytest -m "smoke or api" --alluredir=artifacts/allure-results`, and uploads the `artifacts/` directory.

## Additional Documentation

- [SETUP.md](SETUP.md): full local setup, environment configuration, suite execution, and troubleshooting guide
- [spec.md](spec.md): framework goals, architecture, and implementation direction
>>>>>>> 6b4e95c (Async Impl)
