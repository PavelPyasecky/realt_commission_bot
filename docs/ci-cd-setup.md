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
- manual run via `workflow_dispatch`

Behavior:

- `deploy` runs on pushes to `main`
- deployment uses SSH to the production VPS
- deployment applies Alembic migrations after the container is started

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

- `CI / tests`

Usually:

- `CI / tests` is required for merge
- `CD / deploy` is observed on `main` after merge

## Repository secrets

### Required production secrets

Add in:

- `Settings -> Secrets and variables -> Actions`

Create secrets:

- `SSH_PRIVATE_KEY`
- `PROD_VPS_USER`
- `PROD_VPS_HOST`
- `PROD_ENV_FILE`

`PROD_ENV_FILE` must contain the full production `.env` content encoded as base64.

## Important note

This repository currently has a working VPS-oriented deploy pattern inherited from the previous deployment workflow.

That means the workflow now supports:

- CI on pull requests
- CI on pushes to `main`
- production deployment on pushes to `main`

To complete real deployment, the SSH/VPS secrets above must be present in GitHub Actions.
