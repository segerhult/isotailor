# Architecture Overview

## Overview

This repository houses a full-stack web application. The architecture is characterized by a Python-based backend API server and a JavaScript/TypeScript frontend built using Vue 3 and Vite. The backend, implemented with Python's standard `http.server` module, offers a lightweight, self-contained REST-like API. It handles functionalities such as file uploads, generation of software package manifests, and the creation of custom installation instructions tailored for Debian-based systems. The frontend is a Single Page Application (SPA) served via Nginx, optimized for production with efficient static asset management, an abstracted API client, and adherence to responsive design principles.

A clear separation of concerns is maintained throughout the architecture. The backend exposes a minimal yet extensible HTTP API, incorporating explicit security measures like HTML sanitization and protection against path traversal vulnerabilities. The frontend communicates with this API over HTTP using structured requests. Data persistence is achieved through a file-based system, utilizing a JSON index (`uploads.json`) and a dedicated directory for uploads (`data/uploads/`), which is well-suited for lightweight, local deployments without reliance on external database systems.

Containerization is achieved using Docker, with orchestration managed by Docker Compose. This ensures reproducible local development environments and consistent deployments across various environments. A Continuous Integration and Continuous Deployment (CI/CD) pipeline, configured in GitHub Actions (`.github/workflows/main.yml`), automates testing, linting, and the building of container images.

---

## Frontend

The frontend is developed using Vue 3, leveraging the Composition API. Vite serves as the build tool, and Nginx is employed as the production web server. The frontend codebase is located within the `web/` directory and includes the following key components:

-   **Entry Point**: `web/src/main.js` is responsible for initializing the Vue application.
-   **Root Component**: `web/src/App.vue` structures the overall layout and navigation of the application.
-   **API Integration**: `web/src/api.js` provides an abstraction layer for RESTful communication with the backend API. This includes handling requests for file uploads and retrieving software manifest data.
-   **Static Assets and Configuration**: Files such as `web/index.html` (the main HTML entry point), `web/vite.config.js` (Vite build configuration), `web/nginx.conf` (Nginx server configuration for production), and `web/.dockerignore` (files to exclude from the frontend Docker image) collectively manage the bundling process, local development serving, and production deployment via Nginx.

The frontend is designed to be decoupled from the backend, utilizing relative API paths (e.g., `/api/...`) for service discovery. This design choice enhances flexibility in deployment scenarios, allowing for integration with development servers, Content Delivery Networks (CDNs), or reverse proxies. The frontend avoids reliance on heavy external UI frameworks or CDNs, thereby maintaining a minimal, secure, and performant codebase.

---

## Backend

The backend is implemented as a Python 3.11 HTTP server (`server.py`) which exposes a custom REST-like API. It notably avoids external web framework dependencies like Flask or FastAPI, relying instead on Python's standard library modules such as `http.server`, `json`, and `pathlib`. The server is designed to handle concurrent requests efficiently through the use of `ThreadingHTTPServer`.

Key architectural and security considerations include:

-   **Thread Safety**: Utilizes `ThreadingHTTPServer` to manage concurrent client requests effectively.
-   **Security**: Implements input sanitization using `html.escape` to prevent cross-site scripting (XSS) attacks. File upload paths are validated and restricted using `Path.resolve()` to prevent directory traversal exploits.
-   **State Persistence**: Manages application state by storing an index of uploaded files and metadata in `data/uploads.json`. This includes timestamps and history of software manifest generation.

### API Endpoints (Heuristic count: 11)

The backend exposes the following API endpoints:

1.  `GET /api/status`: Provides health check information and runtime metadata, such as the Python version and server uptime.
2.  `GET /api/manifest`: Generates an installation manifest, including example commands for Debian/Ubuntu systems using `apt`, based on a list of specified software packages.
3.  `POST /api/manifest`: Accepts a JSON payload containing a `software` field to generate customized installation manifests.
4.  `GET /api/uploads`: Lists all files that have been uploaded and indexed.
5.  `POST /api/upload`: Handles multipart/form-data file uploads. Uploaded files are stored in the `data/uploads/` directory, and their metadata is recorded in the index.
6.  `GET /api/upload/<id>`: Retrieves the metadata and a download link for a specific uploaded file, identified by its unique ID.
7.  `DELETE /api/upload/<id>`: Deletes a specific uploaded file and its corresponding entry from the index. This operation is designed to be idempotent.
8.  `GET /api/defaults`: Returns a predefined list of default software packages considered essential or commonly used (e.g., `curl`, `vim`, `git`).
9.  `GET /`: Serves the `index.html` file of the SPA. This acts as a fallback route, particularly for handling client-side routing in the frontend application.

