#!/usr/bin/env python3

"""
@description 历史脚本 gen_full_endpoints.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python gen_full_endpoints.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

