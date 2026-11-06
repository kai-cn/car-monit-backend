#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：POST /manager/suspicious/syncSuspiciousCarTask

这条接口把外部推来的轨迹（List<TrailInfo>）折算成 car_suspicious 行，
签名是 SecuritySHA1Utils.shaEncode(signatureKey + timeStamp) —— 也就是
小写十六进制的 SHA-1，脚本用 hashlib 独立算一遍，不是拿 C++ 的输出自证。

要钉住的行为（都来自 CarSuspiciousServiceImpl.syncSuspiciousCar）：
  * 三个参数任一缺失 ⇒ "参数错误"（注意是参数没给全，不是签名不对）；
  * userId 写死 1L，不是当前登录人；
  * create_time/update_time 用的是 DateUtils.getTimestampNew2() —— 那是**当前时间减 2 天**；
  * track_names = devCodes 去掉一个尾逗号，而 devCodes 里"设备编码"那段**不判重**，
    roadCode:/sectionCode: 两段才判重；
  * 收费站/门架各取 josnList 里的第一个与最后一个（switch 只收这两种 stateType）；
  * tracks 上有 entollstationid/extollstationid 时会覆盖收费站推出来的进出口；
  * 车牌命中白名单 ⇒ 整条不生成；
  * 已有 car_info ⇒ plate_color/car_type/car_vehicle 改用车库里的值，不再走字典与 envehicletype；
  * 已核实（check_status='1'）⇒ 那一行什么都不改；
  * track_josn 是 fastjson2 形态：键按名字排序、null 整个省略。

