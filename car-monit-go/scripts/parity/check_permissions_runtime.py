#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用“无权限账号”做运行时权限与审计冒烟（CI/联调门禁）。

背景：现有对拍脚本全部用 admin 登录，admin 持有 *:*:*，因此“路由漏挂权限中间件”
在响应体对比里完全隐形。check_perms.py 只能做源码级比对，无法证明中间件真的生效。
本脚本起真实服务后验证三件事：

1. 无权限账号访问带 middleware.Perm 的只读端点，必须得到 HTTP 200 + code 403；
2. 同一端点用 admin 访问不得是 403（证明权限判断真的按账号生效，而不是全站 403）；
3. 无权限账号执行一个“仅需登录、带 OperLog”的失败操作后，admin 能在
   /monitor/operlog/list 里查到该操作人的审计行（status=1 + error_msg）。

退出码：0 全部通过；1 存在失败（CI 失败）。

用法：
    python scripts/parity/check_permissions_runtime.py \
        --base-url http://127.0.0.1:9989 \
        --no-perm-user noperm --no-perm-password 'Admin@123'

账号需预先在库里创建；推荐在测试库执行：
    INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, password, status, del_flag)
    VALUES (2, 100, 'noperm', '无权限', '00', '<bcrypt>', '0', '0');
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# 只读端点，避免回归脚本在误配置环境里产生写副作用。
PROTECTED_ENDPOINTS = [
    ("GET", "/monitor/operlog/list?pageNum=1&pageSize=1", "monitor:operlog:list"),
    ("GET", "/monitor/logininfor/list?pageNum=1&pageSize=1", "monitor:logininfor:list"),
    ("GET", "/system/dict/type/list?pageNum=1&pageSize=1", "system:dict:list"),
    ("GET", "/system/role/export?pageNum=1&pageSize=1", "system:role:export"),
]

AUDIT_URL = "/system/user/profile/updatePwd?oldPassword=Wrong%40123&newPassword=Admin%40456"


def request(base_url, method, path, token=None, body=None, timeout=15):
    url = base_url.rstrip("/") + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except ValueError:
        payload = {"_raw": raw[:200].decode("utf-8", "replace")}
    return status, payload


def login(base_url, username, password):
    status, payload = request(
        base_url, "POST", "/login", body={"username": username, "password": password}
    )
    token = payload.get("token")
    if status != 200 or not token:
        raise SystemExit(
            "登录失败 user=%s http=%s resp=%s" % (username, status, json.dumps(payload, ensure_ascii=False))
        )
    return token


def main():
    parser = argparse.ArgumentParser(description="无权限账号的运行时权限与审计冒烟")
    parser.add_argument("--base-url", default=os.getenv("CARMONIT_BASE_URL", "http://127.0.0.1:9989"))
    parser.add_argument("--admin-user", default=os.getenv("CARMONIT_PARITY_ADMIN_USER", "admin"))
    parser.add_argument("--admin-password", default=os.getenv("CARMONIT_PARITY_ADMIN_PASSWORD", "Admin@123"))
    parser.add_argument("--no-perm-user", default=os.getenv("CARMONIT_PARITY_NOPERM_USER", "noperm"))
    parser.add_argument("--no-perm-password", default=os.getenv("CARMONIT_PARITY_NOPERM_PASSWORD", "Admin@123"))
    parser.add_argument("--skip-audit", action="store_true", help="只跑 403 矩阵，不验证 sys_oper_log")
    args = parser.parse_args()

    admin_token = login(args.base_url, args.admin_user, args.admin_password)
    noperm_token = login(args.base_url, args.no_perm_user, args.no_perm_password)

    failures = []
    print("== 无权限账号 403 矩阵 ==")
    for method, path, perm in PROTECTED_ENDPOINTS:
        status, payload = request(args.base_url, method, path, token=noperm_token)
        code = payload.get("code")
        ok = status == 200 and code == 403
        print("%-4s %-45s 期望403 -> http=%s code=%s %s" % (
            method, path.split("?")[0], status, code, "OK" if ok else "FAIL"))
        if not ok:
            failures.append("noperm %s %s 未返回 403: http=%s code=%s" % (method, path, status, code))

        status, payload = request(args.base_url, method, path, token=admin_token)
        admin_code = payload.get("code")
        if admin_code == 403:
            failures.append("admin %s %s 也被 403（权限中间件未按账号生效）" % (method, path))
            print("     admin 校验 FAIL: code=403")

    if not args.skip_audit:
        print("== 非 admin 操作日志落行 ==")
        status, payload = request(args.base_url, "PUT", AUDIT_URL, token=noperm_token)
        if status != 200 or payload.get("code") == 403:
            failures.append("审计触发请求异常: http=%s resp=%s" % (status, json.dumps(payload, ensure_ascii=False)))
        else:
            query = urllib.parse.urlencode({
                "pageNum": "1", "pageSize": "10", "operName": args.no_perm_user,
            })
            status, payload = request(
                args.base_url, "GET", "/monitor/operlog/list?" + query, token=admin_token)
            rows = payload.get("rows") or []
            hit = [r for r in rows if "updatePwd" in str(r.get("operUrl", ""))]
            if status == 200 and hit:
                row = hit[0]
                print("命中审计行: operName=%s status=%s operUrl=%s" % (
                    row.get("operName"), row.get("status"), row.get("operUrl")))
                if str(row.get("status")) != "1":
                    failures.append("审计行 status 期望 1，实际 %s" % row.get("status"))
            else:
                failures.append("未在 sys_oper_log 查到 %s 的 updatePwd 审计行" % args.no_perm_user)

    if failures:
        print("\n失败 %d 项：" % len(failures))
        for item in failures:
            print(" - " + item)
        return 1
    print("\n全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
