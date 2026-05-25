# Pipelines

## Files
- `.github/workflows/main.yml`

## What Runs Where

The `main.yml` workflow file in the `.github/workflows/` directory defines the continuous integration pipeline. This pipeline runs on pull requests (opened, synchronized, or reopened) to the main branch, but only if the pull request originates from outside the `orchestra/` branch and is not triggered by the `github-actions[bot]` user.

**Secrets and Permissions:**

The workflow utilizes the following secrets:

- `GITHUB_TOKEN`:  Used for authenticating with GitHub, enabling actions like checking out code and creating pull requests.
- `OPENROUTER_API_KEY`: Used to authenticate with the OpenAI API via OpenRouter.

The workflow requires the following permissions:

- `contents: write`:  Allows the workflow to modify files within the repository, such as updating the documentation.
- `pull-requests: write`: Allows the creation and updating of pull requests.
- `issues: write`: Allows the creation and updating of issues.

**Outputs/Artifacts:**

The workflow generates documentation using the `orchestra-ai-devops doc-gen` command. This command structure documents the repository. No specific artifacts are explicitly defined in the workflow file.

## Local Equivalents

Local development and testing should mirror the CI checks.  While specific commands aren't outlined in the provided context, typical development workflows would include:

- **Linting:**  Ensure code style consistency. (Command not specified)
- **Testing:** Validate code functionality. (Command not specified)
- **Building:** Prepare the application for deployment. (Command not specified)

These commands are not defined in the provided context.
