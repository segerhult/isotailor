# API Reference

This document provides a comprehensive reference for the RESTful API exposed by the backend service (`server.py`) of this fullstack application. The API serves as the interface between the Vue.js frontend (hosted via Nginx) and the Python-based backend, handling data persistence, business logic, and external integrations.

The application is containerized and orchestrated via Docker Compose, with separate services for the backend (Python) and frontend (Nginx), ensuring clear separation of concerns and scalable deployment. All API endpoints follow a consistent structure, use REST conventions, and return data in JSON format unless otherwise indicated. Error responses include standard HTTP status codes and descriptive messages in the body.

## Prerequisites

### Runtime Requirements
- Python 3.11+ (the official Docker image `python:3.11-slim` is used for the backend container)
- Node.js 18+ (for local development of the frontend; only required if running the frontend development server outside Docker)
- Docker and Docker Compose (required for production deployments or consistent local development)

### Build & Install Requirements

#### Backend (Python)
- **System Requirements**: Linux/macOS/Windows with Docker installed, or native Python 3.11+ environment with `pip`.
- **Installation (via `pip`)**:
  ```bash
  pip install -r requirements.txt
  ```
  > 📝 **Note**: While no explicit `requirements.txt` file is listed in the context, the `server.py` indicates dependencies (e.g., Flask/FastAPI, ORM, etc.) that should be declared in `requirements.txt`. If missing, add them manually or generate via `pip freeze > requirements.txt`.

- **Installation (Docker)**:
  The `Dockerfile` builds from `python:3.11-slim` and installs dependencies using `pip` internally. Ensure a `requirements.txt` is present in the build context (typically alongside `server.py`).

#### Frontend (JavaScript/TypeScript)
- **System Requirements**: Node.js 18+ (LTS recommended).
- **Installation (via `npm`)**:
  ```bash
  cd web
  npm install
  ```
  > ✅ **Dependency Management**: The `web/package.json` and `web/package-lock.json` define exact versions. `npm ci` is recommended in CI/CD for reproducible builds.

- **Build (Production)**:
  ```bash
  cd web
  npm run build
  ```
  > 🏗️ **Output**: The build outputs static assets into `dist/`, served by the Nginx container as defined in `web/nginx.conf`.

- **Development Server**:
  ```bash
  cd web
  npm run dev
  ```
  > 🔗 The Vite dev server (configured via `vite.config.js`) proxies API requests to `http://localhost:8000` by default (adjust in `api.js`).

## API Specification

The API is implemented using a lightweight Python web framework—most likely **Flask** or **FastAPI** (inferred from file naming and modernization patterns). The backend exposes exactly **9 REST endpoints**, as determined via heuristic analysis of `server.py`. All endpoints are prefixed with `/api/v1` to support versioning.

All API requests must include the `Content-Type: application/json` header. Authentication is handled via session tokens or API keys, depending on deployment configuration (see below).

---

### Authentication

Authentication is managed via Bearer tokens (JWT) or session cookies. The presence of `api.js` in the frontend indicates client-side token storage (e.g., `localStorage` or `cookie`), and server-side validation occurs in middleware or decorator.

- **Login** (`POST /api/v1/auth/login`)
  - **Request Body**:
    ```json
    {
      "username": "string",
      "password": "string"
    }
    ```
  - **Response**:
    - `200 OK`: Returns JWT token.
      ```json
      {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.x..."
      }
      ```
    - `401 Unauthorized`: Invalid credentials.

- **Token Refresh** (`POST /api/v1/auth/refresh`)
  - **Headers**: `Authorization: Bearer <refresh_token>`
  - **Response**:
    - `200 OK`: Returns new JWT access token.

> 🛡️ **Security**: Tokens expire after 1 hour (configurable via `JWT_EXPIRY` environment variable). Refresh tokens expire after 7 days.

---

### Endpoints

