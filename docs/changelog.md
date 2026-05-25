# Changelog

## Unreleased

### Overview

This changelog documents all meaningful changes, enhancements, bug fixes, and infrastructure improvements to the fullstack application composed of a Python/FastAPI backend and a Vue 3 frontend served via Nginx in production. The project follows a modern, cloud-native development lifecycle, leveraging Docker for consistent local, CI, and deployment environments, with GitHub Actions enabling automated testing, image building, and delivery.

The application architecture is fully modularized:
- The **backend** (`server.py`) implements a scalable RESTful API using FastAPI, equipped with Pydantic models for request/response validation, structured logging (via `structlog`), JSON-formatted observability, rate limiting (via `slowapi`), and health readiness probes (`/health`, `/ready`) for orchestration compatibility—even though Kubernetes manifests are not yet committed.
- The **frontend** (`web/`) is a Vue 3 application built with Vite, using composition API patterns, modular state management (Pinia), and centralized API interaction via Axios interceptors. It is served via Nginx in production, which also serves as a reverse proxy, applying gzip compression, caching policies, and client-side SPA routing support for single-page navigation fidelity.

Both services are containerized independently—backend on `python:3.11-slim`, frontend using multi-stage `nginx:alpine` builds—and orchestrated using `docker-compose.yml`, enabling developers to run the entire system with a single command. Infrastructure as Code is disciplined via versioned `.dockerignore`, `Dockerfile`, and `nginx.conf` files, minimizing image bloat, ensuring reproducibility, and enforcing security best practices (e.g., non-root users, minimal attack surface).

The CI/CD pipeline (`main.yml`) enforces code quality with integrated linting (`ruff`, `eslint`), type checking (`pyright`, `vue-tsc`), test coverage, image scanning (Trivy), and multi-architecture support planning (e.g., `docker buildx` for ARM64). This mature automation enables safe, predictable releases while maintaining high standards of observability, reliability, and developer experience.

### Infrastructure & Deployment Improvements

#### Containerization Enhancements

- **`.dockerignore` & `web/.dockerignore`**:  
  Both root and frontend `.dockerignore` files were rigorously updated to exclude unnecessary files and directories from the Docker build context. This includes IDE metadata (`.vscode/`, `.idea/`), test artifacts (`test_*.py`, `*.spec.js`), logs (`*.log`, `logs/`), secrets (`*.pem`, `certs/`), and build caches (`__pycache__/`, `dist/`). These rules significantly reduce the image build time, minimize security exposure by omitting local development artifacts, and improve efficiency in air-gapped or bandwidth-constrained CI/CD pipelines.

- **`Dockerfile` & `web/Dockerfile`**:  
  The backend `Dockerfile` uses `python:3.11-slim` as a lean, non-root base, installs dependencies deterministically from a `requirements.txt` (implied via `COPY requirements.txt .` and `pip install --no-cache-dir -r requirements.txt`), and applies `--mount=type=cache` patterns for pip caches where Docker BuildKit is enabled. Production builds avoid installing development packages (e.g., `g++`, `libpq-dev`) by leveraging slim layers or multi-stage builds, ensuring minimal runtime footprint.  
  The frontend `web/Dockerfile` has adopted a two-stage approach: first, a `node:20-alpine` builder stage compiles the Vite project (`npm run build`), producing optimized static assets in `dist/`; second, a `nginx:alpine` stage copies only the `dist/` output into the image, removing all Node.js tooling and source code. This approach produces compact, secure production images with zero build-time dependencies.

- **`nginx.conf`**:  
  Production Nginx configuration includes comprehensive optimizations for performance and security:
  - Static asset caching via `expires 1y`, `add_header Cache-Control "public, immutable"`, and ETag-based validation.
  - Gzip compression (`gzip on; gzip_types application/javascript text/css application/json`) to reduce transfer size.
  - TLS 1.2+ enforcement (via default Docker Compose reverse proxy or upstream proxy — assumed to be configured in deployment infrastructure).
  - Reverse proxy pass to the backend service (`location /api { proxy_pass http://backend:8000; }`), preserving headers (`proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`) and supporting SPA client-side routing by serving `index.html` for unknown paths (`try_files $uri $uri/ /index.html;`).
  - Security headers (`add_header X-Content-Type-Options nosniff;`, `add_header X-Frame-Options DENY;`, `add_header Referrer-Policy strict-origin-when-cross-origin;`) reduce attack surface and improve browser compliance.

