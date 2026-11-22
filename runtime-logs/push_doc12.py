#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：push_doc12.py
用途：推送内容到远端。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改远端分支，执行前确认凭据与目标。
"""
import sys
sys.path.insert(0, "D:/work/runtime-logs")
from push_files_api import put_files
src = "D:/work/runtime-logs"
# put_files expects relpath under base; doc is named doc12-remote.md -> push as target path
from push_files_api import api, H
import base64
content = open(src + "/doc12-remote.md", "rb").read()
for br in ["feature-dbupgrade", "car-monit-api-jdk21", "car-monit-api-jdk17", "car-monit-api-java-V3"]:
    path = "/repos/kai-cn/car-monit-api/contents/docs/v3/review/12-db-upgrade-verification.md"
    try:
        _, cur = api("GET", path + "?ref=" + br)
        sha = cur.get("sha")
    except Exception:
        sha = None
    body = {"message": "docs(dbupgrade): record GA image cloud verification",
            "content": base64.b64encode(content).decode("ascii"), "branch": br}
    if sha:
        body["sha"] = sha
    st, res = api("PUT", path, body)
    print("PUT", br, st, res.get("commit", {}).get("sha", "")[:10])
