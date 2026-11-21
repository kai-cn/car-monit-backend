#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：POST /manager/carinfo/import 与 POST /manager/exceptrecord/import。

xlsx 用 Python 标准库现拼（zipfile + ZIP_DEFLATED），所以这条链路把
zip 中央目录 → inflate → sharedStrings → sheet 全部走了一遍，
不是"自己写自己读"的自证。

前置：
    ./build/car-monit-cpp.exe                 （默认 config/，端口 8080）
    python scripts/make_token.py              （拿当天有效的 JWT）
用法：
    python scripts/verify_import.py [port] [token]

脚本自带夹具、自带清理（QODERIMP 前缀的车牌 / 备注），跑完数据库回到跑前状态。
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0
PLATE = "QODERIMP挂A"
PLATE2 = "QODERIMP挂B"
PLATE3 = "QODERIMP挂C"
NOPLATE = ""
REMARK = "qoder-import-probe"


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:150] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def req(path, method="GET", body=None, ctype=None, token=TOKEN):
    r = urllib.request.Request(BASE + path, method=method)
    if token:
        r.add_header("Authorization", "Bearer " + token)
    data = body.encode("utf-8") if isinstance(body, str) else body
    if data is not None and ctype:
        r.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(r, data=data, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def upload_xlsx(path, content, filename):
    b = "----qoderimportboundary"
    body = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n" % (b, filename)).encode("utf-8")
    body += content + b"\r\n--%s--\r\n" % b.encode("utf-8")
    st, raw = req(path, "POST", body, "multipart/form-data; boundary=" + b)
    try:
        return st, json.loads(raw.decode("utf-8")), raw.decode("utf-8", "replace")
    except Exception:
        return st, {"raw": raw[:200]}, raw.decode("utf-8", "replace")


def mysql(sql):
    r = subprocess.run(["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot",
                        "carmonitdb", "-N", "-B", "-e", sql], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        err = "\n".join(l for l in r.stderr.decode("utf-8", "replace").splitlines()
                        if "Using a password" not in l)
        raise RuntimeError(err or out)
    return out.splitlines()


# ------------------------------------------------------------------ xlsx 拼装机
# 单元格三元组：('s', 文本) 共享字符串 / ('n', 数字) 走 DecimalFormat("#.##")
#               / ('d', 序列号) 日期样式，走 getCellFormatValue07/08 的日期分支

def xlsx(rows, date_with_time_style=True):
    strings, sidx = [], {}
    def sref(t):
        if t not in sidx:
            sidx[t] = len(strings)
            strings.append(t)
        return sidx[t]

    def colname(i):
        n, out = i + 1, ""
        while n:
            n, rem = divmod(n - 1, 26)
            out = chr(65 + rem) + out
        return out

    sheet = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
    ri = 0
    for row in rows:
        ri += 1
        if row is None:
            # 整行不写 <row> ⇒ POI 的 getRow(r) 返回 null，这才是 dataRtnExcel07/08 里
            # "NPE 被 catch 成 break" 的那种行；[[]]（行在但没格）是另一回事，不能 break
            sheet.append("")
            continue
        cells = []
        for ci, cell in enumerate(row):
            ref = colname(ci) + str(ri)
            if cell is None:
                continue
            kind, val = cell
            if kind == "s":
                cells.append('<c r="%s" t="s"><v>%d</v></c>' % (ref, sref(val)))
            elif kind == "n":
                cells.append('<c r="%s"><v>%s</v></c>' % (ref, val))
            elif kind == "d":
                cells.append('<c r="%s" s="1"><v>%s</v></c>' % (ref, val))
        sheet.append('<row r="%d">%s</row>' % (ri, "".join(cells)))
    sheet.append("</sheetData></worksheet>")

    ss = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="%d" uniqueCount="%d">%s</sst>'
          % (len(strings), len(strings), "".join("<si><t>%s</t></si>" % s for s in strings)))
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<numFmts count="1"><numFmt numFmtId="176" formatCode="yyyy-mm-dd\\ hh:mm:ss"/></numFmts>'
              '<cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="176"/></cellXfs>'
              '</styleSheet>')
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                     '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                     '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                     '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                     '</Types>')
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>'
                '</sheets></workbook>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:   # deflate ⇒ 真走 inflate
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/sharedStrings.xml", ss)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", "".join(sheet))
    return buf.getvalue()


