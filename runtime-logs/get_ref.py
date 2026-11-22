#!/usr/bin/env python3
"""
@description 历史脚本 get_ref.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python get_ref.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：查询远端分支 SHA（走 GitHub API，token 来自缓存）。
# 用法：python get_ref.py <repo> <branch>
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, branch = sys.argv[1:3]
H = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0"}
url = "https://api.github.com/repos/%s/git/ref/heads/%s" % (repo, branch)
try:
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:
        d = json.loads(r.read())
    print(repo, branch, d["object"]["sha"])
except Exception as e:
    print("REF_ERR", repo, branch, repr(e))
