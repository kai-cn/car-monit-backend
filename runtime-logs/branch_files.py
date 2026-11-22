#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""List which branches contain a given workflow file."""
import subprocess, sys
REPOS = {'api': r'D:\work\IdeaProjects\car-monit-api-java-V3',
         'backend': r'D:\work\IdeaProjects\car-monit-backend-java-V3'}
repo = REPOS[sys.argv[1]]
needle = sys.argv[2] if len(sys.argv) > 2 else '.github/workflows/self-hosted-ci.yml'
branches = [b.strip() for b in subprocess.run(
    ['git','-C',repo,'for-each-ref','--format=%(refname:short)','refs/remotes/origin'],
    capture_output=True,text=True,encoding='utf-8',errors='replace').stdout.splitlines()
    if b.strip().startswith('origin/') and 'HEAD' not in b]
print(f"Branches containing {needle}:")
for b in branches:
    r = subprocess.run(['git','-C',repo,'cat-file','-e',f'{b}:{needle}'], capture_output=True)
    if r.returncode == 0:
        print('  ', b.replace('origin/',''))