CAR_HEAD = ["车牌颜色", "车牌号", "车型", "车种", "轴数", "逃费类型", "逃费金额（元）", "备注"]

# 断言里用到的字典值一律从库里读，别把字典内容写死在脚本里（本地库和线上不一样）
_d = mysql("select dict_value from sys_dict_data where dict_type='plate_color'"
            " and dict_label='蓝色' limit 1")
PLATE_COLOR_VALUE = _d[0] if _d else "0"


def car_row(color="蓝色", car_type="客一", vehicle="客车", num=2, escaped="入口少轴",
            amount=12.5, remark=REMARK, plate=PLATE2):
    return [("s", color), ("s", plate), ("s", car_type), ("s", vehicle),
            ("n", str(num)), ("s", escaped), ("n", str(amount)), ("s", remark)]


def car_file(rows):
    return xlsx([[("s", h) for h in CAR_HEAD]] + rows)


# ------------------------------------------------------------------ 清理

PLATES = ("'%s','%s','%s','QODERIMP挂X','QODERIMP挂Y','QODERIMP挂Z'"
          % (PLATE, PLATE2, PLATE3))


def cleanup():
    mysql("delete from car_except_record where car_no in (%s) or id='qoderimp-ex-1'" % PLATES)
    mysql("delete from car_info where car_no in (%s) or id='qoderimp-car-1'"
          " or car_no like 'QODERIMPM%%' or remark='%s'" % (PLATES, REMARK))


cleanup()

if not TOKEN:
    print("缺少 token（python scripts/make_token.py），后续断言都会是 401")

# ================================================================== 1) carinfo
print("\n===== POST /manager/carinfo/import =====")

st, j, raw = upload_xlsx("/manager/carinfo/import", b"not xlsx", "probe.xls")
check("非 .xlsx：lastIndexOf(\".xlsx\")==-1 就是拒", st == 200 and j.get("code") == 500
      and j.get("msg") == "请上传Excel文件(.xlsx)", (st, j))

st, j, raw = upload_xlsx("/manager/carinfo/import", b"garbage bytes", "probe.xlsx")
check("文件名过了但包不是 xlsx ⇒ Java 是 XSSFWorkbook 抛 ⇒ 500，不是\"空表\"",
      st == 200 and j.get("code") == 500 and "OOXML" in str(j.get("msg")), (st, j))

st, j, raw = upload_xlsx("/manager/carinfo/import",
                         car_file([car_row()]), "t.xlsx")
# 上面这一条表头是对的，先当作对照
check("表头正确 + 一行数据 ⇒ 数据导入成功", j.get("msg") == "数据导入成功" and j.get("code") == 200,
      (st, j))

st, j, raw = upload_xlsx("/manager/carinfo/import",
                         xlsx([[("s", "车牌颜色"), ("s", "车牌号"), ("s", "车型"), ("s", "车种"),
                               ("s", "轴数"), ("s", "逃费类型"), ("s", "逃费金额"), ("s", "备注")],
                              car_row()]), "t.xlsx")
check("表头差一个字（半角括号）⇒ 导入失败,模板不正确 ⇒ 下载模板文案",
      j.get("msg") == "导入失败,模板不正确,请下载对应的模板！", j)

st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([]), "t.xlsx")
check("只有表头没有数据行 ⇒ 模板excel没有数据可以导入",
      j.get("msg") == "导入失败,模板excel没有数据可以导入，请确定！", j)

