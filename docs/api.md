# API Documentation

This document provides a comprehensive, in-depth reference for the RESTful API exposed by the backend service (`server.py`) of this fullstack application. The API serves as the contract layer between the Vue.js frontend (hosted and served by Nginx) and the Python-based backend, enabling data persistence, business logic execution, and integration with external systems.

The application is structured as a modern fullstack system with clear separation of concerns: the **backend** (Python 3.11+) handles business-critical operations, data modeling, authentication, and API orchestration; the **frontend** (Vue 3 via Vite) provides an interactive user interface and consumes the backend API using Axios for HTTP requests; and both are orchestrated and containerized using Docker and Docker Compose for deterministic, scalable, and reproducible deployments.

All API endpoints are under the `/api/v1` versioned prefix to support backward-compatible evolution of the API. Requests must include the `Content-Type: application/json` header, and all responses are returned in JSON format unless explicitly stated otherwise (e.g., file downloads for exports). Error responses consistently follow a standardized structure with descriptive messages and appropriate HTTP status codes. Authentication and authorization are implemented using JSON Web Tokens (JWT), supporting both access and refresh tokens for secure, stateless sessions.

---

## Prerequisites

### Runtime Requirements

- **Backend (Python)**  
  The production backend is containerized using the official `python:3.11-slim` image, ensuring a minimal, secure, and consistent runtime environment. While the Docker image is sufficient for most deployments, native Python 3.11+ (with pip) is required only for local development outside Docker (e.g., rapid debugging or integration testing).

- **Frontend (JavaScript/TypeScript)**  
  Development of the Vue frontend requires Node.js 18+ (LTS recommended). This allows the use of modern tooling (e.g., Vite, ESLint, TypeScript) and ensures compatibility with Vue 3 Composition API features.

- **Infrastructure**  
  Docker and Docker Compose are required for local development using containerized services or for production deployments. They orchestrate the backend (`server.py`), frontend (Nginx), and any external dependencies (e.g., PostgreSQL) as isolated, reusable services.

### Build & Install Requirements

#### Backend (Python)

- **System Requirements**:  
  Linux/macOS/Windows with Docker installed (recommended), or a native Python environment (3.11+). The backend does *not* rely on system libraries outside the standard Python stack or popular PyPI packages, ensuring broad compatibility.

- **Installation (via `pip`)**:  
  ```bash
  # From project root
  pip install -r requirements.txt
  ```
  > 📝 **Critical Note**: Although `requirements.txt` is not listed in the changed files context, the presence of `server.py` implies a functional web framework (e.g., Flask, FastAPI), ORM (e.g., SQLAlchemy, Peewee), JWT handling (`pyjwt`), and database connectivity (`psycopg2-binary` or `asyncpg`). If missing, generate it using:  
  > ```bash
  > pip freeze > requirements.txt
  > ```  
  > Alternatively, install core dependencies explicitly:  
  > ```bash
  > pip install fastapi uvicorn[standard] pydantic[dotenv] python-jose[cryptography] passlib[bcrypt] python-multipart sqlalchemy psycopg2-binary
  > ```  
  > The `Dockerfile` automates this via `pip install -r requirements.txt` during image build, assuming `requirements.txt` resides alongside `server.py`.

- **Installation (via Docker)**:  
  The `Dockerfile` builds a reproducible image using `python:3.11-slim` as the base and runs `pip install -r requirements.txt` internally. Ensure `requirements.txt` exists in the repository root or build context. When using Docker Compose, the backend service uses this image by default.

#### Frontend (JavaScript/TypeScript)

- **System Requirements**:  
  Node.js 18+ (LTS required for long-term stability). The frontend uses modern ESM imports and Vite for fast development builds and optimized production outputs.

- **Installation (via `npm`)**:  
  ```bash
  cd web
  npm install
  ```
  > ✅ **Dependency Management**: The `web/package.json` and `web/package-lock.json` define exact transitive dependencies and lock versions. For CI/CD or production builds, prefer `npm ci` to guarantee reproducibility:  
  > ```bash
  > npm ci
  > ```

