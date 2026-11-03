#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端点覆盖对账：Java 注解侧 vs C++ 注册侧。

背景：仓库里的 ENDPOINTS_INVENTORY.md 用方法签名正则统计，漏了约 144 个
`GET /{id}` 形态端点，也没扫 ruoyi-generator / ruoyi-quartz，所以"还剩多少"
一直没有可信答案。这里只按注解统计，并把 C++ 侧（含生成器产出的 spec）展开成
同样的 (方法, 路径) 集合做差集。路径变量统一成 /{*} 后比较。

用法：
    python scripts/endpoint_coverage.py            # 总计 + 按控制器分组
    python scripts/endpoint_coverage.py --missing  # 加明细
    python scripts/endpoint_coverage.py --csv      # 机器可读
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CPP_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(CPP_DIR)

JAVA_CTRL_ROOTS = [
    ("base", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/base"),
    ("common", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/common"),
    ("flow", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow"),
    ("manager", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager"),
    ("monitor", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor"),
    ("system", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/system"),
    ("tool", "ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool"),
    ("quartz", "ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller"),
    ("generator", "ruoyi-generator/src/main/java/com/ruoyi/generator/controller"),
]

VERB_MAP = {"Get": "GET", "Post": "POST", "Put": "PUT", "Delete": "DELETE", "Patch": "PATCH"}
MAPPING_RE = re.compile(
    r'@(Get|Post|Put|Delete|Patch)Mapping(?:\(\s*(?:value\s*=\s*)?"([^"]*)"?)?\)?')
CLASS_RM_RE = re.compile(r'@RequestMapping\("([^"]*)"\)')
PERMI_RE = re.compile(r"@PreAuthorize\(\"@ss\.has(?:Any)?Permi\('([^']+)'\)\"\)")

# C++ 侧：手写路由 + 生成器 spec
CPP_ROUTE_RE = re.compile(r'\br\.(get|post|put|del|patch)\(\s*"([^"]+)"')
LISTV_RE = re.compile(r'registerListVariant\(\s*\w+,\s*"([^"]+)"')
SPEC_RE = re.compile(r'register(?:Crud|ReadOnly)\(\s*\w+,\s*"([^"]+)",\s*s,\s*p,\s*"([^"]+)"\)')


def read(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def normalize(path):
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/+", "/", p)
    p = re.sub(r"\{[^}]*\}", "{*}", p)
    return p


def join_path(base, sub):
    if not sub:
        return normalize(base)
    return normalize(base + "/" + sub.lstrip("/"))


def java_endpoints():
    out = []
    for area, rel in JAVA_CTRL_ROOTS:
        root = os.path.join(REPO, rel)
        if not os.path.isdir(root):
            continue
        # 递归：BigScreenController 在 manager/bigscreen 子目录
        for dirpath, _dirs, fns in os.walk(root):
            for fn in sorted(fns):
                if not fn.endswith("Controller.java"):
                    continue
                src = read(os.path.join(dirpath, fn))
                bm = CLASS_RM_RE.search(src)
                base = bm.group(1) if bm else ""
                ctrl = fn[:-len(".java")]
                lines = src.splitlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    m = MAPPING_RE.match(line) if line.startswith("@") else None
                    if not m:
                        i += 1
                        continue
                    verb = VERB_MAP.get(m.group(1))
                    if verb is None:
                        i += 1
                        continue
                    path = m.group(2) or ""
                    method, perm = "", ""
                    j = i
                    while j < len(lines) and j < i + 14:
                        pm = PERMI_RE.search(lines[j])
                        if pm and not perm:
                            perm = pm.group(1)
                        mm = re.search(r'public\s+[\w<>.,\[\]\s]+\s+(\w+)\s*\(', lines[j])
                        if mm:
                            method = mm.group(1)
                            break
                        j += 1
                    out.append({"area": area, "controller": ctrl, "method": method,
                                "http": verb, "path": join_path(base, path), "perm": perm})
                    i += 1
    return out


def cpp_routes():
    routes = set()
    src_root = os.path.join(CPP_DIR, "src", "cm")
    for dirpath, _dirs, fns in os.walk(src_root):
        for fn in fns:
            if not fn.endswith(".cpp"):
                continue
            src = read(os.path.join(dirpath, fn))
            for verb, path in CPP_ROUTE_RE.findall(src):
                v = "DELETE" if verb == "del" else verb.upper()
                routes.add((v, normalize(path)))
            for path in LISTV_RE.findall(src):
                routes.add(("GET", normalize(path)))
            for base, _pk in SPEC_RE.findall(src):
                for v, suffix in (("GET", "/list"), ("GET", "/export"), ("GET", "/{id}"),
                                  ("POST", ""), ("PUT", ""), ("DELETE", "/{id}")):
                    routes.add((v, join_path(base, suffix)))
    return routes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--csv", action="store_true")
    args = ap.parse_args()

    ja = java_endpoints()
    cpp = cpp_routes()
    covered = [e for e in ja if (e["http"], e["path"]) in cpp]
    missing = [e for e in ja if (e["http"], e["path"]) not in cpp]
    print("Java 端点(按注解) = %d   C++ 已注册路由 = %d   已覆盖 = %d   缺失 = %d"
          % (len(ja), len(cpp), len(covered), len(missing)))

    if args.csv:
        import csv
        w = csv.writer(sys.stdout)
        w.writerow(["area", "controller", "java_method", "http", "path", "perm"])
        for e in missing:
            w.writerow([e["area"], e["controller"], e["method"], e["http"], e["path"], e["perm"]])
        return 0

    by_ctrl = {}
    for e in missing:
        by_ctrl.setdefault((e["area"], e["controller"]), []).append(e)
    print("\n== 缺失，按控制器分组 ==")
    for (area, ctrl), items in sorted(by_ctrl.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        shown = " ".join("%s%s" % (i["http"][:3], i["path"]) for i in items[:8])
        print("%-9s %-34s %2d  %s%s" % (area, ctrl, len(items), shown,
                                        " …" if len(items) > 8 else ""))
    if args.missing:
        print("\n== 明细 ==")
        for e in missing:
            print("%-9s %-32s %-26s %-6s %-44s %s" % (e["area"], e["controller"], e["method"],
                                                     e["http"], e["path"], e["perm"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
