# Pipelines

## CI/CD Workflow

This repository utilizes GitHub Actions for continuous integration and continuous deployment (CI/CD). The primary workflow, defined in `.github/workflows/main.yml`, is triggered on pull request events.

### Workflow Details

The `main.yml` workflow automates documentation generation using the `orchestra-ai-devops` tool.

**Trigger:** `pull_request` events (opened, synchronized, reopened).

**Conditions:**
- The pull request must target the repository's main branch (`github.event.pull_request.head.repo.full_name == github.repository`).
- The pull request author must not be the `github-actions[bot]`.
- The pull request branch name must not start with `orchestra/`.

**Permissions:**

The workflow requires the following permissions:
- `contents: write` (to update files in the repository)
- `pull-requests: write` (to add comments to pull requests)
- `issues: write` (to add comments to issues)

**Steps:**

1.  **Checkout Code:** Fetches the repository code at the head ref of the pull request.  `fetch-depth: 0` ensures the full history is available.
2.  **Authenticate Git:** Configures Git to allow pushing changes back to the repository using the `GITHUB_TOKEN`.
3.  **Setup Node.js:** Installs Node.js version 20.
4.  **Run Orchestra Doc Generation:** Executes the `npx orchestra-ai-devops doc-gen .` command. This uses OpenAI's models (specifically `google/gemma-3-12b-it`, hosted at `https://openrouter.ai/api/v1`) to generate documentation based on the project's code and configuration. The following environment variables are used:
    *   `OPENAI_API_KEY`:  API key for accessing OpenAI's models via OpenRouter.
    *   `OPENAI_BASE_URL`: Base URL for the OpenAI API (OpenRouter API).
    *   `AI_BASE_URL`: Base URL for the AI API.
    *   `AI_MODEL`: The OpenAI model to use for documentation generation.
    *   `GITHUB_TOKEN`: The GitHub token for authentication and pushing changes.
    *   `ORCHESTRA_ROLE_ROUTING`: Routing preference for the Orchestra AI agent.
    *   `ORCHESTRA_DOCS_PR`: Flag indicating this is a pull request for documentation generation.

## Local Equivalents

The `orchestra-ai-devops doc-gen` command corresponds to local documentation generation. To run this locally:
