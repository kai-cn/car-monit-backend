# -*- coding: utf-8 -*-
"""Redis 双 DB 隔离校验：Java=db0，Go=db2，写/读/驱逐都只能碰自己那侧。

同时验证「共用 MySQL + 独立缓存」下，一端未缓存的键仍能回源到同一个库拿到一致数据。
结束后清理测试行与测试键。

用法: MSYS2_ARG_CONV_EXCL='*' python scripts/parity/check_redis_isolation.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pp  # noqa: E402
import compare_write as W  # noqa: E402

failures = []


def check(ok, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, (" | " + detail[:170]) if detail else ""))
    if not ok:
        failures.append(label + " " + detail[:120])


def exists(key, db):
    return pp.r("exists", key, db=db).strip() == "1"


def main():
    tk_j, tk_g = pp.login_java(), pp.login_go()

    print("== 1. 登录态 ==")
    for tag, tok, own, other in (("Go", tk_g, pp.GO_DB, pp.JAVA_DB), ("Java", tk_j, pp.JAVA_DB, pp.GO_DB)):
        claims = pp.jwt_claims(tok)
        key = "login_tokens:" + (claims.get("login_user_key") or claims.get("uuid") or "")
        check(exists(key, own), "%s 会话写在自己的 db%s" % (tag, own), key)
        check(not exists(key, other), "%s 会话没有写进对端 db%d" % (tag, other), key)
        raw = pp.r("get", key, db=own)
        check('"@type":"com.ruoyi.common.core.domain.model.LoginUser"' in raw,
              "%s 会话带 FastJson2 类型标记" % tag)

    print("== 2. sys_config 读写与驱逐 ==")
    for tag, base, tok, own, other in (("Go 写", pp.GO, tk_g, pp.GO_DB, pp.JAVA_DB),
                                       ("Java 写", pp.JAVA, tk_j, pp.JAVA_DB, pp.GO_DB)):
        key = "PARITY_iso_" + pp.rand()
        out = pp.req(base, "/system/config", tok, "POST",
                     {"configKey": key, "configValue": "789", "configName": key, "configType": "N"})
        check(out.get("code") == 200, "%s 新增参数" % tag, json.dumps(out, ensure_ascii=False)[:80])
        check(exists("sys_config:" + key, own), "%s 写后缓存落在自己的 db%d" % (tag, own))
        check(not exists("sys_config:" + key, other), "%s 没有污染对端 db%d" % (tag, other))
        # 对端没有这个缓存键，但共用 MySQL，回源后应读到同一个值
        peer = pp.req(pp.JAVA if base == pp.GO else pp.GO,
                      "/system/config/configKey/" + key,
                      tk_j if base == pp.GO else tk_g)
        check(peer.get("msg") == "789", "%s 写、对端回源读到同值" % tag, json.dumps(peer, ensure_ascii=False)[:80])
        rid = W.locate("sys_config", "config_id", key)
        if rid:
            pp.req(base, "/system/config/%s" % rid, tok, "DELETE")
        check(not exists("sys_config:" + key, own), "%s 删除后自己的缓存被驱逐" % tag)

    print("== 3. sys_dict 缓存 ==")
    dtype = "sys_yes_no"
    key = "sys_dict:" + dtype
    pp.r("del", key, db=pp.GO_DB)
    pp.r("del", key, db=pp.JAVA_DB)
    a = pp.req(pp.JAVA, "/system/dict/data/type/" + dtype, tk_j)
    check(exists(key, pp.JAVA_DB) and not exists(key, pp.GO_DB),
          "Java 读字典只写 db%d" % pp.JAVA_DB)
    java_before = pp.r("get", key, db=pp.JAVA_DB)
    b = pp.req(pp.GO, "/system/dict/data/type/" + dtype, tk_g)
    # db0 里 Java 自己的缓存本就该存在，这里要证的是「Go 的读没去动它」
    check(exists(key, pp.GO_DB) and pp.r("get", key, db=pp.JAVA_DB) == java_before,
          "Go 读字典写进 db%d 且未改动 db%d 的对端缓存" % (pp.GO_DB, pp.JAVA_DB))
    check(a.get("code") == 200 and b.get("code") == 200, "两端字典读取成功")
    diff = pp.diff(W.norm(a), W.norm(b))
    check(not diff, "两端字典响应一致（各自缓存冷启动）", json.dumps(diff[:2], ensure_ascii=False)[:160])
    # 两端缓存值本身要同构（同一套 FastJson2 写法）
    jv = pp.r("get", "sys_dict:" + dtype, db=pp.JAVA_DB)
    gv = pp.r("get", "sys_dict:" + dtype, db=pp.GO_DB)
    check('"@type":"com.ruoyi.common.core.domain.entity.SysDictData"' in jv
          and '"@type":"com.ruoyi.common.core.domain.entity.SysDictData"' in gv,
          "两端缓存值都带 SysDictData 类型标记")

    print("== 4. 对象缓存（white_car_list）==")
    res = next(r for r in W.RESOURCES if r["base"] == "/manager/whiteinfo")
    before_go = pp.r("get", "white_car_list", db=pp.GO_DB)
    before_java = pp.r("get", "white_car_list", db=pp.JAVA_DB)
    rows = pp.req(pp.JAVA, "/manager/whiteinfo/list?pageNum=1&pageSize=1000", tk_j).get("rows") or []
    body = W.make_body(rows[0], pp.rand(), None, (), pp.rand_digits())
    out = pp.req(pp.GO, "/manager/whiteinfo", tk_g, "POST", body)
    check(out.get("code") == 200, "Go 新增白名单", json.dumps(out, ensure_ascii=False)[:80])
    after_go = pp.r("get", "white_car_list", db=pp.GO_DB)
    after_java = pp.r("get", "white_car_list", db=pp.JAVA_DB)
    check(body["carNo"] in after_go, "Go 的缓存刷新出现在 db%d" % pp.GO_DB)
    check(after_java == before_java, "Java 的 db%d 缓存未被 Go 的写改动" % pp.JAVA_DB)
    rid = W.locate("car_white_info", "id", body["carNo"])
    if rid:
        pp.req(pp.GO, "/manager/whiteinfo/%s" % rid, tk_g, "DELETE")

    print("\n失败 %d 项" % len(failures))
    for f in failures:
        print("  -", f)

    print("== 清理 ==")
    W.clean()
    for db in (pp.JAVA_DB, pp.GO_DB):
        for key in pp.scan("*PARITY*", db=db):
            pp.r("del", key, db=db)
    print("db0 dbsize=%s db2 dbsize=%s" % (pp.r("dbsize", db=pp.JAVA_DB).strip(),
                                          pp.r("dbsize", db=pp.GO_DB).strip()))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
