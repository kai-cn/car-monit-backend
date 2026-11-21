#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Register backend parity workflow on backend default branch (master)."""
import os, subprocess, sys

repo = r'D:\work\IdeaProjects\car-monit-backend-java-V3'
wf_src = r'D:\work\IdeaProjects\car-monit-backend-jdk25\.github\workflows\parity-verify-cloud.yml'
relpath = '.github/workflows/parity-verify-cloud.yml'
msg = 'ci(parity): register parity-verify-cloud on default branch for workflow_dispatch'


def git(*a, input=None):
    return subprocess.run(['git', '-C', repo, *a], input=input, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


base = git('rev-parse', 'FETCH_HEAD').stdout.strip()
print('base master:', base[:7])
if git('cat-file', '-e', f'{base}:{relpath}').returncode == 0:
    print('already present'); sys.exit(0)

content = open(wf_src, encoding='utf-8').read()
blob = git('hash-object', '-w', '--stdin', input=content).stdout.strip()
env = os.environ.copy()
env['GIT_INDEX_FILE'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'idx_bk_master_parity.idx')
subprocess.run(['git', '-C', repo, 'read-tree', base], env=env, capture_output=True, check=True)
subprocess.run(['git', '-C', repo, 'update-index', '--add', '--cacheinfo', f'100644,{blob},{relpath}'],
               env=env, capture_output=True, check=True)
tree = subprocess.run(['git', '-C', repo, 'write-tree'], env=env, capture_output=True, text=True, check=True).stdout.strip()
os.remove(env['GIT_INDEX_FILE'])
commit = git('commit-tree', tree, '-p', base, '-m', msg)
if commit.returncode != 0:
    print('commit error:', commit.stderr); sys.exit(1)
c = commit.stdout.strip()
git('update-ref', 'refs/heads/master', c)
print('updated master ->', c[:7])
