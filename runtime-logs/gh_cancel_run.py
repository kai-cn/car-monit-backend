#!/usr/bin/env python3

"""
@description 历史脚本 gh_cancel_run.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python gh_cancel_run.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：取消重复的 GitHub Actions run（token 来自本地缓存）。

# 用法：python gh_cancel_run.py <repo> <run_id>

import json

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token

repo, run_id = sys.argv[1:3]

h = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0",

     "Content-Type": "application/json"}

req = urllib.request.Request(

    "https://api.github.com/repos/%s/actions/runs/%s/cancel" % (repo, run_id),

    data=json.dumps({}).encode(), method="POST", headers=h)

try:

    with urllib.request.urlopen(req, timeout=40) as r:

        print("CANCEL_OK run=%s http=%s" % (run_id, r.status))

except Exception as e:

    print("CANCEL_RESULT run=%s %s" % (run_id, e))

