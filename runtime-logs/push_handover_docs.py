#!/usr/bin/env python3
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
