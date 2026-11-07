# -*- coding: utf-8 -*-
"""双端（Java / Python）对比公共层：登录、HTTP、归一化、分类、db 感知的 Redis 读取。

本次接线（见 evidence/_par_report.md）：

  car-monit-api   Java  http://127.0.0.1:9902  Redis db0   openGauss 192.168.56.10:5432/RuoYi
  car-monit-api   Py    http://127.0.0.1:9901  （进程内 Redis shim）  同一份 application.yml 的库
  backend         Java  http://127.0.0.1:9788  Redis db0   MySQL 127.0.0.1:3307/carmonitdb
  backend         Py    http://127.0.0.1:9789  Redis db7   同一库

账号 admin；口令只从环境变量 ``PAR_PASSWORD`` 读（与本目录 ``_sweep_login.py`` 一致 ——
实时凭据不入库）。两端登录都要验证码，答案分别落在自己的 db 里。
地址与 db 号都可用环境变量覆盖（PAR_JAVA / PAR_PY / PAR_JAVA_DB / PAR_PY_DB）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

import httpx

JAVA = os.environ.get("PAR_JAVA", "http://127.0.0.1:9788")
PY = os.environ.get("PAR_PY", "http://127.0.0.1:9789")
JAVA_DB = int(os.environ.get("PAR_JAVA_DB", "0"))
PY_DB = int(os.environ.get("PAR_PY_DB", "7"))
API_JAVA = os.environ.get("PAR_API_JAVA", "http://127.0.0.1:9902")
API_PY = os.environ.get("PAR_API_PY", "http://127.0.0.1:9901")
USER = os.environ.get("PAR_USER", "admin")
PASSWORD = os.environ.get("PAR_PASSWORD", "")
REDIS_CLI = os.environ.get(
    "PAR_REDIS_CLI", "D:/work/Redis-8.10.2-Windows-x64-msys2/redis-cli.exe"
)
TOKENS = Path(__file__).with_name("_par_tokens.json")
TIMEOUT = float(os.environ.get("PAR_TIMEOUT", "180"))


# --------------------------------------------------------------------------- Redis
def r(*args, db: int = 0) -> str:
    cmd = [REDIS_CLI, "-h", "127.0.0.1", "-p", "6379", "-n", str(db), "--raw"] + [
        str(a) for a in args
    ]
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    ).stdout


def scan_keys(pattern: str, db: int = 0, cap: int = 200):
    out, cursor = [], "0"
    for _ in range(cap):
        chunk = r("scan", cursor, "MATCH", pattern, "COUNT", 1000, db=db)
        lines = [x for x in chunk.split("\n") if x]
        if not lines:
            break
        cursor, rest = lines[0], lines[1:]
        out += rest
        if cursor == "0":
            break
    return out


def read_key(key: str, db: int = 0):
    kind = r("type", key, db=db).strip()
    if kind == "none":
        return kind, ""
    if kind == "list":
        return kind, r("lrange", key, 0, -1, db=db)
    if kind == "hash":
        return kind, r("hgetall", key, db=db)
    if kind == "set":
        return kind, r("smembers", key, db=db)
    if kind == "zset":
        return kind, r("zrange", key, 0, -1, db=db)
    return kind, r("get", key, db=db)


def exists(key: str, db: int) -> bool:
    return r("exists", key, db=db).strip() == "1"


# --------------------------------------------------------------------------- HTTP
def call(base: str, path: str, token: str | None = None, method: str = "GET",
         body=None, params: dict | None = None, timeout: float = TIMEOUT):
    """Return (status, bytes, ctype); status is -1 on transport failure."""
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        # trust_env=False：环境里有 HTTP_PROXY/DevSidecar，本机端口不能被代理劫走
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            response = client.request(
                method, base + path, headers=headers,
                json=body if body is not None else None, params=params,
            )
        return response.status_code, response.content, response.headers.get("content-type", "")
    except Exception as exc:  # noqa: BLE001 - harness must not die on one endpoint
        return -1, ("%s: %s" % (type(exc).__name__, exc)).encode(), ""


def req(base, path, token=None, method="GET", body=None, params=None):
    """Parsed JSON body; non-JSON becomes ``__raw__`` so attachment streams stay visible."""
    status, raw, ctype = call(base, path, token, method, body, params)
    try:
        out = json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"__raw__": raw[:300].decode("utf-8", "ignore"), "__status__": status,
                "__ctype__": ctype, "__len__": len(raw)}
    if isinstance(out, dict):
        out.setdefault("__status__", status)
        out.setdefault("__ctype__", ctype)
    return out


def jwt_claims(token: str) -> dict:
    import base64

    part = token.split(".")[1]
    part += "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part))


def login(base: str, db: int) -> str:
    """Mint a session on one end; the captcha answer lives in that end's own Redis db."""
    if not PASSWORD:
        raise RuntimeError("请先 export PAR_PASSWORD=<admin 口令>（凭据不入库，见模块头）")
    plain = req(base, "/login", method="POST",
                body={"username": USER, "password": PASSWORD, "code": "", "uuid": ""})
    if plain.get("code") == 200 and plain.get("token"):
        return plain["token"]

    captcha = req(base, "/captchaImage")
    uuid = captcha.get("uuid")
    answer = r("get", "captcha_codes:" + uuid, db=db).strip().strip('"') if uuid else ""
    out = req(base, "/login", method="POST",
              body={"username": USER, "password": PASSWORD, "code": answer, "uuid": uuid})
    if "token" not in out:
        raise RuntimeError("登录失败 %s (db=%s captcha=%r): %s" % (
            base, db, answer, json.dumps(out, ensure_ascii=False)[:220]))
    return out["token"]