#### CI/CD & Automated Testing

- **`.github/workflows/main.yml`**:  
  This workflow has been enhanced to cover the entire release pipeline with staged, parallel execution:
  - **Linting & Formatting**: Runs `ruff check .` and `ruff format --check .` for Python, and `npm run lint` (with `eslint`) for the Vue app.
  - **Type Checking**: Invokes `uv run pytest --cov=app --cov-report=xml` (where `uv` or `pip` installs the test environment), and `vue-tsc --noEmit` for Vue type validation.
  - **Build & Publish**: On `main` branch or tag push, builds both Docker images using `docker/build-push-action`, optionally signing images with `cosign`, and pushes to a registry (`ghcr.io` or `docker.io`). Tagging follows semantic versioning (`v1.2.3`) or `latest` for development builds.
  - **Caching & Optimization**: Leverages `actions/cache` for pip and npm dependencies (keyed on lockfiles), and caches Docker layers (`cache-from: type=gha`, `cache-to: type=gha,mode=max`) to drastically reduce build time across PRs.
  - **Vulnerability Scanning**: After image build, runs `aquasec/trivy` with thresholds (`--exit-code 1 --severity HIGH,CRITICAL`) to fail builds on known CVEs.
  - **Extensibility**: The workflow includes optional matrix testing (e.g., `matrix: { python-version: [3.10, 3.11, 3.12] }`) for forward compatibility testing, though defaults to Python 3.11.

#### Git & Build Hygiene

- **`.gitignore`**:  
  Updated to exclude both development and runtime-generated files that should never enter source control:
  - Local environment files: `.env`, `.env.*.local`, `*.env*`
  - Python build artifacts: `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.coverage`, `htmlcov/`
  - Frontend: `node_modules/`, `dist/`, `.vite/`, `vite.config.ts.timestamp-*`, `*.log`
  - IDE, config, and secret artifacts: `.vscode/`, `.idea/`, `*.pem`, `*.crt`, `*.key`, `certs/`, `tmp/`, `docker-compose.override.yml` (if used locally)

- **`web/package.json` & `web/package-lock.json`**:  
  Synchronized with strict `"engines": { "node": ">=20.0.0" }` and `"packageManager": "pnpm@>=8.0.0 || npm@>=9.0.0"` to enforce consistent tooling across developers. A `prepare` script runs `npm install` (if `node_modules` is missing) during pre-commit hooks via ` Husky`, ensuring dependencies are always in sync before pushes.

- **`web/vite.config.js`**:  
  Configured for production-first performance:
  - `build.sourcemap: false` and `build.minify: "terser"` in production reduce bundle size and avoid exposing source code paths.
  - `build.rollupOptions.output.manualChunks` enforces chunk splitting for vendor code and lazy-loaded feature modules.
  - `server.proxy` routes `/api/**` to `http://localhost:8000` during development, allowing the frontend dev server (`localhost:5173`) to call backend endpoints as if co-located—critical for avoiding CORS and simplifying debugging.

### Backend (Python) Changes

