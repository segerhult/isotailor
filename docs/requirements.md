# Install Requirements

## Overview

This repository hosts a **fullstack web application** featuring a **Python-based backend API** and a **Vue.js 3 frontend**. The application is designed for containerized deployment using Docker and Docker Compose, with Nginx serving as a reverse proxy for the frontend. Dependencies are managed separately for the backend (Python) and frontend (JavaScript/Node.js) layers.

The backend, located at `server.py`, is a custom Python API. A `Dockerfile` in the root directory indicates it's built using a `python:3.11-slim` base image. The frontend, within the `web/` directory, is a Vue 3 application likely managed by Vite, as suggested by `web/src/App.vue` and `web/src/api.js`. An `nginx.conf` file in `web/` details its configuration for serving static assets and proxying requests.

This document outlines the prerequisites and installation procedures for both local development and containerized execution. It emphasizes the use of language-specific package managers (`pip`, `npm`) and system-level tools.

## Runtime Dependencies

The application requires distinct runtime environments for its backend and frontend components. These must be installed and managed locally for development, while Docker handles them in isolated containers for deployment.

### Python Runtime (Backend)

-   **Python Version**: **Python 3.11 or higher** is a strict requirement, as indicated by the `python:3.11-slim` base image in the `Dockerfile`. While newer minor versions of Python 3.11.x might be compatible, using exactly 3.11.x is recommended for consistency with the base image's environment and standard library behavior.
-   **Package Manager**: **`pip`** is the standard package installer for Python. It is used to install dependencies listed in a `requirements.txt` file. The presence of `server.py` and a `Dockerfile` implies this setup, although `requirements.txt` is not explicitly listed in the provided context. If `requirements.txt` is absent, the backend may have no external Python dependencies or they might be managed implicitly. Pip is typically bundled with Python installations.
-   **Rationale**: The Python runtime is essential for executing the backend API logic defined in `server.py`. This includes handling HTTP requests, processing data, and interacting with any underlying services or databases. Without the correct Python version and installed packages, the backend service cannot start or function correctly.

### Node.js Runtime (Frontend)

-   **Node.js Version**: A **Node.js Long-Term Support (LTS) version** (e.g., v20.x or v22.x) is recommended. The frontend build tool (likely Vite, inferred from `web/src/App.vue` and `web/src/api.js`) requires Node.js. Vite specifically mandates Node.js version 16.14 or higher. Using an LTS version ensures better stability, security, and compatibility with frontend dependencies.
-   **Package Manager**: **`npm`** is the default package manager for Node.js and is strongly implied by the likely presence of `package.json` and `package-lock.json` (which is often committed for reproducible builds). Alternatives like `yarn` or `pnpm` *could* be used if their respective lock files (`yarn.lock`, `pnpm-lock.yaml`) are present and configured. However, `npm install` is the standard command based on common practice and the absence of other lock files.
-   **Rationale**: The Node.js runtime is necessary for the frontend development toolchain, including Vite for local development server (`npm run dev`) and production builds (`npm run build`). It manages JavaScript/TypeScript packages such as Vue 3, Vue Router, Pinia (or other state management), and API client libraries (`src/api.js`). These are compiled into static assets that Nginx will serve.

## System Packages and Prerequisites

Beyond language-specific runtimes, several system-level tools are required for development, building, and deployment:

-   **Git (v2.30+)**: Essential for source code management, cloning the repository, and triggering CI/CD workflows (`.github/workflows/main.yml`).
-   **Docker Engine (v24+)** and **Docker Compose (v2.20+)**: Mandatory for building and running the multi-container application locally using `docker-compose up`. Ensure the Docker daemon is active. Docker Compose V2 is typically installed as part of modern Docker Desktop.
-   **Shell Environment**: A compatible shell (`bash`, `sh`, or similar) is needed to execute command-line scripts and Docker Compose commands.

These are foundational tools that interact with the operating system and are not managed by language-specific package managers.

## Package Managers and Dependency Installation

Dependencies for the backend and frontend are managed independently using their respective package managers.

### Installing Backend (Python) Dependencies

