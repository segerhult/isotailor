# OpenAPI

## Specification Files

The project's OpenAPI 3.0 specification is centrally defined in `docs/openapi.yaml`. This YAML file serves as the definitive contract for all API interactions between the frontend and backend components of this fullstack application. It meticulously details each endpoint, including its HTTP method, path parameters, query parameters, request body schemas, response schemas, and security requirements. The specification is written using the OpenAPI Specification v3.0.3 standard.

This file is crucial for maintaining API consistency across the development lifecycle. It is referenced by the CI/CD pipeline (`.github/workflows/main.yml`) to ensure that the documented API accurately reflects the implementation in `server.py` and is consumed correctly by the frontend in `web/src/api.js`. Any modification to the backend API surface must be mirrored in `docs/openapi.yaml` to prevent inconsistencies.

## Detected Endpoints (Heuristic)

Based on the frontend's API client (`web/src/api.js`) and the backend logic (`server.py`), the following RESTful endpoints are exposed under the `/api` base path:

| Method   | Path                            | Description                                                                                              |
|----------|---------------------------------|----------------------------------------------------------------------------------------------------------|
| `GET`    | `/api/health`                   | Checks the operational status of the backend service. This endpoint is typically used for health checks. |
| `GET`    | `/api/default-software`         | Retrieves a predefined list of default software packages, likely used for populating UI options.       |
| `GET`    | `/api/uploads`                  | Lists all user uploads, potentially with support for filtering and pagination.                             |
| `POST`   | `/api/uploads`                  | Initiates a new upload process, likely returning an ID for subsequent operations.                          |
| `GET`    | `/api/uploads/{id}`             | Fetches detailed metadata for a specific upload identified by its unique ID.                              |
| `PUT`    | `/api/uploads/{id}/software`    | Updates the software configurations associated with a particular upload.                                  |
| `GET`    | `/api/uploads/{id}/manifest`    | Retrieves a manifest file detailing the processed content of a specific upload.                          |
| `GET`    | `/api/uploads/{id}/iso`         | Provides access to download the generated ISO artifact for a completed upload.                            |
| `DELETE` | `/api/uploads/{id}`             | Removes a specific upload and its associated data from the system.                                        |

Most endpoints are expected to use `application/json` for request and response bodies, with the exception of `/api/uploads/{id}/iso`, which serves binary data.

## Request and Response Schemas

The `components/schemas` section within `docs/openapi.yaml` defines reusable data models. Key schemas include:

*   **`Upload`**: Represents an individual upload, containing fields like `id`, `filename`, `status` (e.g., `pending`, `processing`, `completed`, `failed`), `created_at`, `updated_at`, and potentially `software` configurations and `size`.
*   **`SoftwarePackage`**: Describes a software package with attributes such as `id`, `name`, `version`, and an optional `description`.
*   **`HealthCheck`**: A simple schema indicating the service's health status, e.g., `{"status": "healthy", "timestamp": "..."}`.

A standardized `Error` schema is also defined to provide consistent error reporting across API responses, including `code`, `message`, and optional `details`.

## Authentication & Authorization

With the exception of the public `/api/health` endpoint, all other API endpoints require authentication. The expected authentication mechanism is JWT (JSON Web Tokens) passed in the `Authorization` header with the `Bearer` scheme. The `docs/openapi.yaml` includes a `securitySchemes: { bearerAuth: { type: http, scheme: bearer, bearerFormat: JWT }}` definition. Authorization, beyond authentication, is enforced for sensitive operations, ensuring users can only access or modify their own uploads or those explicitly shared with them.

## Path and Parameter Conventions

*   **Path Parameters**: Utilize descriptive, lowercase identifiers such as `{id}` to represent unique resource identifiers.
*   **Query Parameters**: Endpoints like `GET /api/uploads` support parameters for pagination (`limit`, `offset`) and filtering (e.g., `status`, `created_from`, `created_to`).
*   **Data Formats**: Timestamps are consistently formatted using ISO 8601 UTC (e.g., `YYYY-MM-DDTHH:mm:ss.SSSZ`). File uploads are initiated by submitting metadata as JSON to `/api/uploads`, with the actual file data typically transferred via a presigned URL obtained from the response.

