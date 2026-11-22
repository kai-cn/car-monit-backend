#!/usr/bin/env python3
"""重跑全部 Java native-image cloud workflow，以及 Java 对比的跨语言 workflow。

思路：
1. native-image-cloud.yml 在 api/backend 默认分支均存在，先用文件名取 workflow id。
2. 对每个含 native workflow 的 Java 分支派发 stage=build，app 按仓库设置，
   jdk 按分支名映射；platform=linux、runner_mode=cloud。
3. 跨语言 workflow 只在 backend master 派发一次，langs=all。
4. 保存 run id 到 native-crosslang-runs.json，便于后续统一轮询。

风险：native 构建耗时较长；本脚本只派发，不取消、不下载 artifact。
"""
import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',
   'X-GitHub-Api-Version':'2022-11-28','User-Agent':'native-crosslang-dispatch'}
PLANS=[
 # Boot2 master/full-parity have no native profile; native build is N/A for them.
 # Boot3/Boot4 branches all use Mandrel25 toolchain; source java.version stays unchanged.
 ('kai-cn/car-monit-api','car-monit-api-jdk17','api','25'),
 ('kai-cn/car-monit-api','car-monit-api-jdk21','api','25'),
 ('kai-cn/car-monit-api','car-monit-api-jdk25','api','25'),
 ('kai-cn/car-monit-api','feature-dbupgrade','api','25'),
 ('kai-cn/car-monit-api','feature/springboot3','api','25'),
 ('kai-cn/car-monit-api','feature/springboot3-jdk17','api','25'),
 ('kai-cn/car-monit-backend','car-monit-backend-jdk17','backend','25'),
 ('kai-cn/car-monit-backend','car-monit-backend-jdk21','backend','25'),
 ('kai-cn/car-monit-backend','car-monit-backend-jdk25','backend','25'),
 ('kai-cn/car-monit-backend','feature-dbupgrade','backend','25'),
]

def api(u,method='GET',body=None):
    data=json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(u,data=data,headers=H,method=method),timeout=90) as r:
        txt=r.read().decode()
        return json.loads(txt) if txt.strip() else {}

wid_cache={}
def workflow_id(repo,path):
    key=(repo,path)
    if key not in wid_cache:
        wid_cache[key]=api(f'https://api.github.com/repos/{repo}/actions/workflows/{path}')['id']
    return wid_cache[key]

def dispatch(repo,wf,branch,inputs):
    wid=workflow_id(repo,wf)
    api(f'https://api.github.com/repos/{repo}/actions/workflows/{wid}/dispatches','POST',
        {'ref':branch,'inputs':inputs})

records=[]
for repo,branch,app,jdk in PLANS:
    inputs={'release_tag':'','stage':'build','app':app,'jdk':jdk,'platform':'linux',
            'runner_mode':'cloud','linux_runner':'ubuntu-latest','windows_runner':'windows-latest'}
    try:
        dispatch(repo,'native-image-cloud.yml',branch,inputs)
        rec={'repo':repo,'branch':branch,'workflow':'native-image-cloud.yml','inputs':inputs,'status':'dispatched'}
        print('DISPATCHED native',repo,branch)
    except Exception as e:
        rec={'repo':repo,'branch':branch,'workflow':'native-image-cloud.yml','error':str(e),'status':'failed'}
        print('FAILED native',repo,branch,e)
    records.append(rec)

try:
    dispatch('kai-cn/car-monit-backend','crosslang-parity-cloud.yml','master',
             {'langs':'all','linux_runner':'ubuntu-latest'})
    records.append({'repo':'kai-cn/car-monit-backend','branch':'master','workflow':'crosslang-parity-cloud.yml','status':'dispatched'})
    print('DISPATCHED crosslang backend master')
except Exception as e:
    records.append({'repo':'kai-cn/car-monit-backend','branch':'master','workflow':'crosslang-parity-cloud.yml','error':str(e),'status':'failed'})
    print('FAILED crosslang',e)

out=Path(r'D:\work\runtime-logs\native-crosslang-runs.json')
out.write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('TOTAL',len(records))
