# Deployment

This repository is a fullstack application composed of a Python-based backend API server and a Vue.js-based frontend web application, served using NGINX within a containerized environment. The backend (`server.py`) is a lightweight, asynchronous Python HTTP service built on `aiohttp`, exposing RESTful endpoints such as `/api/software`, `/api/manifest`, `/api/upload`, and `/api/uploads`. The frontend is a Vue 3 Single Page Application (SPA), constructed with Vite and served statically via NGINX, which also acts as a reverse proxy to route API requests to the backend service on port `8080`.

All services—frontend, backend, and optional database—are designed to be deployed using Docker and orchestrated via Docker Compose. This ensures reproducibility across environments, eliminates dependency conflicts, and abstracts platform-specific concerns. The application is not intended for native deployment in production due to the tight coupling of the build artifacts, configuration files (e.g., NGINX reverse proxy), and container networking; however, a manual deployment path is included for advanced users requiring debugging or prototyping capabilities.

The structure enforces separation of concerns: the backend Dockerfile (`Dockerfile` at repository root) builds a minimal Python 3.11-slim image for the API, while the frontend Dockerfile (`web/Dockerfile`) packages a prebuilt static web directory into an `nginx:alpine` image, leveraging multi-stage builds for minimal image size and attack surface.

---

## Prerequisites

Before beginning deployment, ensure the following tools are installed and accessible via your system's command-line interface.

### System-Level Requirements

- **Docker Engine**: Version 20.10 or newer required to support modern Docker Compose features. Install via:
  - **Ubuntu/Debian (Linux)**:
    ```bash
    sudo apt-get update
    sudo apt-get install docker.io docker-compose-plugin
    sudo usermod -aG docker $USER  # Re-login to apply group changes
    ```
  - **macOS (Homebrew)**:
    ```bash
    brew install --cask docker
    # After first launch of Docker Desktop, verify:
    brew install docker-compose
    ```
  - **Windows (WSL2 distro)**:
    - Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/).
    - Enable WSL2 integration for your distro in Docker Desktop settings.
    - Verify from within WSL: `docker --version && docker compose version`.

- **Docker Compose Plugin**: Use the integrated `docker compose` (v2) command. Ensure compatibility via:
  ```bash
  docker compose version
  # Expected output: Docker Compose version v2.x.x
  ```

- **Git**: Required to clone the repository and manage versioning. Install via:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install git
  # macOS (Homebrew)
  brew install git
  # Windows (via Git for Windows)
  ```

### Optional Native Requirements (Not Recommended)

While the application is designed for containerized execution, developers may wish to test or debug locally. This approach is **not recommended for production**, as it requires managing:
- **Python 3.11+** and **`pip`**: Required to run `server.py` directly. Install via your OS package manager or [pyenv](https://github.com/pyenv/pyenv). Ensure `pip` is version 22+:
  ```bash
  python -m pip install --upgrade pip
  ```
- **Node.js 18+** and **`npm`**: Needed to build the Vue.js frontend. Prefer using [nvm](https://github.com/nvm-sh/nvm):
  ```bash
  nvm install 18 && nvm use 18
  npm -v  # Should be ≥ 9.x
  ```

> **Warning**: Native deployments require additional setup for CORS, SSL termination, directory permissions (e.g., `data/`), and NGINX reverse proxy configuration. Use Docker unless absolutely necessary.

---

## Repository Structure Overview

A clear understanding of the layout is essential for diagnosing build failures, configuration mismatches, or networking issues.

```
.
├── .dockerignore           # Prevents unnecessary files (e.g., __pycache__, .env) from entering backend build context
├── .gitignore              # Standard ignore patterns for development (IDE configs, logs)
├── .github/
│   └── workflows/
│       └── main.yml        # GitHub Actions CI pipeline: runs `docker compose build` and unit tests
├── Dockerfile              # Backend image: `python:3.11-slim` base, copies only `server.py`, installs `aiohttp`
├── docker-compose.yml      # Service orchestration: defines `web` (NGINX), `app` (backend), and `db` (PostgreSQL)
├── server.py               # Python HTTP server (aiohttp), listening on `0.0.0.0:8080`
├── README.md
├── web/
│   ├── .dockerignore       # Excludes `node_modules`, `.git`, and debug assets from frontend build context
│   ├── Dockerfile          # Multi-stage: `node:18-alpine` for build → `nginx:alpine` for runtime
│   ├── nginx.conf          # NGINX config: serves static files, proxies `/api/...` to `http://backend:8080`
│   ├── package.json        # Vue 3 + Vite dependencies, scripts (`build`, `dev`)
│   ├── vite.config.js      # Vite config: `build.outDir` set to `dist`, `base: ''` for SPA compatibility
│   └── src/
│       ├── App.vue         # Root Vue component
│       ├── api.js          # API client: axios/`fetch` wrapper, sets `baseURL: import.meta.env.VITE_API_BASE`
│       └── main.js         # Vue app bootstrap
```

Key observations:
- **Backend** (`Dockerfile`): Minimal `COPY` of `server.py` only. Relies on `python:3.11-slim`'s `pip` to install dependencies if `requirements.txt` exists (currently none).
- **Frontend** (`web/Dockerfile`): Two-stage build:
  1. Installs Node.js dependencies, builds with `vite build`.
  2. Copies `dist/` into `nginx:alpine`, replaces default config with `web/nginx.conf`.
- **NGINX**: `nginx.conf` is critical for SPA support (`try_files $uri /index.html`) and API routing (`proxy_pass http://backend:8080/api`).