## Integration with Frontend

The frontend application, situated within the `web/` directory, utilizes the API defined by `docs/openapi.yaml`. The `web/src/api.js` file likely employs a library like Axios to interact with the backend. Frontend API client methods (e.g., `getUploads()`, `createUpload()`) directly correspond to the operations defined in the OpenAPI specification. Interceptors in the API client handle tasks such as automatically attaching JWT tokens to outgoing requests and processing standardized error responses from the backend. The frontend also leverages endpoints like `/api/default-software` for UI elements and `/api/uploads/{id}/manifest` to display processed results.

## Swagger UI Integration

The OpenAPI specification is intended to be served interactively via Swagger UI. This documentation portal, often accessible at a path like `/docs` within the frontend application, allows developers and users to explore and test the API. The integration is typically handled by serving a static HTML file (`web/index.html`) via Nginx (`web/nginx.conf`), which in turn renders the content from `docs/openapi.yaml`. The CI/CD pipeline (`.github/workflows/main.yml`) ensures that the `openapi.yaml` file is kept up-to-date and deployed, synchronizing the documentation with the live API.

## Generating Client SDKs & Testing

The `docs/openapi.yaml` file serves as a foundation for generating client SDKs for various languages (e.g., TypeScript clients using `openapi-typescript`, Python clients) and for creating automated tests. It is also a key artifact for contract testing, ensuring that the frontend and backend adhere to the agreed-upon API contract.

To validate and visualize the spec locally:
```bash
# Install swagger-cli globally via npm
npm install -g @apidevtools/swagger-cli

# Validate the OpenAPI specification
swagger-cli validate docs/openapi.yaml

# Serve Swagger UI locally (accessible at http://localhost:8080)
swagger-cli serve docs/openapi.yaml --proxy server.py
```
Or, using Docker for a self-contained Swagger UI environment:
```bash
docker pull swaggerapi/swagger-ui
# Mount the docs directory and expose the Swagger UI port
docker run -p 8080:8080 -v $(pwd)/docs:/docs swaggerapi/swagger-ui -R /docs/openapi.yaml
```

## Maintaining the Spec

To ensure the OpenAPI specification remains accurate and valuable, the following practices are recommended:

*   **Update `docs/openapi.yaml` Proactively**: Any changes to API endpoint paths, methods, request/response structures, or parameter definitions in `server.py` must be reflected in `docs/openapi.yaml` *before* merging the corresponding backend changes.
*   **Test Spec Against Implementation**: Regularly validate the OpenAPI specification against the running backend. Tools like Swagger UI are useful for manual testing, and automated contract tests should be established.
*   **Add Examples**: For complex operations, error responses, or asynchronous workflows, include explicit examples within the `examples` field of schema definitions in `docs/openapi.yaml` to clarify usage.
*   **Document Extensions**: If rate limiting or other non-standard API behaviors are implemented, document them using OpenAPI extensions (e.g., `x-rate-limit`).

## Install Requirements

While no specific installation is required to *view* the final `openapi.yaml`, local development and validation benefit from dedicated tooling.

### Python-based Tools:
For Python environments, use `pip` to install validation and generation libraries:
```bash
pip install openapi-spec-validator openapi-core
# Then validate using:
openapi-spec-validator docs/openapi.yaml
```

### Node.js-based Tools (CLI):
For command-line validation and serving of the specification, use `npm` (or `yarn`, `pnpm`) to install the `swagger-cli`:
```bash
npm install -g @apidevtools/swagger-cli
# Then validate using:
swagger-cli validate docs/openapi.yaml
```

### Docker-based Preview:
If Docker is installed on your system, you can spin up a Swagger UI instance to preview the specification:
```bash
# Pull the latest Swagger UI image
docker pull swaggerapi/swagger-ui

# Run a container, mounting your local docs directory
# This command serves the UI on port 8080 and assumes openapi.yaml is in './docs'
docker run -p 8080:8080 -v $(pwd)/docs:/docs swaggerapi/swagger-ui -R /docs/openapi.yaml
```

By diligently maintaining and utilizing the `docs/openapi.yaml` file, the project ensures robust API documentation, facilitates frontend-backend integration, and supports automated tooling across the fullstack development process.
