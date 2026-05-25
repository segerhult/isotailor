# Local Development Setup

This guide walks you through setting up a local development environment for the fullstack application hosted in this repository. The application consists of a **Python-based backend API** (implemented using a lightweight ASGI/WSGI framework like FastAPI or Flask, served via `server.py`) and a **Vue 3 frontend** (built with Vite and served in production via Nginx). Both components are containerized for consistent local and CI/CD environments, but for rapid development iteration, you may choose to run them natively or via Docker Compose.

The app uses **HTTP/JSON-based communication** between frontend and backend (via the `src/api.js` client utility), and includes:
- `/api/*` backend endpoints (9 total, inferred from heuristic scan of `server.py`)
- Static asset serving and client-side routing handled by Nginx for the built Vue frontend
- Environment-driven configuration for backend API endpoints and ports, as well as frontend build-time injection of backend URLs

This setup supports both native development (for performance and tooling integration) and containerized workflows (for reproducibility and isolation), and is designed to mirror production patterns while enabling developer productivity.

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

#### Installing with System Package Managers (Alternative)

- **macOS**  
  ```bash
  brew install python@3.11 node@18  # Requires Homebrew
  ```

- **Ubuntu/Debian**  
  ```bash
  sudo apt update && sudo apt install -y python3 python3-pip nodejs npm
  # Ensure versions match: `python3 --version`, `node --version`, `npm --version`
  ```

