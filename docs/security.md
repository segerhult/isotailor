# Security

## Overview

This application is a fullstack web platform composed of a Python-based backend API server (`server.py`) and a Vue.js frontend (`web/`), containerized using Docker for deployment consistency and isolation. The architecture follows a conventional three-tier model: the frontend serves the user interface via an Nginx reverse proxy (`web/nginx.conf`), while the backend exposes a RESTful API with nine documented endpoints (as per `docs/openapi.yaml`), implemented in Python 3.11 and served using a WSGI-compatible server (e.g., `gunicorn` or `uvicorn`, though not yet specified in `server.py`; see [Known Gaps](#known-gaps)).

### Authentication & Authorization
Currently, **no explicit authentication mechanism is implemented** in the codebase. The backend (`server.py`) exposes endpoints without any built-in JWT, OAuth, session, or API key validation, and the frontend (`web/src/api.js`) makes unauthenticated HTTP requests to these endpoints. This creates a critical exposure vector: any client capable of reaching the API can read, write, or modify data unless additional security layers (e.g., network isolation, reverse proxy middleware, or ingress-level controls) are enforced externally.

The absence of authentication also implies:
- **No user role model**: All clients (including browsers, scripts, or malicious actors) are treated identically.
- **No input ownership validation**: Write operations (e.g., `POST`, `PUT`, `DELETE`) cannot be attributed to a specific user, making audit trails and data provenance impossible.
- **Vulnerable to CSRF, IDOR, and injection attacks**: Without authentication tokens, CSRF protections, or parameterized queries, the backend is highly susceptible to exploitation.

For production deployment, authentication must be implemented using a modern, standards-compliant framework such as `authlib` (for OAuth2/JWT) or `python-jose`, with tokens issued and validated via middleware. The frontend should store tokens securely (e.g., HTTP-only cookies) and never in `localStorage` or `sessionStorage`.

### Data Protection
No encryption is currently applied at rest or in transit:
- **In-transit**: While TLS termination is expected to be handled by a reverse proxy or load balancer (e.g., Nginx with HTTPS enabled via `web/nginx.conf`), the `nginx.conf` file provided does not enforce HTTPS or HTTP Strict Transport Security (HSTS). Moreover, the Dockerfile does not include certificate management (e.g., Let’s Encrypt), and `docker-compose.yml` does not define TLS-related environment variables or volume mounts for certificates.
- **At-rest**: Sensitive data (e.g., API keys, user credentials, PII) stored in databases or files is not encrypted. If the backend uses SQLite (default in many Flask/FastAPI templates) or writes logs to disk, no encryption or redaction is evident in `server.py`.

Additionally:
- Secrets are not managed via environment variables or secure vaults (e.g., AWS Secrets Manager, HashiCorp Vault). Hardcoded credentials (e.g., in `server.py` or `web/.env`) would be a severe violation of security best practices.
- The `web/src/api.js` file does not implement request/response sanitization or CSRF token injection for same-origin or cross-origin API calls, increasing the risk of Cross-Site Request Forgery (CSRF) or Cross-Site Scripting (XSS) attacks.

### Input Validation & Sanitization
The backend endpoints lack structured input validation:
- Request bodies, query parameters, and headers are not validated against an OpenAPI schema prior to processing.
- SQL or NoSQL injection risks persist if queries are constructed via string interpolation instead of parameterized statements (which are not visible in the provided context but are highly probable without a framework like SQLAlchemy or Prisma).
- The frontend does not validate user input client-side before submission, increasing the attack surface for XSS (e.g., via malicious HTML in form fields).

## Vulnerability Management

### Dependency Scanning & Management
Dependencies for both backend (Python) and frontend (JavaScript) are managed using their respective package managers:
- **Python**: Installed via `pip`, using `requirements.txt` or `pyproject.toml`. However, no `requirements.txt` is visible in the repo root—its absence increases risk, as version pinning may be inconsistent or outdated. Run `pip freeze > requirements.txt` to lock dependencies and prevent supply-chain attacks from unpinned versions.
- **JavaScript**: Managed via `npm`, using `web/package.json` and `web/package-lock.json`. Lockfiles are present and should be committed to ensure reproducible builds.

#### Automated Scanning
The CI pipeline (`.github/workflows/main.yml`) must include dependency scanning steps using:
- `snyk test` or `pip-audit` for Python.
- `npm audit` or `snyk` for JavaScript.
- Static Application Security Testing (SAST) for `server.py` (e.g., `bandit`) and Vue.js (e.g., `eslint-plugin-vue-scoped-css` for insecure patterns).

A `.dockerignore` and `web/.dockerignore` are present and correctly configured to exclude unnecessary files (e.g., `node_modules`, `.git`, test files), reducing the attack surface in container images.

#### Image Hardening
The Dockerfile (`python:3.11-slim`) uses a minimal base image, which is good practice. However:
- The image is built as `root` by default, violating the principle of least privilege. A non-root user should be added and specified via `USER` directive.
- No multi-stage build is visible, which may bloat the final image with build-time dependencies (e.g., compilers), increasing the attack surface.
- No CVE scanning (e.g., `trivy`, `grype`) is integrated into CI, despite the Dockerfile’s presence.

### Reporting Vulnerabilities
There is no documented process for reporting or remediating security issues. A `SECURITY.md` file must be created to outline:
- Supported versions and lifecycle.
- Contact information for security disclosures (e.g., `security@domain.com` or a private GitHub issue template).
- Expected response timelines and acknowledgment policies.

## Install Requirements

### Prerequisites
Before installing, ensure the following system-level dependencies are present:
- **Docker Engine ≥ 24.0** and **Docker Compose ≥ 2.20** (for containerized deployments).
- **Python ≥ 3.11** (with `pip ≥ 22.3`) and **Node.js ≥ 18.x** (with `npm ≥ 9.x`) for local development.

### Backend Installation (Python)
1. Clone the repository:
   ```bash
   git clone https://github.com/<org>/<repo>.git
   cd <repo>
   ```
2. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt  # or use `pip install .` if `pyproject.toml` is present
   ```
   If `requirements.txt` does not exist, generate it via:
   ```bash
   pip freeze > requirements.txt
   ```
   This ensures deterministic builds and mitigates risks from mutable dependency versions.

### Frontend Installation (JavaScript)
1. Navigate to the `web/` directory:
   ```bash
   cd web
   ```
2. Install dependencies:
   ```bash
   npm ci  # preferred for CI (uses package-lock.json)
   # or
   npm install
   ```

### Docker-Based Deployment
1. Build and run via Docker Compose:
   ```bash
   docker-compose build
   docker-compose up
   ```
2. For production, update `web/nginx.conf` to:
   - Enforce HTTPS (redirect HTTP to HTTPS).
   - Enable HSTS headers.
   - Set secure proxy headers (`X-Forwarded-Proto`, `X-Forwarded-For`).
   - Limit request size (`client_max_body_size`) to prevent DoS attacks.
3. Run container scanning:
   ```bash
   docker scan <image-name>
   # or use Trivy
   trivy image <image-name>
   ```

### Environment Configuration
Never hardcode secrets. Use `.env` files (excluded via `.gitignore`) and inject them at runtime:
- Backend: Load via `os.environ.get("SECRET_KEY")` in `server.py`.
- Frontend: Use Vite’s `import.meta.env.VITE_API_URL` (never expose secrets in frontend builds).

## Known Gaps & Recommendations

| Area | Risk | Action |
|------|------|--------|
| Missing Authentication | Critical | Integrate OAuth2/JWT or session-based auth. |
| No TLS Enforcement | High | Configure Nginx for HTTPS and HSTS. |
| No Dependency Scanning in CI | High | Add `snyk`/`pip-audit` to `main.yml`. |
| Non-Root Container User | Medium | Add `RUN useradd -m appuser && USER appuser` to Dockerfile. |
| No Security Headers | Medium | Add headers (`Content-Security-Policy`, `X-Frame-Options`) in Nginx. |
| No `SECURITY.md` | Medium | Create and document vulnerability reporting process. |
| Unvalidated Input | Critical | Use `pydantic` for backend validation; implement client-side validation. |

This document will be updated in tandem with security enhancements to the codebase. Until then, **this application is not production-ready** and should not handle sensitive data.
