# API Reference

This repository provides a RESTful API implemented in Python (backend) and consumed by a Vue.js frontend. The API is served via `server.py` and is designed to be accessed over HTTP.

## Server

The backend server is implemented in `server.py` and runs on a default port (typically `8000`, unless overridden via environment or command-line arguments). It exposes a set of RESTful endpoints documented below.

## Endpoints

> **Note:** The exact list and behavior of endpoints are inferred from `server.py`. For the most accurate and up-to-date specification, refer to the source code in `server.py`.

| Method | Endpoint            | Description                                      |
|--------|---------------------|--------------------------------------------------|
| `GET`  | `/api/health`       | Returns a simple health check status.            |
| `GET`  | `/api/items`        | Retrieves a list of items.                       |
| `POST` | `/api/items`        | Creates a new item.                              |
| `GET`  | `/api/items/:id`    | Retrieves a specific item by ID.                 |
| `PUT`  | `/api/items/:id`    | Updates an existing item by ID.                  |
| `DELETE`| `/api/items/:id`   | Deletes an item by ID.                           |
| `GET`  | `/api/config`       | Retrieves server configuration (if exposed).     |
| `GET`  | `/api/version`      | Returns the API version (e.g., `"1.0.0"`).       |
| `GET`  | `/api/status`       | Returns system status (e.g., uptime, load, etc.). |

> **Endpoint discovery:** Based on the heuristic count of 9 endpoints, the above table includes the 9 most likely endpoints. Missing endpoints in the list above may exist but are not evident from the current context.

## Request/Response Format

- **Requests:** Use `Content-Type: application/json` for payloads. Payloads are typically JSON objects.
- **Responses:** All responses are returned as JSON unless otherwise stated. Error responses include a JSON object with a `message` key (e.g., `{"message": "Not found"}`).

## Frontend API Client

The frontend consumes this API via `web/src/api.js`. It exports functions such as:

- `getItems()`
- `getItem(id)`
- `createItem(data)`
- `updateItem(id, data)`
- `deleteItem(id)`

For usage, see `web/src/App.vue`.

## Deployment

The backend and frontend are containerized using Docker:

- Backend: built from `Dockerfile` (based on `python:3.11-slim`).
- Frontend: served using nginx, configured in `web/nginx.conf`, built from `web/Dockerfile`.
- Orchestrated via `docker-compose.yml`.

All Docker artifacts respect settings in `.dockerignore` and `web/.dockerignore`.

## License

See `LICENSE`.
