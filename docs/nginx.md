# Nginx Configuration

## Overview

This repository implements Nginx as a critical component of the application's infrastructure, serving two primary functions within a fullstack architecture: **static file hosting for the Vue 3 frontend** and **reverse proxying for API requests to the Python backend**. Nginx operates at the edge of the service mesh—handling all external HTTP(S) traffic before routing it to the appropriate internal service. This design decouples the frontend and backend layers, improves security posture, centralizes routing logic, and enables scalable deployment patterns.

The Vue 3 frontend is built using Vite (configured in `web/vite.config.js`), which produces a production-ready static distribution (`web/dist/`). This output is served directly by Nginx via the `root` directive in `web/nginx.conf`, ensuring fast, caching-friendly delivery of HTML, JavaScript, CSS, images, and other assets.

For dynamic API interactions (e.g., `/api/users`, `/api/auth/login`), Nginx intercepts requests and forwards them to the Python-based custom API server (`server.py`) running on port `8000`. This reverse proxying avoids browser-enforced CORS restrictions, abstracts network topology from clients, and allows for consistent error handling and logging. Crucially, Nginx resolves the backend service via Docker's internal DNS (`http://backend:8000`), enabling reliable inter-container communication within the `docker-compose.yml` orchestration layer.

The architecture supports multiple environments: local development, CI/CD pipeline validation, and production deployments—each leveraging the same core `web/nginx.conf`, but with environment-specific variations in path resolution, proxy targets, and TLS handling. This consistency minimizes configuration drift and human error.

---

## Configuration File: `web/nginx.conf`

The **canonical source of truth** for Nginx behavior is the file at [`web/nginx.conf`](web/nginx.conf). It defines one or more `server` blocks that respond to HTTP requests on port `80`, and optionally HTTPS on `443` when TLS is enabled. Key structural and behavioral elements include:

- **Static Asset Serving**:  
  The `location /` block serves the compiled Vue application using the `root` directive, pointing to `/usr/share/nginx/html` (the standard location in the Nginx Alpine image). During the `web/Dockerfile` build, Vite’s output (`web/dist/`) is copied into this directory, ensuring that all required assets (including SPA routing support via `try_files $uri /index.html;`) are available.

- **API Proxying**:  
  Requests to paths beginning with `/api/` are forwarded to the backend using `proxy_pass http://backend:8000;`. Here, `backend` is the Docker service name defined in `docker-compose.yml`. Nginx sets standard proxy headers (`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`) to preserve client context and ensure secure routing inside the container network.

- **Error Handling & SPA Routing**:  
  To support client-side routing in Vue, the `location /` block includes `try_files $uri $uri/ /index.html;`. This ensures that requests for non-asset URLs (e.g., `/dashboard`, `/settings/123`) return `index.html`, allowing Vue Router to handle navigation client-side—while still returning `404.html` for truly missing assets.

- **Security & Optimization**:  
  The config includes performance-oriented directives like `gzip on;`, cache headers for static assets (`Location` blocks for `*.js`, `*.css`, `*.png`, etc.), and basic rate limiting via `limit_req_zone` (if defined), all aimed at improving user experience and reducing server load.

> **Important**: Do *not* embed full config excerpts in documentation. Instead, treat `web/nginx.conf` as the single source of truth. All changes to routing, proxying, or security policies should be validated directly in that file and confirmed via `nginx -t` before deployment.

---

## Containerization and Deployment

### Build Strategy

The Nginx server is containerized using the `web/Dockerfile`, which follows a minimal, multi-stage-friendly approach:

- **Base Image**: `nginx:alpine` – selected for its small attack surface, fast startup, and built-in compatibility with production-grade Nginx features (e.g., streaming, SSL, gzip).
- **Asset Copy**: During build, the pre-compiled frontend (`web/dist/`) is copied into `/usr/share/nginx/html`, and `nginx.conf` is placed at `/etc/nginx/conf.d/default.conf`, the default configuration directory for additional server blocks in the Alpine Nginx image.
- **Port Exposure**: The container exposes port `80` for HTTP traffic; HTTPS can be added via volume mounts (see *TLS Termination* below).

### Docker Compose Integration

In `docker-compose.yml`, the Nginx service (typically named `frontend`) depends on the health status of the `backend` service, enforcing a predictable startup order:

- **Service Naming**: The proxy target `http://backend:8000` resolves automatically through Docker’s embedded DNS, using the service name `backend` defined in the same compose file.
- **Health Checks**: The backend must expose a `/health` endpoint (e.g., `GET /health → 200 OK`) for Docker to consider it *healthy* before starting dependent services. Without this, Nginx may fail to proxy requests.
- **Port Mapping**: Port `80` on the host is bound to port `80` in the container (`80:80`), exposing the frontend and proxying API requests transparently to external clients.

