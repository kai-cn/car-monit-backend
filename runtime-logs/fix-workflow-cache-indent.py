#!/usr/bin/env python3
"""Fix `cache: maven` inserted at step level instead of inside the step's `with:` block.

A previous optimization pass emitted:
      - uses: actions/setup-java@v4
        cache: maven
        with:
          ...
which GitHub rejects with "Unexpected value 'cache'". This script moves the key
inside `with:` on every workflow of both repositories.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

GH_API = r'D:\work\runtime-logs\gh_api.ps1'
FETCH = r'D:\work\runtime-logs\fetch-remote-file.ps1'
PUT = r'D:\work\runtime-logs\put-remote-file.ps1'
REPOS = ['kai-cn/car-monit-api', 'kai-cn/car-monit-backend']


def ps(script, *args):
    cp = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                         '-File', script, *args], capture_output=True, text=True,
                        encoding='utf-8', errors='replace')
    return cp.stdout or ''


def api_get(uri):
    return ps(GH_API, '-Method', 'GET', '-Uri', uri)


def parse_sha_or_names(raw, key):
    try:
        obj = json.loads(raw)
    except Exception:
        return []
    return [item[key] for item in obj if isinstance(item, dict) and key in item]


def fix(text):
    lines = text.split('\n')
    out = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == 'cache: maven':
            indent = line[:len(line) - len(line.lstrip())]
            # find a sibling `with:` in the next few lines
            with_idx = -1
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip() == 'with:' and lines[j][:len(lines[j]) - len(lines[j].lstrip())] == indent:
                    with_idx = j
                    break
            if with_idx >= 0:
                child = indent + '  cache: maven'
                # avoid duplicate inside with:
                exists = False
                for j in range(with_idx + 1, min(with_idx + 12, len(lines))):
                    if lines[j].strip().startswith('cache:'):
                        exists = True
                    if lines[j].strip() == 'uses:':
                        break
                if not exists:
                    out.append(indent + '# Perf: Maven dependency cache; key follows pom.xml changes.')
                    out.append(lines[with_idx])
                    out.append(child)
                    changed = True
                # skip original cache line and the original with line
                i += 1
                # copy everything between i and with_idx except the with line
                for k in range(i, with_idx):
                    out.append(lines[k])
                i = with_idx + 1
                continue
        out.append(line)
        i += 1
    return '\n'.join(out), changed


total = 0
for repo in REPOS:
    short = repo.split('/')[-1]
    branches = parse_sha_or_names(api_get(f'https://api.github.com/repos/{repo}/branches?per_page=100'), 'name')
    print(f'REPO={repo} branches={len(branches)}')
    for br in branches:
        enc = br.replace('/', '%2F')
        paths = parse_sha_or_names(api_get(f'https://api.github.com/repos/{repo}/contents/.github/workflows?ref={enc}'), 'path')
        for p in paths:
            fd, tmp = tempfile.mkstemp(suffix='.yml')
            os.close(fd)
            ps(FETCH, '-Repo', short, '-Branch', br, '-Path', p, '-Out', tmp)
            if not Path(tmp).exists() or Path(tmp).stat().st_size == 0:
                continue
            orig = Path(tmp).read_text(encoding='utf-8', errors='replace')
            fixed, changed = fix(orig)
            if changed:
                Path(tmp).write_text(fixed, encoding='utf-8')
                ps(PUT, '-Repo', repo, '-Branch', br, '-Path', p, '-Src', tmp,
                   '-Message', 'ci(fix): move Maven cache option inside with: block')
                print(f'FIX {br}/{p}')
                total += 1
            Path(tmp).unlink(missing_ok=True)
print('FIXED_FILES=', total)
