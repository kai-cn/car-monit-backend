#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：PUT /manager/suspicious/check（可疑车辆核实）。

这条接口会**物理删除** car_suspicious_check 与 car_except_record 里 car_id 匹配的行，
所以脚本只用自己插入的夹具（id 前缀 qoderchk），跑完硬删干净并复核表回到原样。

最有价值的一条是回滚用例：Java 在 isExcept!="1" 且 checkList 为 null 时，
先把两张表删空、再在 for-each 上 NPE —— 靠 @Transactional 回滚。
C++ 的 Transaction 析构默认回滚、正常返回必须显式 commit，
所以"500 之后数据还在"正好把这条边界钉住。

前置：
    ./build/car-monit-cpp.exe
    python scripts/make_token.py
用法：python scripts/verify_suspicious_check.py [port] [token]
"""
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0
CID = "qoderchk-1"
CID2 = "qoderchk-2"
PLATE = "QODERCHK挂A"
PLATE2 = "QODERCHK挂B"


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
    return [l.split("\t") for l in out.splitlines()] if out else []


def cnt(sql):
    r = mysql(sql)
    return int(r[0][0]) if r else 0


def put(body):
    r = urllib.request.Request(BASE + "/manager/suspicious/check", method="PUT")
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Content-Type", "application/json;charset=UTF-8")
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            txt = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, {"__raw__": e.read().decode("utf-8", "replace")[:200]}
    try:
        return 200, json.loads(txt)
    except Exception:
        return 200, {"__raw__": txt[:200]}


def redis_get(key):
    s = socket.create_connection(("127.0.0.1", 6379), 5)
    s.sendall(b"*2\r\n$3\r\nGET\r\n$%d\r\n%s\r\n" % (len(key), key.encode()))
    buf = b""
    while True:
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
        if buf.startswith(b"$") and buf.endswith(b"\r\n") and len(buf) >= int(buf[1:buf.index(b"\r\n")]) + 6:
            break
    s.close()
    n = int(buf[1:buf.index(b"\r\n")])
    return buf[buf.index(b"\r\n") + 2: buf.index(b"\r\n") + 2 + n].decode("utf-8", "replace") if n > 0 else ""


def purge():
    for t, col in (("car_suspicious", "id"), ("car_suspicious_check", "car_id"),
                   ("car_except_record", "car_id"), ("car_info", "car_no")):
        mysql("delete from %s where %s in ('%s','%s','%s','%s')"
              % (t, col, CID, CID2, PLATE, PLATE2))
    mysql("delete from car_info where id like 'qoderchk%'")


purge()

# ------------------------------------------------------------------ 夹具
SUS_COLS = ("id, car_no, pass_type, in_station_id, in_station, in_time, gantry_station_id,"
            " gantryt_station, gantry_time, escaped_type, is_except, check_status, status,"
            " car_type, car_vehicle, car_num, plate_color, del_flag, create_time")
SUS_VALS = ("'%s','%s','PT001','IN001','入口站A','2025-11-13 18:05:51','GN001','门架B',"
            "'2025-11-13 20:56:26','20','1','0','%s','12','2','2','1','0','2025-01-01 00:00:00'")

baseline_sus = cnt("select count(1) from car_suspicious")
baseline_chk = cnt("select count(1) from car_suspicious_check")
baseline_exc = cnt("select count(1) from car_except_record")

mysql("insert into car_suspicious (%s) values (%s)" % (SUS_COLS, SUS_VALS % (CID, PLATE, "0")))
# 第二条夹具：status='1'，用来验"异常流水已追缴"那道前置判断
mysql("insert into car_suspicious (%s) values (%s)" % (SUS_COLS, SUS_VALS % (CID2, PLATE2, "1")))

print("\n===== PUT /manager/suspicious/check =====")

st, j = put({"id": "", "isExcept": "1"})
check("id 空白 ⇒「可疑车俩不存在！」（文案里的错别字是 Java 原样）",
      j.get("code") == 500 and j.get("msg") == "可疑车俩不存在！", j)

st, j = put({"id": "qoderchk-nobody", "isExcept": "1"})
check("id 查不到 ⇒ 同一句文案", j.get("msg") == "可疑车俩不存在！", j)

st, j = put({"id": CID2, "isExcept": "1"})
check("rtnVo.status == '1' ⇒ 可疑车俩异常流水已追缴！",
      j.get("msg") == "可疑车俩异常流水已追缴！", j)

st, j = put({"id": CID, "isExcept": "1", "checkList": []})
check("isExcept=1 而 checkList 为空 ⇒ 车辆逃费类型列表不能为空！",
      j.get("msg") == "车辆逃费类型列表不能为空！", j)
check("这一条在删除之前就返回 ⇒ 两张表没被动过",
      cnt("select count(1) from car_suspicious_check where car_id='%s'" % CID) == 0, "0")

# 预置旧数据，验证"物理删除"
mysql("insert into car_suspicious_check (id,car_id,car_no,escaped_type,dif_amount,del_flag)"
      " values ('qoderchk-old-1','%s','%s','99',1.00,'0')" % (CID, PLATE))
mysql("insert into car_except_record (id,car_id,car_no,dif_amount,del_flag,status)"
      " values ('qoderchk-old-2','%s','%s',1.00,'0','0')" % (CID, PLATE))
check("夹具旧行已预置",
      cnt("select count(1) from car_suspicious_check where car_id='%s'" % CID) == 1
      and cnt("select count(1) from car_except_record where car_id='%s'" % CID) == 1)

# ------------------------------------------------------------------ 回滚用例
st, j = put({"id": CID, "isExcept": "0"})   # checkList 缺失 ⇒ Java 在此 NPE
check("isExcept!=1 且 checkList 为 null ⇒ NPE 冒到全局处理器 ⇒ code 500",
      j.get("code") == 500, j)
check("⚠️ @Transactional 回滚：删除已经执行过，但 500 之后旧行还在",
      cnt("select count(1) from car_suspicious_check where id='qoderchk-old-1'") == 1
      and cnt("select count(1) from car_except_record where id='qoderchk-old-2'") == 1,
      (cnt("select count(1) from car_suspicious_check where car_id='%s'" % CID),
       cnt("select count(1) from car_except_record where car_id='%s'" % CID)))

# ------------------------------------------------------------------ 正向用例
CHECKS = [
    {"escapedType": "20", "totalAmount": 200.00, "chargeAmount": 100.00, "difAmount": 100.00,
     "attachments": "f1", "remark": "r1"},
    {"escapedType": "10", "totalAmount": 45.00, "chargeAmount": 23.00, "difAmount": 22.00,
     "remark": "r2"},
]
st, j = put({"id": CID, "carNo": PLATE, "isExcept": "1", "checkList": CHECKS,
             "exceptRemark": "核实备注", "exceptFileIds": "a,b", "carType": "11",
             "carVehicle": "2", "carNum": 2, "plateColor": "0", "escapedType": "20,10",
             "passType": "PT-NEW", "remark": "整体备注"})
check("正向核实 ⇒ msg=操作成功！、data=请求里的 id",
      j.get("code") == 200 and j.get("msg") == "操作成功！" and j.get("data") == CID, j)

chk = mysql("select car_id,car_no,suspicous_flag,escaped_type,dif_amount,id from"
            " car_suspicious_check where car_id='%s' order by escaped_type" % CID)
# 上面 select 的列顺序就是下面用到的下标，别改这条 SQL 的列序
check("⚠️ 预置的旧核实记录被物理删除，替换为请求里的 2 条",
      len(chk) == 2 and not any(r[0] == "qoderchk-old-1" for r in chk), chk)
check("saveBatch 前 Java 给每行补了 carId/carNo/suspicousFlag",
      all(r[1] == PLATE and r[2] == "1" for r in chk), chk)
check("id 是 MP ASSIGN_UUID 补的 32 位无横线串（客户端没传 id）",
      all(len(r[5]) == 32 for r in chk), [r[5] for r in chk])

exc = mysql("select car_id,car_no,out_station_id,out_station,out_time,in_station,in_time,"
            "status,total_amount,charge_amount,dif_amount,escaped_type,pass_type"
            " from car_except_record where car_id='%s' order by escaped_type" % CID)
check("异常流水同步生成 2 条", len(exc) == 2, len(exc))
if len(exc) == 2:
    r = exc[0]
    check("⚠️ 流水的「出口」三列取的是可疑车辆的门架三列（列名换成 out_*）",
          r[2] == "GN001" and r[3] == "门架B" and r[4] == "2025-11-13 20:56:26", r[2:5])
    check("「入口」三列取的是车辆自身的入口站与通行时间",
          r[5] == "入口站A" and r[6] == "2025-11-13 18:05:51", r[5:7])
    check("pass_type 来自 rtnVo（不是请求里新传的那个）", r[12] == "PT001", r[12])
    check("status 恒为 '0'（未补缴）", r[7] == "0", r[7])
    check("金额逐列从 check 搬过来",
          float(r[8]) == 45.00 and float(r[9]) == 23.00 and float(r[10]) == 22.00, r[8:11])

car = mysql("select car_no,car_type,car_num,car_vehicle,plate_color,escaped_amount,escaped_type,"
            "del_flag,create_by,eps_id from car_info where car_no='%s'" % PLATE)
# 列序：0 car_no 1 car_type 2 car_num 3 car_vehicle 4 plate_color 5 escaped_amount
#       6 escaped_type 7 del_flag 8 create_by 9 eps_id
check("重点车辆库里没有这个车牌 ⇒ 新插一行", len(car) == 1, car)
if car:
    c = car[0]
    check("新行的 escaped_amount = Σ difAmount = 100.00+22.00 = 122.00（decimal(19,2)）",
          float(c[5]) == 122.00, c[5])
    check("car_type/car_num/car_vehicle/plate_color/escaped_type 都取自请求，不是 rtnVo",
          c[1] == "11" and int(c[2]) == 2 and c[3] == "2" and c[4] == "0" and c[6] == "20,10",
          c[1:6])
    check("del_flag='0' + create_by/eps_id 都补了",
          c[7] == "0" and c[8] not in (None, "") and c[9] not in (None, ""), c[7:10])

upd = mysql("select check_status,is_except,except_remark,except_file_ids,pass_type,car_no,"
            "car_type,plate_color,remark,update_time,create_time"
            " from car_suspicious where id='%s'" % CID)[0]
check("check_status 被置成 '1'", upd[0] == "1", upd[0])
check("is_except / except_remark / remark 用请求里的值覆盖",
      upd[1] == "1" and upd[2] == "核实备注" and upd[8] == "整体备注", upd[1:3] + [upd[8]])
check("⚠️ pass_type 被请求里的新值覆盖（流水那侧仍用旧值）",
      upd[4] == "PT-NEW", upd[4])
check("isExcept=='1' ⇒ except_file_ids 保持请求值（不是空串）",
      upd[3] == "a,b", upd[3])
# ⚠️ CarSuspicious 的父类是 BasePlusEntityLong —— 它**没有** fill = FieldFill.UPDATE，
# 所以 MP 的 updateById 不补 update_by/update_time（car_except_record 那种 BasePlusEntity 才有）。
# 两个审计列都得保持原样；一开始我以为这里应该看到 update_time 变化，是搞错了父类。
check("car_suspicious 父类无 fill ⇒ updateById 既不写 create_time 也不写 update_time",
      upd[10].startswith("2025-01-01 00:00:00") and upd[9] == "NULL", (upd[10], upd[9]))

cache = redis_get("car_list")
check("核实成功后刷了 Redis 车辆缓存（fastjson2 形态里能看到新车牌）",
      PLATE in cache and '"@type":"com.ruoyi.manager.domain.CarInfo"' in cache, PLATE)

# ------------------------------------------------------------------ isExcept=0 分支
mysql("insert into car_suspicious_check (id,car_id,car_no,escaped_type,dif_amount,del_flag)"
      " values ('qoderchk-old-3','%s','%s','99',1.00,'0')" % (CID, PLATE))
st, j = put({"id": CID, "carNo": PLATE, "isExcept": "0", "exceptFileIds": "x,y",
             "checkList": CHECKS, "carType": "11", "carVehicle": "2", "carNum": 2})
check("isExcept=0 也返回操作成功", j.get("msg") == "操作成功！", j)
check("⚠️ isExcept!=1 ⇒ 一条核实/异常流水都不写：预置行被物理删除且不补回",
      cnt("select count(1) from car_suspicious_check where car_id='%s'" % CID) == 0
      and cnt("select count(1) from car_except_record where car_id='%s'" % CID) == 0,
      (cnt("select count(1) from car_suspicious_check where car_id='%s'" % CID),
       cnt("select count(1) from car_except_record where car_id='%s'" % CID)))
upd0 = mysql("select concat('[', except_file_ids, ']'),check_status from car_suspicious"
             " where id='%s'" % CID)[0]
check("⚠️ isExcept=='0' ⇒ except_file_ids 被强制写成空串",
      upd0[0] == "[]" and upd0[1] == "1", upd0)

# ------------------------------------------------------------------ 已有车不再插
before = cnt("select count(1) from car_info where car_no='%s'" % PLATE)
st, j = put({"id": CID, "carNo": PLATE, "isExcept": "1", "checkList": CHECKS[:1],
             "carType": "11", "carVehicle": "2", "carNum": 2})
check("车牌已在重点车辆库 ⇒ 不再插第二行",
      cnt("select count(1) from car_info where car_no='%s'" % PLATE) == before, before)

purge()
check("清理后三张表回到跑前状态",
      cnt("select count(1) from car_suspicious") == baseline_sus
      and cnt("select count(1) from car_suspicious_check") == baseline_chk
      and cnt("select count(1) from car_except_record") == baseline_exc,
      (cnt("select count(1) from car_suspicious"), baseline_sus,
       cnt("select count(1) from car_suspicious_check"), baseline_chk,
       cnt("select count(1) from car_except_record"), baseline_exc))

print("\n合计 PASS=%d FAIL=%d" % (ok, bad))
sys.exit(1 if bad else 0)
