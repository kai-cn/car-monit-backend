#!/usr/bin/env python3

"""
@description 历史脚本 check_remote_scripts.py：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python check_remote_scripts.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import base64

import json

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token

H = {"Authorization": "Bearer " + get_token(), "User-Agent": "x"}

repo, branch, path = sys.argv[1:4]

url = "https://api.github.com/repos/%s/contents/%s?ref=%s" % (repo, path, branch)

with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:

    d = json.loads(r.read())

b = base64.b64decode(d["content"])

print("bytes", len(b), "CRLF", b.count(b"\r\n"), "LF", b.count(b"\n"))

s = b.decode("utf-8", "replace")

for needle in ['"$dbname" -Fp', "OG_NEW_IMAGES", "pick_image"]:

    print(needle, needle in s)

