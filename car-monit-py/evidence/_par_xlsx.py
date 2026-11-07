# -*- coding: utf-8 -*-
"""导出接口双端对比（单元格级）。

两类导出都要覆盖：
  * 附件流（EasyPOI 模板 / POI 直接写）—— 响应体就是 xlsx 字节
  * ExcelUtil 型 —— 响应是 ``{"msg":"<uuid>_xx.xlsx"}``，文件落在 profile/download

两端 writer 不同（POI vs openpyxl），字节永远不可能一致，所以只比
「sheet 名 + 单元格值」。两端都为空的尾部整行/整列会被裁掉（POI 习惯多写一列空样式列、
EasyPOI 空列表时多写一行空格），带值的行列不会被裁。

用法::

    python evidence/_par_xlsx.py [--tier api|business|framework|all] [--only 子串]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _par_common as C  # noqa: E402
import _par_tier as T  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

DOWNLOAD_DIR = os.environ.get("PAR_DOWNLOAD_DIR", "D:/ruoyi/uploadPath/download").replace("\\", "/")

#: 审计日志型导出：本端请求自己会被记进表里，两端调用有先后 ⇒ 必须钉死时间窗。
#: RuoYi 的区间参数是 `params[beginTime]` / `params[endTime]`，写成裸 beginTime 会被忽略。
CLOSED_WINDOW = {
    "/monitor/operlog/export": {"params[beginTime]": "2020-01-01",
                                "params[endTime]": "2026-11-05 09:00:00"},
    "/monitor/logininfor/export": {"params[beginTime]": "2020-01-01",
                                   "params[endTime]": "2026-11-05 09:00:00"},
    "/monitor/jobLog/export": {"params[beginTime]": "2020-01-01",
                               "params[endTime]": "2026-11-05 09:00:00"},
    "/manager/querylog/export": {"params[beginTime]": "2020-01-01",
                                 "params[endTime]": "2026-11-05 09:00:00"},
}


def is_xlsx(raw: bytes) -> bool:
    return raw[:2] == b"PK" and len(raw) > 4000


def cells(body: bytes):
    book = load_workbook(io.BytesIO(body), data_only=True)
    out = []
    for sheet in book.worksheets:
        # values_only=True：拿单元格的值，不是 <Cell 'Sheet'.A1> 这种坐标 repr
        rows = [["" if v is None else str(v) for v in row]
                for row in sheet.iter_rows(values_only=True)]
        out.append((sheet.title, rows))
    return out


def trim(sheets):
    """裁掉两端都可能多写的空尾行/空尾列。"""
    cleaned = []
    for title, rows in sheets:
        while rows and all(c == "" for c in rows[-1]):
            rows.pop()
        width = max((len(r) for r in rows), default=0)
        rows = [r + [""] * (width - len(r)) for r in rows]
        while width > 0 and all(r[width - 1] == "" for r in rows):
            for r in rows:
                r.pop()
            width -= 1
        cleaned.append((title, rows))
    return cleaned


def resolve_written(msg: str) -> str:
    """ExcelUtil 返回值 -> 本次调用生成的落盘文件（越界路径一律拒绝）。"""
    if not isinstance(msg, str) or not msg.lower().endswith(".xlsx"):
        return ""
    base = os.path.basename(msg)
    if base != msg or ".." in base:
        return ""
    full = (DOWNLOAD_DIR + "/" + base).replace("\\", "/")
    return full if os.path.isfile(full) else ""


def grab(base, token, path, params):
    """Return (kind, bytes, status, note). kind in {xlsx, json, other, conn}."""
    status, raw, ctype = C.call(base, path, token, params=params)
    if status == -1:
        return "conn", raw, status, ""
    if is_xlsx(raw):
        return "xlsx", raw, status, ""
    try:
        body = json.loads(raw)
    except Exception:  # noqa: BLE001
        return "other", raw, status, ctype[:40]
    full = resolve_written(str(body.get("msg", ""))) if isinstance(body, dict) else ""
    if full:
        data = Path(full).read_bytes()
        Path(full).unlink(missing_ok=True)  # 只删本次调用生成的文件
        return "xlsx", data, status, "file:" + os.path.basename(full)
    return "json", raw, status, ""


def export_paths(tier: str, only: str):
    import audit_endpoints as A

    rep = A.build_report()
    out = []
    for e in sorted({(x.path) for x in rep.java if x.method == "GET" and "export" in x.path}):
        if only and only not in e:
            continue
        if not T.in_tier(e, tier):
            continue
        out.append(e)
    return out


def num_equal(a: str, b: str) -> bool:
    """1.0 vs 1、2880.40 vs 2880.4 这类「同一个数不同写法」。"""
    try:
        return float(a) == float(b)
    except Exception:  # noqa: BLE001
        return False


def stamp_equal(a: str, b: str) -> bool:
    """2026-02-03 16:19:19.572 vs .572000：同一时刻、小数秒补零差异。"""
    import re

    if re.match(r"^\d{4}-\d{2}-\d{2} ", a) and re.match(r"^\d{4}-\d{2}-\d{2} ", b):
        return a.rstrip("0").rstrip(".") == b.rstrip("0").rstrip(".") or a[:19] == b[:19]
    return False


def java_date_equal(a: str, b: str) -> bool:
    """Thu Aug 21 00:00:00 CST 2025（Date.toString）vs 2025-08-21 00:00:00。"""
    import datetime

    try:
        da = datetime.datetime.strptime(a, "%a %b %d %H:%M:%S %Z %Y")
    except Exception:  # noqa: BLE001
        return False
    try:
        db = datetime.datetime.fromisoformat(b)
    except Exception:  # noqa: BLE001
        return False
    return da == db


def classify(a: str, b: str) -> str:
    if num_equal(a, b):
        return "NUM"
    if stamp_equal(a, b):
        return "STAMP"
    if java_date_equal(a, b) or java_date_equal(b, a):
        return "JDATE"
    return "VALUE"


def sheet_diffs(cj, cp):
    """逐格对比 + 行级排序无关判定，返回 (kind, stats, sample)。"""
    diffs = []
    kinds = {}
    set_equal = True
    if [t for t, _ in cj] != [t for t, _ in cp]:
        diffs.append(["sheet-names", str([t for t, _ in cj]), str([t for t, _ in cp]), "SHEET"])
        kinds["SHEET"] = 1
    for (tj, rj), (tp, rp) in zip(cj, cp):
        for i in range(max(len(rj), len(rp))):
            left = rj[i] if i < len(rj) else ["<no-row>"]
            right = rp[i] if i < len(rp) else ["<no-row>"]
            for j in range(max(len(left), len(right))):
                a = left[j] if j < len(left) else "<no-cell>"
                b = right[j] if j < len(right) else "<no-cell>"
                if a != b:
                    k = classify(a, b)
                    kinds[k] = kinds.get(k, 0) + 1
                    if len(diffs) < 10:
                        diffs.append(["%s!r%dc%d" % (tj, i + 1, j + 1), a, b, k])
        # 行集合相同但顺序不同 = ORDER BY/排序差异，不是值差异
        set_equal = set_equal and sorted("|".join(r) for r in rj) == sorted(
            "|".join(r) for r in rp)
    stats = {"kinds": kinds, "ncell": sum(kinds.values()), "set_equal": set_equal,
             "rows": [len(r) for _t, r in cj][:3]}
    if not kinds:
        return "SAME", stats, []
    if set_equal and set(kinds) <= {"VALUE"}:
        return "ORDER", stats, diffs
    if set(kinds) <= {"NUM", "STAMP", "JDATE"}:
        return "FORMAT", stats, diffs
    return "DIFF", stats, diffs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="all", choices=["api", "business", "framework", "all"])
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="D:/tmp/par-xlsx.json")
    ap.add_argument("--page-size", default="30")
    args = ap.parse_args()

    tk = C.tokens()
    cases, _miss, _extra = T.inventory(args.tier if args.tier != "all" else "", args.only)
    samples = T.harvest(cases, tk["java"])
    paths = export_paths(args.tier, args.only)
    print("导出端点 %d 条（附件流 + ExcelUtil 落盘两类都覆盖）" % len(paths), flush=True)

    def one(path):
        filled = T.fill_vars(path, samples)
        if filled in CLOSED_WINDOW:
            params = dict(CLOSED_WINDOW[filled])
        else:
            params = {"pageNum": 1, "pageSize": args.page_size} if "?" not in filled else {}
        kj, bj, sj, nj = grab(C.JAVA, tk["java"], filled, params)
        kp, bp, sp, np_ = grab(C.PY, tk["python"], filled, params)
        rec = {"path": filled, "params": params, "java": [kj, sj, len(bj), nj],
               "py": [kp, sp, len(bp), np_]}
        if kj != kp:
            rec["kind"] = "KIND"      # 一端给附件、另一端给 JSON/错误
            return rec
        if kj == "conn":
            rec["kind"] = "CONN"
            return rec
        if kj in ("json", "other"):
            dj = C.deep_diff(
                C.norm(json.loads(bj) if kj == "json" else
                       {"raw": bj[:200].decode("utf-8", "ignore")}),
                C.norm(json.loads(bp) if kp == "json" else
                       {"raw": bp[:200].decode("utf-8", "ignore")}))
            rec["kind"] = "SAME" if not dj else "DIFF"
            rec["detail"] = dj[:6]
            return rec
        try:
            cj, cp = trim(cells(bj)), trim(cells(bp))
        except Exception as exc:  # noqa: BLE001
            rec["kind"] = "PARSE"
            rec["detail"] = [str(exc)[:200]]
            return rec
        if cj == cp:
            rec["kind"] = "SAME"
            rec["shape"] = [len(cj), [len(r) for _t, r in cj][:3]]
            return rec
        kind, stats, sample = sheet_diffs(cj, cp)
        rec["kind"] = kind
        rec["stats"] = stats
        rec["detail"] = sample
        return rec

    results = []
    for path in paths:
        rec = one(path)
        if rec["kind"] != "SAME":
            # 审计日志型表会被本端请求自己撑大，非 SAME 先复验一次再定性
            again = one(path)
            rec["confirmed"] = again["kind"] != "SAME"
            rec["second"] = {"kind": again["kind"], "java": again["java"][:3],
                             "py": again["py"][:3], "detail": again.get("detail", [])[:4]}
        print("  %-6s %s %s%s" % (rec["kind"], rec["path"],
                                  json.dumps(rec.get("detail", rec.get("shape", "")),
                                             ensure_ascii=False, default=str)[:150],
                                  "" if rec.get("confirmed", True) else "  [复验转为一致]"),
              flush=True)
        results.append(rec)

    buckets = {}
    for rec in results:
        buckets[rec["kind"]] = buckets.get(rec["kind"], 0) + 1
    summary = {"tier": args.tier, "total": len(results), "buckets": buckets, "entries": results,
               "java_base": C.JAVA, "py_base": C.PY}
    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str),
                              encoding="utf-8")
    print("\n== 导出层: total=%d %s -> %s" % (
        len(results), " ".join("%s=%d" % kv for kv in sorted(buckets.items())), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
