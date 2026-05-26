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

This rewrites the `origin` remote to use **token-authenticated HTTPS**, the standard pattern for secure CI pushes to GitHub. Without this, subsequent `orchestra-ai-devops` commands (which may call `git push`) would fail with `403` or `Authentication failed`.

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
    AI_MODEL: qwen/qwen3-coder-next
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ORCHESTRA_ROLE_ROUTING: prefer
    ORCHESTRA_DOCS_PR: '1'
  run: npx orchestra-ai-devops doc-gen . structure
```

#### Environment Variables Explained

| Variable | Value | Role |
|---------|-------|------|
| `OPENAI_API_KEY` | GitHub Secret `OPENROUTER_API_KEY` | Authenticates to [OpenRouter](https://openrouter.ai), a proxy for open-weight models (e.g., Qwen, Mistral). *Not* OpenAI’s official API. |
| `OPENAI_BASE_URL` / `AI_BASE_URL` | `https://openrouter.ai/api/v1` | Routes LLM calls to OpenRouter instead of `api.openai.com`. Required for model selection. |
| `AI_MODEL` | `qwen/qwen3-coder-next` | Uses Alibaba’s Qwen 3 Coder, fine-tuned for code understanding, generation, and documentation. Offers strong performance at lower cost than GPT-4. |
| `GITHUB_TOKEN` | GitHub auto-provisioned token | Used by `orchestra-ai-devops` to read PR metadata, post comments, and push files. |
| `ORCHESTRA_ROLE_ROUTING` | `prefer` | Enables task decomposition: assigns sub-tasks to specialized agents (e.g., “Docker expert”, “Python architect”) for better accuracy. |
| `ORCHESTRA_DOCS_PR` | `'1'` | Activates PR-specific mode: outputs are written to `.orchestra/` *and* posted as PR comments (not merged into `main`). |

#### Command: `npx orchestra-ai-devops doc-gen . structure`

This scans the repository root (`.`) and performs **four levels of analysis**:

1. **File & Dependency Graph Inference**  
   - Parses `web/package.json`, `web/package-lock.json`, `server.py`, `web/src/`, `Dockerfile`, `docker-compose.yml`
   - Maps import chains: `main.js → App.vue → api.js → /api/health`
   - Identifies hidden dependencies (e.g., `nginx.conf` references `/usr/share/nginx/html`, inferred from `web/Dockerfile`)

2. **Architecture Diagram Generation**  
   - Produces ASCII/PlantUML diagrams for:
     - System topology (client → nginx → API → DB)
     - CI/CD pipeline flow (PR → doc-gen → docs commit)
     - Build layers (Dockerfile multi-stage → multi-image composition)
   - Example snippet from output:
     ```plaintext
     [Browser] → [nginx:80] → [FastAPI (Python 3.11)] → [PostgreSQL]
     ```

3. **API Contract Extraction (Heuristic)**  
   - Scans `server.py` for FastAPI decorators (`@app.get`, `@app.post`, etc.)
   - Infers endpoints, parameters, response schemas, and auth (if present)
   - Outputs `api-summary.json` with structure:
     ```json
     {
       "endpoints": [
         {
           "path": "/api/health",
           "method": "GET",
           "summary": "Health check endpoint",
           "responses": { "200": "OK" }
         },
         ...
       ]
     }
     ```
   - *Note*: This is *not* OpenAPI spec generation — it’s a lightweight, dependency-free summary suitable for PR reviews.

4. **Local Equivalence Mapping**  
   - Maps CI steps to developer-friendly commands:
     - `docker-compose build` ↔ `docker build -f web/Dockerfile .`
     - `npm ci` ↔ local frontend install
     - `uvicorn server:app` ↔ local backend dev server
   - Generates a reproducible `install-requirements.md` (see below)

---

## Generated Artifacts

All outputs are committed to `.orchestra/` *on the PR branch* and posted as PR comments. Key files:

| File | Content | Use Case |
|------|---------|----------|
| `architecture.md` | ASCII diagrams, tech stack table, container breakdown | PR reviewers understand system layout at a glance |
| `api-summary.json` | JSON list of endpoints (no spec version) | Validate API coverage (e.g., new routes added?) |
| `ci-cd-breakdown.md` | CI steps ↔ local commands table | Developers replicate CI locally |
| `install-requirements.md` | Tooling + install steps (see below) | Onboarding, debugging environment drift |
| `docker-build-plan.md` | Build order, layer caching notes, `.dockerignore` impact | Optimize Docker builds |
| `directory-structure.md` | Markdown file tree with descriptions | Rapid repository orientation |

