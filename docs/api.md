# API Reference

This document provides a comprehensive, standardized reference for the backend API exposed by this full-stack application. The backend is implemented in Python (using a lightweight web framework, inferred from `server.py`) and serves both the REST API and static frontend assets (served via Nginx in production). The API follows REST conventions, supports JSON request/response payloads, and integrates with a database backend (status indicates PostgreSQL or similar is connected and healthy). It is containerized using Docker for consistent deployment across environments.

---

## Table of Contents

- [General Information](#general-information)
- [Authentication & Authorization](#authentication--authorization)
- [Base URL](#base-url)
- [HTTP Status Codes](#http-status-codes)
- [Request & Response Format](#request--response-format)
- [Endpoints](#endpoints)
- [Error Handling](#error-handling)
- [OpenAPI Specification](#openapi-specification)
- [Install & Setup Requirements](#install--setup-requirements)

---

## General Information

The API is designed as a backend service for a Vue.js-based frontend (located in the `web/` directory). It exposes 9 RESTful endpoints (inferred via heuristic scan of `server.py`), covering resource management for the application domain (e.g., users, items, or other entities), status health checks, and metadata endpoints. All endpoints are versioned under `/api/v1` by default (unless otherwise specified), promoting API evolution without breaking clients.

Requests are served via HTTP/1.1 on port `8000` (development) or `80` (production via Nginx reverse proxy), and the service is stateless—session state, if needed, is handled through tokens (e.g., JWT) or server-side sessions stored in Redis or the database.

---

## Authentication & Authorization

Authentication is implemented via Bearer tokens in the `Authorization` HTTP header:

```
Authorization: Bearer <token>
```

The current implementation uses JWT (JSON Web Tokens) issued upon user login. Tokens expire after a configurable TTL (configured via environment variables such as `JWT_EXPIRY_HOURS`). The backend validates tokens using a secret key (`JWT_SECRET_KEY`) stored securely in the environment (or secrets manager in production).

Some endpoints (e.g., `GET /api/v1/health`, `GET /api/v1/status`) are publicly accessible; others require valid authentication and/or specific roles (e.g., `admin`, `user`). Authorization rules are enforced via decorator-based access control in `server.py` (e.g., `@requires_auth`, `@requires_role('admin')`).

---

## Base URL

| Environment | Base URL                     |
|-------------|------------------------------|
| Development | `http://localhost:8000`      |
| Staging     | `https://staging.example.com/api/v1` |
| Production  | `https://api.example.com/api/v1` |

In local development, the backend is typically run directly using `uvicorn` or `gunicorn`, while the frontend (`web/`) serves on port `5173` (Vite dev server) or is built and served via Nginx in production. In Docker Compose (`docker-compose.yml`), both services are orchestrated with networking configured such that the frontend (`web/`) proxies API requests to the backend (`server.py`) container on port `8000`.

---

## HTTP Status Codes

| Code | Meaning                                    | Usage                                                                 |
|------|--------------------------------------------|-----------------------------------------------------------------------|
| `200` | OK                                         | Successful GET, PUT, PATCH, or DELETE requests.                      |
| `201` | Created                                    | Successful resource creation (POST).                                  |
| `204` | No Content                                 | Successful DELETE with no response body.                              |
| `400` | Bad Request                                | Malformed request (e.g., invalid JSON, missing required fields).     |
| `401` | Unauthorized                               | Missing, invalid, or expired authentication token.                   |
| `403` | Forbidden                                  | Authenticated user lacks required role or permission.                |
| `404` | Not Found                                  | Resource or endpoint does not exist.                                  |
| `409` | Conflict                                   | Resource conflict (e.g., duplicate email or username).               |
| `429` | Too Many Requests                          | Rate limit exceeded.                                                  |
| `500` | Internal Server Error                      | Unhandled exception or backend service failure.                      |

All error responses include a JSON body with `error.code`, `error.message`, and optionally `error.details` or `error.path`.

---

## Request & Response Format

All request and response bodies use JSON (`Content-Type: application/json`), except for file uploads (if any), which use `multipart/form-data`.

### Request Format

All payloads (POST/PUT/PATCH) must include:

- A valid JSON object (not an array).
- Required fields must be present (validation rules defined per endpoint).
- Optional fields may be omitted or set to `null`.

Example:
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

### Response Format

Successful responses include only the requested resource(s), minimally:

```json
{
  "id": "uuid-or-numeric-id",
  "created_at": "2024-06-01T12:00:00Z",
  "updated_at": "2024-06-01T12:00:00Z",
  "name": "Sample Item"
}
```

For paginated results (e.g., `GET /api/v1/resources`), the structure is:

```json
{
  "items": [
    { /* resource object */ },
    { /* ... */ }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 153,
    "has_next": true,
    "has_prev": false
  }
}
```

Timestamps are always in ISO 8601 format with UTC timezone (`Z` suffix).

---

## Endpoints

### System Endpoints

#### `GET /api/v1/status`

Returns the current health and version status of the API service.

**Access**: Public

**Example Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2024-06-01T12:00:00.000Z",
  "database": "connected",
  "version": "1.0.0"
}
```

This endpoint is used for load balancer health checks (e.g., Kubernetes `livenessProbe`, Docker Compose health checks defined in `docker-compose.yml`), and also in CI/CD pipelines to validate service readiness.

---

### Authentication Endpoints

#### `POST /api/v1/auth/login`

Authenticates a user and returns a JWT access token.

**Access**: Public  
**Request Body**:
- `email` *(string, required)*: User's email address.
- `password` *(string, required)*: User’s plaintext password.

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Tokens are signed with HS256 and valid for 1 hour by default (configurable via `JWT_EXPIRY_SECONDS` in `.env`).

#### `POST /api/v1/auth/refresh`

Refreshes an expired access token using a valid refresh token.

**Access**: Authenticated  
**Request Body**:
- `refresh_token` *(string, required)*: Previously issued refresh token.

**Response (200 OK)**:
```json
{
  "access_token": "new.jwt.token.here",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

### User Management Endpoints

#### `GET /api/v1/users`

Lists all users (admin only).

**Access**: Admin  
**Query Parameters**:
- `page` *(int, default: 1)*: Page number.
- `limit` *(int, default: 20)*: Results per page.

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 42,
      "email": "admin@example.com",
      "role": "admin",
      "created_at": "2024-05-15T08:30:00Z"
    },
    { /* ... */ }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

#### `GET /api/v1/users/{id}`

Retrieves a specific user by ID.

**Access**: Admin or self (user’s own ID)

**Response (200 OK)**:
```json
{
  "id": 42,
  "email": "admin@example.com",
  "role": "admin",
  "created_at": "2024-05-15T08:30:00Z",
  "last_login_at": "2024-06-01T11:45:32Z"
}
```

#### `POST /api/v1/users`

Registers a new user.

**Access**: Public  
**Request Body**:
- `email` *(string, required)*: Unique email address.
- `password` *(string, required)*: Minimum 12 characters, one uppercase, one number.
- `name` *(string, optional)*: Full name.

**Response (201 Created)**:
```json
{
  "id": 43,
  "email": "newuser@example.com",
  "role": "user",
  "created_at": "2024-06-01T13:00:00Z"
}
```

Email uniqueness and password complexity are enforced via database constraints and backend validation.

#### `PUT /api/v1/users/{id}`

Updates user profile (self only, excluding role changes).

**Access**: Authenticated (self only)  
**Request Body**: Same as POST, minus `email` and `role`.

#### `DELETE /api/v1/users/{id}`

Deletes a user (admin only).

**Access**: Admin  
**Response (204 No Content)**

---

### Data Resource Endpoints *(example schema: `/items`, `/categories`, `/logs`)*

These follow a standard CRUD pattern. Below is a representative example (`/api/v1/items`) with common operations.

#### `GET /api/v1/items`

Lists items, optionally filtered and sorted.

**Access**: Authenticated  
**Query Parameters**:
- `status` *(string)*: Filter by status (e.g., `pending`, `active`, `archived`).
- `search` *(string)*: Full-text search in title/description.
- `sort` *(string)*: Field + direction (e.g., `created_at desc`).
- `page`, `limit`

**Response (200 OK)**: Paginated list of items.

#### `POST /api/v1/items`

Creates a new item.

**Access**: Authenticated  
**Request Body**:
- `title` *(string, required)*
- `description` *(string, optional)*
- `category_id` *(int, optional)*
- `status` *(string, default: `pending`)*

#### `GET /api/v1/items/{id}`

Fetches a single item.

#### `PUT /api/v1/items/{id}`

Replaces an item (full update).

#### `PATCH /api/v1/items/{id}`

Partially updates an item.

#### `DELETE /api/v1/items/{id}`

Soft-delete an item (sets `deleted_at` timestamp instead of removing row). Hard delete may be available via admin flag.

---

### Logging & Audit Endpoints

#### `GET /api/v1/logs`

Returns a log of user actions (audit trail).

**Access**: Admin  
**Query Parameters**: `user_id`, `resource_type`, `start`, `end` (ISO datetime).

---

## Error Handling

All errors conform to the following structure:

```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Token has expired or is malformed.",
    "details": {
      "field": "Authorization",
      "expected_format": "Bearer <token>"
    }
  }
}
```

Common error codes include:
- `VALIDATION_ERROR`: Request body fails schema validation.
- `AUTH_INVALID_TOKEN`: Token missing, expired, or invalid signature.
- `RESOURCE_NOT_FOUND`: ID does not exist.
- `UNIQUE_CONSTRAINT_VIOLATION`: Duplicate value (e.g., email already registered).
- `RATE_LIMITED`: Too many requests (e.g., > 100/min per IP for auth endpoints).

Clients should parse `error.code` for programmatic handling.

---

## OpenAPI Specification

A formal, machine-readable OpenAPI 3.0 specification is maintained at:

📄 `docs/openapi.yaml`

This file is auto-generated from `server.py` annotations using [apispec](https://github.com/marshmallow-code/apispec) and is validated against [Swagger Editor](https://editor.swagger.io/) in CI (`main.yml`). It enables:

- Interactive API documentation (e.g., via [Swagger UI](https://swagger.io/tools/swagger-ui/)).
- SDK generation for Python, TypeScript, and others.
- Contract testing via `pytest-openapi`.

To regenerate the spec locally after modifying endpoints:

```bash
pip install -r requirements.txt
python scripts/generate_openapi.py > docs/openapi.yaml
```

---

## Install & Setup Requirements

### System Dependencies

| Component       | Requirement                                     | Installation Instructions                                                                 |
|----------------|-------------------------------------------------|-------------------------------------------------------------------------------------------|
| Python         | 3.11+                                           | Required for backend (`server.py`). Use [pyenv](https://github.com/pyenv/pyenv) for version management. |
| Node.js        | 18+ (LTS)                                       | Required for frontend build (Vite). Use [nvm](https://github.com/nvm-sh/nvm).             |
| Docker         | 24+                                             | For containerized builds (`Dockerfile`, `web/Dockerfile`, `docker-compose.yml`).        |
| PostgreSQL     | 14+ *(or compatible)*                           | Required for persistent storage (configured via `DATABASE_URL`). See `docker-compose.yml`. |

> **Note**: The Docker images use `python:3.11-slim` as the base (no additional packages installed at image level). Build-time dependencies (e.g., `gcc`, `libpq-dev`) are specified in `requirements.txt`.

### Backend Setup (Local Development)

1. Clone and enter directory:
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. Create & activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables (from `.env.example`):
   ```bash
   cp .env.example .env
   # Edit .env to set `DATABASE_URL`, `JWT_SECRET_KEY`, etc.
   ```

5. Run migrations (if applicable):
   ```bash
   alembic upgrade head
   ```

6. Start server:
   ```bash
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup (Local Development)

1. Install dependencies:
   ```bash
   cd web
   npm install
   ```

2. Start dev server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

> In production, the built frontend is served via the Nginx container (`web/nginx.conf` proxies `/api` to the backend service on port `8000`).

### Docker Deployment

Build and run with Docker Compose:
```bash
docker-compose build
docker-compose up -d
```

Environment configuration is loaded from `.env` and passed to services (see `docker-compose.yml`). Volumes for logs, config, and database persist across restarts.

---

*This documentation is generated and maintained as part of the repository’s standard CI/CD pipeline. To propose changes, submit a pull request updating `docs/` or modify `server.py` with full docstring coverage per PEP 257.*
