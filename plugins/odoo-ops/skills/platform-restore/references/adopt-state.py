#!/usr/bin/env python3
"""Generate one Terraform directory per Crossplane workspace, importing what exists.

Run from the platform repo root:  python3 adopt-state.py <workdir>

Each directory gets the provider block of the workspace's ProviderConfig (with
a local backend), the composition's inline module, its vars, and `import`
blocks for the resources that already exist. Then, per directory:
    terraform init && terraform plan     # expect "N to import, 0 to destroy"
    terraform apply                      # writes terraform.tfstate locally
and push-state.sh uploads the states under their workspace names.

Credentials come from env files and are written mode 600 into each directory:
  NEON_API_KEY                      (odoo/.env)
  R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, CF_ACCOUNT_ID, CF_TOKENS_TOKEN (infra/.env)
"""
import json
import os
import sys
import urllib.request

import yaml

WORK = sys.argv[1]
ROOT = os.path.expanduser('~/projects/ordomatics')


def env(path, *keys):
    out = {}
    for line in open(path).read().splitlines():
        line = line.removeprefix('export ')
        if '=' in line:
            k, v = line.split('=', 1)
            if k in keys:
                out.setdefault(k, v.strip().strip('"\''))
    return out


NEON = env(f'{ROOT}/odoo/.env', 'NEON_API_KEY')['NEON_API_KEY']
R2 = env(f'{ROOT}/infra/.env', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'CF_ACCOUNT_ID', 'CF_TOKENS_TOKEN')


def neon(path):
    req = urllib.request.Request('https://console.neon.tech/api/v2' + path,
                                 headers={'Authorization': 'Bearer ' + NEON, 'Accept': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=30))


def provider(config):
    spec = yaml.safe_load(open(f'crossplane/providerconfigs/{config}.yaml'))['spec']
    return spec['configuration'].replace('backend "kubernetes" {}', 'backend "local" {}')


def composition(name):
    c = yaml.safe_load(open(f'crossplane/compositions/{name}.yaml'))
    fp = c['spec']['resources'][0]['base']['spec']['forProvider']
    return fp['module'], {v['key']: v.get('value', '') for v in fp.get('vars', [])}


def claims(directory):
    for f in sorted(os.listdir(directory)):
        if f.endswith('.yaml'):
            yield yaml.safe_load(open(f'{directory}/{f}'))


def selector(claim):
    return (claim['spec'].get('compositionSelector') or {}).get('matchLabels', {}).get(
        'platform.ordomatics.com/provider')


def write(ws, prov, module, tfvars, imports, files):
    d = f'{WORK}/{ws}'
    os.makedirs(d, exist_ok=True)
    blocks = ''.join(f'import {{\n  to = {a}\n  id = "{i}"\n}}\n' for a, i in imports)
    open(f'{d}/main.tf', 'w').write(prov + '\n' + module + '\n' + blocks)
    open(f'{d}/terraform.tfvars.json', 'w').write(json.dumps(tfvars))
    for name, value in files.items():
        open(f'{d}/{name}', 'w').write(value)
        os.chmod(f'{d}/{name}', 0o600)
    print('wrote', ws)


# Neon: projects by NAME (claim spec.name), each with its default branch.
projects = {p['name']: p for p in neon('/projects?limit=200')['projects']}
default_branch = {}
for p in projects.values():
    branches = neon(f"/projects/{p['id']}/branches")['branches']
    default_branch[p['id']] = next(b['id'] for b in branches if b.get('default'))

prov = provider('terraform')
neon_files = {'neon-api-key': NEON}

module, defaults = composition('neon-project-tf')
for c in claims('neon-projects'):
    s = c['spec']
    p = projects.get(s['name'])
    if not p:
        print('SKIP np-%s: no Neon project named %s' % (c['metadata']['name'], s['name']))
        continue
    write('np-' + c['metadata']['name'], prov, module,
          dict(defaults, project_name=s['name'], region=s['region'],
               database_name=s['databaseName'], role_name=s['roleName']),
          [('neon_project.this', p['id']),
           ('neon_database.default', f"{p['id']}/{default_branch[p['id']]}/{s['databaseName']}")],
          neon_files)

module, defaults = composition('database-neon-tf')
for c in claims('databases'):
    if selector(c) != 'neon-tf':
        continue  # neon-ref-tf only reads data sources: an empty state is right
    s = c['spec']
    name = s.get('databaseName') or s['clientSlug']
    write('db-' + c['metadata']['name'], prov, module,
          dict(defaults, project_id=s['neonProjectId'], branch_id=s['neonBranchId'], db_name=name,
               db_host=s.get('neonHost', ''), db_host_direct=s.get('neonHostDirect', '')),
          [('neon_database.db', f"{s['neonProjectId']}/{s['neonBranchId']}/{name}")],
          neon_files)

# R2: bucket and CORS are imported; the per-bucket Cloudflare token cannot be
# (its value is shown once, at creation), so Terraform mints a new one.
prov = provider('cloudflare-r2')
module, _ = composition('storage-r2-tf')
r2_files = {'r2-access-key-id': R2['R2_ACCESS_KEY_ID'], 'r2-secret-access-key': R2['R2_SECRET_ACCESS_KEY'],
            'cloudflare-account-id': R2['CF_ACCOUNT_ID'], 'cloudflare-tokens-token': R2['CF_TOKENS_TOKEN']}
for c in claims('storage'):
    if selector(c) != 'r2':
        continue  # Linode buckets belong to a Linode account: not adoptable across accounts
    s = c['spec']
    imports = [('aws_s3_bucket.this', s['bucketName'])]
    tfvars = {'bucket_name': s['bucketName']}
    if s.get('corsOrigins'):
        imports.append(('aws_s3_bucket_cors_configuration.this[0]', s['bucketName']))
        tfvars['cors_origins'] = s['corsOrigins']
    write('st-' + c['metadata']['name'], prov, module, tfvars, imports, r2_files)
