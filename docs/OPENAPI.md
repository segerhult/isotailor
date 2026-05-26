# OpenAPI

## Specification Files

The OpenAPI 3.0.3 specification for this fullstack application resides at `docs/openapi.yaml`. This file serves as the authoritative contract between the backend (`server.py`) and the frontend (`web/src/api.js`), defining all RESTful API endpoints, their parameters, request/response bodies, authentication mechanisms, and reusable data models.

The specification is maintained as a single source of truth to support multiple critical workflows:
- **Interactive Documentation**: Generated via Swagger UI, available at `/docs` on the frontend server.
- **Client SDK Generation**: TypeScript clients are auto-generated for type-safe consumption in the React frontend.
- **Contract Testing**: Used in CI pipelines to ensure backend changes do not introduce breaking changes.
- **Developer Onboarding**: Provides developers with a self-service reference for API behavior and structure.

All changes to backend routing, request/response payloads, or security requirements must be reflected in `docs/openapi.yaml` *before* merging code, per the CI/CD pipeline defined in `.github/workflows/main.yml`.

---

## Detected Endpoints (Heuristic)

The backend implements nine RESTful endpoints under the `/api` base path. Each endpoint is documented with full metadata, including required authentication, expected payloads, response structures, and edge cases.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Returns service health status for infrastructure-level health checks (e.g., Kubernetes liveness). Unauthenticated. |
| `GET` | `/api/default-software` | Retrieves a curated list of default software packages preconfigured for new uploads. Used by the frontend to initialize form defaults. |
| `GET` | `/api/uploads` | Lists paginated uploads for the authenticated user. Supports filtering by `status`, `created_from`, and `created_to`. Includes metadata but not full artifact details. |
| `POST` | `/api/uploads` | Creates a new upload record in `pending` state. Returns a structured response with metadata and a presigned URL for binary upload (handled separately via `PUT`). |
| `GET` | `/api/uploads/{id}` | Retrieves detailed information for a single upload, including status transitions, associated software, and metadata. Returns `404` if not found or unauthorized. |
| `PUT` | `/api/uploads/{id}/software` | Updates software configuration (e.g., toolchain selection) for an upload. Only allowed for uploads in `pending` or `failed` state. |
| `GET` | `/api/uploads/{id}/manifest` | Returns a JSON manifest describing the finalized artifact (dependencies, file tree, checksums, metadata). Generated only after successful processing. |
| `GET` | `/api/uploads/{id}/iso` | Downloads the compiled ISO file as a binary stream (`application/octet-stream`). Access is restricted to owners or explicitly shared users. |
| `DELETE` | `/api/uploads/{id}` | Deletes the upload record and associated artifacts. May perform soft-deletion depending on configuration. Returns `204 No Content` on success. |

All endpoints—except `/api/health` and `/api/uploads/{id}/iso` (which returns raw binary)—expect and return `application/json` payloads.

---

## Request and Response Schemas

The `components/schemas` section defines reusable data structures used throughout the API. Key models include:

### `Upload`
A core resource representing a user-initiated build request.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` (UUID v4) | Unique identifier assigned upon creation. Immutable. |
| `filename` | `string` | Original filename provided during `POST /api/uploads`. |
| `status` | `string` | One of: `pending` (initial), `processing` (in flight), `completed` (ready), `failed` (irrecoverable). |
| `created_at` | `string` (ISO 8601) | Timestamp of record creation (UTC). |
| `updated_at` | `string` (ISO 8601) | Timestamp of the last state change (UTC). |
| `software` | `string[]` | Array of software package IDs selected by the user (e.g., `["gcc-12", "gdb-13"]`). |
| `size` | `integer` (int64, optional) | Size in bytes of the original binary upload. Present only after upload completes. |
| `download_url` | `string` (optional) | Presigned URL for binary upload, returned by `POST /api/uploads`. |
| `share_id` | `string` (optional) | Unique share token for public/authorized sharing (if enabled). |

### `SoftwarePackage`
Represents a configurable build tool or library.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Internal package identifier (e.g., `llvm-15`). |
| `name` | `string` | Human-readable name (e.g., `LLVM Compiler Infrastructure v15`). |
| `version` | `string` | Semantic version (e.g., `15.0.7`). |
| `description` | `string` (optional) | Optional human-readable description. |
| `tags` | `string[]` (optional) | Categorization tags (e.g., `["compiler", "c-family"]`). |

### `HealthCheck`
Minimal health status for orchestration.

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"healthy"` when service is responsive. |
| `timestamp` | `string` (ISO 8601) | Current server time. |
| `version` | `string` (optional) | Backend version (e.g., `2.1.0`). |

