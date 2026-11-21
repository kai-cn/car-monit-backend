"""Throwaway: mint a real session on BOTH backends with the supplied credential.

No password rotation any more -- the account's real password bcrypt-matches the
pristine hash, so both backends are simply logged into. The credential is read
from ``SWEEP_PASSWORD`` because it is a live secret and never checked in.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

from app.common.constant.constants import CAPTCHA_CODE_KEY, TOKEN
from app.common.core.redis.redis_cache import get_redis_cache, reset_redis_cache

BACKENDS = {"java": "http://127.0.0.1:8090", "python": "http://127.0.0.1:9989"}
USER_NAME = "admin"
PASSWORD = os.environ.get("SWEEP_PASSWORD", "")
TOKENS = Path(__file__).with_name(".sweep_tokens.json")


def login(base: str) -> dict:
    body = {"username": USER_NAME, "password": PASSWORD, "code": "", "uuid": ""}
    response = httpx.post(base + "/login", json=body, timeout=60)
    payload = response.json()
    if payload.get("code") == 200:
        return payload

    # 验证码分支：Java 侧的 validateCaptcha 可能要求 code；答案就在 Redis 里。
    captcha = httpx.get(base + "/captchaImage", timeout=60).json()
    uuid = captcha.get("uuid")
    answer = get_redis_cache().get_cache_object(CAPTCHA_CODE_KEY + uuid)
    body.update({"code": str(answer), "uuid": uuid})
    response = httpx.post(base + "/login", json=body, timeout=60)
    return response.json()


def main() -> int:
    reset_redis_cache()
    get_redis_cache().delete_object("pwd_err_cnt:" + USER_NAME)

    tokens = {}
    failed = False
    for name, base in BACKENDS.items():
        payload = login(base)
        token = payload.get(TOKEN)
        print(
            "%-7s code=%s msg=%s token=%s"
            % (name, payload.get("code"), payload.get("msg"), (token or "")[:18] + "...")
        )
        if not token:
            failed = True
            continue
        tokens[name] = token

    if tokens:
        TOKENS.write_text(json.dumps(tokens), encoding="utf-8")
        print("tokens ->", TOKENS.name)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
