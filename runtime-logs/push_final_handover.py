#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：push_final_handover.py
用途：推送内容到远端。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改远端分支，执行前确认凭据与目标。
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
