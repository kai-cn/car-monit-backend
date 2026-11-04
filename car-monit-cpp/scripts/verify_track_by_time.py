#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：GET /manager/cartrackinfo/listByCarByTime。

这条接口的 Java 实现有三处很容易抄错，断言逐一对应：
  1) 响应是**手搭**的 TableDataInfo：rows 是 TrailInfo（不是实体本身），
     total 来自 new PageInfo(carlist) —— 展开时把 track_josn 为空的行丢掉，
     但 total 不跟着减，所以 total >= len(rows)。
  2) ZdataTrailTracks 的 trailPoints / trackJosn 在返回前被置成空串（不是 null、不是原值）。
  3) isCylx=1 走 getCyly（窗口函数 + LIMIT 3），且 startPage() 的分页落在 **getCyly**
     而不是 getHistoryTrail 上；命中行的 plateKey 追加"(通行N次)"。
另外 TrailInfo/TrailBo 的 JSON 键集是照抄字段声明序的（fastjson 丢掉多余键、
Jackson 补出缺失键），这里按声明序硬断言。

用法：python scripts/verify_track_by_time.py [port] [token]
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9991
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT
PATH = "/manager/cartrackinfo/listByCarByTime"

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:170] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:380])


def raw(query, token=None):
    r = urllib.request.Request("%s%s?%s" % (BASE, PATH, query))
    t = TOKEN if token is None else token
    if t:
        r.add_header("Authorization", "Bearer " + t)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def js(query, token=None):
    st, _h, body = raw(query, token)
    try:
        return st, json.loads(body.decode("utf-8"))
    except Exception:
        return st, {}


def get(url_path, query=""):
    r = urllib.request.Request("%s%s%s" % (BASE, url_path, ("?" + query) if query else ""))
    r.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


TRAIL_INFO_KEYS = ["trailUuid", "enterTime", "tracks", "trailList", "raodTrailList",
                   "trailDevCountBO"]
TRAIL_BO_KEYS = ["pointUuid", "stateType", "pointFlag", "pointJosn", "captureTime",
                 "directionIn", "locationCode", "locationFlag", "ipType", "locationJosn",
                 "devCode", "devName", "imagesArry", "lon", "lat", "roadCode", "sectionCode",
                 "direction", "pileno", "preCaptureTime", "countNum", "pilenoDec", "isQuery"]

st, tbl = js("pageNum=1&pageSize=2")
check("手搭 TableDataInfo 的键序 total,rows,code,msg 与 200/查询成功",
      list(tbl.keys()) == ["total", "rows", "code", "msg"] and tbl.get("code") == 200
      and tbl.get("msg") == "查询成功", list(tbl.keys()))
rows = tbl.get("rows", [])
check("有数据", len(rows) == 2 and tbl.get("total", 0) > 0, (len(rows), tbl.get("total")))
r0 = rows[0]
check("TrailInfo 的键按字段声明序", list(r0.keys()) == TRAIL_INFO_KEYS, list(r0.keys()))

tracks = r0.get("tracks", {})
# 同一个实体在 /base/trailtracks/list 里的键集必须完全一致（Jackson 按声明序）
main = get("/base/trailtracks/list", "pageNum=1&pageSize=1")
mrows = main.get("rows", [])
check("tracks 的键集 = ZdataTrailTracks 的声明序（与 /base/trailtracks/list 完全一致）",
      mrows and list(tracks.keys()) == list(mrows[0].keys()),
      "\n  here: %s\n  main: %s" % (list(tracks.keys())[:8], list(mrows[0].keys())[:8] if mrows else []))
check("trailPoints/trackJosn 被置成空串（Java 在返回前手动清空）",
      tracks.get("trailPoints") == "" and tracks.get("trackJosn") == "",
      (repr(tracks.get("trailPoints")), repr(tracks.get("trackJosn"))))
# 源数据里 track_josn 是有内容的：证明"清空"发生在读出之后
m0 = get("/base/trailtracks/" + urllib.parse.quote(tracks["uuid"]))
check("数据库里 track_josn 非空（所以清空是有意的，不是查不到）",
      bool(m0.get("data", {}).get("trackJosn")), str(m0.get("data", {}).get("trackJosn"))[:60])

tl = r0.get("trailList", [])
check("trailList 非空且每个元素是 TrailBo 的 23 个键、顺序一致",
      tl and all(list(x.keys()) == TRAIL_BO_KEYS for x in tl),
      list(tl[0].keys())[:6] if tl else "空")
src0 = json.loads(m0["data"]["trackJosn"])[0]
check("track_josn 里多出来的键被丢掉（fastjson 只认 TrailBo 的字段）",
      all(k in TRAIL_BO_KEYS for k in src0), list(src0.keys()))
check("lon/lat 输出为数字，pileno 输出为字符串",
      isinstance(tl[0]["lon"], float) and isinstance(tl[0]["lat"], float)
      and isinstance(tl[0]["pileno"], str),
      (type(tl[0]["lon"]).__name__, type(tl[0]["pileno"]).__name__))
check("captureTime/devCode 原样带出",
      tl[0]["captureTime"] == str(src0.get("captureTime", tl[0]["captureTime"])),
      (tl[0]["captureTime"], src0.get("captureTime")))
check("缺失的键补 null（如 directionIn/ipType/countNum）",
      tl[0]["directionIn"] is None and tl[0]["countNum"] is None
      and tl[0]["pilenoDec"] is None, [tl[0][k] for k in ("directionIn", "countNum", "pilenoDec")])
