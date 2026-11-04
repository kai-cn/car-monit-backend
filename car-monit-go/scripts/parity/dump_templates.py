# -*- coding: utf-8 -*-
"""导出模板真值打印：把 Java 侧 templates/export/*.xlsx 的表头行与 $fe 字段引用列出来。

这些模板是 EasyPOI 导出的列真值（不是实体上的 @Excel 注解），Go 侧的 exportCol
清单必须逐字对齐。表头行 = 第一行非空单元格；$fe 行 = 含「{{$fe:」的那一行。

用法:
  python scripts/parity/dump_templates.py [名字关键字 ...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_xlsx import shared_strings, parse_sheet  # noqa: E402
import zipfile  # noqa: E402

TPL = os.environ.get("JAVA_TPL",
                     r"D:\work\IdeaProjects\car-monit-backend-new\ruoyi-admin\src\main\resources\templates\export")
FE_RE = re.compile(r"\{\{\$fe:\s*(\w+)\s+(.*?)\}\}", re.S)


def rows_of(path):
    zf = zipfile.ZipFile(path)
    sst = shared_strings(zf)
    names = sorted(n for n in zf.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    if not names:
        return []
    cells, dims, grid = parse_sheet(zf, names[0], sst)
    return grid


def main():
    keys = [k.lower() for k in sys.argv[1:]]
    for name in sorted(os.listdir(TPL)):
        if not name.endswith(".xlsx"):
            continue
        if keys and not any(k in name.lower() for k in keys):
            continue
        grid = rows_of(os.path.join(TPL, name))
        print("== %s  (%d行)" % (name, len(grid)))
        for i, row in enumerate(grid[:4], 1):
            joined = "|".join(str(c) for c in row)
            m = FE_RE.search(joined)
            if m:
                print("   r%d $fe(%s): %s" % (i, m.group(1), m.group(2)))
            else:
                print("   r%d %s" % (i, [c for c in row if c != ""]))


if __name__ == "__main__":
    main()
