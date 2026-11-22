#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：dispatch-java-junit-matrix.py
用途：派发云 runner 任务。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会触发 GitHub Actions，执行前确认分支和 workflow。
"""
"""Dispatch JUnit full-endpoint contract + load runs for every available Java branch.

Idea:
- one control workflow per repo is dispatched on master with target_ref input
- matrix covers Boot2 Java8, Boot4 Java17/21/25 and api Boot3 Java17/21
- record created run ids in java-junit-runs.json for polling/reporting
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
     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'java-junit-dispatch'}

MATRIX = [
    ('kai-cn/car-monit-backend', 'backend', 'master', '8'),
    ('kai-cn/car-monit-backend', 'backend', 'car-monit-backend-java-V3', '8'),
    ('kai-cn/car-monit-backend', 'backend', 'feat/backend-full-parity', '8'),
    ('kai-cn/car-monit-backend', 'backend', 'car-monit-backend-jdk17', '17'),
    ('kai-cn/car-monit-backend', 'backend', 'car-monit-backend-jdk21', '21'),
    ('kai-cn/car-monit-backend', 'backend', 'car-monit-backend-jdk25', '25'),
    ('kai-cn/car-monit-backend', 'backend', 'feature-dbupgrade', '25'),
    ('kai-cn/car-monit-api', 'api', 'master', '8'),
    ('kai-cn/car-monit-api', 'api', 'car-monit-api-java-V3', '8'),
    ('kai-cn/car-monit-api', 'api', 'car-monit-api-java-fix', '8'),
    ('kai-cn/car-monit-api', 'api', 'feature/springboot3-jdk17', '17'),
    ('kai-cn/car-monit-api', 'api', 'feature/springboot3', '21'),
    ('kai-cn/car-monit-api', 'api', 'car-monit-api-jdk17', '17'),
    ('kai-cn/car-monit-api', 'api', 'car-monit-api-jdk21', '21'),
    ('kai-cn/car-monit-api', 'api', 'car-monit-api-jdk25', '25'),
    ('kai-cn/car-monit-api', 'api', 'feature-dbupgrade', '25'),
]


def api(u, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for attempt in range(1, 5):
        try:
            req = urllib.request.Request(u, data=data, headers=H, method=method)
            with urllib.request.urlopen(req, timeout=90) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt.strip() else {}
        except Exception as e:
            last = e
            time.sleep(attempt * 3)
    raise last


def main():
    wf = {}
    for repo in sorted({m[0] for m in MATRIX}):
        d = api(f'https://api.github.com/repos/{repo}/actions/workflows/java-junit-load-cloud.yml')
        wf[repo] = d['id']
    out = []
    for repo, app, ref, jdk in MATRIX:
        before = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        label = f'{app}-{jdk}-{ref.replace("/", "_")}'
        body = {'ref': 'master', 'inputs': {'target_ref': ref, 'app': app, 'jdk': jdk,
                'endpoints': 'full', 'load_threads': '8', 'load_seconds': '30', 'label': label}}
        api(f'https://api.github.com/repos/{repo}/actions/workflows/{wf[repo]}/dispatches', 'POST', body)
        time.sleep(2)
        runs = api(f'https://api.github.com/repos/{repo}/actions/workflows/{wf[repo]}/runs?per_page=100')['workflow_runs']
        run = next((r for r in runs if r['created_at'] >= before and r['head_branch'] == 'master'), None)
        rid = run['id'] if run else None
        out.append({'repo': repo, 'app': app, 'ref': ref, 'jdk': jdk, 'run_id': rid, 'label': label})
        print('DISPATCHED', app, jdk, ref, rid)
    Path(r'D:\work\runtime-logs\java-junit-runs.json').write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
