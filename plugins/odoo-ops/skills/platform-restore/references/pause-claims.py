#!/usr/bin/env python3
"""Pause (or unpause) the platform repo's Terraform-backed claims.

Run from the platform repo root:
  python3 pause-claims.py pause
  python3 pause-claims.py unpause neon-projects/ordomatics.yaml databases/smartacus-db.yaml ...
  python3 pause-claims.py unpause --all --keep storage/ordomatics.yaml storage/smartacus.yaml

The ClientCluster claim (clusters/<name>/crossplane.yaml) is never paused: a
new account needs a new cluster, so its workspace SHOULD create.
"""
import glob
import re
import sys

DIRS = ['neon-projects', 'neon-branches', 'databases', 'storage']
EXTRA = glob.glob('clusters/*/tunnel.yaml')
NOTE = '    # Held until its Terraform state is rebuilt by import (platform-restore).\n'
BLOCK = '  annotations:\n' + NOTE + '    crossplane.io/paused: "true"\n'


def files():
    return [f for d in DIRS for f in sorted(glob.glob(f'{d}/*.yaml'))] + EXTRA


def pause(path):
    s = open(path).read()
    if 'platform.ordomatics.com/v1alpha1' not in s or 'crossplane.io/paused' in s:
        return False
    if '\n  annotations:\n' in s.split('\nspec:')[0]:
        s = s.replace('\n  annotations:\n', '\n  annotations:\n' + NOTE + '    crossplane.io/paused: "true"\n', 1)
    else:
        s = s.replace('\nmetadata:\n', '\nmetadata:\n' + BLOCK, 1)
    open(path, 'w').write(s)
    return True


def unpause(path):
    s = open(path).read()
    # Any comment line just above the annotation goes with it, and the
    # annotations key too when nothing else is left under it.
    out = re.sub(r'(?:    #[^\n]*\n)?    crossplane\.io/paused: "true"\n', '', s, count=1)
    out = re.sub(r'\n  annotations:\n(?=  [a-z])', '\n', out, count=1)
    if out == s:
        return False
    open(path, 'w').write(out)
    return True


if __name__ == '__main__':
    mode, args = sys.argv[1], sys.argv[2:]
    if mode == 'pause':
        print('paused', sum(pause(f) for f in files()))
    else:
        keep = set(args[args.index('--keep') + 1:]) if '--keep' in args else set()
        targets = [f for f in files() if f not in keep] if '--all' in args else [a for a in args if a != '--all']
        print('unpaused', sum(unpause(f) for f in targets))
