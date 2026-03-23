---
name: odoo-cicd
description: Odoo CI/CD pipelines and git submodules — use when modifying GitHub Actions workflows, GitLab CI config, understanding deployment stages and tag strategies, or managing git submodules.
---

# Odoo CI/CD

## GitHub Actions (`.github/workflows/ci.yaml`)

| Job | Triggers | What it does |
|-----|---------|--------------|
| `build-and-push` | all branches/tags | Builds Docker image, pushes to GitLab registry |
| `test` | main, develop | DB init, health check, connectivity tests |
| `deploy` | main push | Verifies prod image, generates deployment summary |
| `notify` | always | Reports workflow status |

### Tag Strategy

| Push | Image tag |
|------|-----------|
| Version tag (`v*`) | `latest` + version tag |
| `main` | `latest` + short SHA |
| `develop` | `staging` + `staging-{sha}` |
| Other branch | `dev-{sha}` |

**Production URL:** `https://kilifa.fr`

## GitLab CI (`.gitlab-ci.yml`)

3 stages: build → test → deploy

- **Build**: Docker-in-Docker, pushes to GitLab registry
- **Test**: PostgreSQL service, Odoo CLI + DB init checks
- **Deploy**: Tags image for `whatsapp2k/helm/odoo` external registry

## Git Submodules

```bash
# Initialize submodules after clone
git submodule update --init --recursive

# Update all submodules to latest
git submodule update --remote --recursive

# Update a specific submodule
git submodule update --remote addons/odoo-llm
```

Submodules: `addons/enterprise`, `addons/oca/web-api`, `addons/oca/rest-framework`,
`addons/oca/queue`, `addons/whatsapp`, `addons/odoo-llm`
