# Requirements

## Runtime
- Python 3.11

## System Packages
- git (recommended, required for git diff / PR workflows)

## CI Requirements
- GitHub Actions: set `permissions.contents: write` if Orchestra should push branches for docs PRs
- For PR workflows from forks, GitHub tokens are often read-only (docs PR creation may be disabled by policy)

## Environment Variables (minimum)
- `OPENAI_API_KEY`: Your OpenAI API key. Use your OpenRouter key when `AI_BASE_URL` is set to `https://openrouter.ai/api/v1`.
- `AI_BASE_URL`: The base URL for your AI service. Example for OpenRouter: `https://openrouter.ai/api/v1`.
- `AI_MODEL`: The AI model to use. (Example: `openrouter/auto`).
- `GITHUB_TOKEN`: Required for GitHub pull request comments and creation.

## Orchestra

These environment variables control the behavior of the Orchestra component.

- `ORCHESTRA_ROLE_ROUTING`:  `auto` (default) or `prefer` (use plugin preferred role/persona).
- `ORCHESTRA_DOCS_PR`: Set to `1` to enable automatic draft documentation pull request creation in pull request workflows.
- `ORCHESTRA_APP_NAME / ORCHESTRA_APP_URL`: Used to identify requests. Required for OpenRouter headers.
- `ORCHESTRA_SOURCE`: A string appended to the system prompt (Example: `ci:github-actions`).
- `ORCHESTRA_DEBUG`: Set to `1` to enable verbose AI error logging.

## VCS
Configuration for Version Control System (VCS) integration.

- `VCS_PROVIDER`: `github`, `gitlab`, or `azure`.  Auto-detected in CI if not set.



## Commands
- Run docs generator: `npx orchestra-ai-devops doc-gen .`