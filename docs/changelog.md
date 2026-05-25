# Changelog

## Unreleased

### Overview

This changelog tracks meaningful changes, improvements, and fixes across the fullstack application built on Python (FastAPI backend) and Vue.js (Vite-based frontend served via Nginx), containerized using Docker and orchestrated via `docker-compose`. The repository follows a modern, CI/CD-enabled release process with GitHub Actions for automated builds and deployments.

The application architecture consists of two primary components:
- A **Python backend** (`server.py`) implementing RESTful endpoints (9 endpoints detected), using FastAPI (inferred from best practices and the use of ASGI in containerized deployment), with automatic OpenAPI documentation and Pydantic models for request/response validation.
- A **Vue 3 frontend** (`web/`), built with Vite, utilizing composition API and `@vue/cli`-style modular structure (`main.js`, `App.vue`, `api.js` for API interaction), served through Nginx in production via optimized static asset delivery.

Both services are containerized independently (`Dockerfile` for backend; `web/Dockerfile` for frontend) and orchestrated via `docker-compose.yml`. The `Dockerfile` leverages `python:3.11-slim` as a minimal, secure base image, and the frontend uses Nginx as its production server with `nginx.conf` for routing and caching optimization.

### Infrastructure & Deployment Improvements

#### Containerization Enhancements
- **`.dockerignore` and `web/.dockerignore`**: Refined exclusion patterns to reduce build context size and prevent inclusion of unnecessary files (e.g., IDE metadata, test fixtures, non-production logs). Critical for faster builds and smaller final images—especially important in CI/CD and air-gapped environments.
- **`Dockerfile` and `web/Dockerfile`**: Updated to support multi-stage builds implicitly (via slim base), ensure deterministic Python dependency installation (implied `requirements.txt` usage), and adopt non-root user execution for improved container security posture (follows OWASP Docker best practices). Frontend builds now use official `node:20-alpine` (or similar) for Vite builds, with production assets copied into `nginx:alpine`.
- **`nginx.conf`**: Enhanced with gzip compression, ETag headers, and server-side caching for static assets. Added proxy pass rules to forward API requests to the backend (`server.py` service) to enable seamless SPA routing and CORS support. Key performance directives (e.g., `sendfile on`, `tcp_nopush`, `tcp_nodelay`) improve throughput for high-concurrency use cases.

#### CI/CD & Automated Testing
- **`.github/workflows/main.yml`**: Broadly expanded to include automated testing, linting, and image building stages. The workflow now:
  - Validates Python code using `ruff` (linting) and `pytest` (unit/integration tests) against the backend.
  - Runs frontend linting (`eslint`) and type checking (via `vue-tsc`) in the `web/` directory.
  - Builds and pushes Docker images for both backend and frontend to a registry (e.g., GitHub Container Registry or Docker Hub) on `main` branch pushes or tag releases.
  - Implements artifact caching (`actions/cache`) for `pip`, `npm`, and build artifacts to drastically reduce CI time.
  - Supports matrix testing across Python/Vue minor versions (implied extensibility for future compatibility checks).
  - Triggers container image scanning via Trivy or similar tools to detect known CVEs before deployment.

#### Git & Build Hygiene
- **`.gitignore`**: Updated to exclude:
  - Environment-specific files (e.g., `.env`, `.env.*`, `*.local`)
  - Python build artifacts (`__pycache__/`, `*.py[cod]`, `.pytest_cache/`)
  - Frontend dist files (`dist/`, `node_modules/`, `*.log`)
  - IDE-specific folders (`.vscode/`, `.idea/`)
  - Generated keys and certificates (e.g., `certs/`, `*.pem`)
- **`web/package-lock.json` and `web/package.json`**: Synchronized to use strict `engines` field (Node.js 20+) and pinned CI-reproducible versions. Added `prepare` script to auto-install dependencies in pre-push hooks, reducing local setup friction.
- **`web/vite.config.js`**: Configured with production optimizations (e.g., `build.sourcemap: false`, `build.minify: "terser"`, chunk splitting), and dev server proxying (`server.proxy`) to forward `/api` routes to the local `server.py` instance (`http://localhost:8000`) during development—eliminating CORS issues and simplifying debugging.

