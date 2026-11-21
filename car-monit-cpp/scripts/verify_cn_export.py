#!/usr/bin/env python3
# 端到端验证：中文文件名的导出→下载链路 + Spring URL 层安全规则的保真度
#
# 关键语义（来自 ruoyi-framework/SecurityConfig.java）：
#   .antMatchers("/common/download**").anonymous()          == isAnonymous() -> 带 token 反而 403
#   .antMatchers("/common/download/resource**").authenticated()             -> 必须带 token
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:9991"
TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""

ok = 0
bad = 0


def req(path, method="GET", body=None, token=None, ctype=None):
    r = urllib.request.Request(BASE + path, method=method)
    if token:
        r.add_header("Authorization", "Bearer " + token)
    data = None
    if body is not None:
        data = body.encode("utf-8")
        r.add_header("Content-Type", ctype or "application/x-www-form-urlencoded;charset=UTF-8")
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + detail if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + detail)


def q(s):
    return urllib.parse.quote(s, safe="")


# ---- 1) 操作日志导出：GET（Java 是 @GetMapping） 响应是 AjaxResult.success(filename) ----
st, _, raw = req("/monitor/operlog/export?pageNum=1&pageSize=5", token=TOKEN)
j = json.loads(raw.decode("utf-8"))
check("operlog/export GET 返回 code=200", st == 200 and j.get("code") == 200, raw.decode("utf-8")[:120])
fname = j.get("msg", "")
check("导出文件名是中文 + .xlsx", fname.endswith("_操作日志.xlsx"), fname)

# ---- 2) /common/download 不带 token：anonymous() 规则放行 拿到真实 xlsx 字节 ----
st2, hd2, body2 = req("/common/download?fileName=" + q(fname) + "&delete=true")
check("无 token 下载中文文件 200/octet-stream",
      st2 == 200 and "octet-stream" in hd2.get("Content-Type", ""),
      "status=%s ct=%s len=%s" % (st2, hd2.get("Content-Type"), len(body2)))
check("下载内容是 zip 魔数的真 xlsx", body2[:4] == b"PK\x03\x04", repr(body2[:4]))
check("Content-Disposition 用毫秒名", hd2.get("Content-Disposition", "").startswith("attachment; filename="),
      hd2.get("Content-Disposition", "")[:80])

# ---- 3) delete=true 之后再次下载：文件不存在 -> AjaxResult code=500（HTTP 200） ----
st3, hd3, body3 = req("/common/download?fileName=" + q(fname))
j3 = json.loads(body3.decode("utf-8"))
check("delete=true 已删除文件", st3 == 200 and j3.get("code") == 500, body3.decode("utf-8")[:80])

# ---- 4) 同一路径带 token：isAnonymous() 不满足 -> 容器级 403（Spring 错误页形状） ----
st4, hd4, body4 = req("/common/download?fileName=" + q(fname), token=TOKEN)
j4 = json.loads(body4.decode("utf-8"))
check("带 token 命中 /common/download** 的 anonymous() -> 403",
      st4 == 403 and j4.get("error") == "Forbidden" and j4.get("path") == "/common/download",
      "status=%s body=%s" % (st4, body4.decode("utf-8")[:120]))

# ---- 5) 登录日志导出 + /common/download/resource（必须带 token） ----
st5, _, body5 = req("/monitor/logininfor/export?pageNum=1&pageSize=5", token=TOKEN)
j5 = json.loads(body5.decode("utf-8"))
check("logininfor/export code=200", j5.get("code") == 200, body5.decode("utf-8")[:120])
f5 = j5.get("msg", "")
res = "/common/download/resource?resource=" + q("/profile/download/" + f5)
st6, hd6, body6 = req(res, token=TOKEN)
check("resource 下载（authenticated 规则）中文文件成功",
      st6 == 200 and body6[:4] == b"PK\x03\x04", "status=%s len=%s" % (st6, len(body6)))
st7, _, body7 = req(res)
j7 = json.loads(body7.decode("utf-8"))
check("resource 不带 token -> 401 且是 Java 的 AjaxResult 形状",
      st7 == 200 and j7.get("code") == 401, body7.decode("utf-8")[:120])

# ---- 6) 用户导入模板：Java @GetMapping("/importTemplate") 返回的是文件名，不是字节 ----
st8, _, body8 = req("/system/user/importTemplate", token=TOKEN)
j8 = json.loads(body8.decode("utf-8"))
tpl = j8.get("msg", "")
check("importTemplate 返回 AjaxResult.success(文件名)",
      st8 == 200 and j8.get("code") == 200 and tpl.endswith("_用户数据.xlsx"), body8.decode("utf-8")[:120])
st9, hd9, body9 = req("/common/download?fileName=" + q(tpl) + "&delete=true")
check("模板下载是真 xlsx 且可被 zipfile 解析",
      st9 == 200 and body9[:4] == b"PK", "status=%s ct=%s len=%s" % (st9, hd9.get("Content-Type"), len(body9)))
import zipfile, io as _io
try:
    zf = zipfile.ZipFile(_io.BytesIO(body9))
    names = zf.namelist()
    bad_crc = [i.filename for i in zf.infolist() if zf.read(i.filename) is None]
    sheet = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
    check("模板含 6 个 OOXML 部件、CRC 全通过、只有表头行",
          len(names) == 6 and not bad_crc and sheet.count("<row ") == 1 and "用户名称" in sheet,
          "parts=%d rows=%d" % (len(names), sheet.count("<row ")))
except Exception as e:
    check("模板 zip 可解析", False, repr(e))

# ---- 7) /system/notice/view/{id}：anonymous() 规则 —— 带 token 403、不带 token 200 ----
nid = None
st9, _, body9 = req("/system/notice/list?pageNum=1&pageSize=1", token=TOKEN)
try:
    rows = json.loads(body9.decode("utf-8")).get("rows") or []
    if rows:
        nid = rows[0].get("noticeId")
except Exception:
    nid = None
if nid is None:
    print("SKIP  notice/view 无数据可测")
else:
    v = "/system/notice/view/" + str(nid)
    st10, _, b10 = req(v)
    st11, _, b11 = req(v, token=TOKEN)
    check("notice/view 无 token 可访问", st10 == 200 and json.loads(b10.decode("utf-8")).get("code") == 200,
          b10.decode("utf-8")[:80])
    check("notice/view 带 token -> 403（isAnonymous）", st11 == 403, "status=%s" % st11)

# ---- 8) 中文查询参数能进 where 条件（percent-decode + UTF-8 全链路） ----
st12, _, body12 = req("/monitor/operlog/list?pageNum=1&pageSize=5&title=" + q("用户"), token=TOKEN)
j12 = json.loads(body12.decode("utf-8"))
check("中文查询参数可用（code=200）", st12 == 200 and j12.get("code") == 200,
      "total=%s" % j12.get("total"))
print("----")
print("pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
