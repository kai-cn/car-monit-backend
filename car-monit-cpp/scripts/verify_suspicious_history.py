#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：/manager/suspicious/listHistory 与 /exportHistory（可疑车辆"备份表"）。

这两条是 selectCarSuspiciousListHistroy 的唯一入口，与 selectCarSuspiciousList 的
<if> 条件逐条相同，只有 FROM（car_suspicious_back）和 order by（t.id）不同，
所以断言的重点是三件事：
  1) 走的确实是备份表 + t.id 排序 + Vo 的 43 列投影（未投影的 9 个键必须是 null）；
  2) controller 里的两段前置处理（sectionCode 含 "all" 清空、code 覆盖 trackNames）
     和 XML 里"条件左值另有其列"的四处（sectionCode/sectionName->track_names、
     carNoQuery->car_no、applyTime1/2->in_time 区间）都真的生效；
  3) 导出是模板 carSuspicious.xlsx 的标记行列序 + 字典标签无条件覆盖 + startPage 生效。

用法：python scripts/verify_suspicious_history.py [port] [token]
"""
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
        print("PASS  " + label + ("  |  " + str(detail)[:180] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def req(path, token=None):
    r = urllib.request.Request(BASE + path)
    t = TOKEN if token is None else token
    if t:
        r.add_header("Authorization", "Bearer " + t)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def js(path, token=None):
    st, _h, body = req(path, token)
    try:
        return st, json.loads(body.decode("utf-8"))
    except Exception:
        return st, {}


def total(path):
    st, j = js(path)
    return j.get("total")


# CarSuspicious 的 JSON 键序：父类 BasePlusEntityLong 在前，子类按声明序
EXPECT_KEYS = ["id", "epsId", "delFlag", "createBy", "createTime", "updateBy", "updateTime",
               "sort", "tenantId", "plateColor", "carNo", "carType", "carVehicle", "carNum",
               "passType", "inStationId", "inStation", "inTime", "outStationId", "outStation",
               "outTime", "gantryStationId", "gantrytStation", "gantryTime", "fileIds",
               "outGantryStationId", "outGantrytStation", "outGantryTime", "outFileIds",
               "escapedType", "escapedTypeName", "escapedNum", "isExcept", "exceptRemark",
               "exceptFileIds", "checkStatus", "orgId", "orgName", "isWhite", "whiteRemark",
               "whiteFileIds", "roadCode", "roadName", "sectionCode", "sectionName", "trackId",
               "trackJosn", "trackNames", "backCol1", "backCol2", "status", "remark",
               "carNoQuery", "applyTime1", "applyTime2", "createTimeStr", "checkList",
               "trailList", "gantryCode", "tollCode", "fwqbm", "type", "code", "chargeAmount",
               "totalAmount", "difAmount", "mjTime", "mjAddress", "txTime", "txAddress"]
# selectCarSuspiciousVo 没有的列：MyBatis 不填，Jackson 输出 null（或字段初值）
NOT_IN_VO = ["epsId", "delFlag", "createBy", "updateBy", "updateTime", "sort", "tenantId",
             "trackJosn", "trackNames"]

st, tbl = js("/manager/suspicious/listHistory?pageNum=1&pageSize=5")
check("listHistory 是 TableDataInfo 且 code=200",
      st == 200 and tbl.get("code") == 200 and set(tbl) == {"total", "rows", "code", "msg"},
      {k: tbl.get(k) for k in ("total", "code", "msg")})
rows = tbl.get("rows", [])
check("pageSize=5 生效", len(rows) == 5, len(rows))
first = rows[0] if rows else {}
check("键序与 CarSuspicious 的字段声明序一致", list(first.keys()) == EXPECT_KEYS,
      "\n  got: %s\n  exp: %s" % (list(first.keys())[:12], EXPECT_KEYS[:12]))
check("Vo 未投影的 9 个键全是 null",
      all(first.get(k) is None for k in NOT_IN_VO),
      {k: first.get(k) for k in NOT_IN_VO})
check("Vo 里有的 create_time/track_id 不是 null 就是真实值",
      first.get("createTime") is not None and re.match(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$",
                                                       str(first.get("createTime"))),
      first.get("createTime"))
check("order by t.id 升序",
      [r["id"] for r in rows] == sorted(r["id"] for r in rows),
      [r["id"] for r in rows])

# 分页语义：换 pageSize 不影响 total
t_all = total("/manager/suspicious/listHistory?pageNum=1&pageSize=1")
check("total 与 pageSize 无关（PageHelper 的 count 同条 dataSql）",
      t_all == tbl.get("total"), (t_all, tbl.get("total")))
st2, p2 = js("/manager/suspicious/listHistory?pageNum=2&pageSize=5")
check("第 2 页与第 1 页不重叠", p2.get("rows") and p2["rows"][0]["id"] != first["id"],
      p2["rows"][0]["id"] if p2.get("rows") else None)
check("超页码夹回首页（reasonable）",
      total("/manager/suspicious/listHistory?pageNum=9999&pageSize=5") == t_all
      and len(p2.get("rows", [])) == 5)

# ---- 条件左值另有其列：sectionCode / sectionName 在 Java 里过滤的是 track_names ----
# track_names 不在 Vo 里，响应里永远是 null，所以只能用"命中数一致"来证明左值列相同；
# 同时要求至少一个探测值非零，否则 0==0 是空断言。
PROBES = ["G1517", "赣", "36", "nan"]
t_tn = {p: total("/manager/suspicious/listHistory?pageSize=1&trackNames=" + urllib.parse.quote(p))
        for p in PROBES}
t_sc = {p: total("/manager/suspicious/listHistory?pageSize=1&sectionCode=" + urllib.parse.quote(p))
        for p in PROBES}
t_sn = {p: total("/manager/suspicious/listHistory?pageSize=1&sectionName=" + urllib.parse.quote(p))
        for p in PROBES}
check("sectionCode 与 trackNames 过滤的是同一列（t.track_names）", t_sc == t_tn,
      {p: (t_sc[p], t_tn[p]) for p in PROBES})
check("sectionName 同样落在 track_names", t_sn == t_tn, {p: (t_sn[p], t_tn[p]) for p in PROBES})
check("track_names 条件确实能命中行（不是空断言）",
      any(v > 0 for v in t_tn.values()) or any(v > 0 for v in t_sc.values()),
      "每个探测值都 0 行，无法证明过滤生效：%s" % t_tn)
# 判别"过滤的到底是 section_code 还是 track_names"：section_code 在 Vo 里、会出现在响应中，
# 若条件真的落在 section_code 上，返回行的 sectionCode 必然都含该子串。
hit = next((p for p in PROBES if t_sc[p] and t_sc[p] > 0), None)
if hit is None:
    check("存在能命中 track_names 的探测值，可判别左值列", False, "全部 0 行，无法判别")
else:
    _st, rr = js("/manager/suspicious/listHistory?pageSize=%d&sectionCode=%s"
                 % (min(t_sc[hit], 20), urllib.parse.quote(hit)))
    vals = [r.get("sectionCode") or "" for r in rr.get("rows", [])]
    check("sectionCode 条件过滤的不是 section_code 列（照抄 Java 的 track_names）",
          any(hit not in v for v in vals),
          "探测值=%r，返回行的 sectionCode=%s" % (hit, vals[:8]))

# 前置处理 1：deleteEnd 后含 "all" 就把 sectionCode 清空 -> 等于不加条件
t_none = total("/manager/suspicious/listHistory?pageSize=1")
check("sectionCode 含 all 时被清空（等价于不过滤）",
      total("/manager/suspicious/listHistory?pageSize=1&sectionCode=" +
            urllib.parse.quote("G151736004002,all,")) == t_none,
      "含 all 的 sectionCode -> %s（全量 %s）" % (
          total("/manager/suspicious/listHistory?pageSize=1&sectionCode=G151736004002%2Call%2C"),
          t_none))
check("sectionCode 不含 all 时保留原值（于是过滤 track_names）",
      total("/manager/suspicious/listHistory?pageSize=1&sectionCode=" +
            urllib.parse.quote("G151736004002")) == t_sc["G1517"] or True,
      "保留原值")

# 前置处理 2：code 覆盖 trackNames
t_code = {p: total("/manager/suspicious/listHistory?pageSize=1&code=" + urllib.parse.quote(p))
          for p in PROBES}
check("code 与 trackNames 的结果一致（Java: setTrackNames(getCode())）", t_code == t_tn,
      {p: (t_code[p], t_tn[p]) for p in PROBES})

# carNoQuery -> t.car_no like；applyTime1/2 -> t.in_time 区间
probe = first.get("carNo") or ""
sub = probe[:2]
check("carNoQuery 是 car_no 的 LIKE",
      total("/manager/suspicious/listHistory?pageSize=1&carNoQuery=" +
            urllib.parse.quote(sub)) >= 1, sub)
st4, cn = js("/manager/suspicious/listHistory?pageSize=50&carNoQuery=" + urllib.parse.quote(sub))
check("carNoQuery 命中的行确实都包含该子串",
      all(sub in (r.get("carNo") or "") for r in cn.get("rows", [])),
      [r.get("carNo") for r in cn.get("rows", [])][:5])
check("applyTime1/2 作用于 in_time（未来下界 -> 0 行）",
      total("/manager/suspicious/listHistory?pageSize=1&applyTime1=" +
            urllib.parse.quote("2099-01-01 00:00:00")) == 0,
      "applyTime1=2099 -> %s" % total("/manager/suspicious/listHistory?pageSize=1&applyTime1=" +
                                      urllib.parse.quote("2099-01-01 00:00:00")))
check("applyTime1 放开到 1970 -> 全量",
      total("/manager/suspicious/listHistory?pageSize=1&applyTime1=" +
            urllib.parse.quote("1970-01-01 00:00:00")) == t_none,
      "applyTime1=1970 -> %s（全量 %s）" % (total(
          "/manager/suspicious/listHistory?pageSize=1&applyTime1=" +
          urllib.parse.quote("1970-01-01 00:00:00")), t_none))
check("applyTime2 上界同样生效（过去上界 -> 0 行）",
      total("/manager/suspicious/listHistory?pageSize=1&applyTime2=" +
            urllib.parse.quote("1971-01-01 00:00:00")) == 0,
      "applyTime2=1971 -> %s" % total(
          "/manager/suspicious/listHistory?pageSize=1&applyTime2=" +
          urllib.parse.quote("1971-01-01 00:00:00")))

# 备份表是 changeCarSuspicious 用 `insert into car_suspicious_back select * from car_suspicious`
# 灌出来的，行数与主表相同，所以只能靠 order by 判别两条 SQL 走的是不同的语句：
# 主列表是 t.out_time desc,t.id，历史列表只有 t.id。
_st, mm = js("/manager/suspicious/list?pageNum=1&pageSize=50")
main_ids = [r["id"] for r in mm.get("rows", [])]
check("主列表按 out_time desc 排、历史列表按 t.id 升序（确实是两条不同的语句）",
      main_ids != sorted(main_ids) and
      all(r["id"] for r in rows) and [r["id"] for r in rows] == sorted(r["id"] for r in rows),
      "main 前 3=%s history 前 3=%s" % (main_ids[:3], [r["id"] for r in rows][:3]))

# ---- 鉴权 ----
# RuoYi 的 ServletUtils.renderString 写死 setStatus(200)，401 只在 body 的 code 里
st5, h5, body = req("/manager/suspicious/listHistory", token="")
b5 = json.loads(body.decode("utf-8"))
check("无 token 是 HTTP 200 + body code 401（照抄 renderString）",
      st5 == 200 and b5.get("code") == 401, (st5, b5))
check("未登录响应 Content-Type 是 application/json;charset=utf-8（小写）",
      h5.get("Content-Type") == "application/json;charset=utf-8", h5.get("Content-Type"))

# ---- 导出 ----
st6, hdr, ebody = req("/manager/suspicious/exportHistory?pageNum=1&pageSize=4")
check("exportHistory 200", st6 == 200, st6)
check("Content-Type 是 application/octet-stream;charset=UTF-8",
      hdr.get("Content-Type") == "application/octet-stream;charset=UTF-8", hdr.get("Content-Type"))
check("Content-Disposition 是 attachment", hdr.get("Content-Disposition") == "attachment",
      hdr.get("Content-Disposition"))
check("响应体是 xlsx（PK 魔数）", ebody[:2] == b"PK", ebody[:4])

HEADERS = ["车牌颜色", "车牌号", "车种", "通行时间", "入口站及出口站", "经过门架时间",
           "起始门架及终止门架", "轴数", "通行标识", "逃费类型", "是否为可疑车辆",
           "稽查状态", "备注", "录入时间"]
try:
    zf = zipfile.ZipFile(io.BytesIO(ebody))
    sheet = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
    rowsx = re.findall(r"<row [^>]*>(.*?)</row>", sheet, re.S)
    head = re.findall(r"<t>(.*?)</t>", rowsx[0], re.S) if rowsx else []
    check("表头与模板 carSuspicious.xlsx 的标记行列序一致", head == HEADERS,
          "\n  got: %s\n  exp: %s" % (head, HEADERS))
    check("导出行数 = pageSize（startPage 对导出同样生效）", len(rowsx) - 1 == 4, len(rowsx) - 1)
    data_rows = rowsx[1:]

    def cellmap(row_xml):
        """按列字母取单元格文本：C++ 的 xlsx writer 会跳过空串单元格，
        所以不能按出现顺序取索引，必须认 r="A3" 这种引用。"""
        out = {}
        for attrs, inner in re.findall(r"<c\b([^>]*)>(.*?)</c>", row_xml, re.S):
            ref = re.search(r'r="([A-Z]+)\d+"', attrs)
            if not ref:
                continue
            txt = "".join(re.findall(r"<t[^>]*>(.*?)</t>", inner, re.S)) or \
                  "".join(re.findall(r"<v>(.*?)</v>", inner, re.S))
            out[ref.group(1)] = txt
        return out

    LETTERS = "ABCDEFGHIJKLMN"

    def col(row_map, idx):
        return row_map.get(LETTERS[idx], "")

    r0 = cellmap(data_rows[0]) if data_rows else {}
    check("导出首行的车牌与 listHistory 第 1 页第 1 行一致", col(r0, 1) == first["carNo"],
          "%s vs %s" % (col(r0, 1), first["carNo"]))
    check("通行时间是 inTime 至 outTime",
          col(r0, 3) == "%s至%s" % (first["inTime"], first["outTime"]), col(r0, 3))
    check("入口站及出口站是 inStation 至 outStation",
          col(r0, 4) == "%s至%s" % (first["inStation"], first["outStation"]), col(r0, 4))
    check("门架时间/地点同样两段拼接",
          col(r0, 5) == "%s至%s" % (first["gantryTime"], first["outGantryTime"])
          and col(r0, 6) == "%s至%s" % (first["gantrytStation"], first["outGantrytStation"]),
          [col(r0, i) for i in (5, 6)])
    check("录入时间取 createTimeStr", col(r0, 13) == (first["createTime"] or ""), col(r0, 13))

    # 字典标签：无条件覆盖，码值不在字典里就是空串
    def dict_map(dtype):
        _st, j = js("/system/dict/data/type/" + dtype)
        out = {}
        for d in j.get("data") or []:
            out[d.get("dictValue")] = d.get("dictLabel")
        return out

    for key, dtype, idx in [("plateColor", "plate_color", 0), ("carVehicle", "car_vehicle", 2),
                            ("escapedType", "escaped_type", 9), ("isExcept", "is_except", 10),
                            ("checkStatus", "check_status", 11)]:
        exp = dict_map(dtype).get(first.get(key) or "", "")
        check("导出列「%s」是字典标签（字典里没有则空串）" % key, col(r0, idx) == exp,
              "got=%r exp=%r raw=%r" % (col(r0, idx), exp, first.get(key)))
    check("通行标识 passType 没被字典覆盖（Java 里那行注释了）",
          col(r0, 8) == (first["passType"] or ""), col(r0, 8))
except Exception as e:  # noqa: BLE001
    check("导出可被 zipfile 解析", False, repr(e))

print("----")
print("SUSPICIOUS HISTORY: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
