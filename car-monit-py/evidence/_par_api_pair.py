# -*- coding: utf-8 -*-
"""API 双端直连比对：car-monit-api 的 Java 端(9902) vs Python 端(9901)。

第 1 档里 backend 双端出现的差异，必须先分清是 **backend 的 Forest 转发层**不一致，
还是它调用的 **api 双端**本身不一致。本脚本绕开 backend 直接打 api 两端，
覆盖 backend 的 6 个 Forest client 声明的全部路径。

用法::

    python evidence/_par_api_pair.py [--out D:/tmp/par-api.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _par_common as C  # noqa: E402

LIST_PATHS = [
    "/base/feeGantry/list", "/base/feerecords/list", "/base/feestationexit/list",
    "/base/snapshotflow/list", "/base/snapshotflow/listToExport",
    "/base/section/listAll", "/base/toll/listAll", "/base/gantry/listAll",
    "/base/org/listAll", "/base/fwqjcxx/listAll", "/base/sfsjcxx/listAll",
    "/base/sfzjcxx/listAll", "/base/toll/listAll",
]
TIME_PARAMS = {
    "/base/feerecords/list": {"inApplyTime1": "2025-08-01 00:00:00",
                              "inApplyTime2": "2025-08-31 23:59:59"},
    "/base/snapshotflow/list": {"applyTime1": "2025-08-01 00:00:00",
                                "applyTime2": "2025-08-02 00:00:00"},
}
DETAIL_MODULES = ("feeGantry", "feerecords", "feestationexit", "snapshotflow")
EARLIEST = "/base/snapshotflow/earliest-time"


def rows_len(body):
    if isinstance(body, dict):
        for key in ("rows", "data"):
            if isinstance(body.get(key), list):
                return len(body[key]), body.get("total")
    if isinstance(body, list):
        return len(body), None
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/tmp/par-api.json")
    args = ap.parse_args()

    entries, ids = [], {}
    for path in sorted(set(LIST_PATHS)):
        params = {"pageNum": 1, "pageSize": 20} if path.endswith("/list") else {}
        params.update(TIME_PARAMS.get(path, {}))
        case = {"path": path, "params": params}
        for base_key, base in (("java", C.API_JAVA), ("python", C.API_PY)):
            status, raw, ctype = C.call(base, path, params=params)
            try:
                body = json.loads(raw)
            except Exception:  # noqa: BLE001
                body = None
            case[base_key] = {"status": status, "bytes": len(raw), "ctype": ctype[:40],
                              "json": body}
        bj, bp = case["java"]["json"], case["python"]["json"]
        nj, tj = rows_len(bj)
        np_, tp = rows_len(bp)
        diffs = C.deep_diff(C.norm(bj), C.norm(bp)) if (bj is not None and bp is not None) else None
        case["rows"] = [f"{nj}/{tj}", f"{np_}/{tp}"]
        if case["java"]["status"] != case["python"]["status"]:
            case["kind"] = "STATUS"
        elif bj is None or bp is None:
            case["kind"] = "non-json"
        elif not diffs:
            case["kind"] = "SAME"
        else:
            case["kind"] = "DIFF"
            case["diff"] = diffs[:8]
        entries.append(case)
        if isinstance(bj, dict) and isinstance(bj.get("rows"), list) and bj["rows"]:
            first = bj["rows"][0]
            key = first.get("bigId") or first.get("id")
            if key and path.split("/")[2] in DETAIL_MODULES:
                ids.setdefault(path.split("/")[2], str(key))
        if isinstance(bj, list) and bj and path.split("/")[2] in DETAIL_MODULES:
            ids.setdefault(path.split("/")[2], str(bj[0].get("bigId") or bj[0].get("id")))

    for mod, big in sorted(ids.items()):
        path = "/base/%s/%s" % (mod, big)
        case = {"path": path, "params": {}}
        for base_key, base in (("java", C.API_JAVA), ("python", C.API_PY)):
            status, raw, _ct = C.call(base, path)
            try:
                body = json.loads(raw)
            except Exception:  # noqa: BLE001
                body = None
            case[base_key] = {"status": status, "bytes": len(raw), "json": body}
        bj, bp = case["java"]["json"], case["python"]["json"]
        diffs = C.deep_diff(C.norm(bj), C.norm(bp)) if (bj is not None and bp is not None) else None
        if case["java"]["status"] != case["python"]["status"]:
            case["kind"] = "STATUS"
        elif not diffs:
            case["kind"] = "SAME"
        else:
            case["kind"] = "DIFF"
            case["diff"] = diffs[:8]
        entries.append(case)

    case = {"path": EARLIEST, "params": {}}
    for base_key, base in (("java", C.API_JAVA), ("python", C.API_PY)):
        status, raw, _ct = C.call(base, EARLIEST)
        case[base_key] = {"status": status, "body": raw[:120].decode("utf-8", "ignore")}
    case["kind"] = "SAME" if (case["java"] == case["python"]) else "DIFF"
    entries.append(case)

    buckets = {}
    for case in entries:
        buckets[case["kind"]] = buckets.get(case["kind"], 0) + 1
        flag = "OK  " if case["kind"] == "SAME" else "BAD "
        print("%s %-38s java=%-5s py=%-5s rows=%-14s %s" % (
            flag, case["path"][:38], case["java"]["status"], case["python"]["status"],
            "~".join(case.get("rows", ["-", "-"])),
            json.dumps(case.get("diff", ""), ensure_ascii=False, default=str)[:150]))

    summary = {"java_api": C.API_JAVA, "python_api": C.API_PY, "total": len(entries),
               "buckets": buckets, "entries": entries}
    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str),
                              encoding="utf-8")
    print("\n== api 双端: total=%d %s -> %s" % (
        len(entries), " ".join("%s=%d" % kv for kv in sorted(buckets.items())), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