> Example minimal service definition (see [`docker-compose.yml`](docker-compose.yml) for full details):
> ```yaml
> frontend:
>   build:
>     context: ./web
>   ports:
>     - "80:80"
>   depends_on:
>     backend:
>       condition: service_healthy
> 
> backend:
>   build: .
>   ports:
>     - "8000:8000"
>   healthcheck:
>     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
>     interval: 10s
>     timeout: 5s
>     retries: 3
> ```

---

## Local Development Setup

### Option 1: Full Containerized Development (Recommended)

The most reliable and reproducible method for local development is via Docker Compose:

```bash
docker-compose up --build
```

This command:

1. Builds the `web/` image using `web/Dockerfile`, which:
   - Runs `npm install && npm run build` as part of the frontend build process (configured in `web/Dockerfile` via `RUN` steps).
   - Copies `dist/` into `/usr/share/nginx/html`.
   - Places `nginx.conf` into the image at `/etc/nginx/conf.d/default.conf`.
2. Builds and starts the Python backend service.
3. Starts the Nginx container *only after* the backend becomes healthy, preventing 502 errors on initial access.

The result: Nginx listens on `http://localhost`, serves the Vue app at the root path, and proxies `/api/*` to `http://localhost:8000`—all within isolated, deterministic container environments.

### Option 2: Manual Local Nginx (Advanced / Debugging)

For deep troubleshooting or local prototyping without Docker, Nginx can be run manually:

1. **Build the Frontend Locally**  
   ```bash
   cd web && npm install && npm run build
   ```

2. **Adjust `web/nginx.conf` Paths**  
   - Change `root /usr/share/nginx/html;` → `root /path/to/repo/web/dist;`
   - Change `proxy_pass http://backend:8000;` → `proxy_pass http://localhost:8000;`

3. **Install Nginx System-Wide**  
   Use your OS’s package manager:
   - **Ubuntu/Debian**:  
     ```bash
     sudo apt-get update && sudo apt-get install nginx
     ```
   - **macOS (Homebrew)**:  
     ```bash
     brew install nginx
     ```
   - **Red Hat/CentOS/Fedora**:  
     ```bash
     sudo yum install nginx
     # or on newer Fedora: sudo dnf install nginx
     ```

   > Nginx depends on system libraries (e.g., `libpcre`, `zlib`, `openssl`). Package managers resolve these automatically.

4. **Validate and Start**  
   ```bash
   nginx -t -c /path/to/web/nginx.conf
   nginx -c /path/to/web/nginx.conf
   ```

> **Warning**: Manual setups are not reproducible across CI or production. Use them only for debugging. Avoid modifying the canonical `web/nginx.conf` permanently—always revert changes before committing.

---

## TLS Termination (Optional Production Enhancement)

The default `web/nginx.conf` assumes HTTP-only traffic. For production use, TLS termination should be enabled securely via Nginx:

### Prerequisites
- SSL/TLS certificates (e.g., from Let’s Encrypt, AWS ACM, or a private CA).
- Secure storage: Never hardcode certificates in Docker images. Use:
  - Docker secrets (in swarm mode).
  - Environment variables injected via CI/CD.
  - Host-mounted volumes (for local VMs/k8s volumes).

### Configuration Steps
1. **Add HTTPS Server Block**  
   In `web/nginx.conf` (or a separate `.conf` included by Nginx):
   ```nginx
   server {
       listen 443 ssl;
       server_name example.com;

       ssl_certificate /etc/nginx/ssl/fullchain.pem;
       ssl_certificate_key /etc/nginx/ssl/privkey.pem;

       # ... rest of config (same as HTTP server)
   }
   ```

2. **Enforce HTTPS Redirection**  
   Add an HTTP-to-HTTPS redirect block:
   ```nginx
   server {
       listen 80;
       server_name example.com;
       return 301 https://$host$request_uri;
   }
   ```

3. **Docker Compose Adjustments**  
   Mount certificates and adjust port bindings:
   ```yaml
   frontend:
     volumes:
       - ./certs:/etc/nginx/ssl:ro
     ports:
       - "80:80"
       - "443:443"
   ```

> **Best Practice**: Prefer offloading TLS at a cloud load balancer (e.g., AWS ALB, GCP HTTPS Load Balancer), which terminates HTTPS before traffic reaches Nginx—reducing complexity and offloading CPU from app containers.

---

## CI/CD Integration and Validation

### Pre-Deployment Linting

The GitHub Actions workflow (`.github/workflows/main.yml`) enforces configuration integrity *before* building or deploying:

