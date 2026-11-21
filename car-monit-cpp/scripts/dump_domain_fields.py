#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按声明顺序打印 Java 实体的字段（名字/类型/初始值），用于手写响应结构时对齐 JSON 键集。

生成器解析的是"实体 + 表列"的 spec；但有些响应对象根本不落库
（TrailInfo / TrailBo / TrailDevCountBO 这类 VO），它们的 JSON 键集只能照抄字段声明。
这里复用 scripts/gen_crud_spec.py 里那份已经调好的字段正则，避免手抄漏字段。

用法：python scripts/dump_domain_fields.py TrailInfo TrailBo ...
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA = os.path.dirname(ROOT)


def find_class(name):
    for base in ("ruoyi-system", "ruoyi-admin", "ruoyi-common", "ruoyi-framework"):
        d = os.path.join(JAVA, base, "src", "main", "java")
        if not os.path.isdir(d):
            continue
        for dirpath, _dirs, files in os.walk(d):
            if name + ".java" in files:
                return os.path.join(dirpath, name + ".java")
    return None


FIELD = re.compile(r'private\s+((?:[A-Za-z0-9_.]+)(?:<[^;>]*>)?)\s+(\w+)\s*(?:=\s*([^;]+))?;', re.S)


def main():
    for name in sys.argv[1:]:
        p = find_class(name)
        if not p:
            print("!! 找不到 %s" % name)
            continue
        src = io.open(p, encoding="utf-8", errors="replace").read()
        cls = re.search(r'(?:public\s+)?class\s+%s(\s+extends\s+\w+)?' % name, src)
        print("==== %s%s" % (name, cls.group(1) or "" if cls else ""))
        for m in FIELD.finditer(src):
            typ, field, dflt = m.group(1), m.group(2), (m.group(3) or "").strip()
            print("   %-28s %-22s %s" % (typ, field, ("= " + dflt) if dflt else ""))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
