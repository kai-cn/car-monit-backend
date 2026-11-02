# -*- coding: utf-8 -*-
"""双端路由清单比对：Java 控制器注解扫描 vs Go 运行时 GIN 注册表。

Java 侧从源码扫描（含 @GetMapping(value={"/","/{id}"}) 这类多路径写法），
Go 侧从启动日志的 [GIN-debug] 行读取实际注册结果 —— 运行态才算数。
路径占位符统一成 :x，并去掉末尾斜杠（Spring 的 useTrailingSlashMatch 让
/system/user/ 与 /system/user 等价，Gin 需要显式注册两条）。

用法: python scripts/parity/routes.py [--log <carmonit.log>] [--out <json>]
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
JAVA_ROOT = os.path.dirname(REPO)
MODULES = ["ruoyi-admin", "ruoyi-system", "ruoyi-quartz", "ruoyi-generator",
           "ruoyi-framework", "ruoyi-common"]
METHOD_ANN = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
              "DeleteMapping": "DELETE", "PatchMapping": "PATCH"}
STRING_RE = re.compile(r'"([^"]*)"')
CLASS_MAP_RE = re.compile(r"@RequestMapping\s*\(([^)]*)\)")
ANN_RE = re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(\((?:[^()]|\([^()]*\))*\))?")
REQUEST_METHOD_RE = re.compile(r"RequestMethod\.(\w+)")
GIN_RE = re.compile(r"\[GIN-debug\]\s+(POST|GET|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\S+)\s+-->")

# Spring Security 直接注册的端点（不是控制器注解，扫描不到）
EXTRA_JAVA = {("POST", "/logout")}


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("//") or s.startswith("*"):
            continue
        lines.append(re.sub(r"//.*$", "", line))
    return "\n".join(lines)


def norm(path):
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    path = re.sub(r"\{[^}]*\}", ":x", path)
    path = re.sub(r":[A-Za-z_]\w*", ":x", path)
    path = re.sub(r"\*[A-Za-z_]\w*", ":x", path)
    path = re.sub(r"/{2,}", "/", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path or "/"


def top_level_group(args):
    start = args.find("{")
    if start < 0:
        return ""
    depth = 0
    for i in range(start, len(args)):
        if args[i] == "{":
            depth += 1
        elif args[i] == "}":
            depth -= 1
            if depth == 0:
                return args[start + 1:i]
    return args[start + 1:]


def paths_of(args):
    if not args:
        return [""]
    inner = top_level_group(args)
    if inner and "RequestMethod." not in inner:
        found = STRING_RE.findall(inner)
        if found:
            return found
    found = STRING_RE.findall(args)
    return found[:1] if found else [""]


def scan_java():
    routes, controllers = set(), 0
    for module in MODULES:
        base = os.path.join(JAVA_ROOT, module, "src", "main", "java")
        if not os.path.isdir(base):
            continue
        for root, _, names in os.walk(base):
            for name in names:
                if not name.endswith(".java"):
                    continue
                raw = open(os.path.join(root, name), encoding="utf-8", errors="ignore").read()
                if "@RestController" not in raw and "@Controller" not in raw:
                    continue
                controllers += 1
                text = strip_comments(raw)
                head = text.split("public class", 1)[0] if "public class" in text else text
                class_paths = [""]
                cm = CLASS_MAP_RE.search(head)
                if cm:
                    class_paths = paths_of(cm.group(1)) or [""]
                for m in ANN_RE.finditer(text[len(head):]):
                    ann, args = m.group(1), (m.group(2) or "")[1:-1]
                    methods = REQUEST_METHOD_RE.findall(args) if ann == "RequestMapping" else None
                    methods = methods or ([METHOD_ANN[ann]] if ann != "RequestMapping"
                                          else ["GET", "POST", "PUT", "DELETE", "PATCH"])
                    for cp in class_paths:
                        for mp in paths_of(args) or [""]:
                            for verb in methods:
                                routes.add((verb, norm(cp + "/" + mp)))
    routes |= EXTRA_JAVA
    print("Java 控制器 %d 个，路由 %d 条" % (controllers, len(routes)))
    return routes


def scan_go(log_path):
    text = open(log_path, encoding="utf-8", errors="ignore").read()
    routes = {(m.group(1), norm(m.group(2))) for m in GIN_RE.finditer(text)
              if not m.group(2).startswith("http")}
    print("Go 注册路由 %d 条" % len(routes))
    return routes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=os.path.join(os.environ.get("TEMP", "/tmp"), "carmonit.log"))
    ap.add_argument("--out", default=os.path.join(HERE, "routes_compare.json"))
    args = ap.parse_args()
    j, g = scan_java(), scan_go(args.log)
    only_java, only_go = sorted(j - g), sorted(g - j)
    print("\n匹配 %d 条 | Java 有 Go 没有 %d 条 | Go 有 Java 没有 %d 条" % (len(j & g), len(only_java), len(only_go)))
    print("\n== Java 有 / Go 没有 ==")
    for verb, path in only_java:
        print("   %-7s %s" % (verb, path))
    print("\n== Go 有 / Java 没有 ==")
    for verb, path in only_go:
        print("   %-7s %s" % (verb, path))
    json.dump({"java": sorted(j), "go": sorted(g), "only_java": only_java, "only_go": only_go},
              open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n报告:", args.out)


if __name__ == "__main__":
    main()