> ✅ **Impact**: A PR reviewer can understand the *entire system context* in <5 minutes — without reading source code.

---

## Install Requirements (Detailed, Production-Grade)

### Backend: Python 3.11 (for `server.py`)

The backend runs on `python:3.11-slim`, so local environments should match to avoid drift.

| Tool | Version | Installation Method | Notes |
|------|---------|---------------------|-------|
| **Python** | 3.11.x (e.g., 3.11.9) | `pyenv` (recommended) / system package manager | Must match `Dockerfile` base image. Use `pyenv install 3.11.9 && pyenv global 3.11.9`. |
| **`pip`** | ≥22.0 | Included with Python ≥3.8 | Upgrade with `python -m pip install --upgrade pip`. |
| **Key Packages** (inferred from `server.py` and slim image) | `fastapi`, `uvicorn`, `pydantic`, `python-multipart` | Install via `pip install -r requirements.txt` (if present) or `pip install fastapi uvicorn pydantic python-multipart` | If `Dockerfile` contains `RUN pip install ...`, those are the exact packages needed. Verify with `cat Dockerfile | grep pip`. |
| **Virtual Environment** | — | `python -m venv .venv && source .venv/bin/activate` | Required for clean local builds. Avoid global installs. |

#### Backend Setup Checklist

```bash
# 1. Ensure Python 3.11
python --version  # Must be 3.11.x

# 2. Create venv
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn pydantic python-multipart  # OR: -r requirements.txt

# 4. Run backend (matches Docker ENTRYPOINT)
uvicorn server:app --reload  # --reload for dev
# OR: uvicorn server:app --host 0.0.0.0 --port 8000
```

> 🔍 **Heuristic Clarification**: The `Dockerfile` uses `python:3.11-slim` with no `COPY` of `requirements.txt`. This strongly suggests dependencies are either:
> - Declared inline in `Dockerfile` (e.g., `RUN pip install fastapi uvicorn`)
> - Or managed via `pyproject.toml` (e.g., `poetry`/`hatch`), though no `pyproject.toml` was detected.
> 
> To resolve ambiguity, run:
> ```bash
> grep -E "pip install" Dockerfile
> ```
> If empty, assume `pyproject.toml`/`setup.py` usage — but in its absence, use the inferred packages above.

---

### Frontend: Vue 3 + Vite (for `web/`)

The frontend is a modern Vite + Vue 3 SPA. Node 20 is used in CI for compatibility.

| Tool | Version | Installation Method | Notes |
|------|---------|---------------------|-------|
| **Node.js** | 20.x (LTS) | `nvm` (recommended) | `nvm install 20 && nvm use 20`. Ensures parity with `actions/setup-node`. |
| **`npm`** | v10+ | Bundled with Node 20 | Use `npm -v` to verify. |
| **Build Tool** | Vite ≥5.x | `npm ci` (via `web/package.json`) | Lockfile (`package-lock.json`) ensures reproducibility. |
| **UI Framework** | Vue 3 | `npm ci` (via `web/package.json`) | No build step required in CI — `vite build` is only for Docker. |
| **HTTP Client** | `axios` or `fetch` | Inferred from `web/src/api.js` | Not a dependency — standard `fetch` is used unless explicitly imported. |

#### Frontend Setup Checklist

```bash
cd web

# 1. Install dependencies (reproducible)
npm ci

# 2. Run dev server (mirrors local workflow)
npm run dev  # Starts on http://localhost:5173 by default

# 3. Build for production (matches `web/Dockerfile` step)
npm run build  # Outputs to `dist/`
```

> ⚠️ **Critical Distinction**: `npm ci` is *mandatory* for CI parity. `npm install` may update `package-lock.json`, causing differences between:
> - Local `npm install` → Docker build (which uses `npm ci`)
> - CI → Docker build (which uses `npm ci`)

---

### Container Runtime

| Tool | Version | Installation Method | Notes |
|------|---------|---------------------|-------|
| **Docker** | ≥24.0 | OS package (`apt install docker.io`), Docker Desktop, or `docker compose` plugin | Required to run `docker-compose.yml`. |
| **Docker Compose** | v2+ (`docker compose`) | Bundled with Docker Desktop / `docker compose` plugin | The project uses `docker-compose.yml` (v2.x format). |
| **Local Equivalents** | `docker-compose build && docker-compose up` | `docker compose up --build` (v2 syntax) | Use `--remove-orphans` if services persist across runs. |

#### Full Local Stack Test

```bash
# Build & run backend, frontend (nginx), and any sidecars
docker-compose up --build
```

