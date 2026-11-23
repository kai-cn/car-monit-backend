#!/usr/bin/env python3
"""Reconcile WSL master with remote and push local commits.

@description Fetch origin master, show divergence, merge remote into local when safe, then push.
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/reconcile-and-push-masters.py
@dependencies WSL master clones and git askpass.
"""
import os
import subprocess
from pathlib import Path

env = dict(os.environ)
env['GIT_ASKPASS'] = '/home/dev/tools/git-askpass.sh'
env['GIT_TERMINAL_PROMPT'] = '0'

for name in ['car-monit-backend', 'car-monit-api']:
    repo = Path('/home/dev/IdeaProjects') / name
    print('===', name, '===')
    subprocess.run(['git', '-C', str(repo), 'fetch', 'origin', 'master'], check=True, env=env)
    base = subprocess.check_output(['git', '-C', str(repo), 'merge-base', 'HEAD', 'origin/master'], text=True).strip()
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    remote = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'origin/master'], text=True).strip()
    print('BASE', base[:10], 'LOCAL', head[:10], 'REMOTE', remote[:10])
    if head != remote:
        print('LOCAL_LOG')
        print(subprocess.check_output(['git', '-C', str(repo), 'log', '--oneline', 'origin/master..HEAD'], text=True))
        print('REMOTE_LOG')
        print(subprocess.check_output(['git', '-C', str(repo), 'log', '--oneline', 'HEAD..origin/master'], text=True))
    # Preserve local work: merge remote via recursive strategy. Abort if conflicts.
    r = subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Tencent Hunyuan Hy',
                        '-c', 'user.email=ai@example.local', 'merge', 'origin/master', '-m',
                        'merge remote master before final body.code push'],
                       env=env, text=True, capture_output=True)
    print('MERGE_RC', r.returncode)
    print((r.stdout + r.stderr)[-1000:])
    if r.returncode:
        continue
    # Commit any remaining working tree changes before pushing.
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    if subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet']).returncode:
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Tencent Hunyuan Hy',
                        '-c', 'user.email=ai@example.local', 'commit', '-m',
                        'docs(evidence): finalize body.code closure'],
                       check=True, env=env)
    subprocess.run(['git', '-C', str(repo), 'push', 'origin', 'HEAD:master'], check=True, env=env)
    print('PUSHED', repo.name, subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--short', 'HEAD'], text=True).strip())
