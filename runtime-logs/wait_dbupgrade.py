#!/usr/bin/env python3
# 用途：等待一组云 run 完成并打印最终 job/step 结论（token 来自本地缓存）。
# 用法：python wait_dbupgrade.py <repo:runid> [<repo:runid> ...] [max_seconds]
# 例：python wait_dbupgrade.py kai-cn/car-monit-api:44068812191 kai-cn/car-monit-backend:44068845104 900
import json
import sys
import time
import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token

H = {"User-Agent": "car-monit-v3-ops/1.0", "Accept": "application/vnd.github+json",
     "Authorization": "Bearer " + get_token()}

args = sys.argv[1:]
max_seconds = 600
if args and args[-1].isdigit():
    max_seconds = int(args[-1]); args = args[:-1]
targets = [a.split(":") for a in args]


def get(path):
    with urllib.request.urlopen(urllib.request.Request(
            "https://api.github.com" + path, headers=H), timeout=40) as r:
        return json.loads(r.read())


def status(repo, rid):
    r = get("/repos/%s/actions/runs/%s" % (repo, rid))
    jobs = get("/repos/%s/actions/runs/%s/jobs?per_page=100" % (repo, rid)).get("jobs", [])
    return r, jobs


start = time.time()
last = {}
while time.time() - start < max_seconds:
    all_done = True
    for repo, rid in targets:
        r, jobs = status(repo, rid)
        done = r.get("status") == "completed"
        if not done:
            all_done = False
        cur = (r.get("status"), r.get("conclusion"),
               tuple((j.get("name"), j.get("status"), j.get("conclusion")) for j in jobs))
        if cur != last.get(rid):
            print("[%s] %s status=%s conclusion=%s" % (
                time.strftime("%H:%M:%S"), rid, r.get("status"), r.get("conclusion")), flush=True)
            for j in jobs:
                fails = [s.get("name") for s in j.get("steps", []) if s.get("conclusion") == "failure"]
                print("   job=%-32s %s/%s fails=%s" % (
                    j.get("name"), j.get("status"), j.get("conclusion"), fails), flush=True)
            last[rid] = cur
    if all_done:
        print("ALL_DONE", flush=True)
        break
    time.sleep(20)
else:
    print("WAIT_TIMEOUT (runs still active)", flush=True)
