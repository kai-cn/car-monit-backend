# -*- coding: utf-8 -*-
"""上传类端点的错误形态对拍：同一段畸形请求发给两端，比 HTTP 状态 + 响应体。

覆盖 /system/user/importData、/manager/carinfo/import、/manager/exceptrecord/import
三条上传链路上的每一类前置失败：不是 multipart、缺 file 段、空文件、
非 zip、OLE2(xls) 改名、合法 zip 但不是 xlsx、后缀不对。
这些用例全部在解析阶段就被拒掉，不会写库，所以可以随便打。

用法: python scripts/parity/compare_upload_errors.py
"""
import io
import json
import os
import re
import struct
import sys
import uuid
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402
from compare_import import build_xlsx, CAR_HEADERS  # noqa: E402

PATHS = ["/system/user/importData", "/manager/carinfo/import", "/manager/exceptrecord/import"]

OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def zip_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return buf.getvalue()


def multipart(content, filename, fields=None, part_name="file", add_file=True):
    b = "----" + uuid.uuid4().hex
    body = b""
    for k, v in (fields or {}).items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode()
    if add_file:
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                 "Content-Type: application/octet-stream\r\n\r\n" % (b, part_name, filename)).encode()
        body += content + b"\r\n"
    body += ("--%s--\r\n" % b).encode()
    return body, "multipart/form-data; boundary=" + b


def raw_post(base, path, token, body, ctype):
    import urllib.request
    req = urllib.request.Request(base + path, data=body, method="POST", headers={
        "Authorization": "Bearer " + token, "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", -1)
        return code, (e.read() if hasattr(e, "read") else str(e).encode())


USER_IMPORT = "/system/user/importData"
USER_HEADERS = ["用户序号", "用户编码", "部门编号", "登录名称", "用户名称", "用户类型", "用户邮箱",
                "手机号码", "用户性别", "帐号状态", "证书Id", "证书实体Id", "业务id", "业务名称",
                "单位名称", "租户单位id", "租户单位名称", "角色编码"]

CASES = [
    {"label": "非 multipart（JSON 体）", "make": lambda: (b"{}", "application/json")},
    {"label": "缺 file 段", "make": lambda: multipart(b"", "parity.xlsx", {"updateSupport": "false"}, add_file=False)},
    {"label": "file 段名字写错", "make": lambda: multipart(b"x", "parity.xlsx", part_name="uploadfile")},
    {"label": "空文件", "make": lambda: multipart(b"", "parity.xlsx")},
    {"label": "不是 zip 的文本", "make": lambda: multipart(b"hello excel", "parity.xlsx")},
    {"label": "OLE2(xls) 改名 .xlsx", "known": "用户端走 WorkbookFactory，POI 报的是 POIFS 头块扇区大小；"
                                               "Go 只有 excelize 的格式错误。两个 manager 端点直接 new XSSFWorkbook，"
                                               "拿到的是 OLE2/HSSF 提示，已一致",
     "make": lambda: multipart(OLE2_MAGIC + b"\x00" * 600, "parity.xlsx")},
    {"label": "合法 zip 非 xlsx", "make": lambda: multipart(zip_bytes({"a.txt": "hi"}), "parity.xlsx")},
    {"label": "缺 [Content_Types].xml 的 xlsx 包",
     "make": lambda: multipart(zip_bytes({"xl/workbook.xml": "<workbook/>"}), "parity.xlsx")},
    {"label": "后缀 .csv + 合法 xlsx",
     "make": lambda: multipart(build_xlsx(CAR_HEADERS, [[""] * len(CAR_HEADERS)]), "parity.csv")},
    {"label": "car 表头 + 0 数据行",
     "make": lambda: multipart(build_xlsx(CAR_HEADERS, []), "parity.xlsx")},
    # 下面几条只对 /system/user/importData 有意义：它不校验模板，标题对不上也照样往下走。
    {"label": "car 表头 + 空行（@Excel 标题全不匹配）", "only": USER_IMPORT,
     "make": lambda: multipart(build_xlsx(CAR_HEADERS, [[""] * len(CAR_HEADERS)]), "parity.xlsx")},
    {"label": "user 表头 + 0 数据行", "only": USER_IMPORT,
     "make": lambda: multipart(build_xlsx(USER_HEADERS, []), "parity.xlsx")},
    {"label": "user 表头 + 空行", "only": USER_IMPORT,
     "known": "Java 会真的插一次并把 MyBatis 异常文本拼进逐行消息，Go 跳过全空行",
     "make": lambda: multipart(build_xlsx(USER_HEADERS, [[""] * len(USER_HEADERS)]), "parity.xlsx")},
]


def shape(raw):
    """把响应体压成可比较的形态：只留结构，不留 Java 异常里的路径/时间。"""
    try:
        obj = json.loads(raw)
    except Exception:  # noqa: BLE001
        text = re.sub(r"\s+", " ", raw.decode("utf-8", "ignore"))
        return {"__nonjson__": re.sub(r"\d+", "<N>", text)[:160]}
    if isinstance(obj, dict):
        out = {}
        for key in ("code", "msg", "data"):
            if key not in obj:
                continue
            val = obj[key]
            if isinstance(val, str):
                val = re.sub(r"jar:file:/[^\s]*", "<JAR>", val)
                val = re.sub(r"[\w./\\-]*\.jar", "<JAR>", val)
                val = re.sub(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", "<DT>", val)
                val = re.sub(r"line \d+", "line <N>", val)
                val = re.sub(r"\d+", "<N>", val)
            out[key] = val
        return out
    return {"__shape__": type(obj).__name__}


def main():
    tk_j, tk_g = pp.login_java(), pp.login_go()
    problems = []
    for path in PATHS:
        print("\n== %s" % path)
        for case in CASES:
            if case.get("only") and case["only"] != path:
                continue
            row = []
            for base, tk in ((pp.JAVA, tk_j), (pp.GO, tk_g)):
                body, ctype = case["make"]()
                status, raw = raw_post(base, path, tk, body, ctype)
                row.append((status, shape(raw)))
            same = row[0] == row[1]
            print("  %-34s %s" % (case["label"], "一致" if same else "不一致"))
            if same:
                continue
            if case.get("known"):
                print("      已知差异：%s" % case["known"])
                print("      JAVA", json.dumps(row[0], ensure_ascii=False)[:200])
                print("      GO  ", json.dumps(row[1], ensure_ascii=False)[:200])
                continue
            print("      JAVA", json.dumps(row[0], ensure_ascii=False)[:230])
            print("      GO  ", json.dumps(row[1], ensure_ascii=False)[:230])
            problems.append((path, case["label"]))
    print("\n== 上传错误形态：不一致 %d 项 ==" % len(problems))
    for p in problems:
        print("  ", p[0], p[1])


if __name__ == "__main__":
    main()
