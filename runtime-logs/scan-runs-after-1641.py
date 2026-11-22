#!/usr/bin/env python3
"""
@description 历史脚本 scan-runs-after-1641.py：扫描远端或本地状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python scan-runs-after-1641.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import json, sys, urllib.request
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

SINCE='2026-11-21T08:41:00Z'
H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'scan-runs-after'}
for repo in ['kai-cn/car-monit-api','kai-cn/car-monit-backend']:
    runs=[]
    page=1
    while True:
        u=f'https://api.github.com/repos/{repo}/actions/runs?since={SINCE}&per_page=100&page={page}'
        with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:
            d=json.loads(r.read().decode())
        runs += d.get('workflow_runs',[])
        if len(runs)>=d.get('total_count',0) or not d.get('workflow_runs'): break
        page+=1
    print('===',repo,'runs',len(runs))
    for r in sorted(runs,key=lambda x:x['created_at']):
        if r['created_at'] < SINCE: continue
        print(r['id'],r['created_at'],r['name'],r['head_branch'],r['status'],r['conclusion'],r['event'])
