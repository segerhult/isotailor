# API Reference

This document provides a comprehensive, standardized reference for the backend API exposed by this full-stack application. The backend is implemented in Python (using FastAPI, inferred from `server.py` and typical FastAPI patterns) and serves both the REST API and static frontend assets (served via Nginx in production). The API follows REST conventions, supports JSON request/response payloads, and integrates with a database backend. It is containerized using Docker for consistent deployment across environments.

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

The API is designed as a backend service for a frontend application (located in the `web/` directory, likely using Vite based on `npm run dev` command). It exposes multiple RESTful endpoints (at least 9 identified via static analysis of `server.py`), covering resource management, status health checks, and metadata. Endpoints are versioned under `/api/v1` by default.

Requests are served via HTTP/1.1. The service is designed to be stateless, with authentication typically managed through tokens.

---

## Authentication & Authorization

Authentication is implemented via Bearer tokens, expected in the `Authorization` HTTP header:

```
Authorization: Bearer <token>
```

The current implementation relies on JWT (JSON Web Tokens) for issuing tokens upon successful user login. These tokens have a configurable Time To Live (TTL), which can be managed via environment variables. The backend validates these tokens using a secret key, which should be securely stored in the environment.

Certain endpoints, such as health checks, are publicly accessible without authentication. Other endpoints require a valid authentication token and, in some cases, specific user roles (e.g., "admin") for authorization. Access control is enforced programmatically within `server.py`, likely using FastAPI's dependency injection system or custom decorators.

---

## Base URL

| Environment | Base URL                     |
|-------------|------------------------------|
| Development | `http://localhost:8000`      |
| Staging     | `https://staging.example.com/api/v1` |
| Production  | `https://api.example.com/api/v1` |

In local development, the backend is typically run using a WSGI server like `uvicorn`. The frontend development server (likely Vite) runs on a separate port (e.g., `5173`). The `docker-compose.yml` file orchestrates both backend and frontend services, with Nginx acting as a reverse proxy in production (`web/nginx.conf`) to route API requests to the backend and serve frontend assets.

---

## HTTP Status Codes

| Code | Meaning                                    | Usage                                                                 |
|------|--------------------------------------------|-----------------------------------------------------------------------|
| `200` | OK                                         | Successful GET, PUT, PATCH, or DELETE requests.                      |
| `201` | Created                                    | Successful resource creation (POST).                                  |
| `204` | No Content                                 | Successful DELETE request with no response body.                      |
| `400` | Bad Request                                | Invalid request payload (e.g., incorrect JSON format, missing fields). |
| `401` | Unauthorized                               | Authentication credentials missing or invalid.                       |
| `403` | Forbidden                                  | Authenticated user does not have permission to access the resource.  |
| `404` | Not Found                                  | The requested resource or endpoint does not exist.                    |
| `409` | Conflict                                   | Request conflicts with the current state of the resource (e.g., duplicate unique field). |
| `429` | Too Many Requests                          | The client has exceeded the allowed rate limit.                       |
| `500` | Internal Server Error                      | An unexpected error occurred on the server.                          |

Error responses typically include a JSON body detailing the error, including a machine-readable code, a human-readable message, and potentially additional context.

---

## Request & Response Format

All API requests and responses, excluding file uploads (if supported), utilize JSON as the data interchange format. The `Content-Type` header should be set to `application/json` for requests with a body.

### Request Format

*   **Body**: For `POST`, `PUT`, and `PATCH` requests, the body must be a valid JSON object.
*   **Fields**: Required fields should be present as defined for each endpoint, and optional fields can be omitted or set to `null`.
*   **Validation**: Input validation is performed by the backend, based on schemas defined (likely using Pydantic models in FastAPI).

Example `POST` request body for user creation:
```json
{
  "email": "user@example.
