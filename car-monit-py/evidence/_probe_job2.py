"""Throwaway probe: dump every sys_job row (and a job-log sample) from the live Java app."""
from __future__ import annotations

import json
import os
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8090"

payload = httpx.post(
    BASE + "/login",
    json={
        "username": "admin",
        "password": os.environ.get("SWEEP_PASSWORD", ""),
        "code": "",
        "uuid": "",
    },
    timeout=60,
).json()
token = payload.get("token")
if not token:
    raise SystemExit("login failed: %s" % json.dumps(payload, ensure_ascii=False))
auth = {"Authorization": "Bearer " + token}

rows = httpx.get(BASE + "/monitor/job/list", params={"pageSize": 100}, headers=auth, timeout=60).json()
print("=== /monitor/job/list ===")
print(json.dumps(rows, ensure_ascii=False, indent=2))

logs = httpx.get(
    BASE + "/monitor/jobLog/list",
    params={"pageSize": 3, "pageNum": 1},
    headers=auth,
    timeout=60,
).json()
print("=== /monitor/jobLog/list (first 3) ===")
print(json.dumps(logs, ensure_ascii=False, indent=2))

one = httpx.get(BASE + "/monitor/jobLog/1", headers=auth, timeout=60).json()
print("=== /monitor/jobLog/1 ===")
print(json.dumps(one, ensure_ascii=False, indent=2))

if rows.get("rows"):
    job_id = rows["rows"][0]["jobId"]
    detail = httpx.get(BASE + "/monitor/job/" + str(job_id), headers=auth, timeout=60).json()
    print("=== /monitor/job/%s ===" % job_id)
    print(json.dumps(detail, ensure_ascii=False, indent=2))