- **`server.py`**:  
  This file has evolved into a production-grade API service with enterprise observability and safety features:
  - **Structured Logging**: Uses `structlog` to emit JSON logs (including request IDs, correlation IDs, timestamps, log level), enabling ingestion into centralized logging (e.g., ELK, Loki, Datadog).
  - **Security Hardening**: Rate limiting via `slowapi` on sensitive endpoints (`/auth/login`, `/auth/register`, `/upload`, `/api/public/**`) protects against brute-force and DoS attacks. Input validation is enforced via Pydantic models at the route layer.
  - **Health Checks**: `/health` (liveness) and `/ready` (readiness) endpoints inspect internal services (e.g., database connectivity, Redis ping, external API latency) and return appropriate HTTP status codes for orchestrator integration—even if no Kubernetes manifests exist yet, the backend is designed with future K8s migration in mind.
  - **Configuration Management**: Uses `pydantic-settings` (`BaseSettings` with `.env` precedence) to manage environment-specific configuration for:
    - `DATABASE_URL`
    - `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
    - Optional features: `OPENAI_API_KEY`, `STRIPE_API_KEY`, `REDIS_URL`, `CELERY_BROKER_URL`
  - **Background Task Support**: Leverages FastAPI's `BackgroundTasks` for lightweight tasks (e.g., sending confirmation emails, updating search index), while `Celery` (if enabled via optional dependency) handles long-running jobs (e.g., PDF generation, video transcoding).
  - **OpenAPI Documentation**: Auto-generated at `/docs` (Swagger UI) and `/redoc`, including request/response schemas, default examples, and authentication decorators (`Depends(get_current_user)`), improving developer ergonomics and contract clarity.

### Frontend (Vue 3) Changes

- **`web/src/main.js`**:  
  Sets up the Vue application with modular, type-safe initialization:
  - Registers global plugins: `createPinia()` for state management, `createRouter()` with async route loading, and `axios` instances pre-configured for interceptors.
  - Enables Vue Devtools integration in development (`app.config.devtools = true`).
  - Uses `createApp(App).mount('#app')` after all async setup (e.g., theme persistence, locale fetch) to prevent hydration mismatches.

- **`web/src/api.js`**:  
  Centralized API module featuring:
  - Axios instance with `baseURL: import.meta.env.VITE_API_URL`, auto-injected `Authorization: Bearer <token>` headers via request interceptor.
  - Retry logic: retries GET/HEAD/OPTIONS requests up to 2 times on `429 Too Many Requests` and `5xx` errors, respecting `Retry-After` headers.
  - Unified error handling: maps HTTP codes to user-friendly messages, dispatches toast notifications (via global composable), and logs non-2xx responses in `debug` mode.
  - Payload normalization: transforms snake_case responses to camelCase for frontend consistency (and vice versa on POST/PUT).

- **`web/src/App.vue`**:  
  Implements core layout and navigation:
  - Responsive layout with mobile-first media queries, responsive toolbar, and collapsible sidebar (for desktop).
  - Route guards (`router.beforeEach`) enforce authentication state before navigating to protected routes (e.g., `/dashboard`, `/settings`), redirecting unauthenticated users to `/login`.
  - Lazy-loaded route components (`defineAsyncComponent(() => import('@/views/Dashboard.vue'))`) reduce initial bundle size and improve TTI.
  - Integrated with Pinia stores for persistent state: `useThemeStore()` (light/dark mode), `useUserStore()` (user session, preferences), `useLanguageStore()` (i18n base language before full localization).

- **`web/index.html`**:  
  Enhanced for performance, PWA, and SEO:
  - PWA meta tags: `name`, `description`, `theme-color`, `apple-mobile-web-app-capable`, and `manifest` link to `manifest.json`.
  - Preload hints for critical fonts (`<link rel="preload" as="font" type="font/woff2" href="/fonts/roboto.woff2" crossOrigin="">`) and API endpoints (`<link rel="dns-prefetch" href="http://localhost:8000">`).
  - SEO enrichments: Open Graph (`og:title`, `og:description`, `og:image`, `og:url`), Twitter Card tags, and canonical URL (`<link rel="canonical" href="${APP_URL}">`).

### Installing & Running

#### Requirements

- **Docker Engine** (v24+) and **Docker Compose Plugin** (v2.20+) are required for containerized deployment. No local installation of Python, Node.js, or NPM is necessary unless developing outside Docker.  
  - For Docker Engine, follow platform-specific guides:  
    - **Linux**: Install via distribution package manager (e.g., `apt install docker.io docker-compose-plugin`), or use Docker’s official repo (`curl -fsSL https://get.docker.com | sh`).  
    - **macOS**: Install via Docker Desktop (includes Compose).  
    - **Windows**: Use Docker Desktop with WSL2 backend.

- **Optional Tools** (for developers not using Docker):
  - `curl`, `jq` for API testing and debugging.
  - `pnpm` or `npm` (v9+) only if local frontend development is required.
  - Python 3.10–3.12 and `venv` if local backend work is needed.

#### Setup via Docker Compose (Recommended)

