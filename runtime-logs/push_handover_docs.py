#!/usr/bin/env python3

"""
@description 历史脚本 push_handover_docs.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python push_handover_docs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# 用途：把交接文档与脚本索引推送到两仓库 feature-dbupgrade（docs/v3/review/）。

import base64

import json

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from push_files_api import api



DOCS = [

    ("D:/work/runtime-logs/dbupgrade-handover.md", "docs/v3/review/13-db-upgrade-handover.md"),

    ("D:/work/runtime-logs/DBUPGRADE-SCRIPT-INDEX.md", "docs/v3/review/14-dbupgrade-script-index.md"),

]

for repo in ["kai-cn/car-monit-api", "kai-cn/car-monit-backend"]:

    for local, remote in DOCS:

        content = open(local, "rb").read()

        path = "/repos/%s/contents/%s" % (repo, remote)

        try:

            _, cur = api("GET", path + "?ref=feature-dbupgrade")

            sha = cur.get("sha")

        except urllib.error.HTTPError:

            sha = None

        body = {"message": "docs(dbupgrade): add handover and reproduction script index",

                "content": base64.b64encode(content).decode("ascii"), "branch": "feature-dbupgrade"}

        if sha:

            body["sha"] = sha

        st, res = api("PUT", path, body)

        print("PUT", repo, remote, st, res.get("commit", {}).get("sha", "")[:10])

