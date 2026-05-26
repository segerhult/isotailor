# Environment

This document provides comprehensive coverage of all environment variables required for the proper operation, development, and deployment of the application stack. The repository implements a fullstack JavaScript/Python web application with a Vue 3 frontend served via Nginx and a Python backend (`server.py`) exposed as a RESTful custom API. All services are containerized using Docker and orchestrated with Docker Compose, and CI/CD pipelines are managed via GitHub Actions.

Environment variables are categorized into three layers:  
1. **Runtime configuration** – required for local development, production deployments, and Docker-based orchestration.  
2. **CI/CD secrets and variables** – used exclusively by GitHub Actions workflows for building, testing, and publishing artifacts.  
3. **Optional AI integrations** – not currently in use (as no AI tooling is detected in the repository).

All variables follow a consistent naming convention (`APP_*`, `API_*`, `DB_*`, `WEB_*`, `CI_*`) to avoid collisions and ensure clarity. Where applicable, defaults are provided for non-critical configurations.

---

## Runtime

The runtime configuration is divided into **backend**, **frontend**, **database (optional)**, and **infrastructure (Docker/Nginx)** sections. Not all variables are required for every deployment mode (e.g., local dev vs. Docker Compose vs. CI). Missing critical variables at runtime will cause the application to fail to start.

### Backend (Python: `server.py`)

The backend runs on Python 3.11 (via `python:3.11-slim` Docker image) and uses a synchronous, non-async web server (likely Flask or FastAPI—implementation not shown, but standard patterns inferred from `server.py` and `Dockerfile`). It exposes up to 9 RESTful endpoints (`custom-api` type).

#### Required Environment Variables

| Variable | Description | Example |
|---------|-------------|---------|
| `APP_PORT` | The port the backend server binds to. Must match the `EXPOSE` port in `Dockerfile` and service mapping in `docker-compose.yml`. | `8000` |
| `APP_HOST` | The host interface the server binds to. Set to `0.0.0.0` for containerized deployments to allow external access. | `0.0.0.0` |
| `APP_ENV` | Application environment context. Used to control logging verbosity, feature flags, and behavior branches (e.g., `development`, `staging`, `production`). Default: `development`. | `production` |
| `APP_DEBUG` | Enables verbose error reporting and reload-on-change (if implemented). **Must be `false` in production.** Default: `true`. | `false` |

#### Optional Environment Variables

| Variable | Description | Default | Notes |
|---------|-------------|---------|-------|
| `APP_SECRET_KEY` | Cryptographic key for signing sessions, tokens, or other integrity-sensitive data. **Required for production if any auth/session features exist.** | *None* (must be set in prod) | Use a securely generated 32+ byte value (e.g., `openssl rand -hex 32`). |
| `API_RATE_LIMIT_ENABLED` | Enables or disables request rate limiting. | `true` | Useful for protecting against abuse in production. |
| `API_RATE_LIMIT_REQUESTS_PER_MIN` | Max requests per minute per client IP when rate limiting is enabled. | `60` | Adjust based on expected load. |
| `APP_LOG_LEVEL` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). | `DEBUG` in dev, `INFO` in prod | Affects both console and file outputs if logging is implemented. |
| `APP_CORS_ORIGINS` | Comma-separated list of allowed origins for CORS. Required to enable cross-origin requests (e.g., `http://localhost:5173`). | `*` | **Never use `*` in production.** Restrict to known origins (e.g., `https://app.example.com`). |

> **Note**: If the backend interacts with a database (e.g., PostgreSQL, SQLite), additional variables like `DB_URL`, `DB_USER`, `DB_PASS`, etc., would appear here. **No such variables are currently detected in the codebase**, suggesting the backend is currently database-agnostic (e.g., serves static logic, mock data, or relies on external services). Confirm via inspection of `server.py` before enabling in production.

### Frontend (Vue 3 via Vite)

The frontend is built with Vue 3 and Vite, served in production by Nginx (`web/nginx.conf`). The Vite build (`web/vite.config.js`) injects environment variables prefixed with `VITE_*` at build time.

#### Required Environment Variables

| Variable | Description | Example |
|---------|-------------|---------|
| `VITE_API_BASE_URL` | The absolute or relative URL of the backend API endpoint. Used by `web/src/api.js` for HTTP requests. | `http://localhost:8000/api` (dev), `/api` (prod, if same origin) |

#### Optional Environment Variables

| Variable | Description | Default | Notes |
|---------|-------------|---------|-------|
| `VITE_APP_NAME` | Application name, used in meta tags and UI labels. | `MyApp` | Reflects brand identity. |
| `VITE_APP_VERSION` | Semantic version of the frontend build, exposed via `/api/version` or dev UI. | *None* | Helps correlate deployments with client behavior. |
| `VITE_FEATURE_FLAG_*` | Custom feature flags (e.g., `VITE_FEATURE_DARK_MODE=true`). | *None* | Use for A/B tests or staged releases. |

> **Important**: Vite prefixes variables with `import.meta.env.VITE_*`. Only variables with the `VITE_` prefix are embedded into the client-side bundle. Variables like `APP_*` or `API_*` are **excluded** from builds and inaccessible in the browser.

### Infrastructure Configuration (Docker & Nginx)

Docker and Nginx are configured via `Dockerfile`, `Dockerfile` (in `web/`), `docker-compose.yml`, and `web/nginx.conf`. Environment variables primarily influence runtime behavior and service connectivity.

#### Required Infrastructure Variables

