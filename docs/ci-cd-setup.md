# CI/CD Setup

## What is configured in the repository

### CI

File:

- `.github/workflows/ci.yml`

Triggers:

- pull requests to `main`
- pushes to `main`

Checks:

- install dependencies
- `python -m unittest tests.test_crm_services`
- `python -m compileall .`

Expected status check name:

- `CI / test`

### CD

File:

- `.github/workflows/cd.yml`

Trigger:

- pushes to `main`

Behavior:

- runs on pushes to `main`
- requires a repository secret named `CD_DEPLOY_COMMAND`
- executes the deploy command from that secret

Expected status check name:

- `CD / deploy`

## Required GitHub settings

### 1. Branch protection for `main`

Open:

- `Settings -> Branches -> Add branch protection rule`

Recommended rule:

- Branch name pattern: `main`

Enable:

- `Require a pull request before merging`
- `Require approvals`
- `Require status checks to pass before merging`
- `Require branches to be up to date before merging`
- `Do not allow bypassing the above settings` if your process requires strict protection

### 2. Required status checks

Add these checks as required:

- `CI / test`

If you want deployment to be enforced after merge visibility as well, keep:

- `CD / deploy`

Usually:

- `CI / test` is required for merge
- `CD / deploy` is observed on `main` after merge

## Repository secrets

### `CD_DEPLOY_COMMAND`

Add in:

- `Settings -> Secrets and variables -> Actions`

Create secret:

- `CD_DEPLOY_COMMAND`

This secret must contain the full deploy command for your target platform.

Examples:

- `./scripts/deploy.sh`
- `python deploy.py`
- `curl -X POST "$RENDER_DEPLOY_HOOK_URL"`
- `heroku container:release worker -a your-app-name`

## Important note

This repository currently contains a `Procfile`, but no deploy-provider config.

That means the workflow now supports:

- CI on pull requests
- CI on pushes to `main`
- a safe CD entrypoint on pushes to `main`

To complete real deployment, `CD_DEPLOY_COMMAND` must be configured for the actual platform you use.
