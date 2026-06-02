# Local Development Setup

This guide details how to set up a local development environment for this fullstack application. The application comprises a **Python backend API** (served by `server.py`) and a **Vue 3 frontend** (managed by Vite). Both components are designed to be containerized, but this guide also covers native development for faster iteration.

The communication between the frontend and backend relies on **HTTP/JSON requests**, facilitated by the `src/api.js` utility. The backend exposes API endpoints mapped under a base path (e.g., `/api/*`), while the frontend handles static asset serving and client-side routing, with Nginx configured for production builds. Application configuration, such as backend API URLs and ports, is managed through environment variables, influencing both build-time frontend settings and runtime backend behavior.

This setup aims to balance reproducible development via Docker with the productivity benefits of native tooling.

---

## Prerequisites

Ensure you have the following tools installed on your development machine. Versions are important for compatibility and to avoid unexpected issues.

| Tool              | Minimum Version | Usage                                                                 |
| :---------------- | :-------------- | :-------------------------------------------------------------------- |
| Python            | 3.11            | Running the backend server (`server.py`) natively.                    |
| Node.js           | 18.x            | Developing and building the Vue.js frontend (`web/`).                 |
| npm               | 9.x             | Managing frontend dependencies and build scripts.                     |
| Docker            | 24.x            | Containerizing and running backend and frontend services.             |
| Docker Compose    | 2.20.x          | Orchestrating multi-container applications (`docker-compose.yml`).    |

### Tool Management Recommendations

