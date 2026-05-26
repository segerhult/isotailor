# Testing

## Overview

This repository hosts a **fullstack application** composed of a Python-based backend API (`server.py`) and a Vue 3–powered frontend (`web/`), served in production using Nginx (configured in `web/nginx.conf`). The testing strategy is intentionally layered and modular, designed to ensure correctness, maintainability, and resilience across development cycles. Tests are structured into three core categories: **unit**, **integration**, and **end-to-end (E2E)**.

- **Unit tests** focus on isolated components and pure functions—validating logic without network or filesystem side effects. For the backend, `pytest` (with `httpx` for synchronous HTTP mocking where needed) and `unittest.mock` provide powerful test fixtures and patching capabilities. For the frontend, Vitest—integrated natively via Vite—enables fast, parallel test runs using `jsdom` for DOM emulation, and supports component rendering, composable testing, and utility function verification through `@vue/test-utils`.

- **Integration tests** verify interactions between cohesive subsystems: backend route handlers with request/response lifecycle, frontend API clients (`web/src/api.js`) with backend endpoints, and state transitions triggered by successful or failing HTTP responses. Backend integration tests simulate real-world behavior by leveraging `pytest` fixtures that initialize temporary app contexts (e.g., via `app.test_client()`), while frontend integration tests often use `@vue/test-utils` with `vi.mock()` to verify API calls against expected backend contract payloads.

- **End-to-end tests** simulate realistic user journeys in an actual browser environment, validating not only API fidelity but also rendering, navigation, and client-side state management. Cypress is used for E2E testing due to its debugging tools, automatic waiting, and robust testability for Vue applications. E2E tests cover critical user workflows (e.g., form submission → API call → confirmation UI update), ensuring the full stack behaves as expected in a user-facing context.

All test pipelines are orchestrated via GitHub Actions (`.github/workflows/main.yml`), executing in reproducible, ephemeral Docker containers. The CI workflow checks out the latest code, provisions Python 3.11 and Node.js 18+ runtimes, installs dependencies, runs linting (ESLint/Pylint via custom scripts or `pre-commit` if configured), type checks (e.g., `mypy` or Vue TSC if enabled), and finally executes the full test suite—unit, integration, and optional E2E—ensuring regressions are caught before merge.

The project uses **containerization as the default test execution environment**, abstracting environment variance. Both `Dockerfile` (backend) and `web/Dockerfile` (frontend) define minimal, reproducible images based on `python:3.11-slim` and `nginx:alpine`, respectively. `docker-compose.yml` orchestrates the full stack during local development and E2E testing, exposing services on predictable ports (e.g., backend on `8000`, frontend via Nginx on `80`). This means tests can run identically across local machines, CI runners, and CI providers without manual environment setup.

## Install Requirements

### Prerequisites

While Docker provides full environment isolation, local development and rapid debugging require the following tools to be installed system-wide:

