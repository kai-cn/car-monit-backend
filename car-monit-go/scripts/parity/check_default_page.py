# -*- coding: utf-8 -*-
"""默认分页一致性专项校验。

Java 的 TableSupport.getPageDomain 在请求不带 pageNum/pageSize 时取默认 1/10，
所以任何调用 startPage() 的 GET 端点都「必定分页」。Go 只有在 handler 用
web.PageAlways(c) 时才是这个语义（web.Page(c) 在无参数时退化为不分页）。
本脚本把 Java 里所有 startPage() 的 GET 路由列出来，在不带分页参数的前提下
逐条比对两端的 rows 数量与 total。

用法:
  MSYS2_ARG_CONV_EXCL='*' python scripts/parity/check_default_page.py [--only /manager]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402
import compare_get as G  # noqa: E402
from routes import (ANN_RE, CLASS_MAP_RE, JAVA_ROOT, MODULES, REQUEST_METHOD_RE,  # noqa: E402
                    norm, paths_of, scan_go, strip_comments)


def java_startpage_paths():
    out = set()
    for mod in MODULES:
        base = os.path.join(JAVA_ROOT, mod, "src", "main", "java")
        if not os.path.isdir(base):
            continue
        for root, _, names in os.walk(base):
            for name in names:
                if not name.endswith(".java"):
                    continue
                raw = open(os.path.join(root, name), encoding="utf-8", errors="ignore").read()
                if "@RestController" not in raw:
                    continue
                text = strip_comments(raw)
                head = text.split("public class", 1)[0]
                cm = CLASS_MAP_RE.search(head)
                class_paths = paths_of(cm.group(1)) if cm else [""]
                body = text[len(head):]
                for m in ANN_RE.finditer(body):
                    args = (m.group(2) or "")[1:-1]
                    if "startPage()" not in body[m.end():m.end() + 1800]:
                        continue
                    verbs = REQUEST_METHOD_RE.findall(args) or [m.group(1).replace("Mapping", "").upper()]
                    if "GET" not in verbs:
                        continue
                    for cp in class_paths:
                        for mp in paths_of(args) or [""]:
                            out.add(norm(cp + "/" + mp))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=os.path.join(os.environ.get("TEMP", "/tmp"), "carmonit.log"))
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    tk_j, tk_g = pp.login_java(), pp.login_go()
    java_paths = java_startpage_paths()
    go_routes = {p for _, p in scan_go(args.log)}
    all_get = G.load_routes(args.log, "")
    samples = G.harvest_samples(tk_j, all_get)

    checked = skipped = 0
    bad = []
    for path in java_paths:
        if args.only and not path.startswith(args.only):
            continue
        url = G.fill(path, samples) if ":" in path else path
        if norm(url) not in go_routes:
            skipped += 1
            continue
        a, b = pp.req(pp.JAVA, url, tk_j), pp.req(pp.GO, url, tk_g)
        if not isinstance(a, dict) or "rows" not in a or not isinstance(b, dict) or "rows" not in b:
            skipped += 1
            continue
        checked += 1
        la, lb = len(a.get("rows") or []), len(b.get("rows") or [])
        if la != lb or a.get("total") != b.get("total"):
            bad.append((url, la, lb, a.get("total"), b.get("total")))

    print("\n默认分页校验：比对 %d 条，跳过（非 JSON/Go 无此路由）%d 条，不一致 %d 条"
          % (checked, skipped, len(bad)))
    for url, la, lb, ta, tb in bad:
        print("   %-58s rows java=%-4d go=%-4d total java=%-6s go=%s" % (url, la, lb, ta, tb))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