*   **Python Version Management**: Use [pyenv](https://github.com/pyenv/pyenv) to install and manage multiple Python versions without conflict.
*   **Node.js Version Management**: Use [nvm (Node Version Manager)](https://github.com/nvm-sh/nvm) to easily switch between Node.js versions.

This approach helps maintain a clean system environment and ensures project-specific version requirements are met.

### Installing Prerequisites

Follow these steps to install and configure the necessary tools:

#### Using pyenv and pip for Python

1.  **Install pyenv**: (macOS/Linux)
    ```bash
    curl https://pyenv.run | bash
    ```
    Add the following lines to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):
    ```bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    ```
    Then, restart your shell or run `source ~/.bashrc` (or `source ~/.zshrc`).

2.  **Install Python 3.11**:
    ```bash
    pyenv install 3.11.9
    pyenv global 3.11.9  # Sets 3.11.9 as the default Python version
    ```

3.  **Verify Installation**:
    ```bash
    python --version
    pip --version
    ```
    Both commands should output versions consistent with Python 3.11.x.

#### Using nvm for Node.js and npm

1.  **Install nvm**:
    ```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    ```
    After installation, reload your shell configuration:
    ```bash
    source ~/.bashrc  # Or source ~/.zshrc
    ```

2.  **Install and Use Node.js 18.x**:
    ```bash
    nvm install 18
    nvm use 18
    ```

3.  **Verify Installation**:
    ```bash
    node --version
    npm --version
    ```
    Node.js should be v18.x.x, and npm should be v9.x.x or higher.

#### Alternative: System Package Managers

While pyenv and nvm are recommended, you can use system package managers for simpler setups:

*   **macOS (using Homebrew)**:
    ```bash
    brew install python@3.11 node@18
    # You may need to link them:
    # brew link python@3.11 --force
    # brew link node@18 --force
    ```

*   **Ubuntu/Debian**:
    ```bash
    sudo apt update
    sudo apt install -y python3 python3-pip nodejs npm
    # Verify versions: python3 --version, node --version, npm --version
    ```

*   **Windows**:
    Download and install the appropriate installers from the official sources:
    *   [Python 3.11 (64-bit)](https://www.python.org/downloads/windows/)
    *   [Node.js LTS 18.x](https://nodejs.org/en/download/)

> **Caution**: When installing system-wide, avoid using `pip install --user` or `npm install -g` for project dependencies. Always use virtual environments for Python and project-local `npm install` for Node.js to ensure consistent and reproducible builds.

---

## Repository Structure

A quick overview of the project's key files and directories:

```
├── server.py               # Main entry point for the Python backend application.
├── Dockerfile              # Defines the Docker image for the backend service.
├── docker-compose.yml      # Defines and configures multi-container services (backend, frontend).
├── web/                    # Contains the Vue 3 frontend source code.
│   ├── src/                # Vue component, utility, and main application files.
│   │   ├── App.vue         # Root Vue component.
│   │   ├── main.js         # Application entry point; mounts App.vue.
│   │   └── api.js          # Client for making API requests to the backend.
│   ├── index.html          # Main HTML template for the frontend.
│   ├── nginx.conf          # Nginx configuration for serving static assets and SPA routing.
│   ├── Dockerfile          # Defines the Docker image for the frontend service (using Nginx).
│   └── package.json        # Frontend project dependencies and scripts.
├── .github/workflows/main.yml  # CI/CD pipeline configuration.
└── docs/                   # Contains additional documentation, e.g., OpenAPI specs.
    └── openapi.yaml        # OpenAPI specification for the backend API.
```

**Key Components Analysis**:

*   **`server.py`**: Implements the backend API. It's likely using a framework like FastAPI or Flask, designed to be run with an ASGI/WSGI server (like `uvicorn`). It exposes API routes and is configured by environment variables.
*   **`web/` directory**: Houses the Vue 3 frontend, built with Vite.
    *   `web/src/api.js`: This file is crucial. It likely uses a library like `axios` or the native `fetch` API to communicate with the backend. It resolves the backend API URL using a Vite environment variable (`VITE_API_URL`).
    *   `web/nginx.conf`: Configured to serve the static assets produced by the Vite build (`dist/`). It also includes routing logic for Single Page Applications (SPAs), ensuring that client-side routes (like `/dashboard`) correctly return `index.html` for server-side processing.
    *   `web/Dockerfile`: A multi-stage build is used. The initial stage installs dependencies and builds the Vue application. The final stage copies only the built static assets into a lightweight Nginx image, optimizing the final image size.
*   **`Dockerfile` (root)**: Defines the base image and setup for the backend Python environment, likely using `python:3.11-slim`.
*   **`docker-compose.yml`**: Orchestrates the `backend` and `frontend` services. It defines networks, port mappings, volumes, and environment variables for each service, simplifying local development.

---

## Environment Variables

Environment variables are essential for configuring the application's behavior at runtime and build time.

### Backend (`server.py`) Environment Variables

These variables are read by the Python backend server. They can be set directly in the shell, via a `.env` file, or within `docker-compose.yml`.

| Variable        | Required | Default Value | Description                                                                                                                                                                                           |
| :-------------- | :------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SERVER_HOST`   | No       | `0.0.0.0`     | The network interface the backend server listens on. `0.0.0.0` makes it accessible externally (e.g., from Docker containers), while `localhost` or `127.0.0.1` restricts it to the local machine. |
| `SERVER_PORT`   | No       | `8000`        | The port number the backend server runs on. This should align with ports exposed in `docker-compose.yml` and any frontend configuration.                                                               |
| `API_BASE_PATH` | No       | `/api`        | The URL prefix for all backend API endpoints. For example, if set to `/v2/api`, all routes would be prefixed accordingly (e.g., `/v2/api/users`). This aids in versioning and modularity.          |
| `DEBUG`         | No       | `false`       | Enables debug mode. This often activates verbose logging, detailed error pages, and other development-specific features. **Crucially, this should always be `false` in production environments.** |

### Frontend (`web/`) Environment Variables

Vite injects these variables into the frontend build process. Variables prefixed with `VITE_` are exposed to the client-side code. Changes to these variables require a frontend rebuild (`npm run build`).

| Variable        | Required (at build) | Default Value       | Description                                                                                                                                                                                                                         |
| :-------------- | :------------------ | :------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VITE_API_URL`  | Yes                 | `http://localhost:8000` | **The complete base URL for the backend API**. This is critical. The `src/api.js` file uses this to construct full API request URLs. Include the protocol, host, port, and the `API_BASE_PATH` (e.g., `http://localhost:8000/api`). |
| `VITE_APP_TITLE`| No                  | `"MyApp"`           | Sets the title of the application, typically used in the HTML `<title>` tag.                                                                                                                                                      |

#### Setting Environment Variables for Development

1.  **Root `.env` file**: Create a file named `.env` in the repository's top-level directory. This file is often automatically loaded by development tools or scripts.
    ```env
    # .env
    SERVER_HOST=0.0.0.0
    SERVER_PORT=8000
    API_BASE_PATH=/api
    DEBUG=true
    VITE_API_URL=http://localhost:8000/api
    ```

2.  **Docker Compose `.env` file**: `docker-compose.yml` automatically reads a `.env` file from the same directory. This is useful for configuring containerized services.
    ```env
    # .env (for docker-compose)
    BACKEND_PORT=8000
    API_BASE_PATH=/api
    ```
    Note that `VITE_API_URL` for frontend builds in Docker Compose might need to be configured differently (e.g., via build arguments or by setting it during `npm run dev` inside the container).

> **Security**: Never commit sensitive credentials or production secrets to `.env` files. Use a `.env.example` file to document the necessary variables and their expected format for collaborators.

---

## Native Development (Non-Containerized)

This approach runs the backend and frontend services directly on your host machine, allowing for faster feedback loops, especially with hot-reloading for the frontend.

### 1. Backend Setup (`server.py`)

#### Install Python Dependencies

It's highly recommended to use a Python virtual environment to isolate project dependencies.

1.  **Create and activate a virtual environment**:
    ```bash
    # Create the environment (e.g., named 'venv')
    python -m venv venv

    # Activate the environment
    # Linux/macOS:
    source venv/bin/activate
    # Windows:
    # .\venv\Scripts\activate
    ```
    Your terminal prompt should now indicate the active environment (e.g., `(venv) your-prompt$`).

2.  **Install dependencies using pip**:
    If a `requirements.txt` file exists in the root directory:
    ```bash
    pip install -r requirements.txt
    ```
    If `requirements.txt` is not present, install the necessary packages manually:
    ```bash
    pip install fastapi uvicorn python-multipart python-dotenv
    ```
    It's good practice to generate `requirements.txt` after installing dependencies:
    ```bash
    pip freeze > requirements.txt
    ```

#### Run the Backend Server

Ensure your `.env` file is in the repository root, or set environment variables manually.

1.  **Load environment variables (Bash/Zsh)**:
    ```bash
    export $(cat .env | xargs)
    ```
    Alternatively, set them individually:
    ```bash
    export SERVER_PORT=8000
    export API_BASE_PATH=/api
    export DEBUG=true
    ```

2.  **Start the server using `uvicorn`**:
    The `server.py` file is assumed to contain an `app` object (e.g., a FastAPI or Starlette instance).
    ```bash
    uvicorn server:app --reload --host $SERVER_HOST --port $SERVER_PORT
    ```
    *   `server`: refers to the `server.py` file.
    *   `app`: refers to the ASGI application instance within `server.py`.
    *   `--reload`: automatically restarts the server when code changes are detected.
    *   `--host $SERVER_HOST --port $SERVER_PORT`: uses the environment variables for binding.

The backend should now be accessible at `http://localhost:8000`. You can verify this by accessing `http://localhost:8000/health` (if this endpoint exists) or checking the server logs.

### 2. Frontend Setup (`web/`)

#### Install Node.js Dependencies

Navigate to the `web` directory and install the frontend dependencies.

```bash
cd web
npm install
```

#### Configure API URL (if necessary)

The `src/api.js` file should be configured to use `import.meta.env.VITE_API_URL`. If it uses a hardcoded URL, update it to dynamically resolve the backend URL. Example using `fetch`:

```javascript
// web/src/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const get = async (endpoint) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// Add other methods like post, put, delete as needed
```

#### Run the Frontend Development Server

Start the Vite development server for rapid frontend development with hot module replacement (HMR).

```bash
# Ensure you are in the 'web' directory
cd web
npm run dev
```
This command typically starts the development server on `http://localhost:5173` (port may vary). All API requests made by the frontend will be directed to the URL specified in `VITE_API_URL`. This setup supports hot-reloading for frontend code changes, ensuring instant updates in the browser.

> **Result**: With both the backend and frontend running natively, you can access the application via the frontend's development server URL (e.g., `http://localhost:5173`). API calls will be made to the native backend server (`http://localhost:8000/api`).

---

## Containerized Local Development (Docker Compose)

Using Docker Compose provides an isolated and consistent environment that mirrors production configurations. This is especially useful for managing dependencies and ensuring reproducibility.

### Prerequisites

*   Docker Engine installed and running.
*   Docker Compose installed and running.

Verify installations:
```bash
docker --version
docker compose version
```

### Build and Run Services

1.  **Build and Start Services**:
    From the repository's root directory, execute:
    ```bash
    docker compose up --build
    ```
    This command builds the Docker images for the backend and frontend (if not already built) and starts the services defined in `docker-compose.yml`.

    *   **Access**: The frontend (served by Nginx) is typically available at `http://localhost:80` (default HTTP port). API requests prefixed with `/api` are proxied by Nginx to the backend service, which is accessible within the Docker network as `http://backend:8000`.

2.  **Environment Configuration within Docker**:
    *   **Backend**: `docker-compose.yml` defines environment variables for the backend service:
        ```yaml
        services:
          backend:
            build: .
            ports:
              - "${BACKEND_PORT:-8000}:8000"
            environment:
              - SERVER_HOST=0.0.0.0
              - SERVER_PORT=${BACKEND_PORT:-8000}
              - API_BASE_PATH=/api
              - DEBUG=${DEBUG:-false}
            # ... other configurations
        ```
        The `.env` file in the root directory influences `${BACKEND_PORT}` and `${DEBUG}`.
    *   **Frontend**: The `web/Dockerfile` sets `VITE_API_URL` during the image build process:
        ```dockerfile
        # web/Dockerfile
        FROM nginx:alpine AS production
        # ... build steps ...
        ARG NODE_ENV=production
        ARG VITE_API_URL=http://backend:8000/api/ # Default for container network
        ENV NODE_ENV=${NODE_ENV}
        ENV VITE_API_URL=${VITE_API_URL}
        # ... copy dist to nginx ...
        ```
        This ensures the frontend inside the container knows how to reach the backend service (`http://backend:8000/api`).

3.  **Development Workflow with Docker Compose**:

    *   **Backend Code Changes**:
        Edit `server.py`. To apply changes, you can either:
        *   Restart the backend service:
            ```bash
            docker compose restart backend
            ```
        *   Enable live reloading (if supported by your framework, e.g., `uvicorn --reload`). This often requires mounting the source code directory as a volume:
            ```yaml
            # docker-compose.yml snippet
            services:
              backend:
                volumes:
                  - .:/app  # Mount the entire project root, or specific files/dirs
            ```
            Note: Mounting the entire project might be necessary for `--reload` to work effectively, depending on the framework's watch mechanism.

    *   **Frontend Code Changes**:
        For rapid frontend iteration, you can run the Vite dev server *inside* its container:
        ```bash
        # Ensure the frontend service is running (e.g., via 'docker compose up -d frontend')
        docker compose exec frontend npm run dev -- --host 0.0.0.0 --port 5173
        ```
        Access the app at `http://localhost:5173` (you might need to expose this port in `docker-compose.yml`).
        Alternatively, use volume mounts for the `web` directory to enable Vite's HMR directly from your host machine:
        ```yaml
        # docker-compose.yml snippet
        services:
          frontend:
            volumes:
              - ./web:/usr/src/web # Mount the web directory
        ```
        Then, execute `npm run dev` inside the `frontend` container.

> **Performance Tip**: Volume mounts can sometimes be slower than bind mounts or copying files. For optimal build performance, rely on Docker layers for dependencies and code, rebuilding images as needed (`docker compose build frontend`).

---

## Troubleshooting Common Issues

### Frontend Connection Problems (`CORS`, `ERR_CONNECTION_REFUSED`)

*   **Check `VITE_API_URL`**: Ensure it correctly points to the backend's host, port, and API base path.
    *   **Native**: `http://localhost:8000/api`
    *   **Docker Compose**: `http://backend:8000/api` (within Docker network) or `http://localhost:8000/api` (if mapped to host).
*   **Backend Host Binding**: Verify `SERVER_HOST` is set to `0.0.0.0` for the backend when running in Docker, allowing it to accept connections from the frontend container.
*   **CORS Configuration**: Ensure the backend CORS middleware is configured correctly if you encounter CORS errors.

### Frontend Build/Runtime Errors (`Module not found`)

*   **Reinstall Dependencies**: Delete `web/node_modules` and `web/package-lock.json`, then run `npm install`.
*   **Vite Configuration**: Check `vite.config.js` for any incorrect aliases or `exclude` patterns in `resolve.modules` that might prevent modules from being found.

### Backend Installation Failures (`ModuleNotFoundError`)

*   **Dependencies**: Ensure all required packages are listed in `requirements.txt`. If not, update it (`pip freeze > requirements.txt`) and rebuild the backend Docker image (`docker compose build backend --no-cache`).
*   **Python Version**: Confirm the base image in `Dockerfile` matches the project's Python version requirements.

### Single Page Application (SPA) Routing Issues (`404` for routes like `/dashboard`)

*   **Nginx Configuration**: Verify `web/nginx.conf` includes a `try_files` directive to fall back to `/index.html` for unmatched routes:
    ```nginx
    location / {
      root /usr/share/nginx/html; # Or wherever static files are copied
      index index.html index.htm;
      try_files $uri $uri/ /index.html;
    }
    ```

### Docker Compose Errors (`manifest not found`, service startup failures)

*   **Typos**: Double-check service names, image names, and paths in `docker-compose.yml`.
*   **Cache Issues**: Use `docker compose up --build --force-recreate` to ensure fresh image builds and container startups.
*   **Resource Limits**: Ensure your system has sufficient resources (RAM, disk space) for Docker operations.

---

## Testing and Validation

After setting up your local environment, perform these checks to ensure the application is functioning correctly:

1.  **Backend Health Check**:
    *   **Native**: `curl http://localhost:8000/health`
    *   **Docker Compose**: `curl http://localhost/health` (Nginx proxies to backend)
    Expected output: `{"status": "ok"}` (or similar success indicator).

2.  **API Endpoint Verification**:
    *   **Native**: `curl http://localhost:8000/api/users` (Replace `/users` with an actual endpoint)
    *   **Docker Compose**: `curl http://localhost/api/users`
    Check for valid JSON responses. Refer to `docs/openapi.yaml` for available endpoints.

3.  **Frontend UI Interaction**:
    *   Access the application in your browser at the appropriate URL (`http://localhost:5173` for native dev, `http://localhost` for Docker Compose).
    *   Use browser Developer Tools (Network tab) to confirm that API requests are successful (HTTP 200 OK) and return the expected data.

4.  **End-to-End Functionality**:
    *   If the application has authentication, test the login flow.
    *   Navigate through different sections of the UI (e.g., accessing `/dashboard` or user profile pages) to ensure client-side routing and data loading work seamlessly.

---

## Next Steps and Maintenance

### Adding New Dependencies

*   **Backend**: Update `requirements.txt` after installing new Python packages (`pip install <package>`, then `pip freeze > requirements.txt`).
*   **Frontend**: Add new Node.js packages using `npm install <package>` and commit the updated `package.json` and `package-lock.json`.

### Aligning with CI/CD

Ensure the `Dockerfile`, `docker-compose.yml`, and the CI pipeline configuration (`.github/workflows/main.yml`) are consistent regarding:
*   Base Docker images used.
*   Environment variables injected.
*   Build arguments (e.g., `VITE_API_URL`).
*   Build commands and processes.

This consistency prevents discrepancies between local development and automated builds.

### Integrating External Services (Databases, Caches)

When introducing new services (e.g., PostgreSQL, Redis):
*   Update `docker-compose.yml` to include their definitions.
*   Add necessary environment variables to `.env` and document them in `.env.example`.
*   Configure the backend application (`server.py`) to connect to these services using the environment variables.

### Adding Automated Tests

*   **Backend**: Implement tests using a framework like `pytest`.
*   **Frontend**: Use Vitest or Jest for unit and integration tests.
*   Ensure test commands are available in `scripts` (in `package.json`) and integrate them into the CI pipeline.

### Maintaining Documentation

This `README.md` should be updated whenever significant changes occur:
*   New environment variables are introduced or changed.
*   Default ports or API paths are modified.
*   The structure of Docker builds or Compose services changes.
*   Core dependencies (Node.js, Python versions) are updated.

**Further Resources**:
*   Consult `docs/openapi.yaml` for detailed API endpoint specifications.
*   Review `server.py` for inline code documentation.
*   Refer to the official [Vue.js](https://vuejs.org/guide/) and [Vite](https://vitejs.dev/guide/) documentation for frontend specifics.
