"""Throwaway: compare the *cell values* of an exported xlsx on both backends.

The two writers (EasyExcel/POI vs openpyxl) never produce identical bytes, so the only
meaningful check is "same sheet name + same cell values".
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import httpx
from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

paths = sys.argv[1:] or [
    "/manager/aduitfree/exportIncomeStatics",
    "/manager/aduitfree/exportIncomeDetailList",
    "/manager/confimfree/exportCarStatics",
    "/manager/confimfree/exportConcernedList",
    "/manager/exceptrecord/exportOrgId",
    "/manager/suspicious/exportHistory",
]
tokens = json.loads(Path(".sweep_tokens.json").read_text(encoding="utf-8"))


def cells(body: bytes) -> tuple:
    book = load_workbook(io.BytesIO(body), data_only=True)
    sheets = []
    for sheet in book.worksheets:
        rows = [
            ["" if cell is None else str(cell) for cell in row]
            for row in sheet.iter_rows(values_only=False)
        ]
        sheets.append((sheet.title, rows))
    return tuple(sheets)


for path in paths:
    bodies = {}
    for name, base in (("java", "http://127.0.0.1:8090"), ("python", "http://127.0.0.1:9989")):
        response = httpx.get(
            base + path,
            headers={"Authorization": "Bearer " + tokens[name]},
            timeout=180,
        )
        bodies[name] = response.content
    left, right = cells(bodies["java"]), cells(bodies["python"])
    if left == right:
        print("SAME-CELLS  %-48s bytes %d vs %d" % (path, len(bodies["java"]), len(bodies["python"])))
        continue
    print("DIFF-CELLS  %s" % path)
    print("  sheets: %s vs %s" % ([s[0] for s in left], [s[0] for s in right]))
    for index, (a, b) in enumerate(zip(left, right)):
        if a == b:
            continue
        print("  sheet[%d] %r: rows %d vs %d" % (index, a[0], len(a[1]), len(b[1])))
        for row_index, (row_a, row_b) in enumerate(zip(a[1], b[1])):
            if row_a != row_b:
                print("    row %d java=%r" % (row_index, row_a))
                print("    row %d py  =%r" % (row_index, row_b))
