# Docker Deployment

## Overview

This repository hosts a **fullstack application** composed of a **Python backend** and a **Vue.js frontend**, both containerized for consistent, reproducible deployments using Docker and Docker Compose. The architecture is designed for maintainability, scalability, and production readiness:

- A **backend service** implemented in Python (likely Flask, inferred from `server.py`), exposing a RESTful API with at least 9 endpoints. It runs in a minimal Python environment (`python:3.11-slim`) for reduced attack surface and fast startup time.
- A **frontend service** built with Vue 3 (via Vite), bundled during Docker build, and served statically via NGINX (`web/nginx.conf`). Multi-stage builds optimize image size: Node.js is only used for building, not for production serving.
- Both services are orchestrated via `docker-compose.yml`, enabling effortless local development, CI integration, and deployment to orchestrated environments.

The setup leverages modern Docker best practices: slim base images, non-root users (recommended but not yet enforced), deterministic builds (via pinned versions and lock files), and production-grade configurations (e.g., SPA routing, caching headers, health checks). The `.dockerignore` files ensure only necessary files are included in builds, improving cache efficiency and security.

---

## Install Requirements

### Docker Engine & Compose

Docker Desktop (for macOS/Windows) or Docker Engine (for Linux) is required. Docker Compose is included by default in Docker Desktop v2.0+; for standalone Linux systems, it must be installed separately.

#### System-Level Prerequisites

