# OpenAPI

## Specification Files

The OpenAPI 3.0 specification for this project resides at `docs/openapi.yaml`. This file serves as the single source of truth for all RESTful API endpoints exposed by the backend (`server.py`) and consumed by the frontend (`web/src/api.js`). The spec is written in YAML format, aligned with the OpenAPI Specification v3.0.3, and includes comprehensive definitions for paths, methods, request parameters, request/response bodies, security schemes, and data models.

The spec is validated and kept up-to-date as part of the CI/CD pipeline (`.github/workflows/main.yml`). Any changes to the backend route definitions in `server.py`—especially those modifying path signatures, HTTP methods, expected payloads, or response structures—must be reflected in `docs/openapi.yaml` to maintain consistency across documentation, client SDK generation, and testing tooling.

## Detected Endpoints (Heuristic)

The backend implements the following nine RESTful endpoints under the `/api` base path:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Returns the health status of the backend service. Used for readiness and liveness probes. No authentication required. |
| `GET` | `/api/default-software` | Retrieves the list of default software packages preconfigured for new uploads. Typically used to populate a default selection in the UI during upload setup. |
| `GET` | `/api/uploads` | Lists all uploads associated with the authenticated user. Supports pagination and filtering via query parameters (e.g., `?status=pending`, `?limit=10`). Responses include upload metadata such as ID, filename, status, creation timestamp, and associated software configuration. |
| `POST` | `/api/uploads` | Creates a new upload record and returns an upload ID. The request body must include the filename and optional metadata. The actual binary file upload is handled via a separate `PUT`/`POST` to an upload-presigned URL (not covered by this spec but referenced in the response). |
| `GET` | `/api/uploads/{id}` | Retrieves detailed metadata for a specific upload, including status (`pending`, `processing`, `completed`, `failed`), software configuration, and associated tags. Returns a 404 if the upload ID does not exist or is inaccessible. |
| `PUT` | `/api/uploads/{id}/software` | Updates the software configuration associated with a specific upload. The request body contains a JSON object with a `software` array listing selected software packages. Requires the upload to be in `pending` or `failed` state. |
| `GET` | `/api/uploads/{id}/manifest` | Retrieves a structured manifest file (typically JSON) describing the contents, dependencies, and metadata of the finalized upload. Generated only after the upload has been processed and is in `completed` state. |
| `GET` | `/api/uploads/{id}/iso` | Downloads the final ISO artifact associated with the upload. The response is served as `application/octet-stream`. Access is restricted to the owner of the upload or users with explicit share permissions. |
| `DELETE` | `/api/uploads/{id}` | Deletes an upload and its associated metadata. May also trigger cleanup of stored artifacts (e.g., uploaded binary, ISO). Returns 204 No Content on success. May enforce soft-deletion depending on implementation. |

All endpoints expect and return `application/json` payloads unless otherwise specified (e.g., the `/iso` endpoint returns binary data).

## Request and Response Schemas

The `components/schemas` section of `docs/openapi.yaml` defines reusable data structures used across endpoints. Key models include:

### `Upload`
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` (UUID) | Unique identifier of the upload. |
| `filename` | `string` | Original filename provided at creation. |
| `status` | `string` | Current processing status: `pending`, `processing`, `completed`, or `failed`. |
| `created_at` | `string` (ISO 8601 datetime) | Timestamp of upload creation. |
| `updated_at` | `string` (ISO 8601 datetime) | Timestamp of the last status update. |
| `software` | `string[]` | List of software package identifiers selected for this upload. |
| `size` | `integer` (int64, optional) | Size of the uploaded file in bytes. Only present for completed uploads. |

### `SoftwarePackage`
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique identifier of the software package (e.g., `gcc-12`, `vim`). |
| `name` | `string` | Human-readable name (e.g., `GNU Compiler Collection 12`). |
| `version` | `string` | Package version. |
| `description` | `string` | Optional description. |

### `HealthCheck`
| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"healthy"` when available. |
| `timestamp` | `string` (ISO 8601 datetime) | Server time at response generation. |

Error responses follow a consistent structure defined in the `Error` schema:
```yaml
Error:
  type: object
  required: [error]
  properties:
    error:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
          example: "INVALID_INPUT"
        message:
          type: string
          example: "Field 'software' must be an array."
        details:
          type: array
          items:
            type: object
          description: Optional validation fields with localized messages.
```