---

## Build and Run with Docker Compose

Docker Compose simplifies deployment by managing service dependencies, networking, and volume mounts in one command.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repo-name>
```

### 2. Initialize Required Directories

Before first run, ensure critical directories exist:

```bash
mkdir -p data
chmod -R 755 data  # Backend requires write access for uploads/manifests
```

### 3. Build and Start Services

```bash
docker compose up --build -d
```

This command:
- Builds the `web` service using `web/Dockerfile` (frontend build → NGINX image).
- Builds the `app` service (if `Dockerfile` at root is updated) using the base Python image.
- Pulls and starts the `db` service from `postgres:15-alpine` (if enabled).
- Creates a custom bridge network (`<project>_default`) for internal DNS resolution (e.g., `backend` → `app` service).
- Exposes ports:
  - `80` → Frontend (via NGINX).
  - `5432` → PostgreSQL (if `db` service active).
  - **Do not expose `8080` directly** (backend is internal-only).

### 4. Verify Service Status

Check running containers:

```bash
docker compose ps
# Expected output shows `web`, `app`, `db` as `Up`
```

View live logs:

```bash
docker compose logs -f
# Look for: "Application startup complete." (backend), "nginx: [notice] signal process started" (web)
```

### 5. Access the Application

- **Frontend UI**: Open `http://localhost` in your browser.
- **Backend API**: Unreachable directly from host (as intended). Use NGINX proxy at `http://localhost/api/software`.
- **Test Endpoints**:
  ```bash
  curl http://localhost/api/software
  curl -X POST http://localhost/api/manifest -H "Content-Type: application/json" -d '{"os":"Ubuntu","version":"22.04"}'
  ```

---

## Configuration & Environment Variables

### Backend (`server.py`)

Currently, the backend uses **no environment variables** and runs directly on port `8080`. All configuration is hardcoded (e.g., `data/` paths, allowed origins). If future versions introduce environment variables (e.g., `DB_HOST`, `SECRET_KEY`), they should be configured via:

- **Local Development**: Create a `.env` file in the project root:
  ```env
  DB_HOST=host.docker.internal
  DB_PORT=5432
  SECRET_KEY=dev-only-secret
  ```
- **Docker Compose**: Reference variables in `docker-compose.yml`:
  ```yaml
  services:
    app:
      environment:
        - DB_HOST=db
        - SECRET_KEY=${SECRET_KEY}
  ```
- **Production**: Use Docker secrets or a secrets manager (e.g., HashiCorp Vault).

### Frontend (`web/`)

Frontend configuration is injected at **build time** using Vite’s environment variable system. Create `web/.env.production`:

```env
VITE_API_BASE=/api
VITE_APP_TITLE="My Custom ISO Builder"
```

Vite exposes these as `import.meta.env.VITE_API_BASE` in the code (see `web/src/api.js`). Ensure `vite.config.js` does not override `defineConfig({ define: { 'process.env': {} } })` if using legacy `process.env`.

The `nginx.conf` contains static configuration:
```nginx
server {
  listen 80;
  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;  # Enables Vue Router history mode
  }
  location /api {
    proxy_pass http://backend:8080/api;  # Matches backend's listening host:port
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

Ensure `http://backend:8080/api` matches the Docker service name and port.

---

## Manual Deployment (Advanced)

While Docker is preferred, ad-hoc testing or edge-case debugging may require manual deployment.

### Backend (Python)

1. Install dependencies (if any in `requirements.txt`):
   ```bash
   pip install aiohttp
   ```
2. Create the `data/` directory:
   ```bash
   mkdir -p data && chmod 755 data
   ```
3. Run the server:
   ```bash
   python server.py
   # Server starts on http://0.0.0.0:8080
   ```
4. **CORS**: Configure `aiohttp_cors` in `server.py` to allow requests from `localhost:5173` (dev server) or `localhost` (NGINX).

### Frontend (Vue.js + NGINX)

1. Build the static assets:
   ```bash
   cd web
   npm ci  # Ensures exact dependency versions from package-lock.json
   npm run build
   # Generates `web/dist/`
   ```
