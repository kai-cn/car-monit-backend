#!/usr/bin/env python3

"""
@description 历史脚本 diagnose-failed-java-upgrade.py：批量提取失败任务错误摘要；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python diagnose-failed-java-upgrade.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：


1. 读取 java-upgrade-runs.json 中 status=completed 且 conclusion=failure 的 run。


2. 查 jobs，选 conclusion=failure 的 job，拉取完整 job log。


3. 只输出含 ERROR/COMPILATION/cannot find symbol/missing 等关键词的末尾行，


   并把完整日志保存到 java-upgrade-logs/，便于后续复核。


4. 只读，不修改远端。
"""
import json

import re

import subprocess

import sys

import urllib.request

from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'diag'}

OUT=Path(r'D:\work\runtime-logs\java-upgrade-logs')

OUT.mkdir(exist_ok=True)

recs=json.loads(Path(r'D:\work\runtime-logs\java-upgrade-runs.json').read_text(encoding='utf-8'))

KEY=re.compile(r'ERROR|error:|COMPILATION|cannot find symbol|missing|Invalid|Unexpected|ExceptionInInitializer|NoClassDef')



def api(u):

    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:

        return json.loads(r.read().decode())



def log(u):

    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:

        return r.read().decode('utf-8','replace')



for rec in recs:

    rid=rec.get('run_id')

    if not rid or rec.get('conclusion')!='failure':

        continue

    jobs=api(f"https://api.github.com/repos/{rec['repo']}/actions/runs/{rid}/jobs").get('jobs',[])

    bad=next((j for j in jobs if j.get('conclusion')=='failure'),None)

    if not bad:

        print('NO_FAILED_JOB',rec['branch'],rid); continue

    name=(rec['repo'].split('/')[-1]+'_'+rec['branch'].replace('/','_')+'_'+str(rid)+'.log')

    subprocess.run([sys.executable, r'D:\work\runtime-logs\save_full_joblog.py',

                    rec['repo'], str(bad['id']), str(OUT/name)], check=True,

                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    text=(OUT/name).read_text(encoding='utf-8',errors='replace')

    lines=[l for l in text.splitlines() if KEY.search(l)]

    print('===',rec['branch'],rid,'job',bad['id'])

    for l in lines[-12:]:

        print(l[:240])