### `Error`
Standardized error structure returned on non-2xx responses.

```yaml
Error:
  type: object
  required:
    - error
  properties:
    error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
          example: "UPLOAD_NOT_FOUND"
        message:
          type: string
          example: "The requested upload could not be located."
        details:
          type: array
          items:
            type: object
          example:
            - field: "software"
              reason: "must be a non-empty array"
```

Common `error.code` values include:
- `UPLOAD_NOT_FOUND`: `404` when ID is invalid or inaccessible.
- `INVALID_STATE`: `409` when an operation conflicts with current upload status (e.g., modifying software on a `completed` upload).
- `UNAUTHORIZED`: `401` when no token or invalid token provided.
- `FORBIDDEN`: `403` when user lacks permission for the operation.
- `VALIDATION_ERROR`: `400` for malformed request payloads.

---

## Authentication & Authorization

All endpoints—except `/api/health`—require authentication via JWT in the `Authorization` header:

```
Authorization: Bearer <token>
```

The backend middleware (`server.py`) validates tokens issued by a dedicated authentication service (e.g., Auth0, custom OAuth2). Unauthorized requests return `401 Unauthorized`, while access to non-owned resources returns `403 Forbidden`.

Ownership verification logic:
- `GET /api/uploads/{id}`, `PUT /api/uploads/{id}/software`, `DELETE /api/uploads/{id}`: User must be the upload creator.
- `GET /api/uploads/{id}/iso`: User must be owner *or* have explicit share permissions (via `share_id` or internal group membership).
- `POST /api/uploads`: Any authenticated user may create uploads.
- `GET /api/uploads`: Returns only uploads owned by the requesting user.

The `securitySchemes` section explicitly defines this:

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## Path and Parameter Conventions

- **Path Parameters**: Simple, descriptive, lowercase identifiers (e.g., `{id}` for upload UUIDs). All IDs follow RFC4122 v4 format (`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`).
- **Query Parameters** for `GET /api/uploads`:
  - `limit`: Integer (default: `20`, max: `100`). Controls pagination size.
  - `offset`: Integer (default: `0`). Offset for pagination.
  - `status`: Filter by status (e.g., `?status=completed`). Accepts comma-separated list (`?status=completed,failed`).
  - `created_from`, `created_to`: ISO 8601 timestamps for date range filtering (e.g., `?created_from=2023-01-01T00:00:00Z`).
- **Timestamps**: All `created_at`, `updated_at`, and time-based query filters use UTC and ISO 8601 format (`YYYY-MM-DDTHH:mm:ss.SSSZ`).
- **File Upload Flow**: Binary data is *not* sent in the API payload. Instead:
  1. `POST /api/uploads` returns a presigned `download_url`.
  2. The frontend uploads the binary directly to the storage backend via `PUT {download_url}`.
  3. The backend polls or listens for upload completion events.

---

## Integration with Frontend

The frontend (`web/src/api.js`) provides a type-safe, intercept-based abstraction layer over the API:

- **Request Interceptor**: Attaches JWT token from `localStorage`.
- **Response Interceptor**: Handles `401` (redirect to login), `403` (show forbidden message), and structured `4xx/5xx` errors.
- **Typed Clients**: Auto-generated client methods mirror spec endpoints:
  - `listUploads({ limit, offset, status })`
  - `createUpload({ filename, software })`
  - `getUpload(id)`
  - `updateSoftware(id, { software })`
  - `getManifest(id)`
  - `downloadIso(id)` (handles binary stream)
  - `deleteUpload(id)`

The frontend also uses:
- `GET /api/default-software` to initialize `software` selection in upload forms.
- `GET /api/uploads/{id}/manifest` to render build results, dependency trees, and checksums in the UI.

This tight coupling ensures frontend and backend evolve in lockstep, with spec-driven contract testing in CI.

---

## Swagger UI Integration

The OpenAPI spec is integrated into the frontend application and exposed at `/docs` (served by Nginx via `web/nginx.conf`). The UI is implemented as a static SPA using `swagger-ui-dist`, bundled during the frontend build (`npm run build`).

