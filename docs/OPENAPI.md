# OpenAPI Specification

This document details the OpenAPI 3.0 specification for the project's API. All API interactions between the frontend and backend components are defined and governed by this specification.

## Specification Files

The primary OpenAPI 3.0 specification file for this project is located at `docs/openapi.yaml`. This file serves as the definitive contract for the API, meticulously detailing each endpoint, its HTTP method, path parameters, query parameters, request body schemas, response schemas, and security requirements. The specification adheres to the OpenAPI Specification v3.0.3 standard.

This centralized specification is critical for maintaining API consistency throughout the development lifecycle. It is referenced by the CI/CD pipeline in `.github/workflows/main.yml` to ensure that the documented API accurately reflects the implementation in `server.py` and is correctly consumed by the frontend in `web/src/api.js`. Any modifications to the backend API surface must be mirrored in `docs/openapi.yaml` to prevent discrepancies.

## Detected Endpoints (Heuristic)

Based on the frontend's API client (`web/src/api.js`) and implied backend logic (`server.py`), the following RESTful endpoints are exposed under the `/api` base path:

| Method   | Path                            | Description                                                                                                                      |
|----------|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `GET`    | `/api/health`                   | Checks the operational status of the backend service. This endpoint is typically used for health checks and monitoring.            |
| `GET`    | `/api/default-software`         | Retrieves a predefined list of default software packages. This is likely used to populate dropdowns or configuration options in the UI. |
| `GET`    | `/api/routes`                   | Retrieves a list of available routes, potentially for dynamic navigation or configuration within the application.                  |
| `GET`    | `/api/uploads`                  | Lists all user uploads. This endpoint is expected to support query parameters for filtering (e.g., by status, date) and pagination. |
| `POST`   | `/api/uploads`                  | Initiates a new upload process. This typically involves submitting upload metadata and may return an ID for subsequent operations. |
| `GET`    | `/api/uploads/search${qs`       | Searches for uploads based on provided query parameters (`qs`). The exact parameters are detailed within the OpenAPI spec.          |
| `GET`    | `/api/uploads/{id}`             | Fetches detailed metadata for a specific upload identified by its unique ID (`{id}`).                                          |
| `PUT`    | `/api/uploads/{id}/software`    | Updates the software configurations associated with a particular upload, identified by its unique ID (`{id}`).                    |
| `GET`    | `/api/uploads/{id}/manifest`    | Retrieves a manifest file detailing the processed content or associated data for a specific upload (`{id}`).                  |
| `GET`    | `/api/uploads/{id}/iso`         | Provides a downloadable link or stream for the generated ISO artifact related to a specific upload (`{id}`).                      |
| `DELETE` | `/api/uploads/{id}`             | Removes a specific upload and all its associated data from the system, identified by its unique ID (`{id}`).                      |

It is assumed that most endpoints utilize `application/json` for request and response bodies, with the exception of `GET /api/uploads/{id}/iso`, which is expected to serve binary data.

## Request and Response Schemas

The `docs/openapi.yaml` file defines reusable data models within its `components/schemas` section. These schemas ensure data consistency across API requests and responses. Key expected schemas include:

*   **`Upload`**: Represents an individual upload resource, likely containing fields such as `id`, `filename`, `status` (e.g., `pending`, `processing`, `completed`, `failed`), creation and update timestamps, associated software configurations, and potentially file size.
*   **`SoftwarePackage`**: Describes a software package with attributes like `id`, `name`, `version`, and an optional `description`.
*   **`HealthCheck`**: A simple schema to indicate the service's health status, typically formatted as `{"status": "healthy", "timestamp": "..."}`.
*   **`Error`**: A standardized schema for reporting errors, which would include fields like `code`, `message`, and optional `details` to provide clear error information to clients.

## Authentication & Authorization

The OpenAPI specification (`docs/openapi.yaml`) details the security requirements for the API. Generally, the `/api/health` endpoint is expected to be publicly accessible. All other API endpoints require authentication. The standard mechanism for authentication is **JWT (JSON Web Tokens)**, passed in the `Authorization` header using the `Bearer` scheme. The specification includes a `securitySchemes` definition named `bearerAuth` to reflect this. Beyond authentication, authorization rules are enforced to ensure users can only access or modify resources they are permitted to, such as their own uploads or data explicitly shared with them.

## Path and Parameter Conventions

*   **Path Parameters**: Unique resource identifiers are represented using descriptive, lowercase placeholder names enclosed in curly braces, such as `{id}`.
*   **Query Parameters**: Endpoints like `GET /api/uploads` and `GET /api/uploads/search` are designed to accept query parameters for filtering (e.g., `status`, `created_from`, `created_to`) and pagination (e.g., `limit`, `offset`).
*   **Data Formats**: Dates and timestamps are consistently formatted using the ISO 8601 standard in UTC (e.g., `YYYY-MM-DDTHH:mm:ss.SSSZ`). File uploads are typically initiated by submitting metadata as JSON to `/api/uploads`, with the actual file data often transferred via a presigned URL obtained from the API response.

