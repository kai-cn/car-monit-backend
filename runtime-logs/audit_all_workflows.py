#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only audit of repository workflows or credentials exposure.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Read-only audit of every workflow on every remote branch of both repos."""
import subprocess

REPOS = [r'D:\work\IdeaProjects\car-monit-api-java-V3',
         r'D:\work\IdeaProjects\car-monit-backend-java-V3']

PATTERNS = {
    'selfhost': 'self-hosted',
    'wsl': 'wsl-k3s',
    'push': '  push:',
    'pull_req': 'pull_request',
    'pr_target': 'pull_request_target',
    'auto_deploy': 'AUTO_DEPLOY_CLUSTER',
    'runner_var': 'CI_RUNNER_JSON',
    'runner_lbl': 'CI_RUNNER_LABELS',
    'sudo': 'sudo ',
    'secret': 'secrets.',
}


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace').stdout


for repo in REPOS:
    name = repo.rsplit('\\', 1)[-1]
    branches = [b.strip() for b in run(
        ['git', 'for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin'], repo
    ).splitlines() if b.strip().startswith('origin/') and 'HEAD' not in b]
    print('\n' + '=' * 90)
    print('REPO:', name, '| branches:', len(branches))
    for br in branches:
        files = [f.strip() for f in run(
            ['git', 'ls-tree', '-r', '--name-only', br, '.github/workflows/'], repo
        ).splitlines() if f.strip().endswith(('.yml', '.yaml'))]
        risky = []
        for f in files:
            content = run(['git', 'show', f'{br}:{f}'], repo)
            hits = {k: content.count(v) for k, v in PATTERNS.items() if v in content}
            # only report workflows with any risky marker
            interesting = {k: v for k, v in hits.items()
                           if k in ('selfhost', 'wsl', 'push', 'pull_req', 'pr_target',
                                    'auto_deploy', 'runner_var', 'runner_lbl', 'sudo')}
            if interesting:
                risky.append((f.split('/')[-1], interesting))
        short = br.replace('origin/', '')
        if risky:
            print(f'\n  BRANCH {short}')
            for fn, hits in risky:
                print(f'    {fn:32s} {hits}')
        else:
            print(f'  BRANCH {short:35s} (no risky markers; {len(files)} workflows)')
