#!/usr/bin/env python3
# ======================================================================
# 用途：硬门禁——探针必须真的跑出端点且 app 必须 ready，否则 job 立即失败（杜绝假绿）。
# 调用：python gate.py --old out/old.json --new out/new.json
# 说明：不接触凭据；只判 old/new 两份探针 JSON。
# ======================================================================
import argparse
import json
import sys
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def check(side, data):
    errs = []
    eps = data.get("endpoints") or []
    # parity_probe.py does not write a `ready` key; it signals failure via `error`
    # and/or by capturing zero endpoints (e.g. "process exited early rc=1").
    if data.get("error"):
        errs.append("%s: probe error=%s" % (side, data.get("error")))
    if len(eps) < 1:
        errs.append("%s: 0 endpoints captured" % side)
    bad = [e for e in eps if e.get("status") in (None, 0)]
    if bad:
        errs.append("%s: %d endpoints with no status" % (side, len(bad)))
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    a = ap.parse_args()
    errs = []
    for side, p in (("old", a.old), ("new", a.new)):
        try:
            errs += check(side, load(p))
        except Exception as e:
            errs.append("%s: cannot read probe json: %r" % (side, e))
    if errs:
        print("DBUPGRADE_GATE_FAIL")
        for e in errs:
            print("  - " + e)
        sys.exit(1)
    print("DBUPGRADE_GATE_PASS old/new both have endpoints and app ready")


if __name__ == "__main__":
    main()
