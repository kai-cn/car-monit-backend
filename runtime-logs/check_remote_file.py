#!/usr/bin/env python3

"""
@description 历史脚本 check_remote_file.py：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python check_remote_file.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token

repo, branch, path, needle = sys.argv[1:5]

url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, branch, path)

req = urllib.request.Request(url, headers={"Authorization": "Bearer " + get_token(), "User-Agent": "x"})

s = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")

print(repo, branch, path, "needle=", needle, "FOUND" if needle in s else "MISSING")

