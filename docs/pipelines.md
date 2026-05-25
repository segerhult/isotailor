# Pipelines

## Files
- `.github/workflows/main.yml`

## What Runs Where

The `main.yml` workflow in the `.github/workflows/` directory defines the Continuous Integration and Continuous Delivery (CI/CD) pipeline.  This workflow is triggered on pull requests (`opened`, `synchronize`, `reopened`) to the repository.

**Permissions:**
The workflow requires the following permissions:
- `contents: write` - To modify files within the repository (e.g., updating documentation).
- `pull-requests: write` - To interact with pull requests (e.g., adding comments).
- `issues: write` - To interact with issues (e.g., adding labels).

**Conditions:**
The workflow runs under these conditions:
- The pull request targets the main repository (`github.event.pull_request.head.repo.full_name == github.repository`).
- The author is not the `github-actions[bot]` user.
- The branch name does not start with `orchestra/`.

**Steps:**
1. **Checkout Code:** The workflow checks out the code from the pull request's head branch. It fetches the full commit history (`fetch-depth: 0`), persists credentials for improved access, and uses the `GITHUB_TOKEN` for authentication.
2. **Authenticate Git:** Configures the Git remote URL to use a personal access token (`GITHUB_TOKEN`) for pushing changes.
3. **Setup Node.js:** Sets up Node.js version 20 for running JavaScript-based tools.
4. **Run Orchestra Doc-Gen:** Executes the `orchestra-ai-devops doc-gen` command. This tool utilizes OpenAI's API (configured by `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `AI_BASE_URL`, `AI_MODEL`) to generate documentation dynamically.  This step uses the `GITHUB_TOKEN` and `ORCHESTRA_ROLE_ROUTING` and `ORCHESTRA_DOCS_PR` environment variables.

## Local Equivalents

Currently, there is no explicit documentation of local commands that directly correlate to the CI checks defined in the workflow.  This includes linting, testing, and building. Documenting such commands would allow developers to perform similar checks locally for faster feedback during development.
    
## Secrets and Environment Variables

The following secrets and environment variables are used by the `main.yml` workflow:

*   `OPENAI_API_KEY`: OpenAI API key for accessing the OpenAI API.
*   `OPENAI_BASE_URL`: Base URL for the OpenAI API.
*   `AI_BASE_URL`: Base URL for the AI API (same as OpenAI_BASE_URL in this case).
*   `AI_MODEL`: The OpenAI model to use for documentation generation (google/gemma-3-12b-it).
*   `GITHUB_TOKEN`: GitHub token used for authentication with GitHub.
*   `ORCHESTRA_ROLE_ROUTING`: Routing configuration for Orchestra.
*   `ORCHESTRA_DOCS_PR`: Flag indicating whether we're processing a pull request doc.