cleanup()
st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([car_row()]), "t.xlsx")
data = j.get("data") or []
first_id = None
d0 = {}
check("成功响应的 data 是 importList（List<CarInfo>），一条", isinstance(data, list) and len(data) == 1,
      len(data) if isinstance(data, list) else j)
if data:
    d0 = data[0]
    keys = list(d0.keys())
    check("data[0] 键序 = CarInfo 字段声明序（父类在前）",
          keys[:9] == ["id", "epsId", "delFlag", "createBy", "createTime", "updateBy",
                       "updateTime", "sort", "tenantId"], keys[:9])
    check("字典翻译真的落到实体上：蓝色→0、客一→1、客车→1（值取自 sys_dict_data）",
          d0.get("plateColor") == PLATE_COLOR_VALUE and d0.get("carType") == "1"
          and d0.get("carVehicle") == "1",
          {k: d0.get(k) for k in ("plateColor", "carType", "carVehicle")})
    check("逃费类型 label→value：入口少轴→10", d0.get("escapedType") == "10", d0.get("escapedType"))
    check("轴数是数字（Long），逃费金额是数字（BigDecimal 原文）",
          d0.get("carNum") == 2 and d0.get("escapedAmount") == 12.5,
          (d0.get("carNum"), d0.get("escapedAmount")))
    check("没在 Excel 里的列（brand/roadName）输出 null，不是漏键",
          "brand" in d0 and d0["brand"] is None and "roadName" in d0, len(d0))
    check("服务层补的主键/审计字段回显在 data 里（Java 改的是同一批对象）",
          isinstance(d0.get("id"), str) and len(d0.get("id") or "") == 32
          and d0.get("delFlag") == "0" and isinstance(d0.get("createBy"), int),
          (d0.get("id"), d0.get("delFlag"), d0.get("createBy")))
    row = mysql("select plate_color,car_type,car_vehicle,escaped_type,escaped_amount,create_by"
                " from car_info where car_no='%s'" % PLATE2)
    check("库里落的就是翻译后的值", row and row[0].split("\t")[0] == PLATE_COLOR_VALUE, row)
    first_id = d0.get("id")

st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([car_row()]), "t.xlsx")
second = (j.get("data") or [{}])[0]
check("同车牌再导入 ⇒ selectCarInfoList 命中后复用主键（updateById 分支）",
      second.get("id") == first_id, (second.get("id"), first_id))
check("库里还是 1 行 ⇒ 没有重复插入",
      mysql("select count(1) from car_info where car_no='%s'" % PLATE2) == ["1"])
check("⚠️ update 分支只设 updateBy/updateTime ⇒ 响应里 createTime 是 null（对象是刚从 Excel 造的，"
      "库里那列没被读进来）",
      second.get("createTime") is None and isinstance(second.get("updateTime"), str),
      (second.get("createTime"), second.get("updateTime")))

st, j, raw = upload_xlsx("/manager/carinfo/import",
                         car_file([car_row(escaped="入口少轴，大车小标,")]), "t.xlsx")
check("全角逗号 + 结尾逗号：deleteEnd→replace→逐个翻译→再 deleteEnd",
      (j.get("data") or [{}])[0].get("escapedType") == "10,50",
      (j.get("data") or [{}])[0].get("escapedType"))

st, j, raw = upload_xlsx("/manager/carinfo/import",
                         car_file([car_row(plate=PLATE3), car_row(plate="QODERIMP挂X", color="不存在的颜色")]),
                         "t.xlsx")
errs = j.get("data") or []
check("字典认不出 ⇒ msg=error、code=500、data=errorList",
      j.get("msg") == "error" and j.get("code") == 500 and isinstance(errs, list) and errs, j)
if errs:
    check("⚠️ rowNo = index + 2（getErrorBO 里 +1，调用点又 +1）：第 2 行数据报的是 3",
          errs[0].get("rowNo") == 3, errs[0])
    check("错误文案逐字对齐（值 + 空格 + 提示）",
          errs[0].get("message") == "不存在的颜色 车牌颜色不存在,请在字典菜单维护！", errs[0])
    check("errorList 是 ImportErrorEntity 的三个键",
          list(errs[0].keys()) == ["rowNo", "colName", "message"], list(errs[0].keys()))