2. Start NGINX with custom config:
   ```bash
   docker run -d \
     --name frontend \
     -p 80:80 \
     -v $(pwd)/dist:/usr/share/nginx/html:ro \
     -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
     nginx:alpine
   ```

> **Critical**: If `nginx.conf` does not proxy `/api` to `http://localhost:8080`, API calls will fail. Use `http://host.docker.internal:8080` inside NGINX if running on Docker Desktop (macOS/Windows).

---

## Production Considerations

| Area              | Recommendation                                                                 |
|-------------------|--------------------------------------------------------------------------------|
| **Security**      | - **Never expose port `8080`** (backend must be internal-only).<br>- Enable TLS at NGINX: replace `nginx.conf` with one that includes `ssl_certificate` and `ssl_protocols TLSv1.3`.<br>- If `db` is used, set `POSTGRES_PASSWORD` and restrict network access. |
| **Scalability**   | - Scale `app` service: `docker compose up --scale app=3 -d`.<br>- For production, replace `server.py` with `gunicorn -w 4 -k aiohttp.GunicornWebWorker server:app` (requires `gunicorn` and `aiohttp` dependencies). |
| **Persistence**   | - Bind `./data` to the `app` service in `docker-compose.yml`:<br>  ```yaml<br>  app:<br>    volumes:<br>      - ./data:/app/data<br>  ```<br>- For `db`, use named volumes: `volumes: db-data:/var/lib/postgresql/data`. |
| **Health Checks** | Add to `Dockerfile`:<br>  ```dockerfile<br>  HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\<br>    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1<br>  ``` |
| **CI/CD**         | The `.github/workflows/main.yml` builds and tests with `docker compose build` and `docker compose run app pytest`. Ensure no credentials are committed. |

---

## Troubleshooting

### Common Issues

| Symptom                        | Likely Cause                                      | Fix                                                                 |
|--------------------------------|---------------------------------------------------|----------------------------------------------------------------------|
| `docker compose up` fails with `ERROR: Service 'web' failed to build` | Frontend build missing `node_modules` or `dist` | Run `npm ci` manually in `web/` to debug. Check `web/.dockerignore`. |
| `502 Bad Gateway` on `/api/...` | Backend not running or misnamed Docker service    | Check `docker compose ps` for `app` status. Verify `proxy_pass` in `nginx.conf` uses correct service name (`http://backend:8080` vs `http://app:8080`). |
| Vue app shows blank page       | NGINX missing `try_files $uri /index.html;`     | Confirm `web/nginx.conf` includes SPA fallback. Validate with `nginx -t`. |
| Uploads fail (`413 Request Entity Too Large`) | NGINX default body size limit (1MB)           | Add `client_max_body_size 10M;` to `nginx.conf`. |
| `Connection refused` (backend) | Backend container not on same Docker network    | Ensure `docker-compose.yml` uses a custom network (default `bridge` lacks DNS). |

### Debugging Tips

- **Inspect Container Logs**:
  ```bash
  docker compose logs --tail=100 web app db
  # Look for Python tracebacks, NGINX errors, or PostgreSQL startup issues.
  ```
- **Exec into Running Containers**:
  ```bash
  docker compose exec app bash  # Debug backend
  docker compose exec web sh    # Inspect NGINX config
  docker compose exec db psql -U postgres -c '\l'  # List PostgreSQL DBs
  ```
- **Test Backend Connectivity**:
  ```bash
  docker compose exec web curl -v http://app:8080/api/software
  ```
- **Validate NGINX Config**:
  ```bash
  docker compose exec web nginx -t
  ```

---

## Updating the Application

To deploy a new release:

1. Pull latest changes:
   ```bash
   git pull origin main
   ```
2. Rebuild and restart:
   ```bash
   docker compose up --build -d
   ```
3. Verify logs:
   ```bash
   docker compose logs -f
   ```

> **Important**: Data persistence depends on your `docker-compose.yml` configuration. If `./data` is not mounted as a volume, uploaded files/manifests will be lost on restart.

For database migrations or data model changes:
1. Modify `server.py` with migration logic (e.g., `data/uploads.json` schema update).
2. Deploy with `docker compose up -d`.
3. Verify compatibility with existing data (e.g., handle `KeyError` in `POST /api/manifest`).

---

## Support & Further Reading

- [Docker Documentation](https://docs.docker.com/)
- [Vue.js Deployment Guide](https://vuejs.org/guide/scaling-up/tooling.html#build-tools)
- [NGINX Reverse Proxy Tutorial](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [AIOHTTP Production Deployment](https://docs.aiohttp.org/en/stable/deployment.html)
- [Docker Compose Best Practices](https://docs.docker.com/compose/best-practices/)
