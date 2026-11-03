#!/usr/bin/env python3
"""生成 Java↔C++ 端点覆盖清单（ENDPOINTS_INVENTORY.md）。

用法（在 car-monit-cpp 目录）:
    python scripts/gen_inventory.py

计数口径一律走 scripts/endpoint_coverage.py：它遍历 ruoyi-admin / ruoyi-quartz /
ruoyi-generator 三个模块的全部 *Controller.java，按 @GetMapping/@PostMapping/...
注解逐条统计（真实分母 497）。本脚本以前只扫 ruoyi-admin 一个目录，分母停在 326 ——
那就是文档里那个失真数字的来源，不要再在这里自己数第二遍。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import endpoint_coverage as cov  # noqa: E402

CPP_ROOT = os.path.dirname(HERE)


def main():
    java = cov.java_endpoints()
    cpp = cov.cpp_routes()

    rows, ok = [], 0
    for e in java:
        hit = (e["http"], e["path"]) in cpp
        if hit:
            ok += 1
        rows.append((e["controller"], e["http"], e["path"], e["method"], e["perm"],
                     "✅" if hit else "❌"))

    lines = [
        "# 端点清单与迁移覆盖（由 scripts/gen_inventory.py 自动生成）",
        "",
        "口径：Java 侧按 @*Mapping 注解逐条统计，覆盖 ruoyi-admin / ruoyi-quartz / ruoyi-generator。",
        "",
        "Java 端点总数：**%d**；C++ 已注册并匹配：**%d**；未匹配：**%d**。" % (len(java), ok, len(java) - ok),
        "",
        "C++ 已注册路由（源码枚举，含少量 Java 没有的框架扩展路由，如 /health）：**%d**。" % len(cpp),
        "",
        "| 控制器 | HTTP | 路径 | Java 方法 | @PreAuthorize | C++ 状态 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| {} | {} | `{}` | {} | {} | {} |".format(*r))
    out = os.path.join(CPP_ROOT, "ENDPOINTS_INVENTORY.md")
    with io.open(out, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s: %d/%d migrated (C++ 路由 %d)" % (out, ok, len(java), len(cpp)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
