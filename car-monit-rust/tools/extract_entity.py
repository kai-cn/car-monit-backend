#!/usr/bin/env python3
"""输出实体的 @Excel 字段顺序与配置，供 export 移植。"""
import re
import sys

src = open(sys.argv[1], encoding="utf-8").read()
for match in re.finditer(r"((?:\s*/\*\*.*?\*/\s*)?)((?:\s*@[A-Za-z]+(?:\([^)]*\))?\s*)*)private\s+([A-Za-z0-9_<>\[\]]+)\s+([A-Za-z0-9_]+)\s*;", src, re.S):
    comment, annos, typ, name = match.groups()
    excel = re.search(r"@Excel\((.*?)\)", annos, re.S)
    if not excel:
        continue
    args = " ".join(excel.group(1).split())
    doc = re.sub(r"[/*\n ]+", " ", comment).strip()[:40]
    print("- %s : %s | %s | %s" % (name, typ, args, doc))
