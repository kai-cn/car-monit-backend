#!/usr/bin/env python3

"""
@description 历史脚本 push-final-concentrated.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python push-final-concentrated.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

Idea:


- backend source branch receives runtime-logs docs/evidence/scripts and final report.


- api source branch receives memory, review docs and final report.


- use Git Data API tree/commit/ref updates, so each repo gets exactly one commit.


- abort if obvious real credentials are found in local script contents.
"""
import base64

import json

import re

import subprocess

import sys

import urllib.request

from pathlib import Path



sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',

     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'final-concentrated-push'}

BASE = Path(r'D:\work\runtime-logs')

API_V3 = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3')

BK_V3 = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')

SECRET = re.compile(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')





def api(u, method='GET', body=None):

    data = json.dumps(body).encode() if body is not None else None

    with urllib.request.urlopen(urllib.request.Request(u, data=data, headers=H, method=method), timeout=180) as r:

        txt = r.read().decode()

        return json.loads(txt) if txt.strip() else {}





def commit_files(repo, branch, message, files):

    ref = api(f'https://api.github.com/repos/{repo}/git/ref/heads/{branch}')

    base = ref['object']['sha']

    base_commit = api(f'https://api.github.com/repos/{repo}/git/commits/{base}')

    tree = []

    for local, remote in files:

        content = Path(local).read_bytes()

        if remote.endswith(('.py', '.ps1', '.sh')) and SECRET.search(content.decode('utf-8', errors='replace')):

            raise SystemExit('SECRET_FOUND ' + str(local))

        blob = api(f'https://api.github.com/repos/{repo}/git/blobs', 'POST',

                   {'content': base64.b64encode(content).decode(), 'encoding': 'base64'})

        tree.append({'path': remote, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})

    new_tree = api(f'https://api.github.com/repos/{repo}/git/trees', 'POST',

                   {'base_tree': base_commit['tree']['sha'], 'tree': tree})

    commit = api(f'https://api.github.com/repos/{repo}/git/commits', 'POST',

                 {'message': message, 'tree': new_tree['sha'], 'parents': [base]})

    api(f'https://api.github.com/repos/{repo}/git/refs/heads/{branch}', 'PATCH',

        {'sha': commit['sha'], 'force': False})

    print('COMMIT', repo, branch, commit['sha'], 'files', len(files))





def main():

    backend_files = []

    # Docs and evidence in backend source branch runtime-logs.

    for name in ['SESSION-HANDOFF.md', '公开仓库安全加固-任务清单.md',

                 '公开仓库安全加固-脚本与证据索引.md', 'final-java-junit-crosslang-20261122.md',

                 'crosslang-evidence.md', 'crosslang-evidence.json',

                 'java-junit-results.json', 'crosslang-full-results.json',

                 'native-crosslang-status.json', 'java-upgrade-runs.json']:

        p = BASE / name

        if p.exists():

            backend_files.append((p, 'runtime-logs/' + name))

    for name in ['local-rerun-evidence.json', 'local-rerun-evidence.md',

                 'local-junit-smoke.json', 'local-junit-smoke.md']:

        p = BASE / 'local-rerun-evidence' / name

        if p.exists():

            backend_files.append((p, 'runtime-logs/local-rerun-evidence/' + name))

    # All annotated operational scripts, one commit.

    for p in sorted(BASE.rglob('*')):

        if p.suffix.lower() not in {'.py', '.ps1', '.sh'}:

            continue

        if any(part in {'__pycache__', '.git', 'node_modules', 'venv'} for part in p.parts):

            continue

        rel = p.relative_to(BASE).as_posix()

        backend_files.append((p, 'runtime-logs/' + rel))

    # Deduplicate paths, keep last.

    dedup = {}

    for local, remote in backend_files:

        dedup[remote] = (local, remote)

    commit_files('kai-cn/car-monit-backend', 'car-monit-backend-java-V3',

                 'docs(ops): record final JUnit and cross-language verification',

                 list(dedup.values()))



    api_files = [

        (API_V3 / '.workbuddy/memory/2026-11-22.md', '.workbuddy/memory/2026-11-22.md'),

        (API_V3 / 'docs/v3/review/12-session-handoff-20261118.md', 'docs/v3/review/12-session-handoff-20261118.md'),

        (API_V3 / 'docs/v3/review/12-repro-index-20261118.md', 'docs/v3/review/12-repro-index-20261118.md'),

        (API_V3 / 'docs/v3/review/13-final-junit-crosslang-20261122.md', 'docs/v3/review/13-final-junit-crosslang-20261122.md'),

    ]

    commit_files('kai-cn/car-monit-api', 'car-monit-api-java-V3',

                 'docs(review): record final JUnit and cross-language verification',

                 [(p, r) for p, r in api_files if p.exists()])





if __name__ == '__main__':

    main()

