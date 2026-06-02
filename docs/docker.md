# Docker Setup

## Overview

This repository is configured for containerized deployment using Docker. It features a full-stack application comprising a Python backend and a Vue.js frontend. The project includes a `Dockerfile` for building the backend service image, and a separate build process within the `web/` directory for the frontend, which is served by Nginx. The `docker-compose.yml` file is provided to orchestrate the startup, networking, and volumes for both the backend and frontend services, significantly simplifying local development and deployment.

Key aspects of this Docker setup include:
*   **Backend Image:** Utilizes a `python:3.11-slim` base image for a compact and efficient Python runtime environment.
*   **Frontend Image:** Employs a multi-stage build process. An initial stage leverages a Node.js image to build the Vue.js application into static assets. A subsequent stage uses `nginx:alpine` to serve these static assets, incorporating the `web/nginx.conf` configuration for optimal performance and routing.
*   **Dependency Management:** Python dependencies are managed via `requirements.txt`, while frontend dependencies are handled by `package.json` and `package-lock.json`.
*   **Orchestration:** `docker-compose.yml` defines the services, networks, and volume mappings, enabling a cohesive application stack that can be managed with simple Docker Compose commands.

This documentation provides comprehensive guidance on setting up, building, running, and managing the Dockerized application.

---

## Install Requirements

### Docker Engine & Compose

To build and run the Docker containers for this application, ensure you have Docker Engine and Docker Compose installed on your system.

#### System-Level Prerequisites

| Tool            | Installation Method                                                                                                                                                                                                                                                                                                                            | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| :-------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Docker Engine** | **Linux:** Follow the official Docker installation guide for your distribution (e.g., using `apt` for Debian/Ubuntu, `yum`/`dnf` for RHEL/CentOS). <br> **macOS/Windows:** Download and install Docker Desktop from the official Docker website.                                                                                                     | After installation on Linux, it's recommended to add your user to the `docker` group to execute Docker commands without `sudo`: <br> `sudo usermod -aG docker $USER` <br> You will need to log out and log back in for this change to take effect.                                                                                                                    |
| **Docker Compose** | **Docker Desktop:** Includes Docker Compose (v2.0+) as a Docker CLI plugin by default. <br> **Linux (Standalone):** For standalone installations, download the binary from the official Docker Compose releases page on GitHub. <br> ```bash <br> # Example for v2.24.0 - check for the latest version <br> curl -SL \"https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose <br> chmod +x /usr/local/bin/docker-compose <br> ``` | Ensure the installed Docker Compose version is compatible with your Docker Engine version. For Linux users with Docker Desktop, the compose plugin is typically configured automatically.                                                                                                                                                                                                     |

### Language-Specific Dependencies (for Local Development and Debugging)

While Docker containerizes the application's runtime, developers might need local installations of Python and Node.js for advanced local development tasks, debugging outside of Docker, or executing local scripts.

| Component             | Language   | Package Manager                                                              | Installation Commands                                                                                                                                                                                                                                                                                                                                                                                                                   | Notes                                                                                                                                                                                                                                                                                                   |
| :-------------------- | :--------- | :--------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Python Runtime**    | Python     | System Package Manager (`apt`, `yum`, `brew`, etc.) or Version Managers | **Debian/Ubuntu:** `sudo apt update && sudo apt install python3 python3-pip` <br> **macOS:** `brew install python` <br> **Other OS:** Consult your system's package manager documentation. Consider using `pyenv` for managing multiple Python versions.                                                                                                                                                                                                                   | Ensure `python3` and `pip3` (or `pip`) are accessible in your system's PATH. Using virtual environments (e.g., `venv`) is highly recommended for Python project development to isolate dependencies.                                                                                                                   |
| **Node.js & npm/Yarn**| JavaScript | **`nvm` (Node Version Manager - Recommended)** or System Package Manager     | **Using `nvm`:** <br> ```bash <br> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh \| bash <br> source ~/.bashrc # or ~/.zshrc <br> nvm install 20 # Installs current LTS Node.js v20.x <br> nvm use 20 <br> # Optional: Install Yarn globally if preferred over npm <br> npm install -g yarn <br> ``` <br> **Using System Package Manager (e.g., `apt`):** <br> `sudo apt update && sudo apt install nodejs npm` (Note: OS package manager versions might be older). | `nvm` is the preferred method for managing Node.js versions, allowing easy switching between different project requirements. Verify installations with `node -v` and `npm -v`. The frontend build process in `web/Dockerfile` likely targets a Node.js version around v20.x.                                   |
| **Python Dependencies**| Python     | `pip`                                                                        | ```bash <br> # If not running inside Docker, navigate to the backend directory if requirements are specific to it <br> # cd backend_directory/ <br> pip install -r requirements.txt <br> ```                                                                                                                                                                                                                                                                                                        | Run this command within an activated Python virtual environment. This installs all packages listed in `requirements.txt`.                                                                                                                                                                            |
| **Frontend Dependencies**| JavaScript | `npm` or `yarn`                                                              | ```bash <br> cd web <br> npm install # or `yarn install` if Yarn is used <br> ```                                                                                                                                                                                                                                                                                                                                                                                      | This command installs all JavaScript dependencies defined in `web/package.json` and generates/updates the `web/package-lock.json` file, ensuring reproducible builds.                                                                                                                                    |

