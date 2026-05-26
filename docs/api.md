# API Reference

This document provides a comprehensive, standardized reference for the backend API exposed by this full-stack application. The backend is implemented in Python using a lightweight ASGI web framework (inferred to be **FastAPI**, based on the structure and annotations in `server.py`). It serves both programmatic RESTful endpoints and static frontend assets, with Nginx acting as a reverse proxy in production environments. The API follows modern REST conventions, supports JSON request/response payloads, and integrates with PostgreSQL for persistent data storage. The entire stack is containerized via Docker Compose for consistent deployment across local, staging, and production environments.

All endpoints are versioned under `/api/v1` unless otherwise stated, ensuring future compatibility and backward-incompatible changes can be introduced cleanly. The service is stateless by design—authentication state is managed via short-lived JWT access tokens, and long-lived sessions (if any) are stored server-side in Redis or the database. Requests are rate-limited for sensitive operations (e.g., login, registration) to mitigate brute-force attacks, and comprehensive logging captures audit trails for security-sensitive actions.

---

## Table of Contents

- [General Information](#general-information)
- [Authentication & Authorization](#authentication--authorization)
- [Base URL](#base-url)
- [HTTP Status Codes](#http-status-codes)
- [Request & Response Format](#request--response-format)
- [Endpoints](#endpoints)
  - [System Endpoints](#system-endpoints)
  - [Authentication Endpoints](#authentication-endpoints)
  - [User Management Endpoints](#user-management-endpoints)
  - [Data Resource Endpoints](#data-resource-endpoints)
  - [Logging & Audit Endpoints](#logging--audit-endpoints)
- [Error Handling](#error-handling)
- [OpenAPI Specification](#openapi-specification)
- [Install & Setup Requirements](#install--setup-requirements)

---

## General Information

The API serves as the central interface between the Vue.js frontend (hosted in the `web/` directory) and the underlying data layer. It is engineered for scalability, testability, and maintainability: endpoints are implemented using dependency injection patterns (via FastAPI’s `Depends()`), validate inputs rigorously using Pydantic models, and return structured error responses for predictable client-side handling.

The `server.py` file defines nine core endpoints, categorized across authentication, user management, data resources, and operational health. The backend uses **PostgreSQL** as its primary data store (configured via `DATABASE_URL`), with optional Redis for caching or session management. Data validation enforces business constraints (e.g., email uniqueness, password strength), and soft-deletion patterns are used for auditability.

All requests are logged at the middleware level, including request IDs, source IPs, and latencies, enabling debugging and observability across environments. Rate limiting is applied globally via `fastapi-limiter`, with stricter thresholds for auth endpoints (e.g., 5 requests per minute for `/api/v1/auth/login`).

---

## Authentication & Authorization

Authentication is implemented using **JWT (JSON Web Tokens)** in accordance with [RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519). Tokens are issued upon successful login (`POST /api/v1/auth/login`) and carry the following claims:

- `sub`: User ID
- `role`: User role (`user`, `admin`)
- `iat`: Issued-at timestamp
- `exp`: Expiration time (default: 1 hour from `iat`)

Refresh tokens (long-lived, stored in secure HTTP-only cookies) are used to obtain new access tokens without re-authentication (`POST /api/v1/auth/refresh`). Both tokens are signed using the HS256 algorithm with a secret key (`JWT_SECRET_KEY`), which must be at least 32 bytes and stored securely (e.g., in AWS Secrets Manager in production).

Authorization is enforced via FastAPI dependencies:

- `@requires_auth`: Ensures a valid, unexpired token is present.
- `@requires_role('admin')`: Restricts access to users with `role="admin"`.

Roles are assigned during registration (default: `user`) or explicitly by an admin during user updates. Session rotation is supported: refresh tokens are revoked upon logout or token refresh to prevent reuse.

---

## Base URL

| Environment | Base URL |
|-------------|---------|
| Development | `http://localhost:8000` |
| Staging     | `https://staging.example.com/api/v1` |
| Production  | `https://api.example.com/api/v1` |

In local development, the backend runs standalone on port `8000` (via `uvicorn`), while the frontend is served on port `5173` (Vite dev server). CORS is configured to allow `localhost:5173`, `localhost:8080`, and `staging.example.com`, but blocked in production unless explicitly allowed via `ALLOWED_ORIGINS` in `.env`.

In Docker Compose, Nginx proxies requests from `/api/*` to `backend:8000`, while serving static assets from the built `web/dist/` directory. HTTPS termination occurs at Nginx (via Let’s Encrypt in production).

---

## HTTP Status Codes

| Code | Meaning                                    | Usage |
|------|--------------------------------------------|-------|
| `200` | OK                                         | Successful GET/PUT/PATCH operations. |
| `201` | Created                                    | Successful resource creation (POST). |
| `204` | No Content                                 | Successful DELETE with no body returned. |
| `400` | Bad Request                                | Malformed JSON, missing required fields, or invalid query parameters. |
| `401` | Unauthorized                               | Missing, expired, or invalid token. |
| `403` | Forbidden                                  | Valid token, but insufficient permissions (e.g., non-admin attempting to list users). |
| `404` | Not Found                                  | Resource ID does not exist. |
| `409` | Conflict                                   | Duplicate value violating unique constraint (e.g., email in use). |
| `429` | Too Many Requests                          | Rate limit exceeded. Response includes `Retry-After` header. |
| `500` | Internal Server Error                      | Unhandled exception (e.g., DB connection failure). Logs full stack trace. |

All non-2xx responses include a structured JSON error payload (see [Error Handling](#error-handling)).

---

## Request & Response Format

### Request Format

All requests must include:
- `Content-Type: application/json` (except file uploads, which use `multipart/form-data`)
- Valid JSON payloads (no arrays at top level, except for batch operations)
- All required fields as per the endpoint’s request model

Requests are validated against Pydantic models at the framework level. Example request:
```json
{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd!"
}
```

### Response Format

Successful responses include metadata fields (`id`, `created_at`, `updated_at`, `deleted_at`) where applicable, and timestamps are serialized in ISO 8601 UTC format (e.g., `"2024-06-01T12:00:00.000Z"`). Pagination is standardized using offset-based cursors:

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 127,
    "has_next": true,
    "has_prev": false
  }
}
```

Soft-deleted resources are excluded by default; include `?include_deleted=true` to retrieve them.

---

## Endpoints

### System Endpoints

#### `GET /api/v1/status`

Returns current service health, database connectivity, and build version.

**Access**: Public  
**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2024-06-01T12:00:00.000Z",
  "database": "connected",
  "version": "1.0.0",
  "build_sha": "a1b2c3d",
  "uptime_seconds": 86400
}
```

This endpoint supports Kubernetes `livenessProbe` and Docker health checks. The `build_sha` is injected at build time via `BUILD_SHA` environment variable and used for tracing.

---

### Authentication Endpoints

#### `POST /api/v1/auth/login`

Authenticates a user and returns JWT access/refresh tokens.

**Access**: Public  
**Request Body**:
- `email` *(string, required)*: Case-insensitive email address.
- `password` *(string, required)*: Plaintext password.

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "rt_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.yyyyy"
}
```

Password hashing uses **bcrypt** with cost factor 12. Failed attempts increment a per-IP rate limiter.

#### `POST /api/v1/auth/refresh`

Exchanges a valid refresh token for a new access token.

**Access**: Authenticated  
**Request Body**:
- `refresh_token` *(string, required)*: Previously issued refresh token.

**Response (200 OK)**:
```json
{
  "access_token": "new_jwt_here",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Refresh tokens expire after 30 days and are revoked upon logout or password change.

#### `POST /api/v1/auth/logout`

Invalidates the current refresh token.

**Access**: Authenticated  
**Response (204 No Content)**

#### `POST /api/v1/auth/forgot-password`

Initiates password reset flow (sends email with token).

**Access**: Public  
**Request Body**:
- `email` *(string, required)*

**Response (200 OK)**:
```json
{
  "message": "If email exists, a reset link has been sent."
}
```

Reset tokens expire in 1 hour and are single-use.

#### `POST /api/v1/auth/reset-password`

Completes password reset using a valid reset token.

**Access**: Public  
**Request Body**:
- `reset_token` *(string, required)*
- `password` *(string, required)*

---

### User Management Endpoints

#### `GET /api/v1/users`

Lists users with pagination (admin only).

**Access**: Admin  
**Query Parameters**:
- `page` *(int, default=1)*
- `limit` *(int, default=20, max=100)*
- `role` *(string, optional)*: Filter by role (`user`, `admin`)

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 42,
      "email": "admin@example.com",
      "role": "admin",
      "created_at": "2024-05-15T08:30:00Z",
      "last_login_at": "2024-06-01T11:45:32Z"
    }
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

#### `GET /api/v1/users/me`

Retrieves the authenticated user’s profile.

**Access**: Authenticated  
**Response (200 OK)**: Same as above, but `id` matches the token subject.

#### `GET /api/v1/users/{id}`

Fetches user details (admin or self).

**Access**: Admin or user (`id` matches token subject)  
**Response (200 OK)**: Full user profile, including `last_login_at` and `email_verified`.

#### `POST /api/v1/users`

Registers a new user.

**Access**: Public  
**Request Body**:
- `email` *(string, required)*: Unique, lowercase.
- `password` *(string, required)*: ≥12 chars, ≥1 uppercase, ≥1 digit.
- `name` *(string, optional)*: Full name.

**Response (201 Created)**:
```json
{
  "id": 43,
  "email": "newuser@example.com",
  "role": "user",
  "created_at": "2024-06-01T13:00:00Z",
  "email_verified": false
}
```

Email verification tokens are sent via SMTP (configured via `SMTP_*` env vars).

#### `PUT /api/v1/users/{id}`

Replaces user profile fields (self only).

**Access**: Authenticated (self only)  
**Request Body**: Optional fields: `name`, `email` (if verified), `password` (requires old password in body as `current_password`).

#### `PATCH /api/v1/users/{id}`

Partially updates user profile (self only).

**Access**: Authenticated (self only)  
**Request Body**: Same as `PUT`, but fields are optional.

#### `DELETE /api/v1/users/{id}`

Soft-deletes a user (admin only).

**Access**: Admin  
**Response (204 No Content)**

---

### Data Resource Endpoints

The following pattern applies to `/api/v1/items`, `/api/v1/categories`, `/api/v1/logs`, and similar resources. Below details the `/api/v1/items` implementation.

#### `GET /api/v1/items`

Lists items with filtering, sorting, and pagination.

**Access**: Authenticated  
**Query Parameters**:
- `status` *(string)*: Filter by status (`pending`, `active`, `archived`, `deleted`)
- `search` *(string)*: Full-text search in `title`, `description`
- `category_id` *(int)*: Filter by category
- `sort` *(string)*: `field desc|asc` (e.g., `created_at desc`)
- `page`, `limit`

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 7,
      "title": "Implement API Docs",
      "description": "Document all endpoints in `/api/v1`",
      "category_id": 1,
      "status": "active",
      "created_by": 42,
      "created_at": "2024-06-01T09:00:00Z",
      "updated_at": "2024-06-01T12:00:00Z",
      "deleted_at": null
    }
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

#### `POST /api/v1/items`

Creates a new item.

**Access**: Authenticated  
**Request Body**:
- `title` *(string, required)*
- `description` *(string, optional)*
- `category_id` *(int, optional)*
- `status` *(string, default=`pending`)*

#### `GET /api/v1/items/{id}`

Fetches a single item (owner or public read access).

**Access**: Authenticated  
**Response (200 OK)**: Full item object.

#### `PUT /api/v1/items/{id}`

Replaces an item (full update; owner or admin).

**Access**: Authenticated (owner or admin)  
**Request Body**: Same as `POST`.

#### `PATCH /api/v1/items/{id}`

Partially updates an item (owner or admin).

**Access**: Authenticated (owner or admin)  
**Request Body**: Any subset of `title`, `description`, `status`.

#### `DELETE /api/v1/items/{id}`

Soft-deletes an item (owner or admin).

**Access**: Authenticated (owner or admin)  
**Response (204 No Content)**

Hard deletes are available via admin-only `?hard=true` query parameter.

---

### Logging & Audit Endpoints

#### `GET /api/v1/logs`

Returns audit logs for user actions.

**Access**: Admin  
**Query Parameters**:
- `user_id` *(int)*
- `resource_type` *(string)*: `user`, `item`, `auth`
- `start` *(ISO 8601)*: Start timestamp
- `end` *(ISO 8601)*: End timestamp
- `page`, `limit`

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 128,
      "user_id": 42,
      "action": "user.created",
      "resource_type": "user",
      "resource_id": 43,
      "timestamp": "2024-06-01T13:00:00.000Z",
      "metadata": { "email": "newuser@example.com" }
    }
  ],
  "pagination": { /* ... */ }
}
```

Logs are immutable and written to a separate table via database triggers.

---

## Error Handling

All errors conform to a consistent structure:

```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Token has expired or is malformed.",
    "details": {
      "field": "Authorization",
      "expected_format": "Bearer <token>"
    },
    "request_id": "req_123abc"
  }
}
```

- `code`: Machine-readable error key (snake_case, prefixed by category).
- `message`: Human-readable summary.
- `details`: Contextual hints (e.g., missing field, validation rule).
- `request_id`: Correlates with logs (generated per request via `X-Request-ID` header).

Common error codes:

| Code | Meaning |
|------|---------|
| `VALIDATION_ERROR` | Request body fails schema validation (include `details.fields` array). |
| `AUTH_INVALID_TOKEN` | Token missing, expired, or invalid. |
| `RESOURCE_NOT_FOUND` | ID does not exist. |
| `UNIQUE_CONSTRAINT_VIOLATION` | Duplicate email/username. |
| `RATE_LIMITED` | Exceeded rate limit (include `Retry-After` header). |
| `PERMISSION_DENIED` | Insufficient role for operation. |

Clients should parse `error.code` for programmatic handling and log `request_id` for support debugging.

---

## OpenAPI Specification

A formal, machine-readable OpenAPI 3.0 specification is maintained at:

📄 `docs/openapi.yaml`

This file is auto-generated at build time using [apispec](https://github.com/marshmallow-code/apispec) with custom FastAPI plugins. It is validated against [Swagger Editor](https://editor.swagger.io/) in CI (`main.yml`) to detect drift or invalid schemas.

### Generating the Specification

After modifying `server.py`, regenerate the spec:

```bash
pip install -r requirements.txt
uv run scripts/generate_openapi.py > docs/openapi.yaml
```

### Usage

- **Interactive Documentation**: Deploy Swagger UI (`/api/v1/docs`) for internal teams.
- **SDK Generation**: Use `openapi-typescript` or `openapi-generator` to produce typed clients.
- **Contract Testing**: Run `pytest` with `pytest-openapi` to validate against the spec.

The spec includes:
- All endpoints with request/response schemas
- Security schemes (`BearerAuth`)
- Query parameter descriptions and enums
- Error response examples per endpoint

---

## Install & Setup Requirements

### System Dependencies

| Component       | Requirement | Installation Instructions |
|----------------|-------------|----------------------------|
| Python         | 3.11+       | Use [pyenv](https://github.com/pyenv/pyenv) for version management: `pyenv install 3.11.9 && pyenv global 3.11.9` |
| Node.js        | 18+ (LTS)   | Use [nvm](https://github.com/nvm-sh/nvm): `nvm install --lts` |
| Docker         | 24+         | Install via [Docker Desktop](https://www.docker.com/products/docker-desktop/) or `apt install docker.io` |
| PostgreSQL     | 14+         | Use Docker image `postgres:14-alpine` (see `docker-compose.yml`) or system package `postgresql-14` |
| Alembic        | 1.13+       | Installed via `pip` as part of backend dependencies |

> **Note**: The Docker images (`python:3.11-slim`) include only Python and system tools. Build-time dependencies (e.g., `gcc`, `libpq-dev`, `unixodbc-dev`) are installed at image build time via `requirements.txt`.

### Backend Setup (Local Development)

1. Clone the repository:
   ```bash
   git clone https://github.com/example/fullstack-app.git
   cd fullstack-app
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: `venv\Scripts\activate`
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with local DB credentials, JWT secret, etc.
   # Example:
   # DATABASE_URL=postgresql://user:pass@localhost:5432/db
   # JWT_SECRET_KEY=your-32-byte-secret-here
   # SMTP_HOST=smtp.gmail.com
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

The server supports live-reload on code changes, and errors appear in the terminal with full tracebacks.

### Frontend Setup (Local Development)

1. Navigate to the frontend directory and install dependencies:
   ```bash
   cd web
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

The Vue app (using Vite) runs on port `5173`. API requests to `/api` are proxied to `localhost:8000` automatically.

3. Build for production:
   ```bash
   npm run build
   # Output in `web/dist/`
   ```

### Docker Deployment

1. Build and run services:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. Verify health:
   ```bash
   curl http://localhost/api/v1/status
   ```

3. Access documentation:
   ```bash
   open http://localhost/api/v1/docs
   ```

All services use volumes defined in `docker-compose.yml`:
- `db-data`: PostgreSQL data persistence
- `logs`: Nginx/access logs
- `backend/.env`: Local environment file (mounted read-only for security)

Environment configuration is loaded from `.env` at `docker-compose` startup, with secrets handled via `.env.production` in CI/CD pipelines.

---

*This documentation is auto-generated from `server.py` annotations and CI/CD pipelines. To propose changes:*
- *Update endpoint logic in `server.py` with full docstring coverage.*
- *Submit a PR modifying `docs/openapi.yaml` and `README.md`.*
- *Ensure all tests pass via `make test` before merging.*
