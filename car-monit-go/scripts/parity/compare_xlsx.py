# -*- coding: utf-8 -*-
"""导出接口（xlsx 二进制）双端逐格对比。

compare_get.py 只能把 xlsx 标成 non-json（长度必然不同：POI/excelize 写出的
zip 里带创建时间与样式，字节数不构成证据），这里落到单元格值：
zip -> xl/worksheets/*.xml + xl/sharedStrings.xml -> {(sheet, ref): 值}。

用法:
  python scripts/parity/compare_xlsx.py "/base/feerecords/export?pageNum=1&pageSize=3" ...
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def fetch(base, path, token):
    req = urllib.request.Request(base + path, headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall(NS + "si"):
        out.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return out


def sheet_cells(zf, name, sst):
    root = ET.fromstring(zf.read(name))
    cells, dims = {}, [0, 0]
    for row in root.iter(NS + "row"):
        for c in row.findall(NS + "c"):
            ref = c.get("r") or ""
            col_letters = re.match(r"([A-Z]+)(\d+)", ref)
            if not col_letters:
                continue
            letters, rowno = col_letters.group(1), int(col_letters.group(2))
            cidx = 0
            for ch in letters:
                cidx = cidx * 26 + (ord(ch) - 64)
            dims[0] = max(dims[0], cidx)
            dims[1] = max(dims[1], rowno)
            kind = c.get("t") or ""
            v = c.find(NS + "v")
            isel = c.find(NS + "is")
            if kind == "s" and v is not None:
                val = sst[int(v.text or "0")]
            elif kind == "inlineStr" and isel is not None:
                val = "".join(t.text or "" for t in isel.iter(NS + "t"))
            elif v is not None:
                val = v.text or ""
            else:
                continue
            if kind == "b":
                val = "TRUE" if val == "1" else "FALSE"
            cells[(rowno, cidx)] = norm_num(val)
    return cells, dims


def norm_num(val):
    """1.0 -> 1：POI 写浮点、excelize 写整数的常见形态差。"""
    if re.fullmatch(r"-?\d+\.0+", val):
        return val.split(".")[0]
    return val


def grid(cells, dims):
    rows, cols = dims[1], dims[0]
    return [[cells.get((r, c), "") for c in range(1, cols + 1)] for r in range(1, rows + 1)]


def parse(data):
    zf = zipfile.ZipFile(io.BytesIO(data))
    sst = shared_strings(zf)
    names = sorted(n for n in zf.namelist()
                   if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    out = {}
    for n in names:
        out[n.split("/")[-1]] = parse_sheet(zf, n, sst)
    return out


def parse_sheet(zf, name, sst):
    cells, dims = sheet_cells(zf, name, sst)
    return cells, dims, grid(cells, dims)


def col_name(idx):
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def trim(grid):
    """去掉尾部整列/整行为空的占位：POI 会多写一列空样式列，excelize 不写。

    只裁两端都为空的边缘，带值的列不会被裁掉，因此不会掩盖真实差异。
    """
    g = [list(row) for row in grid]
    while g and all(c == "" for c in g[-1]):
        g.pop()
    if not g:
        return g
    width = max(len(r) for r in g)
    while width > 1 and all(row[width - 1] == "" for row in g if len(row) >= width):
        width -= 1
    return [row[:width] + [""] * (width - len(row)) for row in g]


def main():
    tk_j, tk_g = pp.login_java(), pp.login_go()
    for path in sys.argv[1:]:
        sj, bj = fetch(pp.JAVA, path, tk_j)
        sg, bg = fetch(pp.GO, path, tk_g)
        print("\n== %s  Java=%d/%dB  Go=%d/%dB" % (path, sj, len(bj), sg, len(bg)))
        if sj != sg:
            print("   状态码不一致")
            continue
        if not bj.startswith(b"PK") or not bg.startswith(b"PK"):
            print("   非 xlsx：Java=%r Go=%r" % (bj[:200], bg[:200]))
            continue
        gj, gg = parse(bj), parse(bg)
        if list(gj) != list(gg):
            print("   工作表名不同 Java=%s Go=%s" % (list(gj), list(gg)))
        bad = 0
        for name in sorted(set(gj) | set(gg)):
            if name not in gj or name not in gg:
                print("   %s 只在一端存在" % name)
                continue
            a_all = trim(gj[name][2])
            b_all = trim(gg[name][2])
            print("   %s  原始 Java=%d行×%d列 Go=%d行×%d列  裁边后 Java=%d×%d Go=%d×%d" % (
                name, len(gj[name][2]), gj[name][1][0], len(gg[name][2]), gg[name][1][0],
                len(a_all), len(a_all[0]) if a_all else 0,
                len(b_all), len(b_all[0]) if b_all else 0))
            print("     表头 Java=%s" % json.dumps(a_all[0] if a_all else [], ensure_ascii=False)[:400])
            print("     表头 Go  =%s" % json.dumps(b_all[0] if b_all else [], ensure_ascii=False)[:400])
            width = max([len(r) for r in a_all] + [len(r) for r in b_all] + [0])
            per_col = {}
            for ri in range(max(len(a_all), len(b_all))):
                a = a_all[ri] if ri < len(a_all) else []
                b = b_all[ri] if ri < len(b_all) else []
                for ci in range(width):
                    va = a[ci] if ci < len(a) else ""
                    vb = b[ci] if ci < len(b) else ""
                    if va != vb:
                        bad += 1
                        d = per_col.setdefault(ci, {"n": 0, "s": []})
                        d["n"] += 1
                        if len(d["s"]) < 2:
                            d["s"].append((ri + 1, va, vb))
            for ci in sorted(per_col)[:10]:
                title = a_all[0][ci] if a_all and ci < len(a_all[0]) else "?"
                samples = "; ".join("r%d Java=%r Go=%r" % s for s in per_col[ci]["s"])
                print("     列%s(%s) 差异行=%d  %s" % (col_name(ci + 1), title,
                                                            per_col[ci]["n"], samples[:220]))
        print("   单元格差异合计: %d" % bad)


if __name__ == "__main__":
    main()
