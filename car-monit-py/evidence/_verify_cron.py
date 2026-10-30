"""Throwaway: verify the CronExpression port against the Java oracle."""
from __future__ import annotations

import sys
from datetime import datetime

sys.path.insert(0, ".")

from app.quartz.util.cron_utils import CronUtils  # noqa: E402

ACCEPTED = [
    "0 0 2 * * ?",
    "0/10 * * * * ?",
    "0 0 2 ? * MON",
    "0 0 2 L * ?",
    "0 0 2 ? * 6L",
    "0 0 2 ? * 5#2",
    "0 0 2 15W * ?",
    "0 0 2 LW * ?",
    "0 0 2 * * ? 2027",
    "*/0 * * * * ?",
]

REJECTED = [
    "0 0 * * * *",
    "0 0 2 * * *",
    "0 0 2 * *",
    "0 0 25 * * ?",
    "0 0 2 32 * ?",
    "60 0 2 * * ?",
    "0 0 2 * 13 ?",
    "0 0 2 * * 8",
    "bogus",
    "0 0 2 ? * ?",
]

failures = 0
for expr in ACCEPTED:
    got = CronUtils.is_valid(expr)
    mark = "OK " if got else "BAD"
    if not got:
        failures += 1
        print("%s accepted %-24r -> %s (%s)" % (mark, expr, got, CronUtils.get_invalid_message(expr)))
    else:
        print("%s accepted %-24r -> %s" % (mark, expr, got))

for expr in REJECTED:
    got = CronUtils.is_valid(expr)
    mark = "OK " if not got else "BAD"
    if got:
        failures += 1
    print("%s rejected %-24r -> %s (%s)" % (mark, expr, got, CronUtils.get_invalid_message(expr)))

print()
print("next executions @", datetime.now().replace(microsecond=0))
for expr in ACCEPTED + ["0 0 2 ? * MON", "0 0 1 1 * ?", "0 0 2 * * MON"]:
    try:
        print("  %-22r -> %s" % (expr, CronUtils.get_next_execution(expr)))
    except Exception as exc:  # noqa: BLE001
        print("  %-22r -> EXC %s: %s" % (expr, type(exc).__name__, exc))

# 线上 sys_job 里真实存在的 18 条表达式
LIVE = [
    "0/10 * * * * ?",
    "0 0 2 * * ?",
    "0 0 2 ? * MON",
]
print()
print("null ->", end=" ")
try:
    CronUtils.is_valid(None)
except Exception as exc:  # noqa: BLE001
    print(type(exc).__name__, ":", exc)

print()
print("FAILURES =", failures)
