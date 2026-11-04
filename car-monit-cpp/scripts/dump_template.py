#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印 easypoi 模板 xlsx 的标记行：表头 + {{$fe:xxx t.a | t.b}} 的字段顺序。

模板导出类接口（exportConcernedList / exportHistory / …）的列与顺序完全由这份
模板决定，Java 用 ExcelExportUtil 现场解析；C++ 侧目前把表头与字段写成常量表，
所以每次落地一个模板端点都要先看清模板里到底是什么。

用法：
    python scripts/dump_template.py ruoyi-admin/src/main/resources/templates/export/carSuspicious.xlsx
    python scripts/dump_template.py --all
"""
import io
import os
import re
import sys
import zipfile

JAVA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TPL_DIR = os.path.join(JAVA, "ruoyi-admin", "src", "main", "resources", "templates", "export")


def shared(z):
    try:
        raw = z.read("xl/sharedStrings.xml").decode("utf-8")
    except KeyError:
        return []
    out = []
    for si in re.findall(r"<si>(.*?)</si>", raw, re.S):
        out.append("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
    return out


def rows(z, strings):
    try:
        sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    except KeyError:
        return []
    out = []
    for r in re.findall(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', sheet, re.S):
        cells = []
        for c in re.findall(r"<c\b([^>]*)>(.*?)</c>", r[1], re.S):
            ref = re.search(r'r="([A-Z]+)\d+"', c[0])
            t = re.search(r't="s"', c[0])
            v = re.search(r"<v>(.*?)</v>", c[1], re.S)
            istr = re.search(r"<t[^>]*>(.*?)</t>", c[1], re.S)
            val = ""
            if v:
                val = strings[int(v.group(1))] if t and v.group(1).isdigit() else v.group(1)
            elif istr:
                val = istr.group(1)
            cells.append((ref.group(1) if ref else "?", val))
        out.append((int(r[0]), cells))
    return out


def dump(path):
    print("==== %s" % os.path.basename(path))
    with zipfile.ZipFile(path) as z:
        strings = shared(z)
        for num, cells in rows(z, strings):
            print("  row%-3d %s" % (num, " | ".join("%s=%s" % (col, val) for col, val in cells)))


def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        for f in sorted(os.listdir(TPL_DIR)):
            if f.endswith(".xlsx"):
                dump(os.path.join(TPL_DIR, f))
        return
    for a in args:
        p = a if os.path.exists(a) else os.path.join(TPL_DIR, a)
        dump(p)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