check("⚠️ 共享 errorList ⇒ 出错行之前的第 1 行也没入库（errorList 非空 ⇒ 整批不写）",
      mysql("select count(1) from car_info where car_no='%s'" % PLATE3) == ["0"],
      mysql("select count(1) from car_info where car_no='%s'" % PLATE3))
check("HTTP 仍然是 200（RuoYi 的业务码在 body 里）", st == 200, st)

BLANK_CAR = [("s", "蓝色"), ("s", ""), ("s", "客一"), ("s", "客车"),
             ("n", "2"), ("s", "入口少轴"), ("n", "1"), ("s", REMARK)]
BADNUM_CAR = [("s", "蓝色"), ("s", PLATE), ("s", "客一"), ("s", "客车"),
              ("s", "abc"), ("s", "入口少轴"), ("s", "1.2.3"), ("s", REMARK)]

st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([BLANK_CAR]), "t.xlsx")
e = (j.get("data") or [{}])[0]
check("必填格为空 ⇒ \"不能为空\"，colName 取表头\"车牌号\"",
      e.get("colName") == "车牌号" and e.get("message") == "不能为空", e)
check("一行只有\"车牌号\"这一格空 ⇒ 只报一条（其余列都有值）",
      len(j.get("data") or []) == 1, j.get("data"))

st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([BADNUM_CAR]), "t.xlsx")
msgs = [(x.get("colName"), x.get("message")) for x in (j.get("data") or [])]
check("规则 3/2：不是正整数、不是小数",
      ("轴数", "不是正整数") in msgs and ("逃费金额（元）", "不是小数") in msgs, msgs)

# >100 的 break：103 行全错 ⇒ 只留 101 条
many = []
for i in range(103):
    many.append([("s", "不存在的颜色"), ("s", "QODERIMPM%d" % i), ("s", "客一"), ("s", "客车"),
                 ("n", "1"), ("s", "入口少轴"), ("n", "1"), ("s", REMARK)])
st, j, raw = upload_xlsx("/manager/carinfo/import", car_file(many), "t.xlsx")
check("⚠️ errorList.size()>100 才 break ⇒ 最多返回 101 条而不是 100 条",
      len(j.get("data") or []) == 101, len(j.get("data") or []))
mysql("delete from car_info where car_no like 'QODERIMPM%'")

# 整行缺失（sheet 里没有那个 <row>）⇒ POI getRow 返回 null ⇒ NPE 被 catch 成 break
st, j, raw = upload_xlsx("/manager/carinfo/import",
                         xlsx([[("s", h) for h in CAR_HEAD], None,
                               car_row(), car_row(plate="QODERIMP挂X")]), "t.xlsx")
check("表头后紧跟一个\"不存在的行\" ⇒ 与 Java 一样在这里 break，后面两行都不读",
      j.get("msg") == "导入失败,模板excel没有数据可以导入，请确定！", j)

# 行存在但没有单元格（<row r="2"/>）⇒ getLastCellNum() 不抛，循环继续读下一行
st, j, raw = upload_xlsx("/manager/carinfo/import",
                         xlsx([[("s", h) for h in CAR_HEAD], [], car_row()]), "t.xlsx")
check("\"行在、但没有格\"不触发 NPE ⇒ 这一行照常被当成一行数据（8 格全空 ⇒ 4 条必填错误）",
      j.get("msg") == "error" and len(j.get("data") or []) == 4,
      (j.get("msg"), len(j.get("data") or [])))

# 整个第 1 行都不存在 ⇒ getRow(0) == null ⇒ colVdaExcel07 直接 false
st, j, raw = upload_xlsx("/manager/carinfo/import",
                         xlsx([None, [("s", h) for h in CAR_HEAD], car_row()]), "t.xlsx")