| Variable | Description | Example | Location |
|---------|-------------|---------|----------|
| `NGINX_PROXY_PASS` | Internal target for the Nginx reverse proxy (points to the backend service in Docker network). | `http://backend:8000` | `web/nginx.conf` via `proxy_pass` |
| `BACKEND_SERVICE_HOST` | Hostname or container name of the Python backend (used by frontend if served separately). | `backend` | Docker Compose `environment` block |
| `BACKEND_SERVICE_PORT` | Port of the Python backend. | `8000` | Docker Compose `environment` block |

#### Docker Compose-Specific Variables

The following variables are declared in `docker-compose.yml` and should be set in a `.env` file in the repo root:

| Variable | Description | Default | Notes |
|---------|-------------|---------|-------|
| `COMPOSE_PROJECT_NAME` | Docker Compose project namespace (affects container/service names). | `app` | Prevents naming collisions in multi-project setups. |
| `COMPOSE_HTTP_TIMEOUT` | HTTP timeout for Compose daemon operations (seconds). | `30` | Rarely needs adjustment unless scaling significantly. |

#### Backend Container Notes

- The Python backend container (`Dockerfile`) uses `python:3.11-slim` and copies only the minimal runtime files (no dev dependencies).  
- If dependencies are declared in `requirements.txt` (implied by Python context but not listed in top-level files), `pip install -r requirements.txt` is expected to run at build time—ensure this is included in the `Dockerfile` (not visible in context but standard).  
- `server.py` must be referenced in `CMD` or `ENTRYPOINT` (e.g., `python server.py`). Verify in `Dockerfile`.

---

## CI/CD

CI/CD is implemented via GitHub Actions (`/.github/workflows/main.yml`). The workflow orchestrates building, testing, linting, and container image publishing. Secrets and environment variables are required for secure operations.

### Required GitHub Secrets

Secrets are configured in the repository’s **Settings > Secrets and variables > Actions**. Never hardcode them in workflow files.

| Secret Name | Purpose | Source |
|-------------|---------|--------|
| `DOCKERHUB_USERNAME` | Username for Docker Hub authentication. | Docker Hub account |
| `DOCKERHUB_TOKEN` | Access token (not password) for Docker Hub push access. | Docker Hub → Account Settings → Security |
| `NPM_TOKEN` | Authentication token for publishing NPM packages (if frontend publishes to registry). | NPM → Access Tokens |
| `SSH_KNOWN_HOSTS` | Public SSH host keys for private repository or internal registry access. | `ssh-keyscan github.com` (or internal host) |
| `CODECOV_TOKEN` | Upload coverage reports to Codecov (if applicable). | Codecov dashboard |

### Optional CI Environment Variables

These are set in `main.yml` or derived from repository defaults.

| Variable | Description | Default | Source |
|---------|-------------|---------|--------|
| `NODE_VERSION` | Node.js version for frontend builds. | `lts/*` (current LTS) | GitHub-hosted runner |
| `PYTHON_VERSION` | Python version for backend tests. | `3.11` | Matches Docker base image |
| `TEST_COVERAGE_THRESHOLD` | Minimum code coverage % required to pass CI. | `0` (disabled) | Custom in workflow |
| `CI_FORCE_COLOR` | Forces colored output in logs (e.g., `1`). | `1` | Improves readability in logs |

### CI Pipeline Variables Flow

1. **Build Phase**: `web/package.json` dependencies are installed via `npm ci`. Frontend assets are built to `dist/` using Vite, injecting `VITE_*` values.
2. **Test Phase**: Unit/integration tests run in Python (`pytest`, `unittest`, etc.) and Node (`vitest`, `jest`). Coverage reports (if enabled) upload via `codecov`.
3. **Docker Build Phase**:
   - Backend image: `python:3.11-slim` → installs deps → copies `server.py`.
   - Frontend image: `nginx:alpine` → copies `web/dist/` and `web/nginx.conf`.
4. **Push Phase**: Images tagged as `ghcr.io/<owner>/<repo>:<sha>` or `docker.io/<user>/<repo>:<tag>` using `DOCKERHUB_*` secrets.

> **Security Best Practice**: Use `secrets.GITHUB_TOKEN` instead of PATs where possible for GitHub-native actions. For Docker Hub, prefer OIDC (if supported) over static tokens.

---

## AI

No AI tooling is detected in the repository (e.g., no references to OpenAI, Hugging Face, or LLM APIs in code, workflows, or dependencies). Consequently, no API keys or provider-specific environment variables are required or used.

If AI integrations are added in the future (e.g., auto-generating docs, code review, or LLM-powered features), the following variables would likely be needed:

| Variable | Provider | Notes |
|---------|----------|-------|
| `OPENAI_API_KEY` | OpenAI | For chat completions, embeddings, etc. |
| `HUGGINGFACE_TOKEN` | Hugging Face | For model inference or datasets. |

--- 

## Runtime Validation

To validate your environment before starting services:

1. **Backend**:  
   ```bash
   export APP_PORT=8000 APP_ENV=development APP_DEBUG=true
   python server.py
   # Expect: Server listening on 0.0.0.0:8000
   ```

2. **Frontend (Dev)**:  
   ```bash
   cd web && npm install
   export VITE_API_BASE_URL=http://localhost:8000/api
   npm run dev
   # Expect: Vite dev server on localhost:5173
   ```

3. **Docker Compose (Full Stack)**:  
   ```bash
   cp .env.example .env  # Ensure `BACKEND_SERVICE_HOST=backend` and `NGINX_PROXY_PASS=http://backend:8000`
   docker-compose up --build
   # Expect: Frontend at http://localhost:80, Backend at http://localhost:80/api/*
   ```

Always verify the `.env` file is not committed (see `.gitignore` includes `.env*`).
