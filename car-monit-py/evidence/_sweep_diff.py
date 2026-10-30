"""Throwaway: diff every read-only business endpoint between the Java build and the port.

Java runs on :8090 (the real ruoyi-admin.jar, same MySQL/Redis), the port on :9989.
Each endpoint is called twice with identical query strings and the JSON payloads are
compared with a classifier, because "differs" has several very different meanings here:

* ``TYPE``       int vs "int"  -- exactly the StringTypeHandler class of bug
* ``VALUE``      same shape, different content -- a real behaviour difference
* ``NULL-OMIT``  one side sends ``"k": null``, the other omits ``k`` entirely
* ``ORDER``      same multiset, different array order -- no ORDER BY / collation
* ``MISSING``    a key exists only on one side
* ``STATUS``     HTTP status differs
* ``CODE``       ``code`` differs (200 vs 500)

Volatile payloads (server metrics, sessions, verification codes, Excel bytes) are compared
on status/shape only -- see ``SHAPE_ONLY`` / ``STATUS_ONLY``.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

BACKENDS = {"java": "http://127.0.0.1:8090", "python": "http://127.0.0.1:9989"}
TOKENS_FILE = Path(__file__).with_name(".sweep_tokens.json")
REPORT = Path(__file__).with_name("_sweep_report.md")
RAW = Path(__file__).with_name("_sweep_raw.json")

PARAM_RE = re.compile(r"\{[^}]+\}")

#: 有副作用 / 依赖外部系统 / 返回二进制，不能做数据比对
STATUS_ONLY = {
    "/captchaImage",
    "/common/download",
    "/common/download/resource",
    "/system/user/importTemplate",
    "/system/file/getNewCa",
    "/base/snapshotflow/earliest-time",
}
#: 只有形状可比（服务器指标、会话列表、缓存统计都是实时值）
SHAPE_ONLY = {"/monitor/server", "/monitor/cache", "/monitor/online/list"}

#: 完全不碰：会写库、会调外部服务、会动 Kafka
SKIP_PREFIXES = (
    "/base/geometry",
    "/base/cdc",
    "/downTemplate",
    "/system/file/view",
    "/test/",
)


def load_tokens() -> Dict[str, str]:
    return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))


def collect_endpoints() -> List[Tuple[str, Dict[str, Any]]]:
    """Every GET without a path variable, minus the dangerous ones."""
    from app.main import app

    seen = set()
    rows: List[Tuple[str, Dict[str, Any]]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if not path or "GET" not in methods or PARAM_RE.search(path):
            continue
        if path in seen:
            continue
        if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
            continue
        if path.endswith("/export") or path == "/system/user/export":
            continue
        seen.add(path)
        # /list 端点显式放大页大小，让值比对覆盖到更多行；两边收到同一组参数，仍然公平。
        params: Dict[str, Any] = {"pageNum": 1, "pageSize": 20} if path.endswith("/list") else {}
        rows.append((path, params))
    rows.sort()
    return rows


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def deep_diff(java: Any, py: Any, path: str = "", out: Optional[List[dict]] = None) -> List[dict]:
    """Walk two JSON trees and record every difference with a classification."""
    out = [] if out is None else out
    here = path or "$"

    if isinstance(java, dict) and isinstance(py, dict):
        for key in java:
            if key not in py:
                out.append({"path": "%s.%s" % (here, key), "kind": "MISSING", "java": java[key], "py": "<absent>"})
            else:
                deep_diff(java[key], py[key], "%s.%s" % (here, key), out)
        for key in py:
            if key not in java:
                out.append({"path": "%s.%s" % (here, key), "kind": "MISSING", "java": "<absent>", "py": py[key]})
        return out

    if isinstance(java, list) and isinstance(py, list):
        if len(java) != len(py):
            out.append({"path": "%s.length" % here, "kind": "VALUE", "java": len(java), "py": len(py)})
        for index, (left, right) in enumerate(zip(java, py)):
            deep_diff(left, right, "%s[%d]" % (here, index), out)
        return out

    if java == py and type(java) is type(py):
        return out

    if java is None or py is None:
        out.append({"path": here, "kind": "NULL-OMIT", "java": java, "py": py})
    elif isinstance(java, str) and _is_number(py) or isinstance(py, str) and _is_number(java):
        out.append({"path": here, "kind": "TYPE", "java": java, "py": py})
    elif _is_number(java) and _is_number(py) and float(java) == float(py):
        out.append({"path": here, "kind": "TYPE", "java": java, "py": py})
    else:
        out.append({"path": here, "kind": "VALUE", "java": java, "py": py})
    return out


def classify_order_only(java_body: Any, py_body: Any) -> bool:
    """True when the only difference is the order of a top-level array (``rows``/``data``)."""

    def dump(row: Any) -> str:
        return json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)

    if not isinstance(java_body, dict) or not isinstance(py_body, dict):
        return False
    for key in ("rows", "data"):
        left, right = java_body.get(key), py_body.get(key)
        if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            if sorted(map(dump, left)) == sorted(map(dump, right)):
                return True
    return False


def shape_of(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: shape_of(item) for key, item in value.items()}
    if isinstance(value, list):
        return [shape_of(item) for item in value[:1]]
    return type(value).__name__


def call(base: str, token: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        response = httpx.get(
            base + path, params=params, headers={"Authorization": "Bearer " + token}, timeout=180
        )
    except Exception as exc:  # noqa: BLE001 - throwaway harness
        return {"status": None, "error": "%s: %s" % (type(exc).__name__, exc), "elapsed": 0.0}
    elapsed = time.perf_counter() - started
    body: Any
    try:
        body = response.json()
    except Exception:  # noqa: BLE001 - non-JSON payload
        body = {"__raw__": response.text[:400], "__len__": len(response.content)}
    return {"status": response.status_code, "body": body, "elapsed": elapsed}


def main() -> int:
    tokens = load_tokens()
    endpoints = collect_endpoints()
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only:
        endpoints = [row for row in endpoints if only in row[0]]

    print("endpoints:", len(endpoints))
    results = []
    for index, (path, params) in enumerate(endpoints, 1):
        java = call(BACKENDS["java"], tokens["java"], path, params)
        py = call(BACKENDS["python"], tokens["python"], path, params)

        record: Dict[str, Any] = {"path": path, "params": params, "java_status": java["status"], "py_status": py["status"]}
        if java.get("error") or py.get("error"):
            record.update({"verdict": "CONN", "detail": [java.get("error"), py.get("error")]})
        elif java["status"] != py["status"]:
            record.update({"verdict": "STATUS", "detail": [java["status"], py["status"]]})
        elif path in STATUS_ONLY:
            record.update({"verdict": "STATUS-ONLY", "detail": [java["status"]]})
        elif path in SHAPE_ONLY:
            diffs = deep_diff(shape_of(java["body"]), shape_of(py["body"]))
            record.update({"verdict": "SHAPE-DIFF" if diffs else "SHAPE-OK", "detail": diffs[:20]})
        else:
            diffs = deep_diff(java["body"], py["body"])
            if not diffs:
                record.update({"verdict": "SAME", "detail": []})
            elif classify_order_only(java["body"], py["body"]):
                record.update({"verdict": "ORDER", "detail": diffs[:10]})
            else:
                verdict = "DIFF"
                if isinstance(java["body"], dict) and isinstance(py["body"], dict):
                    if java["body"].get("code") != py["body"].get("code"):
                        verdict = "CODE"
                record.update({"verdict": verdict, "detail": diffs[:40]})
        record["java_ms"] = round(java.get("elapsed", 0) * 1000)
        record["py_ms"] = round(py.get("elapsed", 0) * 1000)
        results.append(record)
        if index % 20 == 0:
            print("  ... %d/%d" % (index, len(endpoints)), flush=True)

    RAW.write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    buckets: Dict[str, List[dict]] = {}
    for record in results:
        buckets.setdefault(record["verdict"], []).append(record)
    print("\n=== verdicts ===")
    for verdict, rows in sorted(buckets.items(), key=lambda item: -len(item[1])):
        print("%-12s %d" % (verdict, len(rows)))

    lines = ["# Java vs Python 接口数据比对（自动扫描）", "", "共 %d 个只读 GET 端点。" % len(results), "", "| 结论 | 数量 |", "| --- | --- |"]
    for verdict, rows in sorted(buckets.items(), key=lambda item: -len(item[1])):
        lines.append("| %s | %d |" % (verdict, len(rows)))
    lines.append("")
    for verdict in ("CODE", "DIFF", "STATUS", "CONN", "ORDER", "SHAPE-DIFF", "MISSING"):
        if verdict not in buckets:
            continue
        lines.append("## %s (%d)" % (verdict, len(buckets[verdict])))
        for record in buckets[verdict]:
            lines.append("")
            lines.append("### `GET %s`  java=%sms py=%sms" % (record["path"], record["java_ms"], record["py_ms"]))
            for diff in record["detail"]:
                lines.append("- %s" % json.dumps(diff, ensure_ascii=False, default=str))
        lines.append("")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nreport ->", REPORT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
