# Install Requirements

## Overview

This repository hosts a **fullstack web application** composed of a **Python-based backend API** (`server.py`) and a **Vue.js 3 frontend** served via a lightweight Nginx reverse proxy in production. The application uses a containerized deployment architecture, with Docker and Docker Compose as the primary deployment mechanisms. Due to its modular structure, dependencies are split across the backend (Python) and frontend (JavaScript/Node.js) layers, each with their own isolated environments and tooling.

The backend is a lightweight RESTful API implemented using Python 3.11+ with no external framework (likely raw `http.server`-based or minimal custom routing), and it defines at least nine distinct API endpoints, as inferred from heuristic analysis. The frontend is built using **Vue 3**, with **Vite** serving as the build tool for fast development and optimized production builds. Assets are bundled and served statically using **Nginx**, with explicit configuration (`web/nginx.conf`) to handle SPA routing and proxy API requests to the backend service.

The use of Docker for both services (`Dockerfile` in the root for Python backend; `web/Dockerfile` for frontend Nginx server) and the presence of `docker-compose.yml` indicate a *multi-container orchestrated setup*. This architecture requires careful management of build-time and runtime dependencies for both layers, especially when running outside of Docker (e.g., during development or CI debugging).

This document details the full setup process—both *local development* and *containerized production*—with emphasis on installation methods using language-specific and system-level package managers, and highlights dependencies critical to the build, test, and runtime stages.

## Runtime Dependencies

The application requires two independent runtime environments: one for the **backend (Python)** and one for the **frontend (Node.js)**. While containers abstract this separation during production, developers working on the project locally must install and maintain both toolchains.

### Python Runtime

- **Python 3.11 or higher** is required, as indicated by the base image `python:3.11-slim` in the root `Dockerfile`. While newer minor releases (e.g., 3.12) may be compatible, 3.11.x is the *reference* version for compatibility with the image’s ecosystem and standard library behavior.
- **pip** is the default package installer, bundled with standard Python installations. It is used to install dependencies listed in `requirements.txt` (presumed, though not explicitly listed in context—see *Package Managers* below). Alternatives like `poetry` or `pipenv` are *not currently in use*, as there are no `pyproject.toml` or `Pipfile` artifacts indicated. Use `pip` unless explicitly configured otherwise.
- Why needed: Backend logic, HTTP handling, and custom routing are implemented in Python. Even in minimal implementations, `http.server` or WSGI-compatible frameworks like `werkzeug` may be used (though not specified here). Dependencies such as `requests`, `pydantic`, or `uvicorn` are not confirmed in context but may appear if extended.

### Node.js Runtime (Frontend)

- **Node.js LTS (v20.x or v22.x recommended)** is required to support modern tooling and build tool versions. Vite (vite.config.js) mandates Node.js ≥16.14, but LTS ensures compatibility with current dependencies and security patches.
- **npm ≥10.x**, **yarn ≥4.x**, or **pnpm ≥8.x** may be used—though `package.json` and `package-lock.json` suggest `npm` is the default lockfile mechanism, with `package-lock.json` committed (implying `npm` is the canonical tool). Yarn or pnpm may be used optionally by developers, but CI or local scripts must be consistent with lockfile expectations.
- Why needed: Frontend build toolchain (Vite), Vue 3 runtime, and API client abstractions (`src/api.js`, `main.js`) rely on Node.js to execute build scripts, resolve transitive dependencies (e.g., `vue`, `vue-router`, `pinia`, or `axios`), and produce static assets for Nginx serving.

## System Packages and Prerequisites

A few system-level tools are required regardless of deployment method (local or containerized):

- **Git (v2.30+)**: Used for version control, subproject cloning (if any), and CI pipeline triggers. Required to fetch repository sources during build.
- **Docker Engine (v24+)** and **Docker Compose (v2.20+)**: Required for building and running the multi-container stack locally (via `docker-compose up`). Note: `docker-compose` CLI v2 is standard in modern Docker Desktop installations.
- **Sensible shell environment** (`bash`/`sh` compatible) for running scripts and compose commands.

These tools are used for both development and production builds. They are *not* installed via language-specific package managers but via OS-native or third-party installers.

## Package Managers and Dependency Installation

Dependencies are managed separately for frontend and backend, using language-specific tooling.

### Installing Backend (Python) Dependencies

1. Ensure Python 3.11+ is installed and available on your `PATH`. Verify with:
   ```bash
   python3 --version  # or `python --version` on some platforms
   ```
2. Navigate to the repository root (where `server.py` and (assumed) `requirements.txt` reside):
   ```bash
   cd /path/to/repo
   ```
3. Install system packages (if needed), then run:
   ```bash
   pip install --user -r requirements.txt
   ```
   - If `requirements.txt` does not exist (not specified in context), you may need to create it manually, or the backend may have no external dependencies (pure stdlib). If `server.py` is truly minimal (e.g., using only `http.server`), then *no pip installation* may be needed.
   - Avoid `sudo pip`, especially system-wide, to prevent breaking OS packages. Prefer virtual environments or `--user`.

   ⚠️ **Note**: In containerized builds (`Dockerfile`), the image `python:3.11-slim` expects all dependencies to be declared or installed via `requirements.txt` (if present). If the Docker image builds without installing any packages (`pip install` is absent in context), it implies the backend has *zero external dependencies*. Double-check `server.py` imports.

### Installing Frontend Dependencies (Node.js)

1. Verify Node.js and npm installation:
   ```bash
   node --version
   npm --version
   ```
   Recommend ≥v20.x / ≥10.x for compatibility.

2. Navigate to the `web/` directory (frontend source root):
   ```bash
   cd web
   ```