All API endpoints are designed to return JSON responses for API-specific requests. The root route (`GET /`) provides an HTML fallback. Explicit HTTP status codes are used consistently to indicate the outcome of requests (e.g., `200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`).

### Storage

Data is managed locally within the file system:

-   **`data/`**: The root directory for all persistent application data.
-   **`data/uploads/`**: This directory stores the actual binary files that have been uploaded via the API. It is designed to be isolated and does not require elevated privileges.
-   **`data/uploads.json`**: A JSON file that serves as an index, mapping unique upload IDs to their associated metadata. This metadata includes the file path, original filename, timestamp, and any detected MIME-type hints.

This storage strategy prioritizes simplicity and portability, eliminating the need for external database dependencies. It is suitable for development, edge cases, or low-volume deployments. For production environments requiring higher throughput or scalability, a migration to persistent volumes or external object storage solutions (e.g., AWS S3, Google Cloud Storage, MinIO) would be necessary.

---

## Containers

The project utilizes a multi-stage Docker setup to build and deploy both the backend and frontend services.

### Backend Container (`Dockerfile`)

-   **Base Image**: Built upon `python:3.11-slim`, providing a minimal Python 3.11 environment.
-   **Build Context**: The Dockerfile operates from the repository root. Only necessary files are copied into the image to minimize layer size and build time.
-   **Runtime**: The application runs using Python’s built-in `http.server` module. No additional system packages are pre-installed beyond what is included in the slim base image.
-   **Data Persistence**: The `data/` directory, which holds uploads and the index file, is intended to be mounted as a Docker volume. This ensures that data is preserved across container restarts and updates.

### Frontend Container (`web/Dockerfile`)

This Dockerfile employs a multi-stage build process:

-   **Build Stage**: Uses a Node.js base image to install frontend dependencies (`npm install`) and build the Vue application (`vite build`). The output of this stage is the optimized static assets, typically located in the `dist/` directory.
-   **Production Stage**: This stage uses a lightweight `nginx:alpine` image. It serves the static assets produced in the build stage. The Nginx configuration (`web/nginx.conf`) handles routing, compression (gzip), caching strategies, and serves the `index.html` for the SPA, along with other static files. The container exposes port `80` for incoming HTTP traffic.

### Orchestration (`docker-compose.yml`)

The `docker-compose.yml` file defines and orchestrates the backend and frontend services:

-   **Services**: It defines two primary services: `backend` and `frontend`.
-   **Backend Service**: Exposes port `8000` and is configured to mount the `data/` directory as a named volume for persistent storage.
-   **Frontend Service**: Depends on the `backend` service to ensure it starts after the backend is available. It exposes port `80`. Critically, it configures Nginx (via `web/nginx.conf`) to act as a reverse proxy, forwarding all requests prefixed with `/api` to the `backend` service. Other requests are served as static assets from the built frontend application.

This Docker Compose setup facilitates easy local development using `docker-compose up --build -d`. It also prepares the application for production-like deployments. For local development without Docker, the frontend can be run using `npm run dev`, which leverages Vite's development server and is configured to proxy API requests automatically.

---

## CI/CD

The repository includes a GitHub Actions workflow defined in `.github/workflows/main.yml` to automate Continuous Integration and Continuous Deployment (CI/CD) processes. This pipeline enforces code quality, tests application integrity, and manages container image deployment. Key stages include:

-   **Linting**: Automated checks for code quality and style are performed on Python code (e.g., using `flake8` or `pylint` heuristics) and JavaScript/TypeScript code (using `eslint`). Additionally, configuration files like YAML and Docker Compose files are linted.
-   **Testing**: The pipeline includes steps to run automated tests (if unit tests are implemented). It also validates API contract endpoints, typically using tools like `curl`, to ensure the backend is responding correctly. Successful Docker image builds are also verified.
-   **Security Scanning**: Vulnerability scanning is performed on container images and project dependencies to identify and report known security issues (e.g., using `trivy` or `npm audit`).
-   **Image Publishing**: Upon successful completion of the checks on the `main` branch, container images are automatically pushed to a container registry, such as GitHub Container Registry (GHCR). This process requires authentication, typically managed through repository secrets like `REGISTRY_USERNAME` and `REGISTRY_PASSWORD` configured in the GitHub repository settings.