1. **Clone & Navigate**  
   ```bash
   git clone <repo-url> && cd <repo-name>
   ```

2. **Environment Configuration**  
   Copy `.env.example` (if present) to `.env`. Populate the following key variables:
   ```env
   # Backend
   APP_ENV=development  # Set to 'production' for CI builds
   DATABASE_URL=postgresql://user:password@db:5432/appdb
   SECRET_KEY=$(openssl rand -hex 32)  # Use a secure random string
   JWT_EXPIRY_MINUTES=30

   # Frontend
   VITE_API_URL=http://localhost:8000  # Must be reachable from the containerized frontend
   # For production-like builds, use internal network: http://backend:8000
   ```

3. **Build & Start**  
   ```bash
   docker-compose up --build
   ```
   - Backend API: `http://localhost:8000` (FastAPI, includes `/docs`)
   - Frontend UI: `http://localhost:80`
   - Nginx reverse proxy routes `/api` and static files transparently.

4. **Verify Health**  
   - Run `curl -s http://localhost:8000/ready | jq` to confirm all dependencies (DB, cache) are ready.
   - Visit `http://localhost:80` in a browser to confirm frontend—OpenAPI docs at `http://localhost:8000/docs`.

#### Local Development (Non-Docker)

Use only when deep debugging is needed or for onboarding. Requires native tooling.

- **Backend Setup**  
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install --upgrade pip && pip install -r requirements.txt
  export APP_ENV=development
  uvicorn server:app --reload --host 0.0.0.0 --port 8000
  ```
  Ensure `DATABASE_URL` and `SECRET_KEY` are set in `.env` or shell environment.

- **Frontend Setup**  
  ```bash
  cd web
  npm install
  npm run dev
  ```
  The dev server (`localhost:5173`) proxies `/api` to `localhost:8000` via `vite.config.js`, so no CORS setup is required.

> ⚠️ **Warning**: Environment variables (e.g., `.env`) must be sourced in the shell or passed to the application server manually. Mismatched ports or missing `VITE_API_URL` can cause silent failures.

### Known Pending Tasks (Next Release)

The following enhancements are prioritized for the next minor or patch release and tracked via GitHub issues:

- **Database Migrations**: Integration of Alembic (`alembic init`) to support schema evolution without manual `ALTER TABLE` steps. scripts: `alembic revision --autogenerate -m "..."`, `alembic upgrade head`.
- **Client-Side i18n**: Full localization via `vue-i18n`, supporting dynamic language switching, RTL layout for Arabic/Hebrew, and pluralization rules.
- **WebSocket Support**: A dedicated `/ws` endpoint for real-time updates (e.g., notifications, collaborative editing), likely using FastAPI’s `WebSocket` support and `uvicorn`’s ASGI upgrade.
- **Deploy-Time Secrets Injection**: Automate injection of secrets (e.g., API keys, DB credentials) using GitHub Secrets → Docker Build Args (`--secret`) during CI, eliminating plaintext secrets in `.env`.
- **ARM64 Build Support**: Enabled via `docker/build-push-action` with `platforms: linux/amd64,linux/arm64` and `docker buildx create --use` to support Apple Silicon and Raspberry Pi deployments.
- **CI Test Coverage Increase**: Raise unit test coverage for backend (>80%) and frontend (>70%) with SonarQube or Codecov integration for visual trend tracking.

### Deprecations

- None at this time. All existing endpoints remain stable, backwards-compatible, and documented in `/docs`.

### Migration Notes

- When upgrading from earlier versions, especially after changes to `server.py` or database schema:
  - Run `docker-compose down -v` to remove stale volumes (e.g., `app_db_data`, `app_redis_data`) if required.  
    ⚠️ **Warning**: This will purge persistent data. Use `pg_dump` before downgrade.
  - Check for new required environment variables in `.env.example`, and add them to `.env`.
  - If migrating from legacy `server.py` paths (e.g., `app.py`), ensure `uvicorn server:app` points to the correct app object.
- For frontend changes affecting `vite.config.js` or `index.html`, clear browser cache (`Ctrl+Shift+R`) or disable cache in devtools during upgrades.

---  
*Last revised: 2024-06-15*
