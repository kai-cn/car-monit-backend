"""Throwaway probe: what does the Java ``CronExpression`` consider valid?

``SysJobController#add`` is the cheapest oracle for ``CronUtils.isValid``: an
invalid expression is rejected with ``cron表达式不正确`` **before** any insert.
A valid one inserts a row, which we delete again in the same run.

Every probe row is created with ``jobGroup = PROBE`` and status forced to PAUSE
by ``SysJobServiceImpl#insertJob``, so nothing can fire in the meantime.
"""
from __future__ import annotations

import json
import os
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8090"
PASSWORD = os.environ.get("SWEEP_PASSWORD", "")
GROUP = "PROBE"

EXPRESSIONS = [
    "0 0 2 * * ?",          # 6 段，秒 分 时 日 月 周（日=*，周=?）
    "0/10 * * * * ?",       # 秒增量 + 日=* 周=?
    "0 0 * * * *",          # 日=* 且 周=* -> Quartz 应该拒绝
    "0 0 2 * * *",
    "0 0 2 ? * MON",        # 周用名字
    "0 0 2 L * ?",          # 月末
    "0 0 2 ? * 6L",         # 最后一个周五
    "0 0 2 ? * 5#2",        # 第二个周四
    "0 0 2 15W * ?",        # 最近的工作日
    "0 0 2 LW * ?",         # 最后一个工作日
    "0 0 2 * * ? 2027",     # 7 段带年
    "0 0 2 * *",            # 5 段（缺秒）-> Quartz 拒绝
    "0 0 25 * * ?",         # 小时越界
    "0 0 2 32 * ?",         # 日越界
    "60 0 2 * * ?",         # 秒越界
    "0 0 2 * 13 ?",         # 月越界
    "0 0 2 * * 8",          # 周越界
    "bogus",
    "*/0 * * * * ?",        # 步长为 0
    "0 0 2 ? * ?",          # 两者都是 ? -> Quartz 应该拒绝
]


def login() -> str:
    body = {"username": "admin", "password": PASSWORD, "code": "", "uuid": ""}
    payload = httpx.post(BASE + "/login", json=body, timeout=60).json()
    token = payload.get("token")
    if not token:
        raise SystemExit("login failed: %s" % json.dumps(payload, ensure_ascii=False))
    return token


token = login()
auth = {"Authorization": "Bearer " + token}

for expression in EXPRESSIONS:
    body = {
        "jobName": "__probe__",
        "jobGroup": GROUP,
        "invokeTarget": "ryTask.ryNoParams",
        "cronExpression": expression,
        "misfirePolicy": "3",
        "concurrent": "1",
        "status": "1",
    }
    payload = httpx.post(BASE + "/monitor/job", json=body, headers=auth, timeout=60).json()
    print("%-24r -> %s" % (expression, json.dumps(payload, ensure_ascii=False)))

# 清理：删掉本轮插进去的探针任务
rows = httpx.get(
    BASE + "/monitor/job/list", params={"jobGroup": GROUP, "pageSize": 100},
    headers=auth, timeout=60,
).json().get("rows") or []
if rows:
    ids = ",".join(str(row["jobId"]) for row in rows)
    print("\ncleanup ids:", ids)
    print(httpx.delete(BASE + "/monitor/job/" + ids, headers=auth, timeout=60).text)
else:
    print("\nno rows inserted")