def tokens(refresh: bool = False) -> dict:
    """Log into both ends once, reuse within a run.

    缓存必须按两端地址+db 分键：换实例（例如把 Python 端钉到另一个 api/db）后
    旧 token 在对端解析不出会话，会整批 401。
    """
    key = json.dumps({"java": JAVA, "python": PY, "java_db": JAVA_DB, "python_db": PY_DB},
                     sort_keys=True)
    if TOKENS.exists() and not refresh:
        try:
            cached = json.loads(TOKENS.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            cached = {}
        if (cached.get("key") == key and cached.get("java") and cached.get("python")
                and time.time() - cached.get("at", 0) < 3300):
            return cached
    fresh = {"key": key, "java": login(JAVA, JAVA_DB), "python": login(PY, PY_DB),
             "at": time.time()}
    TOKENS.write_text(json.dumps(fresh), encoding="utf-8")
    return fresh


# --------------------------------------------------------------------------- SQL
MYSQL_CLI = os.environ.get(
    "PAR_MYSQL_CLI", "D:/work/mysql-8.0.30-winx64/bin/mysql.exe"
)
MYSQL_ARGS = ["-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot", "-N", "-B"]


def sql(statement: str, db: str = "carmonitdb"):
    return subprocess.run([MYSQL_CLI] + MYSQL_ARGS + ["-e", statement, db],
                          capture_output=True, text=True, errors="ignore")


# --------------------------------------------------------------------------- 归一化
DT_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
HEX32_RE = re.compile(r"\b[0-9a-f]{32}\b")
LONG_ID_RE = re.compile(r"\b\d{15,20}\b")
NOISE_KEYS = {"timestamp", "random", "uuid", "fileName", "accessBy", "infoId", "operId"}


def norm(value, noise=()):
    if isinstance(value, dict):
        return {k: ("<NOISE>" if k in NOISE_KEYS or k in noise else norm(v, noise))
                for k, v in value.items()}
    if isinstance(value, list):
        return [norm(v, noise) for v in value]
    if isinstance(value, str):
        s = DT_RE.sub("<DT>", value)
        s = UUID_RE.sub("<UUID>", s)
        s = HEX32_RE.sub("<HEX32>", s)
        s = LONG_ID_RE.sub("<ID>", s)
        return s
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, int) and abs(value) > 10 ** 14:
        return "<ID>"
    return value


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def deep_diff(a, b, path="", out=None):
    """Record every difference with a kind, because "differs" has several meanings.

    TYPE       int vs "int"（StringTypeHandler 类问题）
    VALUE      同形状不同内容（真差异）
    NULL-OMIT  一端给 null，另一端整个键缺失
    MISSING    键只在一端存在
    """
    out = [] if out is None else out
    here = path or "$"

    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key in ("__status__", "__ctype__", "__len__"):
                continue
            sub = "%s.%s" % (here, key)
            if key not in a:
                out.append({"path": sub, "kind": "MISSING", "java": "<absent>", "py": b[key]})
            elif key not in b:
                out.append({"path": sub, "kind": "MISSING", "java": a[key], "py": "<absent>"})
            else:
                deep_diff(a[key], b[key], sub, out)
        return out

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"path": "%s.length" % here, "kind": "VALUE", "java": len(a), "py": len(b)})
        for i, (x, y) in enumerate(zip(a, b)):
            deep_diff(x, y, "%s[%d]" % (here, i), out)
        return out

    if a == b and type(a) is type(b):
        return out
    if isinstance(a, (bytes,)) or isinstance(b, (bytes,)):
        a, b = a.decode("utf-8", "ignore"), b.decode("utf-8", "ignore")
    if a is None or b is None:
        out.append({"path": here, "kind": "NULL-OMIT", "java": a, "py": b})
    elif isinstance(a, str) and _is_number(b) or isinstance(b, str) and _is_number(a):
        out.append({"path": here, "kind": "TYPE", "java": a, "py": b})
    elif _is_number(a) and _is_number(b) and float(a) == float(b):
        out.append({"path": here, "kind": "TYPE", "java": a, "py": b})
    else:
        out.append({"path": here, "kind": "VALUE", "java": a, "py": b})
    return out


def order_only(a, b) -> bool:
    """True when only the row order differs (no ORDER BY / collation dependent)."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    for key in ("rows", "data"):
        left, right = a.get(key), b.get(key)
        if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            if sorted(json.dumps(x, sort_keys=True, ensure_ascii=False, default=str) for x in left) == \
               sorted(json.dumps(x, sort_keys=True, ensure_ascii=False, default=str) for x in right):
                return True
    return False


def shape_of(value):
    if isinstance(value, dict):
        return {k: shape_of(v) for k, v in value.items()}
    if isinstance(value, list):
        return [shape_of(v) for v in value[:1]]
    return type(value).__name__
