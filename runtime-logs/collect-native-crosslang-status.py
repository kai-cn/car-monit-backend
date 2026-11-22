#!/usr/bin/env python3
"""收集 native-image-cloud 与 crosslang-parity-cloud 的最新 run 状态。

思路：
1. 读取 native-crosslang-runs.json 中的派发记录。
2. 按 repo + workflow + branch 查最新 run（workflow_dispatch 分支过滤）。
3. 输出 status/conclusion 到 native-crosslang-status.json，并打印简表。
4. 只读，不修改远端，不下载 artifact。
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',
   'User-Agent':'native-crosslang-status'}
src=Path(r'D:\work\runtime-logs\native-crosslang-runs.json')
out=Path(r'D:\work\runtime-logs\native-crosslang-status.json')
records=json.loads(src.read_text(encoding='utf-8'))

def api(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:
        return json.loads(r.read().decode())

result=[]
for rec in records:
    repo=rec['repo']; branch=rec['branch']; wf=rec['workflow']
    q=urllib.parse.urlencode({'branch':branch,'per_page':1})
    d=api(f'https://api.github.com/repos/{repo}/actions/workflows/{wf}/runs?{q}')
    runs=d.get('workflow_runs',[])
    r=runs[0] if runs else {}
    item={'repo':repo,'branch':branch,'workflow':wf,
          'run_id':r.get('id'),'status':r.get('status'),'conclusion':r.get('conclusion'),
          'created_at':r.get('created_at'),'updated_at':r.get('updated_at')}
    result.append(item)
    print(f"{repo.split('/')[-1]:<22} {branch:<28} {item['run_id']} {item['status']}/{item['conclusion']}")
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('TOTAL',len(result),'SUCCESS',sum(1 for x in result if x['conclusion']=='success'))