---

## Repository Layout

The repository is organized to clearly separate concerns and facilitate development and maintenance.

```
├── .github/                    # CI/CD configurations and workflows.
│   └── workflows/
│       └── main.yml           # GitHub Actions pipeline definition.
├── data/                       # Runtime data and persistent storage. Generated on first run.
│   ├── uploads/               # Directory for storing uploaded files.
│   └── uploads.json           # JSON index mapping upload IDs to file metadata.
├── docs/                       # Project documentation.
│   └── openapi.yaml           # OpenAPI 3.0 specification detailing the backend API.
├── web/                        # Frontend application code.
│   ├── dist/                   # Production-ready static assets, generated by Vite build.
│   ├── nginx.conf              # Nginx configuration for serving the frontend and proxying API requests.
│   ├── Dockerfile              # Multi-stage Dockerfile for building the frontend container.
│   ├── .dockerignore          # Specifies files/directories to exclude from the frontend Docker build context.
│   ├── index.html              # The main HTML file, entry point for the SPA.
│   ├── package.json            # NPM project configuration, listing dependencies (Vue, Vite, etc.).
│   ├── package-lock.json       # Lockfile ensuring reproducible frontend dependency installations.
│   ├── vite.config.js          # Vite build tool configuration, including Vue plugin setup and path aliases.
│   └── src/                    # Source code for the Vue.js application.
│       ├── App.vue            # The root Vue component.
│       ├── api.js             # Module for abstracting API communication.
│       └── main.js            # Vue application entry point.
├── Dockerfile                  # Dockerfile for building the backend API server container.
├── docker-compose.yml          # Docker Compose configuration for orchestrating backend and frontend services.
├── server.py                   # The main Python script for the backend API server.
├── .dockerignore              # Specifies files/directories to exclude from the backend Docker build context.
├── .gitignore                 # Git configuration listing files and directories to ignore (e.g., `data/`, `node_modules/`).
├── README.md                  # Project overview, setup instructions, and general documentation.
└── LICENSE                    # Project license (e.g., Apache-2.0).
```

This layout promotes modularity and clarity. The backend and frontend are co-located within the same repository for monorepo simplicity, while maintaining a clear separation. Shared configurations, such as Dockerfiles at the root level, are utilized where appropriate.

---

## System Diagram

```mermaid
graph TD
  subgraph Client
    Browser[Web Browser]
  end

  subgraph Frontend Service
    NginxFE[Nginx<br/>(Serves static assets from /dist)]
    VueApp[Vue SPA<br/>(assets served by Nginx)]
  end

  subgraph Backend Service
    PythonServer[Python HTTP Server<br/>(`server.py`)]
    FileStorage[File Storage<br/>(`data/uploads/`)]
    JsonIndex[JSON Index<br/>(`data/uploads.json`)]
  end

  subgraph Orchestration
    DockerCompose[Docker Compose]
  end

  Browser -->|HTTP/HTTPS| NginxFE
  NginxFE -->|Serve Static Assets| VueApp
  NginxFE -->|Proxy API Requests (/api/*)| PythonServer

  PythonServer -->|Read/Write| FileStorage
  PythonServer -->|Read/Write| JsonIndex

  DockerCompose --> NginxFE
  DockerCompose --> PythonServer
```

-   **Client**: A web browser interacts with the deployed application.
-   **Frontend Service**: Nginx efficiently serves the static assets of the Vue SPA. It also acts as a reverse proxy, forwarding API requests (`/api/*`) to the backend service.
-   **Backend Service**: The Python HTTP server (`server.py`) handles API requests, interacting with the file storage (`data/uploads/`) for uploaded files and the JSON index (`data/uploads.json`) for metadata.
-   **Orchestration**: Docker Compose manages the deployment and networking of the frontend and backend services.

---

## Install Requirements

### Prerequisites (for local development outside of Docker)

Before setting up the project locally without Docker, ensure the following software is installed:

