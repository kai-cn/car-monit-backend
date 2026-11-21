#!/usr/bin/env python3
# 大屏剩余 3 条接口（carStatistics / carWarning / exceptRecordList）的端到端验证。
# carWarning 需要"今天 + 在线车辆"的预警行，脚本自己造、自己清，并顺手验证缓存与告警规则链路。
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9991
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT

ok = bad = 0


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:220] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:280])


def api(path, method="GET", body=None):
    r = urllib.request.Request(BASE + path, method=method)
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        r.add_header("Content-Type", "application/json;charset=UTF-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode("utf-8", "replace")[:200]}


# ---- 极简 RESP 客户端（只为造/清缓存键，不引第三方库）----
class Redis:
    def __init__(self, host="127.0.0.1", port=6379, db=0):
        self.s = socket.create_connection((host, port), timeout=10)
        self.f = self.s.makefile("rb")   # 复用同一个缓冲，逐条读才不会错位
        self._cmd("SELECT", db)

    def _cmd(self, *args):
        out = b"*%d\r\n" % len(args)
        for a in args:
            if isinstance(a, int):
                a = str(a)
            if not isinstance(a, bytes):
                a = a.encode("utf-8")
            out += b"$%d\r\n" % len(a) + a + b"\r\n"
        self.s.sendall(out)
        return self._read()

    def _read(self):
        f = self.f
        line = f.readline()
        if not line:
            return None
        t, rest = line[:1], line[1:].strip()
        if t == b"+":
            return rest.decode()
        if t == b"-":
            return {"err": rest.decode()}
        if t == b":":
            return int(rest)
        if t == b"$":
            n = int(rest)
            if n < 0:
                return None
            data = f.read(n)
            f.read(2)
            return data.decode("utf-8", "replace")
        if t == b"*":
            n = int(rest)
            return [self._read() for _ in range(n)]
        return rest.decode()

    def get(self, k):
        return self._cmd("GET", k)

    def set(self, k, v):
        return self._cmd("SET", k, v)

    def delete(self, *ks):
        return self._cmd("DEL", *ks)

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


try:
    rd = Redis()
except Exception as e:  # Redis 不在线就跳过缓存相关断言
    rd = None
    print("SKIP  Redis 不可用：%s" % e)

TODAY = time.strftime("%Y%m%d")
NOW = time.strftime("%Y-%m-%d %H:%M:%S")

# ================= 1) carStatistics =================
j = api("/manager/bigScreen/carStatistics")
data = j.get("data")
check("carStatistics 是 AjaxResult.success(数组)", j.get("code") == 200 and isinstance(data, list), j)
if isinstance(data, list) and data:
    keys = list(data[0].keys())
    check("CarStatisticsVO 声明序 escapedType, escapedTypeName, number, escapedAmount",
          keys == ["escapedType", "escapedTypeName", "number", "escapedAmount"], keys)
    check("escapedTypeName 恒为 null（SQL 未投影）", all(x.get("escapedTypeName") is None for x in data),
          data[0])
    check("number/escapedAmount 是数字（Java 默认 0 / ZERO）",
          all(isinstance(x.get("number"), int) and isinstance(x.get("escapedAmount"), (int, float)) for x in data),
          data[0])
    total_num = sum(x["number"] for x in data)
    lst = api("/manager/exceptrecord/list?pageNum=1&pageSize=1")
    check("聚合的车数与异常表同源（<= total）", total_num <= (lst.get("total") or 0),
          "number合计=%s, 异常总数=%s" % (total_num, lst.get("total")))
    # 过滤条件：带一个不可能的 escapedType 应该返回空数组
    jf = api("/manager/bigScreen/carStatistics?escapedType=" + urllib.parse.quote("__没有这个类型__"))
    check("escapedType 条件生效（空结果）", isinstance(jf.get("data"), list) and not jf.get("data"), jf)
else:
    check("carStatistics 有数据可测", False, j)

# ================= 2) exceptRecordList =================
e = api("/manager/bigScreen/exceptRecordList?pageNum=1&pageSize=2")
check("exceptRecordList 是 TableDataInfo（total/rows/code/msg）",
      all(k in e for k in ("total", "rows", "code", "msg")) and e.get("code") == 200,
      [k for k in e])
base = api("/manager/exceptrecord/list?pageNum=1&pageSize=2")
check("分页 total 与 /manager/exceptrecord/list 一致", e.get("total") == base.get("total"),
      (e.get("total"), base.get("total")))
if e.get("rows"):
    r0 = e["rows"][0]
    check("每行补了 orgId / supplementaryStatus 两个键",
          "orgId" in r0 and r0.get("supplementaryStatus") in ("0", "1"),
          {"orgId": r0.get("orgId"), "supplementaryStatus": r0.get("supplementaryStatus")})
    # orgId 的 Java SQL 用的是 find_in_set(列, 传入值)，顺序反直觉，这里只做一致性核对：
    # 有 orgId 的行必须能在重点关注表里找到同车的记录
    with_org = [x for x in e["rows"] if x.get("orgId")]
    if with_org:
        cf = api("/manager/confimfree/list?pageNum=1&pageSize=5&carId=" + urllib.parse.quote(with_org[0]["carId"]))
        check("orgId 来自 car_confim_free 同车记录", bool(cf.get("rows")), cf.get("total"))
else:
    check("exceptRecordList 有数据可测", False, e)

# ================= 3) carWarning（自己造数据，跑完复原） =================
# SQL 里 inner join car_info ... and c.status = '1'，而这台库里 203 台车全是 status=0，
# 所以临时把一台车置为在线，测完改回原值（Java 侧同样只看在线车）。
cid = carsno = orig_status = None
ci = api("/manager/carinfo/list?pageNum=1&pageSize=5")
for row in ci.get("rows") or []:
    if row.get("id") and row.get("carNo"):
        cid, carsno, orig_status = str(row["id"]), row["carNo"], row.get("status")
        break
check("找到一台车（inner join car_info 的前置条件）", cid is not None, (cid, carsno, orig_status))

if cid and rd is not None:
    WID = None
    try:
        up = api("/manager/carinfo", "PUT", {"id": cid, "status": "1"})
        check("临时把该车置为在线 status=1", up.get("code") == 200, up)
        rd.delete("car_warning_list")
        body = {
            "carId": cid, "carNo": carsno, "trackNames": "QODER_ROAD,QODER_SECTION",
            "gantryStationId": "QODER_G1", "gantrytStation": "切面验证门架",
            "backCol1": TODAY, "gantryTime": NOW, "delFlag": "0", "status": "1",
            "roadCode": "QODER_ROAD", "sectionCode": "QODER_SECTION",
        }
        ins = api("/manager/carwarning", "POST", body)
        check("造一条今天的预警行", ins.get("code") == 200, ins)
        lst = api("/manager/carwarning/list?pageNum=1&pageSize=10&carNo=" + urllib.parse.quote(carsno))
        for row in lst.get("rows") or []:
            if row.get("backCol1") == TODAY and row.get("gantrytStation") == "切面验证门架":
                WID = row.get("id")
        check("预警行已入库", WID is not None, (WID, lst.get("total")))

        w = api("/manager/bigScreen/carWarning?carNoQuery=" + urllib.parse.quote(carsno))
        rows = w.get("data") or []
        mine = [x for x in rows if x.get("carNo") == carsno]
        check("carWarning 命中造的那条（缓存空 -> 回源 DB）", len(mine) >= 1,
              {"code": w.get("code"), "rows": len(rows), "msg": w.get("msg")})
        if mine:
            m = mine[0]
            print("  row keys: %s" % ",".join(list(m.keys())[:12]))
            check("needToWarnStr 默认是 \"0\"", m.get("needToWarnStr") == "0", m.get("needToWarnStr"))
            check("escapedType/escapedAmount 取自 car_info（XML 里 join 的别名列）",
                  "escapedType" in m and "escapedAmount" in m,
                  (m.get("escapedType"), m.get("escapedAmount")))
            check("回源后写回了 car_warning_list 缓存（不设 TTL）",
                  rd.get("car_warning_list") is not None, (rd.get("car_warning_list") or "")[:80])
            # 命中门架规则 + 时间窗内 -> "1"
            ui = api("/getInfo")
            uid = ((ui.get("user") or {}).get("userId")) or 1
            rd.delete("car_warning_list")  # 让下一次重新回源，确保规则分支被执行
            rd.set("car_warning_rule:%stype1" % uid, json.dumps(["QODER_G1"]))
            rd.set("sys_config:warning_trigger_timespan", "30")
            w2 = api("/manager/bigScreen/carWarning?carNoQuery=" + urllib.parse.quote(carsno))
            m2 = [x for x in (w2.get("data") or []) if x.get("carNo") == carsno]
            check("门架在规则列表内且经过时间在间隔内 -> needToWarnStr=1",
                  m2 and m2[0].get("needToWarnStr") == "1", m2 and m2[0].get("needToWarnStr"))
            # 间隔改成 0 分钟 -> 时间窗不命中
            rd.set("sys_config:warning_trigger_timespan", "0")
            rd.delete("car_warning_list")
            w3 = api("/manager/bigScreen/carWarning?carNoQuery=" + urllib.parse.quote(carsno))
            m3 = [x for x in (w3.get("data") or []) if x.get("carNo") == carsno]
            check("间隔 0 分钟时不该告警（回到 \"0\"）", m3 and m3[0].get("needToWarnStr") == "0",
                  m3 and m3[0].get("needToWarnStr"))
            # 路段/门架编码过滤
            rd.delete("car_warning_list")
            w4 = api("/manager/bigScreen/carWarning?gantryCode=" + urllib.parse.quote("QODER_G1_NOT"))
            check("设备编码不匹配时不返回该行",
                  not [x for x in (w4.get("data") or []) if x.get("carNo") == carsno], w4.get("total"))
        else:
            check("carWarning 有数据可测", False, w)
    finally:
        if WID:
            api("/manager/carwarning/%s" % urllib.parse.quote(str(WID)), "DELETE")
        # 复原：车辆在线状态、缓存键都恢复原样
        api("/manager/carinfo", "PUT", {"id": cid, "status": orig_status if orig_status is not None else "0"})
        rd.delete("car_warning_list", "sys_config:warning_trigger_timespan")
        try:
            ui = api("/getInfo")
            uid = ((ui.get("user") or {}).get("userId")) or 1
            rd.delete("car_warning_rule:%stype1" % uid)
        except Exception:
            pass
        left = api("/manager/carwarning/list?pageNum=1&pageSize=5&carNo=" + urllib.parse.quote(carsno))
        check("夹具已清理（该车不再有残留预警行）",
              not [x for x in (left.get("rows") or []) if x.get("gantrytStation") == "切面验证门架"],
              left.get("total"))
        back = api("/manager/carinfo/%s" % urllib.parse.quote(cid))
        check("车辆在线状态已复原", str(back.get("data", {}).get("status")) == str(orig_status),
              back.get("data", {}).get("status"))

print("----")
print("BIGSCREEN: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
