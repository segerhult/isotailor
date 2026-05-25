# Environment Variables

This document describes required environment variables for running and testing the application, as well as those used in CI/CD.

## Runtime

The backend (`server.py`) uses the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | No | Port on which the backend server listens. Defaults to `8000` if not set. |

The frontend (Vue.js + Vite) uses the following environment variables during build and runtime:

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | No | Base URL for the backend API. If not set, defaults to the same origin (e.g., `http://localhost:8000` in dev). Used by `src/api.js`. |

> 💡 To override `VITE_API_BASE_URL` at runtime in production, set `VITE_API_BASE_URL` in the environment where the static site is served (e.g., via reverse proxy or deployment platform config). Vite injects these values at build time.

## CI/CD

The CI pipeline (`.github/workflows/main.yml`) does not require any secrets or environment variables beyond those provided by GitHub Actions by default (e.g., `GITHUB_TOKEN`). No custom secrets are referenced in the workflow or Docker configurations.
