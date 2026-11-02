# -*- coding: utf-8 -*-
"""/oss/** 与根路径端点的双端一致性验证。

Java 侧 MinIO(172.30.100.102:9002) 不可达，所有调用都落到 GlobalExceptionHandler：
HTTP 200 + {"msg": "<异常文本>", "code": 500}；上传字段名不是 object 时 Java 直接 NPE(msg=null)。
Go 侧要求：信封、HTTP 状态、msg 是否为 null 都要一致（异常文本本身允许不同）。
"""
import sys

sys.path.insert(0, "D:/work/IdeaProjects/car-monit-backend-new/car-monit-go/scripts/parity")
import pp  # noqa: E402

CASES = [
    ("GET", "/oss/bucket"),
    ("GET", "/oss/bucket/developer"),
    ("GET", "/oss/object/a/b"),
    ("GET", "/oss/object/a/b/60"),
    ("GET", "/oss/object/a/b/900"),
    ("POST", "/oss/bucket/parity-test-bucket"),
    ("DELETE", "/oss/bucket/parity-test-bucket"),
    ("DELETE", "/oss/object/a/b"),
    ("GET", "/"),
    ("POST", "/"),
    ("PUT", "/"),
    ("DELETE", "/"),
    ("PATCH", "/"),
]

tj, tg = pp.login_java(), pp.login_go()
bad = 0
for method, path in CASES:
    sj, rj, cj = pp.call(pp.JAVA, path, tj, method)
    sg, rg, cg = pp.call(pp.GO, path, tg, method)
    j, g = pp.req(pp.JAVA, path, tj, method), pp.req(pp.GO, path, tg, method)
    same_status = sj == sg
    same_code = j.get("code") == g.get("code") or (isinstance(j, dict) and isinstance(g, dict) and j.get("__status__") == g.get("__status__"))
    print("%-6s %-32s java(%s,code=%s) go(%s,code=%s) %s" % (
        method, path, sj, j.get("code", j.get("__raw__", "")[:14]),
        sg, g.get("code", g.get("__raw__", "")[:14]),
        "OK" if (same_status and same_code) else "DIFF"))
    if not (same_status and same_code):
        bad += 1
        print("     java body:", rj[:120])
        print("     go   body:", rg[:120])

# 匿名访问：Java 是 {msg: "请求访问：...认证失败...", code: 401}
for method, path in (("GET", "/oss/bucket"), ("GET", "/system/user/list")):
    sj, rj, _ = pp.call(pp.JAVA, path, None, method)
    sg, rg, _ = pp.call(pp.GO, path, None, method)
    j, g = pp.norm(pp.req(pp.JAVA, path, None, method)), pp.norm(pp.req(pp.GO, path, None, method))
    ok = sj == sg and j.get("code") == g.get("code")
    print("匿名  %-6s %-22s java(%s,%s) go(%s,%s) %s" % (
        method, path, sj, j.get("code"), sg, g.get("code"), "OK" if ok else "DIFF"))
    if not ok:
        bad += 1
        print("     java:", rj[:120], "\n     go  :", rg[:120])

print("\n不一致项:", bad)
