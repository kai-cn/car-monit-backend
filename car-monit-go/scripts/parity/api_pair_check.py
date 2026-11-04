# -*- coding: utf-8 -*-
"""api 双端（car-monit-api 的 Java 端 9902 / Go 端 9903）直连比对。

backend 的 tier-1 差异必须先归因：是 backend 不一致，还是它调的 api 不一致。
本脚本直接打 api 两端，比对 23 条 backend 会用到的路径（详情路径的 bigId 取自列表首行）。

用法:
  MSYS2_ARG_CONV_EXCL='*' python scripts/parity/api_pair_check.py [--java 9902] [--go 9903]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402

# backend 的 forest client 声明的全部 api 路径（{bigId} 用列表首行的真实值填充）
LIST_PATHS = [
    "/base/feeGantry/list", "/base/feerecords/list", "/base/feestationexit/list",
    "/base/snapshotflow/list", "/base/snapshotflow/listToExport",
    "/base/section/listAll", "/base/toll/listAll", "/base/gantry/listAll",
    "/base/org/listAll", "/base/fwqjcxx/listAll", "/base/sfsjcxx/listAll",
]
DETAIL_TEMPLATE = "/base/%s/{bigId}"
EARLIEST = "/base/snapshotflow/earliest-time"


def fetch(port, path):
    st, raw, ct = pp.call("http://127.0.0.1:%d" % port, path, None, timeout=120)
    try:
        body = json.loads(raw)
    except Exception:
        body = None
    return st, ct, raw, body


def norm_json(v):
    if isinstance(v, dict):
        return {k: norm_json(x) for k, x in v.items() if k not in ("timestamp",)}
    if isinstance(v, list):
        return [norm_json(x) for x in v]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--java", type=int, default=9902)
    ap.add_argument("--go", type=int, default=9903)
    args = ap.parse_args()

    rows = []
    ids = {}
    for path in LIST_PATHS:
        sj, cj, rj, bj = fetch(args.java, path + ("?pageNum=1&pageSize=3" if path.endswith("/list") else ""))
        sg, cg, rg, bg = fetch(args.go, path + ("?pageNum=1&pageSize=3" if path.endswith("/list") else ""))
        same_status = sj == sg
        d = pp.diff(pp.norm(norm_json(bj) if bj is not None else rj),
                    pp.norm(norm_json(bg) if bg is not None else rg)) if same_status else []
        kind = "same" if same_status and (d == [] or d is None) else ("status" if not same_status else "diff")
        rows.append((path, sj, sg, len(rj), len(rg), kind, (str(d[0])[:90] if d else "")))
        # 抓 bigId 供详情路径使用
        if isinstance(bj, dict) and isinstance(bj.get("rows"), list) and bj["rows"]:
            first = bj["rows"][0]
            key = first.get("bigId") or first.get("id")
            if key:
                mod = path.split("/")[2]
                ids.setdefault(mod, str(key))
        if isinstance(bj, list) and bj:
            key = bj[0].get("bigId") or bj[0].get("id")
            if key:
                ids.setdefault(path.split("/")[2], str(key))

    print("%-34s %-6s %-6s %-9s %-9s %s" % ("api 路径", "java", "go", "字节(j)", "字节(g)", "结论"))
    bad = 0
    for path, sj, sg, nj, ng, kind, first in rows:
        flag = "OK  " if kind == "same" else "BAD "
        if kind != "same":
            bad += 1
        print("%s %-34s %-6s %-6s %-9s %-9s %s %s" % (flag, path[:34], sj, sg, nj, ng, kind, first))

    print("\n== 详情路径（bigId 取自列表首行）==")
    for mod, big in sorted(ids.items()):
        path = "/base/%s/%s" % (mod, big)
        sj, cj, rj, bj = fetch(args.java, path)
        sg, cg, rg, bg = fetch(args.go, path)
        same = sj == sg and pp.diff(pp.norm(norm_json(bj) if bj is not None else rj),
                                    pp.norm(norm_json(bg) if bg is not None else rg)) == []
        if not same:
            bad += 1
        print("%s %-34s java=%s(%dB) go=%s(%dB)" % ("OK  " if same else "BAD ", path[:34], sj, len(rj), sg, len(rg)))

    sj, cj, rj, bj = fetch(args.java, EARLIEST)
    sg, cg, rg, bg = fetch(args.go, EARLIEST)
    if not (sj == sg and rj == rg):
        bad += 1
        print("BAD  %-34s java=%s(%r) go=%s(%r)" % (EARLIEST, sj, rj[:40], sg, rg[:40]))
    else:
        print("OK   %-34s 两端一致（%s, %dB）" % (EARLIEST, sj, len(rj)))

    print("\napi 双端不一致 %d 条" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
