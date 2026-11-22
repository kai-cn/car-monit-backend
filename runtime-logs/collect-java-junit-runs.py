#!/usr/bin/env python3
"""
@description 历史脚本 collect-java-junit-runs.py：收集云端 run、job 或 artifact 状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python collect-java-junit-runs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json', 'User-Agent': 'collect-junit'}


def api(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    items = json.loads(Path(r'D:\work\runtime-logs\java-junit-runs.json').read_text(encoding='utf-8'))
    for it in items:
        if not it.get('run_id'):
            it['status'], it['conclusion'] = 'UNKNOWN', None
            continue
        d = api(f"https://api.github.com/repos/{it['repo']}/actions/runs/{it['run_id']}")
        it['status'], it['conclusion'] = d['status'], d['conclusion']
        print(it['app'], it['jdk'], it['ref'], it['run_id'], it['status'], it['conclusion'])
    Path(r'D:\work\runtime-logs\java-junit-results.json').write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
