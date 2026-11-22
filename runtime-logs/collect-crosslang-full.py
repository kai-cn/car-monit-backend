#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：collect-crosslang-full.py
用途：收集云端 run 状态。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：只读远端状态，不修改分支。
"""
"""Collect status of cross-language full parity runs."""
import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json', 'User-Agent': 'collect-crosslang'}


def api(u):
    last = None
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=90) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            import time
            time.sleep(attempt * 3)
    raise last


def main():
    items = json.loads(Path(r'D:\work\runtime-logs\crosslang-full-runs.json').read_text(encoding='utf-8'))
    for it in items:
        if not it.get('run_id'):
            it['status'], it['conclusion'] = 'UNKNOWN', None
            continue
        u = f"https://api.github.com/repos/{it['repo']}/actions/runs/{it['run_id']}"
        d = api(u)
        it['status'], it['conclusion'] = d['status'], d['conclusion']
        print(it['app'], it['run_id'], it['status'], it['conclusion'])
    Path(r'D:\work\runtime-logs\crosslang-full-results.json').write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