---

## Architecture Overview

### Backend Service (`server.py`, `Dockerfile`)

The backend is written in Python and is containerized using a `Dockerfile` based on the `python:3.11-slim` image. This base image is chosen for its minimal size and efficient Python 3.11 runtime.

*   **Dockerfile Structure:** The `Dockerfile` for the backend typically executes commands such as:
    1.  Setting a working directory (e.g., `WORKDIR /app`).
    2.  Copying `requirements.txt` into the container.
    3.  Installing Python dependencies using `pip install --no-cache-dir -r requirements.txt`. The `--no-cache-dir` flag is used to reduce the final image size by preventing pip from storing downloaded packages locally within the image.
    4.  Copying the application's source code into the container.
    5.  Exposing the port the application listens on (e.g., `EXPOSE 8000`).
    6.  Defining the command to run the application, often `CMD ["python", "server.py"]` for simple Flask applications, or a command that starts a production-grade WSGI server like Gunicorn (e.g., `CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "server:app"]`).
*   **Dependencies:** Managed by the `requirements.txt` file. The backend is expected to provide an API with approximately 11 endpoints, as inferred from project analysis.
*   **Runtime Environment:** The `python:3.11-slim` image is Debian-based, offering a secure foundation. For enhanced security, it is best practice to configure the `Dockerfile` to run the application as a non-root user.
*   **Data Persistence:** Container filesystems are ephemeral. Persistent data, such as logs or user uploads, should be managed through Docker volumes, which are typically configured in `docker-compose.yml` (e.g., `./logs:/app/logs`).

### Frontend Service (`web/`, `web/Dockerfile`, `web/nginx.conf`)

The frontend is a Vue.js application. It is built into static assets (HTML, CSS, JavaScript) using Node.js and then served efficiently by an Nginx web server.

*   **Build Process (Multi-Stage Dockerfile):** The `web/Dockerfile` implements a multi-stage build strategy:
    1.  **Build Stage:** Utilizes a Node.js image (e.g., `node:20-alpine`) to install project dependencies (using `npm ci` for clean installations based on `package-lock.json`) and execute the build command (e.g., `npm run build`). This stage produces the static application files, usually in a `dist/` directory.
    2.  **Production Stage:** Employs a lightweight `nginx:alpine` image. It copies the generated static assets from the build stage into the Nginx web root (typically `/usr/share/nginx/html/`). The Nginx configuration file (`web/nginx.conf`) is copied over the default Nginx configuration.
*   **NGINX Configuration (`web/nginx.conf`):** This configuration file is critical for serving the frontend assets and handling routing:
    *   **Single Page Application (SPA) Routing:** A directive such as `try_files $uri $uri/ /index.html;` is essential within the `location /` block. This ensures that for any requested path that doesn't match a static file, Nginx serves `index.html`. This allows the Vue Router to manage client-side routing for dynamic URLs.
    *   **Caching:** Directives for browser caching of static assets (e.g., `expires 1y; add_header Cache-Control "public, immutable";`) are typically configured to improve load times on subsequent visits.
    *   **Compression:** `gzip` compression is usually enabled to reduce the transfer size of assets.