- **Windows**  
  Download and install from official sources:
  - [Python 3.11 installer (amd64)](https://www.python.org/downloads/windows/)
  - [Node.js LTS 18.x (MSI installer)](https://nodejs.org/en/download/)

> ⚠️ **Caution**: Avoid mixing system-wide `pip install --user` or global `npm install -g` for project dependencies. Use virtual environments and `package.json` to ensure reproducibility.

---

## Repository Structure Overview

```
├── server.py               # Python backend (ASGI/WSGI app, runs on port 8000 by default)
├── Dockerfile              # Backend container image (python:3.11-slim)
├── docker-compose.yml      # Orchestrates frontend & backend services (services: backend, frontend)
├── web/                    # Vue 3 frontend source
│   ├── src/
│   │   ├── main.js         # Entry point, mounts App.vue
│   │   ├── App.vue         # Root component, includes router & global layout
│   │   └── api.js          # Axios-based API client; resolves base URL via `VITE_API_URL`
│   ├── index.html          # HTML template for Vite dev/prod builds
│   ├── nginx.conf          # Nginx config for serving static files & SPA fallback routing
│   ├── Dockerfile          # Frontend container (uses nginx:alpine)
│   └── package.json        # Dependencies: vue, vite, @vue/*, axios, eslint
├── .github/workflows/main.yml  # CI/CD pipeline for builds, tests, and image pushes
└── docs/                   # Additional documentation (if present)
```

> 🔍 **Key Details**:  
> - `web/Dockerfile` uses multi-stage builds: first installs dependencies and builds assets, then copies only the static output (`dist/`) into an `nginx:alpine` image.  
> - `web/nginx.conf` implements a `try_files` directive for SPA routing (`/dashboard`, `/user/123` → `index.html`).  
> - `server.py` defines routes like `/api/health`, `/api/users`, `/api/auth/login`, etc., returning JSON responses.

---

## Environment Variables

Environment variables drive runtime behavior for both backend and frontend. These are loaded at runtime for the backend and injected **at build time** for the frontend via Vite's `import.meta.env`.

### Backend (`server.py`) Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVER_HOST` | No | `0.0.0.0` | Bind address for the backend server. Use `localhost` for local-only testing, `0.0.0.0` to accept external connections (e.g., from Docker or other containers). |
| `SERVER_PORT` | No | `8000` | Port on which the backend listens. Must match the port exposed in `docker-compose.yml` and used in `api.js`. |
| `API_BASE_PATH` | No | `/api` | Prefix for all API routes. Used to avoid hardcoding in frontend `api.js`. E.g., `/api/users` becomes `/api/v2/users` if changed. |
| `DEBUG` | No | `false` | Enables verbose logging and development error pages (if supported by framework). **Never enable in production.** |

> 💡 **Tip**: These variables can be set directly in `.env` (see below) or passed via `docker-compose.yml`’s `environment:` section.

### Frontend (`web/`) Environment Variables

Vite prefixes all injected env vars with `VITE_`. These are **statically replaced at build time**, so changing them requires rebuilding the app (`npm run build`).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes (for builds) | `http://localhost:8000` | Full base URL to the backend server (including path, e.g., `http://localhost:8000/api`). Used by `src/api.js` for all API calls. |
| `VITE_APP_TITLE` | No | `"MyApp"` | Application title (optional, used in `index.html`). |

> 🔧 **Important**: When running `npm run dev`, Vite automatically populates `VITE_API_URL` from `.env` or defaults to `http://localhost:8000`. However, this assumes:
> - The backend runs locally on port `8000`  
> - No proxy is involved  
> In containerized setups (e.g., Docker Compose), override to `http://backend:8000/api` during build (handled via Dockerfile build args or `.env` at build time).

#### Setting Environment Variables for Development

1. Create a `.env` file in the repo root:
   ```env
   # .env
   SERVER_HOST=0.0.0.0
   SERVER_PORT=8000
   API_BASE_PATH=/api
   DEBUG=true
   ```
   For frontend, add:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

2. For **Docker Compose**, create a `.env` file at repo root (read automatically by `docker-compose.yml`):
   ```env
   BACKEND_PORT=8000
   API_BASE_PATH=/api
   ```

> ⚠️ **Never commit secrets or production credentials to `.env`**. Use `.env.example` to document required variables for collaborators.

---

## Native Development (Non-Containerized)

This mode runs services directly on your host machine for fast hot-reloading during frontend development and debug-friendly backend iteration (e.g., using VS Code’s Python debugger or `uvicorn --reload`).

### 1. Setup Backend (`server.py`)

#### Install Dependencies
```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# Install required packages
pip install -r requirements.txt  # If present; otherwise install manually:
pip install fastapi uvicorn python-multipart python-dotenv
```

> 📌 **Note**: If `requirements.txt` does not exist, create one:
> ```bash
> pip freeze > requirements.txt
> ```
> and commit it for reproducibility.

#### Run Backend
```bash
# Set environment variables (already defined in `.env` if using dotenv)
export $(cat .env | xargs)  # Bash (load .env into shell)
# OR manually:
export SERVER_PORT=8000
export API_BASE_PATH=/api
export DEBUG=true

# Run server (if using uvicorn)
uvicorn server:app --reload --host $SERVER_HOST --port $SERVER_PORT
```

> 💡 The backend should start on `http://localhost:8000`. Confirm by visiting `http://localhost:8000/health` (returns `{"status": "ok"}`) or checking logs.

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
export const get = async (path) => {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
};
```

#### Run Dev Server
```bash
# Start frontend dev server with hot reload
npm run dev
# Typically exposes app at http://localhost:5173
```

> ✅ You should now be able to interact with the app via `http://localhost:5173`, with all `/api/*` calls proxied to `http://localhost:8000/api`.  
> 🔁 Hot reload works for Vue changes, but backend changes require server restart (unless `--reload` is used).

---

## Containerized Local Development (Docker Compose)

Use this for a consistent, isolated environment—ideal for reproducing CI/CD behavior, testing environment-specific behavior, or when dependencies (e.g., databases) are added later.

### Prerequisites
- Docker Engine ≥ 24.x (Docker Desktop ≥ 4.25.x for macOS/Windows)
- Docker Compose ≥ 2.20.x

Verify:
```bash
docker --version    # e.g., Docker version 24.0.7, build afdd53b
docker compose version
```

### Build & Run

1. **Build & Start Services**
   ```bash
   docker compose up --build
   ```

   > ⚠️ **Default ports**:  
   > - Frontend (Nginx): `80` (mapped to host `80`)  
   > - Backend: `8000` (exposed only internally via Docker network)  
   > Access the app at `http://localhost` (port `80`), which proxies `/api` to `backend:8000`.

2. **Environment Configuration**
   - The `docker-compose.yml` includes:
     ```yaml
     environment:
       - SERVER_PORT=${BACKEND_PORT:-8000}
       - API_BASE_PATH=/api
     ```
   - For frontend, `VITE_API_URL` is set during build via Dockerfile build args:
     ```dockerfile
     ARG VITE_API_URL=http://backend:8000/api
     ENV VITE_API_URL=$VITE_API_URL
     ```

3. **Development Workflow**
   - **Backend**: Edit `server.py` and run:
     ```bash
     docker compose restart backend
     ```
     Or add volume mounts for live reloading (if supported by framework):
     ```yaml
     services:
       backend:
         volumes:
           - ./server.py:/app/server.py:ro
           # For uvicorn --reload, bind-mount the entire directory (advanced)
     ```
   - **Frontend**: Use `docker compose up` *without* `--build` to retain old build, then start Vite dev server inside the container:
     ```bash
     docker compose exec frontend npm run dev -- --host 0.0.0.0 --port 5173
     ```
     Access at `http://localhost:5173` (if exposed in `docker-compose.yml`).  
     Alternatively, mount source:
     ```yaml
     frontend:
       volumes:
         - ./web:/usr/src/web
     ```
     And adjust `nginx.conf` to serve from `/usr/src/web/dist` (not recommended for speed).

> 💡 **Tip**: For production-like development, use `docker compose --profile dev up --build` with profiles defined in `docker-compose.yml`.

---

## Troubleshooting

### Common Issues

1. **Frontend can’t reach backend (`CORS` or `ERR_CONNECTION_REFUSED`)**
   - Ensure `VITE_API_URL` matches the backend host:port *and* includes the `/api` path.
   - In native mode: `http://localhost:8000/api`  
   - In Docker mode: `http://backend:8000/api` (container network) or `http://localhost:8000/api` (if using `network_mode: host` or port-forwarding).

2. **`Module not found` errors in frontend**
   - Delete `node_modules` + `package-lock.json` and re-run `npm install`.
   - Ensure `vite.config.js` isn’t accidentally excluding `node_modules`:
     ```js
     export default defineConfig({
       resolve: {
         alias: { '@': path.resolve(__dirname, './src') }
       }
     });
     ```

3. **Backend fails to start with `ModuleNotFoundError`**
   - Confirm dependencies in `requirements.txt`:
     ```dockerfile
     RUN pip install --no-cache-dir -r requirements.txt
     ```
   - If `requirements.txt` is missing, generate it (`pip freeze > requirements.txt`) and rebuild:
     ```bash
     docker compose build --no-cache backend
     ```

4. **SPA routing (e.g., `/dashboard`) returns 404**
   - Verify `web/nginx.conf` has:
     ```nginx
     location / {
       try_files $uri $uri/ /index.html;
     }
     ```

5. **`docker compose up` fails with `ERROR: manifest for ... not found`**
   - Check `docker-compose.yml` for typos (e.g., `build: web/` vs `./web`).
   - Re-run with `--build --force-recreate`.

---

## Testing & Validation

After setup, verify the app end-to-end:

1. **Backend health check**
   ```bash
   curl http://localhost:8000/health  # Native: returns `{"status": "ok"}`
   curl http://localhost/health       # Docker: same (proxied by Nginx)
   ```

2. **API endpoints**
   ```bash
   curl http://localhost:8000/api/users  # Native
   curl http://localhost/api/users       # Docker
   ```

3. **Frontend UI**
   - Visit `http://localhost` (Docker) or `http://localhost:5173` (native dev).
   - Open DevTools → Network tab: Confirm API calls succeed (status `200`) and include expected JSON.

4. **Full integration**
   - Log in (if applicable) → navigate to `/dashboard` → verify data loads.

---

## Next Steps

- **Add dependencies**: Extend `requirements.txt` (backend) or `package.json` (frontend) as needed.
- **CI/CD alignment**: Ensure `Dockerfile` and `docker-compose.yml` match `.github/workflows/main.yml`:
  - Same base images (`python:3.11-slim`, `nginx:alpine`)
  - Matching build args (`VITE_API_URL`)
  - Identical environment variables
- **External integrations**: When adding DBs or APIs, update `.env.example` and document variable usage.
- **Testing**: Add `pytest` or `vitest` suites and integrate into CI.

This guide remains synced with repository evolution. Update this file when:
- Adding new environment variables
- Changing ports or routes
- Modifying Docker builds or compose services  
- Updating Node.js/Python version requirements  

For further assistance, refer to:
- `docs/api.md` (if present)  
- `README.md`  
- `server.py`’s inline documentation  
- Vue 3 + Vite [official guides](https://vitejs.dev/guide/)
