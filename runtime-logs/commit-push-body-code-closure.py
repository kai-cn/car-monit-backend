#!/usr/bin/env python3
"""Commit and push final body.code closure in WSL masters.

@description 使用 WSL 本地 Git 提交所有代码修复、证据与文档，再推送到 master。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/commit-push-body-code-closure.py
@dependencies WSL master clones and git askpass.
"""
import os
import subprocess
from pathlib import Path

REPOS = [Path('/home/dev/IdeaProjects/car-monit-backend'),
         Path('/home/dev/IdeaProjects/car-monit-api')]
MSG = 'fix(parity): finalize endpoint body.code review and documentation'
env = dict(os.environ)
env['GIT_ASKPASS'] = '/home/dev/tools/git-askpass.sh'
env['GIT_TERMINAL_PROMPT'] = '0'

for repo in REPOS:
    print('===', repo.name, '===')
    subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
    if subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet']).returncode:
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Tencent Hunyuan Hy',
                        '-c', 'user.email=ai@example.local', 'commit', '-m', MSG],
                       check=True, env=env)
    else:
        print('NOTHING_TO_COMMIT')
    subprocess.run(['git', '-C', str(repo), 'push', 'origin', 'HEAD:master'], check=True, env=env)
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--short', 'HEAD'], text=True).strip()
    print('PUSHED', repo.name, head)
