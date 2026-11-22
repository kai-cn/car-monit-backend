#!/usr/bin/env python3
"""
@description 历史脚本 list_artifacts.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python list_artifacts.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：列出某个 run 的 artifact id/name 和摘要（token 来自本地缓存）。
# 用法：python list_artifacts.py <repo> <run_id>
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, run_id = sys.argv[1:3]
H = {"User-Agent": "car-monit-v3-ops/1.0", "Accept": "application/vnd.github+json",
     "Authorization": "Bearer " + get_token()}
with urllib.request.urlopen(urllib.request.Request(
        "https://api.github.com/repos/%s/actions/runs/%s/artifacts?per_page=100" % (repo, run_id),
        headers=H), timeout=60) as r:
    data = json.loads(r.read())
for a in data.get("artifacts", []):
    print("id=%s name=%s size=%s expired=%s" % (
        a["id"], a["name"], a.get("size_in_bytes"), a.get("expired")))
