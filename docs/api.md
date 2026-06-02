# API Documentation

This document provides a comprehensive, standardized reference for the backend API exposed by this full-stack application. The backend is implemented in Python using FastAPI, serving both the REST API and, in production, static frontend assets (orchestrated by Nginx). The API adheres to RESTful principles, utilizes JSON for request and response payloads, and integrates with a persistent data store. Containerization via Docker ensures consistent deployment.

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

The API serves as the backend for a frontend application located in the `web/` directory. It exposes multiple RESTful endpoints, including resource management, utility functions, and health checks. Endpoints are versioned under `/api/v1`.

Requests are handled over HTTP/1.1. The service is designed to be largely stateless, with session management and security typically handled via tokens. The backend is built with Python and leverages FastAPI for its asynchronous capabilities and automatic data validation.

---

## Authentication & Authorization

Authentication is primarily handled through Bearer tokens, which must be included in the `Authorization` HTTP header:

```
Authorization: Bearer <token>
```

The system employs JWT (JSON Web Tokens) for issuing tokens upon successful user authentication. These tokens have a configurable Time To Live (TTL), adjustable via environment variables. The backend validates these tokens using a secret key, which should be managed securely as an environment variable.

While some endpoints, such as basic health checks, are publicly accessible, most require a valid authentication token. Certain sensitive endpoints may also enforce role-based access control (e.g., requiring an "admin" role). Access control logic is embedded within the backend code (`server.py`), likely utilizing FastAPI's dependency injection system or custom middleware.

---

## Base URL

The base URL for the API varies depending on the deployment environment:

| Environment | Base URL                     | Notes                                                    |
|-------------|------------------------------|----------------------------------------------------------|
| Development | `http://localhost:8000`      | Used when running locally, often with `uvicorn`.         |
| Staging     | `https://staging.example.com/api/v1` | Example URL for a staging environment.                   |
| Production  | `https://api.example.com/api/v1` | Example URL for the production environment.              |

In a local development setup, the backend (e.g., running via `uvicorn` on port `8000`) and the frontend development server (likely Vite, running on a different port like `5173`) operate independently. The `docker-compose.yml` file facilitates co-orchestration of these services. In production, `web/nginx.conf` details how Nginx acts as a reverse proxy, routing API requests to the backend service and serving static frontend assets.

---

## HTTP Status Codes

The API utilizes standard HTTP status codes to indicate the outcome of requests:

| Code | Meaning          | Description                                                                                                |
|------|------------------|------------------------------------------------------------------------------------------------------------|
| `200` | OK               | The request was successful. Used for successful GET, PUT, PATCH, or DELETE operations.                     |
| `201` | Created          | The resource was successfully created. Typically returned after a successful POST request.                 |
| `204` | No Content       | The request was successful, but there is no content to return in the response body. Often used for DELETE. |
| `400` | Bad Request      | The client sent an invalid request (e.g., malformed JSON, missing required fields).                         |
| `401` | Unauthorized     | Authentication is required or has failed. The client needs to provide valid credentials.                  |
| `403` | Forbidden        | The client is authenticated but does not have permission to access the requested resource.                  |
| `404` | Not Found        | The requested resource or API endpoint does not exist.                                                      |
| `409` | Conflict         | The request could not be completed due to a conflict with the current state of the resource (e.g., duplicate entry). |
| `429` | Too Many Requests| The client has exceeded a rate limit. The server is temporarily withholding.                                |
| `500` | Internal Server Error | An unexpected error occurred on the server, preventing the request from being fulfilled.                |

Error responses are typically returned in a JSON format, providing details such as an error code, a human-readable message, and potentially stack traces or additional context for debugging.

---

## Request & Response Format

Unless otherwise specified (e.g., for file uploads), all API requests and responses utilize JSON as the data interchange format. Clients should set the `Content-Type` header to `application/json` for requests that include a body.

### Request Format

*   **Body**: For `POST`, `PUT`, and `PATCH` requests, the request body must contain a valid JSON object.
*   **Fields**: Required fields must be included as defined by the API schema for each endpoint. Optional fields may be omitted or explicitly set to `null`.
*   **Validation**: The backend performs robust input validation based on data schemas, likely defined using Pydantic models within FastAPI, ensuring data integrity and adherence to expected formats.

**Example `POST` request body for user creation:**

