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

Triggers:

- pull requests to `main`
- pushes to `main`
- manual run via `workflow_dispatch`

Behavior:

- `verify-changes` runs for pull requests and validates that the Docker image builds
- `deploy-production` runs on pushes to `main`
- deployment uses SSH to the production VPS
- deployment uses the in-repository `Dockerfile` and `docker-compose.yml`
- Alembic migrations run after the container is started

Expected status check names:

- `CD / verify-changes`
- `CD / deploy-production`

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
- `CD / verify-changes`

Usually:

- `CI / tests` is required for merge
- `CD / verify-changes` is required for merge
- `CD / deploy-production` is observed on `main` after merge

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

This repository now uses the same Timeweb VPS deployment model as the working `v2` branch:

- `Dockerfile`
- `docker-compose.yml`
- SSH deploy to the VPS
- compose rebuild / restart
- Alembic migrations after container startup

That means the workflow now supports:

- CI on pull requests
- CI on pushes to `main`
- Docker build verification on pull requests
- production deployment on pushes to `main`
