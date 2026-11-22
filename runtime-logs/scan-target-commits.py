#!/usr/bin/env python3
"""只读扫描两仓库所有分支中指定提交信息的提交数量与是否连续。

思路：GitHub commits API 按分支拉提交列表，统计 message 首行精确匹配
TARGET 的提交；连续提交可直接 soft reset 合并，非连续需更复杂策略。
"""
import json, sys, urllib.request
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

TARGET='docs(scripts): add rationale and risk notes to historical scripts'
H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'scan-commits'}
REPOS=['kai-cn/car-monit-api','kai-cn/car-monit-backend']

def api(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=90) as r:
        return json.loads(r.read().decode())

for repo in REPOS:
    branches=[b['name'] for b in api(f'https://api.github.com/repos/{repo}/branches?per_page=100')]
    for br in branches:
        try:
            commits=api(f'https://api.github.com/repos/{repo}/commits?sha={br}&per_page=200')
        except Exception:
            continue
        hits=[c for c in commits if c['commit']['message'].splitlines()[0]==TARGET]
        if hits:
            print(repo,br,'count',len(hits),'first',hits[0]['sha'][:8],'last',hits[-1]['sha'][:8])