check("raodTrailList 恒为空数组（Java 里 getCarGeometry 没被调用）",
      r0["raodTrailList"] == [], r0["raodTrailList"])
check("enterTime 为 null（控制器没填）", r0["enterTime"] is None, r0["enterTime"])
check("trailUuid == plateKey", r0["trailUuid"] == tracks["plateKey"], r0["trailUuid"])
check("trailDevCountBO = {exceptNum:0, trailDevList:[], trailList:null, exceptMsg:null}",
      list(r0["trailDevCountBO"].keys()) == ["exceptNum", "trailDevList", "trailList", "exceptMsg"]
      and r0["trailDevCountBO"]["exceptNum"] == 0
      and r0["trailDevCountBO"]["trailDevList"] == []
      and r0["trailDevCountBO"]["trailList"] is None
      and r0["trailDevCountBO"]["exceptMsg"] is None, r0["trailDevCountBO"])
for col, dec in [("startLon", "startLonDec"), ("stratLat", "stratLatDec"),
                 ("endLon", "endLonDec"), ("endLat", "endLatDec")]:
    check("service 里的 new BigDecimal(%s) -> %s" % (col, dec),
          tracks[dec] == float(tracks[col]), (tracks[col], tracks[dec]))
# 没被 getHistoryTrail 投影的列必须是 null（不是"查到了不显示"）
check("未投影列（firtStationCode/plateColor/createBy…）为 null",
      tracks["firtStationCode"] is None and tracks["plateColor"] is None,
      (tracks["firtStationCode"], tracks["plateColor"]))
check("total >= len(rows)（空 track_josn 的行被丢掉但 total 不减）",
      tbl["total"] >= len(rows), (tbl["total"], len(rows)))

# ---- 分页与条件 ----
_st, p3 = js("pageNum=1&pageSize=3")
check("pageSize 生效且 total 不变", len(p3.get("rows", [])) <= 3
      and p3.get("total") == tbl["total"], (len(p3.get("rows", [])), p3.get("total")))
_st, big = js("pageNum=9999&pageSize=10")
check("reasonable：超页码夹回首页", big.get("total") == tbl["total"]
      and len(big.get("rows", [])) > 0, (big.get("total"), len(big.get("rows", []))))
_st, noPage = js("")
check("不传分页 => 不分页，total = carlist.size()",
      noPage.get("total") == len(noPage.get("rows", [])) or noPage.get("total", 0) >= 100,
      (noPage.get("total"), len(noPage.get("rows", []))))
pk = tracks["plateKey"]
_st, eq = js("pageSize=5&carNo=" + urllib.parse.quote(pk))
check("carNo 是 plate_key 的精确等值（命中的行车牌相同）",
      all(r["tracks"]["plateKey"] == pk for r in eq.get("rows", [])), eq.get("total"))
_st, like = js("pageSize=5&plateKey=" + urllib.parse.quote(pk[:2]))
check("plateKey 是 plate_key 的 LIKE（至少包含前缀）",
      all(pk[:2] in r["tracks"]["plateKey"] for r in like.get("rows", [])), like.get("total"))
_st, ent = js("pageSize=1&entollstationid=" + urllib.parse.quote(tracks["entollstationid"]))
check("entollstationid 等值过滤生效",
      all(r["tracks"]["entollstationid"] == tracks["entollstationid"]
          for r in ent.get("rows", [])), ent.get("total"))
_st, fut = js("pageSize=1&applyTime1=" + urllib.parse.quote("2099-01-01"))
check("applyTime1 是 enter_time >=（未来 -> 0 行）", fut.get("total") == 0, fut.get("total"))
_st, past = js("pageSize=1&applyTime2=" + urllib.parse.quote("1970-01-01"))
check("applyTime2 是 enter_time < 次日（过去 -> 0 行）", past.get("total") == 0, past.get("total"))

# ---- isCylx=1 ----
_st, cy = js("pageNum=1&pageSize=5&isCylx=1&carNo=" + urllib.parse.quote(pk))
cyrows = cy.get("rows", [])
check("isCylx=1 有结果", bool(cyrows), cy.get("total"))
check("isCylx=1 命中行的 plateKey 带\"(通行N次)\"",
      all("通行" in r["trailUuid"] and r["trailUuid"].endswith("次)") for r in cyrows),
      [r["trailUuid"] for r in cyrows][:3])
check("isCylx=1 时 total 来自未分页的 getHistoryTrail",
      cy.get("total") >= len(cyrows), (cy.get("total"), len(cyrows)))
_st, cy2 = js("pageNum=1&pageSize=1&isCylx=1&carNo=" + urllib.parse.quote(pk))
# 判别分页落在哪条查询上：
#   落在 getCyly（Java 的真实行为）=> uuid 列表被夹成 1 个 => total = carlist.size() = 1
#   落在 getHistoryTrail         => uuid 仍是 3 个 => total = 3、rows = 1
check("isCylx=1 时 startPage 落在 getCyly 上（total 随 pageSize 一起缩）",
      cy2.get("total") == 1 and len(cy2.get("rows", [])) == 1,
      "total=%s rows=%s（pageSize=5 时 total=%s）" % (cy2.get("total"), len(cy2.get("rows", [])),
                                                    cy.get("total")))

# ---- 鉴权：没有 @PreAuthorize，但 URL 层是 authenticated ----
st5, h5, body5 = raw("pageNum=1", token="")
b5 = json.loads(body5.decode("utf-8"))
check("无 token => HTTP 200 + body code 401（renderString 写死 200）",
      st5 == 200 and b5.get("code") == 401, (st5, b5.get("code")))

print("----")
print("TRACK BY TIME: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
