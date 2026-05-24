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

The application consists of a backend server and a Vue.js frontend, both containerized using Docker.  Refer to the `docker-compose.yml` file for instructions.

## API Documentation

Refer to the API documentation for details on the available endpoints and their usage.