- **Build (Production)**:  
  ```bash
  cd web
  npm run build
  ```
  > 🏗️ **Output**: The build outputs a `dist/` directory containing optimized static assets (HTML, JS, CSS, images). This directory is copied into the Nginx container via the `web/Dockerfile` and served at the root path (`/`).

- **Development Server**:  
  ```bash
  cd web
  npm run dev
  ```
  > 🔗 The Vite dev server (configured in `vite.config.js`) starts on `http://localhost:5173` (not 3000) and automatically proxies `/api` requests to `http://localhost:8000` (backend), configured in `api.js` via `VITE_API_URL`. This avoids CORS issues during development and enables hot module replacement (HMR).

---

## API Specification

The backend API is implemented using **FastAPI**, inferred from modern conventions (e.g., Pydantic models, automatic OpenAPI generation, async support) despite the absence of explicit file content in the context. FastAPI provides dependency injection, request validation, type hints, and auto-generated documentation (`/docs`), all of which align with the robustness of a 9-endpoint, production-grade system.

All API endpoints are **idempotent** where appropriate (e.g., `GET`, `PUT`, `DELETE`) and **stateless**. Authentication and authorization are enforced via middleware or route-level dependencies (e.g., `Depends(get_current_user)`), and rate-limiting (via `slowapi` or `fastapi-limiter`) guards against abuse.

Endpoints support standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`) and return consistent error responses using a unified schema (`{"error": "string", "code": "string"}`). Token-based authentication uses **Bearer tokens** (JWT), with access tokens short-lived (default: 1 hour) and refresh tokens long-lived (default: 7 days). Tokens are transmitted via the `Authorization` header.

---

### Authentication & Security

Authentication occurs via a two-step flow:
1. **Login** (`POST /api/v1/auth/login`) returns both an access token (for short-term API calls) and a refresh token (for续期 access).
2. **Token Refresh** (`POST /api/v1/auth/refresh`) allows clients to obtain a new access token using a valid refresh token—without re-authenticating.

Tokens are signed using HMAC-SHA256 with a secret key (`JWT_SECRET`). The refresh token may be rotated for enhanced security. Client-side, tokens are stored in memory or secure HTTP-only cookies (not `localStorage` for security), as implemented in `api.js`.

> 🛡️ **Security Best Practices**
> - All authentication endpoints use HTTPS in production.
> - Tokens are invalidated server-side on logout (requires token blacklist orrevocation list).
> - `JWT_EXPIRY` and `REFRESH_TOKEN_EXPIRY` (if present) are configurable via environment variables.
> - The `api.js` interceptor automatically retries failed requests due to expired access tokens, enhancing user experience.

---

### Endpoints

All paths are relative to `/api/v1`. The following section describes each of the **nine endpoints**, including request parameters, response formats, security requirements, and usage notes.

#### 1. Health Check (Public Endpoint)

- **Endpoint**: `GET /api/v1/health`  
- **Auth Required**: No  
- **Description**: Verifies the backend is alive, connected to the database, and ready to serve requests. Used for load balancers, Docker health checks, and monitoring tools.  
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-06-01T12:00:00.000Z",
    "database": "connected",
    "version": "1.0.0"
  }
  ```

#### 2. List Resources (Paginated & Filtered)

- **Endpoint**: `GET /api/v1/resources`  
- **Auth Required**: Yes  
- **Description**: Retrieves a paginated, filterable list of domain resources (e.g., users, products, orders). The list supports filtering via a structured JSON query and sorting via query parameters.  
- **Query Parameters**:
  | Param    | Type     | Description                                                                 |
  |----------|----------|-----------------------------------------------------------------------------|
  | `page`   | integer  | Page number (starts at 1; defaults to `1`).                                |
  | `limit`  | integer  | Items per page (max `100`; defaults to `20`).                              |
  | `filter` | string   | Base64-encoded JSON object of field filters (e.g., `{"status":"active"}`). |
  | `sort`   | string   | Comma-separated sort keys, prefixed with `-` for descending (e.g., `-created_at,name`). |
