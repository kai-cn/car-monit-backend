#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：changeTrailInfo / listFileCarNo / suspicious history/{id}

这三条端点的核心是"桩号→经纬度"的三级回退链。本机没有 roadPath 服务也没有腾讯服务，
所以链路的**降级**行为才是可观察的主体：两条出站分支一律"吞异常返回 null ⇒ 继续往下退"，
最后落在纯本地的 getCarGeometry（读 geometry 表拼区间）。这不是妥协 —— Java 在同样的
环境里就是这么跑的；把降级写成空数组或 500 才是不一致。

为了把"缓存命中"那一支也变成可观察的，脚本会直接往 Redis 塞一条 car_lxgh:<…>，
这样 ByPlanNew 不走 HTTP 就返回，连 lxbh 那个"首点 roadCode 为 null 就永久锁死成 null"
的 quirk 都能验到。

前置：
    ./build/car-monit-cpp.exe                     （默认 config/）
    python scripts/make_token.py
用法：
    python scripts/verify_trail_geo.py [port] [token]
"""
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:150] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def call(path, method="GET", body=None, raw=None):
    r = urllib.request.Request(BASE + path, method=method)
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    data = None
    if raw is not None:
        data = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        r.add_header("Content-Type", "application/json;charset=UTF-8")
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        r.add_header("Content-Type", "application/json;charset=UTF-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            txt = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, {"__raw__": e.read().decode("utf-8", "replace")[:300]}, ""
    try:
        return 200, json.loads(txt), txt
    except Exception:
        return 200, {"__raw__": txt[:300]}, txt


def redis(*args):
    s = socket.create_connection(("127.0.0.1", 6379), 5)
    out = b"*%d\r\n" % len(args)
    for a in args:
        b = a.encode() if isinstance(a, str) else a
        out += b"$%d\r\n%s\r\n" % (len(b), b)
    s.sendall(out)
    buf = s.recv(1 << 20)
    s.close()
    return buf


def mysql(sql):
    r = subprocess.run(["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot",
                        "carmonitdb", "-N", "-B", "-e", sql], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        err = "\n".join(l for l in r.stderr.decode("utf-8", "replace").splitlines()
                        if "Using a password" not in l)
        raise RuntimeError(err or out)
    return [l.split("	") for l in out.splitlines()] if out else []


# geometry 表里的真实区间，用来构造"能命中本地桩号计算"的轨迹点
G = mysql("select lxbh,qdzh,zdzh from geometry where lxfx='1' order by lxbh,qdzh limit 1")
LXBH, QD, ZD = G[0][0], int(G[0][1]), int(G[0][2])
MID_PILENO = "K%d+500" % QD          # → 归一化成 "<qd>.500"


def point(road=LXBH, pileno=MID_PILENO, dev=None, state=None, lon=None, lat=None, extra=None):
    p = {"pointUuid": "qoder-pt"}
    if road is not None:
        p["roadCode"] = road
    if pileno is not None:
        p["pileno"] = pileno
    if dev is not None:
        p["devName"] = dev
    if state is not None:
        p["stateType"] = state
    if lon is not None:
        p["lon"] = lon
    if lat is not None:
        p["lat"] = lat
    if extra:
        p.update(extra)
    return p


def tracks(**kw):
    t = {"uuid": "qoder-trail", "plateKey": "QODERGEO挂A"}
    t.update(kw)
    return t


print("\n===== PUT /manager/cartrackinfo/changeTrailInfo =====")

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT", {})
data = j.get("data") or {}
check("空 body ⇒ 6 个键、全 null（TrailInfo 没有字段初始值）",
      list(data.keys()) == ["trailUuid", "enterTime", "tracks", "trailList", "raodTrailList",
                            "trailDevCountBO"], list(data.keys()))
check("⚠️ trailList 缺失是 null 而不是 []（setter 没被调用）",
      "trailList" in data and data["trailList"] is None, data.get("trailList"))

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(), "trailList": []})
d = j["data"]
check("trailList 为空数组 ⇒ 条件 size>0 不成立 ⇒ raodTrailList/trailDevCountBO 保持 null",
      d["raodTrailList"] is None and d["trailDevCountBO"] is None,
      (d["raodTrailList"], d["trailDevCountBO"]))
keys = list(d["tracks"].keys())
check("tracks 输出 ZdataTrailTracks 全部 51 个属性（含 22 个 @TableField(exist=false)）",
      len(keys) == 51, len(keys))
check("⚠️ 拼错的字段名照抄：stratLat / firtStationCode / trackJosn / pilenoDec 位置",
      "stratLat" in keys and "firtStationCode" in keys and "trackJosn" in keys)
check("tracks.enterTime 有 @JsonFormat ⇒ 字符串；TrailInfo.enterTime 没有 ⇒ 数字",
      d["enterTime"] is None and ("enterTime" not in d["tracks"] or d["tracks"]["enterTime"] is None),
      (d["enterTime"], d["tracks"].get("enterTime")))

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(), "trailList": [point()]})
d = j["data"]
row0 = (d["trailList"] or [{}])[0]
check("pilenoDec 是 getCarGeometry 写上去的副作用 ⇒ 响应里必须有值",
      row0.get("pilenoDec") == float(QD) + 0.5, row0.get("pilenoDec"))
check("⚠️ 32 个键的 TrailBo 投影：9 个嵌套 BO 输出 null 而不是整个键少掉",
      len(row0) == 32 and "gantryCaptureBO" in row0 and row0["gantryCaptureBO"] is None, len(row0))
geo = d["raodTrailList"] or []
check("本地桩号计算命中 geometry 区间 ⇒ raodTrailList 有元素", len(geo) >= 1, len(geo))
if geo:
    g = geo[0]
    check("Geometry 输出 7 个键、声明序，未赋值的 5 个是 null",
          list(g.keys()) == ["id", "lxbh", "lxfx", "qdzh", "zdzh", "paths", "zhStr"], list(g.keys()))
    check("⚠️ paths 是**字符串**（里面是被序列化过两次的 JSON 数组），不是嵌套数组",
          isinstance(g.get("paths"), str) and g["paths"].lstrip().startswith("[["),
          str(g.get("paths"))[:60])
    check("lxbh = 路线编号", g.get("lxbh") == LXBH, g.get("lxbh"))
    inner = json.loads(g["paths"])
    check("拼接出来的点数与 geometry 区间里的点数一致（不是空数组）", len(inner) >= 1, len(inner))

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(), "trailList": [point(pileno="不是桩号")]})
check("非法桩号 ⇒ new BigDecimal 抛 NumberFormatException ⇒ 500（不是忽略该点）",
      j.get("code") == 500 and "NumberFormatException" in str(j.get("msg")), j)

# ---------------- exceptMsg / 设备分组
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(startLonDec=117.7, stratLatDec=29.2), "trailList": [point()]})
msg = (j["data"].get("trailDevCountBO") or {}).get("exceptMsg")
check("只有起点缺终点 ⇒ exceptMsg 用「终点位置」那句",
      msg == "由于无法获取轨迹终点位置，系统路线规划采用已有的轨迹点进行轨迹绘制，可能会导致部分路线丢失。",
      msg)

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(), "trailList": [point()]})
msg = (j["data"].get("trailDevCountBO") or {}).get("exceptMsg")
check("起止都缺 ⇒ 「起始位置和终点位置」", msg and "起始位置和终点位置" in msg, msg)

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(startLonDec=117.7, stratLatDec=29.2, endLonDec=117.8,
                                  endLatDec=29.3), "trailList": [point()]})
msg = (j["data"].get("trailDevCountBO") or {}).get("exceptMsg")
check("四个 Dec 都在 ⇒ exceptMsg 是空串而不是 null", msg == "", repr(msg))

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(),
                 "trailList": [point(dev="门架A", state="GantryCapture"),
                               point(dev="门架A", state="GantryCapture")]})
bo = j["data"]["trailDevCountBO"]
check("同一设备的两个门架抓拍 ⇒ 只出一个 TrailDevBO（rtnList 去重）",
      len(bo["trailDevList"]) == 1, len(bo["trailDevList"]))
check("⚠️ 但 trailList 是完整的输入列表 ⇒ 两个点都在（两个字段基数不同是设计如此）",
      len(bo["trailList"]) == 2 and len(j["data"]["trailList"]) == 2,
      (len(bo["trailList"]), len(j["data"]["trailList"])))
check("有牌识无流水 ⇒ status=1 且 exceptNum 按设备组计数",
      bo["trailDevList"][0]["status"] == "1" and bo["exceptNum"] == 1,
      (bo["trailDevList"][0]["status"], bo["exceptNum"]))
check("TrailDevBO 的键是 status/devName/trailList（Java 字段声明序）",
      list(bo["trailDevList"][0].keys()) == ["status", "devName", "trailList"],
      list(bo["trailDevList"][0].keys()))
check("⚠️ Java 字段名是 `TrailDevList`，JSON 键却是 trailDevList（getter 推导）",
      "trailDevList" in bo and "TrailDevList" not in bo, list(bo.keys()))

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(),
                 "trailList": [point(dev="门架B", state="GantryCapture"),
                               point(dev="门架B", state="FeeRecord")]})
bo = j["data"]["trailDevCountBO"]
check("同设备既有牌识又有流水 ⇒ status=0、exceptNum=0",
      bo["trailDevList"][0]["status"] == "0" and bo["exceptNum"] == 0,
      (bo["trailDevList"][0]["status"], bo["exceptNum"]))
check("分组用的 map 里两个点都在 ⇒ 该设备组的 trailList 有 2 个",
      len(bo["trailDevList"][0]["trailList"]) == 2, len(bo["trailDevList"][0]["trailList"]))

st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(),
                 "trailList": [point(dev="", state="GantryCapture"),
                               point(dev=None, state="StationCapture")]})
bo = j["data"]["trailDevCountBO"]
check("devName 为空不分组、永不计入 exceptNum；非门架/卡口类型不参与分组",
      bo["exceptNum"] == 0 and len(bo["trailDevList"]) == 2,
      (bo["exceptNum"], len(bo["trailDevList"])))

# ---------------- car_lxgh 缓存命中（不依赖外部服务）
CACHED_PATHS = "[[117.1,29.1],[117.2,29.2]]"
# ByPlanNew 的键：car_lxgh + plateKey + entollstationid + extollstationid + 点数
key_hit = "car_lxgh:QODERGEO挂ASTEN001STEX0011"
redis("DEL", key_hit)
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(entollstationid="STEN001", extollstationid="STEX001"),
                 "trailList": [point(dev="D1", state="GantryCapture")]})
first = j["data"]["raodTrailList"]
check("未命中缓存 + roadPath 服务不可达 ⇒ 降级到 ByPlan，再降级到本地桩号",
      isinstance(first, list) and len(first) >= 1, first)
check("降级过程中不写缓存（失败值不进 Redis）",
      redis("EXISTS", key_hit) == b":0\r\n", redis("EXISTS", key_hit))

redis("SET", key_hit, CACHED_PATHS)
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(entollstationid="STEN001", extollstationid="STEX001"),
                 "trailList": [point(dev="D1", state="GantryCapture")]})
hit = j["data"]["raodTrailList"]
check("缓存命中 ⇒ 单元素 [{lxbh, paths}]，paths 就是缓存里那份串",
      len(hit) == 1 and hit[0]["paths"] == CACHED_PATHS, hit)
check("命中的键格式与 Java 一致：car_lxgh + 车牌 + 入口站 + 出口站 + 点数（**无分隔符**）",
      True, key_hit)
redis("DEL", key_hit)

# lxbh 锁死成 null 的 quirk：首点 roadCode 为 null
key_null = "car_lxgh:QODERGEO挂ASTEN002STEX0022"
redis("SET", key_null, CACHED_PATHS)
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(entollstationid="STEN002", extollstationid="STEX002"),
                 "trailList": [point(road=None), point(road=LXBH)]})
hit = j["data"]["raodTrailList"]
check("⚠️ 首点 roadCode 为 null ⇒ lxbh 被置成 null 后永久锁死（第二点有路线编号也不管用）",
      len(hit) == 1 and hit[0]["lxbh"] is None, hit)
redis("DEL", key_null)

# api_map 开关
redis("SET", "sys_config:api_map", "0")
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(entollstationid="STEN001", extollstationid="STEX001"),
                 "trailList": [point()]})
check("sys_config:api_map == \"0\" ⇒ 走 ByPlan（腾讯分支），不可用仍降级到本地桩号",
      len(j["data"]["raodTrailList"]) >= 1 and
      j["data"]["raodTrailList"][0]["lxbh"] == LXBH, j["data"]["raodTrailList"])
redis("SET", "sys_config:api_map", " 1 ")
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(entollstationid="STEN001", extollstationid="STEX001"),
                 "trailList": [point()]})
check("api_map == \" 1 \"（带空白）⇒ trim 后不是 \"0\"，走本地 roadPath 分支后同样降级",
      len(j["data"]["raodTrailList"]) >= 1, j["data"]["raodTrailList"])
redis("DEL", "sys_config:api_map")

# queryLog
mysql("delete from car_query_log where query_condition like '%QODERGEO挂A%'")
st, j, _ = call("/manager/cartrackinfo/changeTrailInfo", "PUT",
                {"tracks": tracks(), "trailList": [point()]})
# create_time 只有秒级、id 又是随机 UUID ⇒ "order by create_time desc, id" 在同一秒内
# 是不确定的（一开始就撞上过另一条 changeTrailInfo {} 的记录）。按夹具车牌取，别靠时序。
log = mysql("select model_type, menu_point, user_id, query_condition from car_query_log"
            " where query_condition like '%QODERGEO挂A%' limit 1")
if log:
    mt, mp, uid, qc = (log[0] + ["", "", "", ""])[:4]
    check("queryLog 先于轨迹计算落库：model_type/menu_point 都是 \"1\"",
          mt == "1" and mp == "1", (mt, mp))
    check("⚠️ query_condition 是 fastjson2 形态：null 键整个省略（与响应的 Jackson 形态不同）",
          "trailUuid" not in qc and "tracks" in qc, qc[:120])
else:
    check("queryLog 写了 car_query_log", False, log)

# ---------------- listFileCarNo
print("\n===== GET /manager/suspicious/listFileCarNo =====")

st, j, _ = call("/manager/suspicious/listFileCarNo")
check("不传 carNo ⇒ 被强行设成 \"-1\"（查不到而不是查全表）⇒ total 0",
      j.get("total") == 0 and j.get("rows") == [], j)

CARNO = "赣AK7388"
st, j, _ = call("/manager/suspicious/listFileCarNo?carNo=" + urllib.parse.quote(CARNO))
rows = j.get("rows") or []
check("带车牌能查到行", len(rows) >= 1, len(rows))
if rows:
    r0 = rows[0]
    check("⚠️ total = rows.size()，不是数据库总数（PageInfo 拿到的是普通 ArrayList）",
          j.get("total") == len(rows), (j.get("total"), len(rows)))
    check("每行都补了 checkList 与 trailList（selectCarSuspiciousById 的形态）",
          isinstance(r0.get("checkList"), list) and isinstance(r0.get("trailList"), list)
          and len(r0["trailList"]) == 1, (len(r0.get("checkList") or []),
                                          len(r0.get("trailList") or [])))
    for k in ("chargeAmount", "totalAmount", "difAmount"):
        check("三个金额是**字符串**且带 BigDecimal 标度（累加自 checkList）",
              isinstance(r0.get(k), str) and "." in r0[k], (k, r0.get(k)))
    acc_c = acc_t = acc_d = 0
    for c in r0["checkList"]:
        acc_c += c["chargeAmount"] or 0
        acc_t += c["totalAmount"] or 0
        acc_d += c["difAmount"] or 0
    check("累加值与 checkList 一致",
          abs(float(r0["chargeAmount"]) - acc_c) < 1e-6
          and abs(float(r0["totalAmount"]) - acc_t) < 1e-6
          and abs(float(r0["difAmount"]) - acc_d) < 1e-6,
          (r0["chargeAmount"], acc_c))
    etn = r0.get("escapedTypeName")
    check("⚠️ escapedTypeName 结尾那个逗号**不删**（其他地方都会 deleteEnd）",
          etn is not None and etn.endswith(","), repr(etn))
    check("escapedTypeName 是按 escaped_type 码逐个查 label 拼出来的",
          all(x in json.dumps(mysql("select dict_label from sys_dict_data"
                                    " where dict_type='escaped_type'"), ensure_ascii=False)
              for x in (etn or "").split(",") if x), etn)

st, j, _ = call("/manager/suspicious/listFileCarNo?carNo=%s&isExcept=0&checkStatus=0"
                % urllib.parse.quote(CARNO))
check("⚠️ 调用方传的 isExcept/checkStatus 被无条件覆盖成 1 ⇒ 结果与不传时相同",
      len(j.get("rows") or []) == len(rows), (len(j.get("rows") or []), len(rows)))

st, j, _ = call("/manager/suspicious/listFileCarNo?carNo=%s&pageSize=1&pageNum=1"
               % urllib.parse.quote(CARNO))
check("pageSize=1 ⇒ total 也变成 1（分页元信息错得和 Java 一样）",
      j.get("total") == len(j.get("rows") or []) == 1, j.get("total"))

# ---------------- history/{id}
print("\n===== GET /manager/suspicious/history/{id} =====")

BID = mysql("select id from car_suspicious_back where track_josn is not null"
            " and char_length(track_josn) > 200 limit 1")[0][0]
st, j, _ = call("/manager/suspicious/history/" + urllib.parse.quote(BID))
d = j.get("data") or {}
check("备份表详情读的是 car_suspicious_back（historySpec）", bool(d.get("id")), d.get("id"))
check("by-id 的 SELECT 比列表多一列 track_josn ⇒ 该键有值",
      isinstance(d.get("trackJosn"), str) and len(d["trackJosn"]) > 200,
      len(d.get("trackJosn") or ""))
check("checkList / trailList 都补齐", isinstance(d.get("checkList"), list)
      and isinstance(d.get("trailList"), list) and len(d["trailList"]) == 1,
      (len(d.get("checkList") or []), len(d.get("trailList") or [])))
tl = (d["trailList"] or [{}])[0]
check("trailList[0] 是完整 TrailInfo（6 个键）",
      list(tl.keys()) == ["trailUuid", "enterTime", "tracks", "trailList", "raodTrailList",
                          "trailDevCountBO"], list(tl.keys()))
check("trailUuid 被覆盖成 car_suspicious 的 carNo（不是原 track_josn 里的值）",
      tl.get("trailUuid") == d.get("carNo"), (tl.get("trailUuid"), d.get("carNo")))
if tl.get("tracks") and isinstance(tl["tracks"], dict):
    check("track_josn 里的 tracks 也按 51 键投影（多余的键丢掉、缺的补 null）",
          len(tl["tracks"]) == 51, len(tl["tracks"]))

st, j, _ = call("/manager/suspicious/history/qoder-not-exist-id")
check("查不到 ⇒ selectCarSuspiciousHistoryById 返回 null ⇒ data 键整个不出现",
      "data" not in j and j.get("code") == 200, j)

# 反向证明数据源确实是备份表：用一个只存在于 car_suspicious 的 id
ONLY_MAIN = mysql("select id from car_suspicious where id not in"
                  " (select id from car_suspicious_back) limit 1")
if ONLY_MAIN:
    st, j, _ = call("/manager/suspicious/history/" + urllib.parse.quote(ONLY_MAIN[0][0]))
    check("只存在于 car_suspicious 的 id 在这条接口上查不到（表没走错）",
          "data" not in j, j)

print("\n合计 PASS=%d FAIL=%d" % (ok, bad))
sys.exit(1 if bad else 0)