check("第 1 行不存在 ⇒ 表头比较拿到 null 行，模板不正确",
      j.get("msg") == "导入失败,模板不正确,请下载对应的模板！", j)

# 首列写 "结束" ⇒ dataRtnExcel07 在读取阶段就 break（还没轮到逐格校验）
st, j, raw = upload_xlsx("/manager/carinfo/import",
                         xlsx([[("s", h) for h in CAR_HEAD],
                               [("s", "结束"), ("s", PLATE), ("s", "客一"), ("s", "客车"),
                                ("n", "1"), ("s", "入口少轴"), ("n", "1"), ("s", REMARK)],
                               car_row(plate="QODERIMP挂X")]), "t.xlsx")
check("首列\"结束\" ⇒ 与 Java 一样在读取阶段 break，后面的行根本不参与校验",
      j.get("msg") == "导入失败,模板excel没有数据可以导入，请确定！", j)
check("因为提前 break ⇒ 那一行也没落库",
      mysql("select count(1) from car_info where car_no='QODERIMP挂X'") == ["0"],
      mysql("select count(1) from car_info where car_no='QODERIMP挂X'"))

st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([car_row()]), "t.xlsx")
mysql("delete from car_info where car_no='%s'" % PLATE2)
st2, j2, _r2 = upload_xlsx("/manager/carinfo/import", car_file([car_row()]), "t.xlsx")
check("清掉缓存外的一行后重导 ⇒ 又走 insert（生成新主键）",
      j2.get("msg") == "数据导入成功" and
      (j2.get("data") or [{}])[0].get("id") != (data or [{}])[0].get("id"), j2)

# selectCarInfoList 的 not exists：异常流水全部已补缴 ⇒ 这辆车在查询里"消失"
mysql("delete from car_info where car_no='%s'" % PLATE2)
mysql("insert into car_info (id,car_no,del_flag,status) values ('qoderimp-car-1','%s','0','0')" % PLATE2)
mysql("insert into car_except_record (id,car_no,in_time,del_flag,status,dif_amount)"
      " values ('qoderimp-ex-1','%s','2024-01-02 03:04:05','0','2',1.00)" % PLATE2)
st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([car_row()]), "t.xlsx")
new_id = (j.get("data") or [{}])[0].get("id")
check("⚠️ not exists 过滤：异常流水已缴清的 plate 在 selectCarInfoList 里查不到 ⇒ 当成新车牌另插一行",
      mysql("select count(1) from car_info where car_no='%s'" % PLATE2) == ["2"]
      and new_id != "qoderimp-car-1", (new_id, mysql("select id from car_info where car_no='%s'" % PLATE2)))

cache = mysql("select 1")  # 占位，Redis 用另一个 helper
def redis_get(key):
    import socket
    s = socket.create_connection(("127.0.0.1", 6379), 5)
    s.sendall(b"*2\r\n$3\r\nGET\r\n$%d\r\n%s\r\n" % (len(key), key.encode()))
    buf = b""
    while b"\r\n" not in buf or not buf.endswith(b"\r\n"):
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
        if buf.startswith(b"$") and len(buf) > int(buf[1:buf.index(b"\r\n")]) + 4:
            break
    s.close()
    head, rest = buf.split(b"\r\n", 1)
    n = int(head[1:])
    return (rest[:n].decode("utf-8", "replace") if n > 0 else "") if n >= 0 else ""

val = redis_get("car_list")
check("Redis car_list 是 fastjson2 WriteClassName 形态（@type + Long 带 L）",
      '"@type":"com.ruoyi.manager.domain.CarInfo"' in val and "L," in val, val[:120])
# 上面那辆 QODERIMP挂B 因为异常流水已缴清被 not exists 滤掉了，正好用它反证；
# 缓存里应该出现的是"没有被滤掉"的车，所以再导一辆干净车牌专门验这一条
CACHE_PLATE = "QODERIMPCACHE1"
mysql("delete from car_info where car_no='%s'" % CACHE_PLATE)
st, j, raw = upload_xlsx("/manager/carinfo/import",
                         car_file([car_row(plate=CACHE_PLATE)]), "t.xlsx")
