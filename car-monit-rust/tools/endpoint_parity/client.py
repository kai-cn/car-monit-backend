# -*- coding: utf-8 -*-
"""两端登录 + HTTP 客户端。

验证码答案直接从 Redis 的 `captcha_codes:{uuid}` 读（Java 用 FastJson2 存，可能是 `23L`）。
账号只从环境变量取，不写进仓库：

    PARITY_USER / PARITY_PASSWORD      两端登录账号（必需，无默认值）
    PARITY_REDIS_HOST / PARITY_REDIS_PORT   默认 127.0.0.1:6379
    PARITY_REDIS_DB_JAVA / PARITY_REDIS_DB_RUST   两端各自的 Redis db 序号
        （两端不共用 db，验证码与缓存都按各自的 db 取；默认都是 0）
"""
from __future__ import annotations

import json
import os
import socket
import ssl
import urllib.error
import urllib.request

REDIS_HOST = os.environ.get("PARITY_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("PARITY_REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("PARITY_REDIS_DB", "0"))
# backend-Java(9988)+api-Java(9902) 共用 db0；backend-Rust(9990)+api-Rust(9911) 共用 db15。
REDIS_DB_JAVA = int(os.environ.get("PARITY_REDIS_DB_JAVA", str(REDIS_DB)))
REDIS_DB_RUST = int(os.environ.get("PARITY_REDIS_DB_RUST", "15"))
JAVA_BASE = os.environ.get("PARITY_JAVA_BASE", "http://127.0.0.1:9988").rstrip("/")
RUST_BASE = os.environ.get("PARITY_RUST_BASE", "http://127.0.0.1:9990").rstrip("/")


def redis_db_for(base: str = None) -> int:
    """按端选 db：验证码、缓存键都只在写入那端的 db 里。"""
    if base is None:
        return REDIS_DB
    trimmed = base.rstrip("/")
    if trimmed == RUST_BASE:
        return REDIS_DB_RUST
    if trimmed == JAVA_BASE:
        return REDIS_DB_JAVA
    return REDIS_DB


def redis_command(*parts, db: int = None):
    sock = socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=5)
    try:
        handle = sock.makefile("rb")
        if db is not None and db != 0:
            sock.sendall(b"*2\r\n$6\r\nSELECT\r\n$%d\r\n%d\r\n" % (len(str(db)), db))
            handle.readline()  # +OK
        payload = b"*%d\r\n" % len(parts)
        for part in parts:
            raw = part.encode("utf-8") if isinstance(part, str) else part
            payload += b"$%d\r\n" % len(raw) + raw + b"\r\n"
        sock.sendall(payload)
        reply = handle.readline().strip()
        if reply == b"$-1":
            return None
        if not reply.startswith(b"$"):
            return reply.decode("utf-8", errors="replace")
        size = int(reply[1:])
        data = handle.read(size)
        return data.decode("utf-8", errors="replace")
    finally:
        sock.close()


def redis_get(key: str, db: int = None):
    return redis_command("GET", key, db=REDIS_DB if db is None else db)


def _read_reply(handle):
    line = handle.readline()
    if not line:
        raise RuntimeError("Redis 连接提前关闭")
    kind, rest = line[0:1], line[1:].strip()
    if kind == b"+":
        return rest.decode("utf-8", errors="replace")
    if kind == b":":
        return int(rest)
    if kind == b"-":
        return RuntimeError(rest.decode("utf-8", errors="replace"))
    if kind == b"$":
        size = int(rest)
        if size == -1:
            return None
        data = handle.read(size)
        handle.read(2)
        return data.decode("utf-8", errors="replace")
    if kind == b"*":
        count = int(rest)
        return None if count == -1 else [_read_reply(handle) for _ in range(count)]
    return rest.decode("utf-8", errors="replace")


def redis_cmd(*parts, db: int = None):
    """执行任意 Redis 命令（返回 RESP 解码结果；错误返回异常对象）。"""
    sock = socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=10)
    try:
        handle = sock.makefile("rb")
        if db is not None and db != 0:
            sock.sendall(b"*2\r\n$6\r\nSELECT\r\n$%d\r\n%d\r\n" % (len(str(db)), db))
            _read_reply(handle)
        payload = b"*%d\r\n" % len(parts)
        for part in parts:
            raw = part.encode("utf-8") if isinstance(part, str) else part
            payload += b"$%d\r\n" % len(raw) + raw + b"\r\n"
        sock.sendall(payload)
        return _read_reply(handle)
    finally:
        sock.close()


def http(method, url, token=None, body=None, timeout=30, headers=None):
    """返回 (status, headers, body)；网络异常时 status=-1，body 是错误文本。"""
    data = None
    sent = dict(headers or {})
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        sent["Content-Type"] = "application/json;charset=UTF-8"
    if token:
        sent["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=data, headers=sent, method=method)
    # 默认校验证书；只有显式 PARITY_INSECURE_TLS=1 才跳过（本地自签 https 场景）。
    context = None
    if url.startswith("https") and os.environ.get("PARITY_INSECURE_TLS") == "1":
        context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()
    except Exception as error:  # 连接失败/超时
        return -1, {}, str(error).encode("utf-8")


def login(base: str, user: str = None, password: str = None, redis_db: int = None):
    """按 Java 的登录流程取 token；验证码关闭时 code/uuid 传空。

    验证码写在**登录那端**的 Redis db 里（backend-Java=db0，backend-Rust=db15），
    所以按 `redis_db_for(base)` 选库，除非调用方显式指定。
    """
    user = user if user is not None else os.environ.get("PARITY_USER")
    password = password if password is not None else os.environ.get("PARITY_PASSWORD")
    if not user or not password:
        raise SystemExit("需要登录账号：请设置环境变量 PARITY_USER / PARITY_PASSWORD")
    db = redis_db if redis_db is not None else redis_db_for(base)
    status, _, body = http("GET", base + "/captchaImage", timeout=10)
    try:
        info = json.loads(body)
    except Exception:
        return None, status, {"error": "captchaImage 非 JSON: %s" % body[:120]}
    uuid = info.get("uuid")
    code = ""
    if info.get("captchaEnabled"):
        raw = (redis_get("captcha_codes:%s" % uuid, db=db) or "").strip().strip('"')
        code = raw[:-1] if raw.endswith("L") else raw
    status, _, body = http(
        "POST", base + "/login", body={"username": user, "password": password, "code": code, "uuid": uuid}, timeout=20
    )
    try:
        payload = json.loads(body)
    except Exception:
        payload = {}
    return payload.get("token"), status, payload
