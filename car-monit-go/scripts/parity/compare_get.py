# -*- coding: utf-8 -*-
"""全量 GET 双端逐字段对比。

路由来源：Go 启动日志里的 [GIN-debug] GET 行（运行态注册才算数），
路径占位符用真实样本填充（先扫各模块 /list 接口取 rows[0] 的 id 字段）。
每个 URL 在 Java(9988) 与 Go(9989) 各请求一次，归一化后深度比较。

用法:
  python scripts/parity/compare_get.py --prefix /manager [--out report.json] [--workers 4]
"""
import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402
from routes import GIN_RE, norm  # noqa: E402

# 占位符 -> 兜底样本值（能从 /list 里取到真实值时优先用真实值）
FALLBACK = {
    "expires": "60", "ids": "1", "type": "0", "status": "0",
    "fileName": "readme.txt", "bucketName": "developer", "objectName": "parity",
    "roleCode": "admin", "dictType": "sys_yes_no", "configKey": "sys.index.skinName",
    "jobGroupName": "DEFAULT", "jobName": "parity", "jobGroup": "DEFAULT",
    "tableName": "sys_user", "columns": "user_id", "serviceName": "sys",
    "ipaddr": "127.0.0.1", "shareId": "1", "noticeId": "1", "ver": "1",
}
LIST_HINT = re.compile(r"/(list|listAll|listMy|listutil)$")
# 已知会改写数据或打外部服务的 GET（仍要比，只是报告里单独标注）
SIDE_EFFECT = ("syncAllGeometry", "getHenDa", "sendSms", "cdc/", "snapshot")


# 分层校验：按「响应是否来自 car-monit-api」划分，先易后难、先外后内
#   api       —— 经 vehicleMonitor.baseUrl 转发到 car-monit-api 的接口
#   business  —— 其余业务接口（/manager、/base、/flow 里读库的部分）
#   framework —— 框架接口（/system、/monitor、/tool、/oss、登录验证码等）
API_ROUTES = (
    re.compile(r"^/base/(feeGantry|feerecords|feestationexit|snapshotflow)(/|$)"),
    re.compile(r"^/manager/cartrackinfo/(listByCarId|listByCarByTime|carSnapShot)$"),
)
BUSINESS_ROOTS = ("/manager", "/base", "/flow")
FRAMEWORK_ROOTS = ("/system", "/monitor", "/tool", "/oss", "/common", "/v3", "/swagger")
# 顶层单段路由不在任何 root 下，但都是登录后立刻要用的只读接口，归进框架档一起比：
#   /getInfo /getRouters —— 前端取当前用户信息与菜单
#   /downTemplate/:x     —— 下载导入模板（ExcelUtil 落盘型，附件流由 compare_export_all 逐格比）
#   /test/**             —— 脚手架演示表，Java 侧同样注册了（只读部分比一下不要钱）
FRAMEWORK_EXTRA = ("/getInfo", "/getRouters", "/downTemplate", "/test")


def in_tier(path, tier):
    if tier == "api":
        return any(r.match(path) for r in API_ROUTES)
    if tier == "business":
        return path.startswith(BUSINESS_ROOTS) and not any(r.match(path) for r in API_ROUTES)
    if tier == "framework":
        return path.startswith(FRAMEWORK_ROOTS) or path.startswith(FRAMEWORK_EXTRA)
    return True