- **Python 3.11 or higher**  
  Required for the backend API (`server.py`). Confirm with `python --version` or `python3 --version`.  
  *Installation*:
  - **macOS (Homebrew)**: `brew install python@3.11`
  - **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install python3.11 python3.11-venv`
  - **Windows**: Download from [python.org](https://www.python.org/downloads/); ensure *Add to PATH* is checked during installation.

- **Node.js 18.x (LTS) or higher**  
  Required for the frontend (`web/`), including `npm`, `vite`, and build tooling.  
  *Installation*:
  - **macOS (Homebrew)**: `brew install node@18`
  - **Ubuntu/Debian**: Use [NodeSource repos](https://github.com/nodesource/distributions):  
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ```
  - **Windows**: Download and run `.msi` installer from [nodejs.org](https://nodejs.org/).

- **Docker Engine & Docker Compose (recommended)**  
  Enables consistent, reproducible test and development environments independent of host configuration.  
  *Installation*:
  - **macOS/Windows**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
  - **Ubuntu/Debian**:  
    ```bash
    sudo apt-get install docker.io docker-compose-plugin
    sudo usermod -aG docker $USER  # Log out and back in to apply group changes
    ```
  - **Verify installation**: `docker --version && docker compose version`.

> 🚨 **Important**: Even with Docker installed, `docker-compose` may require elevated permissions depending on system group membership. Run `docker ps` to confirm access before proceeding.

### Backend Setup (Python)

Testing dependencies for the backend are **not declared in a `requirements-dev.txt` file** in the current repository context, and the `Dockerfile` builds on a clean `python:3.11-slim` base with no pre-installed test tools. Therefore, to run tests **outside Docker**, create a dedicated `requirements-dev.txt` in the project root with:

```
pytest
pytest-cov
httpx
pytest-asyncio   # If backend uses async endpoints (e.g., with FastAPI/Starlette)
```

Install using `pip` (preferably in a virtual environment to avoid global pollution):

```bash
# Recommended: Use a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install base + dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

> 🔔 **Note**: If `requirements.txt` does not yet exist, define it with core runtime dependencies (e.g., `fastapi`, `uvicorn`, `pydantic`) based on `server.py`. If the backend uses an ORM like SQLAlchemy or PostgreSQL (not visible in current context), include its dev/test packages (e.g., `pytest-alembic`) and mock data libraries (`faker`, `factory-boy`).

The backend is **stateless during tests**—no persistent database is required. It relies on in-memory data structures and `pytest` fixtures (e.g., `@pytest.fixture`) to manage test isolation and data reset between test runs. If backend logic later integrates with external services (databases, queues), use `unittest.mock.patch` or `pytest-mock` to stub them.

### Frontend Setup (JavaScript/TypeScript)

Frontend testing relies on **Vitest** for fast, Vite-native unit testing and **Cypress** for E2E. While the `web/package.json` already declares dev dependencies (e.g., `vitest`, `@vue/test-utils`, `jsdom`), ensure they match current versions:

1. Navigate to `web/` and install dependencies:

```bash
cd web
npm install
```

2. Confirm presence of required dev dependencies:

```bash
npm ls vitest @vue/test-utils @vitejs/plugin-vue jsdom
# If missing, add explicitly:
npm install --save-dev vitest @vue/test-utils @vitejs/plugin-vue jsdom
```

3. Configure `vite.config.js` to enable Vitest with DOM support and coverage:

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { coverageConfigDefault } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts', // Optional: custom setup (e.g., global mocks)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/main.ts',       // App entrypoint
        'src/router/*',      // Router config
        'src/views/**',      // View components (often integration targets)
        'src/App.vue'        // Root component (usually low-unit-value)
      ]
    }
  }
})
```

4. (Optional) Create a `src/test/setup.ts` to configure globals (e.g., mock `$t` for i18n, or axios interceptors).

5. **For Cypress E2E testing**, install separately:

```bash
npm install --save-dev cypress
npx cypress install
```

6. Add `cypress.config.js` in the `web/` root:

```js
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:8080', // Matches Nginx port in `web/nginx.conf`
    supportFile: 'src/test/e2e/support/index.ts',
    specPattern: 'src/test/e2e/specs/**/*.cy.{js,jsx,ts,tsx}',
    fixturesFolder: 'src/test/e2e/fixtures',
    video: true,
    screenshotOnRunFailure: true
  }
})
```

> 🔔 **Note**: Cypress requires GUI libraries on Linux (e.g., `libgtk-3-0`, `libnss3`) for headless Chrome. In Docker, install via `apt` in `web/Dockerfile`. For local Mac/Windows, no additional system dependencies are required.

## Running Tests Locally

### Backend Tests (Python)

From the **repository root**, invoke `pytest` with the backend module as the target:

```bash
# Unit & integration tests with line coverage, verbose output
pytest server.py --cov=. --cov-report=term-missing -v

# If a `tests/` directory is created (see Best Practices), prefer:
pytest tests/ --cov=. --cov-report=term-missing -v
```

Common flags for iterative development:
- `-k 'api and not auth'`: Run tests matching the expression (e.g., all `api` tests excluding `auth`).
- `--maxfail=1`: Stop at first failure to reduce feedback latency.
- `--pdb`: Drop into `pdb` debugger on failure for inspection.
- `--maxfail=0`: Continue through all tests, even after failures (for comprehensive reporting).

> 📌 **Example minimal test structure**:  
> Create `tests/test_server.py`:
> ```python
> import pytest
> from server import app

> @pytest.fixture
> def client():
>     app.config['TESTING'] = True
>     with app.test_client() as client:
>         yield client

> def test_index_returns_200(client):
>     response = client.get('/')
>     assert response.status_code == 200
>     assert b"Welcome" in response.data

> def test_health_check_exists(client):
>     response = client.get('/health')
>     assert response.status_code == 200
>     assert response.json == {"status": "ok"}
> ```

If `server.py` uses FastAPI (indicated by `APIRouter`, `Depends`, etc.), mock database sessions with `@pytest.fixture` using `mocker` or `mock`:

```python
from unittest.mock import MagicMock

@pytest.fixture
def db_session(mocker):
    mock = MagicMock()
    mocker.patch('server.get_db', return_value=mock)
    yield mock
```

### Frontend Unit Tests (Vue + Vitest)

From the `web/` directory:

```bash
# Run all unit tests with coverage report
npm test
# or explicitly:
npx vitest

# Run in watch mode (re-run on file changes)
npm run test:watch

# Generate HTML coverage report (saved in `coverage/`)
npx vitest --coverage
```

To test Vue components interactively:

```bash
# Launch Vitest UI (browser-based test explorer)
npx vitest --ui
# Access at http://localhost:51204
```

Component testing best practices:
- Use `mount()` for full component rendering (DOM, lifecycle, child components).
- Use `shallowMount()` to isolate the component by stubbing children.
- Mock `defineProps`, `defineEmits`, and router/store dependencies via `mocks` option.

### Frontend E2E Tests (Cypress)

From the `web/` directory:

```bash
# Launch interactive Cypress Test Runner (GUI)
npm run cypress:open
# or: npx cypress open

# Run headless tests (for CI or non-GUI environments)
npm run cypress:run
# or: npx cypress run --headless --browser chrome

# Run with debug logging
CYPRESS_DEBUG=1 npx cypress run
```

> 🚨 **Critical Prerequisites**: Before running E2E tests, both services **must be running**:
> 1. **Backend** on `http://localhost:8000`  
> 2. **Frontend** (served via Nginx or Vite dev server) on `http://localhost:8080` (Nginx default) or `http://localhost:5173` (Vite dev).

#### Option A: Run Services Manually (Local Dev)

```bash
# Terminal 1: Start backend (use uvicorn for FastAPI or python -m for Flask)
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Build and serve frontend with Nginx (or Vite dev)
cd web && npm run dev  # for Vite dev server
# or: cd web && npm run build && npx serve -s dist  # for production-like build
```

Set `baseUrl` in `cypress.config.js` accordingly.

#### Option B: Use Docker Compose (Recommended for Reproducibility)

```bash
# Start all services (backend + frontend via Nginx)
docker-compose up --build -d

# Ensure services are ready (backend health check often takes a few seconds)
sleep 10

# Now run E2E tests *inside* the frontend container (if Cypress is installed there),
# or from the host against exposed ports:
npm run cypress:run
```

To run Cypress inside the container, extend `web/Dockerfile`:

```Dockerfile
# ... existing layers ...
RUN apt-get update && apt-get install -y \
    libgtk-3-0 libnss3 libdbus-glib-1-2 libatk1.0-0 libatk-bridge2.0-0 \
    libgdk-pixbuf2.0-0 libpango-1.0-0 libcairo2 libasound2
COPY package*.json ./
RUN npm ci && npx cypress install
CMD ["npx", "cypress", "run", "--headless", "--browser", "chrome"]
```

Then run:

```bash
docker-compose run --rm web npm run cypress:run
```

## Running Tests in CI

The `.github/workflows/main.yml` workflow orchestrates all checks. Below is a *canonical example* reflecting current signals:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      # Optional: Add a PostgreSQL service if backend uses DB
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5

    steps:
      - uses: actions/checkout@v4

      # Backend: Python environment & test
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install backend dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run backend tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term -v
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: backend

      # Frontend: Node.js environment & test
      - name: Use Node.js 18
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: 'web/package-lock.json'

      - name: Install frontend dependencies
        working-directory: web
        run: npm ci

      - name: Run frontend unit tests
        working-directory: web
        run: npm test -- --coverage

      # E2E: Optional (requires services to be available)
      - name: Start Docker Compose services
        run: docker-compose up -d

      - name: Wait for backend to be healthy
        run: |
          until curl -s http://localhost:8000/health | grep -q '"status":"ok"'; do
            sleep 2
          done

      - name: Run Cypress E2E tests
        uses: cypress-io/github-action@v6
        with:
          working-directory: web
          wait-on: 'http://localhost:8000'
          browser: chrome
          config: baseUrl=http://localhost:8080  # matches Nginx
        env:
          CYPRESS_baseUrl: http://localhost:8080
```

> 🔔 **Key Considerations**:
> - Use `npm ci` (not `npm install`) in CI for deterministic builds.
> - Pin action versions (e.g., `@v4`, `@v5`) for stability.
> - For E2E, `docker-compose up` runs services in detached mode. Add a health-check step to avoid flaky timing.
> - If E2E is not required for every PR (e.g., only on `main`), gate behind an environment variable (`if: github.ref == 'refs/heads/main'`).

## Test Coverage & Reporting

### Backend Coverage

Generated via `pytest-cov`, with XML output for integration with CI coverage dashboards:

```bash
pytest --cov=. --cov-report=term-missing --cov-report=xml
```

- `term-missing`: Highlights uncovered lines directly in the terminal.
- `xml`: Outputs `coverage.xml`, consumable by tools like Codecov or Coveralls.

For integration with Codecov in CI, the workflow snippet:

```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage.xml
    flags: backend
    name: backend-coverage
```

### Frontend Coverage

Vitest generates reports in multiple formats. Configure `vite.config.js` coverage block to include JSON/HTML for archiving:

```bash
npx vitest --coverage
# Outputs: coverage/*.html (browser-readable), coverage/coverage-final.json
```

To upload to coverage tools in CI:

```yaml
- name: Upload frontend coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./web/coverage/coverage-final.json
    flags: frontend
    name: frontend-coverage
```

## Best Practices

### State Isolation & Determinism
- **Backend**: Use `@pytest.fixture(scope="function")` (default) to reset app state per test. Avoid global `unittest.mock.patch`—use `mocker` fixture instead.
- **Frontend**: Use Vitest’s `afterEach` or `vi.clearAllMocks()` to reset mocks between tests. Mock time-sensitive APIs (`Date.now`, `setTimeout`) via `vi.useFakeTimers()`.

### API Contract Testing
- Ensure `web/src/api.js` includes tests for all 9 backend endpoints (per heuristic). For each:
  - Verify request path, method, headers (e.g., `Content-Type`).
  - Assert response status, shape (e.g., `{ data: [...] }` vs `{ error: ... }`).
  - Test error paths (e.g., 401/403/500).
- Use `vi.mock('axios')` to stub responses and verify payloads.

### CI Fail Fast & Feedback
- Use `--maxfail=1` for both `pytest` and `vitest` to stop after first failure—reduces resource usage and time-to-feedback.
- In E2E, configure Cypress to stop on first failure:  
  `npx cypress run --record --key ${{ secrets.CYPRESS_RECORD_KEY }} --ci-build-id $GITHUB_RUN_ID`

### Test Naming & Organization
- **Backend**: `test_<resource>_<action>_<condition>` (e.g., `test_users_post_create_saves_to_db`).
- **Frontend**: `<component>_<behavior>_<scenario>` (e.g., `UserList_shows_loading_when_fetching`).
- Organize tests in mirrored directory structures (e.g., `tests/server/test_auth.py`, `web/src/components/UserList.spec.js`).

### Mocking External Dependencies
- **Database**: Stub with `mocker.patch('server.db.get_user', return_value=user_mock)`.
- **Third-party APIs**: Use `httpx_mock` for backend (`pip install httpx-mock`) or `nock`-like utilities for frontend (`vi.mock('axios')`).
- **Time/Random**: Freeze time via `freezegun` (backend) or `vi.setSystemTime()` (frontend).

### E2E Test Stability
- **Avoid flaky waits**: Use Cypress’s built-in assertions (e.g., `cy.get('.item').should('have.length', 3)`) instead of `cy.wait(1000)`.
- **Test user journeys, not implementation**: Focus on UI outcomes (`user sees success message`), not element selectors (`clicks button#submit`).

## Future Improvements

- **Formalize Test Directory Structure**: Migrate ad-hoc test code into organized modules (`tests/unit/`, `tests/integration/`, `web/src/test/unit/`, `web/src/test/e2e/`).
- **Role-Based Testing**: Add fixtures for user roles (e.g., `admin`, `guest`) to test authorization flows (`test_admin_can_delete_user`).
- **Snapshot Testing**: Enable UI snapshotting for Vue components to catch unintended rendering changes (requires `@vue/test-utils` + `jest-serializer-vue` or Vitest plugin).
- **Contract Testing**: Introduce Pact or Spectral to validate API contracts between frontend and backend, decoupling releases.
- **Accessibility (a11y) Testing**: Add `cypress-axe` for automated WCAG checks in E2E tests.
- **Performance Thresholds**: Track Largest Contentful Paint (LCP) and Cumulative Layout Shift (CLS) via Lighthouse CI or Cypress plugins.
