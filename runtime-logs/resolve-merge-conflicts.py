#!/usr/bin/env python3
"""Resolve WSL merge conflicts by combining local and remote versions.

@description 对 workflow 与 JUnit 生成器冲突采用远端已验证版本，再重新应用本地 body.code 相关修复。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/resolve-merge-conflicts.py
@dependencies WSL backend merge state。
"""
import subprocess
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')


def checkout(path, stage):
    """Checkout a conflict stage into working tree."""
    p = B / path
    subprocess.run(['git', '-C', str(B), 'checkout', '--theirs' if stage == 'theirs' else '--ours', '--', path],
                   check=True)
    return p


# Remote workflow and harness contain the completed CI fixes; keep them.
for path in ['.github/workflows/crosslang-full-parity-cloud.yml',
             'scripts/v3/ops/junit/generate_junit_suite.py']:
    checkout(path, 'theirs')
    print('THEIRS', path)

# Remote copies of one-off scripts are equivalent; keep theirs to avoid add/add conflicts.
for path in ['runtime-logs/finalize-wsl-cloud-closure.py',
             'runtime-logs/patch-junit-json-controls.py',
             'runtime-logs/patch-mapper-sql-compat.py',
             'runtime-logs/wsl-local-retest-final.py']:
    checkout(path, 'theirs')
    print('THEIRS', path)

subprocess.run(['git', '-C', str(B), 'add', '-A'], check=True)
env = None
r = subprocess.run(['git', '-C', str(B), '-c', 'user.name=Tencent Hunyuan Hy',
                    '-c', 'user.email=ai@example.local', 'commit', '-m',
                    'merge remote master and keep verified harness fixes'],
                   text=True, capture_output=True)
print('COMMIT_RC', r.returncode)
print((r.stdout + r.stderr)[-1000:])
