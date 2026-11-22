#!/usr/bin/env python3

"""
@description 历史脚本 fetch_joblog_cached.py：从远端读取文件或状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python fetch_joblog_cached.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：用本地缓存 token 拉取某个 job 的云端日志并保存到 runtime-logs（不下载 artifact）。

# 用法：python fetch_joblog_cached.py <repo> <job_id> <out_file>

import os

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



repo, job_id, out_file = sys.argv[1:4]

H = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0",

     "Accept": "application/vnd.github+json"}



class NR(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):

        return urllib.request.Request(newurl, headers={"User-Agent": "car-monit-v3-ops/1.0"})



url = "https://api.github.com/repos/%s/actions/jobs/%s/logs" % (repo, job_id)

req = urllib.request.Request(url, headers=H)

try:

    data = urllib.request.build_opener(NR).open(req, timeout=120).read()

    with open(out_file, "wb") as f:

        f.write(data)

    print("LOG_SAVED %s bytes=%d" % (out_file, len(data)))

except Exception as e:

    print("LOG_FAIL %r" % (e,))

