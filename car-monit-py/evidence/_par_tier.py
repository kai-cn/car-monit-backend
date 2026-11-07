# -*- coding: utf-8 -*-
"""分档双端一致性校验：Java backend(:9788) vs Python backend(:9789)。

档位（沿用 car-monit-go/scripts/parity/compare_get.py 的定义，路径变量语法换成 {var}）：
  api       —— 经 vehicleMonitor.baseUrl 转发到 car-monit-api 的接口
  business  —— /manager、/base、/flow 里其余读库接口
  framework —— /system、/monitor、/tool、/oss、/common、/v3、/swagger 等框架接口

URL 清单来源：scripts/audit_endpoints.py 的 **Java 静态清单**（501 条），
这样"Python 少了接口"不会被自动忽略；路径占位符用 Java 侧 /list 首行的真实值填充。

空表会让数据比对失明，所以第 1 档除了默认参数还跑 TIME/EMPTY 两套矩阵
（feerecords 要 inApplyTime1/2，snapshotflow 要 applyTime1/2，轨迹要 carNo）。

用法::

    python evidence/_par_tier.py --tier api      --out $TEMP/t1.json
    python evidence/_par_tier.py --tier business --out $TEMP/t2.json
    python evidence/_par_tier.py --tier framework --out $TEMP/t3.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import _par_common as C  # noqa: E402

VAR_RE = re.compile(r"\{([^}]+)\}")
LIST_HINT = re.compile(r"/(list|listAll|listMy|listutil)$")

API_ROUTES = (
    re.compile(r"^/base/(feeGantry|feerecords|feestationexit|snapshotflow)(/|$)"),
    re.compile(r"^/manager/cartrackinfo/(listByCarId|listByCarByTime|carSnapShot)$"),
)
BUSINESS_ROOTS = ("/manager", "/base", "/flow")
FRAMEWORK_ROOTS = ("/system", "/monitor", "/tool", "/oss", "/common", "/v3", "/swagger",
                   "/login", "/logout", "/getInfo", "/getRouters", "/captchaImage", "/health")

# 运行态/二进制：只比状态码或形状
STATUS_ONLY = {"/captchaImage", "/health", "/common/download", "/common/download/resource",
               "/system/user/importTemplate", "/system/file/view", "/v3/api-docs",
               "/swagger-ui/index.html", "/swagger-ui.html"}
SHAPE_ONLY = {"/monitor/server", "/monitor/cache", "/monitor/online/list",
              "/monitor/cache/getNames", "/monitor/job/list"}

# 会写库/打外部系统/依赖缺表，本轮不比
SKIP_PREFIXES = ("/base/geometry", "/base/cdc", "/downTemplate", "/test/",
                 "/base/sysutilTest", "/monitor/job/export")

FALLBACK = {
    "expires": "60", "ids": "1", "type": "0", "status": "0", "name": "readme.txt",
    "fileName": "readme.txt", "bucketName": "developer", "objectName": "parity",
    "roleCode": "admin", "dictType": "sys_yes_no", "configKey": "sys.index.skinName",
    "jobGroupName": "DEFAULT", "jobName": "parity", "jobGroup": "DEFAULT",
    "tableName": "sys_user", "columns": "user_id", "serviceName": "sys",
    "ipaddr": "127.0.0.1", "shareId": "1", "noticeId": "1", "ver": "1", "id": "1",
}

#: 第 1 档参数矩阵（label -> (子串匹配, params))。carNo/时间窗在运行时用真实样本填充。
TIME_MATRIX = {
    "/base/feerecords": {"inApplyTime1": "2025-08-01 00:00:00", "inApplyTime2": "2025-08-31 23:59:59"},
    "/base/snapshotflow": {"applyTime1": "2025-08-01 00:00:00", "applyTime2": "2025-08-02 00:00:00"},
    "/base/feeGantry": {},
    "/base/feestationexit": {},
}


def in_tier(path: str, tier: str) -> bool:
    if tier == "api":
        return any(r.match(path) for r in API_ROUTES)
    if tier == "business":
        return path.startswith(BUSINESS_ROOTS) and not any(r.match(path) for r in API_ROUTES)
    if tier == "framework":
        return path.startswith(FRAMEWORK_ROOTS)
    return True


def inventory(tier: str, only: str):
    """Java 静态 GET 清单 ∩ Python 注册清单（Python 缺失的另行报告）。"""
    import audit_endpoints as A

    norm = A.normalize_path
    rep = A.build_report()
    java_get = sorted({e.path for e in rep.java if e.method == "GET"})
    py_get = {norm(p) for _m, p in rep.python if _m == "GET"}
    java_norm = {norm(p) for p in java_get}
    rows = []
    for path in java_get:
        if any(path.startswith(s) for s in SKIP_PREFIXES):
            continue
        if "/export" in path:
            continue  # 附件流交给 _par_xlsx.py
        if only and only not in path:
            continue
        if not in_tier(path, tier):
            continue
        rows.append({"path": path, "on_python": norm(path) in py_get})
    missing = [p for p in java_get
               if norm(p) not in py_get and not any(p.startswith(s) for s in SKIP_PREFIXES)]
    extra = sorted({p for _m, p in rep.python if _m == "GET" and norm(p) not in java_norm})
    return rows, missing, extra


def harvest(cases, tk):
    """扫 Java 侧列表接口，收集字段名 -> 真实样本，用于填充占位符与时间/车牌参数。

    同时按模块存一份（``<module>|<field>``）：``/base/gantryIp/{id}`` 的主键是 Long，
    用全局 samples 里的 hex32 bigId 去填会两端都报错，只有错误文本可比。
    """
    samples = {}
    for row in cases:
        path = row["path"]
        if VAR_RE.search(path) or not LIST_HINT.search(path):
            continue
        module = re.sub(r"(listAll|listMy|listutil|list)$", "", path).strip("/")
        body = C.req(C.JAVA, path, tk, params={"pageNum": 1, "pageSize": 1})
        rows = body.get("rows") if isinstance(body, dict) else None
        if not isinstance(rows, list):
            rows = body.get("data") if isinstance(body, dict) else None
        if isinstance(body, list):
            rows = body
        if not rows or not isinstance(rows[0], dict):
            continue
        for key, value in rows[0].items():
            if value is None or isinstance(value, (dict, list)):
                continue
            low = key.lower()
            samples.setdefault(low, str(value))
            samples.setdefault(module + "|" + low, str(value))
            samples.setdefault(re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key).lower(), str(value))
            samples.setdefault(module + "|" + re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key).lower(),
                               str(value))
            if low in ("bigid", "id"):
                samples.setdefault("bigid", str(value))
                samples.setdefault(module + "|bigid", str(value))
    return samples


def fill_vars(path: str, samples) -> str:
    module = path.rsplit("/", 1)[0].strip("/")

    def repl(match):
        name = match.group(1)
        for cand in (name, name.rstrip("s")):
            key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cand).lower().strip("_")
            for probe in (module + "|" + key, key):
                if probe in samples:
                    return samples[probe]
            if cand in FALLBACK:
                return FALLBACK[cand]
        return FALLBACK.get(name, "1")

    return VAR_RE.sub(repl, path)


def carno(samples) -> str:
    for key in ("carno", "car_no", "platekey", "plate_no", "plateno"):
        if samples.get(key):
            return samples[key]
    return "1"


def build_urls(cases, samples, tier: str):
    out, seen = [], set()
    for row in cases:
        path = fill_vars(row["path"], samples)
        sets = []
        if LIST_HINT.search(path):
            base = {"pageNum": 1, "pageSize": 20}
            sets.append(("", base))
        else:
            sets.append(("", {}))
        if tier == "api":
            for prefix, extra in TIME_MATRIX.items():
                if not extra or not path.startswith(prefix):
                    continue
                merged = dict(sets[0][1])
                merged.update(extra)
                if path.startswith("/manager/cartrackinfo"):
                    merged["carNo"] = carno(samples)
                sets.append(("time", merged))
        if path.startswith("/manager/cartrackinfo"):
            merged = dict(sets[0][1])
            merged["carNo"] = carno(samples)
            sets.append(("carNo", merged))
        for label, params in sets:
            key = (path, json.dumps(params, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            out.append({"path": path, "params": params, "label": label,
                        "on_python": row["on_python"]})
    return out


def probe(case, tk_j, tk_p):
    path, params = case["path"], case["params"]
    sj, rj, _cj = C.call(C.JAVA, path, tk_j, params=params)
    sp, rp, _cp = C.call(C.PY, path, tk_p, params=params)
    try:
        bj = json.loads(rj)
    except Exception:  # noqa: BLE001
        bj = None
    try:
        bp = json.loads(rp)
    except Exception:  # noqa: BLE001
        bp = None
    rec = {"path": path, "params": params, "label": case["label"],
           "on_python": case["on_python"], "java": sj, "py": sp}
    if sj == -1 or sp == -1:
        rec.update(kind="CONN", detail=[rj[:120].decode("utf-8", "ignore"),
                                        rp[:120].decode("utf-8", "ignore")])
        return rec
    if bj is None or bp is None:
        rec.update(kind="non-json", detail=[len(rj), len(rp)])
        return rec
    if sj != sp:
        rec.update(kind="STATUS", detail=[sj, sp])
        return rec
    if path in STATUS_ONLY:
        rec.update(kind="STATUS-OK", detail=[sj])
        return rec
    if path in SHAPE_ONLY:
        diffs = C.deep_diff(C.shape_of(bj), C.shape_of(bp))
        rec.update(kind="SHAPE-OK" if not diffs else "SHAPE-DIFF", detail=diffs[:12])
        return rec
    nj, np_ = C.norm(bj), C.norm(bp)
    diffs = C.deep_diff(nj, np_)
    if not diffs:
        rec.update(kind="SAME", detail=[])
        return rec
    if isinstance(bj, dict) and isinstance(bp, dict) and bj.get("code") != bp.get("code"):
        rec.update(kind="CODE", detail=diffs[:6])
        return rec
    if C.order_only(nj, np_) and all(d["kind"] in ("VALUE", "MISSING") for d in diffs[:1]):
        rec.update(kind="ORDER", detail=diffs[:8])
        return rec
    kinds = sorted({d["kind"] for d in diffs})
    rec.update(kind="+" .join(kinds) if len(kinds) <= 2 else "DIFF", detail=diffs[:12],
               ndiff=len(diffs))
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", required=True, choices=["api", "business", "framework", "all"])
    ap.add_argument("--out", default="")
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh-token", action="store_true")
    args = ap.parse_args()

    tk = C.tokens(refresh=args.refresh_token)
    cases, java_only, py_only = inventory(args.tier, args.only)
    samples = harvest(cases, tk["java"])
    urls = build_urls(cases, samples, args.tier)
    if args.limit:
        urls = urls[: args.limit]
    print("档位=%s 待比 URL %d 条（样本字段 %d 个；Java 独有路径 %d，Python 独有 %d）"
          % (args.tier, len(urls), len(samples), len(java_only), len(py_only)), flush=True)

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        first = list(pool.map(lambda u: probe(u, tk["java"], tk["python"]), urls))
    for i, (case, rec) in enumerate(zip(urls, first), 1):
        if rec["kind"] not in ("SAME", "STATUS-OK", "SHAPE-OK"):
            # api 侧冷缓存、审计表自增长都会造成一次性抖动，非一致先复验
            again = probe(case, tk["java"], tk["python"])
            rec["confirmed"] = again["kind"] == rec["kind"]
            rec["second"] = {"kind": again["kind"], "java": again["java"], "py": again["py"],
                             "detail": again.get("detail", [])[:4]}
        results.append(rec)
        if rec["kind"] not in ("SAME", "STATUS-OK", "SHAPE-OK"):
            print("  %-10s %s %s %s%s" % (rec["kind"], rec["path"],
                                          json.dumps(rec["params"], ensure_ascii=False)[:60],
                                          json.dumps(rec["detail"], ensure_ascii=False, default=str)[:170],
                                          "" if rec["confirmed"] else "  [复验形态不同]"),
                  flush=True)
        if i % 30 == 0:
            print("  ... 已比 %d/%d" % (i, len(urls)), flush=True)

    buckets = {}
    for rec in results:
        buckets[rec["kind"]] = buckets.get(rec["kind"], 0) + 1
    summary = {
        "tier": args.tier,
        "java_base": C.JAVA, "py_base": C.PY, "java_db": C.JAVA_DB, "py_db": C.PY_DB,
        "api_java": C.API_JAVA, "api_py": C.API_PY,
        "total": len(results), "buckets": buckets,
        "java_only_paths": java_only, "python_only_paths": py_only,
        "not_on_python": [r["path"] for r in results if not r["on_python"]],
        "entries": results,
    }
    print("\n== 汇总 %s: total=%d %s" % (args.tier, len(results),
          " ".join("%s=%d" % kv for kv in sorted(buckets.items()))))
    if args.out:
        Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str),
                                  encoding="utf-8")
        print("报告:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