| Tool | Installation Method |
|------|---------------------|
| **Docker Engine** | [Official installation guide](https://docs.docker.com/engine/install/) – supports Debian/Ubuntu (`apt`), RHEL/CentOS (`yum`/`dnf`), macOS (Docker Desktop), and Windows (Docker Desktop or WSL2 backend). |
| **Docker Compose** | Included in Docker Desktop. For standalone Linux systems: <br> `curl -SL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose` (update version as needed). |

> **Important:** To avoid `permission denied` errors when running Docker without `sudo`, add your user to the `docker` group: `sudo usermod -aG docker $USER`. Log out and back in for changes to take effect.

### Node.js & Python (For Local Development *Outside* Containers)

While the Docker-based approach eliminates local dependency requirements for *running* the app, developers may still need them for:
- Debugging issues isolated to the host environment
- Running development servers with hot-reload (e.g., `npm run dev`, `flask run`)
- Non-Docker CI pipelines or local unit testing

| Component | Language | Package Manager | Installation Commands |
|-----------|----------|-----------------|------------------------|
| Python | Backend | System (`apt`, `brew`, etc.) | `sudo apt install python3 python3-pip` (Debian/Ubuntu)<br>`brew install python` (macOS) |
| Node.js & npm | Frontend | `nvm` (recommended) or system | ```bash\n# Using nvm (Node Version Manager):\ncurl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh \| bash\nnvm install 20\n# (Optional) Install Yarn globally\nnpm install --global yarn\n``` |
| Python dependencies | Backend | `pip` | ```bash\npip install -r requirements.txt\n# or if using pyproject.toml / setup.py:\npip install -e .\n``` |
| Frontend dependencies | Frontend | `npm` | `cd web && npm install` |

> **Critical Note:** Local Node.js is *not required* for production Docker builds. The `web/Dockerfile` uses a multi-stage build: a `node:20-alpine` stage compiles the Vue app into static assets (`dist/`), which are then copied into a minimal `nginx:alpine` image. Local Node.js is only needed if developing without Docker (e.g., `npm run dev` for live previews).

---

## Architecture Details

### Backend (`server.py`, `Dockerfile`)

- **Runtime Environment:** Python 3.11 (slim variant based on Debian Bookworm), optimizing for minimal size and reduced attack surface. All dependencies are pure Python packages (e.g., Flask, Gunicorn, requests) installed via `pip`—no system packages are installed (`RUN apt-get install` is absent in the Dockerfile).
- **Build Strategy:** Single-stage build implied by the Dockerfile. The `Dockerfile` likely follows this pattern:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8000  # (or other port)
  CMD ["python", "server.py"]
  ```
  - Dependencies are declared in `requirements.txt` (or `pyproject.toml` if using `pip install -e .`).
  - `.dockerignore` excludes `__pycache__`, `*.pyc`, `.git`, and `.env` files to keep the image clean and secure.
- **Networking:** The backend listens on a configurable port (commonly `5000`, `8000`, or `8080`). Verify via `EXPOSE` in the Dockerfile and `app.run()` or server startup command in `server.py`. For production, use an ASGI server like `uvicorn` or WSGI server like `gunicorn`.
- **State & Volumes:** The container filesystem is ephemeral. Persistent data (logs, uploads) should be mounted via volumes (e.g., `./logs:/app/logs`).

### Frontend (`web/`)

- **Runtime Environment:** Static assets served by NGINX (`nginx:alpine`). This is lightweight, secure, and battle-tested for static content delivery.
- **Build Process (Multi-Stage):**
  1. **Build Stage (`node:20-alpine`):**
     ```dockerfile
     FROM node:20-alpine AS build
     WORKDIR /app
     COPY web/package*.json ./
     RUN npm ci --only=production || npm install --only=production
     COPY web/ ./
     RUN npm run build  # outputs to /app/dist/
     ```
  2. **Production Stage (`nginx:alpine`):**
     ```dockerfile
     FROM nginx:alpine
     COPY --from=build /app/dist /usr/share/nginx/html
     COPY web/nginx.conf /etc/nginx/conf.d/default.conf
     EXPOSE 80
     CMD ["nginx", "-g", "daemon off;"]
     ```
- **`web/nginx.conf` Configuration Highlights:**
  - SPA routing: `location / { try_files $uri $uri/ /index.html; }` ensures Vue Router handles all client-side routes.
  - Compression: `gzip on; gzip_types text/plain application/json application/javascript;`
  - Caching: `location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ { expires 1y; add_header Cache-Control "public, immutable"; }`
  - Proxy: Unlikely to proxy to backend (as they run as separate services), but if needed, upstream config points to `backend:8000`.
- **Dependencies:** All are declared in `web/package.json`, with `package-lock.json` ensuring deterministic builds. `vite.config.js` defines entry points, plugins, and build options (e.g., `base: '/static/'` if deployed under a subpath).

---

## Image Details

### Backend Image

| Property | Value |
|----------|-------|
| Base image | `python:3.11-slim` (Debian Bookworm-based, ~150MB) |
| Architectures | `linux/amd64`, `linux/arm64` (via Docker Buildx) |
| Filesystem | Minimal: no `bash`, `curl`, `vim`, or shell utilities. Use `python` or `sh` for debugging. |
| Entrypoint/Cmd | `["python", "server.py"]` (if Flask/WSGI) or `["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "server:app"]` (if production WSGI). Verify in `Dockerfile`. |
| Volume mounts | `server.py`, `requirements.txt` must be bundled; user data (e.g., uploads) should use host-mounted volumes. |
| Security | No `root` user required—recommended to add `RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app` and `USER appuser`. |

### Frontend Image

| Property | Value |
|----------|-------|
| Base image | `nginx:alpine` (~15MB) |
| Static output | `/usr/share/nginx/html/` |
| Config file | `/etc/nginx/conf.d/default.conf` (overridden by `web/nginx.conf`) |
| Port | `80` (HTTP) — mapped to host port `80` in `docker-compose.yml`. |
| No runtime dependencies | All dependencies resolved at build time; production image contains only NGINX and static assets. |

---

## Build

### Build Backend Image

```bash
# From repository root
docker build -t myapp-backend .
```

- **Assumptions:**
  - `requirements.txt` exists in root directory with all Python dependencies (e.g., `flask`, `gunicorn`, `requests`).
  - `.dockerignore` excludes `__pycache__`, `venv/`, `.git`, `.env`, `logs/`, and test files (`tests/`, `test_*`).
- **Best Practice:** Ensure reproducibility by pulling latest base image:
  ```bash
  docker build --pull -t myapp-backend .
  ```

### Build Frontend Image

```bash
# From repository root
docker build -t myapp-frontend -f web/Dockerfile .
```

- **Assumptions:**
  - `web/Dockerfile` uses multi-stage build (`node:20-alpine` → `nginx:alpine`).
  - `web/.dockerignore` excludes `node_modules`, `.git`, and unnecessary dev dependencies (e.g., `src/**/*.test.js`).
- **Validation:** After building, verify static assets:
  ```bash
  docker run --rm myapp-frontend ls /usr/share/nginx/html
  # Should output: index.html, assets/, etc.
  ```

### Multi-Platform Builds (Optional)

For cross-platform support (e.g., Apple Silicon M1/M2/M3):

```bash
# Create and use a Buildx builder
docker buildx create --use mybuilder

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myuser/myapp:latest \
  --push .
```

- Requires Docker Buildx (included in Docker Desktop; install separately for Linux: `docker buildx install`).

---

## Run

### Prerequisites

- **Environment variables** must be configured (via `.env` file or `-e` flags):
  - `FLASK_ENV=production` (or `development`)
  - Backend secrets: `SECRET_KEY`, `DATABASE_URL`, `API_KEY` (use strong, unique values)
  - Frontend API endpoint: `VITE_API_URL` (if `vite.config.js` uses `defineConfig({ envPrefix: ['VITE_'] })`)
- **Never hardcode secrets** in Dockerfiles or source code. Use:
  - `.env` files (for local dev)
  - Docker secrets (for orchestrated deployments)
  - Host-mounted secrets files (`--secret type=file,src=./secrets.env`)

### Run with Docker Compose

The `docker-compose.yml` coordinates both services. A representative configuration:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"  # host:container
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./logs:/app/logs
    networks:
      - app-net
    # (Optional) health check
    # healthcheck:
    #   test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    #   interval: 30s
    #   timeout: 10s
    #   retries: 3

  frontend:
    build: ./web
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - NGINX_BACKEND_HOST=backend  # resolves to backend:8000 via Docker DNS
    networks:
      - app-net

networks:
  app-net:
    driver: bridge
```

#### Start Services

```bash
# Build and run in detached mode
docker compose up -d --build

# Stream logs in real-time (Ctrl+C to detach)
docker compose logs -f

# Stop containers, remove networks/volumes
docker compose down -v
```

> **Optimize Iteration:** Add `COMPOSE_DOCKER_CLI_BUILD=1` and `DOCKER_BUILDKIT=1` to enable parallel builds and caching. Modify `server.py` and `web/src/App.vue`—changes are *not* hot-reloaded in production builds (they’re static). For development, use `docker-compose.dev.yml` with bind mounts and live reload.

### Run Manually (Not Recommended for Production)

Use only for debugging or isolated testing.

#### Backend (isolated)

```bash
# Set required env vars (or use .env file)
export SECRET_KEY=$(openssl rand -hex 16)

# Run with port mapping
docker run -p 8000:8000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=$SECRET_KEY \
  myapp-backend
```

#### Frontend (isolated)

```bash
# Build if not pre-built
docker build -t myapp-frontend -f web/Dockerfile .

# Run (NGINX serves on port 80)
docker run -d -p 80:80 --name myapp-frontend myapp-frontend
```

#### Interconnect (Manual Override)

Avoid legacy `--link`. Use user-defined networks for DNS resolution:

```bash
docker network create app-net

# Start backend
docker run --network app-net --name backend myapp-backend

# Start frontend (NGINX upstream: backend:8000)
docker run -d -p 80:80 \
  --network app-net \
  --name frontend \
  -e NGINX_BACKEND_HOST=backend \
  myapp-frontend
```

> **Verify connectivity:** Inside frontend container: `docker exec -it frontend sh` → `wget -qO- http://backend:8000/health`.

---

## Troubleshooting

### Backend Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'flask'` | Missing `flask` in `requirements.txt` | Add `flask>=2.3,<3.0` (pin versions) |
| `Address already in use` | Host port conflict (e.g., `8000` in use) | Map to different host port: `-p 8001:8000` |
| `FileNotFoundError: [Errno 2] No such file or directory: 'requirements.txt'` | `.dockerignore` excludes `requirements.txt` | Verify `.dockerignore` does *not* exclude `requirements.txt`. |
| `ImportError: cannot import name 'app' from 'server'` | `server.py` exports wrong variable (e.g., `app = Flask(__name__)` missing) | In `server.py`, ensure app instance is named `app` or adjust Gunicorn command. |

### Frontend Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `502 Bad Gateway` from NGINX | Backend unreachable at `backend:8000` | Check `NGINX_BACKEND_HOST` matches backend service name; verify backend is running and exposing port `8000`. |
| Blank page / SPA routing `404` for `/about` | Missing `try_files` in NGINX config | In `web/nginx.conf`, ensure `location / { try_files $uri $uri/ /index.html; }` |
| Stale static assets | Aggressive browser caching | Add cache-busting in `vite.config.js`: `build: { rollupOptions: { output: { manualChunks: ... } } }` or set `Cache-Control: no-cache` in `nginx.conf` for `index.html`. |

### General Tips

- **Debug interactively:**  
  ```bash
  docker run -it --rm myapp-backend sh
  # Then run: python -c "import flask; print(flask.__version__)"
  ```

- **Check environment at runtime:**  
  ```bash
  docker run --rm myapp-backend printenv | grep SECRET_KEY
  ```

- **Validate Docker Compose config:**  
  ```bash
  docker compose config
  ```

- **Inspect image layers:**  
  ```bash
  docker history myapp-backend
  ```

---

## Production Hardening

1. **Multi-Stage Backend Build (Recommended)**  
   Reduce final image size by splitting into build/runtime stages:
   ```dockerfile
   FROM python:3.11 AS build
   WORKDIR /build
   COPY requirements.txt .
   RUN pip install --user --no-cache-dir -r requirements.txt

   FROM python:3.11-slim
   WORKDIR /app
   COPY --from=build /root/.local /root/.local
   COPY . .
   ENV PATH=/root/.local/bin:$PATH
   USER appuser
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "server:app"]
   ```

2. **Non-Root User**  
   Add to both Dockerfiles:
   ```dockerfile
   RUN adduser --disabled-password --gecos '' appuser && \
       chown -R appuser /app
   USER appuser
   ```

3. **Secrets Management**  
   - Use `.env` files (with `docker compose -f docker-compose.yml -f docker-compose.prod.yml`)
   - Mount secrets as files:  
     `docker run --secret source=secret_key,target=/run/secrets/secret_key`  
     (requires Docker Swarm/Kubernetes; fallback to host-mounted volumes)

4. **Health Checks**  
   Add to backend Dockerfile:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
   ```

5. **Logging**  
   - Backend: Log to `stdout` (Docker captures automatically)
   - Frontend: NGINX logs to `/var/log/nginx/access.log` and `/var/log/nginx/error.log` (default behavior)

6. **Base Image Updates**  
   - Pin versions: `python:3.11.7-slim`  
   - Rebuild regularly: `docker-compose build --pull`

> **Critical:** Avoid `latest` tags in production. Commit `requirements.txt` and `package-lock.json` to ensure deterministic builds.

---

## CI/CD Integration

The repository includes `.github/workflows/main.yml` (GitHub Actions). A typical pipeline:

1. **On push to `main`:**
   - Run backend tests: `pytest`
   - Run frontend tests: `npm run test:unit`
   - Lint: `ruff`, `eslint`, `stylelint`
2. **Build Docker images** (with BuildKit and caching):
   ```yaml
   - name: Build and push Docker images
     uses: docker/build-push-action@v5
     with:
       push: true
       tags: myuser/myapp:${{ github.sha }}
       cache-from: type=gha
       cache-to: type=gha,mode=max
   ```
3. **Deploy:**
   - Push to Docker Hub/GitHub Container Registry
   - Trigger deployment via `ssh` or `kubectl apply -f`

### Key CI/CD Best Practices

- **`.dockerignore` Exclusions:** Ensure it excludes:
  - `tests/`, `coverage/`, `dist/` (dev/test assets)
  - `node_modules/` (ignored in `web/.dockerignore`, but verify root-level)
  - `.git/`, `.env*`, `*.log`
- **Multi-Stage Builds in CI:** Use `DOCKER_BUILDKIT=1` to enable parallel builds and caching.
- **Security Scanning (Recommended):** Add:
  ```yaml
  - name: Run Trivy vulnerability scanner
    uses: aquasecurity/trivy-action@v0.16.0
    with:
      image-ref: myuser/myapp:${{ github.sha }}
      format: table
      exit-code: 1
  ```

> **Verify Build Reproducibility:** After push, pull the image on another host and run:
> ```bash
> docker run --rm myuser/myapp:${{ github.sha }} python -c "import server; print(server.__version__)"
> ```