Key aspects:
- **Live Preview**: Users can explore and test endpoints directly in the browser.
- **Spec Fetching**: The UI dynamically loads `openapi.yaml` from `/api/openapi` (proxied via Nginx to `/docs/openapi.yaml` on the backend container).
- **Versioning**: A `version` tag in the spec title links to `docs/CHANGELOG.md` and the latest release tag (e.g., `v2.1.0`).
- **CI Sync**: On every push to `main`, `docs/openapi.yaml` is validated and deployed with the frontend artifacts to ensure consistency.

No custom plugins or extensions are used beyond standard Swagger UI features.

---

## Maintaining the Spec

To preserve accuracy and usability, the following practices are enforced:

1. **Spec-First Development**: Backend route changes require an accompanying `docs/openapi.yaml` update in the same PR.
2. **Validation Hook**: A pre-commit hook (`scripts/validate-openapi.sh`) runs `openapi-spec-validator` on changes.
3. **CI Gate**: The CI pipeline (`main.yml`) runs `openapi-spec-validator docs/openapi.yaml` on pull requests.
4. **Sample Coverage**: Non-trivial operations (e.g., `POST /api/uploads`, `PUT /api/uploads/{id}/software`) include `examples` fields with concrete JSON payloads and responses.
5. **Rate Limiting & Quotas**: If applied, must be defined using `x-rate-limit-*` vendor extensions in relevant operations.
6. **Error Consistency**: All `4xx/5xx` responses must conform to the `Error` schema.

---

## Install Requirements

While the OpenAPI spec itself is human-readable and tool-agnostic, practical usage (validation, generation, local preview) requires additional tooling.

### For Python-based Validation & Generation

Install via `pip` for CLI tools and libraries:
```bash
# Install core validation and generation libraries
pip install openapi-spec-validator openapi-core openapi-generator-cli

# Validate spec against v3.0 spec
openapi-spec-validator docs/openapi.yaml

# Generate server stubs (Python Flask/FastAPI)
openapi-generator-cli generate -i docs/openapi.yaml -g python-flask -o /tmp/server-stub

# Validate and generate client bindings
openapi-core validate docs/openapi.yaml
```

### For Node.js CLI Tools & SDK Generation

Use `npm` or `yarn` for Node-based tooling:
```bash
# Global CLI for spec validation and serving
npm install -g @apidevtools/swagger-cli

# Validate syntax
swagger-cli validate docs/openapi.yaml

# Serve locally (Swagger UI)
swagger-cli serve docs/openapi.yaml

# TypeScript SDK generation (using openapi-typescript)
npm install -D openapi-typescript
npx openapi-typescript docs/openapi.yaml -o web/src/generated/client.ts

# Type-safe Axios client (openapi-client-axios)
npm install -D openapi-client-axios
npx openapi-client-axios docs/openapi.yaml -o web/src/generated/axios-client.ts
```

### For Docker-based Preview

Use Docker to run Swagger UI without local dependencies:
```bash
# Ensure Docker daemon is running
# Pull latest image
docker pull swaggerapi/swagger-ui

# Run container, mounting the docs directory
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/openapi.yaml \
  -v $(pwd)/docs:/openapi \
  swaggerapi/swagger-ui
```
Then visit `http://localhost:8080` to view the interactive documentation.

### Frontend SDK Generation (TypeScript)

The project uses `openapi-typescript` for tight TypeScript integration:
```bash
# Generate client definitions for `web/src/api.js`
npm run generate:client  # Defined in `package.json` as `npx openapi-typescript docs/openapi.yaml -o web/src/generated/client.ts`

# Include generated types in `tsconfig.json`:
# "include": ["web/src/generated/client.ts"]
```
Generated types are committed to the repository to avoid build-time dependency on the backend spec—updated only via CI.

### System-Level Prerequisites

| Tool | Installation Method | Notes |
|------|---------------------|-------|
| Python 3.11+ | `pyenv`, `apt`, `brew` | Required for `openapi-spec-validator` and local `server.py` testing. |
| Node.js 18+ | `nvm`, `brew`, `apt` | Required for `openapi-typescript`, `swagger-cli`, and frontend tooling. |
| Docker | `brew`, `apt`, `winget`, Docker Desktop | Required for containerized Swagger UI and `docker-compose` services. |
| `openapi-generator-cli` | `npm`, Docker, or standalone JAR | Used for server/client stub generation in CI and local dev. |

All tools are version-pinned in `.tool-versions` (for `asdf`) and `Dockerfile` (for `python:3.11-slim`).