3. Install frontend packages:
   ```bash
   npm install
   ```
   - This resolves dependencies declared in `package.json` and locks them in `package-lock.json` (ensuring reproducibility).
   - Alternatives (e.g., `yarn`, `pnpm`) may be used *only if* lockfile and config files are aligned (e.g., `yarn.lock`/`pnpm-lock.yaml`). Since `package-lock.json` is present, `npm install` is authoritative.

   🔧 **Build optimization**: Vite (`vite.config.js`) is used for dev server and production build (`vite build`). The `web/nginx.conf` file likely expects output in `dist/`, consistent with Vite’s default.

## Install System Tools by Platform

Install system prerequisites *once per host*. For CI/CD or CI environments, these are pre-installed via infrastructure-as-code or base images.

### macOS (Homebrew)

If using [Homebrew](https://brew.sh/):
```bash
# Update Homebrew and upgrade existing packages (optional)
brew update && brew upgrade

# Install Git (v2.x+)
brew install git

# Optional: Install Node.js and Python via Homebrew (recommended for consistency)
brew install node python
```

> 💡 *Alternative*: Install Node.js via [NodeSource](https://github.com/nodesource/distributions) or [nvm](https://github.com/nvm-sh/nvm) for per-project versioning; Python via `pyenv` or system pkg.

### Ubuntu/Debian (APT)

```bash
# Update package index
sudo apt-get update

# Install Git
sudo apt-get install -y git

# Install Node.js (LTS 22.x as of 2025)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.11+ (if not present)
sudo apt-get install -y python3 python3-pip python3-venv
```

> ✅ **Note**: Ubuntu 22.04+ ships Python 3.10; use [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) for 3.11+ if needed:
> ```bash
> sudo add-apt-repository ppa:deadsnakes/ppa
> sudo apt-get update
> sudo apt-get install -y python3.11 python3.11-venv python3-pip
> ```

### Windows (PowerShell)

Using [Windows Package Manager (`winget`)](https://learn.microsoft.com/en-us/windows/package-manager/):

```powershell
# Install Git (via official package)
winget install --id Git.Git -e --source winget

# Install Node.js LTS (via Node.js official installer)
winget install --id OpenJS.NodeJS.LTS -e --source winget

# Optional: Install Python 3.11 (check winget for latest)
winget install Python.Python.3.11
```

> 💡 Ensure `PATH` includes `C:\Program Files\Git\cmd`, `%USERPROFILE%\AppData\Local\Programs\Python\Python311\`, and `C:\Program Files\nodejs\`.

## CI/CD Requirements

The project includes `.github/workflows/main.yml`, implying GitHub Actions for CI. Key requirements:

### Secrets and Permissions

- **No external secrets** are indicated in context (e.g., Docker Hub credentials, API keys). However, if the workflow builds/pushes Docker images, the following *should* be configured in GitHub repository settings:
  - `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` for Docker Hub push access (if applicable).
  - `REGISTRY` (e.g., `ghcr.io`) and `GITHUB_TOKEN` if publishing to GitHub Container Registry.
  - `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` if deploying to AWS (not indicated).
- Permissions required in `main.yml`:
  - `contents: read` (to checkout code)
  - `packages: write` (if publishing container images)
  - `checks: write` (for test reports, if any)
  - `id-token: write` (if using OIDC for cloud auth)

### Pipeline Dependencies

The workflow likely:
1. Checks out code.
2. Builds and caches frontend (`npm ci`, `npm run build`) and backend (`docker build`).
3. Runs linting/tests (e.g., `npm test`, `pytest`—if configured).
4. Builds and pushes Docker images.

Ensure all dependencies for testing (e.g., `pytest`, `eslint`, `prettier`) are installed in CI. Since `web/package.json` may declare `"scripts": {"test": "..."}`, confirm test commands are valid.

## Build and Run Commands

All commands assume you are in the repository root unless specified.

### Local Development (Non-Container)

#### Backend (Python)

```bash
python3 server.py
```
> 🔍 *If* `server.py` is a standard Flask/FastAPI app, `pip install flask`/`uvicorn` would be needed—but context suggests it’s *not* used. Verify imports.

#### Frontend (Vue + Vite)

```bash
cd web
npm install
npm run dev    # starts dev server on port 5173 (default)
```
> 🔧 Use `npm run build` to generate static assets into `dist/`.

### Containerized Development (Docker Compose)

Ensure Docker daemon is running, then:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

> 🐳 `web/nginx.conf` is expected to proxy `/api` requests to `server.py` (exposed on port 8000 by backend container, or similar—confirm `docker-compose.yml` service definitions and port mappings).

### CI Build/Test Commands

If `.github/workflows/main.yml` uses `actions/setup-node` and `actions/setup-python`, typical commands include:

```bash
# Frontend lint & test (if configured)
cd web
npm ci
npm run lint
npm run test
npm run build

# Backend test (if `pytest` or unit tests exist)
python3 -m pip install --user pytest  # if needed
pytest
```

> 📌 **Note**: If no tests are defined, ensure CI only builds and pushes containers.

## Summary Checklist for Setup

| Component | Requirement | Command |
|-----------|-------------|---------|
| Backend runtime | Python ≥3.11 | `python3 --version` |
| Backend deps | `requirements.txt` (if any) | `pip install -r requirements.txt` |
| Frontend runtime | Node.js LTS | `node --version`, `npm --version` |
| Frontend deps | `web/package.json` | `cd web && npm install` |
| Container runtime | Docker Engine + Compose | `docker info`, `docker compose version` |
| System tools | Git | `git --version` |
| Development server (backend) | Start `server.py` | `python3 server.py` |
| Development server (frontend) | `npm run dev` in `web/` | `cd web && npm run dev` |

Always verify dependencies *in each layer*—especially when switching between containerized and local modes—to avoid subtle environment drift.