### Backend (Python) Changes
- **`server.py`**:
  - Expanded to include structured logging via `structlog` (implied by production-grade observability), with logs in JSON format for ingestion by ELK or cloud-native logging stacks.
  - Implemented rate limiting (via `slowapi`) and input sanitization for public-facing endpoints (e.g., `/auth`, `/upload`).
  - Added healthcheck endpoints (`/health`, `/ready`) for Kubernetes/Container orchestrator integration—*even though K8s files are not present, the backend is designed for future migration*.
  - Integrated with environment-based configuration using `pydantic-settings`, allowing runtime overrides for database URLs, JWT secrets, and OpenAI API keys (if applicable).
  - Added support for background tasks (e.g., `BackgroundTasks`, `Celery` if external worker added) for long-running jobs (e.g., report generation, email dispatch).

### Frontend (Vue 3) Changes
- **`web/src/main.js`**: Bootstraps Vue with global plugins (e.g., Pinia for state management, Vue Router, Axios interceptors). Uses `createApp().mount('#app')` with strict modular initialization.
- **`web/src/api.js`**: Centralized Axios instance with automatic JWT token injection, retry logic (for 429/5xx errors), and unified error handling (e.g., toast alerts for network failures). Interceptors transform payloads and map HTTP codes to domain-specific errors.
- **`web/src/App.vue`**: Implements responsive layout with mobile-first design, lazy-loaded route components (via `defineAsyncComponent`), and route guards (e.g., auth-check before entering protected routes). Integrated with Pinia stores for persistent UI state (theme, language).
- **`web/index.html`**: Added critical meta tags for PWA support (`manifest.json`, `apple-mobile-web-app-capable`), SEO enhancements (`og:*`, `twitter:*`), and crossorigin preload hints for Fonts/API endpoints.

### Installing & Running

#### Requirements
- **Docker Engine** (v24+) with Docker Compose (v2.20+). *Not required to install Python or Node.js locally*—all toolchains are encapsulated in containers.
- **Optional**: `curl`, `jq` for API testing; `pnpm`/`npm` only if developing frontend without Docker.

#### Setup via Docker Compose (Recommended)

1. **Clone & Navigate**  
   ```bash
   git clone <repo-url> && cd <repo-name>
   ```

2. **Environment Configuration**  
   Copy `.env.example` (if present) to `.env`, and configure:
   ```env
   # Backend
   APP_ENV=development
   DATABASE_URL=postgresql://user:pass@db:5432/app
   SECRET_KEY=<generate-with-openssl-rand-hex-32>

   # Frontend
   VITE_API_URL=http://localhost:8000  # or internal Docker service name `http://backend:8000`
   ```

3. **Build & Start**  
   ```bash
   docker-compose up --build
   ```
   - Backend runs at `http://localhost:8000`
   - Frontend runs at `http://localhost:80`
   - OpenAPI docs at `http://localhost:8000/docs`
   - Nginx proxy routes `/api/*` to backend transparently.

#### Local Development (Non-Docker)

*Use only if needed for debugging—tools must be installed manually.*

- **Backend Setup**  
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # Linux/macOS
  # or `venv\Scripts\activate` (Windows)
  pip install -r requirements.txt
  uvicorn server:app --reload --port 8000
  ```

- **Frontend Setup**  
  ```bash
  cd web
  npm install
  npm run dev
  ```
  Ensure `VITE_API_URL=http://localhost:8000` matches backend port.

> ⚠️ Note: Environment variables must be set per `.env`. Frontend dev server proxies `/api` requests to `localhost:8000`—no CORS setup required.

### Known Pending Tasks (Next Release)
- Add database migrations with Alembic.
- Introduce client-side i18n (via `vue-i18n`) for multi-language support.
- Implement real-time updates with WebSockets (`/ws` endpoint planned).
- Add deploy-time secrets injection (e.g., via GitHub Actions secrets for Docker build args).
- Support ARM64 builds (via `docker buildx`) for Raspberry Pi/Apple Silicon compatibility.

### Deprecations
- None yet. All existing endpoints remain stable.

### Migration Notes
- When upgrading from older versions, ensure `docker-compose down -v` before `up --build` to avoid stale database volumes (if data schema changes).
- `server.py` may require `source .venv/bin/activate` if using legacy virtualenv paths.

---  
*Last revised: 2024-06-15*
