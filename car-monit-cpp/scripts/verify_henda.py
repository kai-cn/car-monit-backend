#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：/base/geometry 的 3 条 HenDa 接口 + /base/snapshotflow/earliest-time。

真实环境里 36.200.20.14:7890 与 127.0.0.1:9901 都不通，而这几条接口的**失败形态各不相同**
（吞成 null / 先答 success / 直接抛），所以必须有个能配合的假上游才能把两侧都验到：
本脚本自带一个桩服务，并把 app 的 forest.variables.hendaUrl / vehicleMonitor.baseUrl
指到它（logs/cfg_stub 是 config/ 的拷贝 + 两行覆盖）。

桩服务同时做两件事：
  * 按 nonce/timestamp **独立重算** HenDa 那个"累加量翻倍"的签名，与收到的 signature 对拍；
  * 记录原始 query string，用来证明 params 被编码了两次、以及 params 里 JSON 的键序。

前置：
    CM_SERVER_PORT=9993 ./build/car-monit-cpp.exe --config logs/cfg_stub
用法：python scripts/verify_henda.py [port] [token]
"""
import hashlib
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9993
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT
STUB_PORT = 9124
APPID = "YHZS"
SECRET = "b48381c4b98311ea90b100155d14fa3b"

ok = bad = 0
seen = []          # 桩服务收到的请求
mode = {"earliest": "envelope"}
lock = threading.Lock()


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:170] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:400])


def ref_signature(appid, timestamp, nonce, secret, json_str):
    strip = lambda s: s.replace("[", "").replace("]", "")
    parts = sorted([strip(appid), strip(timestamp), strip(nonce), secret])
    pub = ""
    for s in parts:
        pub = s if pub == "" else pub + pub + "&" + s
    body = json_str.replace("\n", "").replace(" ", "")
    src = pub + "&" + body
    return hashlib.md5(src.encode("utf-8")).hexdigest()


class Stub(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = parsed.query
        with lock:
            seen.append({"path": parsed.path, "raw": self.path, "query": qs})
        if parsed.path.endswith("/getLonLatByPos"):
            p = urllib.parse.parse_qs(qs)
            lxbh = (p.get("lxbh") or [""])[0]
            if "FAIL500" in self.path:
                self.send_response(500)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if "NULLDATA" in self.path:
                body = b'{"data":null}'
            else:
                body = b'{"data":{"x":"115.1","y":"28.2"}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path.endswith("/earliest-time"):
            with lock:
                m = mode["earliest"]
            body = {"envelope": b'{"msg":"\xe6\x93\x8d\xe4\xbd\x9c\xe6\x88\x90\xe5\x8a\x9f","code":200,"data":"2025-01-01 00:00:00"}',
                    "datestr": b'"2025-01-01 00:00:00"',
                    "empty": b''}[m]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()


def req(path, token=None, timeout=30):
    r = urllib.request.Request(BASE + path)
    t = TOKEN if token is None else token
    if t:
        r.add_header("Authorization", "Bearer " + t)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def js(path, token=None):
    st, raw = req(path, token)
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:
        return st, {"raw": raw[:200]}


srv = ThreadingHTTPServer(("127.0.0.1", STUB_PORT), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.3)

try:
    # ---------- 1) getHenDa 成功路径 ----------
    st, j = js("/base/geometry/getHenDa?lxbh=G60&lxfx=1&zhStr=12.345")
    check("getHenDa 成功：data 是 {longitude, latitude}，且是字符串（Java 里 getString）",
          st == 200 and list(j.keys()) == ["msg", "code", "data"]
          and list(j["data"].keys()) == ["longitude", "latitude"]
          and j["data"] == {"longitude": "115.1", "latitude": "28.2"}, j)
    with lock:
        hits = [s for s in seen if s["path"].endswith("/getLonLatByPos")]
    check("确实发出了对上游的 GET", bool(hits), len(hits))
    if hits:
        q = urllib.parse.parse_qs(hits[-1]["query"])
        check("query 里有 appid/nonce/signature/timestamp/params 五个键",
              set(q) == {"params", "appid", "nonce", "signature", "timestamp"}, sorted(q))
        check("appid 用配置里的 YHZS", q.get("appid") == ["YHZS"], q.get("appid"))
        nonce, ts = q["nonce"][0], q["timestamp"][0]
        check("nonce 是 13 位毫秒、timestamp 是 14 位 yyyyMMddHHmmss",
              re.fullmatch(r"\d{13}", nonce) and re.fullmatch(r"\d{14}", ts), (nonce, ts))
        check("signature 是 32 位小写十六进制",
              bool(re.fullmatch(r"[0-9a-f]{32}", q["signature"][0])), q["signature"])
        check("signature 与桩服务独立重算的参照值一致（含累加量翻倍的 bug）",
              q["signature"][0] == ref_signature(APPID, ts, nonce, SECRET, nonce),
              (q["signature"][0], ref_signature(APPID, ts, nonce, SECRET, nonce)))
        # params：Java 先 URLEncoder.encode(json)，Forest 再对整个值编一次 => 双重编码
        raw_params = re.search(r"params=([^&]*)", hits[-1]["raw"]).group(1)
        # 外层 Forest 也是 URLEncoder 风格：空格写成 '+'，且不转义已有的 '+'
        once = urllib.parse.unquote(raw_params)          # 解掉外层
        twice = urllib.parse.unquote_plus(once)          # 内层是 URLEncoder 的输出 => '+' 是空格
        check("params 是双重编码（解码一次还剩 %22，再解一次才是 JSON 原文）",
              "%22" in once and twice.startswith("{"), (once[:40], twice[:40]))
        inner = json.loads(twice)
        check("params 里 filter 的值保留了两个空格（源码如此）",
              inner["filter"] == "lxbh='G60'  and gxfx = '1'", inner["filter"])
        check("内层 URLEncoder 把空格写成 '+'、外层不再转义 '+' => 线上看到的是 ++",
              "++and+" in once, once[:60])
        def jhash(k):
            h = 0
            for ch in k:
                h = (h * 31 + ord(ch)) & 0xFFFFFFFF
            return h - 0x100000000 if h >= 0x80000000 else h

        def bucket(k):                      # new HashMap<>(3) => 表容量 4
            h = jhash(k)
            return (h ^ (h >> 16)) & 3

        expected_order = sorted(inner.keys(), key=bucket)
        check("params 的键序 = Java HashMap(容量4) 的桶序（桩端独立算一遍对拍）",
              list(inner.keys()) == expected_order,
              (list(inner.keys()), expected_order, {k: bucket(k) for k in inner}))
        check("m 用的是 zhStr 而不是 qdzh", inner["m"] == "12.345", inner["m"])

    # ---------- 2) 失败被吞成 null ----------
    st2, j2 = js("/base/geometry/getHenDa?lxbh=FAIL500&lxfx=1&zhStr=1")
    check("上游 500 => getHenDa 仍是 200 且**没有 data 键**（catch 返回 null）",
          st2 == 200 and list(j2.keys()) == ["msg", "code"] and j2.get("code") == 200, j2)
    st3, j3 = js("/base/geometry/getHenDa?lxbh=NULLDATA&lxfx=1&zhStr=1")
    check("data 为 null => 同样看不出远端有问题", list(j3.keys()) == ["msg", "code"], j3)

    # ---------- 3) 先答 success 的两条异步接口 ----------
    t0 = time.time()
    st4, j4 = js("/base/geometry/syncAllGeometry1?lxbh=G60&lxfx=1&qdzh=10")
    check("syncAllGeometry1 立即 200（不等后台）", st4 == 200 and j4.get("code") == 200
          and time.time() - t0 < 3, (j4, round(time.time() - t0, 3)))
    st5, j5 = js("/base/geometry/syncAllGeometry1")
    check("不带任何参数也是 200：qdzh 为 null 的 NPE 发生在池线程里，客户端看不见",
          j5.get("code") == 200, j5)
    st6, j6 = js("/base/geometry/syncAllGeometry")
    check("syncAllGeometry：geometry_copy1 不存在 => 同步抛 => code:500（本地可观测分支）",
          j6.get("code") == 500, j6)
    n_geo = req("/base/geometry/list?pageNum=1&pageSize=1")

    # ---------- 4) earliest-time：信封 / 日期串 / 空 ----------
    st7, j7 = js("/base/snapshotflow/earliest-time")
    check("上游返 AjaxResult 信封而目标是裸 Date => 转换异常 => code:500",
          j7.get("code") == 500 and "Date" in str(j7.get("msg")), j7)
    with lock:
        mode["earliest"] = "datestr"
    st8, j8 = js("/base/snapshotflow/earliest-time")
    check("上游直接给日期串 => data 是 ISO-8601 带 +08:00（裸 java.util.Date 的默认序列化）",
          j8.get("code") == 200 and str(j8.get("data")).startswith("2025-01-01T00:00:00")
          and "+08:00" in str(j8.get("data")), j8)
    with lock:
        mode["earliest"] = "empty"
    st9, j9 = js("/base/snapshotflow/earliest-time")
    check("上游给空 => success(\"暂无数据\") 命中的是 **msg 重载**：整条响应没有 data 键",
          j9.get("code") == 200 and j9.get("msg") == "暂无数据" and "data" not in j9, j9)

    # ---------- 5) 鉴权 ----------
    st10, j10 = js("/base/geometry/getHenDa", token="")
    check("无 token => HTTP 200 + body code 401", j10.get("code") == 401, j10)
    st11, j11 = js("/base/geometry/syncAllGeometry1", token="")
    check("异步那条也要先过鉴权（不能先起线程再判权限）", j11.get("code") == 401, j11)
finally:
    srv.shutdown()

print("----")
print("HEN DA / EARLIEST: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
