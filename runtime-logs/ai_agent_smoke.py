#!/usr/bin/env python3

#
# @description 历史脚本 ai_agent_smoke.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage python ai_agent_smoke.py [args]；具体参数以脚本 argparse 或源码说明为准。
# @dependencies Python 3 标准库及脚本原有第三方依赖
#
# 启动 FastAPI 子进程（uvicorn），等待 /health，然后以真实 HTTP 调用：
#
#
# POST /ai/agent/query（带 X-Agent-Key）→ 断言契约
#
#
# POST /ai/agent/query（无令牌）→ 断言 403
#
#
# 全过程不需要真实 LLM key（AI_AGENT_API_KEY 为空 → FakeAgentModel）。
#
#
#
#
#
# 【Java 对照】等价于 SpringBootTest + MockMvc 冒烟，但走真实 socket。
#
from __future__ import annotations



import json

import os

import socket

import subprocess

import sys

import time

import urllib.error

import urllib.request



PORT = 9911

BASE = "http://127.0.0.1:%d" % PORT





def _wait_port(port: int, seconds: int) -> bool:

    deadline = time.time() + seconds

    while time.time() < deadline:

        try:

            with socket.create_connection(("127.0.0.1", port), timeout=1):

                return True

        except OSError:

            time.sleep(0.4)

    return False





def _post(path: str, body: dict, token: str | None) -> tuple[int, dict]:

    headers = {"Content-Type": "application/json"}

    if token:

        headers["X-Agent-Key"] = token

    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),

                                 headers=headers, method="POST")

    try:

        with urllib.request.urlopen(req, timeout=30) as r:

            return r.status, json.loads(r.read().decode("utf-8", "replace"))

    except urllib.error.HTTPError as e:

        return e.code, json.loads(e.read().decode("utf-8", "replace"))





def main() -> int:

    token = os.environ.get("AI_AGENT_ACCESS_TOKEN", "")

    if not token:

        print("FAIL: AI_AGENT_ACCESS_TOKEN missing")

        return 1

    env = dict(os.environ)

    env["AI_AGENT_API_KEY"] = ""  # FakeModel

    log = open("ai_agent_smoke_server.log", "wb")

    proc = subprocess.Popen(

        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",

         "--port", str(PORT), "--workers", "1"],

        cwd=os.getcwd(), env=env, stdout=log, stderr=subprocess.STDOUT)

    try:

        if not _wait_port(PORT, 90):

            print("FAIL: server not ready")

            return 1

        code, body = _post("/ai/agent/query", {"question": "你好", "session_id": "smoke"}, None)

        if code != 403:

            print("FAIL: no-token status=%s body=%s" % (code, body))

            return 1

        code, body = _post("/ai/agent/query", {"question": "你好", "session_id": "smoke"}, token)

        if code != 200:

            print("FAIL: authed status=%s body=%s" % (code, body))

            return 1

        expected = {"answer", "tool_calls", "trace_id", "rounds"}

        if set(body) != expected:

            print("FAIL: contract fields=%s" % sorted(body))

            return 1

        print("AI_AGENT_SMOKE_OK trace=%s rounds=%s tools=%d" %

              (body["trace_id"], body["rounds"], len(body["tool_calls"])))

        return 0

    finally:

        proc.terminate()

        try:

            proc.wait(timeout=10)

        except subprocess.TimeoutExpired:

            proc.kill()

        log.close()





if __name__ == "__main__":

    raise SystemExit(main())

