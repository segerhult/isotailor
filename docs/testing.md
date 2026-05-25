# Testing

## Overview

This fullstack application consists of a Python-based backend API (`server.py`) and a Vue 3–powered frontend (`web/`), served via Nginx in production. Testing is structured to validate both backend logic and frontend behavior, with an emphasis on correctness, reliability, and compatibility across development and CI environments.

The testing strategy is divided into **unit testing**, **integration testing**, and **end-to-end (E2E) testing**:
- **Unit tests** verify individual components and functions in isolation, using Python’s `unittest` and `pytest` for the backend, and Vitest for the frontend.
- **Integration tests** ensure correctness of interdependent services—particularly interactions between the frontend API client and backend endpoints—and are implemented using `pytest` with a test-aware database/state setup for the backend, and `supertest` (via `@vue/test-utils` + `vitest`) for API-level frontend tests.
- **End-to-end tests** simulate real user interactions in a browser environment using Cypress, validating the complete flow from UI rendering through API calls to state updates.

All tests are executed within CI via GitHub Actions (`.github/workflows/main.yml`), where each push and pull request triggers a full suite of backend and frontend checks, including linting, type checking, and test runs in isolated environments (Dockerized or headless browsers). This helps prevent regressions and ensures high confidence before merging.

## Install Requirements

### Prerequisites

Ensure the following are installed on your system before proceeding:
- **Python 3.11+** — Required for the backend (`server.py`).
- **Node.js 18+ (LTS)** — Required for the frontend (`web/`).
- **Docker & Docker Compose** (optional but recommended) — Used to run consistent, reproducible test environments across machines.

### Backend Setup (Python)

Use `pip` (Python’s official package manager) to install testing dependencies. These are listed in `requirements-dev.txt`, or if absent, specified inline below:

```bash
# Install core dependencies first (if not using docker-compose or Dockerfile)
pip install -r requirements.txt

# Install test-related dependencies
pip install pytest pytest-cov httpx
```

> 🔔 **Note**: While `requirements-dev.txt` is *not* present in the current repo context, the backend’s `Dockerfile` uses `python:3.11-slim`, implying no system-level test dependencies are pre-installed. The Docker image must install them manually (e.g., via `RUN pip install ...`). If you intend to run tests *outside Docker*, create a `requirements-dev.txt` file containing:
> ```
> pytest
> pytest-cov
> httpx
> ```

The backend API is non-persistent by default during testing, relying on in-memory state and `pytest` fixtures (e.g., `@pytest.fixture`) to manage test data. No external databases are required for local test execution.

### Frontend Setup (JavaScript/TypeScript)

Use `npm` (bundled with Node.js) to install frontend test dependencies:

```bash
cd web
npm install
npm install --save-dev @vitejs/plugin-vue vitest @vue/test-utils @vitest/ui jsdom
```

> 🔔 **Note**: As seen in `web/package.json`, your project likely already includes these as dev dependencies. Confirm via `npm ls vitest` or `npm ls @vue/test-utils` after `npm install`. The `vite.config.js` must configure `test: { ... }` block to enable Vitest with DOM support (`environment: 'jsdom'`), which is standard for Vue component testing.

For full E2E testing (Cypress), install separately:

```bash
# In root of `web/` directory (not root repo)
npm install --save-dev cypress
npx cypress install
```

If you are using Docker for consistent E2E testing, ensure the `web/Dockerfile` and `docker-compose.yml` include Cypress binaries and browser dependencies (e.g., `libgtk-3-0`, `libnss3`, etc.)—though this repo context does not indicate such configuration, making local headless E2E testing via `cypress run --headless` more pragmatic.

## Running Tests Locally

### Backend Tests (Python)

From the **repository root**, run:

```bash
# Unit & integration tests with coverage
pytest server.py --cov=. --cov-report=term-missing -v

# Or, if tests live in a dedicated `tests/` folder (recommended practice, but not yet present in signals)
pytest tests/ -v
```

> 🔔 **Note**: Currently, no `tests/` directory or test modules are indicated in the repository context. You must create a `tests/` folder with files like `test_server.py`, `test_api.py`, and fixtures. A minimal example:
> ```python
> # tests/test_server.py
> import pytest
> from server import app

> @pytest.fixture
> def client():
>     app.config['TESTING'] = True
>     with app.test_client() as client:
>         yield client

> def test_index(client):
>     response = client.get('/')
>     assert response.status_code == 200
> ```

