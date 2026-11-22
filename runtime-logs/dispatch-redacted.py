#!/usr/bin/env python3
# 用途：触发 workflow_dispatch 且不回显任何 input 值；token 来自本地缓存（无账号弹窗）。
# 用法：python dispatch-redacted.py <repo> <workflow> <ref> k=v [k=v ...]
import json
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token

repo, workflow, ref = sys.argv[1:4]
inputs = dict(pair.split("=", 1) for pair in sys.argv[4:])
token = get_token()
headers = {"User-Agent": "car-monit-v3-ops/1.0",
           "Accept": "application/vnd.github+json",
           "Authorization": "Bearer " + token,
           "Content-Type": "application/json"}
body = json.dumps({"ref": ref, "inputs": inputs}).encode()
req = urllib.request.Request(
    "https://api.github.com/repos/%s/actions/workflows/%s/dispatches" % (repo, workflow),
    data=body, method="POST", headers=headers)
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        print("DISPATCH_OK repo=%s workflow=%s ref=%s inputs_redacted" % (repo, workflow, ref))
except urllib.error.HTTPError as e:
    sys.exit("DISPATCH_FAIL http=%s body=%s" % (e.code, e.read().decode()[:300]))

for _ in range(12):
    time.sleep(3)
    q = urllib.request.Request(
        "https://api.github.com/repos/%s/actions/runs?event=workflow_dispatch&per_page=5" % repo,
        headers=headers)
    with urllib.request.urlopen(q, timeout=40) as r:
        runs = json.loads(r.read())
    matched = [r for r in runs.get("workflow_runs", [])
               if (r.get("path") or "").endswith(workflow) and r.get("head_branch") == ref]
    if matched:
        # 取 created_at 最新的，避免匹配到同 workflow 的旧 run。
        newest = max(matched, key=lambda r: r.get("created_at", ""))
        print("RUN id=%s url=%s status=%s" % (newest["id"], newest["html_url"], newest["status"]))
        sys.exit(0)
print("RUN_NOT_YET_VISIBLE")
