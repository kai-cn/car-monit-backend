#!/usr/bin/env python3

"""
@description 历史脚本 cancel_dbupgrade_runs.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python cancel_dbupgrade_runs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：取消某仓库所有进行中/排队的 db-upgrade-cloud run（token 来自缓存）。

# 用法：python cancel_dbupgrade_runs.py <repo>

import json

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



repo = sys.argv[1]

H = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0",

     "Content-Type": "application/json"}

base = "https://api.github.com/repos/%s/actions/runs" % repo

for status in ("in_progress", "queued", "pending", "waiting"):

    try:

        with urllib.request.urlopen(urllib.request.Request(

                base + "?status=%s&per_page=100" % status, headers=H), timeout=60) as r:

            data = json.loads(r.read())

    except Exception as e:

        print("list error", status, e); continue

    for run in data.get("workflow_runs", []):

        if run.get("name") != "db-upgrade-cloud":

            continue

        rid = run["id"]

        try:

            req = urllib.request.Request(base + "/%s/cancel" % rid,

                                         data=b"{}", method="POST", headers=H)

            with urllib.request.urlopen(req, timeout=40) as rr:

                print("CANCEL", rid, run["head_branch"], rr.status)

        except Exception as e:

            print("cancel fail", rid, e)

