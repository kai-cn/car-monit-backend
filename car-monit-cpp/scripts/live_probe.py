#!/usr/bin/env python3
"""带合法 token 的实机探针：对指定路径发真实请求，打印 HTTP 状态 + 业务 code + 响应片段。

token 由 Redis 里现存的 login_tokens:* 会话签发（scripts/make_token.py 的算法，
与 Java TokenService + jjwt 完全等价），因此这条链路同时验证了
「JWT 验签 → FastJson2 LoginUser 反序列化 → 权限拦截 → 业务处理」四段。

用法：
    python scripts/live_probe.py --port 9990 /base/cdc/status /system/user/list
    python scripts/live_probe.py --verb DELETE /base/cdc/dead-letters/clear
    echo /login | xargs ...   # 也可从 stdin 一次喂一批路径
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_token import Resp  # noqa: E402

SECRET = "abcdefghijklmnopqrstuvwxyz"
CLAIM = "login_user_key"


def b64u(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def jwt_for(uuid, key=None):
    k = key or base64.b64decode(SECRET + "=" * ((4 - len(SECRET) % 4) % 4))
    h = b64u(json.dumps({"alg": "HS512"}, separators=(",", ":")).encode())
    p = b64u(json.dumps({CLAIM: uuid}, separators=(",", ":")).encode())
    return h + "." + p + "." + b64u(hmac.new(k, (h + "." + p).encode(), hashlib.sha512).digest())


def curl(base, path, token, verb="GET", extra=None):
    cmd = ["curl", "-s", "--ssl-no-revoke", "-o", "-", "-w", "\\n%{http_code}",
           "-X", verb, "-H", "Authorization: Bearer " + token]
    for e in extra or []:
        cmd += ["-H", e]
    cmd.append(base + path)
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    body = r.stdout.decode("utf-8", "replace")
    code = body.rsplit("\n", 1)[-1].strip() if "\n" in body else "?"
    payload = body[: body.rfind("\n")] if "\n" in body else body
    return code, payload


def business_code(payload):
    try:
        j = json.loads(payload)
    except Exception:
        return None
    return j.get("code") if isinstance(j, dict) else None


def find_live_session(port, host="127.0.0.1"):
    """挑一个仍然有效的会话：签发后打 /getInfo，只有 code==200 才算能用"""
    r = Resp(host, 6379)
    keys = r.cmd("KEYS", "login_tokens:*") or []
    # 剩余 TTL 长的优先
    scored = []
    for k in keys:
        k = k.decode() if isinstance(k, bytes) else k
        ttl = r.cmd("TTL", k)
        if isinstance(ttl, int) and ttl > 60:
            scored.append((ttl, k.split(":", 1)[1]))
    scored.sort(reverse=True)
    base = f"http://{host}:{port}"
    for _, uuid in scored[:30]:
        code, payload = curl(base, "/getInfo", jwt_for(uuid))
        if business_code(payload) == 200:
            return uuid, payload
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9990)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--verb", default="GET")
    ap.add_argument("--token", help="直接指定 token，跳过会话探测")
    ap.add_argument("--header", action="append", help="额外请求头，可重复")
    ap.add_argument("paths", nargs="*", help="留空则从 stdin 逐行读取")
    args = ap.parse_args()

    base = f"http://{args.host}:{args.port}"
    token = args.token or ""
    if not token:
        uuid, info = find_live_session(args.port, args.host)
        if not uuid:
            print("!! 没有任何可用会话（Redis 里 login_tokens:* 全部失效？）", file=sys.stderr)
            return 2
        token = jwt_for(uuid)
        print(f"# 使用会话 {uuid}")
    paths = args.paths or [l.strip() for l in sys.stdin if l.strip() and not l.startswith("#")]

    bad = 0
    for p in paths:
        code, payload = curl(base, p, token, args.verb, args.header)
        bc = business_code(payload)
        flag = "OK " if bc == 200 else "ERR"
        if bc != 200:
            bad += 1
        print(f"{flag} http={code} code={bc} {args.verb} {p} :: {payload[:160]}")
    print(f"# {len(paths)} 个请求，{len(paths) - bad} 成功，{bad} 非成功")
    return 0


if __name__ == "__main__":
    sys.exit(main())
