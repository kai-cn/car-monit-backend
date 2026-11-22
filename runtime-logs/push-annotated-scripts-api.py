#!/usr/bin/env python3

"""
@description 历史脚本 push-annotated-scripts-api.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python push-annotated-scripts-api.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：


1. 从远端分支 tree 读取现存 runtime-logs/*.py/.ps1/.sh 路径。


2. 只推送这些"已入库且经过安全审查"的路径；本地源中新增但远端不存在的脚本不推送，


   避免重新引入此前被排除的含凭据脚本。


3. 每个文件先 GET sha 再 PUT，幂等。


4. 不 force push、不删除文件、不下载 artifact。
"""
import base64, json, sys, urllib.request

from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



REPO='kai-cn/car-monit-backend'

BRANCH='car-monit-backend-java-V3'

SRC=Path(r'D:\work\runtime-logs')

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',

   'X-GitHub-Api-Version':'2022-11-28','User-Agent':'annotated-script-push'}



def api(u,method='GET',body=None):

    data=json.dumps(body).encode() if body is not None else None

    with urllib.request.urlopen(urllib.request.Request(u,data=data,headers=H,method=method),timeout=90) as r:

        txt=r.read().decode()

        return json.loads(txt) if txt.strip() else {}



sha=api(f'https://api.github.com/repos/{REPO}/git/ref/heads/{BRANCH}')['object']['sha']

tree=api(f'https://api.github.com/repos/{REPO}/git/trees/{sha}?recursive=1')

paths=[x['path'] for x in tree.get('tree',[])

       if x['path'].startswith('runtime-logs/') and x['path'].lower().endswith(('.py','.ps1','.sh'))]

print('REMOTE_SCRIPTS',len(paths))

done=0

for path in paths:

    local=SRC/path[len('runtime-logs/'):]

    if not local.exists():

        continue

    text=local.read_text(encoding='utf-8',errors='replace')

    enc=path.replace(' ','%20')

    try:

        old=api(f'https://api.github.com/repos/{REPO}/contents/{enc}?ref={BRANCH}')

        osha=old.get('sha')

    except Exception:

        osha=None

    body={'message':'docs(scripts): add rationale and risk notes to historical scripts',

          'content':base64.b64encode(text.encode('utf-8')).decode(),'branch':BRANCH}

    if osha: body['sha']=osha

    api(f'https://api.github.com/repos/{REPO}/contents/{enc}','PUT',body)

    done+=1

print('PUSHED',done)