*   **Dependencies:** Managed through `web/package.json` and `web/package-lock.json`. The build process relies on npm scripts defined within `package.json`.

---

## Image Details

### Backend Image

| Property          | Value                                                                                                                                                                                          | Notes                                                                                                                                                                                                                                                        |
| :---------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Base Image**    | `python:3.11-slim`                                                                                                                                                                             | Based on Debian Bookworm, this image is approximately 150MB, offering a compact and secure environment for Python 3.11.                                                                                                                                        |
| **Build Strategy**| Likely a single-stage build, where dependencies are installed directly onto the final runtime image.                                                                                           | Consider implementing a multi-stage build for the backend if specific build tools are not required in the final running container, further reducing the image size.                                                                                             |
| **System Packages**| No explicit system packages are installed via `apt-get` within the provided `Dockerfile`.                                                                                                      | This implies that standard command-line utilities like `bash`, `curl`, or `vim` might not be available in the container. Debugging may require using the limited built-in shell (`sh`) or Python's diagnostic capabilities.                                            |
| **Entrypoint/Cmd**| The `CMD` instruction in the `Dockerfile` is likely set to `["python", "server.py"]` or configured to use a WSGI server like `gunicorn` (e.g., `gunicorn -b 0.0.0.0:8000 server:app`). | Verify the Flask application instance name in `server.py` (e.g., `app = Flask(__name__)`). For production deployments, using `gunicorn` is standard practice. Ensure the port (`8000` is a common default) is correctly exposed and the application listens on it. |
| **User**          | The `Dockerfile` may default to running as the `root` user.                                                                                                                                    | **Security Best Practice:** Modify the `Dockerfile` to create a dedicated non-root user (e.g., `appuser`) and switch to it using the `USER` instruction before executing the application commands.                                                             |
| **Volumes**       | The `Dockerfile` does not define default volumes.                                                                                                                                              | Volumes for persistent data storage (e.g., logs, databases, uploads) should be explicitly defined and managed within the `docker-compose.yml` file.                                                                                                      |
| **Build Context** | Ensure a `.dockerignore` file is present to exclude unnecessary files and directories (like `node_modules`, `.git`, build artifacts) from the Docker build context, speeding up the build process and reducing image layers.                                                               |                                                                                                                                                                                                                                                          |

---

## Building and Running the Application

### Building Docker Images

This application uses Docker Compose to manage multi-container setups. Changes to the `Dockerfile` or `docker-compose.yml` file may necessitate rebuilding the images.

1.  **Navigate to the Project Root:**
    ```bash
    cd /path/to/your/repository
    ```

2.  **Build the Services:**
    Run the following command in the repository's root directory. Docker Compose will read the `docker-compose.yml` file and build or pull the necessary images, then start the containers.

    ```bash
    docker-compose build
    ```
    This command will:
    *   Build the backend image based on the `Dockerfile` in the root directory.
    *   Build the frontend image based on the `Dockerfile` within the `web/` directory.
    *   Download any other required base images.

### Running the Application

After successfully building the images, you can start the application stack using Docker Compose.

1.  **Start Services in Detached Mode:**
    ```bash
    docker-compose up -d
    ```
    This command will:
    *   Start the backend service container.
    *   Start the frontend (Nginx) service container.
    *   Connect the containers to the network defined in `docker-compose.yml`.
    *   The `-d` flag runs the containers in the background (detached mode).

2.  **Access the Application:**
    The application should now be accessible via your web browser.
    *   **Frontend:** By default, Nginx serves the frontend at `http://localhost:80` (or the port mapped in `docker-compose.yml`).
    *   **Backend:** The backend API is typically exposed internally on a port (e.g., `8000`) and is accessible by the frontend service via the Docker network. Direct external access to the backend port might not be configured by default.

### Stopping the Application

To stop the running services:

```bash
docker-compose down
```
This command stops and removes the containers, networks, and default volumes created by `docker-compose up`. If you wish to preserve volume data, you can use `docker-compose stop`.

### Environment Variables

The application might rely on environment variables for configuration. These are typically defined in a `.env` file in the project root, which `docker-compose.yml` automatically loads. Common variables might include:

