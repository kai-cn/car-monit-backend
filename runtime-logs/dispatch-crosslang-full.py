#!/usr/bin/env python3
"""
@description 历史脚本 dispatch-crosslang-full.py：派发或重派云端 runner 任务；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python dispatch-crosslang-full.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

Idea:

- each repo's master control workflow uses Java25 Boot4 baseline branch

- inputs pin full endpoint set and all four candidates (python/go/cpp/rust)

- save run ids for later status collection
"""
import datetime
import json
import sys
import time
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'crosslang-full-dispatch'}
PLANS = [
    ('kai-cn/car-monit-backend', 'car-monit-backend-jdk25', 'backend'),
    ('kai-cn/car-monit-api', 'car-monit-api-jdk25', 'api'),
]


def api(u, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, data=data, headers=H, method=method), timeout=90) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt.strip() else {}
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise last


def main():
    out = []
    for repo, ref, app in PLANS:
        before = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        body = {'ref': 'master', 'inputs': {'target_ref': ref, 'app': app, 'langs': 'all',
                'load_threads': '8', 'load_seconds': '30', 'label': f'{app}-java25-crosslang-full'}}
        wf = api(f'https://api.github.com/repos/{repo}/actions/workflows/crosslang-full-parity-cloud.yml')['id']
        api(f'https://api.github.com/repos/{repo}/actions/workflows/{wf}/dispatches', 'POST', body)
        time.sleep(3)
        runs = api(f'https://api.github.com/repos/{repo}/actions/workflows/{wf}/runs?per_page=20')['workflow_runs']
        run = next((r for r in runs if r['created_at'] >= before and r['head_branch'] == 'master'), None)
        rid = run['id'] if run else None
        out.append({'repo': repo, 'app': app, 'ref': ref, 'run_id': rid})
        print('DISPATCHED', app, rid)
    Path(r'D:\work\runtime-logs\crosslang-full-runs.json').write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