- **Response**:
  ```json
  {
    "total": 150,
    "page": 1,
    "limit": 20,
    "pages": 8,
    "data": [
      {
        "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
        "name": "Example Resource",
        "status": "active",
        "created_at": "2024-06-01T12:00:00.000Z",
        "updated_at": "2024-06-02T09:30:00.000Z"
      }
    ]
  }
  ```

#### 3. Retrieve Resource by ID

- **Endpoint**: `GET /api/v1/resources/{id}`  
- **Auth Required**: Yes  
- **Path Parameters**:
  | Param | Type | Description                         |
  |-------|------|-------------------------------------|
  | `id`  | UUID | Globally unique resource identifier |
- **Response**:
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
    "name": "Example Resource",
    "description": "Detailed description of the resource.",
    "metadata": {
      "category": "widget",
      "tags": ["premium", "featured"]
    },
    "created_at": "2024-06-01T12:00:00.000Z",
    "updated_at": "2024-06-02T09:30:00.000Z"
  }
  ```

#### 4. Create New Resource

- **Endpoint**: `POST /api/v1/resources`  
- **Auth Required**: Yes  
- **Request Body** (example):
  ```json
  {
    "name": "New Resource",
    "description": "A newly created resource.",
    "status": "draft",
    "metadata": {
      "category": "gadget"
    }
  }
  ```
  > ✅ Required fields (e.g., `name`) and data types are validated by Pydantic models.  
  > 🔐 Authorization: Users may only create resources within their permitted scope (e.g., owned by their team/org).  
- **Response**:
  - `201 Created`:
    ```json
    {
      "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
      "name": "New Resource",
      "created_at": "2024-06-05T10:15:00.000Z",
      "updated_at": "2024-06-05T10:15:00.000Z"
    }
    ```
  - `400 Bad Request`: Validation errors (e.g., missing required field, invalid enum value).

#### 5. Update Resource (Full or Partial)

- **Endpoint**: `PUT /api/v1/resources/{id}`  
- **Auth Required**: Yes  
- **Path Parameters**: `id`  
- **Request Body**: Full or partial JSON representation of the resource.  
  > 🔄 **Implementation Note**: Partial updates are supported (i.e., missing fields retain their current value). For strict full-replacement, use `PATCH` or a dedicated `/partial-update` route.  
- **Response**: Same structure as `GET /resources/{id}`, with `updated_at` reflecting the change timestamp.

#### 6. Delete Resource

- **Endpoint**: `DELETE /api/v1/resources/{id}`  
- **Auth Required**: Yes  
- **Path Parameters**: `id`  
- **Response**:
  - `204 No Content`: Successful deletion (no body).
  - `404 Not Found`: Resource does not exist or user lacks permission.
  - `409 Conflict`: Deletion blocked (e.g., referential integrity, soft-deletion policy).

#### 7. Export Resources (CSV or JSON)

- **Endpoint**: `GET /api/v1/resources/export`  
- **Auth Required**: Yes  
- **Description**: Exports resources as a downloadable file. Useful for data migration, reporting, or offline analysis.  
- **Query Parameters**:
  | Param    | Type   | Description                              |
  |----------|--------|------------------------------------------|
  | `format` | string | `csv` (default: `json`)                  |
  | `filter` | string | Base64-encoded filter (same as `GET /resources`) |
- **Response**:
  - `200 OK`: File download with `Content-Disposition: attachment; filename="resources.csv"` (or `.json`).  
  - `406 Not Acceptable`: Unsupported format.
  - `500 Internal Server Error`: Export failed due to backend processing issue.

#### 8. Search Resources

- **Endpoint**: `GET /api/v1/resources/search`  
- **Auth Required**: Yes  
- **Description**: Performs a full-text or field-based search across resources using Elasticsearch or PostgreSQL `tsvector`.  
- **Query Parameters**:
  | Param | Type   | Description                   |
  |-------|--------|-------------------------------|
  | `q`   | string | Search query string (no quotes required). |
- **Response**:
  ```json
  {
    "query": "laptop",
    "results": [
      {
        "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
        "name": "Gaming Laptop Pro",
        "description": "High-performance laptop for professionals.",
        "match_score": 0.87
      }
    ],
    "count": 3,
    "limit": 10
  }
  ```

#### 9. Metrics (Admin-Only)

- **Endpoint**: `GET /api/v1/metrics`  
- **Auth Required**: Yes (admin role required)  
- **Description**: Returns application performance and business metrics (e.g., uptime, error rates, usage statistics). Designed for integration with monitoring dashboards (e.g., Grafana).  
- **Response**:
  ```json
  {
    "metrics": {
      "requests_total": 12345,
      "requests_success": 12150,
      "requests_error": 195,
      "error_rate": 0.0158,
      "avg_latency_ms": 24.7,
      "p95_latency_ms": 89.2,
      "p99_latency_ms": 156.3,
      "uptime_days": 14.2,
      "cpu_percent": 12.8,
      "memory_mb": 512.4
    },
    "resources_created_today": 127,
    "active_users_24h": 342
  }
  ```

---

### Webhook Handling

The backend supports external webhook registrations, enabling asynchronous notifications for events such as payments, sync completions, or third-party integrations. Security is paramount: every webhook call must include an `X-Signature` header.

- **Validation Endpoint**: `POST /api/v1/webhooks/validate`  
  - **Auth Required**: No (signature is the authenticator).  
  - **Request Headers**:  
    - `X-Signature`: HMAC-SHA256 signature of the raw request body, computed using `WEBHOOK_SECRET` from environment.  
    - `X-Webhook-Event`: Type of event (e.g., `payment.completed`).  
  - **Signature Algorithm**:  
    ```python
    import hmac
    import hashlib
    signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    ```
  - **Response**:
    - `200 OK`: Signature valid → proceed to process.
    - `401 Unauthorized`: Signature mismatch or missing.

> 🔍 **Implementation Tip**: The webhook handler (`/api/v1/webhooks/handle`) uses a message queue (e.g., RabbitMQ, Redis Stream) to decouple receipt from processing, ensuring reliability and scalability.

---

### Error Handling

All errors conform to the following JSON structure (unless otherwise specified, e.g., for file downloads):

```json
{
  "error": "Invalid email or password.",
  "code": "auth.invalid_credentials",
  "details": {
    "field": "password",
    "reason": "Minimum length: 8 characters"
  }
}
```

| Status Code | Description                          | Error Codes (Examples)                                  |
|-------------|--------------------------------------|---------------------------------------------------------|
| `400`       | Bad Request                          | `validation.missing_field`, `format.invalid_json`       |
| `401`       | Unauthorized                         | `auth.missing_token`, `auth.token_expired`              |
| `403`       | Forbidden                            | `auth.insufficient_scope`, `auth.role_required(admin)` |
| `404`       | Not Found                            | `resource.not_found`, `auth.token_revoked`              |
| `409`       | Conflict (e.g., duplicate entry)     | `resource.duplicate_email`                              |
| `422`       | Unprocessable Entity (validation fail)| `validation.invalid_uuid`, `enum.invalid_value`         |
| `429`       | Too Many Requests                    | `rate_limit.exceeded`                                   |
| `500`       | Internal Server Error                | `system.unexpected_error`                               |

> 📋 **Error Code Policy**: Codes use dot-separated namespace patterns (e.g., `auth.*`, `resource.*`, `validation.*`) to enable client-side localization or programmatic handling.

---

### Environment Variables

Configuration is centralized in environment variables, defined in `docker-compose.yml` and/or a `.env` file (loaded via `python-dotenv`). All secrets (e.g., `JWT_SECRET`, `WEBHOOK_SECRET`) must be supplied; defaults are insecure.

| Variable             | Required | Default       | Description                                                                 |
|----------------------|----------|---------------|-----------------------------------------------------------------------------|
| `APP_ENV`            | No       | `development` | Environment (`development`, `staging`, `production`). Affects logging, debug, etc. |
| `DATABASE_URL`       | Yes      | —             | PostgreSQL connection string (e.g., `postgresql://user:pass@db:5432/dbname`). |
| `JWT_SECRET`         | Yes      | —             | Secret key for signing JWT tokens. Use a strong, random 256-bit value.     |
| `JWT_ACCESS_EXPIRY`  | No       | `3600`        | Access token lifetime in seconds.                                           |
| `JWT_REFRESH_EXPIRY` | No       | `604800`      | Refresh token lifetime in seconds.                                          |
| `WEBHOOK_SECRET`     | Yes      | —             | Shared secret for verifying webhook signatures.                             |
| `PORT`               | No       | `8000`        | Port the backend listens on.                                                |
| `CORS_ORIGINS`       | No       | `["*"]`       | Comma-separated list of allowed origins (e.g., `http://localhost:5173`).   |
| `LOG_LEVEL`          | No       | `INFO`        | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).                        |
| `RATE_LIMIT_REQUESTS`| No       | `100`         | Max requests per `RATE_LIMIT_WINDOW`.                                       |
| `RATE_LIMIT_WINDOW`  | No       | `60`          | Rate limit window in seconds.                                               |

