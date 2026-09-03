# ClearGrid QA Automation Setup Guide

This guide explains how to bootstrap the framework locally, configure runtime variables, run each test slice, and understand the artifacts it produces. It is based on the code that exists in this repository today, not on planned future coverage.

## Prerequisites

- Python 3.12 recommended to match CI
- `pip`
- Network access to install Python packages and Playwright browsers
- Access to a non-production ClearGrid environment if you want to run API, UI, E2E, or load suites against live systems
- Optional: Allure CLI if you want to render HTML reports locally

## 1. Create A Virtual Environment

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `python3.12` is not available on your machine, use your local Python 3 interpreter. Keeping Python 3.12 locally reduces drift from CI, which is what the GitHub Actions workflow uses.

## 2. Install Playwright Browsers

Install the default browser used by the framework:

```bash
playwright install chromium
```

If you plan to run with `CG_BROWSER_NAME=firefox` or `CG_BROWSER_NAME=webkit`, install those browsers too:

```bash
playwright install firefox webkit
```

## 3. Configure Environment Variables

The framework reads configuration through `Settings.from_env()` in `src/config/settings.py`. It does not auto-load a `.env` file at runtime, so anything you put in a file must still be exported into your shell before you run pytest or Locust.

Create a `.env` file with the following values as your starting point:

```dotenv
CG_ENVIRONMENT=local
CG_BASE_URL=http://localhost:3000
CG_API_BASE_URL=http://localhost:8000
CG_AUTH_BASE_URL=http://localhost:8000
CG_DB_DSN=
CG_API_TOKEN=
CG_UI_USERNAME=
CG_UI_PASSWORD=
CG_BROWSER_NAME=chromium
CG_HEADLESS=true
CG_API_TIMEOUT_SECONDS=15
CG_ARTIFACTS_DIR=artifacts
CG_LOAD_BORROWER_ID=load-test-borrower
```

Then load it into the current shell:

```bash
set -a
source .env
set +a
```

### Variable Reference

| Variable | Default | Used By | Notes |
| --- | --- | --- | --- |
| `CG_ENVIRONMENT` | `local` | All test slices | Logical environment label for logs, reporting, and CI context |
| `CG_BASE_URL` | `http://localhost:3000` | UI and E2E | Base URL for the Playwright browser context |
| `CG_API_BASE_URL` | `http://localhost:8000` | API, E2E, load | Base URL used by domain API clients |
| `CG_AUTH_BASE_URL` | `http://localhost:8000` | API, E2E, load | Auth service base URL used when token login fallback is needed |
| `CG_DB_DSN` | empty | DB and E2E | SQLAlchemy-compatible DSN, for example `postgresql+psycopg://user:password@host:5432/dbname` |
| `CG_API_TOKEN` | empty | API, E2E, load | Preferred auth path for non-UI execution |
| `CG_UI_USERNAME` | empty | UI, API fallback, E2E | Used by login-based auth when `CG_API_TOKEN` is not set |
| `CG_UI_PASSWORD` | empty | UI, API fallback, E2E | Pair with `CG_UI_USERNAME` |
| `CG_BROWSER_NAME` | `chromium` | UI and E2E | Must be one of `chromium`, `firefox`, or `webkit` |
| `CG_HEADLESS` | `true` | UI and E2E | Browser headless toggle |
| `CG_API_TIMEOUT_SECONDS` | `15` | API, E2E, load | Request timeout used by API clients |
| `CG_ARTIFACTS_DIR` | `artifacts` | All test slices | Root directory for screenshots, HTML, traces, and Allure output |
| `CG_LOAD_BORROWER_ID` | `load-test-borrower` | Load tests | Borrower identifier used by `load_tests/settlement_load.py` |

### Minimum Variable Sets

- Unit and smoke tests: no secrets required; defaults are enough.
- API and load tests: set `CG_API_BASE_URL` and either `CG_API_TOKEN` or both `CG_UI_USERNAME` and `CG_UI_PASSWORD`.
- UI tests: set `CG_BASE_URL` and ensure the app under test is reachable; you will usually also need a real lower-environment test account.
- E2E and DB validation: add `CG_DB_DSN` pointing at an approved lower environment.

