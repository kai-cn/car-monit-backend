#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：scan-runs-after-1641.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
"""只读扫描 2026-11-21 16:41(+08) 后两仓库全部 Actions run。"""
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