val = redis_get("car_list")
check("刚导入、且没有被 not exists 滤掉的车牌进了 car_list ⇒ updateRedisCarList 真的跑了",
      j.get("msg") == "数据导入成功" and CACHE_PLATE in val,
      (j.get("msg"), CACHE_PLATE in val))
check("⚠️ 已缴清的那辆（not exists 滤掉）不在缓存里 —— 缓存和列表接口是同一个查询",
      PLATE2 not in val, PLATE2)
mysql("delete from car_info where car_no='%s'" % CACHE_PLATE)
jc = redis_get("car_list_jc")
check("car_list_jc 只有 carId/carNo 两个业务键（CarVO 其余属性 null 被 fastjson2 省略）",
      '"@type":"com.ruoyi.base.domain.CarVO"' in jc and "trackJosn" not in jc, jc[:140])

cleanup()

# ================================================================== 2) exceptrecord
print("\n===== POST /manager/exceptrecord/import =====")

EX_HEAD = ["序号", "出口收费站", "出口时间", "通行PASSID", "车牌", "交易车型", "车种", "入口站",
           "入口时间", "漏交通行费类型", "", "交易金额", "", "", "应交金额", "", "",
           "实际追交金额", "", "", "备注", ""]

# 收费站名必须用库里真有的，否则"名→码"那条断言测的是查不到分支
_t = mysql("select distinct toll_name from ods_szdn_toll where toll_name is not null"
           " and toll_name <> '' order by toll_name limit 2")
TOLL_OK = _t[0] if _t else "泰和"
TOLL2 = _t[1] if len(_t) > 1 else TOLL_OK


def ex_file(rows, head_row=1):
    """Java 的两条表头分支：colVdaExcel08(sheet, colsName, 1) || (.., 2) —— head_row 就是那个 num。
    数据永远从下标 3 读，所以表头行与"表头之后、数据之前"的那一行都必须存在
    （row==null 会被 dataRtnExcel08 的 NPE-catch 当成 break）。"""
    rows_all = [[("s", "标题行")]]
    while len(rows_all) < head_row:
        rows_all.append([("s", "说明行")])
    rows_all.append([(h and ("s", h) or None) for h in EX_HEAD])
    while len(rows_all) < 3:
        rows_all.append([("s", "小计行")])
    return xlsx(rows_all + rows)


def ex_row(seq=1, out_station="", out_time="2024-01-02 10:00:00", passid="P001", plate=PLATE,
            car_type="客1", vehicle="", in_station="", in_time="2024-01-02 03:04:05",
            back1="二级类型名", escaped="入口少轴", charge=5.0, total=20.0, remark=REMARK,
            out_station_ok=True):
    """22 列，按 strName/strNum：0/11/12/14/15/17/18/19/21 这几列 Java 不取值。"""
    return [
        ("n", str(seq)),                        # 0 序号（skip）
        ("s", TOLL_OK if out_station_ok else "不存在的收费站"),   # 1 outStation
        ("s", out_time),                        # 2 outTime  ← 规则 1,8
        ("s", passid),                          # 3 passType
        ("s", plate),                           # 4 carNo    ← 规则 1
        ("s", car_type),                        # 5 carType
        ("s", vehicle),                         # 6 carVehicle（会被车型推出来的值覆盖）
        ("s", TOLL2 if out_station_ok else "也不存在的站"),   # 7 inStation
        ("s", in_time),                         # 8 inTime   ← 规则 1,8
        ("s", back1),                           # 9 backCol1
        ("s", escaped),                         # 10 escapedType ← 规则 1
        None,                                   # 11 交易金额（skip）
        None,                                   # 12 省内（skip，prop 也是 ""）
        ("n", str(charge)),                     # 13 chargeAmount ← 规则 1,2
        None,                                   # 14 应交金额（skip）
        None,                                   # 15 省外（skip，prop ""）
        ("n", str(total)),                      # 16 totalAmount ← 规则 1,2
        None,                                   # 17 实际追交金额（skip）
        None,                                   # 18 省内（skip）
        None,                                   # 19 小计（prop ""）
        ("s", remark),                          # 20 remark
        None,                                   # 21 备注后的空列（skip）
    ]


