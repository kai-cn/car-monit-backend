"""Throwaway probe: error paths of ``/monitor/job`` and ``/monitor/jobLog``."""
from __future__ import annotations

import json
import os
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8090"

token = httpx.post(
    BASE + "/login",
    json={
        "username": "admin",
        "password": os.environ.get("SWEEP_PASSWORD", ""),
        "code": "",
        "uuid": "",
    },
    timeout=60,
).json()["token"]
auth = {"Authorization": "Bearer " + token}


def show(label: str, response: httpx.Response) -> None:
    text = response.text
    if len(text) > 400:
        text = text[:400] + "..."
    print("%-46s -> HTTP %s %s" % (label, response.status_code, text))


def post(body: dict) -> None:
    show("POST /monitor/job %s" % json.dumps(body, ensure_ascii=False),
         httpx.post(BASE + "/monitor/job", json=body, headers=auth, timeout=60))


GOOD = {
    "jobName": "__probe__",
    "jobGroup": "PROBE",
    "invokeTarget": "ryTask.ryNoParams",
    "cronExpression": "0 0 2 * * ?",
    "misfirePolicy": "3",
    "concurrent": "1",
    "status": "1",
}

# 1. 缺少 cronExpression（null） -> CronExpression(null) 抛 IllegalArgumentException
body = dict(GOOD)
body.pop("cronExpression")
post(body)

# 2. cronExpression 为空串
body = dict(GOOD)
body["cronExpression"] = ""
post(body)

# 3. 缺 jobName / invokeTarget（getter 上的 @NotBlank 无 @Validated，应该是惰性的）
body = dict(GOOD)
body.pop("jobName")
post(body)

body = dict(GOOD)
body.pop("invokeTarget")
post(body)

# 4. 非法 misfirePolicy -> TaskException(CONFIG_ERROR)
body = dict(GOOD)
body["misfirePolicy"] = "9"
post(body)

# 5. 缺 jobGroup
body = dict(GOOD)
body.pop("jobGroup")
post(body)

# 6. 空 body
post({})

# 7. PUT 不存在的 jobId
show("PUT /monitor/job jobId=999999",
     httpx.put(BASE + "/monitor/job", json={
         "jobId": 999999, "jobName": "__probe__", "jobGroup": "PROBE",
         "invokeTarget": "ryTask.ryNoParams", "cronExpression": "0 0 2 * * ?",
         "misfirePolicy": "3", "concurrent": "1", "status": "1",
     }, headers=auth, timeout=60))

# 8. changeStatus 不存在的 jobId
show("PUT /monitor/job/changeStatus jobId=999999",
     httpx.put(BASE + "/monitor/job/changeStatus",
               json={"jobId": 999999, "status": "0"}, headers=auth, timeout=60))

# 9. run 不存在的 jobId
show("PUT /monitor/job/run jobId=999999",
     httpx.put(BASE + "/monitor/job/run", json={"jobId": 999999}, headers=auth, timeout=60))

# 10. 删除不存在的 jobId
show("DELETE /monitor/job/999999",
     httpx.delete(BASE + "/monitor/job/999999", headers=auth, timeout=60))

# 11. 删除，路径变量不是数字
show("DELETE /monitor/job/abc",
     httpx.delete(BASE + "/monitor/job/abc", headers=auth, timeout=60))

# 12. 查询不存在的 jobId
show("GET /monitor/job/999999",
     httpx.get(BASE + "/monitor/job/999999", headers=auth, timeout=60))

# 13. jobLog 详情（Java 的路径变量名不匹配）
show("GET /monitor/jobLog/1", httpx.get(BASE + "/monitor/jobLog/1", headers=auth, timeout=60))
show("GET /monitor/jobLog/abc", httpx.get(BASE + "/monitor/jobLog/abc", headers=auth, timeout=60))

# 14. jobLog 删除不存在的 id
show("DELETE /monitor/jobLog/999999",
     httpx.delete(BASE + "/monitor/jobLog/999999", headers=auth, timeout=60))
show("DELETE /monitor/jobLog/abc",
     httpx.delete(BASE + "/monitor/jobLog/abc", headers=auth, timeout=60))

# 15. 导出（只取返回体，不下载文件）
show("GET /monitor/job/export",
     httpx.get(BASE + "/monitor/job/export", headers=auth, timeout=120))
show("GET /monitor/jobLog/export",
     httpx.get(BASE + "/monitor/jobLog/export", headers=auth, timeout=120))

# 16. 非法 cron + 非法 misfire 的优先级
body = dict(GOOD)
body["cronExpression"] = "bogus"
body["misfirePolicy"] = "9"
post(body)

# 清理本轮插入的行
rows = httpx.get(BASE + "/monitor/job/list", params={"jobGroup": "PROBE", "pageSize": 100},
                 headers=auth, timeout=60).json().get("rows") or []
if rows:
    ids = ",".join(str(row["jobId"]) for row in rows)
    print("\ncleanup ids:", ids)
    print(httpx.delete(BASE + "/monitor/job/" + ids, headers=auth, timeout=60).text)
else:
    print("\nno rows inserted")
