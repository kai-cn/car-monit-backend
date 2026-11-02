# -*- coding: utf-8 -*-
"""双端对比公共层：登录、HTTP 调用、归一化、db 感知的 Redis 读取。

环境约定（见 docs/PARITY-2026-11-02.md）：
  Java  http://127.0.0.1:9988  Redis db0   MySQL 127.0.0.1:3307/carmonitdb
  Go    http://127.0.0.1:9989  Redis db2   同一库
账号 admin / Admin@2025-；Java 登录需要验证码，答案从 db0 的 captcha_codes:<uuid> 读。
"""
import json
import re
import subprocess
import urllib.error
import urllib.request

JAVA = "http://127.0.0.1:9988"
GO = "http://127.0.0.1:9989"
REDIS_CLI = "D:/work/Redis-8.10.2-Windows-x64-msys2/redis-cli.exe"
MYSQL = "D:/work/mysql-8.0.30-winx64/bin/mysql.exe"
JAVA_DB, GO_DB = 0, 2
MYSQL_ARGS = ["-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot", "-N", "-B"]
MARK = "PARITY"


# --------------------------------------------------------------------------- Redis
def r(*args, db=0):
    cmd = [REDIS_CLI, "-h", "127.0.0.1", "-p", "6379", "-n", str(db), "--raw"] + [str(a) for a in args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="ignore").stdout


def scan(pattern, db=0):
    out, cursor = [], "0"
    for _ in range(200):
        chunk = r("scan", cursor, "MATCH", pattern, "COUNT", 1000, db=db)
        lines = [x for x in chunk.split("\n") if x]
        if not lines:
            break
        cursor, rest = lines[0], lines[1:]
        out += rest
        if cursor == "0":
            break
    return out


def read_key(key, db=0):
    t = r("type", key, db=db).strip()
    if t == "none":
        return t, ""
    if t == "list":
        return t, r("lrange", key, 0, -1, db=db)
    if t == "hash":
        return t, r("hgetall", key, db=db)
    if t == "set":
        return t, r("smembers", key, db=db)
    if t == "zset":
        return t, r("zrange", key, 0, -1, db=db)
    return t, r("get", key, db=db)


# --------------------------------------------------------------------------- SQL
def sql(statement, db="carmonitdb"):
    return subprocess.run([MYSQL] + MYSQL_ARGS + ["-e", statement, db],
                          capture_output=True, text=True, errors="ignore")


# --------------------------------------------------------------------------- HTTP
def call(base, path, token=None, method="GET", body=None, timeout=120):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type", "")
    except Exception as e:
        return -1, str(e).encode(), ""


def req(base, path, token=None, method="GET", body=None):
    """返回解析后的 JSON（非 JSON 时给 __raw__，便于区分附件流）。"""
    status, raw, ctype = call(base, path, token, method, body)
    try:
        out = json.loads(raw)
    except Exception:
        return {"__raw__": raw[:200].decode("utf-8", "ignore"), "__status__": status,
                "__ctype__": ctype}
    if isinstance(out, dict):
        out.setdefault("__status__", status)
        out.setdefault("__ctype__", ctype)
    return out


def jwt_claims(token):
    import base64
    part = token.split(".")[1]
    part += "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part))


def login_java():
    j = req(JAVA, "/captchaImage")
    uuid = j.get("uuid")
    ans = r("get", "captcha_codes:" + uuid, db=JAVA_DB).strip().strip('"') if uuid else ""
    out = req(JAVA, "/login", method="POST",
              body={"username": "admin", "password": "Admin@2025-", "code": ans, "uuid": uuid})
    if "token" not in out:
        raise RuntimeError("Java 登录失败: %s (captcha=%r)" % (json.dumps(out, ensure_ascii=False)[:200], ans))
    return out["token"]


def login_go():
    out = req(GO, "/login", method="POST", body={"username": "admin", "password": "Admin@2025-"})
    if "token" not in out:
        raise RuntimeError("Go 登录失败: %s" % json.dumps(out, ensure_ascii=False)[:200])
    return out["token"]


# --------------------------------------------------------------------------- 归一化
DT_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
HEX32_RE = re.compile(r"[0-9a-f]{32}")
LONG_ID_RE = re.compile(r"\b\d{15,20}\b")
MARK_RE = re.compile(MARK + r"[_A-Za-z0-9]*")

# 这些字段的值由运行态决定（时间、随机文件名、会话 id），对比时统一屏蔽
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
        return MARK_RE.sub("<PARITY>", s)
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, int) and abs(value) > 10 ** 14:
        return "<ID>"
    return value


def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in ("__status__", "__ctype__"):
                continue
            if k not in a:
                out.append((path + "/" + k, "<ABSENT_IN_JAVA>", b[k]))
            elif k not in b:
                out.append((path + "/" + k, a[k], "<ABSENT_IN_GO>"))
            else:
                out += diff(a[k], b[k], path + "/" + k)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path + "/len", len(a), len(b)))
        for i in range(min(len(a), len(b))):
            out += diff(a[i], b[i], path + "/%d" % i)
        return out
    if a != b:
        out.append((path, a, b))
    return out


def rand(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", n=5):
    import random
    return "".join(random.choice(alphabet) for _ in range(n))


def rand_digits(n=9):
    return rand("0123456789", n)
