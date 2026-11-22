#!/usr/bin/env python3

"""
@description 历史脚本 check-target-contiguity.py：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python check-target-contiguity.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import json, sys, urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token

TARGET='docs(scripts): add rationale and risk notes to historical scripts'

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'check-contiguity'}

u='https://api.github.com/repos/kai-cn/car-monit-backend/commits?sha=car-monit-backend-java-V3&per_page=200'

with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:

    commits=json.loads(r.read().decode())

flags=[c['commit']['message'].splitlines()[0]==TARGET for c in commits[:120]]

idx=[i for i,v in enumerate(flags) if v]

print('total',len(commits),'hits',len(idx),'first_idx',min(idx) if idx else None,'last_idx',max(idx) if idx else None)

print('contiguous',idx==list(range(min(idx),max(idx)+1)) if idx else False)

print('head_is_target',flags[0] if flags else False)

for i in range(max(0,min(idx)-2),min(len(commits),max(idx)+3)):

    print(i,commits[i]['sha'][:8],flags[i],commits[i]['commit']['message'].splitlines()[0][:80])

