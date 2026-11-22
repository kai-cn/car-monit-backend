#!/usr/bin/env python3

"""
@description 历史脚本 fetch_file_api.py：从远端读取文件或状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python fetch_file_api.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：通过 Contents API 取远端文件内容到本地（token 来自缓存）。

# 用法：python fetch_file_api.py <repo> <branch> <remote_path> <local_out>

import base64

import json

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token

repo, branch, path, out = sys.argv[1:5]

H = {"Authorization": "Bearer " + get_token(), "User-Agent": "x"}

url = "https://api.github.com/repos/%s/contents/%s?ref=%s" % (repo, path, branch)

with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60) as r:

    d = json.loads(r.read())

data = base64.b64decode(d["content"])

open(out, "wb").write(data)

print("saved", out, len(data), "bytes")