*   `DATABASE_URL`: Connection string for the database.
*   `API_KEY`: Secret key for API authentication.
*   `NODE_ENV`: Environment for the Node.js build (e.g., `production`, `development`).

Examine the `docker-compose.yml` file and the application's code (`server.py`, `web/src/api.js`) to identify all required environment variables.

---

## Development Workflow

### Local Development Server Commands

While Docker Compose provides a production-like environment, you might also run development servers locally for faster iteration.

1.  **Backend Development Server:**
    ```bash
    # Ensure you have Python dependencies installed locally (see Install Requirements)
    # Activate your Python virtual environment
    # cd path/to/your/repo
    python server.py
    ```
    This command starts the Flask development server. Ensure the port it listens on is consistent with frontend expectations or Docker Compose configuration.

2.  **Frontend Development Server:**
    ```bash
    # Ensure you have Node.js and npm/yarn installed locally (see Install Requirements)
    cd web
    npm run dev # Or yarn dev, depending on your package.json scripts
    ```
    This command typically starts the Vue.js development server with hot-reloading enabled, providing a fast feedback loop during frontend development.

### API Documentation

The OpenAPI specification for the backend API is available at `docs/openapi.yaml`. This file can be used to generate client SDKs, interactive documentation (e.g., using Swagger UI or Redoc), or for overall API understanding.

```bash
# Example: Serving API docs locally using a separate tool
# docker run --rm -p 8080:8080 -v "${PWD}/docs/openapi.yaml":/usr/share/nginx/html/openapi.yaml swaggerapi/swagger-ui
# Then access http://localhost:8080
```

---

## Troubleshooting Common Issues

*   **Container Exits Immediately:** Check container logs using `docker-compose logs <service_name>` (e.g., `docker-compose logs backend`). Errors in application startup, missing dependencies, or incorrect environment variables are common causes.
*   **Frontend Not Loading / 404 Errors:**
    *   Verify the Nginx configuration (`web/nginx.conf`) correctly handles SPA routing (`try_files`).
    *   Ensure the frontend build process (`npm run build`) completed successfully and placed assets in the expected directory (e.g., `dist/`).
    *   Check Nginx container logs: `docker-compose logs frontend`.
*   **Backend API Not Responding:**
    *   Confirm the backend container is running: `docker ps`.
    *   Check backend logs: `docker-compose logs backend`.
    *   Verify that the frontend is configured to communicate with the backend using the correct service name and port as defined in `docker-compose.yml` (e.g., `http://backend:8000`). Do not use `localhost` for inter-container communication.
*   **Port Conflicts:** If `docker-compose up` fails with "port is already allocated," another process on your host machine is using the port specified in `docker-compose.yml`. Either stop the conflicting process or change the host port mapping in `docker-compose.yml` (e.g., `8081:80` instead of `80:80`).
*   **Dependency Issues:** Ensure local dependencies are installed correctly (`pip install -r requirements.txt`, `npm install`) if you are performing development tasks outside of Docker. Within Docker, verify that the `requirements.txt` and `package.json` files are correct and the installation commands in the Dockerfiles execute without errors.

---

## Production Hardening and Best Practices

*   **Non-Root User:** Always configure containers to run applications as non-root users. Modify the `Dockerfile(s)` to create and switch to a dedicated user.
*   **Least Privilege:** Only install necessary packages and dependencies. Use slim base images.
*   **Secrets Management:** Avoid hardcoding sensitive information directly in `Dockerfile` or `docker-compose.yml`. Use environment variables loaded from a secure `.env` file or integrate with a secrets management system.
*   **Health Checks:** Implement health check endpoints in your backend service and configure them in `docker-compose.yml` to allow Docker to monitor and restart unhealthy containers.
*   **Logging:** Ensure robust logging from both backend and frontend services. Configure Docker logging drivers appropriately for your production environment (e.g., forward logs to a centralized logging system).
*   **Resource Limits:** Set CPU and memory limits for containers in `docker-compose.yml` to prevent resource exhaustion.
*   **Regular Updates:** Keep base images and application dependencies updated to patch security vulnerabilities.
*   **Read-Only Root Filesystem:** If possible, configure containers to run with a read-only root filesystem and mount specific directories as writable volumes only where necessary.
