#!/usr/bin/env python3
"""为所有 Java 分支派发云端升级验证 run。

思路：
1. 优先用 parity-verify-cloud.yml（native + 全端点业务一致性），输入 platform=linux、repeat=1。
2. 没有 parity workflow 的 V3/fix 分支，用 master.yml / ci.yml 做完整 Java 构建门禁。
3. workflow id 从 GitHub /actions/workflows 按 path 取得；dispatch ref 指定目标分支。
4. 每个 run 记录到 java-upgrade-runs.json，后续轮询脚本只读这个文件。

风险：同一时间派发多个 run 会消耗 Actions 分钟，但公开仓库免费；不下载 artifact，
验证结论全部从云端 job 日志读取。脚本只 dispatch，不修改仓库内容。
"""
import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',
   'X-GitHub-Api-Version':'2022-11-28','User-Agent':'java-upgrade-dispatch'}
PLANS={
 'kai-cn/car-monit-api':[
   ('master','java-upgrade-verify.yml'),
   ('car-monit-api-java-V3','java-upgrade-verify.yml'),
   ('car-monit-api-java-fix','java-upgrade-verify.yml'),
   ('car-monit-api-jdk17','parity-verify-cloud.yml'),
   ('car-monit-api-jdk21','parity-verify-cloud.yml'),
   ('car-monit-api-jdk25','parity-verify-cloud.yml'),
   ('feature/springboot3','parity-verify-cloud.yml'),
   ('feature/springboot3-jdk17','parity-verify-cloud.yml'),
   ('feature-dbupgrade','parity-verify-cloud.yml'),
 ],
 'kai-cn/car-monit-backend':[
   ('master','java-upgrade-verify.yml'),
   ('car-monit-backend-java-V3','java-upgrade-verify.yml'),
   ('car-monit-backend-jdk17','parity-verify-cloud.yml'),
   ('car-monit-backend-jdk21','parity-verify-cloud.yml'),
   ('car-monit-backend-jdk25','parity-verify-cloud.yml'),
   ('feat/backend-full-parity','java-upgrade-verify.yml'),
   ('feature-dbupgrade','parity-verify-cloud.yml'),
 ],
}
OUT=Path(r'D:\work\runtime-logs\java-upgrade-runs.json')

def api(u, method='GET', body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(u,data=data,headers=H,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode()
    return json.loads(raw) if raw.strip() else {}

records=[]
for repo, plans in PLANS.items():
    wf=api(f'https://api.github.com/repos/{repo}/actions/workflows?per_page=100')
    ids={x['path'].split('/')[-1]:x['id'] for x in wf['workflows']}
    for branch, filename in plans:
        wid=ids.get(filename)
        if not wid:
            print('NO_WORKFLOW_ID',repo,branch,filename); continue
        body={'ref':branch}
        if filename=='parity-verify-cloud.yml':
            body['inputs']={'platform':'linux','repeat':'1'}
        try:
            api(f'https://api.github.com/repos/{repo}/actions/workflows/{wid}/dispatches','POST',body)
            records.append({'repo':repo,'branch':branch,'workflow':filename,'id':wid,'status':'dispatched'})
            print('DISPATCHED',repo,branch,filename)
        except Exception as e:
            records.append({'repo':repo,'branch':branch,'workflow':filename,'id':wid,'status':'ERROR','error':str(e)})
            print('ERROR',repo,branch,filename,e)
OUT.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('TOTAL',len(records))