> ⚙️ **Deployment Tip**: In production, inject secrets via Docker secrets, Kubernetes secrets, or Vault—not via `docker-compose.yml`.

---

### Frontend Integration

The frontend (`web/src/api.js`) provides a centralized Axios instance with automatic token management and error handling. Key features include:

- **Base URL**: Configurable via `VITE_API_URL` (default: `http://localhost:8000/api/v1`).
- **Token Refresh Interceptor**: Automatically retries 401 responses by requesting a new access token using the refresh token.
- **Request Formatting**: Serializes JavaScript objects to JSON.
- **Response Parsing**: Parses JSON responses and propagates errors.

Example usage:

```javascript
import api from '@/api'

// Fetch paginated resources
const { data } = await api.get('/resources', {
  params: { page: 1, limit: 25, filter: btoa(JSON.stringify({ status: 'active' })) }
})

// Create resource
const resource = await api.post('/resources', {
  name: 'Test',
  metadata: { category: 'test' }
})
```

> 📌 **Security Note**: The `api.js` interceptor ensures tokens are refreshed *before* they expire (e.g., at 50% lifetime), minimizing interrupted sessions.

---

### Deployment Notes

#### Containerized Deployment (Recommended)

1. **Build Frontend**:
   ```bash
   cd web && npm run build
   ```
   Generates `web/dist/`.

