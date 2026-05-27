# Deployment

This repository contains a full-stack application. The deployment strategy relies heavily on Docker and Docker Compose for orchestration, ensuring a consistent and reproducible environment across development and production.

## Overview

The application consists of:

*   **Backend API:** A Python-based HTTP server (`server.py`) using `aiohttp`. This server exposes RESTful endpoints for managing software, manifests, and uploads. It listens on port `8080` within the Docker network.
*   **Frontend Web Application:** A Vue.js Single Page Application (SPA) built with Vite. The frontend assets are served statically by NGINX.
*   **NGINX Server:** Configured to serve the frontend's static files and act as a reverse proxy, forwarding API requests (prefixed with `/api`) to the backend Python service.

The `docker-compose.yml` file orchestrates these services, along with an optional PostgreSQL database (`db`), defining their networks, volumes, and dependencies.

## Prerequisites

Before you can deploy the application, ensure you have the following tools installed and configured on your system.

### System-Level Requirements

*   **Docker Engine**: Version 20.10 or higher is required. Docker Desktop is recommended for macOS and Windows. For Linux, follow the official Docker installation guide for your distribution.
    *   **Linux (Ubuntu/Debian)**:
        ```bash
        sudo apt-get update
        sudo apt-get install docker.io docker-compose-plugin
        sudo systemctl enable docker
        sudo systemctl start docker
        # Add your user to the 'docker' group to run without sudo
        sudo usermod -aG docker $USER
        # Log out and log back in for group changes to take effect
        ```
    *   **macOS**: Install [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/). Ensure Docker Compose is accessible (it's included with Docker Desktop).
    *   **Windows**: Install [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) and ensure WSL 2 integration is enabled if you plan to use WSL.

*   **Docker Compose Plugin**: This guide assumes you are using the modern `docker compose` command (v2). Verify your installation:
    ```bash
    docker compose version
    # Expected output: Docker Compose version v2.x.x
    ```
    If you only have `docker-compose` (v1), it's recommended to upgrade.

*   **Git**: Required to clone the repository.
    *   **Linux (Ubuntu/Debian)**:
        ```bash
        sudo apt-get update
        sudo apt-get install git
        ```
    *   **macOS**: Install via [Homebrew](https://brew.sh/):
        ```bash
        brew install git
        ```
    *   **Windows**: Download and install from [git-scm.com](https://git-scm.com/).

### Language-Specific Requirements (for Manual/Development Setup)

While Docker is the recommended deployment method, these are needed for local development or manual execution outside of Docker:

*   **Python**: Version 3.11 or higher is required for the backend.
    *   **System Package Manager**: Most Linux distributions and macOS provide Python. Ensure you have at least Python 3.11.
        ```bash
        python3 --version
        ```
    *   **Version Management (Recommended)**: Tools like `pyenv` are useful for managing multiple Python versions.
        ```bash
        # Example using pyenv
        pyenv install 3.11.7
        pyenv global 3.11.7
        ```
*   **pip**: Python's package installer. Ensure it's up-to-date.
    ```bash
    python -m pip install --upgrade pip
    ```
*   **Node.js**: Version 18 or higher is required for building the frontend.
    *   **Version Management (Recommended)**: Use `nvm` (Node Version Manager) for easier management.
        ```bash
        # Install nvm if you don't have it
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        # Source nvm (or restart your terminal)
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

        # Install and use Node.js v18
        nvm install 18
        nvm use 18
        ```
*   **npm**: Node Package Manager. Comes with Node.js installations. Verify version:
    ```bash
    npm -v
    # Should be version 9 or higher
    ```

> **Warning**: Manual deployment without Docker requires significant effort to configure networking, security (SSL/TLS), and manage dependencies. It is **not recommended for production environments**.

## Repository Structure

Understanding the project layout is key to effective deployment and troubleshooting:

```
.
├── .dockerignore           # Specifies files/directories to exclude from backend Docker build context.
├── .gitignore              # Standard Git ignore patterns.
├── .github/
│   └── workflows/
│       └── main.yml        # GitHub Actions CI workflow definition. Builds images and runs tests.
├── Dockerfile              # Dockerfile for the Python backend API. Uses `python:3.11-slim` base.
├── docker-compose.yml      # Defines and configures multi-container Docker applications (web, app, db).
├── server.py               # The main Python backend application code.
├── README.md               # Project's main README file.
└── web/                    # Frontend application directory.
    ├── .dockerignore       # Files/directories to exclude from frontend Docker build context.
    ├── Dockerfile          # Multi-stage Dockerfile for the Vue.js frontend. Builds with Node.js, serves with NGINX.
    ├── nginx.conf          # NGINX configuration for serving static assets and proxying API requests.
    ├── package.json        # Frontend project's dependencies and scripts (e.g., 'build').
    ├── vite.config.js      # Vite build tool configuration.
    └── src/                # Frontend source code.
        ├── App.vue         # Root Vue component.
        ├── api.js          # JavaScript module for interacting with the backend API.
        └── main.js         # Vue application entry point.
```

**Key Components & Their Roles**:

*   **`Dockerfile` (Root):** Builds the backend service image. It starts from `python:3.11-slim`, copies `server.py`, and installs dependencies using pip.
*   **`web/Dockerfile`:** Utilizes a multi-stage build. The first stage uses a Node.js image to build the Vite application (`npm run build`), generating static files in `web/dist/`. The second stage copies these static files into an `nginx:alpine` image and includes the `web/nginx.conf` for serving.
*   **`docker-compose.yml`:** The central orchestrator. It defines:
    *   `web` service: Uses `web/Dockerfile`. Exposes port 80 to the host.
    *   `app` service: Uses root `Dockerfile`. Listens on internal port 8080.
    *   `db` service (optional): A PostgreSQL instance.
    It sets up a custom bridge network for these services to communicate via service names (e.g., `app`, `db`).
*   **`web/nginx.conf`:** Crucial for routing. It's configured to:
    *   Serve static files from `/usr/share/nginx/html`.
    *   Handle SPA routing using `try_files $uri $uri/ /index.html;`.
    *   Proxy requests starting with `/api` to the backend service (`http://app:8080`).

## Deployment using Docker Compose

This is the recommended method for deploying the application.

### 1. Clone the Repository

First, clone this repository to your local machine:

```bash
git clone <repository-url>
cd <repo-name>
```

### 2. Prepare Data Directory

The backend application may generate or require data (e.g., uploads, manifests). Create and ensure proper permissions for the `data` directory:

```bash
mkdir -p data
chmod 755 data
```
This directory should be bind-mounted as a volume in `docker-compose.yml` to persist data across container restarts.

### 3. Build and Start Services

Navigate to the root directory of the cloned repository and run:

```bash
docker compose up --build -d
```

This command will:

*   **Build Images**:
    *   Build the backend image using the `Dockerfile` in the root directory.
    *   Build the frontend image using the `web/Dockerfile`. This involves running `npm run build` within a Node.js container and then copying the output into an NGINX container.
*   **Start Containers**: Launch all defined services (`web`, `app`, `db`) in detached mode (`-d`).
*   **Networking**: Create a dedicated Docker network for the services to communicate using their service names.
*   **Port Mapping**: Map ports from the host machine to the container services. Specifically, port `80` on the host will map to the NGINX service (`web`), making the frontend accessible. Port `8080` (backend) is intentionally not exposed to the host, only accessible internally by the `web` service.

### 4. Verify Deployment

Check the status of running containers:

```bash
docker compose ps
```
You should see `web`, `app`, and `db` (if enabled) listed with status `Up`.

To view real-time logs from all services:

```bash
docker compose logs -f
```
Look for successful startup messages from both the Python backend and NGINX.

### 5. Access the Application

Open your web browser and navigate to `http://localhost`. The NGINX server will serve the frontend application.

You can test the backend API endpoints via the NGINX proxy:

```bash
curl http://localhost/api/software
curl -X POST http://localhost/api/manifest -H "Content-Type: application/json" -d '{"os":"Ubuntu","version":"22.04"}'
```

## Configuration

### Backend (`server.py`)

Currently, `server.py` does not explicitly read environment variables for configuration. It runs on `0.0.0.0:8080` and expects data files in the `./data` directory.

If environment variables were to be introduced (e.g., for database connection strings, secrets), they would be defined:

*   **Locally**: In a `.env` file in the project root, which `docker-compose` automatically loads.
    ```env
    # .env example
    DB_HOST=db
    DB_USER=postgres
    DB_PASSWORD=changeme
    ```
*   **In `docker-compose.yml`**: By adding an `environment:` section to the `app` service definition. Variables starting with `${...}` are loaded from the `.env` file.

### Frontend (`web/`)

Frontend configuration, particularly the API base URL, is managed via Vite's environment variables.

*   **Build-time Configuration**: Create environment files within the `web/` directory (e.g., `web/.env.production`).
    ```env
    # web/.env.production example
    VITE_API_BASE=/api
    VITE_APP_TITLE="My App"
    ```
    These variables are accessed in the frontend code via `import.meta.env.VITE_API_BASE`. The `nginx.conf` is set up to proxy `/api` requests to the backend, so `VITE_API_BASE=/api` is appropriate for the Docker deployment.

### NGINX (`web/nginx.conf`)

The `web/nginx.conf` file dictates how NGINX handles requests:

```nginx
server {
  listen 80;
  server_name localhost; # Or your domain name in production

  location / {
    root /usr/share/nginx/html;
    # For Vue Router in history mode
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    # Proxy requests to the backend service named 'app' on port 8080
    proxy_pass http://app:8080/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # Optional: Add error pages, logging, etc.
}
```

*   The `location /` block serves static files and ensures SPA routing works correctly.
*   The `location /api/` block forwards all requests starting with `/api/` to the backend service (`app`) listening on port `8080`. Ensure the service name (`app`) matches the name in `docker-compose.yml`.

## Manual Deployment (Advanced Users)

This section describes how to run the backend and frontend independently, outside of Docker Compose. **This is not recommended for production.**

### Backend (Python)

1.  **Install Dependencies**:
    ```bash
    cd /path/to/repo
    python -m pip install --upgrade pip
    pip install aiohttp # If not already specified in a requirements.txt
    ```
2.  **Create Data Directory**:
    ```bash
    mkdir -p data && chmod 755 data
    ```
3.  **Run Server**:
    ```bash
    python server.py
    ```
    The server will start, typically accessible at `http://0.0.0.0:8080`. You may need to configure CORS handling in `server.py` manually if accessing from a different origin (e.g., `http://localhost:5173` for Vite's dev server).

### Frontend (Vue.js + NGINX)

1.  **Install Dependencies & Build**:
    ```bash
    cd /path/to/repo/web
    npm ci # Use 'npm ci' for exact dependency installs based on package-lock.json
    npm run build
    # This creates the production build in the `web/dist/` directory.
    ```
2.  **Serve with NGINX**:
    You can use Docker to serve the static files with NGINX, or install NGINX directly on your host.

    *   **Using Docker**:
        ```bash
        # Ensure you are in the root directory of the repository
        docker run --name frontend-manual -d \
          -p 80:80 \
          -v $(pwd)/web/dist:/usr/share/nginx/html:ro \
          -v $(pwd)/web/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
          nginx:alpine
        ```
        *Note*: If running the backend manually on `localhost:8080`, you'll need to adapt `web/nginx.conf` to proxy to `http://localhost:8080` instead of `http://app:8080`. If running backend within Docker on host machine, use `proxy_pass http://host.docker.internal:8080;`.

## Production Considerations

*   **Security**:
    *   **Network Exposure**: *Never* expose the backend port `8080` directly to the host or internet. It must remain internal to the Docker network and only accessible via NGINX.
    *   **TLS/SSL**: For production, configure NGINX to use HTTPS. This involves obtaining SSL certificates and updating `web/nginx.conf` to handle TLS termination.
    *   **Database Security**: If the `db` service is used, ensure a strong `POSTGRES_PASSWORD` is set and restrict network access to the database.
*   **Scalability**:
    *   For increased backend capacity, use `docker compose up --scale app=N -d`, where `N` is the desired number of instances.
    *   Consider using a production-grade Python WSGI server like `gunicorn` behind `aiohttp` for better concurrency management if extremely high loads are expected. Add `gunicorn` to backend dependencies and modify the `command` in `docker-compose.yml`.
*   **Persistence**:
    *   Ensure that the `data` directory for the backend is correctly configured as a persistent volume in `docker-compose.yml`. Without it, uploads and manifests will be lost when containers are recreated.
    *   For the PostgreSQL database, use named volumes (e.g., `db-data:/var/lib/postgresql/data`) for persistent storage.
*   **Health Checks**: Implement Docker health checks in the `Dockerfile` for the `app` service to monitor the backend's responsiveness.
    ```dockerfile
    # Example in backend Dockerfile
    HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
      CMD python -c "import socket; socket.create_connection(('localhost', 8080), timeout=5)" || exit 1
    ```
*   **CI/CD**: The `.github/workflows/main.yml` file outlines the CI process, which includes building Docker images and running tests. Adapt this workflow for your production deployment pipeline (e.g., pushing images to a container registry like Docker Hub or ECR).

## Troubleshooting

### Common Issues

| Symptom                                  | Cause                                                                       | Solution                                                                                                         |
| :--------------------------------------- | :-------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------- |
| `docker compose up` fails during build   | Missing development dependencies or incorrect build context.                | Run `npm ci` in `web/` locally. Check `.dockerignore` files for unexpected exclusions. Update Node.js version if needed. |
| 502 Bad Gateway for `/api/*` requests    | Backend service is down or `proxy_pass` URL is incorrect.                   | Check `docker compose ps` for the `app` service status. Verify `proxy_pass http://app:8080/api/` in `nginx.conf`. |
| Frontend loads, but API calls fail       | CORS issues or incorrect `VITE_API_BASE` URL.                               | Ensure `VITE_API_BASE` is set to `/api` in `web/.env.production`. Check backend logs for CORS errors.           |
| Blank page on initial frontend load      | NGINX configuration missing SPA fallback or `index.html` not found.       | Verify `try_files $uri $uri/ /index.html;` in `web/nginx.conf`. Check NGINX container logs for file access errors. |
| Uploads fail (`413 Request Entity Too Large`) | Default NGINX `client_max_body_size` limit.                               | Add or increase `client_max_body_size` (e.g., `10M;`) in `web/nginx.conf`. Rebuild/restart the `web` service.         |
| Container exits immediately              | Application error (e.g., syntax error, unhandled exception).                | Examine the container logs using `docker compose logs <service_name>`.                                           |

### Debugging Techniques

*   **View Logs**: Always the first step.
    ```bash
    docker compose logs <service_name>
    docker compose logs -f # Follow logs in real-time
    ```
*   **Inspect Running Containers**: Access a shell inside a running container to check file systems, network status, and running processes.
    ```bash
    docker compose exec app bash      # Access backend container
    docker compose exec web sh        # Access NGINX container
    docker compose exec db psql -U ... # Access database client
    ```
*   **Test Network Connectivity**: From within one container, try connecting to another.
    ```bash
    # Inside the 'web' container, test connection to 'app'
    docker compose exec web curl http://app:8080/health
    ```
*   **Validate NGINX Configuration**: Check for syntax errors in the NGINX configuration file.
    ```bash
    docker compose exec web nginx -t
    ```

## Updating the Application

To deploy a new version of the application:

1.  **Pull Latest Changes**:
    ```bash
    git pull origin main # Or your primary branch
    ```
2.  **Rebuild and Restart**:
    ```bash
    docker compose up --build -d
    ```
    The `--build` flag ensures that Docker images are rebuilt based on any changes in the `Dockerfile` or related build assets.
3.  **Monitor Logs**: Keep an eye on the logs to ensure the update was successful.
    ```bash
    docker compose logs -f
    ```

If database schema changes or data migrations are required, they should be handled within the backend application logic or via separate migration scripts, possibly triggered after the service restart.