## 4. Validate The Installation

Start with the cheapest checks:

```bash
pytest tests/unit -q
pytest -m smoke
```

If both pass, the Python dependencies, pytest configuration, framework defaults, and core execution wiring are in place.

## 5. Run Each Test Slice

| Slice | Command | External Systems Needed |
| --- | --- | --- |
| Unit | `pytest tests/unit -q` | None |
| Smoke | `pytest -m smoke` | None |
| API | `pytest -m api` | API endpoint plus auth |
| UI | `pytest -m ui` | Frontend environment plus Playwright browser |
| E2E | `pytest -m e2e` | UI, API, and DB access |
| CI-like local run | `pytest -m "smoke or api" --alluredir=artifacts/allure-results` | Same prerequisites as the selected marks |

For load testing, start Locust with the checked-in entry point:

```bash
locust -f load_tests/settlement_load.py
```

For a non-interactive local run, use headless mode:

```bash
locust -f load_tests/settlement_load.py --headless -u 10 -r 2 -t 1m
```

Functional clients are asynchronous. Locust supplies its own synchronous,
instrumented HTTP client, so the load test uses a dedicated adapter and requires
`CG_API_TOKEN`; it does not perform the asynchronous credential-login fallback.

## 6. Understand The Current Coverage Boundary

- `tests/unit/` and `tests/smoke/` are safe starter checks and do not depend on a live ClearGrid system.
- `tests/ui/test_login_flow.py` currently exercises the page-object pattern and chainable workflow style. Before using it as strong gating coverage, replace placeholder selectors, routes, and credentials with real application-specific ones.
- `tests/e2e/` currently contains guidance for future full-stack flows rather than a full implemented E2E suite.
- The repo structure is ready for deeper workflow coverage even where the current test surface is still scaffold-level.

## 7. Artifacts And Reporting

- `src/services/test_run.py` owns the per-test context, async browser lifecycle,
  async API client, optional database adapter, and artifact directory.
- Failed UI runs save screenshots, page HTML, HAR, and Playwright traces beneath
  `CG_ARTIFACTS_DIR/<run-id>/`.

To write Allure results locally:

```bash
pytest -m "smoke or api" --alluredir=artifacts/allure-results
```

If the Allure CLI is installed, render the report with:

```bash
allure serve artifacts/allure-results
```

## 8. Match CI Locally

The pull request quality gate in `.github/workflows/pr_quality_gate.yml` does the following:

1. Uses Python 3.12.
2. Installs dependencies from `requirements.txt`.
3. Installs Playwright Chromium.
4. Runs `pytest -m "smoke or api" --alluredir=artifacts/allure-results` with `CG_ENVIRONMENT=ci` and `CG_HEADLESS=true`.
5. Uploads the `artifacts/` directory.

If you want to reproduce CI behavior locally, export the same environment variables and run the same command.

## 9. Extend The Framework Cleanly

- Add new page objects to `src/pages/` and keep test files focused on workflows rather than selectors.
- Add new domain wrappers under `src/api/` and keep raw `requests` calls out of test cases.
- Add typed request and response models under `src/models/`.
- Add DB helpers under `src/db/validators.py` and phrase them as business-level assertions.
- Add synthetic data builders under `src/data_factory/`.
- Reuse the existing pytest fixtures and client factories in functional tests and Locust scenarios.

## 10. Troubleshooting

- Browser launch fails: run `playwright install chromium` or install the browser named in `CG_BROWSER_NAME`.
- `Unsupported browser` error: valid values are `chromium`, `firefox`, and `webkit`.
- `No API token found and no credentials available for authentication`: set `CG_API_TOKEN` or both `CG_UI_USERNAME` and `CG_UI_PASSWORD`.
- `.env` changes do not take effect: reload them into the current shell before rerunning pytest or Locust.
- DB validation fails immediately: confirm `CG_DB_DSN` is a valid SQLAlchemy/psycopg DSN and points to an approved lower environment.
- Artifacts are missing: ensure the configured `CG_ARTIFACTS_DIR` is writable.
