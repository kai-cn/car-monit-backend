#!/usr/bin/env python3
"""
@description 历史脚本 diagnose-native-failures.py：批量提取失败任务错误摘要；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python diagnose-native-failures.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：读取 native-crosslang-status.json 中 conclusion=failure 的 run；

查 failed job，调用 save_full_joblog.py 保存日志到 native-logs/，

再输出含 ERROR/COMPILATION/cannot find/missing 等关键词的末尾行。

只读诊断，不修改远端。
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'native-diag'}
OUT=Path(r'D:\work\runtime-logs\native-logs'); OUT.mkdir(exist_ok=True)
items=json.loads(Path(r'D:\work\runtime-logs\native-crosslang-status.json').read_text(encoding='utf-8'))
KEY=re.compile(r'ERROR|error:|COMPILATION|cannot find symbol|missing|Invalid|Unexpected|ExceptionInInitializer|NoClassDef|failed')

def api(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:
        return json.loads(r.read().decode())

for it in items:
    if it.get('conclusion')!='failure' or it['workflow']!='native-image-cloud.yml':
        continue
    jobs=api(f"https://api.github.com/repos/{it['repo']}/actions/runs/{it['run_id']}/jobs").get('jobs',[])
    bad=next((j for j in jobs if j.get('conclusion')=='failure'),None)
    if not bad:
        print('NO_FAILED_JOB',it['branch'],it['run_id']); continue
    name=f"{it['repo'].split('/')[-1]}_{it['branch'].replace('/','_')}_{it['run_id']}.log"
    subprocess.run([sys.executable,r'D:\work\runtime-logs\save_full_joblog.py',it['repo'],str(bad['id']),str(OUT/name)],
                   check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    text=(OUT/name).read_text(encoding='utf-8',errors='replace')
    print('===',it['branch'],it['run_id'],'job',bad['id'])
    for l in [x for x in text.splitlines() if KEY.search(x)][-18:]:
        print(l[:240])
