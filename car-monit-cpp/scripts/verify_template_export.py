#!/usr/bin/env python3
# 模板导出类接口 + listCarOrgId 的实机验证。
# 断言三件事：响应形态（Java 是"只有字节流 + return null"）、文件是真 xlsx、列与值取自模板标记行。
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9991
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:200] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:280])


def raw(path):
    r = urllib.request.Request(BASE + path)
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def js(path):
    st, _, body = raw(path)
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return {"_bad": body[:200]}


def template_rows(body):
    """解开 xlsx，返回 (sheet 名, 表头单元格, 数据行数)"""
    zf = zipfile.ZipFile(io.BytesIO(body))
    assert zf.testzip() is None, "CRC 校验失败"
    wb = zf.read("xl/workbook.xml").decode("utf-8")
    sheet = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
    names = re.findall(r'<sheet name="([^"]+)"', wb)
    rows = re.findall(r"<row [^>]*>(.*?)</row>", sheet, re.S)
    head = re.findall(r"<t>(.*?)</t>", rows[0], re.S) if rows else []
    return names, head, len(rows) - 1


EXPORTS = [
    ("/manager/exceptrecord/exportOrgId?epsId=-1",
     ["序号", "出口收费站", "出口时间", "通行PASSID", "车牌", "交易车型", "车种", "入口站",
      "入口时间", "漏交通行费类型", "交易金额", "应交金额", "实际追交金额", "备注"]),
    ("/manager/confimfree/exportConcernedList",
     ["车牌号", "车型", "车种", "逃费类型", "录入单位", "应缴金额（元）", "收费金额（元）", "差额（元）", "备注"]),
    ("/manager/confimfree/exportCarStatics",
     ["录入单位", "入口少轴车辆数", "入口少轴金额（元）", "屏蔽车辆数", "屏蔽金额（元）",
      "货车客标车辆数", "货车客标金额（元）", "有入无出车辆数", "有入无出金额（元）",
      "大车小标车辆数", "大车小标金额（元）", "假冒其他优免车车辆数", "假冒其他优免车金额（元）",
      "合计数量", "合计金额（元）"]),
    ("/manager/aduitfree/exportIncomeStatics",
     ["录入单位", "车辆数量", "逃费金额（元）"]),
    ("/manager/aduitfree/exportIncomeDetailList?orgId=-1",
     ["车牌号", "追缴金额（元）", "录入单位", "录入时间"]),
]

for path, headers in EXPORTS:
    st, hd, body = raw(path)
    name = path.split("?")[0]
    ct = hd.get("Content-Type", "")
    check("%s 只有字节流（octet-stream + attachment）" % name,
          st == 200 and "application/octet-stream" in ct and hd.get("Content-Disposition") == "attachment",
          (st, ct, hd.get("Content-Disposition"), len(body)))
    if body[:4] != b"PK\x03\x04":
        check("%s 是真 xlsx" % name, False, body[:120])
        continue
    try:
        sheets, head, nrows = template_rows(body)
    except Exception as e:
        check("%s 可被 zipfile 解析" % name, False, repr(e))
        continue
    check("%s 是合法 xlsx 且 sheet 名与模板一致" % name, sheets == ["Sheet1"], sheets)
    check("%s 表头与模板标记行的取值列一致" % name, head == headers,
          "\n  got: %s\n  exp: %s" % (head, headers))
    print("        数据行数 = %d" % nrows)

# ---- listCarOrgId ----
lst = js("/manager/exceptrecord/listCarOrgId?pageNum=1&pageSize=3")
check("listCarOrgId 是 TableDataInfo",
      all(k in lst for k in ("total", "rows", "code", "msg")) and lst.get("code") == 200,
      {k: lst.get(k) for k in ("total", "code", "msg")})
check("不带 epsId 时 Java 兜成 -1（本机 eps_id 无 -1 -> 0 行）",
      lst.get("total") == 0, lst.get("total"))
org = js("/manager/confimfree/list?pageNum=1&pageSize=1")
orgrows = org.get("rows") or []
if orgrows:
    oid = orgrows[0].get("epsId") or orgrows[0].get("orgId")
    q = js("/manager/exceptrecord/listCarOrgId?pageNum=1&pageSize=50&epsId=%s" % oid)
    check("带 epsId 时能取到该单位的异常流水", q.get("total", 0) > 0, (oid, q.get("total")))
    rows = q.get("rows") or []
    if rows:
        check("排序按 dif_amount desc",
              all((rows[i].get("difAmount") or 0) >= (rows[i + 1].get("difAmount") or 0)
                  for i in range(len(rows) - 1)),
              [r.get("difAmount") for r in rows[:5]])
        check("createInfo 是「单位名 录入人昵称」拼接",
              all((" " in (r.get("createInfo") or "")) or r.get("createInfo") is None for r in rows),
              rows[0].get("createInfo"))
        # 与既有列表接口对齐：同一 epsId 的总数应一致
        same = js("/manager/exceptrecord/list?pageNum=1&pageSize=1&epsId=%s" % oid)
        check("listNew 与 list 在同一 epsId 下总数一致", same.get("total") == q.get("total"),
              (same.get("total"), q.get("total")))

# ---- exportOrgId 的字典翻译：车型/车种/逃费类型换成标签，补缴状态无条件换 ----
st, _, body = raw("/manager/exceptrecord/exportOrgId?epsId=" + str(oid if orgrows else -1))
if body[:4] == b"PK\x03\x04":
    zf = zipfile.ZipFile(io.BytesIO(body))
    sheet = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
    vals = re.findall(r"<t>(.*?)</t>", sheet, re.S)
    print("        导出单元格抽样: %s" % json.dumps(vals[:14], ensure_ascii=False)[:220])
    check("exportOrgId 有数据行（说明字典翻译路径跑通）", len(vals) > 14, len(vals))

print("----")
print("TEMPLATE EXPORT: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