1.  **Verify Python Installation**: Ensure Python 3.11+ is installed and accessible in your system's PATH.
    ```bash
    python3 --version
    # or potentially 'python --version'
    ```
2.  **Navigate to Repository Root**: Change your directory to the root of the project where `server.py` and the presumed `requirements.txt` are located.
    ```bash
    cd /path/to/your/repository
    ```
3.  **Install Dependencies**: Use `pip` to install packages listed in `requirements.txt`. It is highly recommended to use a virtual environment to isolate project dependencies.
    ```bash
    # Recommended: Create and activate a virtual environment
    python3 -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate

    # Install dependencies
    pip install --user -r requirements.txt  # if not using venv
    # OR preferably within a venv:
    pip install -r requirements.txt
    ```
    *If `requirements.txt` is absent*: The backend might not have external dependencies. Inspect `server.py` for `import` statements that could indicate necessary packages. If dependencies are expected but the file is missing, it may need to be created manually.

    ⚠️ **Container Build Note**: The `Dockerfile` uses `python:3.11-slim`. If the `Dockerfile` includes a `RUN pip install -r requirements.txt` step, it will install dependencies within the container image. If this step is missing, the container relies on Python's standard library or pre-installed system packages.

### Installing Frontend Dependencies (Node.js)

1.  **Verify Node.js and npm Installation**: Confirm Node.js and npm are installed and accessible.
    ```bash
    node --version
    npm --version
    ```
2.  **Navigate to Web Directory**: Change to the `web/` directory, which contains the frontend source code and `package.json`.
    ```bash
    cd web
    ```
3.  **Install Dependencies**: Use `npm install` to download and install all packages listed in `package.json` and update `package-lock.json`.
    ```bash
    npm install
    ```
    *Alternative Package Managers*: If `yarn.lock` or `pnpm-lock.yaml` were present instead of `package-lock.json`, you would use `yarn install` or `pnpm install` respectively. Given `package-lock.json`'s common use, `npm install` is the default and authoritative command.

    🔧 **Build Tooling**: Vite is assumed to be the build tool. `npm run dev` will start a development server, and `npm run build` will create optimized static assets in a `dist/` directory, which `web/nginx.conf` is configured to serve.

## Install System Tools by Platform

These instructions cover the installation of essential system tools on common operating systems.

### macOS (using Homebrew)

