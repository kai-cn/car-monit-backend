#!/usr/bin/env python3
"""生成 Java↔C++ 端点覆盖清单。

用法（在 car-monit-cpp 目录）:
    python3 scripts/gen_inventory.py

输出: ENDPOINTS_INVENTORY.md
"""
import os
import re
import sys

CPP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_ROOT = os.path.dirname(CPP_ROOT)
JAVA_CTRL = os.path.join(JAVA_ROOT, "ruoyi-admin/src/main/java/com/ruoyi/web/controller")


def java_endpoints():
    out = []
    for root, _, files in os.walk(JAVA_CTRL):
        for f in sorted(files):
            if not f.endswith("Controller.java"):
                continue
            path = os.path.join(root, f)
            src = open(path, encoding="utf-8", errors="replace").read()
            m = re.search(r"public class (\w+)", src)
            cname = m.group(1) if m else f[:-5]
            cm = re.search(
                r'@RequestMapping\(\s*(?:value\s*=\s*)?"([^"]*)"', src[: src.find("public class")]
            )
            prefix = cm.group(1) if cm else ""
            for mm in re.finditer(
                r"\n\s*public\s+(?:static\s+)?[\w<>\[\],\.\?\s]+\s+(\w+)\s*\([^)]*\)\s*"
                r"(?:throws [\w,\s\.]+)?\s*\{",
                src,
            ):
                name = mm.group(1)
                before = src[max(0, mm.start() - 700) : mm.start()]
                cut = max(before.rfind(";"), before.rfind("}"))
                block = before[cut + 1 :]
                mp = re.search(
                    r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*'
                    r'(?:\(\s*(?:value\s*=\s*)?"([^"]*)"[^)]*\)|\(\s*\))?',
                    block,
                )
                if not mp:
                    continue
                kind, sub = mp.group(1), mp.group(2) or ""
                perm = re.search(r"@ss\.hasPermi\('([^']+)'\)", block)
                anyperm = re.search(r"@ss\.hasAnyPermi\('([^']+)'\)", block)
                role = re.search(r"@ss\.hasRole\('([^']+)'\)", block)
                method = {
                    "Get": "GET",
                    "Post": "POST",
                    "Put": "PUT",
                    "Delete": "DELETE",
                    "Patch": "PATCH",
                    "Request": "ANY",
                }[kind]
                if sub:
                    full = "/" + prefix.strip("/") + "/" + sub.lstrip("/") if prefix.strip("/") else "/" + sub.lstrip("/")
                    full = re.sub(r"/+", "/", full)
                else:
                    full = "/" + prefix.strip("/") if prefix.strip("/") else "/"
                auth = ""
                if perm:
                    auth = perm.group(1)
                elif anyperm:
                    auth = "ANY:" + anyperm.group(1)
                elif role:
                    auth = "ROLE:" + role.group(1)
                out.append((cname, method, full, name, auth))
    return out


CPP_MAP = {"get": "GET", "post": "POST", "put": "PUT", "del": "DELETE", "patch": "PATCH", "add": "ANY"}


def cpp_endpoints():
    found = set()
    src_root = os.path.join(CPP_ROOT, "src", "cm")
    for root, _, files in os.walk(src_root):
        for f in files:
            if not f.endswith(".cpp"):
                continue
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            for m in re.finditer(
                r"\.(get|post|put|del|patch|add)\s*\(\s*\"([^\"]+)\"", text
            ):
                found.add((CPP_MAP[m.group(1)], normalize(m.group(2))))
    # 框架内硬编码路由
    for p, meth in [("/logout", "POST"), ("/health", "GET")]:
        found.add((meth, p))
    return found


def normalize(path):
    path = re.sub(r"\{[^}]*\}", "{}", path)
    return re.sub(r"/+", "/", path).rstrip("/") or "/"


def main():
    java = java_endpoints()
    cpp = cpp_endpoints()
    cpp_norm = {(m, normalize(p)) for (m, p) in cpp}
    rows = []
    ok = 0
    for cname, method, path, name, auth in java:
        hit = (method, normalize(path)) in cpp_norm
        if method == "ANY":
            hit = any((mm, normalize(path)) in cpp_norm for mm in ("GET", "POST", "PUT", "DELETE", "PATCH"))
        if hit:
            ok += 1
        rows.append((cname, method, path, name, auth, "✅" if hit else "❌"))

    lines = [
        "# 端点清单与迁移覆盖（由 scripts/gen_inventory.py 自动生成）",
        "",
        f"Java 控制器方法总数：**{len(java)}**；已注册：**{ok}**；未注册：**{len(java) - ok}**。",
        "",
        "| 控制器 | 方法 | 路径 | Java 方法 | @PreAuthorize | C++ 状态 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| {} | {} | `{}` | {} | {} | {} |".format(*r))
    out = os.path.join(CPP_ROOT, "ENDPOINTS_INVENTORY.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out}: {ok}/{len(java)} migrated")


if __name__ == "__main__":
    sys.exit(main())
