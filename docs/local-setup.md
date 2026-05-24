# Local Setup

This guide outlines the necessary steps to set up the environment for local development.

## Prerequisites

*   **Docker:** Ensure Docker is installed and running on your system.
*   **Node.js:** Required for the web frontend. Versions are managed by `package-lock.json` and `package.json` in the `/web` directory.
*   **Python 3.11:** The backend is built on Python 3.11.

## Environment Variables

The following environment variables are used by the application:

*   `OPENAI_API_KEY`: Your OpenAI API key.
*   `AI_BASE_URL`: The base URL for your AI service. Example for OpenRouter: `https://openrouter.ai/api/v1`.
*   `AI_MODEL`: The AI model to use (e.g., "gpt-3.5-turbo").
*   `GITHUB_TOKEN`: (Optional) A GitHub token for pull request integrations. Required only if you are working with PR integrations.

## Building and Running the Application

The application consists of a backend server and a Vue.js frontend, both containerized using Docker. Refer to the `docker-compose.yml` file for instructions.

## Docker Configuration

The application utilizes Docker and Docker Compose for local development.  Specific configurations are detailed in the following files:

*   `.dockerignore`: Specifies files and directories to exclude from Docker image creation.
*   `Dockerfile`: Defines how to build the Python backend image.
*   `web/.dockerignore`: Specifies files and directories to exclude from the web frontend Docker image creation.
*   `web/Dockerfile`: Defines how to build the Vue.js frontend image.
*   `docker-compose.yml`: Defines the services and network configuration for the application.
*   `web/nginx.conf`: Nginx configuration for the web frontend.

## Code Structure

*   `server.py`: Contains the Python backend server code.
*   `web/`: Contains the Vue.js frontend code.
    *   `web/index.html`: The main HTML entry point for the frontend.
    *   `web/src/App.vue`: The main Vue component.
    *   `web/src/api.js`: Contains functions for interacting with the backend API.
    *   `web/src/main.js`: The entry point for the Vue.js application.
    *   `web/vite.config.js`: Configuration for Vite, the frontend build tool.
