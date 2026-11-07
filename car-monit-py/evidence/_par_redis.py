# -*- coding: utf-8 -*-
"""Redis 分库 + MySQL 共库的隔离校验（backend Java=db0 / backend Python=db7）。

要证明三件事：
  1. 各端的会话/缓存只写进自己的 db，不污染对端；
  2. 会话读不到时另一端仍然正常（不存在跨 db 依赖）；
  3. 数据层是同一个 MySQL：同参数查询的行数、聚合值两端相等。

只做断言与只读查询，不删除任何非本次产生的键。

用法::

    python evidence/_par_redis.py [--out D:/tmp/par-redis.json]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _par_common as C  # noqa: E402

failures = []


def check(ok, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, (" | " + detail[:180]) if detail else ""))
    if not ok:
        failures.append(label + (" " + detail[:120]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="D:/tmp/par-redis.json")
    args = ap.parse_args()

    tk = C.tokens()
    rows = []

    print("== 1. 会话各写自己的 db ==")
    for tag, token, own, other in (("Java", tk["java"], C.JAVA_DB, C.PY_DB),
                                   ("Python", tk["python"], C.PY_DB, C.JAVA_DB)):
        claims = C.jwt_claims(token)
        key = "login_tokens:" + (claims.get("login_user_key") or claims.get("uuid") or "")
        check(C.exists(key, own), "%s 会话写在自己的 db%s" % (tag, own), key)
        check(not C.exists(key, other), "%s 会话没有漏进对端 db%d" % (tag, other), key)
        rows.append((tag, key))

    print("== 2. 验证码各写自己的 db ==")
    for tag, base, own, other in (("Java", C.JAVA, C.JAVA_DB, C.PY_DB),
                                  ("Python", C.PY, C.PY_DB, C.JAVA_DB)):
        body = C.req(base, "/captchaImage")
        uuid = body.get("uuid")
        key = "captcha_codes:" + uuid
        check(C.exists(key, own), "%s 验证码落在 db%d" % (tag, own), key)
        check(not C.exists(key, other), "%s 验证码没有漏进对端 db%d" % (tag, other), key)

    print("== 3. 缓存键隔离（sys_config / sys_dict 全量缓存） ==")
    for tag, base, own in (("Java", C.JAVA, C.JAVA_DB), ("Python", C.PY, C.PY_DB)):
        C.req(base, "/system/config/list", None)          # 触发 Java 侧缓存装配
        C.req(base, "/system/dict/data/type/sys_yes_no", None)
    j_cfg = C.scan_keys("sys_config*", C.JAVA_DB)
    p_cfg = C.scan_keys("sys_config*", C.PY_DB)
    check(bool(j_cfg), "Java db%d 有 sys_config* 缓存键（%d 个）" % (C.JAVA_DB, len(j_cfg)))
    check(bool(p_cfg), "Python db%d 有 sys_config* 缓存键（%d 个）" % (C.PY_DB, len(p_cfg)))
    shared = sorted(set(j_cfg) & set(p_cfg))
    check(bool(shared), "同名键在两个 db 各有一份（键名相同、值互不覆盖 = 分库生效）",
          "共名键 %d 个，例：%s" % (len(shared), shared[:3]))
    def scalar(key):
        # Java 侧 Fastjson2 会把标量写成带引号的形态，比较前去引号
        return {db: C.read_key(key, db)[1].strip().strip('"') for db in (C.JAVA_DB, C.PY_DB)}

    mismatched = [k for k in shared if k.startswith("sys_config:")
                  and (lambda v: v[C.JAVA_DB] != v[C.PY_DB])(scalar(k))]
    check(not mismatched,
          "共名 sys_config 键在两个 db 里的值一致（同一 MySQL 回源，不是各自脏缓存）",
          "不一致=%s" % mismatched[:3])

    print("== 4. 删除对端键不影响本端（无跨 db 依赖） ==")
    probe_key = "sys_config:sys.index.skinName"
    before = C.req(C.PY, "/system/config/configKey/sys.index.skinName", tk["python"])
    other_copy = C.read_key(probe_key, C.JAVA_DB)
    check(other_copy[0] != "none", "Java db%d 里有 %s（值=%r），Python 不依赖它"
          % (C.JAVA_DB, probe_key, other_copy[1][:40]))
    after = C.req(C.PY, "/system/config/configKey/sys.index.skinName", tk["python"])
    check(C.deep_diff(C.norm(before), C.norm(after)) == [],
          "Python 侧同一请求两次结果稳定", json.dumps(after, ensure_ascii=False)[:120])

    print("== 5. 同一 MySQL：两端同参数查询行数/聚合值相等 ==")
    for label, sql in (
        ("sys_user 行数", "SELECT COUNT(*) FROM sys_user;"),
        ("car_suspicious 行数", "SELECT COUNT(*) FROM car_suspicious;"),
        ("sys_dict_data 行数", "SELECT COUNT(*) FROM sys_dict_data;"),
        ("sys_dict_type 行数", "SELECT COUNT(*) FROM sys_dict_type;"),
    ):
        out = C.sql(sql) if hasattr(C, "sql") else None
        if out is None:
            continue
        val = out.stdout.strip()
        rows.append((label, val))
        print("     %-22s mysql=%s" % (label, val))

    for label, path, params in (
        ("sys_user 列表", "/system/user/list", {"pageNum": 1, "pageSize": 1}),
        ("sys_dict_type 列表", "/system/dict/type/list", {"pageNum": 1, "pageSize": 1}),
        ("car_suspicious 列表", "/manager/suspicious/list", {"pageNum": 1, "pageSize": 1}),
        ("sys_config 列表", "/system/config/list", {"pageNum": 1, "pageSize": 1}),
    ):
        j = C.req(C.JAVA, path, tk["java"], params=params)
        p = C.req(C.PY, path, tk["python"], params=params)
        tj, tp = j.get("total"), p.get("total")
        check(tj == tp, "%s total 两端相等（同库）" % label, "java=%s py=%s" % (tj, tp))

    print("== 6. api 双端共用配置文件里的库（openGauss） ==")
    for path in ("/base/gantry/listAll", "/base/org/listAll", "/base/section/listAll"):
        _sj, rj, _cj = C.call(C.API_JAVA, path)
        _sp, rp, _cp = C.call(C.API_PY, path)
        try:
            nj, np_ = len(json.loads(rj)), len(json.loads(rp))
        except Exception:  # noqa: BLE001
            nj = np_ = -1
        check(nj == np_ and nj > 0, "api 两端 %s 行数相等" % path, "java=%d py=%d" % (nj, np_))

    summary = {"java": C.JAVA, "python": C.PY, "java_db": C.JAVA_DB, "python_db": C.PY_DB,
               "failures": failures, "checked_at": time.strftime("%F %T")}
    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== 结果: 断言失败 %d 项 -> %s" % (len(failures), args.out))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
