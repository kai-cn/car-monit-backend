#!/usr/bin/env python3
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
