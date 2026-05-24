# Requirements

## Runtime
- Python 3.11

## System Packages
- git (recommended, required for git diff / PR workflows)

## CI Requirements
- GitHub Actions: set `permissions.contents: write` if Orchestra should push branches for docs PRs
- For PR workflows from forks, GitHub tokens are often read-only (docs PR creation may be disabled by policy)

## Environment Variables (minimum)
- OPENAI_API_KEY (OpenRouter key when using OpenRouter)
- AI_BASE_URL (set to `https://openrouter.ai/api/v1` for OpenRouter)
- AI_MODEL (example: `openrouter/auto`)
- GITHUB_TOKEN (for PR comments/PR creation)

## Commands
- Run docs generator: `npx orchestra-ai-devops doc-gen .`
