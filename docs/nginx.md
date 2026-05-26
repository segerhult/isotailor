# Nginx Configuration

## Overview

This repository leverages **Nginx** as a high-performance, production-grade HTTP server and reverse proxy to unify traffic management for a fullstack application comprising a **Vue 3 frontend** and a **Python-based custom API backend**. Nginx operates at the network edge, handling all inbound HTTP requests before routing them to the appropriate internal service—either serving static frontend assets directly or proxying dynamic API calls to the backend. This architecture provides critical benefits: decoupling of frontend and backend layers, elimination of CORS issues for browser clients, centralized request routing and security policies, and improved scalability through connection reuse and caching.

The Vue 3 frontend (built with [Vite](web/vite.config.js)) compiles into a minimal set of static files (`index.html`, JavaScript bundles, CSS, images) in the `web/dist/` directory. Nginx serves these files with optimal performance using low-latency, memory-mapped file serving and aggressive client-side caching headers for static assets. For API interactions (e.g., `/api/users`, `/api/auth/login`, `/api/health`), Nginx intercepts requests and forwards them to the Python backend (`server.py`) running on port `8000`, abstracting the network topology and enabling secure, authenticated communication without exposing internal services directly to clients.

This design supports multiple deployment scenarios:  
- **Local development** via Docker Compose for reproducible, isolated environments.  
- **CI/CD pipelines** that validate Nginx configuration integrity before deployment.  
- **Production environments**, where Nginx may sit behind cloud load balancers (e.g., AWS ALB) and optionally terminate TLS—though this repository defaults to HTTP and encourages offloading TLS to infrastructure layers for simplicity and performance.

Critically, `web/nginx.conf` is the **single canonical source of truth** for Nginx behavior. All routing rules, proxy timeouts, gzip compression, security headers, and SPA routing logic reside there, and modifications must be validated with `nginx -t` before deployment. Never embed Nginx configuration blocks in documentation; instead, reference this file and document *intent*, *behavior*, and *operational impact*, not syntax.

---

## Configuration File: `web/nginx.conf`

The file at [`web/nginx.conf`](web/nginx.conf) defines the core routing, security, and performance behavior for the frontend service. It is embedded into the Nginx container during the Docker build and takes effect immediately upon container startup. The configuration is structured around two primary `location` blocks and includes directives for static asset optimization and SPA support.

### Static Frontend Serving (`location /`)

The root location block serves the compiled Vue application. It uses the `root` directive to point to `/usr/share/nginx/html`, which is populated at build time by the [`web/Dockerfile`](web/Dockerfile). This block includes the `try_files` directive:

```nginx
try_files $uri $uri/ /index.html;
```

This ensures that all non-asset requests (e.g., `/dashboard`, `/settings/123`) return `index.html`, allowing Vue Router to handle client-side navigation. Crucially, `404.html` is *not* served by Nginx directly; instead, Vue Router handles route fallbacks, improving maintainability and reducing config complexity.

Static asset caching is enabled via targeted sub-locations (e.g., `location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$`) that set extended `Cache-Control` headers (`max-age=31536000`, immutable) and enable gzip compression, maximizing client-side caching and reducing bandwidth consumption.

### API Reverse Proxy (`location /api/`)

Requests to paths beginning with `/api/` are proxied to the backend service defined in [`docker-compose.yml`](docker-compose.yml) using:

```nginx
proxy_pass http://backend:8000;
```

Here, `backend` is the Docker service name, resolving via Docker’s embedded DNS to the backend container’s internal IP. Nginx preserves client context by passing standard headers:

- `Host $host` — ensures the backend receives the original request host.
- `X-Real-IP` and `X-Forwarded-For` — preserve the client’s IP address through the proxy chain.
- `X-Forwarded-Proto` — informs the backend whether the original request was HTTP or HTTPS, critical for secure redirect logic and CSRF protection.

A `proxy_read_timeout` is configured to accommodate long-polling or slow responses, while `proxy_connect_timeout` prevents hanging connections from stalling the proxy.

### Security & Performance Enhancements

The config includes:
- **Gzip compression** (`gzip on; gzip_types text/plain application/json application/javascript text/css`) to reduce payload size.
- **Error pages** (`error_page 404 /404.html`) for user-friendly failure responses.
- **Basic security headers** (e.g., `X-Frame-Options`, `X-Content-Type-Options`)—though full OWASP-compliant headers may be extended in production.
- **Rate limiting** via `limit_req_zone` (conditional on deployment needs), mitigating brute-force or DoS attempts.

