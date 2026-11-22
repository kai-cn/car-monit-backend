#!/usr/bin/env python3
"""
@description 历史脚本 cancel-stale-native-crosslang.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python cancel-stale-native-crosslang.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：

1. 读取 native-crosslang-status.json 中当前 run id。

2. 按 repo + workflow + branch 列出最近 20 个 run。

3. 只取消 status 为 queued/in_progress 且 id 不是当前 run 的旧任务。

4. 不取消 completed run，不影响其他 workflow。
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',
   'X-GitHub-Api-Version':'2022-11-28','User-Agent':'cancel-stale'}
items=json.loads(Path(r'D:\work\runtime-logs\native-crosslang-status.json').read_text(encoding='utf-8'))

def api(u,method='GET'):
    with urllib.request.urlopen(urllib.request.Request(u,headers=H,method=method),timeout=90) as r:
        txt=r.read().decode()
        return json.loads(txt) if txt.strip() else {}

for it in items:
    cur=it.get('run_id')
    q=urllib.parse.urlencode({'branch':it['branch'],'per_page':20})
    runs=api(f"https://api.github.com/repos/{it['repo']}/actions/workflows/{it['workflow']}/runs?{q}").get('workflow_runs',[])
    for r in runs:
        if r['id']==cur or r.get('status') not in ('queued','in_progress'):
            continue
        try:
            api(f"https://api.github.com/repos/{it['repo']}/actions/runs/{r['id']}/cancel",'POST')
            print('CANCELLED',it['branch'],r['id'])
        except Exception as e:
            print('SKIP',r['id'],e)
