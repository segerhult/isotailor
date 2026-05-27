# CI/CD Pipelines

## Overview

This repository implements a **self-documenting CI/CD pipeline architecture** for a full-stack web application composed of:
- A **Python backend** (FastAPI-based, inferred from structure, `server.py`, and `python:3.11-slim` Docker base image)
- A **Vue 3 frontend** (served via **nginx**, using **Vite** as the build tool)
- Containerized deployment using **Docker** and **Docker Compose**

The CI pipeline is uniquely configured to serve as both a **validation gatekeeper** and a **documentation generator**, leveraging the open-source [Orchestra AI DevOps](https://github.com/orchestra-ai/orchestra-ai) tool to produce rich, up-to-date architectural documentation on every pull request. This creates a feedback loop where code changes automatically generate context-aware documentation for reviewers — eliminating context-switching, reducing onboarding time, and reducing knowledge silos.

The core philosophy is **"documentation as code"**: the project structure, API contracts, and installation procedures are derived *directly from the code*, ensuring consistency and correctness. There are no manual documentation updates — instead, structural analysis and LLM-driven narrative generation run as part of CI.

This approach complements — not replaces — future testing, linting, and image-building steps. For now, the pipeline serves as the primary CI artifact generator, and its minimal footprint makes it easy to extend incrementally.

---

## Pipeline Trigger Logic

The CI workflow is defined exclusively in `.github/workflows/main.yml`. It runs **only** on `pull_request` events (`opened`, `synchronize`, `reopened`), and **never** on direct `push`es to `main`, tags, or releases.

| Event Type | Runs? | Rationale |
|------------|-------|-----------|
| `pull_request` | ✅ Yes | Core validation and documentation generation |
| `push` to `main` | ❌ No | Assumes branch protection + required PR review |
| `push` to feature branches | ❌ No (unless PR opened) | Avoids duplicate doc-gen runs before review |
| `release` / tags | ❌ No | No publish/deploy workflow defined yet |
| Workflow dispatch / schedule | ❌ No | Not configured (future expansion candidate) |

This design prioritizes **stability via review** over automation: changes only enter the main branch after PR validation and team review. Direct pushes are disallowed by GitHub branch protection (not in the workflow config, but implied by the lack of `push` trigger). The absence of tag-based builds indicates that release automation (e.g., semantic versioning → Docker push → Helm upgrade) is not yet in scope.

---

## Conditional Execution Rules

The workflow includes three critical guardrails to prevent abuse, recursion, and misfire:

| Condition | Expression | Purpose |
|---------|------------|---------|
| Same-repo PR only | `github.event.pull_request.head.repo.full_name == github.repository` | Prevents external forks from accessing secrets or draining CI minutes (no `push` to repo after fork). |
| Exclude bot actor | `github.actor != 'github-actions[bot]'` | Prevents infinite loops if, e.g., an auto-merge or auto-update script reopens a PR. |
| Exclude Orchestra branches | `!startsWith(github.head_ref, 'orchestra/')` | Stops doc updates (stored on branches like `orchestra/doc-update/abc123`) from re-triggering the same doc generation process recursively. |

These conditions make the pipeline **self-protecting**: even if misconfigured, it cannot be exploited or recursed accidentally.

---

## Detailed Job Breakdown: `orchestra`

The workflow contains a single job named `orchestra`, provisioned on `ubuntu-latest` (GitHub-hosted runner). This job is responsible for:

- Checking out the PR branch (with full git history)
- Preparing Git credentials for push
- Installing Node.js runtime
- Invoking the Orchestra AI tool for deep, LLM-augmented documentation generation

### Job Permissions (Scoped Least Privilege)

| Permission | Scope | Why It’s Needed |
|-----------|-------|-----------------|
| `contents: write` | Repository files & branches | Allows committing generated docs (`.orchestra/`) directly to the PR branch |
| `pull-requests: write` | PR comments & metadata | Enables `orchestra-ai-devops` to post AI-generated summaries to the PR (e.g., “Architecture overview”, “API Summary”) |
| `issues: write` | Repository issues | Reserved for future use (e.g., auto-create architecture suggestions or refactor tickets) |

> ⚠️ **Security Note**: `GITHUB_TOKEN` is auto-provisioned by GitHub and is scoped to the *current repository only*. It is never persisted to logs or stored in secrets. Using `secrets.OPENROUTER_API_KEY` instead of hardcoded keys ensures API credentials are rotated externally.

---

### Step 1: Checkout PR Branch

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    ref: ${{ github.head_ref }}
    persist-credentials: true
    token: ${{ secrets.GITHUB_TOKEN }}
```

- `fetch-depth: 0`: *Critical* for Orchestra AI’s deep structural analysis. A shallow clone (`fetch-depth: 1`) would break:
  - Import resolution (e.g., `import { api } from './src/api'`)
  - Dependency graph reconstruction (via `package-lock.json`, `server.py` imports, Docker layer parsing)
  - Semantic diff analysis (e.g., “What changed in the API?”)
- `ref: github.head_ref`: Explicitly targets the PR branch tip — not the merge commit or base — ensuring analysis reflects *exactly* what’s under review.
- `persist-credentials: true`: Enables the Git CLI (`git push`) to authenticate in later steps.

---

### Step 2: Configure Git for Push

```yaml
- name: Auth git for push
  run: git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

This rewrites the `origin` remote to use **token-authenticated HTTPS**, the standard pattern for secure CI pushes to GitHub. Without this, subsequent `orchestra-ai-devops` commands (which attempt to push generated documentation) would fail with `403` or `Authentication failed`.

---

### Step 3: Setup Node.js Runtime

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
```

The `orchestra-ai-devops` CLI is a Node.js application. Node 20 is selected to match:
- The latest **LTS** version at time of writing
- Compatibility with `vite` (frontend build tool), which recommends Node ≥18
- Stability for tools like `npm` v10+, `pnpm`, and `node-gyp` (for native builds, though none present here)

> 💡 **Note**: Node 20 is *not* used for the application runtime — it’s only for doc-gen tooling. The backend and frontend are containerized (using Python 3.11 and nginx).

---

### Step 4: Run Documentation Generator

```yaml
- name: Run Orchestra doc-gen
  env:
    OPENAI_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    OPENAI_BASE_URL: https://openrouter.ai/api/v1
    AI_BASE_URL: https://openrouter.ai/api/v1
    AI_MODEL: google/gemini-2.5-flash-lite # Updated to reflect current usage
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ORCHESTRA_ROLE_ROUTING: prefer
    ORCHESTRA_DOCS_PR: '1'
  run: npx orchestra-ai-devops doc-gen . structure
```

#### Environment Variables Explained

| Variable | Value | Role |
|---------|-------|------|
| `OPENAI_API_KEY` | GitHub Secret `OPENROUTER_API_KEY` | Authenticates to [OpenRouter](https://openrouter.ai), a proxy for open-weight models (e.g., Gemini, Qwen). *Not* OpenAI’s official API. |
| `OPENAI_BASE_URL` / `AI_BASE_URL` | `https://openrouter.ai/api/v1` | Routes LLM calls to OpenRouter instead of `api.openai.com`. Required for model selection. |
| `AI_MODEL` | `google/gemini-2.5-flash-lite` | Uses Google's Gemini 2.5 Flash Lite model, optimized for speed and cost-efficiency in code analysis and documentation generation. |
| `GITHUB_TOKEN` | GitHub auto-provisioned token | Used by `orchestra-ai-devops` to read PR metadata, post comments, and push files. |
| `ORCHESTRA_ROLE_ROUTING` | `prefer` | Enables task decomposition: assigns sub-tasks to specialized agents (e.g., “Docker expert”, “Python architect”) for better accuracy. |
| `ORCHESTRA_DOCS_PR` | `'1'` | Activates PR-specific mode: outputs are written to `.orchestra/` *and* posted as PR comments (not merged into `main`). |

#### Command: `npx orchestra-ai-devops doc-gen . structure`

This scans the repository root (`.`) and performs **four levels of analysis**:

1.  **File & Dependency Graph Inference**:
    - Parses `web/package.json`, `web/package-lock.json`, `server.py`, `web/src/`, `Dockerfile`, `docker-compose.yml`, and `docs/openapi.yaml`.
    - Maps import chains (e.g., `main.js → App.vue → api.js → /api/health`).
    - Identifies external dependencies and their roles within the application architecture.
    - Recognizes the OpenAPI specification (`docs/openapi.yaml`) for detailed API analysis.

2.  **Architecture Diagram Generation**:
    - Produces ASCII, PlantUML, or other supported formats for:
      - System topology (e.g., Browser → Nginx → FastAPI → Database).
      - CI/CD pipeline flow (e.g., Pull Request → Documentation Generation → Documentation Commit).
      - Build layers (e.g., Dockerfile multi-stage build process).
    - Example snippet from output:
        ```plaintext
        [Browser] → [nginx:80] → [FastAPI (Python 3.11)] → [Database]
        ```

3.  **API Contract Extraction and Validation**:
    - Scans `server.py` for FastAPI route definitions (e.g., `@app.get`, `@app.post`).
    - Analyzes `docs/openapi.yaml` for a precise definition of API endpoints, parameters, request/response schemas, and authentication methods.
    - Merges in-code route definitions with the OpenAPI spec to ensure consistency and identify potential discrepancies.
    - Outputs `api-summary.json` (or similar) with structure detailing:
        ```json
        {
          "endpoints": [
            {
              "path": "/api/health",
              "method": "GET",
              "summary": "Health check endpoint",
              "description": "Checks the health status of the API.",
              "responses": { "200": { "description": "OK" } }
            },
            // ... more endpoints
          ]
        }
        ```
    - *Note*: This goes beyond simple inference by actively validating against the OpenAPI spec.

4.  **Local Equivalence Mapping**:
    - Maps CI/CD steps to developer-friendly local commands:
      - `docker-compose build` equivalent to backend and frontend build processes.
      - `npm ci` for frontend dependency installation.
      - `uvicorn server:app` for running the backend development server.
    - Generates a reproducible `install-requirements.md` file detailing setup steps for local development.

---

## Generated Artifacts

All outputs are committed to `.orchestra/` *on the PR branch* and posted as PR comments. Key files include:

| File | Content | Use Case |
|------|---------|----------|
| `architecture.md` | ASCII diagrams, tech stack table, container breakdown | PR reviewers can quickly grasp the system layout. |
| `api-summary.json` | JSON list of endpoints validated against `openapi.yaml` | Verify API coverage and consistency. |
| `ci-cd-breakdown.md` | CI steps mapped to local commands | Developers can easily replicate CI processes locally. |
| `install-requirements.md` | Step-by-step guide for local setup | Streamlines onboarding and environment setup. |
| `docker-build-plan.md` | Build order, layer caching strategies, `.dockerignore` impact | Understand and optimize Docker build processes. |
| `directory-structure.md` | Markdown file tree with component descriptions | Provides a quick overview of the repository's organization. |

> ✅ **Impact**: A PR reviewer can understand the *entire system context* in minutes — significantly reducing the need to read source code for initial comprehension.

---

## Install Requirements (Detailed, Production-Grade)

This section details the environment and tooling necessary for both local development and matching the CI environment.

### Backend: Python 3.11 (for `server.py`)

The backend is containerized using `python:3.11-slim` as its base image. Local development environments should mirror this to prevent runtime discrepancies.

| Tool | Recommended Version | Installation Method | Notes |
|------|---------------------|---------------------|-------|
| **Python Interpreter** | 3.11.x (e.g., 3.11.9) | `pyenv` (strongly recommended) or system package manager | Crucial for matching the `Dockerfile`'s base image. Use `pyenv install 3.11.9 && pyenv global 3.11.9` for management. |
| **`pip`** | ≥22.0 | Bundled with Python ≥3.8 | Ensure it's up-to-date: `python -m pip install --upgrade pip`. |
| **Backend Dependencies** | (`fastapi`, `uvicorn`, `pydantic`, `python-multipart`, potentially others from `server.py` imports) | `pip install -r requirements.txt` (if `requirements.txt` exists) or direct `pip install <package-name>` | If the `Dockerfile` explicitly lists dependencies with `RUN pip install ...`, replicate those exact packages. Verify using `grep -E 'RUN.*pip install' Dockerfile`. |
| **Virtual Environment** | N/A | `python -m venv .venv && source .venv/bin/activate` | Essential for isolating project dependencies and maintaining clean builds. Avoid global Python package installations. |

#### Backend Local Setup Checklist

```bash
# 1. Verify Python version
python --version
# Expected: Python 3.11.x

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install base dependencies
pip install --upgrade pip setuptools wheel
# If requirements.txt exists:
# pip install -r requirements.txt
# Otherwise, install inferred dependencies:
pip install fastapi uvicorn pydantic python-multipart

# 4. Run the backend development server
# This command should align with the Dockerfile's CMD or ENTRYPOINT if specified.
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

> 🔍 **Ambiguity Resolution**: The `Dockerfile` uses `python:3.11-slim` without an explicit `requirements.txt` copy. This implies dependencies might be installed inline (`RUN pip install ...`) or managed via a build tool like Poetry or Hatch (though no `pyproject.toml` was detected). Examine the `Dockerfile` for `RUN pip install` commands to confirm the exact package list. If none are found, rely on the inferred list or check for `pyproject.toml`.

---

### Frontend: Vue 3 + Vite (for `web/`)

The frontend is a Single Page Application (SPA) built with Vite and Vue 3. The CI environment uses Node.js 20 to ensure compatibility with the build tools.

| Tool | Recommended Version | Installation Method | Notes |
|------|---------------------|---------------------|-------|
| **Node.js** | 20.x (LTS) | `nvm` (recommended) | Install via `nvm install 20 && nvm use 20`. This ensures parity with the       `actions/setup-node` version used in CI. |
| **`npm`** | v10+ | Bundled with Node 20 | Verify with `npm -v`. |
| **Frontend Dependencies** | Managed via `web/package.json` and `web/package-lock.json` | `npm ci` (inside the `web/` directory) | *Crucially*, use `npm ci` to install exact versions from the lock file, ensuring reproducibility and matching the CI build process. |
| **Build Tool** | Vite | Managed by `npm ci` | Vite is the primary build tool. |
| **UI Framework** | Vue 3 | Managed by `npm ci` | No separate installation required beyond `npm ci`. |

#### Frontend Local Setup Checklist

```bash
# Navigate to the frontend directory
cd web

# 1. Install dependencies using the lock file for reproducibility
npm ci

# 2. Start the development server (matches CI build/serve steps)
npm run dev
# Typically runs on http://localhost:5173 or similar.

# 3. Build the production-ready frontend assets (mirrors Docker build step)
npm run build
# This command outputs static assets to the 'dist/' directory.
```

> ⚠️ **Critical Distinction**: Always use `npm ci` for dependency installation in both local development and CI. Using `npm install` can inadvertently update `package-lock.json`, leading to discrepancies between your local setup and the Docker image built in CI.

---

### Container Runtime

The application relies on Docker for containerization and Docker Compose for orchestrating multiple services (backend, frontend, potentially databases).

| Tool | Recommended Version | Installation Method | Notes |
|------|---------------------|---------------------|-------|
| **Docker** | ≥24.0 | Official Docker installation guides for your OS, Docker Desktop | Required to build and run Docker images and containers. |
| **Docker Compose** | v2+ (as `docker compose`) | Bundled with Docker Desktop, or installed as a plugin | The project uses the `docker-compose.yml` file, which is compatible with Docker Compose v2 syntax. |

#### Full Local Stack Test (`docker-compose.yml`)

To run the entire application stack locally, matching the containerized deployment:

```bash
# Ensure Docker and Docker Compose are running.
# Navigate to the root directory containing docker-compose.yml.

# Build all services (backend, frontend nginx) and start them in detached mode.
docker compose up --build -d

# To view logs:
docker compose logs -f

# To stop and remove containers, networks, and volumes:
docker compose down
```

This command builds the necessary Docker images (if not already present) and starts the backend and frontend (served by nginx) services, making them accessible on `localhost:8000` and `localhost:80` respectively (ports configurable in `docker-compose.yml`).

---

## Secrets & Security

### Secrets Management

The CI pipeline utilizes GitHub Secrets to securely manage sensitive information.

| Secret Name | Usage in CI (`.github/workflows/main.yml`) | Purpose | Security Considerations |
|-------------|--------------------------------------------|---------|-------------------------|
| `OPENROUTER_API_KEY` | `env.OPENAI_API_KEY`, `env.OPENAI_BASE_URL` | Authenticates the documentation generation tool to the OpenRouter API for LLM access. | **Do not commit this key directly.** Rotate regularly. Scope access if possible via OpenRouter's dashboard. Never log the secret's value. |
| `GITHUB_TOKEN` | `secrets.GITHUB_TOKEN` (used by `actions/checkout`, `git remote set-url`, `orchestra-ai-devops`) | Provides CI environment authentication for accessing repository contents, pushing changes (generated docs), and interacting with the GitHub API. | This is a time-limited, automatically generated token scoped to the repository. Avoid using personal access tokens (PATs) with broader scopes. |

### `.gitignore` Recommendations

A robust `.gitignore` file is crucial for preventing accidental commits of sensitive data and unnecessary build artifacts. Based on the project structure, the following patterns should be included:

-   **Environment Variables**: `*.env`, `*.env.*`, `!.env.example` (if an example file is used)
-   **Python Dependencies**: `.venv/`, `venv/`, `env/`, `*.pyc`, `__pycache__/`
-   **Node.js Dependencies**: `node_modules/`, `*.log`
-   **Build Artifacts**: `dist/`, `build/`, `public/build/`
-   **IDE / Editor Config**: `.idea/`, `.vscode/`, `*.swp`
-   **OS Generated Files**: `.DS_Store`, `Thumbs.db`
-   **CI/CD Generated Artifacts**: `.orchestra/` (consider committing initially, then adding to `.gitignore` or using `git update-index --skip-worktree` to manage updates)

> 🔒 **Scanning Recommendation**: Before committing changes, consider using tools like `gitleaks` or `truffleHog` to scan for accidentally included secrets:
> ```bash
> gitleaks detect --source . --verbose
> ```

---

## Local ↔ CI Parity Checklist

This checklist helps ensure that the development environment closely matches the CI execution environment, minimizing "works on my machine" issues.

| Action | Local Command(s) | CI Equivalent (in `.github/workflows/main.yml`) | Potential Discrepancies |
|--------|--------------------|------------------------------------------------|--------------------------|
| **Project Analysis & Documentation Generation** | `npx orchestra-ai-devops doc-gen . structure` | `npx orchestra-ai-devops doc-gen . structure` | LLM model differences, OpenAPI spec version mismatches, subtle code parsing variations. |
| **Backend Dependency Installation** | `source .venv/bin/activate && pip install -r requirements.txt` (or `pip install ...`) | `pip install ...` (as per Dockerfile) | Missing packages, version conflicts if `requirements.txt` or Dockerfile is outdated. |
| **Frontend Dependency Installation** | `cd web && npm ci` | `cd web && npm ci` (within the Docker build context) | Node.js version differences, corrupt `node_modules` / `package-lock.json` locally. |
| **Backend Runtime** | `uvicorn server:app --reload --host 0.0.0.0 --port 8000` | `CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]` (in `Dockerfile`) | Port conflicts, environment variable differences, underlying Python library versions. |
| **Frontend Serving** | `cd web && npm run dev` | `nginx` server within Docker container (serving `web/dist/`) | Build output differences (`npm run build`), nginx configuration variations. |
| **Full Stack Execution** | `docker compose up --build` | N/A (CI focuses on artifact generation) | Differences in container networking, exposed ports, or service dependencies defined in `docker-compose.yml`. |

> ✅ **Validation Tip**: After running the `orchestra-ai-devops doc-gen` command locally, compare the generated `.orchestra/` files against those produced by the CI pipeline on a PR. Any significant differences highlight areas where local and CI environments may have diverged.

---

## Future Expansions

The current CI pipeline is intentionally streamlined to focus on automated documentation. As the project evolves, consider augmenting the CI/CD strategy with the following workflows:

| Feature | Proposed Workflow File | Trigger Event(s) | Rationale |
|---------|------------------------|-------------------|-----------|
| **Backend Unit & Integration Tests** | `.github/workflows/backend-tests.yml` | `pull_request`, `push` to `main` | Execute tests using `pytest` to validate backend logic and ensure code quality. Fail PRs that introduce regressions. |
| **Frontend Unit & E2E Tests** | `.github/workflows/frontend-tests.yml` | `pull_request`, `push` to `main` | Run tests via `vitest` (or similar) for frontend components and potentially Playwright/Cypress for end-to-end scenarios. |
| **Linting & Code Formatting** | `.github/workflows/linting.yml` | `pull_request` | Enforce code style consistency using tools like `ruff` for Python and `eslint`/`prettier` for JavaScript/Vue. Prevents style debates during reviews. |
| **Docker Image Building & Pushing** | `.github/workflows/docker-publish.yml` | `release` (on tags `v*`) | Automate the building of optimized Docker images for the backend and frontend, and push them to a container registry (e.g., Docker Hub, GHCR). |
| **Security Scanning** | `.github/workflows/security.yml` | `pull_request`, `push` to `main` | Integrate static analysis security testing (SAST) and dependency vulnerability scanning (e.g., `trivy`, `snyk`, `pip-audit`). |
| **Terraform/Infrastructure Deployment** | `.github/workflows/deploy.yml` | `push` to `main`, triggered by `release` workflow | If infrastructure is managed via Terraform, orchestrate `terraform apply` after successful deployments. |

> 📝 **Recommended Next Steps**: Implementing automated testing (`backend-tests.yml`, `frontend-tests.yml`) and linting (`linting.yml`) are high-priority additions that significantly improve code reliability and maintainability with moderate effort.

---

## Conclusion

This repository's CI/CD pipeline represents a robust, modern approach centered on **"documentation as code"** and **developer productivity**. By leveraging Orchestra AI DevOps, the pipeline acts as an intelligent assistant, automatically generating and updating critical architectural and operational documentation with every code change proposed via pull request.

Key strengths of this pipeline include:

-   **Automated Documentation**: Eliminates manual documentation effort and ensures accuracy.
-   **Enhanced Review Process**: Provides reviewers with immediate, context-rich information.
-   **Streamlined Onboarding**: Makes it easier for new developers to understand the project structure and setup.
-   **Reduced Context Switching**: Developers can grasp system details without leaving their PR review.
-   **Minimalist Design**: Focused core workflow with clear paths for future expansion.
-   **Security-Conscious**: Utilizes GitHub Secrets and adheres to best practices for sensitive data management.

This pipeline serves as a foundational element for maintaining a healthy, well-documented, and efficiently managed full-stack application. Its extensible nature allows for the seamless integration of testing, security scanning, and deployment automation as the project matures.
