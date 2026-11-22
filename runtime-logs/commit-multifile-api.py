#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：commit-multifile-api.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
"""Create one GitHub commit containing many local files.

Why: writing each file through the contents API creates one commit per file,
which polluted history. This helper builds blobs + one tree + one commit and
updates the branch ref with a single update-ref call.

Usage:
  python commit-multifile-api.py --repo owner/name --branch master \
    --message "feat: ..." --file local/path=repo/path [--file ...]
"""
import argparse
import base64
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'multifile-commit'}


def api(u, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(u, data=data, headers=H, method=method), timeout=120) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt.strip() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--branch', required=True)
    ap.add_argument('--message', required=True)
    ap.add_argument('--file', action='append', required=True, help='local=repo path')
    a = ap.parse_args()

    ref = api(f'https://api.github.com/repos/{a.repo}/git/ref/heads/{a.branch}')
    base_sha = ref['object']['sha']
    base_commit = api(f'https://api.github.com/repos/{a.repo}/git/commits/{base_sha}')
    tree = []
    for spec in a.file:
        local, remote = spec.split('=', 1)
        content = Path(local).read_bytes()
        blob = api(f'https://api.github.com/repos/{a.repo}/git/blobs', 'POST',
                   {'content': base64.b64encode(content).decode(), 'encoding': 'base64'})
        tree.append({'path': remote, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    new_tree = api(f'https://api.github.com/repos/{a.repo}/git/trees', 'POST',
                   {'base_tree': base_commit['tree']['sha'], 'tree': tree})
    commit = api(f'https://api.github.com/repos/{a.repo}/git/commits', 'POST',
                 {'message': a.message, 'tree': new_tree['sha'], 'parents': [base_sha]})
    api(f'https://api.github.com/repos/{a.repo}/git/refs/heads/{a.branch}', 'PATCH',
        {'sha': commit['sha'], 'force': False})
    print(commit['sha'])


if __name__ == '__main__':
    main()