前置：./build/car-monit-cpp.exe + python scripts/make_token.py
用法：python scripts/verify_sync_suspicious.py [port] [token]
"""
import hashlib
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0
SIG_KEY = "qoder-sig-key"
PLATE = "QODERSYNC挂A"
WHITE = "QODERSYNC挂W"


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:150] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def mysql(sql):
    r = subprocess.run(["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot",
                        "carmonitdb", "-N", "-B", "-e", sql], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        err = "\n".join(l for l in r.stderr.decode("utf-8", "replace").splitlines()
                        if "Using a password" not in l)
        raise RuntimeError(err or out)
    return out


def mq(sql):
    out = mysql(sql)
    return [l.split("\t") for l in out.splitlines()] if out else []


def cnt(sql):
    v = mysql(sql)
    return int(v) if v else 0


def call(body, raw_body=None):
    r = urllib.request.Request(BASE + "/manager/suspicious/syncSuspiciousCarTask", method="POST")
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Content-Type", "application/json;charset=UTF-8")
    data = raw_body if raw_body is not None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            txt = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, {"__raw__": e.read().decode("utf-8", "replace")[:200]}
    try:
        return 200, json.loads(txt)
    except Exception:
        return 200, {"__raw__": txt[:200]}


def sign(key, ts):
    # Java: shaEncode(signatureKey + timeStamp)，Long 拼进字符串是十进制
    return hashlib.sha1((key + str(ts)).encode("utf-8")).hexdigest()


def tracks(plate=PLATE, uuid="qoder-trail-1", **kw):
    t = {"plateKey": plate, "uuid": uuid, "enaxlecount": 3, "envehicletype": "11",
         "escapedType": "20", "escapedTypeRemark": "异常原因：门架牌识数量:2",
         "entollstationid": "EN001", "entollstationname": "入口站甲",
         "extollstationid": "EX001", "extollstationname": "出口站乙",
         "enterTime": "2025-11-01 08:00:00", "exitTime": "2025-11-01 10:00:00",
         "plateColor": "蓝色", "passType": "PASS-1", "escapedTfcj": "TFCJ-9"}
    t.update(kw)
    return t


def pt(state, dev, name, road="G0321", section="S1", capture="2025-11-01 09:00:00", **kw):
    p = {"stateType": state, "devCode": dev, "devName": name,
         "roadCode": road, "sectionCode": section, "captureTime": capture}
    p.update(kw)
    return p


JOSN = [pt("StationCapture", "ST01", "收费站一"),
        pt("GantryCapture", "GN01", "门架一"),
        pt("ServiceAreaCapture", "SA01", "服务区一"),
        pt("GantryCapture", "GN02", "门架二"),
        pt("StationCapture", "ST02", "收费站二")]


def redis_cmd(*args):
    s = socket.create_connection(("127.0.0.1", 6379), 5)
    out = b"*" + str(len(args)).encode() + b"\x0d\x0a"
    for a in args:
        b = a.encode() if isinstance(a, str) else a
        out += b"$" + str(len(b)).encode() + b"\x0d\x0a" + b + b"\x0d\x0a"
    s.sendall(out)
    r = s.recv(4096)
    s.close()
    return r


def purge():
    mysql("delete from car_suspicious where car_no in ('%s','%s')" % (PLATE, WHITE))
    mysql("delete from car_info where car_no in ('%s','%s')" % (PLATE, WHITE))
    mysql("delete from car_white_info where car_no = '%s'" % WHITE)
    # 缓存里留着旧形态会让下一轮读到脏数据，两条都清掉
    for k in ("car_list", "white_car_list"):
        redis_cmd("DEL", k)


purge()
print("\n===== POST /manager/suspicious/syncSuspiciousCarTask =====")

ts = int(time.time() * 1000)
GOOD = {"signatureKey": SIG_KEY, "timeStamp": ts, "signature": sign(SIG_KEY, ts),
        "trailInfoList": [{"tracks": tracks(), "trailList": JOSN}]}

st, j = call({"trailInfoList": []})
check("三个签名参数都没给 ⇒ 参数错误", j.get("code") == 500 and j.get("msg") == "参数错误", j)

st, j = call({**GOOD, "signature": "deadbeef"})
check("签名不对 ⇒ 错误，签名验证失败！", j.get("msg") == "错误，签名验证失败！", j)

st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts, "signature": sign(SIG_KEY, ts),
              "trailInfoList": []})
check("签名对、列表空 ⇒ AjaxResult.success()（只有 msg/code，没有 data）",
      j.get("code") == 200 and "data" not in j, j)

st, j = call(GOOD)
check("签名对且有轨迹 ⇒ success", j.get("code") == 200, j)
rows = mq("select track_id, track_josn, car_no, plate_color, car_type, car_vehicle, car_num,"
          " pass_type, in_station_id, in_station, in_time, out_station_id, out_station, out_time,"
          " gantry_station_id, gantryt_station, gantry_time, out_gantry_station_id,"
          " out_gantryt_station, out_gantry_time, is_except, status, track_names, escaped_type,"
          " remark, back_col1, create_by, create_time, update_time, del_flag"
          " from car_suspicious where car_no='%s'" % PLATE)
check("生成了 1 行", len(rows) == 1, len(rows))
if rows:
    r = dict(zip([c.strip() for c in (
        "track_id track_josn car_no plate_color car_type car_vehicle car_num pass_type"
        " in_station_id in_station in_time out_station_id out_station out_time"
        " gantry_station_id gantryt_station gantry_time out_gantry_station_id"
        " out_gantryt_station out_gantry_time is_except status track_names escaped_type remark"
        " back_col1 create_by create_time update_time del_flag").split()], rows[0]))
    check("track_id/uuid 用的是 tracks.uuid", r["track_id"] == "qoder-trail-1", r["track_id"])
    check("is_except='1'、status='0'、del_flag='0'",
          r["is_except"] == "1" and r["status"] == "0" and r["del_flag"] == "0",
          (r["is_except"], r["status"], r["del_flag"]))
    check("create_by 是写死的 1，不是当前登录人", r["create_by"] == "1", r["create_by"])
    expect_day = time.strftime("%Y-%m-%d", time.localtime(time.time() - 2 * 86400))
    check("⚠️ create_time 用的是 getTimestampNew2() ⇒ 当前时间减 2 天",
          r["create_time"].startswith(expect_day), (r["create_time"], expect_day))
    check("car_num 取 tracks.enaxlecount", r["car_num"] == "3", r["car_num"])
    check("envehicletype=11 ⇒ car_type='11'、car_vehicle='2'",
          r["car_type"] == "11" and r["car_vehicle"] == "2", (r["car_type"], r["car_vehicle"]))
    pc = mq("select dict_value from sys_dict_data where dict_type='plate_color'"
            " and dict_label='蓝色'")
    check("plate_color 由中文 label 翻成码（走 selectDictDataLaleMap）",
          pc and r["plate_color"] == pc[0][0], (r["plate_color"], pc))
    check("⚠️ 进出口站被 tracks 的 entollstationid/extollstationid 覆盖（不是收费站第一个/最后一个）",
          r["in_station_id"] == "EN001" and r["in_station"] == "入口站甲"
          and r["out_station_id"] == "EX001" and r["in_time"] == "2025-11-01 08:00:00",
          (r["in_station_id"], r["out_station_id"], r["in_time"]))
    check("门架取 StationCapture/GantryCapture 之外的两类：第一个与最后一个门架",
          r["gantry_station_id"] == "GN01" and r["gantryt_station"] == "门架一"
          and r["out_gantry_station_id"] == "GN02" and r["out_gantryt_station"] == "门架二",
          (r["gantry_station_id"], r["out_gantry_station_id"]))
    tn = r["track_names"]
    check("track_names：设备段不判重、roadCode/sectionCode 段判重，结尾逗号被去掉",
          tn.count("roadCode:G0321") == 1 and tn.count("sectionCode:S1") == 1
          and tn.count("StationCapture:ST01") == 1 and not tn.endswith(","), tn)
    check("服务区那种 stateType 也照样进 devCodes（switch 里没收集，但设备编码那段不看类型）",
          "ServiceAreaCapture:SA01" in tn, tn)
    check("back_col1 = tracks.escapedTfcj、remark = escapedTypeRemark、escaped_type 只在新增时写",
          r["back_col1"] == "TFCJ-9" and r["remark"].startswith("异常原因")
          and r["escaped_type"] == "20", (r["back_col1"], r["remark"][:20], r["escaped_type"]))
    tj = json.loads(r["track_josn"])
    keys = list(tj.keys())
    check("⚠️ track_josn 是 fastjson2 形态：键按名字排序", keys == sorted(keys), keys)
    check("track_josn 里 null 键整个省略（trailUuid/enterTime 都没传）",
          "trailUuid" not in keys and "tracks" in keys and "trailList" in keys, keys)
    tk = list(tj["tracks"].keys())
    check("嵌套的 tracks 同样排序 + 丢 null", tk == sorted(tk) and "carNum" not in tk, tk)

# 再跑一次 ⇒ 命中已有行走 update 分支
st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts + 1, "signature": sign(SIG_KEY, ts + 1),
              "trailInfoList": [{"tracks": tracks(), "trailList": JOSN}]})
check("同 plateKey+uuid 再推 ⇒ 不新增行",
      cnt("select count(1) from car_suspicious where car_no='%s'" % PLATE) == 1,
      cnt("select count(1) from car_suspicious where car_no='%s'" % PLATE))

# 已核实的行不再改动
mysql("update car_suspicious set check_status='1', track_names='KEEP-ME' where car_no='%s'" % PLATE)
st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts + 2, "signature": sign(SIG_KEY, ts + 2),
              "trailInfoList": [{"tracks": tracks(), "trailList": JOSN}]})
check("⚠️ check_status='1' ⇒ 那一行整个跳过（Java 里是个空的 if 块）",
      mq("select track_names from car_suspicious where car_no='%s'" % PLATE)[0][0] == "KEEP-ME",
      mq("select track_names from car_suspicious where car_no='%s'" % PLATE))
mysql("update car_suspicious set check_status='0' where car_no='%s'" % PLATE)

# 白名单
mysql("insert into car_white_info (id,car_no,del_flag,status) values ('qodersync-w','%s','0','0')" % WHITE)
# getRedisCarWhiteList 是 cache-aside、没有失效钩子 ⇒ 插完库要把缓存清掉才会读到
redis_cmd("DEL", "white_car_list")
st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts + 3, "signature": sign(SIG_KEY, ts + 3),
              "trailInfoList": [{"tracks": tracks(plate=WHITE, uuid="qoder-trail-w"),
                                 "trailList": JOSN}]})
check("白名单车牌 ⇒ 整条不生成（getRedisCarWhiteList 命中就 continue）",
      cnt("select count(1) from car_suspicious where car_no='%s'" % WHITE) == 0,
      cnt("select count(1) from car_suspicious where car_no='%s'" % WHITE))

# car_info 存在时改用车库里的属性
mysql("insert into car_info (id,car_no,plate_color,car_type,car_vehicle,del_flag,status)"
      " values ('qodersync-car','%s','6','9','3','0','1')" % PLATE)
redis_cmd("DEL", "car_list")
st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts + 4, "signature": sign(SIG_KEY, ts + 4),
              "trailInfoList": [{"tracks": tracks(uuid="qoder-trail-2"), "trailList": JOSN}]})
# 按 track_id 取那一行，同一个车牌此时可能已经有多行
r2 = mq("select plate_color,car_type,car_vehicle from car_suspicious where track_id='qoder-trail-2'")
check("已有 car_info ⇒ plate_color/car_type/car_vehicle 改用车库里的值",
      r2 and r2[-1] == ["6", "9", "3"], r2)

# uuid 为空 / plateKey 为空 ⇒ 整条跳过
before = cnt("select count(1) from car_suspicious where car_no='%s'" % PLATE)
st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts + 5, "signature": sign(SIG_KEY, ts + 5),
              "trailInfoList": [{"tracks": tracks(uuid=""), "trailList": JOSN},
                                {"tracks": tracks(plate=""), "trailList": JOSN}]})
after = cnt("select count(1) from car_suspicious where car_no='%s'" % PLATE)
check("plateKey 或 uuid 为空 ⇒ 一行都不生成", before == after, (before, after))

# trailList 空 ⇒ 跳过
st, j = call({"signatureKey": SIG_KEY, "timeStamp": ts + 6, "signature": sign(SIG_KEY, ts + 6),
              "trailInfoList": [{"tracks": tracks(uuid="qoder-trail-3"), "trailList": []}]})
check("trailList 为空 ⇒ 跳过（不生成 track_names 全空的行）",
      cnt("select count(1) from car_suspicious where track_id='qoder-trail-3'") == 0, "0")

# 签名时间戳必须是数字原文：Java 用 Long 拼接
st, j = call(None, raw_body=json.dumps({"signatureKey": SIG_KEY, "timeStamp": ts + 7,
                                        "signature": sign(SIG_KEY, ts + 7),
                                        "trailInfoList": []}, ensure_ascii=False).encode())
check("timeStamp 以整数 JSON 字面量传来 ⇒ 签名串是十进制，不含小数点",
      j.get("code") == 200, j)

purge()
print("\n合计 PASS=%d FAIL=%d" % (ok, bad))
sys.exit(1 if bad else 0)