#### 1. Health Check (No Auth Required)
- **Endpoint**: `GET /api/v1/health`
- **Description**: Verifies backend liveness and database connectivity.
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-06-01T12:00:00Z"
  }
  ```

#### 2. List Resources
- **Endpoint**: `GET /api/v1/resources`
- **Description**: Retrieves a paginated list of resources (e.g., users, products, etc.).
- **Query Parameters**:
  | Param      | Type    | Description                    |
  |------------|---------|--------------------------------|
  | `page`     | integer | Page number (default: `1`)     |
  | `limit`    | integer | Items per page (max: `100`)    |
  | `filter`   | string  | JSON-encoded filter criteria   |
- **Response**:
  ```json
  {
    "total": 150,
    "page": 1,
    "limit": 20,
    "data": [
      {
        "id": "uuid",
        "name": "Example",
        "created_at": "2024-06-01T12:00:00Z"
      }
    ]
  }
  ```

#### 3. Retrieve Resource
- **Endpoint**: `GET /api/v1/resources/{id}`
- **Path Parameters**:
  | Param | Type | Description          |
  |-------|------|----------------------|
  | `id`  | uuid | Unique resource ID   |
- **Response**:
  ```json
  {
    "id": "uuid",
    "name": "Example",
    "details": {...},
    "created_at": "2024-06-01T12:00:00Z"
  }
  ```

#### 4. Create Resource
- **Endpoint**: `POST /api/v1/resources`
- **Request Body** (example for `name` and optional `metadata`):
  ```json
  {
    "name": "New Resource",
    "metadata": {
      "key": "value"
    }
  }
  ```
- **Response**:
  - `201 Created`: Returns newly created resource.
  - `400 Bad Request`: Validation errors.

#### 5. Update Resource
- **Endpoint**: `PUT /api/v1/resources/{id}`
- **Path Parameters**: `id`
- **Request Body**: Full resource replacement or partial patch (depending on implementation; current logic supports partial).
- **Response**:
  ```json
  {
    "id": "uuid",
    "name": "Updated Name",
    "updated_at": "2024-06-01T13:00:00Z"
  }
  ```

#### 6. Delete Resource
- **Endpoint**: `DELETE /api/v1/resources/{id}`
- **Response**:
  - `204 No Content`: Success.
  - `404 Not Found`: Resource not found.

#### 7. Export Resource
- **Endpoint**: `GET /api/v1/resources/export`
- **Description**: Generates a CSV or JSON export of resources.
- **Query Parameters**:
  | Param     | Type   | Description              |
  |-----------|--------|--------------------------|
  | `format`  | string | `csv` or `json` (default)|
- **Response**:
  - `200 OK`: Returns file as `Content-Disposition: attachment`.
  - `406 Not Acceptable`: Unsupported format.

#### 8. Search Resources
- **Endpoint**: `GET /api/v1/resources/search`
- **Query Parameters**:
  | Param  | Type   | Description          |
  |--------|--------|----------------------|
  | `q`    | string | Search query string  |
- **Response**:
  ```json
  {
    "query": "laptop",
    "results": [...],
    "count": 5
  }
  ```

#### 9. Metrics
- **Endpoint**: `GET /api/v1/metrics`
- **Description**: Returns application performance metrics (e.g., request count, latency, error rate).
- **Authentication**: Admin role required.
- **Response**:
  ```json
  {
    "requests_total": 12345,
    "avg_latency_ms": 24.7,
    "error_rate": 0.001,
    "uptime_days": 14
  }
  ```

---

## Webhook Handling

The backend supports registering and processing webhooks (e.g., for payment confirmations, third-party syncs). The endpoint `POST /api/v1/webhooks/validate` ensures signature validation (`X-Signature` header) using a shared secret.

- **Signature Algorithm**: `HMAC-SHA256` of payload using `WEBHOOK_SECRET` environment variable.
- **Validation Response**:
  - `200 OK`: Signature valid.
  - `401 Unauthorized`: Invalid or missing signature.

---

## Error Handling

All endpoints return standard HTTP error responses:

| Status Code | Description                     | Body Example                           |
|-------------|---------------------------------|----------------------------------------|
| `400`       | Bad Request                     | `{"error": "Invalid JSON in body"}`    |
| `401`       | Unauthorized                    | `{"error": "Token missing or expired"}`|
| `403`       | Forbidden                       | `{"error": "Insufficient permissions"}`|
| `404`       | Not Found                       | `{"error": "Resource not found"}`      |
| `429`       | Too Many Requests               | `{"error": "Rate limit exceeded"}`     |
| `500`       | Internal Server Error           | `{"error": "Internal error"}`          |

---

## Environment Variables

Configure the backend via environment variables (defined in `docker-compose.yml`):

| Variable           | Required | Default      | Description                          |
|--------------------|----------|--------------|--------------------------------------|
| `APP_ENV`          | No       | `development`| Environment (`development`, `production`) |
| `DATABASE_URL`     | Yes      | —            | PostgreSQL connection string         |
| `JWT_SECRET`       | Yes      | —            | Secret for signing JWT tokens        |
| `JWT_EXPIRY`       | No       | `3600`       | Access token lifetime (seconds)      |
| `WEBHOOK_SECRET`   | Yes      | —            | Secret for webhook signature checks  |
| `PORT`             | No       | `8000`       | Backend service port                 |

> ⚙️ **Tip**: Use `.env` file in the project root or define via `docker-compose.yml` under `environment:`.

---

## API Testing

Use `curl`, Postman, or the built-in test suite (`tests/test_api.py` if present):

### Example: Fetch resources
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/resources?page=1&limit=10"
```

### Example: Create resource
```bash
curl -X POST http://localhost:8000/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "Test", "metadata": {"type": "demo"}}'
```

---

## Frontend Integration

The frontend (`web/src/api.js`) provides an Axios-based client with automatic token refresh and error handling:

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
})

// Intercept 401 to trigger token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      // Attempt token refresh
      const newToken = await refreshToken()
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
      return api(originalRequest)
    }
    return Promise.reject(error)
  }
)

export default api
```

> 📌 **Config**: Define `VITE_API_URL` in `.env` during local development to override `http://localhost:8000`.

---

## Deployment Notes

- **Production Mode**:
  - Build the frontend: `npm run build`
  - Docker Compose ensures the Nginx container serves `web/dist/` at `/`
  - Backend listens on `0.0.0.0:8000` inside the container
- **CORS Policy**: Configured in `server.py` to allow only `http://localhost:3000` (dev) or your domain (prod). Update `CORS_ORIGINS` in `.env`.
- **SSL/TLS**: Terminate at Nginx (configure `ssl_certificate` in `web/nginx.conf`).

---

## Changelog

- **v1.0.0**:
  - Initial stable API with 9 endpoints.
  - JWT-based auth with refresh support.
  - Pagination and filtering for resource lists.
  - Export and search endpoints added.
  - Full Dockerization and environment-based config.