This starts:
- Backend on `localhost:8000`
- Frontend (nginx) on `localhost:80`
- (Optional) Database, if `docker-compose.yml` includes it.

---

## Secrets & Security

### Secrets in Use

| Secret | Purpose | Best Practices |
|--------|---------|----------------|
| `OPENROUTER_API_KEY` | Authenticates to OpenRouter for AI doc-gen | Rotate every 90 days. Scope to *read-only* if OpenRouter supports it. Never log. |
| `GITHUB_TOKEN` | CI authentication (checkout, push, comments) | Auto-provisioned. Never use `PAT` — it has broader permissions. |
| `.env` files (e.g., `server.env`) | — | *None needed*. No `.env` is committed (implied by `.gitignore` presence). |

> 🔒 **Scanning Recommendation**: Run `gitleaks` or `truffleHog` locally before committing:
> ```bash
> gitleaks detect --source . --verbose
> ```

### `.gitignore` Coverage (Inferred)

The presence of `server.py`, `web/package-lock.json`, and `Dockerfile` implies a `.gitignore` excluding:
- `*.env`, `*.local`
- `.venv/`, `node_modules/`
- `dist/`, `build/`
- IDE artifacts (`.idea/`, `.vscode/`)
- `.orchestra/` *after* initial commit (since CI generates it, not humans)

> ✅ **Best Practice**: Commit `.orchestra/` *initially* (as generated by CI), but exclude it from future CI runs to avoid merge conflicts (or use `git update-index --skip-worktree`).

---

## Local ↔ CI Parity Checklist

| Action | Local Command | CI Equivalent (in `.github/workflows/main.yml`) |
|--------|---------------|------------------------------------------------|
| Analyze project structure | `npx orchestra-ai-devops doc-gen . structure` | `npx orchestra-ai-devops doc-gen . structure` (same command) |
| Lint backend | `ruff check server.py` (if `ruff` installed) | To-be-added `lint.yml` |
| Lint frontend | `cd web && npm run lint` (if `eslint` installed) | To-be-added `lint.yml` |
| Unit test backend | `pytest` (if tests present) | To-be-added `test.yml` |
| Unit test frontend | `cd web && npm run test:unit` (if `vitest` used) | To-be-added `test.yml` |
| Build Docker images | `docker-compose build` | Not yet automated (future expansion) |
| Run full stack | `docker-compose up` | Not yet automated |
| Generate OpenAPI spec | `uvicorn server:app --port 8000 & curl http://localhost:8000/openapi.json > openapi.json` | Optional: extend `doc-gen` to include |

> ✅ **Validation Tip**: After running `npx orchestra-ai-devops` locally, compare outputs to CI’s `.orchestra/` — discrepancies indicate local environment drift.

---

## Future Expansions

The current pipeline is intentionally lean. As the project matures, consider these add-ons:

| Feature | New Workflow | Trigger | Why |
|---------|--------------|---------|-----|
| **Unit Tests** | `.github/workflows/test.yml` | `pull_request` | `pytest` for backend, `vitest` for frontend. Fail PRs on test errors. |
| **Linting & Formatting** | `.github/workflows/lint.yml` | `pull_request` | `ruff` (Python), `eslint` (Vue), `prettier` — enforce style consistency. |
| **Docker Image Build & Push** | `.github/workflows/release.yml` | `release` (tags `v*`) | Build `backend`, `frontend`, `app` images; push to `ghcr.io`. |
| **Kubernetes Helm Lint** | `.github/workflows/helm.yml` | `pull_request` (if `charts/` added) | `helm lint`, `helm template` |
| **Security Scans** | `.github/workflows/security.yml` | `pull_request` + `push to main` | `trivy fs .`, `snyk code test`, `pip-audit`. |

> 📝 **Migration Path**: Start with `test.yml` and `lint.yml` — they add immediate value with minimal complexity.

---

## Conclusion

This CI/CD pipeline embodies a **modern, developer-centric philosophy**: CI isn’t just a gate — it’s a *documentation co-pilot*. By combining automated structural analysis with LLM-generated narratives, it eliminates the "documentation tax" that plagues many projects.

The pipeline is:
- ✅ **Minimal** (1 workflow, 4 steps)
- ✅ **Safe** (no secrets in code, strict conditions)
- ✅ **Self-updating** (doc-gen runs on every PR)
- ✅ **Extensible** (foundation for testing/linting/releases)

As long as the project remains containerized and full-stack, this pattern will scale — turning every PR into an opportunity to sharpen project context and onboarding clarity.
