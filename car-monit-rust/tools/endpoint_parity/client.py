# -*- coding: utf-8 -*-
"""两端登录 + HTTP 客户端。

验证码答案直接从 Redis 的 `captcha_codes:{uuid}` 读（Java 用 FastJson2 存，可能是 `23L`）。
账号只从环境变量取，不写进仓库：

    PARITY_USER / PARITY_PASSWORD      两端登录账号（必需，无默认值）
    PARITY_REDIS_HOST / PARITY_REDIS_PORT   默认 127.0.0.1:6379
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


def redis_command(*parts):
    sock = socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=5)
    try:
        payload = b"*%d\r\n" % len(parts)
        for part in parts:
            raw = part.encode("utf-8") if isinstance(part, str) else part
            payload += b"$%d\r\n" % len(raw) + raw + b"\r\n"
        sock.sendall(payload)
        handle = sock.makefile("rb")
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


def redis_get(key: str):
    return redis_command("GET", key)


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


def redis_cmd(*parts):
    """执行任意 Redis 命令（返回 RESP 解码结果；错误返回异常对象）。"""
    sock = socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=10)
    try:
        payload = b"*%d\r\n" % len(parts)
        for part in parts:
            raw = part.encode("utf-8") if isinstance(part, str) else part
            payload += b"$%d\r\n" % len(raw) + raw + b"\r\n"
        sock.sendall(payload)
        return _read_reply(sock.makefile("rb"))
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


def login(base: str, user: str = None, password: str = None):
    """按 Java 的登录流程取 token；验证码关闭时 code/uuid 传空。"""
    user = user if user is not None else os.environ.get("PARITY_USER")
    password = password if password is not None else os.environ.get("PARITY_PASSWORD")
    if not user or not password:
        raise SystemExit("需要登录账号：请设置环境变量 PARITY_USER / PARITY_PASSWORD")
    status, _, body = http("GET", base + "/captchaImage", timeout=10)
    try:
        info = json.loads(body)
    except Exception:
        return None, status, {"error": "captchaImage 非 JSON: %s" % body[:120]}
    uuid = info.get("uuid")
    code = ""
    if info.get("captchaEnabled"):
        raw = (redis_get("captcha_codes:%s" % uuid) or "").strip().strip('"')
        code = raw[:-1] if raw.endswith("L") else raw
    status, _, body = http(
        "POST", base + "/login", body={"username": user, "password": password, "code": code, "uuid": uuid}, timeout=20
    )
    try:
        payload = json.loads(body)
    except Exception:
        payload = {}
    return payload.get("token"), status, payload
