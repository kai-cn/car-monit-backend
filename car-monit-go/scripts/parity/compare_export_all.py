# -*- coding: utf-8 -*-
"""所有导出/导入模板路由的单元格级双端对比（含 ExcelUtil 落盘型导出）。

compare_get.py 对附件流只能标成 non-json；ExcelUtil 型导出（返回
{msg:"<uuid>_xx.xlsx"}、文件落在 profile/download）连附件都看不到。
本脚本把三类一起覆盖：
  * 响应是 xlsx 字节（EasyPOI 附件流）  -> 直接逐格对比
  * 响应是 JSON 且 msg 以 .xlsx 结尾    -> 读两端落盘文件逐格对比，并把这两个文件删掉
  * importTemplate（导入模板，同为 ExcelUtil 落盘型）也纳入口径

用法:
  python scripts/parity/compare_export_all.py [--log 启动日志] [--out report.json] [--only 前缀]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402
import compare_xlsx as cx  # noqa: E402
from routes import GIN_RE, norm  # noqa: E402

DOWNLOAD_DIR = os.environ.get(
    "PARITY_DOWNLOAD_DIR", "D:/ruoyi/uploadPath/download").replace("\\", "/")


def export_routes(log_path, only=""):
    text = open(log_path, encoding="utf-8", errors="ignore").read()
    out = []
    for m in GIN_RE.finditer(text):
        if m.group(1) != "GET" or m.group(2).startswith("http"):
            continue
        path = norm(m.group(2))
        if not re.search(r"export|import", path.lower()):
            continue
        if only and not path.startswith(only):
            continue
        if path not in out:
            out.append(path)
    return out


def resolve_written(msg):
    """ExcelUtil 的返回值 -> 本次调用生成的落盘文件绝对路径（越界的一律拒绝）。"""
    if not isinstance(msg, str) or not msg.lower().endswith(".xlsx"):
        return ""
    base = os.path.basename(msg)
    if base != msg or ".." in base:
        return ""
    full = (DOWNLOAD_DIR + "/" + base).replace("\\", "/")
    return full if os.path.isfile(full) else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=os.path.join(os.environ.get("TEMP", "/tmp"), "go-ref-9984.log"))
    ap.add_argument("--out", default="")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    tk_j, tk_g = pp.login_java(), pp.login_go()
    routes = export_routes(args.log, args.only)
    print("导出路由 %d 条，落盘目录 %s" % (len(routes), DOWNLOAD_DIR))

    results, total_bad, files_left = [], 0, 0
    for path in routes:
        url = path + ("?pageNum=1&pageSize=30" if "?" not in path else "")
        sj, bj, _ = pp.call(pp.JAVA, url, tk_j)
        sg, bg, _ = pp.call(pp.GO, url, tk_g)
        entry = {"p": url, "java": sj, "go": sg, "kind": "", "bad": 0, "note": ""}
        print("\n== %s  Java=%d/%dB  Go=%d/%dB" % (url, sj, len(bj), sg, len(bg)))

        if bj.startswith(b"PK") and bg.startswith(b"PK"):
            entry["kind"] = "attachment"
            entry["bad"] = cx.compare_cells(bj, bg)
        else:
            try:
                mj = json.loads(bj).get("msg")
                mg = json.loads(bg).get("msg")
            except Exception:
                mj = mg = None
            fj, fg = resolve_written(mj), resolve_written(mg)
            if not fj or not fg:
                entry["kind"] = "non-xlsx"
                entry["note"] = "Java=%r Go=%r 文件=%r/%r" % (
                    str(mj)[:60], str(mg)[:60], bool(fj), bool(fg))
                print("   非 xlsx 附件也非 ExcelUtil 落盘：%s" % entry["note"])
            else:
                entry["kind"] = "excelutil"
                entry["note"] = "java文件=%s go文件=%s" % (os.path.basename(fj), os.path.basename(fg))
                bad = cx.compare_cells(open(fj, "rb").read(), open(fg, "rb").read())
                entry["bad"] = bad
                for f in (fj, fg):        # 只删本次调用生成的那两个文件
                    try:
                        os.remove(f)
                    except OSError as e:
                        files_left += 1
                        print("   删除失败 %s: %s" % (f, e))
        total_bad += entry["bad"]
        results.append(entry)

    kinds = {}
    for r in results:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("\n== 汇总：端点 %d 条，形态 %s，单元格差异合计 %d，未能删除的临时文件 %d" % (
        len(results), kinds, total_bad, files_left))
    for r in results:
        if r["bad"] or r["kind"] == "non-xlsx":
            print("   %-46s %-10s 差异格=%-6d %s" % (r["p"], r["kind"], r["bad"], r["note"][:90]))
    if args.out:
        json.dump({"total": len(results), "kinds": kinds, "bad": total_bad,
                   "entries": results},
                  open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("报告:", args.out)


if __name__ == "__main__":
    main()
