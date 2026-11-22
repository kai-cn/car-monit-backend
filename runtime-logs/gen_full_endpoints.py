#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：gen_full_endpoints.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
# 从 515 端点 TSV 生成可在云 runner 直接探测的 GET 清单（路径变量替换为样例值）。
import re
import sys

src = sys.argv[1] if len(sys.argv) > 1 else r"d:\work\runtime-logs\backend-v3-endpoints.tsv"
out = sys.argv[2] if len(sys.argv) > 2 else r"d:\work\runtime-logs\backend-v3-get-full.txt"

rows = []
for line in open(src, encoding="utf-8"):
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 2:
        continue
    verb, path = parts[0], parts[1]
    if verb != "GET":
        continue
    # 路径变量：id/ids/code 等统一给 1；保持路径层级
    concrete = re.sub(r"\{[^}]+\}", "1", path)
    rows.append(concrete)

# 去重保序
seen, uniq = set(), []
for p in rows:
    if p not in seen:
        seen.add(p)
        uniq.append(p)

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(uniq) + "\n")
print("GET endpoints (concrete, unique):", len(uniq), "->", out)
