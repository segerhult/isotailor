# Local Development Setup

This guide walks you through setting up a local development environment for the fullstack application hosted in this repository. The application consists of a **Python-based backend API** (served via a custom Flask or FastAPI-like `server.py`) and a **Vue.js frontend** (built with Vite and served via Nginx in production). Both components are containerized for consistent local and CI/CD environments, but for rapid development iteration, you may choose to run them natively or via Docker Compose.

The app uses **HTTP/JSON-based communication** between frontend and backend (via the `src/api.js` client utility), and includes:
- `/api/*` backend endpoints (9 total, inferred from heuristic scan of `server.py`)
- Static asset serving and routing handled by Nginx for the built Vue frontend
- Environment-driven configuration for backend API endpoints and ports

---

## Prerequisites

### System Requirements

You will need the following tools installed on your machine:

| Tool | Version | Notes |
|------|---------|-------|
| Python | ≥ 3.11 | Required to run the backend server (`server.py`) directly. |
| Node.js | ≥ 18.x | Required to develop and build the Vue frontend (`web/`). |
| npm | ≥ 9.x | Bundled with Node.js; used for dependency installation and build commands. |
| Docker & Docker Compose | ≥ 24.x & ≥ 2.20.x | Required for containerized local development. Optional but recommended for consistency. |