## Authentication & Authorization

All endpoints—except `/api/health`—require JWT-based authentication via the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are issued by the authentication service (e.g., Auth0, custom OAuth2 provider) and validated by the backend middleware (`server.py`). The OpenAPI spec includes a `securitySchemes` section:
```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

Access control for sensitive operations (e.g., `GET /api/uploads/{id}/iso`, `DELETE /api/uploads/{id}`) enforces ownership or explicit sharing permissions. Unauthorized or forbidden access returns HTTP `401` or `403` with a structured error payload.

## Path and Parameter Conventions

- Path parameters use descriptive, lowercase identifiers (e.g., `{id}` for upload identifiers).
- Query parameters for `GET /api/uploads` support standard pagination: `limit` (default: `20`, max: `100`) and `offset` (default: `0`). Filtering by `status`, `created_from`, and `created_to` (ISO 8601 date) is supported.
- Timestamps in request/response bodies are in UTC and formatted per ISO 8601 (`YYYY-MM-DDTHH:mm:ss.SSSZ`).
- File upload metadata is submitted as JSON, while the binary itself is sent to a temporary presigned URL returned by the `POST /api/uploads` response.

## Integration with Frontend

The frontend (`web/src/api.js`) consumes this API using Axios. Request interceptors attach the user’s JWT token, and response interceptors handle standardized errors (e.g., redirecting on `401`). The `web/src/api.js` module exports methods like `listUploads()`, `createUpload(payload)`, `getUploadManifest(id)`, etc., mirroring the endpoints defined in `openapi.yaml`.

The frontend also uses the `/api/default-software` endpoint to pre-fill configuration forms and relies on `/api/uploads/{id}/manifest` to render the final build output summary.

## Generating Client SDKs & Testing

The `docs/openapi.yaml` file is used to generate TypeScript clients (e.g., via `openapi-typescript` or `openapi-client-axios`) and Python test fixtures (e.g., via `openapi-generator`). It is also referenced in the CI pipeline for contract testing using `pinkpdf` or `openapi-compatibility-validator`.

To validate and visualize the spec locally:
```bash
pip install swagger-cli
swagger-cli validate docs/openapi.yaml
swagger-cli serve docs/openapi.yaml  # Starts a local Swagger UI at http://localhost:8080
```

Alternatively, use Docker to run the Swagger UI container:
```bash
docker run -p 80:8080 -e SWAGGER_JSON=/docs/openapi.yaml -v $(pwd)/docs:/docs swaggerapi/swagger-ui
```

## Maintaining the Spec

As the project evolves, the following practices must be followed:
- **Update `docs/openapi.yaml`** *before* merging backend changes that modify paths, schemas, or behavior.
- **Test spec changes** against the local server (`python server.py`) using Swagger UI or Postman collections derived from the spec.
- **Include sample requests/responses** in the `examples` field where behavior is nontrivial (e.g., error states, async upload flows).
- **Document rate limits and usage quotas** in the `x-rate-limit` extension if enforced.

## Install Requirements

No additional dependencies are required to *use* the OpenAPI spec, but to *generate* or *validate* it, the following tools are recommended:

### For Python-based validation/generation:
```bash
# Install OpenAPI tools using pip
pip install openapi-core openapi-spec-validator

# Validate spec
openapi-spec-validator docs/openapi.yaml
```

### For CLI-based generation and serving (Node.js ecosystem):
```bash
# Using npm
npm install -g @apidevtools/swagger-cli
swagger-cli validate docs/openapi.yaml
```

### For Docker-based preview:
Ensure Docker is installed (via `brew` on macOS, `apt` on Linux, or `winget` on Windows), then run:
```bash
docker pull swaggerapi/swagger-ui
docker run -p 8080:8080 -v $(pwd)/docs:/docs swaggerapi/swagger-ui
```

### Frontend SDK Generation (TypeScript):
```bash
# Using openapi-typescript
npm install -D openapi-typescript
npx openapi-typescript docs/openapi.yaml -o src/generated/client.ts
```

Adherence to these guidelines ensures the spec remains accurate, reliable, and useful for documentation, testing, and client development across the fullstack architecture.