-   **Python ≥ 3.11**:
    -   **macOS**: Install via Homebrew: `brew install python`
    -   **Ubuntu/Debian**: Use apt: `sudo apt-get update && sudo apt-get install python3.11 python3-pip`
    -   **Windows**: Download the installer from the official [Python website](https://www.python.org/downloads/).

-   **Node.js ≥ 20 and npm ≥ 10**:
    -   **macOS**: Install via Homebrew: `brew install node`
    -   **Ubuntu/Debian**: Use NodeSource repository: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs`
    -   **Windows**: Download the installer from the official [Node.js website](https://nodejs.org/).

-   **Docker & Docker Compose**: *(Highly recommended for a consistent development and deployment experience)*
    -   **macOS/Windows**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
    -   **Linux (Ubuntu)**: Install Docker Engine and Docker Compose plugin:
        ```bash
        sudo apt-get update && sudo apt-get install docker.io docker-compose-plugin
        # Add your user to the docker group to run docker commands without sudo
        sudo usermod -aG docker $USER
        # You will need to log out and log back in for the group change to take effect.
        ```

### Backend Setup (Python)

1.  **Clone the Repository**: Obtain the project code.
2.  **Install Dependencies**: No external Python package dependencies are required beyond the standard library. Therefore, a `requirements.txt` file is not used.
3.  **Run the Server**: Execute the backend server script:
    ```bash
    python server.py --port 8000
    ```
    -   **Optional Flags**: You can specify the host and port: `--host 0.0.0.0 --port 8000`.
    -   Upon the first run, the server will automatically create the necessary data directories (`data/` and `data/uploads/`).

### Frontend Setup (JavaScript/Vue)

1.  **Navigate to the Frontend Directory**: Change your current directory to `web/`.
    ```bash
    cd web/
    ```
2.  **Install Dependencies**: Install all necessary Node.js packages using npm:
    ```bash
    npm install
    ```
3.  **Run Development Server**: Start the Vite development server for live reloading and debugging:
    ```bash
    npm run dev
    ```
    -   The application will typically be accessible at `http://localhost:5173` (Vite's default).
    -   The `vite.config.js` is pre-configured to automatically proxy API requests made to `/api` to the backend server at `http://localhost:8000`.
4.  **Build for Production**: Generate optimized static assets for deployment:
    ```bash
    npm run build
    ```
    -   The build output will be placed in the `web/dist/` directory.

### Containerized Setup (Docker Compose)

This is the recommended method for running the application, ensuring consistency across environments.

1.  **Ensure Docker and Docker Compose are Installed**: Refer to the prerequisites section above.
2.  **Build and Run Services**: Start both the backend and frontend services using Docker Compose:
    ```bash
    docker-compose up --build -d
    ```
    -   The backend service will be accessible (internally) and the frontend will be served. The frontend's Nginx will proxy API calls to the backend.
    -   Access the application via `http://localhost:8000` (or the port mapped in `docker-compose.yml` for the frontend service, typically port 80 mapped to host port 8000 for simplicity in this setup).
    -   The `data/` directory will be persisted using a named volume defined in `docker-compose.yml`, ensuring data is not lost between container restarts.

---

## Future Considerations

The current architecture provides a solid foundation. Potential areas for future enhancement include:

-   **Scalability Enhancement**: Migrate from local file-based storage (`data/`) to scalable object storage solutions like AWS S3, Google Cloud Storage, or a self-hosted MinIO instance. This would improve resilience and horizontal scaling capabilities.
-   **Authentication and Authorization**: Implement robust security measures by integrating authentication mechanisms, such as JSON Web Tokens (JWT) or OAuth 2.0, to protect API endpoints.
-   **Automated Testing**: Expand test coverage by introducing comprehensive unit and integration test suites using frameworks like `pytest` for the backend and `Vitest` or `Jest` for the frontend.
-   **Observability**: Integrate structured logging (e.g., using `structlog`) and monitoring tools (e.g., Prometheus with Grafana) to gain better insights into application performance and behavior.
-   **OpenAPI Specification**: Further refine the `docs/openapi.yaml` file by adding detailed request/response schemas, example payloads, and security scheme definitions to enhance API discoverability and client generation.

---

*Last updated based on repository state (2025-04-05).*
