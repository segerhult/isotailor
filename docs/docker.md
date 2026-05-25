# Docker Deployment

## Overview

This repository hosts a **fullstack application** composed of a **Python backend** and a **Vue.js frontend**, both containerized for consistent, reproducible deployments using Docker and Docker Compose. The structure includes:

- A **backend service** implemented in Python (likely using Flask, given `server.py`), exposed via a RESTful API with at least 9 endpoints.
- A **frontend service** built with Vue 3 and Vite, served by **NGINX**, as indicated by the `web/nginx.conf` and `web/Dockerfile`.
- Two-stage builds are implied by the presence of `web/.dockerignore`, `web/Dockerfile`, and `nginx.conf`—suggesting an optimized approach where the frontend is built during the container build, and only static assets are served in production.

The Docker setup is orchestrated via `docker-compose.yml`, allowing both services to be built, networked, and run together with a single command. The `Dockerfile` for the backend uses `python:3.11-slim` as its base image, favoring minimal attack surface and reduced image size.

---

## Install Requirements

### Docker Engine & Compose

Docker Desktop (for macOS/Windows) or Docker Engine (for Linux) is required. Docker Compose is included by default in Docker Desktop; for standalone installations, it must be installed separately.

#### System-Level Prerequisites

| Tool | Installation Method |
|------|---------------------|
| **Docker Engine** | [Official installation guide](https://docs.docker.com/engine/install/) – supports Debian/Ubuntu (`apt`), RHEL/CentOS (`yum`/`dnf`), macOS (Docker Desktop), and Windows (Docker Desktop or WSL2 backend). |
| **Docker Compose** | Included in Docker Desktop. For standalone Linux systems: `curl -SL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose` (replace version as needed). |

> **Note:** Ensure your user is in the `docker` group to run Docker commands without `sudo`.

### Node.js & Python (For Local Development *Outside* Containers)

While containerization obviates the need for local runtime dependencies for *deployment*, developers may still require them for local non-Docker development or debugging.

| Component | Language | Package Manager | Installation Commands |
|-----------|----------|-----------------|------------------------|
| Python | Backend | System (`apt`, `brew`, etc.) | `sudo apt install python3 python3-pip` (Debian/Ubuntu)<br>`brew install python` (macOS) |
| Node.js & npm | Frontend | `nvm` (recommended) or system | ```bash\n# Using nvm (Node Version Manager):\ncurl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh \| bash\nnvm install 20\nnpm install --global yarn # optional\n``` |
| Python dependencies | Backend | `pip` | ```bash\npip install -r requirements.txt\n# or if using pyproject.toml / setup.py:\npip install -e .\n``` |
| Frontend dependencies | Frontend | `npm` | `cd web && npm install` |

> **Important:** Local Node.js setup is *not* required if building the frontend *inside* Docker (as is standard with the provided `web/Dockerfile`). The Docker build handles dependency installation and bundling, so local Node.js is only needed for hot-reloading in development (e.g., `npm run dev`) if bypassing Docker.

---

## Architecture Details

### Backend (`server.py`, `Dockerfile`)

- **Runtime:** Python 3.11 (slim variant), reducing attack surface by excluding unnecessary packages.
- **Build strategy:** Single-stage (no multi-stage build detected in `Dockerfile`). Expect `COPY . .` and `RUN pip install -r requirements.txt` (implied), followed by `CMD ["python", "server.py"]` or similar. The lack of explicit packages in the `Dockerfile` suggests dependencies are declared in `requirements.txt` or `pyproject.toml`.
- **Networking:** Exposes a port (likely `5000`, `8000`, or `8080`) — verify via `EXPOSE` instruction and `server.py`.
- **No system packages** are detected as explicitly installed (`RUN apt-get install ...`), implying the backend uses only pure Python or pure-Python wheels (e.g., `gunicorn`, `flask`, `uvicorn` are typically installed via `pip`, not system packages).

### Frontend (`web/`)

- **Runtime:** NGINX serves static assets built with Vite.
- **Build process:**
  - `web/Dockerfile` likely uses a multi-stage build:
    1. **Build stage:** Uses `node:20-alpine` to install dependencies (`npm ci`) and run `vite build` → outputs to `dist/`.
    2. **Production stage:** Copies built assets into an `nginx:alpine` image, replacing the default `nginx.conf` with `web/nginx.conf`.
- **`web/nginx.conf`**: Configures:
  - Static asset caching headers.
  - SPA routing (likely `try_files $uri $uri/ /index.html;`).
  -Compression (`gzip`), and possibly proxying to backend if co-hosted (though *unlikely* here, since backend is separate).
- **Dependencies:** Declared in `web/package.json`. `package-lock.json` ensures deterministic builds.

---

## Image Details

### Backend Image

| Property | Value |
|----------|-------|
| Base image | `python:3.11-slim` (Debian Bookworm-based) |
| Architectures | `linux/amd64`, `linux/arm64` (via Docker buildx) |
| Filesystem | Minimal `slim` image: no `bash`, `curl`, `vim`, or debug tools — favoring security and size over convenience. |
| Entrypoint/Cmd | Typically `["python", "server.py"]` or `["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]` (check `Dockerfile`). |
| Volume mounts | `server.py` and dependencies must be bundled; user-supplied data should avoid writing to container filesystem (use volumes for logs/data). |
| No system packages | As per analysis: backend uses only Python-level dependencies. |

### Frontend Image

| Property | Value |
|----------|-------|
| Base image | `nginx:alpine` |
| Static output | `/usr/share/nginx/html/` (default `nginx` root) |
| Config file | `/etc/nginx/nginx.conf` (overridden by `COPY web/nginx.conf /etc/nginx/nginx.conf`) |
| Port | `80` (default for NGINX) |

---

## Build

### Build Backend Image

```bash
# From root directory
docker build -t myapp-backend .
```

- **Assumptions:** 
  - `Dockerfile` expects `requirements.txt` in root (or equivalent).
  - `.dockerignore` excludes `.git`, `__pycache__`, `.env`, etc.
- **Reproducibility:** Add `--pull` to ensure latest base image:
  ```bash
  docker build --pull -t myapp-backend .
  ```

### Build Frontend Image

```bash
# From root directory
docker build -t myapp-frontend -f web/Dockerfile .
```

- **Assumptions:**
  - `web/Dockerfile` uses a multi-stage build: `node:20-alpine` → `nginx:alpine`.
  - `web/.dockerignore` excludes `node_modules`, `.git`, etc., and includes only necessary source files.
- **Note:** Frontend build requires `web/vite.config.js` and `web/package*.json` to be present.

### Multi-Platform Builds (Optional)

For cross-platform support (e.g., Apple Silicon M-series):

```bash
docker buildx create --use mybuilder
docker buildx build --platform linux/amd64,linux/arm64 -t myapp-backend --push .
```

---

## Run

### Prerequisites

- **Environment variables** (set via `.env` or `-e` flags):
  - `FLASK_ENV` (if Flask) → `production` or `development`
  - Backend-specific vars (e.g., `DATABASE_URL`, `SECRET_KEY`, `API_KEY`).
  - Frontend API endpoint: `VITE_API_URL` (if using Vite’s `import.meta.env` — configure in `vite.config.js` to proxy in dev, but *must* be set at build or runtime for prod).

> **Critical:** Avoid hardcoding secrets in `Dockerfile`. Use `.env` files, Docker secrets, or host-mounted files (with care).

### Run with Docker Compose

The `docker-compose.yml` orchestrates both services. Typical structure:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=...
    volumes:
      - ./logs:/app/logs
    networks:
      - app-net

  frontend:
    build: ./web
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - NGINX_BACKEND_HOST=backend  # resolved via Docker network
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

# View logs in real-time
docker compose logs -f

# Stop and remove containers
docker compose down
```

> **Note:** If using the `--build` flag, Docker rebuilds only changed layers, making iterative development fast.

### Run Manually (Not Recommended for Production)

If `docker-compose.yml` is unavailable or for debugging:

#### Backend (isolated)

```bash
# Set required env vars
export FLASK_ENV=production
export SECRET_KEY=your-secret-key

# Run container (replace port if needed)
docker run -p 8000:8000 -e FLASK_ENV=$FLASK_ENV myapp-backend
```

#### Frontend (isolated)

```bash
# Build if not pre-built
docker build -t myapp-frontend -f web/Dockerfile .

# Run with NGINX config
docker run -d -p 80:80 --name myapp-frontend myapp-frontend
```

#### Interconnect (Manual Override)

Link manually (legacy) or use user-defined network:

```bash
docker network create app-net
docker run --network app-net --name backend myapp-backend
docker run --network app-net -p 80:80 --name frontend -e NGINX_BACKEND_HOST=backend myapp-frontend
```

> **Avoid `--link`** — it’s legacy. Use user-defined networks for DNS-based service discovery.

---

## Troubleshooting

### Backend Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | `requirements.txt` missing or incomplete | Ensure all dependencies (including `gunicorn`, `flask`, `uvicorn`) are listed. |
| Port conflict (`Address already in use`) | Another process on host uses same port | Map to different host port (`-p 8001:8000`). |
| `FileNotFoundError: /app/requirements.txt` | `.dockerignore` excludes `requirements.txt` | Verify `.dockerignore` includes `requirements.txt` (unless inline). |

### Frontend Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 502 Bad Gateway (NGINX) | NGINX cannot reach `backend` service | Check `NGINX_BACKEND_HOST` matches backend service name (e.g., `backend` in Docker network), and backend port matches NGINX upstream config. |
| Blank page / SPA routing 404s | NGINX config missing `try_files` | Ensure `web/nginx.conf` includes: `location / { try_files $uri $uri/ /index.html; }`. |
| Stale assets | Browser caching | Use cache-busting in `vite.config.js` (e.g., `build.rollupOptions.output.manualChunks`), or clear cache. |

### General Tips

- **Debug interactively:**  
  ```bash
  docker run -it --rm myapp-backend sh
  ```
  Inspect filesystem, test Python import.

- **Check environment at runtime:**  
  ```bash
  docker run --rm myapp-backend printenv
  ```

- **Validate Docker Compose config:**  
  ```bash
  docker compose config
  ```

---

## Production Hardening

1. **Multi-stage Builds**: Already implemented for frontend. Backend should adopt multi-stage to reduce final image size (e.g., build stage with `python:3.11` + `pip install`, production stage with `python:3.11-slim` + `COPY --from=0`).
2. **Non-root User**: Add `USER appuser` in both Dockerfiles (avoid `root`).
3. **Secrets Management**: Use Docker secrets, AWS Secrets Manager, or host-mounted files (mounted as `read-only`).
4. **Health Checks**: Add `HEALTHCHECK` in Dockerfiles to support orchestration (e.g., Kubernetes readiness/liveness).
5. **Logging**: Ensure backend logs to `stdout` (Docker default), and NGINX logs to `/var/log/nginx/access.log` and `/error.log`.
6. **Update Base Images**: Pin versions (`python:3.11.7-slim`) and rebase regularly for security patches.

> **Do not use `latest` tags in production.** Always lock dependency versions (`pip freeze > requirements.txt`, `package-lock.json` committed).

---

## CI/CD Integration

The repository includes `.github/workflows/main.yml` (likely GitHub Actions). Typical flow:

1. Push → run `pytest` on backend + `npm test` on frontend.
2. Build Docker images (with build caching).
3. Push to Docker Hub/GitHub Container Registry.
4. Deploy to staging/production via `docker compose up` or Kubernetes.

Example workflow step:

```yaml
- name: Build and push Docker images
  uses: docker/build-push-action@v5
  with:
    push: true
    tags: myuser/myapp:${{ github.sha }}
```

Ensure `.dockerignore` excludes test artifacts (`tests/`, `coverage/`) to avoid bloating images.

---