No TLS configuration is included by default. Production deployments should enable HTTPS via external load balancers or explicit Nginx SSL directives—see [TLS Termination](#tls-termination-optional-production-enhancement).

> **Note**: The exact syntax and directives are subject to change. Always refer to `web/nginx.conf` for the authoritative configuration. Use `nginx -t -c web/nginx.conf` (locally) or its Docker equivalent for validation before committing or deploying changes.

---

## Containerization and Deployment

### Build Strategy

The Nginx frontend is containerized using [`web/Dockerfile`](web/Dockerfile), which follows a minimal, multi-stage-friendly pattern:

- **Base image**: `nginx:alpine` — chosen for its small footprint (< 50 MB), security-focused design, and full feature parity with mainline Nginx (including HTTP/2, SSL, streaming, and advanced proxying).
- **Build-time frontend compilation**: The Dockerfile invokes `npm install && npm run build` *during image build*, ensuring the `web/dist/` artifact is generated *before* copying into the final image. This guarantees deterministic builds and avoids runtime dependencies (e.g., Node.js, Vite) in production.
- **Configuration embedding**: `web/nginx.conf` is copied into `/etc/nginx/conf.d/default.conf`, the standard location for custom server blocks in the Alpine Nginx image.
- **Entrypoint**: The official image’s `ENTRYPOINT ["nginx", "-g", "daemon off;"]` ensures Nginx runs as PID 1 in the container, handling signals cleanly (e.g., for graceful reloads).

The resulting image contains *only* the runtime components needed to serve static assets and proxy API requests—no build tools, logs, or source code.

### Docker Compose Integration

[`docker-compose.yml`](docker-compose.yml) orchestrates the frontend (Nginx) and backend (Python) services with strict dependencies and health enforcement:

- The `frontend` service:
  - Builds from `./web`.
  - Exposes port `80` to the host (`80:80`).
  - Depends on the `backend` service *only after it becomes healthy*, preventing startup race conditions and 502 errors.
- The `backend` service:
  - Builds from the repository root (`.`) using [`Dockerfile`](Dockerfile).
  - Exposes port `8000`.
  - Implements a `/health` endpoint (verified via `curl -f http://localhost:8000/health`), which must return `HTTP 200` for Docker to consider the service *ready*.

Inter-container DNS resolution ensures `proxy_pass http://backend:8000;` in `web/nginx.conf` resolves reliably—even when container IPs change on restart. Network isolation (via Docker’s default bridge) further hardens the architecture by limiting exposure to other services.

---

## Local Development Setup

### Option 1: Full Containerized Development (Recommended)

The most reliable and consistent method for local development uses Docker Compose:

```bash
docker-compose up --build
```

This command orchestrates the following flow:

1. **Frontend Build Phase**:  
   - The `web/Dockerfile` runs `npm install && npm run build`, generating `web/dist/` inside the container.
   - Assets and `nginx.conf` are embedded into the image.
2. **Backend Build & Startup**:  
   - The root `Dockerfile` builds the Python backend image with `server.py`.
3. **Service Orchestration**:  
   - Docker waits for the `backend` container to pass its health check (via `/health`).
   - Only then does it start the `frontend` container, ensuring Nginx never attempts to proxy to an unready backend.

The result: A functional environment at `http://localhost` where:
- The Vue app loads at `/`.
- API requests (e.g., `/api/auth/login`) are transparently routed to `http://localhost:8000`.
- No manual config or path adjustments are needed—changes to `web/nginx.conf` take effect after `docker-compose restart frontend`.

### Option 2: Manual Local Nginx (Advanced / Debugging)

For debugging or rapid iteration *without* Docker, Nginx can be run manually—but this setup is **not reproducible** and should be avoided for CI or production work.

#### Prerequisites
- **Nginx installed system-wide** (see [Install Requirements](#install-requirements)).
- **Backend running locally** on port `8000` (e.g., `python server.py`).
- **Frontend built**:
  ```bash
  cd web && npm install && npm run build
  ```

#### Configuration Adjustments
Modify `web/nginx.conf` *only temporarily* (do not commit):
- Change `root /usr/share/nginx/html;` → `root /full/path/to/repo/web/dist;`
- Change `proxy_pass http://backend:8000;` → `proxy_pass http://localhost:8000;`

#### Validation & Execution
```bash
nginx -t -c /full/path/to/web/nginx.conf
nginx -c /full/path/to/web/nginx.conf
```

To apply config changes without restarting:
```bash
nginx -s reload
```

> **Critical Warning**: Manual configurations drift easily from the canonical file. Always revert `web/nginx.conf` to its original state before committing or pushing.

---

## TLS Termination (Optional Production Enhancement)

The default configuration assumes unencrypted HTTP traffic. For production deployments, TLS termination should be enabled—though the recommended approach is to **offload TLS at a reverse proxy or cloud load balancer** (e.g., AWS ALB, Cloudflare) rather than terminating it in Nginx.

### When to Terminate TLS in Nginx

Direct TLS termination in Nginx is appropriate only for:
- Self-hosted VMs or bare-metal servers without cloud load balancers.
- Internal services where cost or complexity constraints preclude infrastructure-grade TLS offloading.

### Configuration Requirements

1. **SSL Server Block**  
   Add a new `server` block in `web/nginx.conf` or an included `.conf`:
   ```nginx
   server {
       listen 443 ssl;
       server_name example.com;

       ssl_certificate /etc/nginx/ssl/fullchain.pem;
       ssl_certificate_key /etc/nginx/ssl/privkey.pem;

       # Include static serving + API proxying blocks from HTTP server
   }
   ```

2. **HTTP-to-HTTPS Redirect**  
   Enforce encryption via a separate HTTP server:
   ```nginx
   server {
       listen 80;
       server_name example.com;
       return 301 https://$host$request_uri;
   }
   ```

3. **Docker Compose Adjustments**  
   Mount certificates and expose port `443`:
   ```yaml
   frontend:
     volumes:
       - ./certs:/etc/nginx/ssl:ro  # Certs must be readable by `nginx` user
     ports:
       - "80:80"
       - "443:443"
   ```

### Certificate Management Best Practices

- **Never bake secrets into Docker images**. Use:
  - Docker secrets (in swarm mode).
  - CI/CD secrets injection (e.g., GitHub Secrets → env vars).
  - Host-mounted volumes or Kubernetes `Secrets`.
- Prefer Let’s Encrypt with automated renewal (e.g., `certbot`) for public-facing services.
- For internal services, use a private CA and distribute certificates via configuration management.

### Production Recommendation

For most deployments, **terminate TLS at the edge** (e.g., AWS ALB) and use HTTP internally. This reduces CPU load on app containers, simplifies certificate rotation, and aligns with zero-trust principles. Update `web/nginx.conf` only to reflect that TLS is handled upstream (e.g., set `X-Forwarded-Proto` explicitly).

---

## CI/CD Integration and Validation

The GitHub Actions workflow (`.github/workflows/main.yml`) enforces Nginx configuration integrity *before* any build or deploy steps execute.

### Pre-Deployment Linting

A dedicated step validates `web/nginx.conf` in a clean environment:

```bash
docker run --rm -v "$(pwd)/web:/etc/nginx/conf.d" nginx:alpine nginx -t
```

This:
- Uses the official `nginx:alpine` image as a reference binary.
- Mounts only `web/` (not the entire repo) to minimize state leakage.
- Fails the build immediately if syntax errors exist (e.g., missing semicolons, invalid directives like `proxy_pass http://invalid;`).

This step catches configuration drift caused by local development edits, merge conflicts, or IDE auto-formatting before they impact downstream pipelines.

### Build Consistency Guarantees

The build pipeline ensures tight coupling between Nginx config and frontend artifacts:

1. `npm run build` (via `web/Dockerfile`) generates `web/dist/`.
2. Both `dist/` and `web/nginx.conf` are copied atomically into the final image.
3. This eliminates "config drift" where:
   - An old Nginx config expects a route not present in the new `dist/`.
   - Caching headers mismatch new asset fingerprints.

For example, if `vite.config.js` changes output paths (e.g., `dist/assets` → `dist/bundle`), the Nginx `location ~ \.(js|css)` block *must* be updated accordingly—otherwise, assets return `404`. The build-time embedding ensures such mismatches fail fast during the CI `nginx -t` check.

---

## Install Requirements

Nginx is a **system-level HTTP server and reverse proxy**, *not* a language-specific dependency. It must be installed via system package managers or Docker, *never* via `pip` or `npm`. Attempts to install via `pip install nginx` yield a Python wrapper (e.g., `python-nginx`), not the actual server binary—leading to silent failures and wasted debugging time.

### Installation by Environment

| Environment | Method | Command | Notes |
|-------------|--------|---------|-------|
| **Production (Containerized)** | Implicit via Dockerfile | `FROM nginx:alpine` | No manual install needed. The image includes Nginx, config, and startup script. |
| **Production (Bare Metal / VM)** | System package manager | **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install nginx`<br>**Red Hat/CentOS**: `sudo yum install nginx` or `sudo dnf install nginx`<br>**macOS**: `brew install nginx` | Must manually: <br>1. Copy `web/nginx.conf` to `/etc/nginx/conf.d/default.conf`.<br>2. Set `root` to the absolute path of `web/dist/`.<br>3. Set `proxy_pass` to `http://localhost:8000`.<br>4. Restart Nginx: `sudo systemctl restart nginx` or `brew services restart nginx`. |
| **Local Development (Non-Docker)** | System package manager | Same as above | Ensure the Python backend (`server.py`) is running *before* starting Nginx. Use `nginx -s reload` to apply config changes without downtime. |
| **CI / Docker Compose** | Implicit in `web/Dockerfile` | — | Docker handles all dependencies. No manual action required. |

> **Critical Guidance**:  
> - Do *not* attempt to install Nginx via `pip` or `npm`. These are unrelated ecosystems and will not provide the required `nginx` binary.  
> - For Alpine Linux (used in Docker), ensure `libressl` or `openssl` is available if TLS is enabled—though this is already included in `nginx:alpine`.  
> - Package managers automatically resolve dependencies (e.g., `libpcre` for regex, `zlib` for gzip). Manual compilation is unnecessary and discouraged.

---

## Troubleshooting Tips

### Common Errors and Resolutions

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| **502 Bad Gateway** | Nginx cannot reach `backend:8000` | - Verify `backend` service is named `backend` in `docker-compose.yml`.<br>- Check `backend` health: `docker-compose ps` and visit `http://localhost:8000/health`.<br>- Confirm `proxy_pass` matches `http://backend:8000;` *exactly* (no trailing `/`). |
| **403 Forbidden** | Incorrect `root` path or permissions | - Confirm `web/dist/` exists and contains `index.html`.<br>- Ensure `root` in `nginx.conf` points to the *absolute* path (not `./dist`).<br>- In Docker: `docker exec frontend ls -l /usr/share/nginx/html` to verify contents. |
| **SPA routes (e.g., `/dashboard`) return 404** | Missing `try_files` or misordered `location` blocks | - Ensure `location /` block appears *before* `/api/` (Nginx matches most specific first).<br>- Confirm `try_files $uri $uri/ /index.html;` is present *and* uses the correct order (`$uri/` before `/index.html`). |
| **CORS errors in browser** | Conflicting CORS headers (e.g., set in both backend and Nginx) | - Prefer handling CORS *only in the backend* (e.g., `FastAPI` with `CORSMiddleware`).<br>- If setting in Nginx, add *only once* in `location /api/`:<br>  `add_header Access-Control-Allow-Origin $http_origin;`<br>  `add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';`<br>  `add_header Access-Control-Allow-Headers 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';`<br>  `if ($request_method = 'OPTIONS') { return 204; }` |
| **Config changes not reflected** | Nginx not reloaded | - In Docker: `docker-compose restart frontend` (full restart) or `docker exec frontend nginx -s reload`.<br>- Locally: `nginx -s reload` or restart the service: `sudo systemctl reload nginx`. |

### Debugging Commands

- **Inspect live logs** (Docker):
  ```bash
  docker-compose logs -f frontend
  ```
  For backend proxy issues, grep for errors:
  ```bash
  docker-compose logs -f | grep "upstream prematurely closed connection"
  ```

- **Check container filesystem**:
  ```bash
  docker exec -it frontend ls -lR /usr/share/nginx/html
  docker exec -it frontend cat /etc/nginx/conf.d/default.conf
  ```

- **Test proxy connectivity manually**:
  ```bash
  docker exec frontend curl -v http://backend:8000/api/health
  docker exec frontend nslookup backend
  ```

- **Validate config syntax locally**:
  ```bash
  docker run --rm -v "$(pwd)/web:/etc/nginx/conf.d" nginx:alpine nginx -t
  ```

- **Simulate a request with headers**:
  ```bash
  docker exec frontend curl -v http://localhost/
  docker exec frontend curl -sI http://localhost/api/health
  ```

---

## Related Files

| File | Purpose |
|------|---------|
| [`web/nginx.conf`](web/nginx.conf) | **Primary Nginx configuration**—defines routing, static asset paths, proxy behavior, SPA support, and performance/security headers. |
| [`web/Dockerfile`](web/Dockerfile) | Builds the Nginx frontend container: compiles frontend assets, embeds config, and sets up the runtime. |
| [`docker-compose.yml`](docker-compose.yml) | Orchestrates frontend (Nginx) and backend services, health checks, and inter-container networking. |
| [`web/index.html`](web/index.html) | Entry point for the Vue app; embedded into `/usr/share/nginx/html` during build. |
| [`server.py`](server.py) | Python backend; receives proxied API requests from Nginx (e.g., `/api/*`). |
| [`web/vite.config.js`](web/vite.config.js) | Configures Vite build output paths (e.g., `dist/`, asset naming) to align with Nginx `root` and caching rules. |
| [`web/package.json`](web/package.json) | Declares frontend dependencies (Vue, Vite, etc.) used during Docker build. |
| [`.github/workflows/main.yml`](.github/workflows/main.yml) | CI/CD pipeline step that validates `web/nginx.conf` via `nginx -t` before deployment. |
