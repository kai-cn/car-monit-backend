#!/usr/bin/env python3

"""
@description 历史脚本 collect-java-upgrade-runs.py：收集云端 run、job 或 artifact 状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python collect-java-upgrade-runs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：


1. 读取 dispatch 阶段生成的 java-upgrade-runs.json（repo/branch/workflow/id）。


2. 用 /actions/workflows/{id}/runs?branch=<branch>&per_page=1 查询该分支最新 run。


3. 输出 run id、status、conclusion，并回写同一 JSON 供后续诊断脚本使用。


4. 只读 GitHub Actions 状态，不下载 artifact、不改远端。





注意：派发后可能有几秒延迟；若查不到 run，稍后重跑本脚本即可。
"""
import json

import sys

import urllib.request

from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'java-upgrade-poll'}

PATH=Path(r'D:\work\runtime-logs\java-upgrade-runs.json')

records=json.loads(PATH.read_text(encoding='utf-8'))



def api(u):

    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as r:

        return json.loads(r.read().decode())



for rec in records:

    if rec.get('status')=='ERROR':

        continue

    br=rec['branch'].replace('/','%2F')

    try:

        d=api(f"https://api.github.com/repos/{rec['repo']}/actions/workflows/{rec['id']}/runs?branch={br}&per_page=1")

        runs=d.get('workflow_runs',[])

        if not runs:

            print('PENDING',rec['repo'],rec['branch']); continue

        r=runs[0]

        rec.update({'run_id':r['id'],'status':r['status'],'conclusion':r.get('conclusion'),

                    'created_at':r['created_at'],'updated_at':r['updated_at']})

        print(f"{rec['repo'].split('/')[-1]:20s} {rec['branch']:28s} {r['id']} {r['status']}/{r.get('conclusion')}")

    except Exception as e:

        print('ERROR',rec['repo'],rec['branch'],e)

PATH.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