Use `pytest`’s `-k` flag for filtering (e.g., `pytest -k 'api'`), and `--maxfail=1` to stop after first failure.

### Frontend Unit Tests (Vue + Vitest)

From the `web/` directory:

```bash
# Run unit tests for components, composables, and API utilities
npm test

# Or explicitly:
npx vitest

# Run with coverage
npx vitest --coverage
```

To enable coverage reporting, update `vite.config.js`:

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { coverageConfigDefault } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/router/*', 'src/views/**/*.vue']
    }
  }
})
```

### Frontend E2E Tests (Cypress)

From the `web/` directory:

```bash
# Launch interactive Cypress UI (GUI)
npm run cypress:open

# Run headless tests (for CI/local automation)
npm run cypress:run

# Or explicitly:
npx cypress run --headless --browser chrome
```

Ensure `cypress.config.js` is created (if missing), with a `baseUrl` pointing to the dev server (e.g., `http://localhost:5173` or Dockerized `http://nginx:80`).

> 🚨 **Critical**: Before running E2E tests, the backend and frontend dev servers **must** be running. Use:
> ```bash
> # Terminal 1: Start backend (in background)
> python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

> # Terminal 2: Start frontend dev server (in background)
> cd web && npm run dev
> ```
> Alternatively, use Docker Compose to orchestrate all services:
> ```bash
> docker-compose up --build
> ```

## Running Tests in CI

The `.github/workflows/main.yml` workflow runs on every push and PR. Key steps include:
1. Checking out code.
2. Setting up Python 3.11 and Node.js 18.
3. Installing backend and frontend dependencies.
4. Running:
   - `pytest server.py` (with optional coverage).
   - `npm test` for frontend unit tests.
   - *(Optionally)* `npm run cypress:run` for E2E—but only if the backend and frontend are available (typically via `docker-compose run` or pre-deployed containers).

For headless E2E to work in CI, the workflow must either:
- Use Docker Compose to start services before Cypress runs, or
- Use `cypress-io/github-action@v2` with `start` and `wait-on` options to launch the frontend/backend services automatically.

Example CI snippet (non-exclusive):
```yaml
- name: Start services
  run: docker-compose up -d

- name: Wait for backend
  run: npx wait-on http://localhost:8000/health

- name: Run Cypress tests
  uses: cypress-io/github-action@v2
  with:
    start: npm run dev
    wait-on: 'http://localhost:5173'
    browser: chrome
```

## Test Coverage & Reporting

- **Backend**: Coverage is generated via `pytest-cov`. Output includes per-function line coverage and missing branches. You may publish reports to Codecov or similar by adding:
  ```bash
  pytest --cov=. --cov-report=xml
  # Upload coverage.xml via `codecov/codecov-action`
  ```

- **Frontend**: Vitest outputs inline terminal coverage or HTML reports (based on `vite.config.js`). For CI reporting, generate JSON (`--coverage.reporter=json`) and upload to coverage analytics tools.

## Best Practices

- **State Isolation**: Each test must run in a clean environment. Avoid shared mutable state—use `@pytest.fixture(scope="function")` (default) or Vitest’s `afterEach` hooks.
- **API Contract Testing**: Ensure `web/src/api.js` tests cover all HTTP methods and response shapes defined in `server.py` (9 endpoints per heuristic).
- **CI Fail Fast**: Use `--maxfail=1` or `--stop-on-failure` (where supported) to reduce feedback latency.
- **Test Naming**: Use `test_<module>_<behavior>_<condition>` (e.g., `test_users_endpoint_returns_200_on_success`).
- **Mock External Dependencies**: Stub database calls (if any), third-party APIs, and time-sensitive logic using `unittest.mock` or Vitest’s `vi.fn()`.

## Future Improvements

- Introduce a `tests/` directory and migrate ad-hoc test code into organized modules.
- Add fixtures for common user roles (admin, guest) to support role-based endpoint tests.
- Implement snapshot testing for UI components with `@vue/test-utils` + `jest-serializer-vue`.
- Enhance E2E coverage for common user journeys (login → dashboard → create item).
- Consider **contract testing** (e.g., Pact) between frontend and backend to decouple releases.

---  
*This guide is maintained alongside the repository and updated as testing infrastructure evolves.*
