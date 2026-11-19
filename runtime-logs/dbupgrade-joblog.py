#!/usr/bin/env python3
# 用途：读取 GitHub Actions run 的 job 步骤状态（token 来自本地缓存，无弹窗、不回显凭据）。
# 用法：python dbupgrade-joblog.py <repo> <run_id>
import json
import sys
import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token

repo, run_id = sys.argv[1:3]
h = {"User-Agent": "car-monit-v3-ops/1.0", "Accept": "application/vnd.github+json",
     "Authorization": "Bearer " + get_token()}


def get(path):
    with urllib.request.urlopen(urllib.request.Request(
            "https://api.github.com" + path, headers=h), timeout=40) as r:
        return json.loads(r.read())


run = get("/repos/%s/actions/runs/%s" % (repo, run_id))
print("RUN %s %s status=%s conclusion=%s" % (run_id, run["name"], run["status"], run["conclusion"]))
for j in get("/repos/%s/actions/runs/%s/jobs?per_page=100" % (repo, run_id)).get("jobs", []):
    print("  JOB %-40s %s/%s id=%s" % (j.get("name"), j.get("status"), j.get("conclusion"), j.get("id")))
    for s in j.get("steps", []):
        print("    %-55s %s/%s" % (s.get("name")[:55], s.get("status"), s.get("conclusion")))
