#!/usr/bin/env python3

"""
@description 历史脚本 extract_backend_endpoints.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python extract_backend_endpoints.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# 从 Java V3 分支源码提取 @RestController 的全量端点（方法级注解）。

# 输出：TSV 文件 <verb>\t<path>\t<auth?>，供云 runner workflow 生成探针清单。

import os

import re

import subprocess

import sys



REPO = os.environ.get("JAVA_V3_REPO", r"d:\work\IdeaProjects\car-monit-backend-java-V3")

OUT = sys.argv[1] if len(sys.argv) > 1 else r"d:\work\runtime-logs\backend-v3-endpoints.tsv"





def git(*args):

    return subprocess.run(["git", "-C", REPO] + list(args),

                          capture_output=True, text=True, errors="replace").stdout





files = [f for f in git("ls-tree", "-r", "--name-only", "HEAD").splitlines()

         if f.endswith("Controller.java")]

rows = []

for f in files:

    src = git("show", "HEAD:" + f)

    # 只处理带 @RestController 的类；@Controller（视图）不在 API 对拍范围

    if "@RestController" not in src and "@Controller" not in src:

        continue

    base = re.search(r'@RequestMapping\(\s*(?:value\s*=\s*)?"([^"]+)"', src)

    bp = base.group(1) if base else ""

    # 类级 @PreAuthorize / 方法级 @PreAuthorize

    class_auth = bool(re.search(r"@PreAuthorize|@RequiresPermissions|@RequiresLogin", src))

    for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping\s*(?:\(([^)]*)\))?', src):

        verb = m.group(1).upper()

        args = m.group(2) or ""

        pm = re.search(r'(?:value|path)\s*=\s*\{?\s*"([^"]*)"', args)

        if pm:

            sub = pm.group(1)

        elif '"' in args:

            sub = re.search(r'"([^"]*)"', args).group(1)

        else:

            sub = ""

        path = (bp.rstrip("/") + "/" + sub.lstrip("/")) if (bp or sub) else "/"

        path = path.replace("//", "/")

        if not path.startswith("/"):

            path = "/" + path

        rows.append((verb, path, "auth" if class_auth else "public", f))



seen = set()

uniq = []

for r in rows:

    k = (r[0], r[1])

    if k not in seen:

        seen.add(k)

        uniq.append(r)



with open(OUT, "w", encoding="utf-8") as fh:

    for verb, path, auth, f in uniq:

        fh.write("%s\t%s\t%s\t%s\n" % (verb, path, auth, f.split("/")[-1]))

print("controllers=%d endpoints=%d out=%s" % (len(files), len(uniq), OUT))

