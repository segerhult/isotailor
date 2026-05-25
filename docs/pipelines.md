# Pipelines

## Files
- `.github/workflows/main.yml`

## What Runs Where

The `main.yml` workflow in the `.github/workflows/` directory is triggered on `pull_request` events, specifically when a pull request is opened, synchronized, or reopened.

**Permissions:**

The workflow requires the following permissions:

- `contents: write` (to update files)
- `pull-requests: write` (to add comments to pull requests)
- `issues: write` (to add comments to issues)

**Conditions:**

The workflow runs only when:

- The pull request's head repository matches the current repository.
- The actor is not the `github-actions[bot]`.
- The head ref does not start with `orchestra/`.

**Steps:**

1.  **Checkout Code:** Checks out the code from the pull request's head ref.
2.  **Authenticate Git for Push:** Configures the Git remote to use a personal access token for pushing changes.
3.  **Setup Node.js:** Sets up Node.js version 20.
4.  **Run Orchestra Doc-Gen:** Executes the `doc-gen` command from the `orchestra-ai-devops` package. This generates documentation using OpenAI's models.

**Environment Variables:**

The `orchestra-ai-devops doc-gen` command uses the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key.  (obtained via the `OPENROUTER_API_KEY` secret)
- `OPENAI_BASE_URL`: The base URL for the OpenAI API.
- `AI_BASE_URL`: The base URL for the AI API.
- `AI_MODEL`: The AI model to use.
- `GITHUB_TOKEN`: The GitHub token.
- `ORCHESTRA_ROLE_ROUTING`: Routing preference for Orchestra.
- `ORCHESTRA_DOCS_PR`: Indicates that this is a documentation pull request.



## Local Equivalents

The `orchestra-ai-devops doc-gen` command corresponds to documentation generation. Local commands for linting, testing, and building the application are not directly documented within this CI/CD pipeline documentation. Refer to the project's `package.json` in the `web/` directory for information on frontend tasks and `server.py` for backend task information.
