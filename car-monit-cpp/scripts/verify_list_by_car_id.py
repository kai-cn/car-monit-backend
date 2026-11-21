#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：GET /manager/cartrackinfo/listByCarId 与 GET /manager/cartrackinfo/carSnapShot

这两条是 manager 里仅剩的"要打通外部接口"的轨迹入口，Java 侧的形态是：

  listByCarId —— 先查本地 zdata_trail_tracks（carNo 兜成 "-1" 保证不会全表扫），
      本地**一行都没有**才回退 HttpSysUtilApiService.carTrackQueryByCarNo；
      回退命中时这个 GET 会写库：先 removeRealData(请求车牌) 再 saveBatch(远程回来的 tracks)。
      注意"判空"用的是 DB 行数而不是展开后的 rows —— track_josn 全空的行进不了 rows，
      但照样算"有数据"，于是远程回退不会触发。这一条只有实机能分辨。

  carSnapShot —— stateType 与 pointUuid 不齐就直接返回没有 data 的 success；
      齐了就把**整个 TrailBo 拍平成 query string** 打给上游（null 省略、按声明序、
      BigDecimal 保住标度、空串也带上）。

脚本自己起一个假上游（Forest 的两个路径），所以 C++ 服务要这么启：

    CM_VEHICLEMONITOR_BASEURL=http://127.0.0.1:19124 ./build/car-monit-cpp.exe

