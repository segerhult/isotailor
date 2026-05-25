# Environment

This document outlines the setup required to run the application, including environment variables and dependencies.

## Runtime

- `OPENAI_API_KEY`: API key used for OpenAI-compatible providers. Use your OpenRouter key when `AI_BASE_URL` is set to `https://openrouter.ai/api/v1`.
- `AI_MODEL`: Model name to use (example: `google/gemma-3-12b-it`).
- `AI_BASE_URL`: The base URL for the OpenAI-compatible API (OpenRouter: `https://openrouter.ai/api/v1`).
- `AI_PROVIDER`: (Optional) The AI provider to use (`openai`, `gemini`, or `ollama`). Defaults to `openai`.
- `ORCHESTRA_ROLE_ROUTING`: `auto` (default) or `prefer` (use plugin preferred role/persona).
- `ORCHESTRA_DOCS_PR`: Set to `1` to enable automatic draft documentation pull request creation in pull request workflows.
- `ORCHESTRA_APP_NAME` / `ORCHESTRA_APP_URL`: Used to identify requests. Required for OpenRouter headers.
- `ORCHESTRA_SOURCE`: A string appended to the system prompt (example: `ci:github-actions`).
- `ORCHESTRA_DEBUG`: Set to `1` to enable verbose AI error logging.
- `VCS_PROVIDER`: `github`, `gitlab`, or `azure`. Auto-detected in CI if not set.
- `GITHUB_TOKEN`: Required for GitHub pull request comments and creation.
- `GITHUB_OWNER` / `GITHUB_REPO`: Optional. Inferred from `GITHUB_REPOSITORY` in GitHub Actions.

## Running the application

The application's backend and frontend are containerized using Docker. The backend is built from `Dockerfile` and the frontend from `web/Dockerfile`. Refer to the [Docker Compose documentation](docker-compose.yml) for configuration details.

### Backend

The backend is built using Python 3.11. Dependencies are managed within the container.

### Frontend

The frontend is a Vue.js application built using Vite. Navigate to the `web` directory to view relevant files:

- `web/nginx.conf`: Nginx configuration file for serving the frontend.
- `web/src/api.js`: JavaScript file containing API calls.
- `web/vite.config.js`: Vite configuration file for development and build process.

## CI/CD

- Document secrets and environment variables required by CI pipelines.

## AI (Optional)

- If this repository uses AI tooling in CI, document required keys and providers here.
