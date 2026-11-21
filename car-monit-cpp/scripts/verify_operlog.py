#!/usr/bin/env python3
# @Log 切面的端到端验证：做真实写操作，再从 /monitor/operlog/list 读回落库的字段。
# 断言口径来自 Java LogAspect + SysOperLogMapper.insertOperlog。
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://127.0.0.1:%d" % (int(sys.argv[1]) if len(sys.argv) > 1 else 9991)
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""

ok = bad = 0


def req(path, method="GET", body=None, ctype=None):
    r = urllib.request.Request(BASE + path, method=method)
    if TOKEN:
        r.add_header("Authorization", "Bearer " + TOKEN)
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        r.add_header("Content-Type", ctype or "application/json;charset=UTF-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def js(path, method="GET", body=None, ctype=None):
    st, raw = req(path, method, body, ctype)
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:
        return st, {"_raw": raw[:200]}


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:260] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:300])


def latest(title, url_contains=None, limit=30):
    q = "/monitor/operlog/list?pageNum=1&pageSize=%d&title=%s" % (
        limit, urllib.parse.quote(title))
    _, j = js(q)
    rows = j.get("rows") or []
    if url_contains:
        rows = [x for x in rows if url_contains in (x.get("operUrl") or "")]
    return rows


KEY = "qoder.aspect.check"
NAME = "切面验证参数"

# ---- 1) 新增参数：POST /system/config 命中 @Log(title=参数管理, INSERT) ----
st, j = js("/system/config", "POST", json.dumps({
    "configName": NAME, "configKey": KEY, "configValue": "1",
    "configType": "N", "remark": "scripts/verify_operlog.py", "password": "should-be-dropped"}))
check("POST /system/config 成功", j.get("code") == 200, j)
time.sleep(0.8)

rows = latest("参数管理")
mine = [x for x in rows if (x.get("operParam") or "").find(KEY) >= 0]
check("落库一条 参数管理/INSERT", len(mine) >= 1, [x.get("operId") for x in rows][:5])
if mine:
    r0 = mine[0]
    print("  row: " + json.dumps({k: r0.get(k) for k in (
        "title", "businessType", "businessTypeLabel", "method", "requestMethod", "operatorType",
        "operName", "deptName", "operUrl", "operIp", "operLocation", "status", "operTime")},
        ensure_ascii=False))
    check("businessType=1(INSERT) / operatorType=1(MANAGE) / status=0",
          r0.get("businessType") == 1 and r0.get("operatorType") == 1 and r0.get("status") == 0,
          (r0.get("businessType"), r0.get("operatorType"), r0.get("status")))
    check("method 是 Java 的 类全名.方法()",
          r0.get("method") == "com.ruoyi.web.controller.system.SysConfigController.add()",
          r0.get("method"))
    check("operUrl 不含 query（getRequestURI 语义）", r0.get("operUrl") == "/system/config", r0.get("operUrl"))
    check("operName/deptName 来自登录用户", bool(r0.get("operName")) and r0.get("deptName") is not None,
          (r0.get("operName"), r0.get("deptName")))
    check("operIp=127.0.0.1 且 oper_location=内网IP",
          r0.get("operIp") in ("127.0.0.1", "0:0:0:0:0:0:0:1") and r0.get("operLocation") == "内网IP",
          (r0.get("operIp"), r0.get("operLocation")))
    # 入参分支：POST + 空参数表 -> 序列化入参；fastjson2 丢 null 与 password
    try:
        p = json.loads(r0.get("operParam") or "{}")
    except Exception:
        p = {"_bad": r0.get("operParam")}
    check("operParam 记录入参且排除 password",
          p.get("configKey") == KEY and "password" not in p, r0.get("operParam"))
    try:
        jr = json.loads(r0.get("jsonResult") or "{}")
    except Exception:
        jr = {"_bad": r0.get("jsonResult")}
    check("jsonResult 是返回值且丢 null", jr.get("code") == 200 and "data" not in jr,
          r0.get("jsonResult"))

# ---- 2) 同参数的 GET 列表不应该产生日志（Java 的 list 没有 @Log） ----
js("/system/config/list?pageNum=1&pageSize=5")
time.sleep(0.4)
check("GET /system/config/list 不写操作日志",
      not [x for x in latest("参数管理") if (x.get("operUrl") or "").endswith("/list")],
      [x.get("operUrl") for x in latest("参数管理")][:5])

# ---- 3) 删除该参数：DELETE 只有路径变量 -> operParam 是 "{}" ----
_, lst = js("/system/config/list?pageNum=1&pageSize=5&configKey=" + urllib.parse.quote(KEY))
rows_cfg = lst.get("rows") or []
if not rows_cfg:
    check("能查到刚建的参数", False, lst)
else:
    cid = rows_cfg[0]["configId"]
    st2, j2 = js("/system/config/%s" % cid, "DELETE")
    check("DELETE /system/config/{id} 成功", j2.get("code") == 200, j2)
    time.sleep(0.8)
    drows = [x for x in latest("参数管理") if x.get("businessType") == 3]
    check("落库一条 参数管理/DELETE", len(drows) >= 1, [x.get("operId") for x in latest("参数管理")][:4])
    if drows:
        d0 = drows[0]
        check("DELETE 的 operParam 是 {}（Java 走 paramsMap 分支）",
              d0.get("operParam") in ("{}", None, ""), d0.get("operParam"))
        check("method 指向 remove()", (d0.get("method") or "").endswith("SysConfigController.remove()"),
              d0.get("method"))

# ---- 4) 异常分支：POST /system/user {} 在 Java 侧是 NPE -> status=1 + error_msg ----
st3, j3 = js("/system/user", "POST", "{}")
check("POST /system/user {} 返回 code 500（Java 的 NPE 复刻）", j3.get("code") == 500, j3)
time.sleep(0.8)
frows = [x for x in latest("用户管理") if x.get("businessType") == 1 and x.get("status") == 1]
check("落库一条 status=1 的失败记录", len(frows) >= 1,
      [(x.get("operId"), x.get("status"), x.get("errorMsg")) for x in latest("用户管理")][:4])
if frows:
    f0 = frows[0]
    check("失败记录 method 指向 SysUserController.add()",
          (f0.get("method") or "").endswith("SysUserController.add()"), f0.get("method"))
    # Java: NullPointerException#getMessage() == null -> StringUtils.substring(null,..) -> NULL
    check("NPE 的 error_msg 是 NULL（不是字符串 \"null\"）", f0.get("errorMsg") is None,
          repr(f0.get("errorMsg")))

print("----")
print("OPERLOG ASPECT: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