st, j, raw = upload_xlsx("/manager/exceptrecord/import", b"x", "p.xlsx")
check("不是 xlsx 包 ⇒ 500（文件名 .xlsx 只过第一道）", j.get("code") == 500, j)

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row()]), "t.xlsx")
check("表头在第 2 行 ⇒ colVdaExcel08(..,1) 命中", j.get("msg") == "数据导入成功", j)
d = (j.get("data") or [{}])[0]
keys = list(d.keys())
check("data[0] 键序 = CarExceptRecord 声明序（父类在前）",
      keys[:9] == ["id", "epsId", "delFlag", "createBy", "createTime", "updateBy",
                   "updateTime", "sort", "tenantId"], keys[:9])
check("⚠️ supplementaryStatus 是字段初始值 \"0\"，没被赋值也要输出",
      d.get("supplementaryStatus") == "0", d.get("supplementaryStatus"))
check("in/out 时间原样输出 yyyy-MM-dd HH:mm:ss（@JsonFormat）",
      d.get("inTime") == "2024-01-02 03:04:05" and d.get("outTime") == "2024-01-02 10:00:00",
      (d.get("inTime"), d.get("outTime")))
check("car_type_change：客1→1；车种由车型推出（1→客车=1）",
      d.get("carType") == "1" and d.get("carVehicle") == "1",
      (d.get("carType"), d.get("carVehicle")))
check("逃费类型 label→value：入口少轴→10", d.get("escapedType") == "10", d.get("escapedType"))
check("收费站名→码：命中才写 id",
      d.get("outStation") == TOLL_OK and isinstance(d.get("outStationId"), str)
      and d.get("outStationId"),
      (d.get("outStation"), d.get("outStationId")))
check("difAmount = total - charge，两位小数（BigDecimal.subtract 的标度）",
      d.get("difAmount") == 15.0, d.get("difAmount"))
check("⚠️ 车牌不在重点车辆库 ⇒ 走 saveCarInfo 新建；但 carId 用的是**校验前**建好的 carMap，"
      "所以这一行的 carId 还是 null（Java 同样如此）",
      isinstance(d.get("carId"), type(None)) and
      mysql("select count(1) from car_info where car_no='%s'" % PLATE) == ["1"],
      (d.get("carId"), mysql("select count(1) from car_info where car_no='%s'" % PLATE)))

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row()], head_row=2), "t.xlsx")
check("表头改放到第 3 行也认（colVdaExcel08(..,1) || (..,2) 的第二个分支）",
      j.get("msg") == "数据导入成功", j)

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         xlsx([[("s", "标题")], [("s", "x"), ("s", "x")],
                               [("s", "x")] * 3] + [ex_row()]), "t.xlsx")
check("两行都不像表头 ⇒ 导入失败,模板不正确",
      j.get("msg") == "导入失败,模板不正确,请下载对应的模板！", j)

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(total=3.0, charge=8.0)]), "t.xlsx")
check("缴费金额：total < charge ⇒ 收费金额不能大于应缴金额",
      any(x.get("message") == "收费金额不能大于应缴金额" and x.get("colName") == "缴费金额"
          for x in (j.get("data") or [])), j.get("data"))

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(in_time="2024-01-05 00:00:00",
                                         out_time="2024-01-02 00:00:00")]), "t.xlsx")
check("入口时间大于出口时间，请确认!",
      any(x.get("message") == "入口时间大于出口时间，请确认!" and x.get("colName") == "时间"
          for x in (j.get("data") or [])), j.get("data"))

