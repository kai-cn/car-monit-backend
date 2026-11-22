#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：check-target-contiguity.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
"""检查目标提交在指定分支上是否连续、是否位于顶端。"""
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