## Integration with Frontend

The frontend application, located within the `web/` directory, interacts with the backend API as defined by `docs/openapi.yaml`. The `web/src/api.js` file likely uses a JavaScript HTTP client library (such as Axios) to manage these interactions. The methods exposed in `web/src/api.js` (e.g., `getUploads()`, `createUpload()`) directly map to the operations defined in the OpenAPI specification. Frontend API clients are expected to include interceptors that automatically attach JWT tokens to outgoing requests and handle standardized error responses from the backend. Furthermore, the frontend utilizes endpoints detailed in the spec for UI elements, such as fetching default software options from `/api/default-software` or displaying upload manifests from `/api/uploads/{id}/manifest`.

## Swagger UI / API Documentation Portal

The OpenAPI specification serves as the single source of truth for the API surface. It is intended to be rendered interactively via Swagger UI, providing a developer portal for exploring and testing the API. This interactive documentation is typically published at a specific route within the frontend application, often `/docs`. The Nginx configuration file `web/nginx.conf` details how this static documentation, rendered from `docs/openapi.yaml`, is served. The CI/CD pipeline (`.github/workflows/main.yml`) ensures that `docs/openapi.yaml` is kept up-to-date and deployed, synchronizing the documentation with the live API.

## Generating Client SDKs & Contract Testing

The `docs/openapi.yaml` file is a valuable asset for generating client SDKs in various programming languages (e.g., TypeScript clients via `openapi-typescript`, Python clients) and for establishing automated contract tests. It acts as a crucial artifact for ensuring that the frontend and backend adhere to the agreed-upon API contract, preventing integration issues.

To validate and visualize the spec locally:

### Using `swagger-cli`:
```bash
# Install swagger-cli globally via npm
npm install -g @apidevtools/swagger-cli

# Validate the OpenAPI specification
swagger-cli validate docs/openapi.yaml

# Serve Swagger UI locally (accessible at http://localhost:8080 by default)
# This command serves the UI and proxies requests to the backend server.
# Ensure your backend server is running on the host and port expected by the proxy.
swagger-cli serve docs/openapi.yaml --proxy localhost:5000 # Adjust port if necessary
```

### Using Docker for Swagger UI:
This provides a self-contained environment for viewing the API documentation.
```bash
# Pull the latest Swagger UI image
docker pull swaggerapi/swagger-ui

# Run a container, mounting your local docs directory.
# This command serves the UI on port 8080 and assumes openapi.yaml is in the './docs' directory.
docker run -p 8080:8080 -v "${PWD}/docs:/docs" swaggerapi/swagger-ui -R /docs/openapi.yaml
```

## Maintaining the Specification

To ensure the OpenAPI specification remains accurate and useful, adhering to the following practices is essential:

*   **Proactive Updates**: Any changes made to API endpoint paths, HTTP methods, request/response structures, or parameter definitions in `server.py` *must* be reflected in `docs/openapi.yaml` *before* merging the corresponding backend changes.
*   **Validation Against Implementation**: Regularly validate the OpenAPI specification against the running backend. Manual testing via Swagger UI and automated contract tests are recommended.
*   **Inclusion of Examples**: For complex operations, common error scenarios, or asynchronous workflows, include explicit examples within the `examples` field of schema definitions in `docs/openapi.yaml`. This significantly enhances clarity for consumers.
*   **Documentation of Extensions**: If non-standard API behaviors or custom metadata are implemented (e.g., rate limiting, specific processing details), document them within the OpenAPI specification using reserved extensions (e.g., `x-rate-limit`).

## Install Requirements

While no specific installation is required to *view* the final `openapi.yaml` file content, local development and validation benefit from dedicated tooling.

### Python-based Tools:
For Python environments, use `pip` to install necessary validation and generation libraries:
```bash
python -m pip install --upgrade pip
python -m pip install openapi-spec-validator openapi-core
```
After installation, you can validate the specification using:
```bash
openapi-spec-validator docs/openapi.yaml
```

### Node.js-based Tools (CLI):
For command-line validation and serving of the specification, use `npm` (or `yarn`, `pnpm`) to install the `swagger-cli`:
```bash
npm install -g @apidevtools/swagger-cli
```
Then, validate the specification:
```bash
swagger-cli validate docs/openapi.yaml
```

By diligently maintaining and utilizing the `docs/openapi.yaml` file, this project ensures robust API documentation, facilitates seamless frontend-backend integration, and supports automated tooling across the fullstack development lifecycle.