- A dedicated step runs:
  ```bash
  docker run --rm -v "$(pwd)/web:/etc/nginx/conf.d" nginx:alpine nginx -t
  ```
  This validates `web/nginx.conf` in a pristine environment, catching syntax errors (e.g., missing semicolons, malformed directives) early.

- If validation fails, the build aborts, preventing broken deployments.

### Build Consistency Guarantees

The build pipeline ensures tight coupling between Nginx config and frontend artifacts:

1. `npm run build` (triggered via `web/Dockerfile`) generates `web/dist/`.
2. `web/Dockerfile` copies *both* the `dist/` directory and `nginx.conf` atomically into the image.
3. This eliminates "config drift" where, for example, an old `nginx.conf` is used with new frontend assets.

---

## Install Requirements

Nginx is **a system-level HTTP server**, not a language-specific dependency. Its installation is decoupled from `pip` or `npm`, and should never be attempted via those tools (e.g., `pip install nginx` installs a Python wrapper, not the server).

### Installation by Environment

| Environment | Method | Command | Notes |
|-------------|--------|---------|-------|
| **Production (Containerized)** | Implicit via Dockerfile base image | `FROM nginx:alpine` | Fully self-contained; no manual install needed. |
| **Production (Bare Metal / VM)** | System package manager | Ubuntu: `sudo apt-get install nginx`<br>macOS: `brew install nginx` | Must manually copy `web/nginx.conf` into `/etc/nginx/conf.d/` and set `root`/`proxy_pass` paths. |
| **Local Development (Non-Docker)** | System package manager | Same as above | Ensure `nginx` is running *after* backend (`server.py`) is started. Use `nginx -s reload` to apply config changes. |
| **CI / Docker Compose** | Implicit in `web/Dockerfile` | — | Docker handles dependency resolution and startup via its `ENTRYPOINT ["nginx", "-g", "daemon off;"]`. |

> **Critical**: Never install Nginx via `pip` or `npm`. These are unrelated projects and will not provide the required binary (`nginx`). Misusing these tools wastes time and confuses debugging.

---

## Troubleshooting Tips

### Common Errors and Resolutions

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| **502 Bad Gateway** | Nginx cannot connect to `backend:8000` | - Verify `docker-compose.yml` service name is `backend`.<br>- Check backend is healthy (`docker-compose ps` + `/health` response).<br>- Ensure `proxy_pass` matches `http://backend:8000`. |
| **403 Forbidden** | Incorrect `root` path or file permissions | - Confirm `web/dist/` exists and contains `index.html`.<br>- Ensure `root` in `nginx.conf` points to correct directory.<br>- Check container filesystem permissions: `docker exec <frontend> ls -l /usr/share/nginx/html`. |
| **SPA routes show 404** (e.g., `/dashboard`) | Missing `try_files` or `root` misconfiguration | - Ensure `location /` uses `try_files $uri $uri/ /index.html;`.<br>- Confirm static assets aren’t being matched by `/api/` proxy. |
| **CORS errors in browser** | Missing or conflicting `Access-Control-Allow-Origin` headers | - Prefer handling CORS *only* in the backend *or* Nginx—not both.<br>- In `nginx.conf`, ensure `location /api/` includes:<br>  `add_header Access-Control-Allow-Origin *;` *if needed*, and only once. |
| **Configuration changes not taking effect** | Nginx not reloaded | - In Docker: `docker-compose restart frontend`.<br>- Locally: `nginx -s reload` or restart the service. |

### Debugging Commands

- **Check live Nginx logs**:
  ```bash
  docker-compose logs -f frontend
  ```
  Or locally: `tail -f /var/log/nginx/error.log`

- **Inspect container filesystem**:
  ```bash
  docker exec -it <frontend-container> ls -lR /usr/share/nginx/html
  ```

- **Test proxy connection manually**:
  ```bash
  docker exec frontend curl -v http://backend:8000/api/health
  ```

---

## Related Files

| File | Purpose |
|------|---------|
| [`web/nginx.conf`](web/nginx.conf) | **Primary Nginx configuration**—defines routing, static asset paths, proxy behavior, security headers, and SPA support. |
| [`web/Dockerfile`](web/Dockerfile) | Builds the Nginx frontend container, embedding compiled assets and config. |
| [`docker-compose.yml`](docker-compose.yml) | Orchestrates frontend (Nginx) and backend (Python) services, health checks, and networking. |
| [`web/index.html`](web/index.html) | Entry point for static frontend; embedded into Nginx’s docroot during build. |
| [`server.py`](server.py) | Python backend; receives proxied API requests from Nginx. |
| [`.github/workflows/main.yml`](.github/workflows/main.yml) | CI/CD pipeline—including Nginx config validation (`nginx -t`). |
| [`web/vite.config.js`](web/vite.config.js) | Configures Vite build; ensures output paths align with Nginx `root` directive. |
