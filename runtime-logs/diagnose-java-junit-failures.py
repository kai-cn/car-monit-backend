#!/usr/bin/env python3
"""
@description 历史脚本 diagnose-java-junit-failures.py：批量提取失败任务错误摘要；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python diagnose-java-junit-failures.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

Idea:

- read java-junit-results.json produced by collect-java-junit-runs.py

- for each failed run, call GitHub Actions jobs API directly (no PowerShell dependency)

- download the failed job log with the existing authenticated save_full_joblog.py

- print the most authoritative error lines so fixes can be batched



This script is read-only with respect to remote state; it only writes local logs.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

BASE = Path(r'D:\work\runtime-logs')
PATTERNS = [
    'APPLICATION FAILED', 'Description:', 'Action:', 'Caused by:',
    'Error creating bean', 'No qualifying bean', 'Failed to configure a DataSource',
    'Communications link failure', 'Access denied for user', 'Unknown database',
    'Connection refused', 'Process completed with exit code', 'Build failed',
    'COMPILATION ERROR', 'ERROR:', 'service process exited', 'service readiness timeout',
    'mkdir: Permission denied', 'Failed to execute goal', 'BUILD FAILURE',
]
HEADERS = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
           'User-Agent': 'diagnose-java-junit'}


def api(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    results = json.loads((BASE / 'java-junit-results.json').read_text(encoding='utf-8'))
    failed = [x for x in results if x.get('conclusion') == 'failure']
    print('FAILED_RUNS', len(failed))
    for item in failed:
        rid, repo = item['run_id'], item['repo']
        if not rid:
            continue
        jobs = api(f'https://api.github.com/repos/{repo}/actions/runs/{rid}/jobs')['jobs']
        bad = next((j for j in jobs if j.get('conclusion') == 'failure'), None)
        print('===', repo, item['ref'], rid, 'job', bad['id'] if bad else None)
        if not bad:
            continue
        name = f"junit-{repo.split('/')[-1]}-{item['ref'].replace('/', '_')}-{rid}.log"
        path = BASE / 'junit-logs' / name
        path.parent.mkdir(exist_ok=True)
        subprocess.run([sys.executable, str(BASE / 'save_full_joblog.py'), repo, str(bad['id']), str(path)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if not path.exists():
            print('  log missing')
            continue
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        hits = [ln for ln in lines if any(p in ln for p in PATTERNS)]
        for ln in hits[-20:]:
            print(' ', ln[ln.find('Z ') + 2:] if 'Z ' in ln else ln)


if __name__ == '__main__':
    main()
