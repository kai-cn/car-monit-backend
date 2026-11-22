#!/usr/bin/env python3
"""
@description 历史脚本 push_final_handover.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python push_final_handover.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
import base64
import sys
import urllib.error
sys.path.insert(0, "D:/work/runtime-logs")
from push_files_api import api
content = open("D:/work/runtime-logs/doc13-final.md", "rb").read()
for repo in ["kai-cn/car-monit-api", "kai-cn/car-monit-backend"]:
    path = "/repos/%s/contents/docs/v3/review/13-db-upgrade-handover.md" % repo
    try:
        _, cur = api("GET", path + "?ref=feature-dbupgrade")
        sha = cur.get("sha")
    except urllib.error.HTTPError:
        sha = None
    body = {"message": "docs(dbupgrade): mark all GA verification runs complete",
            "content": base64.b64encode(content).decode("ascii"), "branch": "feature-dbupgrade"}
    if sha:
        body["sha"] = sha
    st, res = api("PUT", path, body)
    print("PUT", repo, st, res.get("commit", {}).get("sha", "")[:10])