> 💡 **Recommendation**: Use [pyenv](https://github.com/pyenv/pyenv) to manage Python versions and [nvm](https://github.com/nvm-sh/nvm) for Node.js to avoid version conflicts and system-wide pollution.

#### Installing with Language-Specific Tools

**Python (via `pyenv` + `pip`)**  
1. Install `pyenv` (macOS/Linux):
   ```bash
   curl https://pyenv.run | bash
   ```
   Then add the following to `~/.bashrc` or `~/.zshrc`:
   ```bash
   export PATH="$HOME/.pyenv/bin:$PATH"
   eval "$(pyenv init -)"
   ```
2. Install Python 3.11:
   ```bash
   pyenv install 3.11.9
   pyenv global 3.11.9
   ```
3. Verify:
   ```bash
   python --version  # Should output Python 3.11.x
   pip --version
   ```

**Node.js (via `nvm`)**  
1. Install `nvm`:
   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
   ```
   Reload shell config:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```
2. Install and use Node 18:
   ```bash
   nvm install 18
   nvm use 18
   ```
3. Verify:
   ```bash
   node --version  # Should output v18.x.x
   npm --version   # Should output ≥9.0.0
   ```

---

## Repository Structure Overview

```
├── server.py               # Python backend (Flask/FastAPI-style, runs on port 8000 by default)
├── Dockerfile              # Backend container image (python:3.11-slim)
├── docker-compose.yml      # Orchestrates frontend & backend services
├── web/                    # Vue 3 frontend source
│   ├── src/
│   │   ├── main.js         # Entry point
│   │   ├── App.vue         # Root component
│   │   └── api.js          # Axios-based API client pointing to backend
│   ├── index.html          # HTML template for Vite
│   ├── nginx.conf          # Nginx config for serving static files and handling SPA routing
│   ├── Dockerfile          # Frontend container (uses nginx:alpine)
│   └── package.json        # Dependencies: vue, vite, @vue/*, axios, etc.
└── .github/workflows/main.yml  # CI/CD pipeline for builds & deployments
```

---

## Environment Variables

Environment variables drive configuration for both backend and frontend. They are loaded at runtime and **must be set** before running services locally—especially when connecting to external dependencies (e.g., databases or third-party APIs, though none are present in the base setup).

### Backend (`server.py`) Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVER_HOST` | No | `0.0.0.0` | Bind address for the backend server. Use `localhost` for local-only testing, `0.0.0.0` to accept external connections (e.g., from Docker or other containers). |
| `SERVER_PORT` | No | `8000` | Port on which the backend listens. |
| `API_BASE_PATH` | No | `/api` | Prefix for all API routes. Used to avoid hardcoding in frontend `api.js`. |
| `DEBUG` | No | `false` | Enables verbose logging and development error pages (if supported by framework). **Never enable in production.** |

### Frontend (`web/`) Environment Variables

The Vue app uses Vite’s environment variable syntax (`VITE_` prefix). These are injected **at build time**, so you must rebuild the frontend if you change them.

| Variable | Required | Required? | Default | Description |
|----------|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | Required when building (`npm run build`) | `http://localhost:8000` | Full URL to the backend server (e.g., `http://localhost:8000/api`). Used by `src/api.js` for all API calls. |

> 🔧 **Important**: When running the dev server (`npm run dev`), Vite automatically provides `localhost`-based defaults for `VITE_API_URL` *if unset*, defaulting to `http://localhost:8000`. However, this assumes the backend runs locally on port `8000`. In containerized setups (see below), override this to match the Docker service name (e.g., `http://backend:8000/api`).

---

## Native Development (Non-Containerized)

This mode runs services directly on your host machine for fast hot-reloading during frontend development and debug-friendly backend iteration.

### 1. Setup Backend (`server.py`)

#### Install Dependencies
```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# Install required packages (see backend requirements if present)
pip install -r requirements.txt  # If exists; otherwise install manually (e.g., Flask/FastAPI)
pip install flask  # or fastapi uvicorn python-multipart
```

#### Run Backend
```bash
# Set environment variables
export SERVER_PORT=8000
export API_BASE_PATH=/api

# Run server
python server.py
# Or if using uvicorn (for FastAPI):
# uvicorn server:app --reload --host $SERVER_HOST --port $SERVER_PORT
```

> 💡 The backend should start on `http://localhost:8000`. Confirm by visiting `/health` or checking logs.

### 2. Setup Frontend (`web/`)

#### Install Dependencies
```bash
cd web
npm install
```

#### Configure API Endpoint (Dev Only)
Ensure `src/api.js` uses dynamic URLs. If hardcoded, update it to use:
```js
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

#### Run Dev Server
```bash
# Start frontend dev server with hot reload
npm run dev
# Typically exposes app at http://localhost:5173
```

> ✅ You should now be able to interact with the app via `http://localhost:5173`, with all `/api/*` calls proxied to `http://localhost:8000/api`.

---

## Containerized Local Development (Docker Compose)

Use this for a consistent, isolated environment—ideal for reproducing CI/CD behavior or when dependencies (e.g., databases) are added later.

### Prerequisites
- Docker Engine ≥ 24.x
- Docker Compose ≥ 2.20.x

Verify:
```bash
docker --version    # Docker Desktop ≥ 4.25.x (includes Compose v2)
docker compose version
```

### Build & Run

1. **Build & Start Services**
   ```bash
   docker compose up --build
   ```

   > ⚠️ **Default ports**:  
   > - Frontend (Nginx): `80`  
   > - Backend: `8000` (internal network only; exposed via `nginx.conf` reverse proxy)  
   > Access the app at `http://localhost` (port `80`).

2. **Environment Configuration**
   - Copy `.env.example` (if provided) to `.env`, or define:
     ```env
     # .env at repo root
     SERVER_PORT=8000
     API_BASE_PATH=/api
     ```
   - For frontend, `VITE_API_URL` defaults to `http://localhost:8000` during dev but must be `http://backend:8000` in production builds—handled by the Docker build context.

3. **Development Workflow**
   - Edit `server.py`: Changes require container rebuild or volume mount (`volumes:` in `docker-compose.yml`).  
     Example `docker-compose.yml` snippet for hot-reload backend:
     ```yaml
     services:
       backend:
         volumes:
           - ./server.py:/app/server.py
           - ./venv:/app/venv  # Optional: if using virtualenv
     ```
   - Edit `web/src/`: Use volume mounts to sync changes without rebuild:
     ```yaml
       frontend:
         volumes:
           - ./web/src:/usr/share/nginx/html/src
           - ./web/vite.config.js:/vite.config.js
     ```
     Then run `docker compose up` *and* start the Vite dev server inside the container:
     ```bash
     docker compose exec frontend npm run dev -- --host 0.0.0.0
     ```

---

## Troubleshooting

### Common Issues

1. **Frontend can’t reach backend (`CORS` or `ERR_CONNECTION_REFUSED`)**
   - Ensure `VITE_API_URL` matches the backend host:port.
   - In native mode: `http://localhost:8000`  
   - In Docker mode: `http://localhost:8000` (if using `network_mode: host`) or `http://localhost` (if Nginx proxies).

2. **`Module not found` errors in frontend**
   - Delete `node_modules` + `package-lock.json` and re-run `npm install`.
   - Ensure `vite.config.js` isn’t accidentally excluding `node_modules`.

3. **Backend fails to start with `ModuleNotFoundError`**
   - Confirm dependencies in `requirements.txt` (or inline in `Dockerfile`):
     ```dockerfile
     RUN pip install --no-cache-dir flask uvicorn
     ```
   - If no `requirements.txt`, add one or install packages manually.

4. **SPA routing (e.g., `/dashboard`) returns 404**
   - Verify `web/nginx.conf` has:
     ```nginx
     location / {
       try_files $uri $uri/ /index.html;
     }
     ```

---

## Testing & Validation

After setup, verify the app end-to-end:

1. **Backend health check**
   ```bash
   curl http://localhost:8000/health  # Should return JSON `{"status": "ok"}`
   ```

2. **API endpoints**
   ```bash
   curl http://localhost:8000/api/users  # Example endpoint
   ```

3. **Frontend UI**
   - Visit `http://localhost` (Docker) or `http://localhost:5173` (native dev).
   - Open DevTools → Network tab: Confirm API calls succeed (status `200`).

---

## Next Steps

- **Add dependencies**: Extend `requirements.txt` or `package.json` as needed.
- **CI/CD alignment**: Ensure `Dockerfile` and `docker-compose.yml` match `.github/workflows/main.yml`.
- **External integrations**: When adding DBs or APIs, update `.env.example` and document variable usage.

This guide remains synced with repository evolution. Update this file when adding new environment variables, changing ports, or modifying the Docker setup.
