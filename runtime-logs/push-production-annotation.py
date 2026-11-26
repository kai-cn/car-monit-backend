#!/usr/bin/env python3
"""
@description 一次性推送生产级注释收口材料：向 backend 源分支提交文档、证据与全部注释脚本，向 api 源分支提交记忆与复现文档。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python push-production-annotation.py
@dependencies GitHub API 本地缓存凭据；仅使用 Git Data API 更新固定源分支，不 force push。
"""
import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'production-annotation-push'}
BASE = Path(r'D:\work\runtime-logs')
BK_V3 = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')
API_V3 = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3')
SECRET = re.compile(r'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')


def api(url, method='GET', body=None):
    """调用 GitHub API；凭据只从内存读取，不打印响应中的敏感字段。"""
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=H, method=method), timeout=180) as r:
        text = r.read().decode()
        return json.loads(text) if text.strip() else {}


def one_commit(repo, branch, message, pairs):
    """把多文件作为一个树对象提交到指定分支；发现疑似真实凭据立即终止。"""
    ref = api(f'https://api.github.com/repos/{repo}/git/ref/heads/{branch}')
    base = ref['object']['sha']
    parent = api(f'https://api.github.com/repos/{repo}/git/commits/{base}')
    tree = []
    for local, remote in pairs:
        p = Path(local)
        content = p.read_bytes()
        if remote.endswith(('.py', '.ps1', '.sh')) and SECRET.search(content.decode('utf-8', errors='replace')):
            raise SystemExit('SECRET_FOUND ' + str(p))
        blob = api(f'https://api.github.com/repos/{repo}/git/blobs', 'POST',
                   {'content': base64.b64encode(content).decode(), 'encoding': 'base64'})
        tree.append({'path': remote, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    new_tree = api(f'https://api.github.com/repos/{repo}/git/trees', 'POST',
                   {'base_tree': parent['tree']['sha'], 'tree': tree})
    commit = api(f'https://api.github.com/repos/{repo}/git/commits', 'POST',
                 {'message': message, 'tree': new_tree['sha'], 'parents': [base]})
    api(f'https://api.github.com/repos/{repo}/git/refs/heads/{branch}', 'PATCH',
        {'sha': commit['sha'], 'force': False})
    print('COMMIT', repo, branch, commit['sha'], 'files', len(pairs))


def main():
    pairs = []
    docs = ['SESSION-HANDOFF.md', '公开仓库安全加固-任务清单.md',
            '公开仓库安全加固-脚本与证据索引.md', 'final-java-junit-crosslang-20261122.md',
            '从头复现步骤-20261122.md', 'crosslang-evidence.md', 'crosslang-evidence.json',
            'java-junit-results.json', 'crosslang-full-results.json',
            'native-crosslang-status.json', 'java-upgrade-runs.json']
    pairs.extend((BASE / n, 'runtime-logs/' + n) for n in docs if (BASE / n).exists())
    for n in ['local-rerun-evidence.json', 'local-rerun-evidence.md',
              'local-junit-smoke.json', 'local-junit-smoke.md']:
        p = BASE / 'local-rerun-evidence' / n
        if p.exists():
            pairs.append((p, 'runtime-logs/local-rerun-evidence/' + n))
    for n in ['local-package-results.json', 'local-package-results.md']:
        p = BASE / 'local-package-evidence' / n
        if p.exists():
            pairs.append((p, 'runtime-logs/local-package-evidence/' + n))
    for n in ['junit-contract.json', 'junit-load.json']:
        p = BASE / 'wsl-retest-evidence' / n
        if p.exists():
            pairs.append((p, 'runtime-logs/wsl-retest-evidence/' + n))
    for p in sorted(BASE.rglob('*')):
        if p.suffix.lower() not in {'.py', '.ps1', '.sh'}:
            continue
        if any(part in {'__pycache__', '.git', 'node_modules', 'venv'} for part in p.parts):
            continue
        pairs.append((p, 'runtime-logs/' + p.relative_to(BASE).as_posix()))
    for n in ['12-session-handoff-20261118.md', '13-final-junit-crosslang-20261122.md',
              '14-reproduction-from-scratch-20261122.md']:
        p = BK_V3 / 'docs/v3/review' / n
        if p.exists():
            pairs.append((p, 'docs/v3/review/' + n))
    dedup = {remote: (local, remote) for local, remote in pairs}
    one_commit('kai-cn/car-monit-backend', 'car-monit-backend-java-V3',
               'docs(ops): record production annotation, local retest and reproduction', list(dedup.values()))

    api_pairs = []
    for local, remote in [
        (API_V3 / '.workbuddy/memory/2026-11-22.md', '.workbuddy/memory/2026-11-22.md'),
        (API_V3 / 'docs/v3/review/12-session-handoff-20261118.md', 'docs/v3/review/12-session-handoff-20261118.md'),
        (API_V3 / 'docs/v3/review/12-repro-index-20261118.md', 'docs/v3/review/12-repro-index-20261118.md'),
        (API_V3 / 'docs/v3/review/13-final-junit-crosslang-20261122.md', 'docs/v3/review/13-final-junit-crosslang-20261122.md'),
        (API_V3 / 'docs/v3/review/14-reproduction-from-scratch-20261122.md', 'docs/v3/review/14-reproduction-from-scratch-20261122.md'),
    ]:
        if Path(local).exists():
            api_pairs.append((local, remote))
    one_commit('kai-cn/car-monit-api', 'car-monit-api-java-V3',
               'docs(review): record production annotation, local retest and reproduction', api_pairs)


if __name__ == '__main__':
    main()