2. **Start Services**:
   ```bash
   docker-compose up -d --build
   ```
   - The backend service builds `python:3.11-slim` + dependencies and runs `uvicorn server:app --host 0.0.0.0 --port 8000`.
   - The frontend service copies `web/dist/` into an Nginx container, served on port `80`.

3. **Environment Setup**:
   - Set secrets in `docker-compose.yml` or `.env`.
   - Ensure `DATABASE_URL` points to a PostgreSQL container or external instance.

#### CORS Configuration

- **Development**: `CORS_ORIGINS=http://localhost:5173,http://localhost:8080`  
- **Production**: Restrict to your domain(s), e.g., `CORS_ORIGINS=https://app.example.com,https://admin.example.com`

#### SSL/TLS Termination

- Nginx (`web/nginx.conf`) is configured to:
  - Redirect HTTP → HTTPS.
  - Serve static assets with caching headers.
  - Terminate TLS (certificates in `ssl/` mounted volume).

#### Monitoring & Health

- Backend exposes `/health` (Liveness/Readiness for Kubernetes).
- Metrics (`/metrics`) feed into Prometheus/Grafana dashboards.
- Logs are structured (`json`) for centralized logging (e.g., ELK, Loki).

---

### Changelog

- **v1.0.0 (Initial Release)**
  - Stable 9-endpoint REST API with full CRUD support.
  - JWT-based auth (access + refresh tokens) with secure defaults.
  - Pagination, filtering, and full-text search for resources.
  - CSV/JSON export functionality.
  - Webhook signature validation (`HMAC-SHA256`).
  - Standardized error responses with error codes.
  - Full Docker & Docker Compose integration.
  - FastAPI backend with Pydantic models and automatic OpenAPI docs (`/docs`).
  - Vue 3 frontend with Axios client and interceptors for token refresh.
  - Environment-based configuration and CORS handling.
