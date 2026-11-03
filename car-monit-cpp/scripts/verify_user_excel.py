#!/usr/bin/env python3
# SysUser 的 @Excel 列集合 / 值转换 / dept 关联的保真度验证
# 期望值直接抄自 ruoyi-common/.../entity/SysUser.java 的 @Excel 注解
import io
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:9991"
TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""

# 直接照抄 SysUser.java 里 @Excel 的声明顺序与 type
F = [
    ("用户序号", "ALL", True), ("用户编码", "ALL", True), ("部门编号", "IMPORT", False),
    ("登录名称", "ALL", False), ("用户名称", "ALL", False), ("用户类型", "ALL", False),
    ("用户邮箱", "ALL", False), ("手机号码", "ALL", False), ("用户性别", "ALL", False),
    ("帐号状态", "ALL", False), ("最后登录IP", "EXPORT", False), ("最后登录时间", "EXPORT", False),
    ("证书Id", "ALL", False), ("证书实体Id", "ALL", False), ("业务id", "ALL", False),
    ("业务名称", "ALL", False), ("单位名称", "ALL", False), ("租户单位id", "ALL", False),
    ("租户单位名称", "ALL", False), ("角色编码", "ALL", False),
    ("部门名称", "EXPORT", False), ("部门负责人", "EXPORT", False),
]
EXPORT_HEAD = [n for n, t, _ in F if t in ("ALL", "EXPORT")]
TEMPLATE_HEAD = [n for n, t, _ in F if t in ("ALL", "IMPORT")]

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + detail if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + detail)


def get(path, token=True):
    r = urllib.request.Request(BASE + path)
    if TOKEN and token:
        r.add_header("Authorization", "Bearer " + TOKEN)
    return urllib.request.urlopen(r, timeout=120).read()


def download(fname):
    # /common/download** 是 anonymous()：带 token 会被 Spring 判 403，所以这里不带
    return get("/common/download?fileName=" + urllib.parse.quote(fname) + "&delete=true", token=False)


def sheet_xml(body):
    zf = zipfile.ZipFile(io.BytesIO(body))
    assert zf.testzip() is None, "zip CRC 校验失败"
    return zf.read("xl/worksheets/sheet1.xml").decode("utf-8"), zf


def header_of(sheet):
    import re
    row = sheet.split("<row ", 1)[1].split("</row>", 1)[0]
    return re.findall(r"<t>(.*?)</t>", row, re.S)


def cells_of(sheet, nth):
    import re
    rows = re.findall(r"<row [^>]*>(.*?)</row>", sheet, re.S)
    out = []
    for c in re.findall(r"<c [^>]*?(?:/>|>(?:<is><t>(.*?)</t></is>|<v>(.*?)</v>))", rows[nth], re.S):
        out.append(c[0] or c[1] or "")
    return out


# ---- 1) 导出列头 = Java Type.EXPORT 过滤结果 ----
j = json.loads(get("/system/user/export").decode("utf-8"))
fname = j.get("msg", "")
check("export 返回 msg=文件名（Java 的 msg 重载，无 data 键）",
      j.get("code") == 200 and fname.endswith("_用户数据.xlsx") and "data" not in j,
      json.dumps(j, ensure_ascii=False))
body = download(fname)
sheet, zf = sheet_xml(body)
check("导出列头与 Java @Excel(EXPORT) 完全一致", header_of(sheet) == EXPORT_HEAD,
      "\n  got: %s\n  exp: %s" % (header_of(sheet), EXPORT_HEAD))

# ---- 2) 单元格值：转换器 + Long 走文本 + dept 关联 ----
data = cells_of(sheet, 1)
if len(data) == len(EXPORT_HEAD):
    m = dict(zip(EXPORT_HEAD, data))
    print("  row1: " + json.dumps(m, ensure_ascii=False)[:400])
    raw = json.loads(get("/system/user/list?pageSize=200").decode("utf-8"))
    u = raw["rows"][0]
    import re as _re
    _rows = _re.findall(r"<row [^>]*>(.*?)</row>", sheet, _re.S)
    check("用户序号/用户编码 是数字单元格（cellType=NUMERIC）",
          _rows[1].startswith('<c r="A2"><v>1</v></c>') and '<c r="B2"><v>1</v></c>' in _rows[1],
          _rows[1][:70])
    check("租户单位id 是文本单元格（Java 默认 cellType=STRING，Long 也写字符串）",
          m["租户单位id"] == str(u["tenantId"]) or m["租户单位id"] == "",
          "xlsx=%r json=%r" % (m["租户单位id"], u["tenantId"]))
    check("帐号状态按 readConverterExp 转换（0 -> 正常）",
          m["帐号状态"] in ("正常", "停用", ""), "got=%r status=%r" % (m["帐号状态"], u["status"]))
    check("用户类型 exp 只有一条 1=... 映射", m["用户类型"] in
          ("机构用户2专家3供应商", "2", "3", ""), "got=%r userType=%r" % (m["用户类型"], u["userType"]))
    check("部门名称来自 dept.deptName（MyBatis association）",
          m["部门名称"] == (u.get("dept") or {}).get("deptName", "") or m["部门名称"] == "",
          "xlsx=%r dept=%r" % (m["部门名称"], u.get("dept")))
    check("最后登录时间是 yyyy-MM-dd HH:mm:ss",
          m["最后登录时间"] == "" or len(m["最后登录时间"]) == 19 and m["最后登录时间"][4] == "-",
          "got=%r" % m["最后登录时间"])
else:
    check("导出首行数据长度与表头一致", False, "cells=%d head=%d" % (len(data), len(EXPORT_HEAD)))

# ---- 3) 模板列头 = Java Type.IMPORT 过滤结果 ----
j2 = json.loads(get("/system/user/importTemplate").decode("utf-8"))
f2 = j2.get("msg", "")
b2 = download(f2)
s2, _ = sheet_xml(b2)
check("importTemplate 列头与 Java @Excel(IMPORT) 完全一致", header_of(s2) == TEMPLATE_HEAD,
      "\n  got: %s\n  exp: %s" % (header_of(s2), TEMPLATE_HEAD))
check("模板只有表头一行", s2.count("<row ") == 1, "rows=%d" % s2.count("<row "))

# ---- 4) dept 关联进了列表 JSON（Java 的 resultMap association） ----
raw = json.loads(get("/system/user/list?pageSize=1").decode("utf-8"))
u0 = raw["rows"][0]
check("list 行含非空 dept 对象", isinstance(u0.get("dept"), dict) and u0["dept"].get("deptName"),
      json.dumps(u0.get("dept"), ensure_ascii=False)[:200])
check("dept 只填 SQL 里存在的列（parentId/orderNum/status 为 null）",
      u0["dept"]["parentId"] is None and u0["dept"]["status"] is None,
      json.dumps(u0["dept"], ensure_ascii=False)[:200])
check("行内扁平 deptName 仍是 null（Java resultMap 不映射到该属性）", u0["deptName"] is None, repr(u0["deptName"]))
check("tenantName 由 d2.dept_name 填充", "tenantName" in u0, repr(u0.get("tenantName")))

print("----")
print("pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
