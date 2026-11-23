#!/usr/bin/env python3
"""Finalize api master with remote evidence and local compatibility fixes.

@description 恢复远端证据文件，workflow 使用远端已验证版本，保留 PostgreSQL interval 与 ES host 修复。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/finalize-api-master.py
@dependencies WSL api master。
"""
import os
import re
import subprocess
from pathlib import Path

A = Path('/home/dev/IdeaProjects/car-monit-api')
env = dict(os.environ)
env['GIT_ASKPASS'] = '/home/dev/tools/git-askpass.sh'
env['GIT_TERMINAL_PROMPT'] = '0'


def git(*args, check=True):
    """Run git command."""
    return subprocess.run(['git', '-C', str(A), *args], check=check, text=True, capture_output=True)


# Restore remote evidence files that were deleted in the stale local branch.
for path in ['runtime-logs/crosslang-evidence.json', 'runtime-logs/crosslang-evidence.md']:
    r = git('checkout', 'origin/master', '--', path)
    print('RESTORE', path, r.returncode)

# Keep remote verified workflow; local duplicate env entries are not needed.
r = git('checkout', 'origin/master', '--', '.github/workflows/crosslang-full-parity-cloud.yml')
print('WORKFLOW', r.returncode)

# Keep go config from remote if local diff is only historical duplicate.
r = git('checkout', 'origin/master', '--', 'car-monit-api-go/configs/config.yaml')
print('GO_CONFIG', r.returncode)

# Correct timestamps in files we keep from local tree.
keep = [
    'car-monit-api-cpp/src/service/track.cpp',
    'car-monit-api-go/internal/repo/zdata_trail_tracks.go',
    'car-monit-api-python/pro-business-api/src/main/resources/com/ruoyi/base/mapper/xml/ZdataTrailTracksMapper.xml',
    'pro-business-api/src/main/java/com/ruoyi/base/mapper/xml/ZdataTrailTracksMapper.xml',
    'pro-business-api/src/main/resources/application.yml',
    'scripts/v3/ops/junit/generate_junit_suite.py',
]
date_re = re.compile(r'@date\s+\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?')
for rel in keep:
    p = A / rel
    if not p.exists():
        continue
    raw = p.read_bytes()
    crlf = b'\r\n' in raw
    t = raw.decode('utf-8', errors='replace')
    t = date_re.sub('@date 2026-11-23 09:01:14', t)
    t = t.replace('@author AI Assistant', '@author Tencent Hunyuan Hy')
    data = (t.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else t).encode('utf-8')
    if data != raw:
        p.write_bytes(data)
        print('NORMALIZED', rel)

git('add', '-A')
if git('diff', '--cached', '--quiet').returncode:
    r = git('-c', 'user.name=Tencent Hunyuan Hy', '-c', 'user.email=ai@example.local',
            'commit', '-m', 'fix(parity): keep SQL ES compatibility and final docs')
    print('COMMIT', r.returncode, (r.stdout + r.stderr)[-500:])
git('push', 'origin', 'HEAD:master')
print('HEAD', git('rev-parse', '--short', 'HEAD').stdout.strip())
