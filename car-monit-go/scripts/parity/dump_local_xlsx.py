#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印本地 xlsx 的每一行单元格（含空列位置），用来核对导入模板的表头。

用法: python scripts/parity/dump_local_xlsx.py <a.xlsx> [起始行] [结束行]
"""
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import compare_xlsx as cx


def main():
    path = sys.argv[1]
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else lo + 5
    with open(path, "rb") as fh:
        sheets = cx.parse(fh.read())
    for name, (_cells, _dims, grid) in sorted(sheets.items()):
        print("== %s  共 %d 行" % (name, len(grid)))
        for i, row in enumerate(grid):
            if i < lo:
                continue
            if i >= hi:
                break
            print("  行%d(%d列): %s" % (i, len(row), " | ".join(
                "%d=%s" % (j, v if v != "" else "·") for j, v in enumerate(row))))


if __name__ == "__main__":
    main()
