#!/usr/bin/env python3
# 用途：取消某仓库所有进行中/排队的 db-upgrade-cloud run（token 来自缓存）。
# 用法：python cancel_dbupgrade_runs.py <repo>
import json
import sys
import urllib.request
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token

repo = sys.argv[1]
H = {"Authorization": "Bearer " + get_token(), "User-Agent": "car-monit-v3-ops/1.0",
     "Content-Type": "application/json"}
base = "https://api.github.com/repos/%s/actions/runs" % repo
for status in ("in_progress", "queued", "pending", "waiting"):
    try:
        with urllib.request.urlopen(urllib.request.Request(
                base + "?status=%s&per_page=100" % status, headers=H), timeout=60) as r:
            data = json.loads(r.read())
    except Exception as e:
        print("list error", status, e); continue
    for run in data.get("workflow_runs", []):
        if run.get("name") != "db-upgrade-cloud":
            continue
        rid = run["id"]
        try:
            req = urllib.request.Request(base + "/%s/cancel" % rid,
                                         data=b"{}", method="POST", headers=H)
            with urllib.request.urlopen(req, timeout=40) as rr:
                print("CANCEL", rid, run["head_branch"], rr.status)
        except Exception as e:
            print("cancel fail", rid, e)