# 前面几条"导入成功"的用例已经写过 remark=REMARK 的行，这里先清干净，
# 否则"这一批一行都没写"会被上一批的残留顶掉。
mysql("delete from car_except_record where remark='%s'" % REMARK)
mysql("delete from car_info where car_no='QODERIMP挂Y'")
st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(), ex_row(escaped="不存在的类型", plate="QODERIMP挂Y")]),
                         "t.xlsx")
errs = j.get("data") or []
check("⚠️ rowNo = index + 2：第 2 条数据（Excel 第 5 行）报的是 3，永远比真实行号少 2",
      errs and errs[-1].get("rowNo") == 3, errs)
check("认不出的逃费类型也报错（这里与 carinfo 同一文案）",
      errs and "逃费类型不存在" in errs[-1].get("message", ""), errs)
check("出错 ⇒ 一行都不写",
      mysql("select count(1) from car_except_record where remark='%s'" % REMARK) == ["0"],
      mysql("select count(1) from car_except_record where remark='%s'" % REMARK))

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(seq=1), ex_row(seq=2, plate=PLATE3)]), "t.xlsx")
check("多行一起导 ⇒ 两行都写进去",
      mysql("select count(1) from car_except_record where remark='%s'" % REMARK) == ["2"],
      mysql("select id,car_no from car_except_record where remark='%s'" % REMARK))
ids = mysql("select id from car_except_record where remark='%s' order by id" % REMARK)
st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(seq=1)]), "t.xlsx")
check("按 车牌+入口时间 upsert：同车牌同入口时间 ⇒ 复用已有主键",
      mysql("select count(1) from car_except_record where car_no='%s' and remark='%s'"
            % (PLATE, REMARK)) == ["1"], (ids, mysql(
          "select id,in_time from car_except_record where car_no='%s'" % PLATE)))

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(seq=1, plate=PLATE3, in_time="2024-01-02 03:04:05",
                                         out_time="2024-01-02 10:00:00")]), "t.xlsx")
check("⚠️ isExitsTime 判的是\"区间有交集\"而不是\"完全相同\"，且返回值被丢弃 ⇒"
      "响应仍然报成功，那一行只是没落库",
      j.get("msg") == "数据导入成功", j)

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         ex_file([ex_row(out_station_ok=False, plate="QODERIMP挂Z")]), "t.xlsx")
d = (j.get("data") or [{}])[0]
check("收费站名查不到 ⇒ 不报错，station/stationId 一个有值一个 null",
      j.get("msg") == "数据导入成功" and d.get("outStation") == "不存在的收费站"
      and d.get("outStationId") is None,
      (j.get("msg"), d.get("outStation"), d.get("outStationId")))

mysql("delete from sys_dict_data where dict_type='plate_color' and dict_label='重复色'")
mysql("insert into sys_dict_data (dict_sort,dict_label,dict_value,dict_type,status)"
      " values (900,'重复色','1','plate_color','0'),(901,'重复色','2','plate_color','0')")
st, j, raw = upload_xlsx("/manager/carinfo/import", car_file([car_row(color="重复色")]), "t.xlsx")
check("⚠️ 字典重复 label ⇒ Collectors.toMap 抛 IllegalStateException ⇒ code 500",
      j.get("code") == 500 and "Duplicate key" in str(j.get("msg")), j)
mysql("delete from sys_dict_data where dict_type='plate_color' and dict_label='重复色'")

st, j, raw = upload_xlsx("/manager/exceptrecord/import",
                         xlsx([[("s", "标题")], [(h and ("s", h) or None) for h in EX_HEAD],
                               [("s", "小计")]]), "t.xlsx")
check("只有表头没有数据 ⇒ 模板excel没有数据可以导入",
      j.get("msg") == "导入失败,模板excel没有数据可以导入，请确定！", j)

cleanup()
print("\n合计 PASS=%d FAIL=%d" % (ok, bad))
sys.exit(1 if bad else 0)