```json
{
  "email": "user@example.com",
  "password": "secure_password123",
  "username": "newuser"
}
```

### Response Format

*   **Success**: Successful responses will contain a JSON payload representing the requested resource or the result of the operation.
*   **Error**: Error responses include a JSON object detailing the error, as described in the [Error Handling](#error-handling) section.

**Example successful `GET` response for a user resource:**

```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "email": "user@example.com",
  "username": "newuser",
  "created_at": "2023-10-27T10:00:00Z",
  "updated_at": "2023-10-27T10:00:00Z"
}
```

---

## Endpoints

The API exposes a collection of RESTful endpoints, versioned under `/api/v1`. Below is a description of the available endpoints, their HTTP methods, expected request bodies, and typical response payloads.

*(Note: The exact list and detail of endpoints are inferred and may require validation against the running application or OpenAPI specification.)*

### Authentication Endpoints

#### `POST /api/v1/auth/register`

*   **Description**: Registers a new user in the system.
*   **Request Body**:
    ```json
    {
      "email": "string (required)",
      "password": "string (required)",
      "username": "string (required)"
    }
    ```
*   **Responses**:
    *   `201 Created`: User registered successfully. Returns user details excluding sensitive information like password hash.
        ```json
        {
          "id": "uuid",
          "email": "string",
          "username": "string",
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
    *   `400 Bad Request`: Invalid email format, weak password, or missing required fields.
    *   `409 Conflict`: Email or username already exists.

#### `POST /api/v1/auth/login`

*   **Description**: Authenticates a user and returns an access token.
*   **Request Body**:
    ```json
    {
      "email": "string (required)",
      "password": "string (required)"
    }
    ```
*   **Responses**:
    *   `200 OK`: User successfully authenticated. Returns an access token.
        ```json
        {
          "access_token": "string (JWT)",
          "token_type": "bearer"
        }
        ```
    *   `401 Unauthorized`: Invalid email or password.

#### `POST /api/v1/auth/refresh`

*   **Description**: Refreshes an expired access token using a refresh token (if implemented).
*   **Request Body**:
    ```json
    {
      "refresh_token": "string (required)"
    }
    ```
*   **Responses**:
    *   `200 OK`: Token refreshed successfully. Returns a new access token.
        ```json
        {
          "access_token": "string (JWT)",
          "token_type": "bearer"
        }
        ```
    *   `401 Unauthorized`: Invalid or expired refresh token.

### User Management Endpoints

#### `GET /api/v1/users/me`

*   **Description**: Retrieves the profile information for the currently authenticated user. Requires Bearer token authentication.
*   **Responses**:
    *   `200 OK`: Returns the current user's profile.
        ```json
        {
          "id": "uuid",
          "email": "string",
          "username": "string",
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
    *   `401 Unauthorized`: Authentication token is missing or invalid.
    *   `404 Not Found`: User associated with the token could not be found.

#### `PUT /api/v1/users/me`

*   **Description**: Updates the profile information for the currently authenticated user. Requires Bearer token authentication.
*   **Request Body**: (Fields are optional, only include those to be updated)
    ```json
    {
      "email": "string (optional)",
      "username": "string (optional)"
    }
    ```
*   **Responses**:
    *   `200 OK`: User profile updated successfully. Returns the updated user profile.
        ```json
        {
          "id": "uuid",
          "email": "string",
          "username": "string",
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
    *   `400 Bad Request`: Invalid input data (e.g., invalid email format).
    *   `401 Unauthorized`: Authentication token is missing or invalid.
    *   `409 Conflict`: If the email or username is already in use by another user.

#### `DELETE /api/v1/users/me`

*   **Description**: Deletes the account of the currently authenticated user. Requires Bearer token authentication.
*   **Responses**:
    *   `204 No Content`: User account successfully deleted.
    *   `401 Unauthorized`: Authentication token is missing or invalid.

### System Endpoints

#### `GET /api/v1/health`

*   **Description**: Checks the health status of the API service. This endpoint is typically publicly accessible.
*   **Responses**:
    *   `200 OK`: The API service is healthy.
        ```json
        {
          "status": "ok"
        }
        ```

#### `GET /api/v1/openapi.json`

*   **Description**: Provides the OpenAPI specification for the API in JSON format. This is useful for generating client SDKs or exploring the API interactively (e.g., via Swagger UI).
*   **Responses**:
    *   `200 OK`: Returns the OpenAPI JSON document.

#### `GET /api/v1/docs`

*   **Description**: Renders the interactive API documentation (Swagger UI) in the browser.
*   **Responses**:
    *   `200 OK`: Serves the HTML interface for exploring the API.

*(Additional endpoints for specific application features like managing resources, configurations, or data might exist and should be documented here as they are identified.)*

---

## Error Handling

The API employs a standardized error response format to provide clear and actionable feedback to clients when issues arise.

When an error occurs, the server will typically respond with an appropriate HTTP status code (e.g., `400`, `401`, `404`, `500`). The response body will be a JSON object containing details about the error.

**Example Error Response:**

```json
{
  "detail": [
    {
      "type": "string (e.g., 'validation_error', 'authentication_error')",
      "msg": "string (human-readable error message)",
      "loc": ["string (field name or path)"],
      "ctx": { "key": "value" } // Optional context for the error
    }
  ]
}
```

*   **`detail`**: An array containing one or more error objects.
*   **`type`**: A machine-readable code identifying the category of the error.
*   **`msg`**: A human-readable description of the error.
*   **`loc`**: Specifies the location of the error, often indicating the field that caused the validation failure.
*   **`ctx`**: Provides additional context-specific information about the error, useful for debugging.

---

## OpenAPI Specification

The API's structure, endpoints, request/response schemas, and security definitions are formally documented using the OpenAPI 3.0 specification. This specification is available at:

*   **File Location**: `docs/openapi.yaml`
*   **Endpoint**: `GET /api/v1/openapi.json`

This OpenAPI document serves as the single source of truth for the API's design and can be used with various tools for:

*   Generating interactive documentation (e.g., Swagger UI, Redoc).
*   Generating client SDKs in multiple programming languages.
*   Automated testing and validation.

---

## Install & Setup Requirements

To develop, run, or contribute to this project, you will need to set up your local development environment. This involves installing specific dependencies for both Python (backend) and JavaScript (frontend).

### Backend (Python)

1.  **Python Installation**: Ensure you have Python 3.11 installed. You can download it from [python.org](https://www.python.org/downloads/) or use a version manager like `pyenv`.
2.  **Virtual Environment**: It is highly recommended to use a Python virtual environment to manage project dependencies.
    *   **Creation**:
        ```bash
        python -m venv .venv
        ```
    *   **Activation**:
        *   **Linux/macOS**:
            ```bash
            source .venv/bin/activate
            ```
        *   **Windows**:
            ```bash
            .venv\Scripts\activate
            ```
3.  **Install Python Dependencies**: Once the virtual environment is activated, install the required Python packages using pip:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` should be generated or maintained to list all necessary backend packages, including FastAPI, Uvicorn, Pydantic, etc.*

### Frontend (JavaScript/Node.js)

1.  **Node.js and npm/yarn Installation**: Ensure you have Node.js (LTS version recommended) and a package manager (npm or yarn) installed. You can download Node.js from [nodejs.org](https://nodejs.org/).
2.  **Install Frontend Dependencies**: Navigate to the `web/` directory and install the project's JavaScript dependencies:
    ```bash
    # Using npm
    cd web
    npm install

    # Using yarn
    cd web
    yarn install
    ```

### Docker and Docker Compose

For containerized development and deployment, Docker and Docker Compose are utilized.

1.  **Docker Installation**: Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/). Ensure the Docker daemon is running.
2.  **Docker Compose**: Docker Desktop includes Docker Compose.
3.  **Running with Docker Compose**: To build and run the application containers locally:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker images (if not already built) and start the backend, frontend, and any other services defined in `docker-compose.yml`.

### Environment Variables

Certain configurations, especially sensitive ones like secret keys for JWT or database credentials, are managed through environment variables. Ensure these are set correctly in your local environment or within your `.env` file (if used and added to `.gitignore`). Common variables might include:

*   `DATABASE_URL`: Connection string for the database.
*   `SECRET_KEY`: A strong, random secret key for signing JWTs.
*   `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for access tokens in minutes.

The `Dockerfile` indicates a base image of `python:3.11-slim`, suggesting a minimal Python environment for the backend container. No additional system packages are explicitly listed as being installed during the Docker build process, implying that Python dependencies are managed solely through `pip`.
