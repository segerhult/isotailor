# CI/CD Pipeline Documentation

## Overview

This repository implements a robust, containerized CI/CD pipeline for a **full-stack web application**, composed of a **Python backend** (FastAPI-based) and a **Vue.js frontend** served via **nginx**. The pipeline ensures automated testing, integration, and documentation generation, leveraging GitHub Actions for orchestration and Docker for reproducible builds across environments.

The core build and deployment strategy centers around containerization (`Dockerfile`, `web/Dockerfile`, `docker-compose.yml`) to ensure environment parity between development, CI, and production. The CI pipeline is configured to run on pull requests (PRs), with a specialized job responsible not just for validation but also for **self-documenting** the project structure and architecture using the [Orchestra AI DevOps](https://github.com/orchestra-ai/orchestra-ai) tool. This ensures that documentation stays in sync with code changes in near real-time.

---

## Core CI Workflow: `.github/workflows/main.yml`

The workflow is defined in `.github/workflows/main.yml` and is triggered exclusively on `pull_request` events (including `opened`, `synchronize`, and `reopened`). It does *not* run on pushes or tags, reflecting a design choice where **main branch stability is maintained via PR reviews** rather than pre-merge builds on direct pushes.

### Workflow Triggers and Conditions

| Trigger            | Runs? | Notes |
|--------------------|-------|-------|
| `pull_request`     | ✅ Yes | For all PR types (`opened`, `synchronize`, `reopened`) |
| `push` to `main`   | ❌ No  | Not configured; assumes protected branch + required PRs |
| `push` to other branches | ❌ No | Not triggered unless via PR |
| `release` / tags   | ❌ No  | No tag/publish workflows defined (yet) |

### Conditional Gatekeeping

The workflow includes logic to prevent internal automation loops and misuse:

- ✅ `github.event.pull_request.head.repo.full_name == github.repository`: Ensures only **PRs from the same repo** (i.e., internal feature/bugfix branches) run the workflow. External forks are excluded — preventing potential abuse of secrets or compute.
- ✅ `github.actor != 'github-actions[bot]'`: Prevents re-runs triggered by automated workflows (e.g., auto-merge, rebases), avoiding infinite loops.
- ✅ `!startsWith(github.head_ref, 'orchestra/')`: Excludes branches created by the Orchestra documentation generator itself (see below), avoiding recursive self-modification.

These conditions together create a *safe, self-cleaning* doc-generation feedback loop — doc updates *don’t* re-trigger doc generation.

---

## Job: `orchestra`

The only job in this workflow is named `orchestra`, running on an `ubuntu-latest` runner with persistent credentials to allow pushing updates (e.g., documentation artifacts) back to the PR branch.

### Permissions

| Permission      | Scope              | Purpose |
|----------------|--------------------|---------|
| `contents: write`  | Repository files   | Enables pushing updates (e.g., generated `.orchestra/` directory, documentation markdown files) to the PR branch |
| `pull-requests: write` | PR metadata & comments | Allows `orchestra-ai-devops` to attach documentation as PR comments (when `ORCHESTRA_DOCS_PR: '1'`) |
| `issues: write`    | Repository issues  | Reserved for advanced use cases (e.g., auto-issuing architecture suggestions) |

> ⚠️ **Security Note**: All permissions are scoped to the *minimum* required for documentation generation and PR updates. `secrets.GITHUB_TOKEN` is used (not `PAT`), and secrets are passed securely via environment variables.

---

### Step-by-Step Execution

#### 1. Checkout PR Branch

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0           # Full git history for semantic analysis
    ref: ${{ github.head_ref }}  # Explicitly target the PR branch
    persist-credentials: true
    token: ${{ secrets.GITHUB_TOKEN }}
```

- `fetch-depth: 0`: Critical for `orchestra-ai-devops` to perform structural and dependency *semantic analysis* (e.g., resolving imports, file relationships, API schemas). Shallow clones would break deep introspection.
- `persist-credentials: true`: Required for subsequent Git pushes.
- `ref`: Ensures we analyze the *exact* PR branch state — not the merge base or `main`.

#### 2. Configure Git for Push

```yaml
- name: Auth git for push
  run: git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- Updates the `origin` remote to use token-authenticated HTTPS (standard for GitHub Actions workflows that need to push).
- This step ensures subsequent doc-gen tools (which invoke Git under the hood) can push updated docs to the PR branch.

#### 3. Setup Node.js Runtime

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
```

- Required because `orchestra-ai-devops` is a Node.js-based CLI tool (`npx` invocation).
- Uses Node v20, aligning with modern npm/yarn support and compatibility with `vite` (the frontend build tool).

#### 4. Run Documentation Generator

```yaml
- name: Run Orchestra doc-gen
  env:
    OPENAI_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    OPENAI_BASE_URL: https://openrouter.ai/api/v1
    AI_BASE_URL: https://openrouter.ai/api/v1
    AI_MODEL: qwen/qwen3-coder-next
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ORCHESTRA_ROLE_ROUTING: prefer
    ORCHESTRA_DOCS_PR: '1'
  run: npx orchestra-ai-devops doc-gen . structure
```

##### Environment Variables Explained:

| Variable                | Value / Source                 | Purpose |
|-------------------------|--------------------------------|---------|
| `OPENAI_API_KEY`        | GitHub Secret (`OPENROUTER_API_KEY`) | Authenticates to OpenRouter (a multi-model provider), *not* OpenAI directly. |
| `OPENAI_BASE_URL` / `AI_BASE_URL` | `https://openrouter.ai/api/v1` | Routes requests to OpenRouter, which proxies to `qwen/qwen3-coder-next`. |
| `AI_MODEL`              | `qwen/qwen3-coder-next`        | Specifies the LLM — optimized for code understanding and doc generation. |
| `GITHUB_TOKEN`          | GitHub-provided token          | Used by `orchestra-ai-devops` to read PR metadata, comment, and push updates. |
| `ORCHESTRA_ROLE_ROUTING`| `prefer`                       | Instructs Orchestra to auto-assign tasks to specialized sub-agents (e.g., Docker expert, Python linter, Vue analyzer). |
| `ORCHESTRA_DOCS_PR`     | `'1'`                          | Enables PR-specific mode: docs are attached as comments and pushed to the PR branch, not committed to `main`. |

##### Command: `npx orchestra-ai-devops doc-gen . structure`

- Scans the repository root (`.`) and performs **deep structural analysis**, including:
  - Dependency graph extraction (`server.py`, `web/package.json`, `web/src/`, `Dockerfile` layers)
  - Architecture diagram inference (backend ↔ frontend ↔ nginx ↔ Docker Compose)
  - API endpoint discovery (heuristically, based on `server.py` Flask/FastAPI route decorators)
  - Image build plan generation (`Dockerfile` → runtime layers, `web/Dockerfile` → nginx static assets)
  - Local development equivalence mapping (e.g., how to replicate CI locally)
- Outputs a structured `.orchestra/` directory with:
  - `architecture.md`: ASCII/PlantUML diagrams + technical narrative
  - `api-summary.json`: Extracted endpoints, schemas, auth (if present)
  - `ci-cd-breakdown.md`: How CI, Docker, and local commands map
  - `install-requirements.md`: Exact tooling + versions + installation steps

> ✅ **Benefit**: PR reviewers gain immediate, context-aware context *without* reading all source files — just the high-level architecture and build flow.

---

## Local Equivalents: Replicating CI Behavior Locally

While CI focuses on documentation and structural integrity, the *same tools* can be run locally for pre-commit validation. Below are exact equivalents.

### Prerequisites (Install Requirements)

| Tool            | Package Manager | Command | Notes |
|-----------------|-----------------|---------|-------|
| `node` (v20+)   | `nvm` (recommended) | `nvm install 20 && nvm use 20` | NVM ensures version consistency with CI |
| `python` (3.11) | `pyenv` (recommended) | `pyenv install 3.11.9 && pyenv global 3.11.9` | Matches `python:3.11-slim` base image |
| `docker`        | System package / Docker Desktop | `sudo apt install docker.io` (Linux) | Required for `docker-compose` builds |
| `docker-compose`| `pip` or Docker Desktop | `pip install docker-compose` (legacy) / bundled with Docker Desktop | Newer setups include Compose v2 (`docker compose`) |

#### Backend Dependencies (`server.py`)

The Python backend uses `requirements.txt` implicitly (no explicit file detected, but `pip install` is assumed in `Dockerfile`). To mirror CI:

```bash
# In repository root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # OR: pip install . (if `setup.py`/`pyproject.toml` present)
```

> 🔍 **Heuristic inference**: Given the presence of `Dockerfile` (with `python:3.11-slim`) and no `requirements.txt`, it is highly likely dependencies are declared inline in the Docker build (e.g., `RUN pip install fastapi uvicorn`) or via `pyproject.toml`. To verify:
> - Check `Dockerfile` for `pip install ...` lines
> - Confirm with `pipdeptree` or `pip-compile --generate-hashes` for lock consistency

#### Frontend Dependencies (`web/`)

The frontend is a Vite + Vue 3 app (inferred from `vite.config.js`, `web/src/main.js`, `src/App.vue`):

```bash
cd web
npm ci  # Prefer `npm ci` over `npm install` for reproducibility (uses `package-lock.json`)
# OR, if dev setup needed:
npm run dev  # To start Vite dev server (mirrors `web/.dockerignore` excludes)
```

> ⚠️ **Critical**: `npm ci` ensures the exact dependency versions used in CI and Docker builds. `npm install` may mutate `package-lock.json`, causing drift.

---

## Install Requirements (Detailed)

### Python Backend

- **Base OS**: Ubuntu 22.04+ (to match GitHub Actions `ubuntu-latest`)
- **Python**: 3.11.x (any patch version compatible with `python:3.11-slim`)
- **Package Manager**: `pip` (version ≥22.0)
- **Key Packages** (heuristically inferred):
  - `fastapi` or `flask` → routing
  - `uvicorn` → ASGI server (likely, given slim image + `server.py`)
  - `pydantic` → validation (if data schemas used)
  - `python-multipart` → if `Form` data handling
- **Installation**:
  ```bash
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt  # If present
  # OR for direct setup:
  pip install fastapi uvicorn pydantic
  ```

### JavaScript Frontend

- **Node.js**: 20.x (LTS, matching CI `actions/setup-node`)
- **Package Manager**: `npm` (v10+ bundled with Node 20)
- **Build Tool**: `vite` (detected via `web/vite.config.js`)
- **UI Framework**: `vue@3` + `@vue/runtime-core` (inferred from `web/src/App.vue`)
- **HTTP Client**: Likely `axios` or `fetch` (via `web/src/api.js`)
- **Installation**:
  ```bash
  cd web
  npm ci  # RECOMMENDED (reproducible)
  # OR: npm install  # Only if modifying dependencies
  ```

> 🐳 **Docker Equivalents**:
> - Backend: `docker build -t backend . && docker run backend`
> - Frontend: `docker build -t frontend -f web/Dockerfile . && docker run frontend`
> - Full stack: `docker-compose up --build`

---

## Secrets & Security Considerations

| Secret                          | Where Used | Recommendation |
|---------------------------------|------------|----------------|
| `OPENROUTER_API_KEY`            | `orchestra-ai-devops` step | Rotate regularly. Scope to *read-only* if possible (OpenRouter supports API key scopes). |
| `GITHUB_TOKEN`                  | All CI steps | Use `GITHUB_TOKEN` (not PAT). Never commit to logs. |
| None for `server.py` or `web/`  | — | Ensure no `.env` files are committed (`.gitignore` likely covers this). |

> 🔒 **Best Practice**: Run `secrets.scan` (via `gitleaks` or `truffleHog`) locally before committing. The current `.gitignore` (inferred from presence of `server.py` + `web/`) should exclude `*.env`, `.venv/`, `node_modules/`, and IDE artifacts.

---

## Artifacts & Outputs

The workflow *does not* produce build artifacts (e.g., `dist/`, Docker images) — its sole purpose is **self-documentation**. However, the generated docs are:

- ✅ Committed to the PR branch under `.orchestra/`
- ✅ Summarized as PR comments (if `ORCHESTRA_DOCS_PR: '1'`)
- ✅ Available for PR reviewers to inspect architecture, install steps, and API contracts

---

## Future Expansions

This minimal workflow is intentionally focused. To grow maturity, consider adding:

| Feature | Workflow File | Why |
|---------|---------------|-----|
| Unit tests | `.github/workflows/test.yml` | `pytest` + `vitest` |
| Linting | `.github/workflows/lint.yml` | `ruff`, `eslint`, `stylelint` |
| Docker Image Build & Push | `.github/workflows/release.yml` | On tags (`v*`), push to `ghcr.io` |
| Helm Chart Lint | `.github/workflows/helm.yml` | If Kubernetes is later adopted |
| Security Scans | `.github/workflows/security.yml` | `trivy`, `snyk`, or `oss-scan` |

---

## Local Development ↔ CI Parity Checklist

| Action                  | Local Command | CI Equivalent |
|-------------------------|---------------|---------------|
| Analyze project structure | `npx orchestra-ai-devops doc-gen . structure` | `.github/workflows/main.yml` |
| Backend linting         | `ruff check server.py` | To-be-added `lint.yml` |
| Frontend linting        | `cd web && npm run lint` | To-be-added `lint.yml` |
| Build Docker images     | `docker-compose build` | Not yet automated (expansion candidate) |
| Run full app            | `docker-compose up` | Not yet automated |
| Generate API spec       | `fastapi openapi > openapi.json` (if FastAPI) | Optional: add to `doc-gen` |

> ✅ **Good sign**: The presence of `docker-compose.yml`, `web/nginx.conf`, and `Dockerfile` confirms strong containerization discipline — reducing "it works on my machine" risk.

--- 

**Last Updated**: Automatically generated by `orchestra-ai-devops` on PR opening/sync.  
**Maintainer Note**: Keep `.orchestra/` committed — it is the single source of truth for project structure.