def load_routes(log_path, prefix, tier=""):
    text = open(log_path, encoding="utf-8", errors="ignore").read()
    out = []
    for m in GIN_RE.finditer(text):
        method, path = m.group(1), m.group(2)
        if method != "GET" or path.startswith("http"):
            continue
        path = norm(path)
        if prefix and not path.startswith(prefix):
            continue
        if tier and not in_tier(path, tier):
            continue
        if path in ("/", "/healthz"):
            continue
        out.append(path)
    # 去重（同一模板只测一次）
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def harvest_samples(token, routes):
    """扫所有 /list 接口，收集字段名 -> 样本值，用于填充路径占位符。"""
    samples = {}
    for path in routes:
        if not LIST_HINT.search(path) or ":" in path:
            continue
        url = path + "?pageNum=1&pageSize=1"
        data = pp.req(pp.JAVA, url, token)
        rows = data.get("rows") if isinstance(data, dict) else None
        if not isinstance(rows, list) and isinstance(data, dict):
            rows = data.get("data")
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            continue
        for key, value in rows[0].items():
            if isinstance(value, (dict, list)) or value is None:
                continue
            low = key.lower()
            samples.setdefault(low, str(value))
            samples.setdefault(re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key).lower(), str(value))
            if low == "bigid":
                # api 侧详情路径的占位符是 :id，但真实主键叫 bigId
                samples.setdefault("id", str(value))
    return samples


def fill(path, samples):
    def repl(m):
        name = m.group(1)
        for cand in (name, name.rstrip("s"), name + "s"):
            key = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cand).lower()
            if key in samples:
                return samples[key]
            if cand in FALLBACK:
                return FALLBACK[cand]
        return FALLBACK.get(name, "1")

    return re.sub(r":([A-Za-z_]\w*)", repl, path)


def probe(path, tk_j, tk_g):
    sj, rj, cj = pp.call(pp.JAVA, path, tk_j)
    sg, rg, cg = pp.call(pp.GO, path, tk_g)
    try:
        j = json.loads(rj)
    except Exception:
        j = None
    try:
        g = json.loads(rg)
    except Exception:
        g = None
    if j is None or g is None:
        return {"p": path, "kind": "non-json", "java": [sj, cj[:40], len(rj)],
                "go": [sg, cg[:40], len(rg)]}
    noise = {k for k in ("timestamp", "random")}
    d = pp.diff(pp.norm(j, noise), pp.norm(g, noise))
    if not d:
        return {"p": path, "kind": "same"}
    return {"p": path, "kind": "diff", "java_code": j.get("code") if isinstance(j, dict) else None,
            "go_code": g.get("code") if isinstance(g, dict) else None, "diff": d[:8]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=os.path.join(os.environ.get("TEMP", "/tmp"), "carmonit.log"))
    ap.add_argument("--prefix", default="")
    ap.add_argument("--tier", default="", choices=["", "api", "business", "framework"],
                    help="tier check: api / business / framework")
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    tk_j, tk_g = pp.login_java(), pp.login_go()
    routes = load_routes(args.log, args.prefix, args.tier)
    samples = harvest_samples(tk_j, routes)
    urls = []
    for p in routes:
        u = fill(p, samples)
        if "?" not in u and "/list" in u:
            u += "?pageNum=1&pageSize=3"
        if u not in urls:
            urls.append(u)
    if args.limit:
        urls = urls[:args.limit]
    print("前缀 %s 待比 URL %d 条（占位符样本 %d 个字段）" % (args.prefix or "/", len(urls), len(samples)))

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(lambda u: probe(u, tk_j, tk_g), urls), 1):
            results.append(res)
            if res["kind"] != "same":
                print("  %s %s %s" % (res["kind"][:5], res["p"],
                                      json.dumps(res.get("diff", res.get("java", "")), ensure_ascii=False)[:150]))
            if i % 25 == 0:
                print("  ... 已比 %d/%d" % (i, len(urls)))

    summary = {
        "prefix": args.prefix or "/",
        "tier": args.tier or "all",
        "total": len(urls),
        "same": sum(1 for r in results if r["kind"] == "same"),
        "diff": sum(1 for r in results if r["kind"] == "diff"),
        "nonjson": sum(1 for r in results if r["kind"] == "non-json"),
        "side_effect": sum(1 for r in results if any(s in r["p"] for s in SIDE_EFFECT)),
        "entries": results,
    }
    print("\n== 汇总 %s: total=%d same=%d diff=%d non-json=%d" % (
        summary["prefix"], summary["total"], summary["same"], summary["diff"], summary["nonjson"]))
    if args.out:
        json.dump(summary, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("报告:", args.out)


if __name__ == "__main__":
    main()
