# Local Development Setup

This guide outlines the necessary steps to set up the environment for local development.

## Prerequisites

*   **Docker:** Ensure Docker is installed and running on your system.
*   **Node.js:** Required for the web frontend.  Versions managed by `package-lock.json` and `package.json` in the `/web` directory.
*   **Python 3.11:** The backend is built on Python 3.11.

## Environment Variables

The following environment variables are used by the application:

*   `OPENAI_API_KEY`: Your OpenAI API key.
*   `AI_BASE_URL`: The base URL for your AI service.  Example for OpenRouter: `https://openrouter.ai/api/v1`.
*   `AI_MODEL`: The AI model to use (e.g., "gpt-3.5-turbo").
*   `GITHUB_TOKEN`: (Optional) A GitHub token for pull request integrations.  Required only if you are working with PR integrations.

## Building and Running the Application

The application consists of a backend server and a Vue.js frontend.  These are containerized using Docker.

1.  **Backend:** The backend server (server.py) is built using a Python 3.11 slim image and configured in the `Dockerfile`.  The Docker image is built as part of the CI/CD process.

2.  **Frontend:**  The Vue.js frontend is built using Vite and packaged as a Docker image. The `Dockerfile` and configuration file `vite.config.js` in the `/web` directory define the build process.  The Nginx configuration file (`web/nginx.conf`) serves the built frontend. The frontend's `package.json` and `package-lock.json` specify dependencies.

## Development Workflow

To run the application locally:

1.  Set the required environment variables as described above.

2.  Navigate to the root directory of the repository.

3. Ensure Docker is running, then execute: `docker compose up --build` (if a docker-compose.yml file were present). As there isn't one, you'll need to manually build and run the backend and frontend containers.

    *   **Build Backend:** `docker build -t my-backend .`
    *   **Run Backend:** `docker run -p 8000:8000 my-backend`

    *   **Build Frontend:**  Navigate to the `/web` directory and run `docker build -t my-frontend .`
    *   **Run Frontend:** `docker run -p 80:80 my-frontend`

    *Note:* These commands assume you want to map port 8000 for the backend and port 80 for the frontend.  Adjust as needed. The docker images are created using the Dockerfiles specified in the repository's root directory and the `/web` directory respectively.

## API Documentation

Refer to the API documentation for details on the available endpoints and their usage: [doc/openapi.md](doc/openapi.md)
