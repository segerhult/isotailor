# Deployment

This repository is a fullstack application composed of a Python-based backend API server and a Vue.js-based frontend web application, served using NGINX. The deployment process leverages Docker and Docker Compose for containerization, ensuring consistency across development, staging, and production environments. Below is a comprehensive guide covering environment requirements, dependencies, building, running, configuration, and advanced deployment considerations.

---

## Prerequisites

Before deploying the application, ensure the following tools are installed on your target machine:

- **Docker Engine**: Version 20.10 or newer. Install via:
  - **Ubuntu/Debian**:  
    ```bash
    sudo apt-get update && sudo apt-get install docker.io docker-compose-plugin
    ```
  - **macOS (Homebrew)**:  
    ```bash
    brew install docker docker-compose
    ```
  - **Windows (WSL2)**: Install Docker Desktop for Windows, which includes both Docker Engine and Docker Compose.

- **Docker Compose**: Recommended as a standalone plugin (`docker compose` subcommand) or as a separate binary (`docker-compose`). Verify with:
  ```bash
  docker compose version
  ```

- **Git**: Required to clone the repository. Install via your OS package manager or download from [git-scm.com](https://git-scm.com/).

> **Note**: While Docker simplifies deployment, if you choose to run the application natively (not recommended), you must separately install:
> - Python 3.11+ and `pip` (for the backend)
> - Node.js 18+ and `npm` (for building the frontend)
>
> However, native deployment requires manual dependency resolution, port configuration, and static asset serving—Docker is strongly preferred.

---

## Repository Structure Overview

Understanding the structure is crucial for deployment decisions:

```
.
├── .dockerignore           # Excludes unnecessary files from backend build context
├── .gitignore              # Git ignore rules (development artifacts)
├── Dockerfile              # Backend image: built from python:3.11-slim
├── docker-compose.yml      # Orchestrates frontend + backend services
├── server.py               # Python backend (simple HTTP server)
├── web/
│   ├── .dockerignore       # Frontend build context exclusions
│   ├── Dockerfile          # NGINX-based frontend image
│   ├── nginx.conf          # Static asset server and reverse proxy config
│   ├── package.json        # Vue.js dependencies (including Vite)
│   ├── vite.config.js      # Vite build configuration
│   └── src/
│       ├── App.vue
│       ├── api.js          # API client module
│       └── main.js
└── README.md
```

The backend (`server.py`) is a lightweight Python HTTP service listening on port `8080` (default). The frontend is a Vue.js Single Page Application (SPA) built with Vite, served statically via NGINX on port `80`.

---

## Build and Run with Docker Compose

The simplest way to deploy the application is using `docker-compose.yml`. This file defines three services:

| Service Name | Image Context | Role                        | Ports         |
|--------------|---------------|-----------------------------|---------------|
| `web`        | `nginx:alpine`| NGINX reverse proxy and static file server | `80:80`, `443:443` |
| `app`        | `./app`       | Backend application (Not present yet in repo root) | Internal only |
| `db`         | `postgres:15-alpine` | PostgreSQL database | `5432:5432` |

> **Note**: The `docker-compose.yml` file includes references to services (`app`, `db`) that are not yet implemented in the root directory, but the configuration is provided as a baseline template.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repo-name>
```

### 2. Build and Start Containers

```bash
docker compose up --build -d
```

This command:
- Builds images as defined (currently only the NGINX web service and PostgreSQL database).
- Starts containers in detached mode.
- Automatically creates a user-defined bridge network for inter-service communication.
- Maps `localhost:80` → frontend (NGINX), `localhost:5432` → database.

> **Note**: The `app` service build context is set to `./app` but no corresponding Dockerfile exists yet. You must create this directory and Dockerfile before the full stack can run.

To verify services are running:
```bash
docker compose ps
```

To check logs in real-time:
```bash
docker compose logs -f
```

### 3. Access the Application

- **Frontend UI**: Open `http://localhost` in a browser.
- **Backend API**: Access at `http://localhost:8080` (once backend is properly integrated).
- **API Client Behavior**: The Vue frontend (`web/src/api.js`) uses relative paths (e.g., `/api/...`) under the assumption that NGINX (port 80) proxies requests to the backend.

---

## Configuration & Environment Variables

### Backend (`server.py`)

The backend server (`server.py`) runs directly on port `8080` and does not currently use environment variables. It serves the following:
- Root path `/` — HTML form for software selection.
- `GET /api/software` — returns list of available software.
- `POST /api/manifest` — builds and returns a custom ISO installation manifest.
- File upload endpoints: `/api/upload` and `/api/uploads`.

If environment variables are introduced in future versions (e.g., for database or external service configuration), they should be set via:
- A `.env` file in the project root (for local dev):
  ```env
  SECRET_KEY=my-very-secret-key
  ```
- Docker secrets (production).
- Host-level environment variables (if using `docker-compose --env-file`).

### Frontend (`web/`)

Static configuration is baked into the NGINX config (`web/nginx.conf`), which includes:
- `try_files $uri /index.html;` for SPA routing.
- Proxy pass to `http://backend:8080/api` for API requests (subject to `docker-compose.yml` network naming).

Dynamic frontend config (e.g., API base URL) is typically injected at build time. Vite supports `.env` files in the frontend directory:
- Create `web/.env.production`:
  ```env
  VITE_API_BASE=/api
  ```
- This gets resolved at build time (`vite.config.js` should include `defineConfig({ define: { 'process.env': {} } })` or use Vite’s `import.meta.env`).

---

## Manual Deployment (Advanced)

While Docker Compose is the recommended method, you may deploy services individually.

### Backend (Python)

1. **Run the server**:
   ```bash
   python server.py
   ```

2. Ensure the `data/` directory exists and is writable (for uploads and manifests).

### Frontend (Vue.js + NGINX)

1. **Build the SPA**:
   ```bash
   cd web
   npm ci && npm run build
   ```

2. **Serve static files** with NGINX:
   ```bash
   docker run -d \
     -p 80:80 \
     -v $(pwd)/dist:/usr/share/nginx/html:ro \
     -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
     nginx:alpine
   ```

> **Caution**: This method does not handle API proxying unless `nginx.conf` correctly routes `/api` requests to the backend.

---

## Production Considerations

| Area              | Recommendation                                                                 |
|-------------------|--------------------------------------------------------------------------------|
| **Security**      | - Never expose backend (`8080`) directly to the public internet.<br>- Use HTTPS (terminate TLS at NGINX or a reverse proxy like Traefik).<br>- Set environment variables for secrets if introduced. |
| **Scalability**   | - Scale the backend service once deployed in Docker.<br>- Use a process manager (e.g., `gunicorn`) if running natively. |
| **Persistence**   | - Mount volumes for persistent data (e.g., `data/` for uploaded files and manifest index).<br>- Example in `docker-compose.yml`: `volumes: - ./data:/app/data`. |
| **Health Checks** | Add `HEALTHCHECK` instructions to `Dockerfile`s once stable.                   |
| **CI/CD**         | The `.github/workflows/main.yml` suggests GitHub Actions integration—ensure builds and tests run on `docker compose build`. |

---

## Troubleshooting

### Common Issues

| Symptom                        | Likely Cause                                      | Fix                                                                 |
|--------------------------------|---------------------------------------------------|----------------------------------------------------------------------|
| `frontend` fails to start      | NGINX config syntax error                         | Validate `web/nginx.conf` using `nginx -t` in a dev container.     |
| API calls fail (404/502)       | Mismatched proxy target in `nginx.conf`          | Ensure `proxy_pass` points to correct host:port (`http://backend:8080/api`). |
| Backend connection refused     | Services not on same Docker network              | Confirm `docker-compose.yml` defines a shared network.             |
| Vue app shows blank page       | Missing `history` mode support in NGINX          | Confirm `try_files $uri /index.html;` is in `nginx.conf`.          |
| Upload or manifest fails       | `data/` directory missing or not writable        | Create `data/` directory with correct permissions.                 |

### Debugging Tips

- **Inspect container logs**:
  ```bash
  docker compose logs web db
  ```
- **Exec into a running container**:
  ```bash
  docker compose exec web sh
  docker compose exec db sh
  ```
- **Check backend health**:
  ```bash
  curl http://localhost:8080/
  ```

---

## Updating the Application

To deploy a new version:

1. Pull latest code:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart services:
   ```bash
   docker compose up --build -d
   ```

No manual cache clearing or configuration migration is needed if only code changes—Docker ensures idempotent builds.

> **Note**: For data schema changes or persistent storage enhancements (e.g., `data/uploads.json`), implement them in `server.py` and verify migration logic before deployment.

---

## Support & Further Reading

- [Docker Documentation](https://docs.docker.com/)
- [Vue CLI Deployment Guide](https://vuejs.org/guide/scaling-up/tooling.html#build-tools)
- [NGINX Reverse Proxy Configuration](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

This deployment guide is versioned with the repository. Refer to `docker-compose.yml`, `Dockerfile`, and `server.py` for runtime specifics.