用法：python scripts/verify_list_by_car_id.py [port] [token]
"""
import json
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9991
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT
UP_PORT = 19124

PLATE_LOCAL = "QODER挂L"      # 2 行有 track_josn + 1 行 NULL
PLATE_BLANK = "QODER挂B"      # 只有 track_josn 为 NULL 的行
PLATE_MISS = "QODER挂N"       # 本地没有 ⇒ 走远程
PLATE_REMOTE = "QODER挂R"     # 远程返回的车牌（跟请求车牌不一样，正好验到删除用的是请求车牌）

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:150] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def call(path, query=""):
    r = urllib.request.Request("%s%s?%s" % (BASE, path, query))
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            txt = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
    try:
        return json.loads(txt)
    except Exception:
        return {"__raw__": txt[:300]}


def mysql(sql):
    r = subprocess.run(["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot",
                        "carmonitdb", "-N", "-B", "-e", sql], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        err = "\n".join(l for l in r.stderr.decode("utf-8", "replace").splitlines()
                        if "Using a password" not in l)
        raise RuntimeError(err or out)
    return [l.split("\t") for l in out.splitlines()] if out else []


def cnt(sql):
    rows = mysql(sql)
    return int(rows[0][0]) if rows and rows[0] else 0


# ------------------------------------------------------------------ 假上游
UP = {"status": 200, "body": "{}", "requests": []}


class UpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        UP["requests"].append(self.path)
        body = UP["body"].encode("utf-8")
        self.send_response(UP["status"])
        self.send_header("Content-Type", "application/json;charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def up_reset(payload=None, status=200, raw=None):
    UP["requests"] = []
    UP["status"] = status
    UP["body"] = raw if raw is not None else json.dumps(payload, ensure_ascii=False)


def up_query_of(idx=0):
    return urllib.parse.urlparse(UP["requests"][idx]).query


try:
    srv = HTTPServer(("127.0.0.1", UP_PORT), UpHandler)
except OSError as e:
    print("SKIP  假上游端口 %d 起不来（%s）——远程分支无法验证" % (UP_PORT, e))
    sys.exit(0)
threading.Thread(target=srv.serve_forever, daemon=True).start()

# ------------------------------------------------------------------ 夹具
JOSON = json.dumps([
    {"pointUuid": "qoder-pt-1", "lon": 116.4321, "lat": 39.9, "captureTime": "2026-11-01 10:00:00",
     "pileno": "K12+345", "roadCode": "QODER", "extraKeyNotOnTrailBo": "丢掉"},
    {"pointUuid": "qoder-pt-2", "lon": 116.5, "directionIn": True, "countNum": 3},
], ensure_ascii=False)


def cleanup():
    mysql("delete from zdata_trail_tracks where plate_key in ('%s','%s','%s','%s','-1')"
          % (PLATE_LOCAL, PLATE_BLANK, PLATE_MISS, PLATE_REMOTE))


def insert_row(uuid, plate, josn, enter="2026-11-01 10:00:00"):
    j = ("'%s'" % josn) if josn is not None else "NULL"
    mysql("insert into zdata_trail_tracks (uuid, plate_key, track_josn, enter_time, point_count)"
          " values ('%s','%s',%s,'%s',2)" % (uuid, plate, j, enter))


cleanup()
insert_row("qoder-lbic-1", PLATE_LOCAL, JOSON, "2026-11-01 10:00:00")
insert_row("qoder-lbic-2", PLATE_LOCAL, JOSON, "2026-11-02 10:00:00")
insert_row("qoder-lbic-3", PLATE_LOCAL, None, "2026-11-03 10:00:00")
insert_row("qoder-lbic-4", PLATE_BLANK, None, "2026-11-01 10:00:00")

TRAIL_INFO_KEYS = ["trailUuid", "enterTime", "tracks", "trailList", "raodTrailList",
                   "trailDevCountBO"]
TRAIL_BO_KEYS = ["pointUuid", "stateType", "pointFlag", "pointJosn",
                 "borderWeighingCaptureBO", "gantryCaptureBO", "provCaptureBO",
                 "stationCapture", "feeRecord", "feeStationEnter", "feeStationExit",
                 "captureTime", "directionIn", "locationCode", "locationFlag", "ipType",
                 "locationJosn", "gantryIpBO", "stationIpBO",
                 "devCode", "devName", "imagesArry", "lon", "lat", "roadCode", "sectionCode",
                 "direction", "pileno", "preCaptureTime", "countNum", "pilenoDec", "isQuery"]

# ------------------------------------------------------------------ 本地分支
up_reset()
tbl = call("/manager/cartrackinfo/listByCarId",
           "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_LOCAL))
check("手搭 TableDataInfo：键序 total,rows,code,msg + 200/查询成功",
      list(tbl.keys()) == ["total", "rows", "code", "msg"] and tbl.get("code") == 200
      and tbl.get("msg") == "查询成功", list(tbl.keys()))
rows = tbl.get("rows", [])
check("total 是 DB 行数(3)、rows 只有 track_josn 非空的两行",
      tbl.get("total") == 3 and len(rows) == 2, (tbl.get("total"), len(rows)))
check("本地命中就**不**打上游（一条请求都没有）", UP["requests"] == [], UP["requests"])
check("TrailInfo 键序照声明序", list(rows[0].keys()) == TRAIL_INFO_KEYS, list(rows[0].keys()))
check("trailUuid = plateKey、enterTime = null、raodTrailList = []",
      rows[0]["trailUuid"] == PLATE_LOCAL and rows[0]["enterTime"] is None
      and rows[0]["raodTrailList"] == [],
      (rows[0]["trailUuid"], rows[0]["enterTime"]))
check("trailList 是 32 键的 TrailBo，未声明的键被丢掉",
      all(list(x.keys()) == TRAIL_BO_KEYS for x in rows[0]["trailList"])
      and "extraKeyNotOnTrailBo" not in rows[0]["trailList"][0],
      list(rows[0]["trailList"][0].keys())[:5])
check("本地分支把 trailPoints/trackJosn 清空",
      rows[0]["tracks"]["trailPoints"] == "" and rows[0]["tracks"]["trackJosn"] == "",
      (rows[0]["tracks"]["trailPoints"], rows[0]["tracks"]["trackJosn"][:30]))

# 分页落在哪：这条是本地单查询，pageNum 直接决定行数
tbl2 = call("/manager/cartrackinfo/listByCarId",
            "pageNum=1&pageSize=1&carNo=" + urllib.parse.quote(PLATE_LOCAL))
# enter_time 最新的那行（qoder-lbic-3）恰好是 track_josn 为 NULL 的 ⇒ 分页后只剩它，
# 展开后被丢掉。rows 空但 total 仍是 3，这正是"total 不跟着展开减"的形态。
check("pageSize=1 只捞到 NULL 那行 ⇒ rows=[]、total 仍是 3",
      tbl2.get("rows") == [] and tbl2.get("total") == 3,
      (tbl2.get("rows"), tbl2.get("total")))
tbl2b = call("/manager/cartrackinfo/listByCarId",
             "pageNum=2&pageSize=1&carNo=" + urllib.parse.quote(PLATE_LOCAL))
check("翻到第二页就拿出一行（分页确实落在 DB 上，不是内存切片）",
      len(tbl2b.get("rows", [])) == 1 and tbl2b.get("total") == 3,
      (len(tbl2b.get("rows", [])), tbl2b.get("total")))

# ---- 判别"本地有行但 track_josn 全空"：这不算空，不能回退 ----
up_reset()
tbl3 = call("/manager/cartrackinfo/listByCarId",
            "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_BLANK))
check("track_josn 全空 ⇒ rows 为空但 total=1，且**不**回退远程（判的是 carlist.size()）",
      tbl3.get("rows") == [] and tbl3.get("total") == 1 and UP["requests"] == [],
      (tbl3.get("rows"), tbl3.get("total"), UP["requests"]))

# ---- 车牌兜底：空白 -> "-1"（所以必然查不到）----
up_reset({"code": 200, "msg": "查询成功", "total": 0, "rows": []})
for q in ["pageNum=1&pageSize=10", "pageNum=1&pageSize=10&carNo=",
          "pageNum=1&pageSize=10&carNo=%20%20"]:
    call("/manager/cartrackinfo/listByCarId", q)
check("carNo 缺失/空白一律兜成 \"-1\" 再打远程（trim 之后才算空白）",
      len(UP["requests"]) == 3
      and all(urllib.parse.parse_qs(up_query_of(i)).get("carNo") == ["-1"] for i in range(3)),
      [up_query_of(i) for i in range(len(UP["requests"]))])

# ------------------------------------------------------------------ 远程分支
remote_row = {
    "trailUuid": "qoder-remote-uuid",
    "enterTime": "2026-11-05 08:30:00",
    "tracks": {
        "uuid": "qoder-remote-1", "plateKey": "  " + PLATE_REMOTE + " ",
        "enterTime": "2026-11-05 08:30:00", "exitTime": "2026-11-05 09:30:00",
        "startLon": "116.40", "endLat": "39.100",
        "remoteOnlyField": "实体上没有这个属性",
    },
    "trailList": [{"pointUuid": "rp-1", "lon": "116.500", "pileno": "K1+000", "zzz": 1},
                  {"pointUuid": "rp-2"}],
    "raodTrailList": [["不该保留", 1]],
    "trailDevCountBO": {"exceptNum": 9, "trailDevList": [{"a": 1}],
                        "trailList": [{"x": 1}], "exceptMsg": "不该保留"},
}
up_reset({"code": 200, "msg": "查询成功", "total": 7, "rows": [remote_row]})
tbl4 = call("/manager/cartrackinfo/listByCarId",
            "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_MISS))
check("本地为空 ⇒ 真的打了 /base/sysutil/carTrackQueryByCarNo",
      UP["requests"] and UP["requests"][0].startswith("/base/sysutil/carTrackQueryByCarNo?"),
      UP["requests"])
qs = up_query_of(0)
check("CarParaVO 拍平：只带非 null 属性、声明序 carNo→pageNum→pageSize",
      qs == "carNo=%s&pageNum=1&pageSize=20" % urllib.parse.quote(PLATE_MISS), qs)
r4 = tbl4.get("rows", [])
check("回退命中后 total 换成远程的 total", tbl4.get("total") == 7 and len(r4) == 1,
      (tbl4.get("total"), len(r4)))
check("TrailInfo 键序不变、trailUuid/enterTime 来自远程",
      list(r4[0].keys()) == TRAIL_INFO_KEYS
      and r4[0]["trailUuid"] == "qoder-remote-uuid",
      (list(r4[0].keys()), r4[0]["trailUuid"]))
check("enterTime 是 TrailInfo 那份（无 @JsonFormat ⇒ epoch 毫秒数字）",
      isinstance(r4[0]["enterTime"], int) and r4[0]["enterTime"] > 1700000000000,
      r4[0]["enterTime"])
t4 = r4[0]["tracks"]
check("tracks 里远程多出来的键被丢掉（fastjson 先转成实体）",
      "remoteOnlyField" not in t4, list(t4.keys())[:5])
check("plateKey 过了 isNull ⇒ 两头空格被 trim 掉",
      t4["plateKey"] == PLATE_REMOTE, repr(t4["plateKey"]))
check("回退分支**不**清空 trailPoints（跟本地分支不一样）",
      t4["trailPoints"] is None, repr(t4["trailPoints"]))
check("trackJosn 是 fastjson2 形态：按字段名排序 + null 省略（实机对拍 2.0.43）",
      t4["trackJosn"] == '[{"lon":116.5,"pileno":"K1+000","pointUuid":"rp-1"},'
                         '{"pointUuid":"rp-2"}]', t4["trackJosn"])
# ⚠️ 已知差异：Java 把 "116.500" 转成 BigDecimal 后 toJSONString 仍是 116.500（标度保留），
# C++ 的 JSON 数值只有 double ⇒ 写成 116.5。见 FINAL_DIFFERENCES 的 BigDecimal 标度那一行。
check("⚠️ 同一个值：BigDecimal 标度在 C++ 侧丢掉（116.500 → 116.5）",
      "116.500" not in t4["trackJosn"], t4["trackJosn"])
check("pointCount = 轨迹点数", t4["pointCount"] == 2, t4["pointCount"])
check("raodTrailList / trailDevCountBO 被控制器覆盖成空壳",
      r4[0]["raodTrailList"] == []
      and r4[0]["trailDevCountBO"] == {"exceptNum": 0, "trailDevList": [],
                                       "trailList": None, "exceptMsg": None},
      (r4[0]["raodTrailList"], r4[0]["trailDevCountBO"]))
check("trailList 投影成 32 键（zzz 被丢掉）",
      list(r4[0]["trailList"][0].keys()) == TRAIL_BO_KEYS,
      list(r4[0]["trailList"][0].keys())[:4])
# ---- 读接口的写副作用：删的是**请求**车牌，插的是**远程**车牌 ----
check("saveBatch 把远程 tracks 落库（uuid 沿用远程给的）",
      cnt("select count(1) from zdata_trail_tracks where uuid='qoder-remote-1'"
          " and plate_key='%s'" % PLATE_REMOTE) == 1,
      mysql("select uuid,plate_key,point_count from zdata_trail_tracks"
            " where uuid='qoder-remote-1'"))
josn_col = mysql("select track_josn from zdata_trail_tracks where uuid='qoder-remote-1'")
check("落库的 track_josn 与响应里那份一致（同一个字符串）",
      josn_col and josn_col[0][0] == t4["trackJosn"], josn_col[:1])
check("removeRealData 删的是请求车牌而不是远程车牌（这里是两个不同的值）",
      cnt("select count(1) from zdata_trail_tracks where plate_key='%s'" % PLATE_MISS) == 0
      and cnt("select count(1) from zdata_trail_tracks where plate_key='%s'" % PLATE_REMOTE) == 1,
      (cnt("select count(1) from zdata_trail_tracks where plate_key='%s'" % PLATE_MISS),
       cnt("select count(1) from zdata_trail_tracks where plate_key='%s'" % PLATE_REMOTE)))

# 二次调用：现在本地有行了 ⇒ 不再回退
up_reset()
call("/manager/cartrackinfo/listByCarId",
     "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_REMOTE))
check("落库之后再查同一车牌就走本地（副作用可观察）", UP["requests"] == [], UP["requests"])

# ---- 远程返回空 rows ⇒ 不写库、total 保持 PageInfo 的 0 ----
cleanup()
up_reset({"code": 200, "msg": "查询成功", "total": 99, "rows": []})
tbl5 = call("/manager/cartrackinfo/listByCarId",
            "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_MISS))
check("远程 rows 为空 ⇒ rows=[]、total=0（不是远程的 99），且不落库",
      tbl5.get("rows") == [] and tbl5.get("total") == 0
      and cnt("select count(1) from zdata_trail_tracks where plate_key='%s'" % PLATE_MISS) == 0,
      (tbl5.get("rows"), tbl5.get("total")))

# ---- 远程 rows 里没有 tracks ⇒ Java 是 NPE ⇒ 500 ----
up_reset({"code": 200, "msg": "查询成功", "total": 1, "rows": [{"trailUuid": "x"}]})
tbl6 = call("/manager/cartrackinfo/listByCarId",
            "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_MISS))
check("远程行缺 tracks ⇒ NPE 形态：HTTP 200 + code 500",
      tbl6.get("code") == 500 and "data" not in tbl6, tbl6)

# ---- 上游 5xx 且不是 TableDataInfo 形态 ----
up_reset(raw="<html>borken</html>", status=500)
tbl7 = call("/manager/cartrackinfo/listByCarId",
            "pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(PLATE_MISS))
check("上游响应体不是 JSON ⇒ 解析异常照样是 code 500（没有静默空列表）",
      tbl7.get("code") == 500, tbl7)

# ------------------------------------------------------------------ carSnapShot
up_reset()
j = call("/manager/cartrackinfo/carSnapShot", "pointUuid=p-1")
check("缺 stateType ⇒ success() 只有 msg/code，没有 data",
      list(j.keys()) == ["msg", "code"] and j.get("code") == 200, j)
j = call("/manager/cartrackinfo/carSnapShot", "stateType=1")
check("缺 pointUuid ⇒ 同样只有 msg/code", list(j.keys()) == ["msg", "code"], j)
j = call("/manager/cartrackinfo/carSnapShot", "stateType=%20&pointUuid=p-1")
check("stateType 是空白也算缺（isNull 会 trim，trim 后仍 blank）",
      list(j.keys()) == ["msg", "code"] and UP["requests"] == [], (j, UP["requests"]))

up_reset({"pointUuid": "p-1", "stateType": "1", "lon": 116.4321, "lat": 39.9,
          "directionIn": True, "countNum": 2, "pilenoDec": 1.5, "whatever": "drop me"})
j = call("/manager/cartrackinfo/carSnapShot",
         "stateType=1&pointUuid=p-1&lon=116.500&directionIn=true&isQuery=")
check("两个条件齐 ⇒ 打 /base/sysutil/getByTrailBo",
      UP["requests"] and UP["requests"][0].startswith("/base/sysutil/getByTrailBo?"),
      UP["requests"])
q = up_query_of(0)
check("TrailBo 拍平按声明序、null 省略",
      q.startswith("pointUuid=p-1&stateType=1&directionIn=true&lon=116.500&isQuery"), q)
check("BigDecimal 标度原样带上（116.500 不能变 116.5）", "lon=116.500" in q, q)
check("空串参数照样带上（值的形式与 Forest 略有差，见差异表）", "isQuery" in q, q)
data = j.get("data", {})
check("响应 data 是 TrailBo 的 32 键、顺序按声明序",
      list(data.keys()) == TRAIL_BO_KEYS, list(data.keys())[:6])
check("上游多出来的键被丢掉、没给的补 null",
      "whatever" not in data and data["devCode"] is None and data["sectionCode"] is None,
      (data.get("devCode"), data.get("sectionCode")))
check("上游给了的键照样带出（pilenoDec=1.5 不能被当成缺省）",
      data["pilenoDec"] == 1.5, data.get("pilenoDec"))
check("directionIn/countNum/lon 按声明类型转换",
      data["directionIn"] is True and data["countNum"] == 2 and data["lon"] == 116.4321,
      (data["directionIn"], data["countNum"], data["lon"]))

# 上游返 null（空响应体）⇒ success((Object)null) ⇒ 仍然没有 data
up_reset(raw="")
j = call("/manager/cartrackinfo/carSnapShot", "stateType=1&pointUuid=p-1")
check("上游空响应体 ⇒ Forest 解出 null ⇒ 没有 data 键", list(j.keys()) == ["msg", "code"], j)

# 上游返 AjaxResult 信封（真实环境更可能是这样）⇒ 32 个键全 null
up_reset({"code": 200, "msg": "操作成功", "data": {"pointUuid": "p-1"}})
j = call("/manager/cartrackinfo/carSnapShot", "stateType=1&pointUuid=p-1")
check("上游返信封而不是 TrailBo 本体 ⇒ 按声明序输出 32 个 null",
      list(j.get("data", {}).keys()) == TRAIL_BO_KEYS
      and all(v is None for v in j["data"].values()), j.get("data", {}).get("pointUuid"))

# 参数绑定失败发生在进方法之前 ⇒ 连上游都不该打
up_reset({"pointUuid": "p"})
j = call("/manager/cartrackinfo/carSnapShot", "stateType=1&pointUuid=p-1&lon=abc")
check("lon=abc ⇒ 绑定阶段就失败（BindException 形态），不打上游",
      j.get("code") == 500 and UP["requests"] == [] and "convert" in str(j.get("msg", "")),
      (j, UP["requests"]))
j = call("/manager/cartrackinfo/carSnapShot", "stateType=1&pointUuid=p-1&directionIn=maybe")
check("布尔属性给非法字面量 ⇒ 同样是绑定失败",
      j.get("code") == 500 and UP["requests"] == [], (j, UP["requests"]))

# ------------------------------------------------------------------ 鉴权
r = urllib.request.Request("%s/manager/cartrackinfo/listByCarId?pageNum=1" % BASE)
try:
    with urllib.request.urlopen(r, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        st = resp.status
except urllib.error.HTTPError as e:
    st = e.code
    body = json.loads(e.read().decode("utf-8"))
check("两条接口都没有 @PreAuthorize，但 URL 层仍是 authenticated ⇒ 无 token 401",
      st == 200 and body.get("code") == 401, (st, body.get("code")))

cleanup()
srv.shutdown()
print("----")
print("LIST BY CAR ID: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
