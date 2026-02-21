---
name: odoo-cicd
description: GitHub Actions and GitLab CI/CD pipeline management for the Ordomatics Odoo project. Use when the user asks about CI/CD pipelines, build status, deployment, Docker registry, or pipeline configuration.
allowed-tools: Bash, Read, Glob, Grep
---

# Odoo CI/CD Pipelines

The Ordomatics Odoo project uses two parallel CI/CD systems.

## GitHub Actions (`.github/workflows/ci.yaml`)

**Triggered on:** push to `main`/`develop`, version tags (`v*`), pull requests

### Jobs

| Job | Runs on | Does |
|-----|---------|------|
| `build-and-push` | all triggers | Builds Docker image, pushes to GitLab registry |
| `test` | main, develop | DB init, health check, connectivity tests |
| `deploy` | main push only | Verifies prod image, generates deployment summary |
| `notify` | always | Reports overall status |

### Docker Tag Strategy

| Branch/Tag | Tags Applied |
|-----------|-------------|
| `v*` (version tag) | `latest`, `{version}` |
| `main` | `latest`, `{sha:8}` |
| `develop` | `staging`, `staging-{sha:8}` |
| other | `dev-{sha:8}` |

### Secrets Required

```
GIT_TOKEN              # GitHub token for submodule access
GITLAB_USERNAME        # GitLab registry login
GITLAB_ACCESS_TOKEN    # GitLab registry password
```

### Variables Required (GitHub repo vars)

```
GITLAB_REGISTRY_URL    # Registry host
GITLAB_IMAGE_PATH      # Image path in registry
DB_HOST, DB_PORT, DB_NAME, DB_USER
SERVER_URL, META_BASE_API_URL, AGENTIC_BASE_URL
```

### Viewing Workflow Status

```bash
# List recent workflow runs
gh run list --repo moctarjallo/odoo

# View a specific run
gh run view {run-id}

# Watch a running workflow
gh run watch {run-id}

# View logs
gh run view {run-id} --log
```

---

## GitLab CI (`.gitlab-ci.yml`)

**3 stages:** build → test → deploy

| Stage | Runs on | Does |
|-------|---------|------|
| build | main, develop, tags | Docker-in-Docker build, pushes to internal registry |
| test | main, develop | PostgreSQL service, Odoo CLI tests, DB init |
| deploy | main only | Tags image for `whatsapp2k/helm/odoo`, pushes to external registry |

Also includes: SAST scanning + container scanning on deploy stage.

---

## Production Deployment

**Production URL:** `https://kilifa.fr`
**Registry image:** `whatsapp2k/helm/odoo`

The deploy job does NOT deploy automatically — it prepares the image and outputs
the required runtime secrets/variables for the deployment operator.

### Required runtime secrets for production

```
DB_PASSWORD, ADMIN_PASSWD
OPENAI_API_KEY, ANTHROPIC_API_KEY, AGENTIC_API_KEY
WAVE_API_KEY, WAVE_SECRET_KEY
META_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_BUSINESS_ACCOUNT_ID
WHATSAPP_VERIFY_TOKEN
GAINDE_*, JENKINS_*, ARGO_PASSWORD  (infrastructure access)
```

---

## Common CI/CD Tasks

### Trigger a manual build

Push a commit to `develop` (staging) or `main` (production).

```bash
git push origin develop   # → staging build
git push origin main      # → production build
git tag v1.2.3 && git push origin v1.2.3  # → versioned release
```

### Update a workflow

Edit `.github/workflows/ci.yaml` or `.gitlab-ci.yml`, commit and push.
Always test changes on `develop` first before merging to `main`.

### Add a new build argument

1. Add to `Dockerfile` as `ARG MY_VAR`
2. Add to `docker-compose.yml` under `build.args`
3. Add to GitHub Actions `docker/build-push-action` `build-args`
4. Add to GitLab CI `docker build --build-arg` command
5. Add to GitHub repo variables or secrets as appropriate

### Add a new runtime secret

1. Add to `.env` locally
2. Document in the deploy job's notification output in `ci.yaml`
3. Add to GitLab CI `variables` section if needed for tests
