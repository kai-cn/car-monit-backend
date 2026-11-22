#!/usr/bin/env python3

"""
@description 历史脚本 push_doc12.py：通过 Git 或 API 推送本地材料；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python push_doc12.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