If you have [Homebrew](https://brew.sh/) installed:
```bash
# Update Homebrew and upgrade existing installed packages (optional)
brew update
brew upgrade

# Install Git
brew install git

# Install Node.js (LTS recommended)
brew install node

# Install Python (3.11+ recommended)
brew install python
```

### Ubuntu/Debian (using APT)

```bash
# Update package list
sudo apt-get update

# Install Git
sudo apt-get install -y git

# Install Node.js (LTS version 22.x recommended)
# Download and execute the NodeSource setup script for Node.js
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.11 and pip, and venv for virtual environments
# Note: Ubuntu 22.04 LTS typically ships with Python 3.10. For 3.11+, use the deadsnakes PPA.
# If Python 3.11 is not available directly via apt:
# sudo add-apt-repository ppa:deadsnakes/ppa
# sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip
```

### Windows (using PowerShell/winget)

Using the Windows Package Manager (`winget`):
```powershell
# Find and install Git
winget install --id Git.Git -e --source winget

# Find and install the latest LTS version of Node.js
winget install --id OpenJS.NodeJS.LTS -e --source winget

# Find and install Python 3.11 (or a later version if available)
winget install --id Python.Python.3.11 -e --source winget
```
Ensure that the installation directories for Git, Node.js, and Python are added to your system's `PATH` environment variable. This is usually handled automatically by the installers.

## CI/CD Requirements (`.github/workflows/main.yml`)

The presence of `.github/workflows/main.yml` indicates that GitHub Actions is used for Continuous Integration.

### Secrets and Permissions

-   **Secrets**: The workflow file should be reviewed for any required secrets that need to be configured in the GitHub repository's settings. Common secrets include:
    -   `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`: If the workflow builds and pushes Docker images to Docker Hub.
    -   `REGISTRY` and `GITHUB_TOKEN`: If publishing to GitHub Container Registry (GHCR) or other private registries.
    -   Cloud provider credentials (e.g., `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`): If the workflow includes deployment steps.
-   **Permissions**: The workflow's job definitions in `main.yml` must grant appropriate permissions to the `GITHUB_TOKEN`. Essential permissions often include:
    -   `contents: read`: To check out the repository code.
    -   `packages: write`: If the workflow publishes container images.
    -   `checks: write`: For reporting test results.

### Pipeline Dependencies and Commands

The CI pipeline will need to install the same Node.js and Python runtimes and dependencies as required for local development. It will typically execute commands similar to these:

-   **Frontend Setup & Build**:
    ```bash
    cd web
    npm ci  # Use `npm ci` for deterministic installs in CI
    npm run lint  # If linting is configured
    npm run test  # If unit/integration tests are configured
    npm run build # Build Vue.js application
    ```
-   **Backend Setup & Test**:
    ```bash
    # Install backend dependencies (assuming requirements.txt exists)
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    # Install testing tools if not in requirements.txt
    pip install pytest  # Example for pytest

    # Run backend tests
    pytest
    ```
-   **Docker Build & Push**: If the workflow builds Docker images, it will utilize the `Dockerfile` and `docker-compose.yml`. Commands like `docker build` and `docker push` will be invoked.

Ensure that any development dependencies required for testing or linting (e.g., ESLint, Prettier, Pytest) are listed in the respective `package.json` (`devDependencies`) or `requirements.txt` files.

## Build and Run Commands

These commands assume you are in the repository's root directory unless otherwise specified.

### Local Development (Outside Docker)

#### Backend (Python)

Start the Python backend server directly:
```bash
python3 server.py
```
*Note*: If `server.py` is part of a framework like Flask or FastAPI, additional installation (`pip install flask` or `pip install fastapi uvicorn`) and a different run command might be necessary. However, the context suggests a custom, potentially minimal, implementation.

#### Frontend (Vue + Vite)

Navigate to the `web/` directory, install dependencies, and start the development server:
```bash
cd web
npm install
npm run dev
```
The Vite development server typically runs on `http://localhost:5173` by default. Use `npm run build` to create production-ready static assets in the `dist/` directory.

### Containerized Development (using Docker Compose)

Ensure Docker Desktop or Docker Engine and Docker Compose are running.

```bash
# Build all images and start all services in the foreground
docker-compose up --build

# Start services in the background
docker-compose up -d --build

# View logs from all services
docker-compose logs -f

# Stop and remove containers, networks, and images created by 'up'
docker-compose down
```
The `docker-compose.yml` file orchestrates the backend, frontend (likely Nginx), and potentially other services. The `web/nginx.conf` should be configured to proxy API requests (e.g., `/api/*`) to the backend service, as defined in `docker-compose.yml`.

## Summary Checklist for Setup

| Component             | Requirement                     | Verification / Installation Command                                                                    |
| :-------------------- | :------------------------------ | :----------------------------------------------------------------------------------------------------- |
| **Backend Runtime**   | Python ≥ 3.11                   | `python3 --version`                                                                                    |
| **Backend Dependencies**| `requirements.txt` (if exists)  | `pip install -r requirements.txt` (preferably within a `venv`)                                         |
| **Frontend Runtime**  | Node.js LTS                     | `node --version`, `npm --version`                                                                      |
| **Frontend Dependencies**| `web/package.json`              | `cd web && npm install`                                                                                |
| **Containerization**  | Docker Engine & Compose v2      | `docker info`, `docker compose version`                                                                |
| **Version Control**   | Git                             | `git --version`                                                                                        |
| **Local Dev (Backend)**| Run `server.py`                 | `python3 server.py`                                                                                    |
| **Local Dev (Frontend)**| Vite Dev Server                 | `cd web && npm run dev`                                                                                |
| **Container Dev**     | Docker Compose                  | `docker-compose up --build`                                                                            |

Always ensure consistency between your local development environment and the containerized build environment to prevent unexpected issues. Pay close attention to dependency versions specified in `requirements.txt` and `package.json` (and their lock files).
