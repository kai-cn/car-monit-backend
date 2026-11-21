#!/usr/bin/env python3
# 用途：取消重复的 GitHub Actions run（token 来自本地缓存）。
# 用法：python gh_cancel_run.py <repo> <run_id>
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
repo, run_id = sys.argv[1:3]
h = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0",
     "Content-Type": "application/json"}
req = urllib.request.Request(
    "https://api.github.com/repos/%s/actions/runs/%s/cancel" % (repo, run_id),
    data=json.dumps({}).encode(), method="POST", headers=h)
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        print("CANCEL_OK run=%s http=%s" % (run_id, r.status))
except Exception as e:
    print("CANCEL_RESULT run=%s %s" % (run_id, e))
