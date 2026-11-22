#!/usr/bin/env python3

"""
@description 历史脚本 extract_reports_only.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python extract_reports_only.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：下载 3 个证据 artifact，仅解包小的报告/版本/资源文件（跳过 fat jar），完成后写 DONE 标记。

# token 来自本地缓存；不回显凭据。

import io

import json

import os

import sys

import urllib.request

import zipfile



sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



H = {"User-Agent": "car-monit-v3-ops/1.0", "Accept": "application/vnd.github+json",

     "Authorization": "Bearer " + get_token()}

ROOT = "D:/work/runtime-logs/dbupgrade-evidence"

DONE = os.path.join(ROOT, "DONE")

KEEP = ("report.json", "report.md", "compare.json", "compare.md",

        "old.json", "new.json", ".version.txt", ".stats.json", ".rows.txt", ".dump.method.txt")





class NR(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):

        return urllib.request.Request(newurl, headers={"User-Agent": "car-monit-dl"})





TARGETS = [

    ("kai-cn/car-monit-api", 14322975501, "api-opengauss"),

    ("kai-cn/car-monit-api", 14321353917, "api-mysql"),

    ("kai-cn/car-monit-backend", 14322007061, "backend-mysql"),

]



os.makedirs(ROOT, exist_ok=True)

if os.path.exists(DONE):

    os.remove(DONE)



try:

    opener = urllib.request.build_opener(NR)

    for repo, aid, name in TARGETS:

        dest = os.path.join(ROOT, name)

        os.makedirs(dest, exist_ok=True)

        url = "https://api.github.com/repos/%s/actions/artifacts/%s/zip" % (repo, aid)

        req = urllib.request.Request(url, headers=H)

        with opener.open(req, timeout=600) as r:

            data = r.read()

        with zipfile.ZipFile(io.BytesIO(data)) as z:

            for item in z.namelist():

                if item.endswith("/"):

                    continue

                base = os.path.basename(item)

                if any(base.endswith(k) for k in KEEP):

                    z.extract(item, dest)

        print("EXTRACTED", name, "zip_bytes", len(data), flush=True)

    with open(DONE, "w") as f:

        f.write("OK")

    print("DONE", flush=True)

except Exception as e:

    with open(DONE, "w") as f:

        f.write("FAIL " + repr(e))

    print("FAIL", repr(e), flush=True)

