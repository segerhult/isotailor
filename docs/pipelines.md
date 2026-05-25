# Pipelines

## Files
- `.github/workflows/main.yml`

## Workflow Details

This repository utilizes a GitHub Actions workflow named `Dynamic docs`, defined in the `.github/workflows/main.yml` file. This workflow is triggered on pull requests targeting the main branch. It automatically generates documentation using the `orchestra-ai-devops` tool.

### Trigger Conditions

The workflow runs under the following conditions:

*   **Event:** `pull_request` events of type `opened`, `synchronize`, or `reopened`.
*   **Branch Restriction:** The pull request must target the repository's main branch (`github.event.pull_request.head.repo.full_name == github.repository`).
*   **Actor Exclusion:** The workflow will not run if the actor is the `github-actions[bot]`.
*   **Ref Exclusion:** The workflow will not run if the branch name starts with `orchestra/`.

### Permissions

The workflow requires the following permissions:

*   `contents`: Allows the workflow to read and write to the repository's contents.
*   `pull-requests`: Allows the workflow to add comments to pull requests.
*   `issues`: Allows the workflow to add comments to issues.

### Steps

1.  **Checkout Code:** Checks out the code from the pull request branch using `actions/checkout@v4`, fetching the full history. It persists credentials and uses the `GITHUB_TOKEN` for authentication.
2.  **Authenticate Git:** Sets the Git remote URL using the `GITHUB_TOKEN` for pushing changes.
3.  **Setup Node:** Sets up a Node.js environment with version 20 using `actions/setup-node@v4`.
4.  **Run Orchestra Doc Generation:** Executes the `orchestra-ai-devops doc-gen` command using `npx`.  This command generates documentation leveraging OpenAI's API.

### Environment Variables

The `orchestra-ai-devops doc-gen` command utilizes the following environment variables:

*   `OPENAI_API_KEY`: Your OpenAI API key.
*   `OPENAI_BASE_URL`: The base URL for the OpenAI API.
*   `AI_BASE_URL`:  The base URL for the AI API (same as `OPENAI_BASE_URL` in this case).
*   `AI_MODEL`: The AI model to use (e.g., `google/gemma-3-12b-it`).
*   `GITHUB_TOKEN`: The GitHub token used for authentication and pushing changes.
*   `ORCHESTRA_ROLE_ROUTING`: Controls role routing behavior (set to `prefer`).
*   `ORCHESTRA_DOCS_PR`: Indicates that this is a documentation pull request.



## Local Equivalents

The `orchestra-ai-devops doc-gen` command generates documentation locally as well.
