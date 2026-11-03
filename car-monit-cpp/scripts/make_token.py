#!/usr/bin/env python3
"""签发一个与 Java TokenService 等价的 JWT（HS512 + jjwt 的 Base64 密钥语义）。

用法：
    python scripts/make_token.py                 # 从 Redis 现存的 login_tokens:* 里挑一个
    python scripts/make_token.py --uuid <uuid>   # 指定 uuid
    python scripts/make_token.py --mint          # 没有现存会话时，自己写一个 LoginUser 进 Redis

对应 Java:
    claims.put(Constants.LOGIN_USER_KEY, token);            # login_user_key
    Jwts.builder().setClaims(claims).signWith(SignatureAlgorithm.HS512, secret).compact()
密钥按 jjwt 的规则先做 Base64 解码（"abcdefghijklmnopqrstuvwxyz" -> 18 字节）。
"""
import argparse
import base64
import hashlib
import hmac
import json
import socket
import sys

SECRET = "abcdefghijklmnopqrstuvwxyz"
HEADER = {"alg": "HS512"}


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def make_token(uuid: str) -> str:
    key = base64.b64decode(SECRET + "=" * (-len(SECRET) % 4))
    header = b64url(json.dumps(HEADER, separators=(",", ":")).encode())
    payload = b64url(json.dumps({"login_user_key": uuid}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}".encode()
    sig = hmac.new(key, signing_input, hashlib.sha512).digest()
    return f"{header}.{payload}.{b64url(sig)}"


# ---------------- 最小 RESP 客户端（避免依赖 redis 包） ----------------
class Resp:
    def __init__(self, host="127.0.0.1", port=6379):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.f = self.sock.makefile("rb")

    def cmd(self, *args):
        out = [f"*{len(args)}\r\n".encode()]
        for a in args:
            b = a if isinstance(a, bytes) else str(a).encode("utf-8")
            out += [b"$%d\r\n" % len(b), b + b"\r\n"]
        self.sock.sendall(b"".join(out))
        return self._read()

    def _read(self):
        line = self.f.readline()
        if not line:
            raise IOError("redis closed")
        t, body = line[:1], line[1:].strip()
        if t == b"+":
            return body.decode("utf-8", "replace")
        if t == b"-":
            raise RuntimeError("redis error: " + body.decode())
        if t == b":":
            return int(body)
        if t == b"$":
            n = int(body)
            if n == -1:
                return None
            data = self.f.read(n + 2)[:n]
            return data
        if t == b"*":
            return [self._read() for _ in range(int(body))]
        return body.decode("utf-8", "replace")


def find_uuid(r: Resp):
    cursor = "0"
    while True:
        cursor, keys = r.cmd("SCAN", cursor, "MATCH", "login_tokens:*", "COUNT", 500)
        if keys:
            return keys[0][len("login_tokens:"):].decode() if isinstance(keys[0], bytes) else keys[0].split(":", 1)[1]
        if cursor == "0" or cursor == b"0":
            return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uuid", help="直接使用指定 uuid")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=6379)
    ap.add_argument("--header", action="store_true", help="输出完整 Authorization 头")
    args = ap.parse_args()

    uuid = args.uuid
    if not uuid:
        r = Resp(args.host, args.port)
        uuid = find_uuid(r)
    if not uuid:
        print("Redis 里没有 login_tokens:* 会话；先登录一个账号，或用 --uuid 指定", file=sys.stderr)
        return 2
    token = make_token(uuid)
    print(f"Authorization: Bearer {token}" if args.header else token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
