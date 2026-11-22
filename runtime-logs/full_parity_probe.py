#!/usr/bin/env python3

#
# @description 历史脚本 full_parity_probe.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage python full_parity_probe.py [args]；具体参数以脚本 argparse 或源码说明为准。
# @dependencies Java 运行时；Python 3 标准库及脚本原有第三方依赖
#
# 口令只从环境变量读取（CI_ADMIN_PASSWORD），不写文件、不打印、不进 out/*.json。
#
#
#
#
#
# 用法：
#
#
# python full_parity_probe.py --variant java-v3 --port 19903 \
#
#
# --cmd "java -jar out/baseline.jar --server.port=19903" \
#
#
# --endpoints out/endpoints.txt --out out/java-v3.json
#
from __future__ import annotations

import argparse, hashlib, json, os, signal, socket, subprocess, sys, threading, time

from pathlib import Path



IS_WIN = os.name == "nt"





def port_open(port: int) -> bool:

    try:

        with socket.create_connection(("127.0.0.1", port), timeout=1):

            return True

    except OSError:

        return False





def http_get(port: int, path: str, headers: dict, timeout: int = 20):

    import urllib.request, urllib.error

    url = "http://127.0.0.1:%d%s" % (port, path)

    t0 = time.time()

    try:

        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=timeout) as r:

            body, code = r.read(), r.status

    except urllib.error.HTTPError as e:

        body, code = e.read(), e.code

    except Exception as e:

        return 0, b"", round((time.time() - t0) * 1000, 2), str(e)[:180]

    return code, body, round((time.time() - t0) * 1000, 2), None





def do_login(port: int, user: str, password: str) -> str:

    import urllib.request

    body = json.dumps({"username": user, "password": password, "code": "", "uuid": ""}).encode()

    req = urllib.request.Request("http://127.0.0.1:%d/login" % port, data=body, method="POST",

                                 headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=30) as r:

        data = json.loads(r.read().decode("utf-8", "replace"))

    token = data.get("token") or (data.get("data") or {}).get("token")

    if not token:

        raise RuntimeError("login failed code=%s msg=%s" % (data.get("code"), data.get("msg")))

    return token





def main() -> None:

    ap = argparse.ArgumentParser()

    ap.add_argument("--variant", required=True)

    ap.add_argument("--port", type=int, required=True)

    ap.add_argument("--cmd", required=True)

    ap.add_argument("--endpoints", required=True)

    ap.add_argument("--out", required=True)

    ap.add_argument("--user", default="admin")

    ap.add_argument("--password-env", default="CI_ADMIN_PASSWORD")

    ap.add_argument("--ready-timeout", type=int, default=300)

    ap.add_argument("--mode", choices=["full", "reachability"], default="full")

    ap.add_argument("--check-stability", action="store_true")

    a = ap.parse_args()



    password = os.environ.get(a.password_env, "")

    if not password:

        sys.exit("password env %s missing" % a.password_env)

    endpoints = [l.strip() for l in Path(a.endpoints).read_text(encoding="utf-8").splitlines() if l.strip()]



    logf = open(a.out + ".app.log", "wb")

    proc = subprocess.Popen(a.cmd, shell=True, stdout=logf, stderr=subprocess.STDOUT,

                            start_new_session=not IS_WIN)

    out = {"variant": a.variant, "endpoint_count": len(endpoints), "endpoints": [],

           "startup_ms": None, "login": None, "error": None}



    ready = False

    t0 = time.time()

    while time.time() - t0 < a.ready_timeout:

        if proc.poll() is not None:

            out["error"] = "process exited rc=%s" % proc.returncode

            break

        if port_open(a.port):

            ready = True

            break

        time.sleep(0.5)

    out["startup_ms"] = int((time.time() - t0) * 1000)



    if ready:

        # 登录：token 只保存在内存变量，不写 out、不打印

        token = None

        for _ in range(60):

            try:

                token = do_login(a.port, a.user, password)

                break

            except Exception:

                time.sleep(1)

        if not token:

            out["error"] = "login_failed"

        else:

            out["login"] = "ok"  # 仅状态，不含 token

            headers = {"Authorization": "Bearer " + token}

            rows = []

            for ep in endpoints:

                code, body, ms, err = http_get(a.port, ep, headers)

                sha = hashlib.sha256(body).hexdigest()[:16] if body else ""

                sha2, stable = sha, True

                if a.check_stability:

                    c2, b2, _, _ = http_get(a.port, ep, headers)

                    sha2 = hashlib.sha256(b2).hexdigest()[:16] if b2 else ""

                    stable = (code == c2 and sha == sha2)

                rows.append({"endpoint": ep, "status": code, "bytes": len(body),

                             "latency_ms": ms, "sha256": sha, "sha256_2nd": sha2, "stable": stable,

                             "body": body.decode("utf-8", "replace")[:4000]

                             if a.mode == "full" and body else "", "error": err})

            out["endpoints"] = rows



    # 清理进程

    try:

        if IS_WIN:

            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)

        else:

            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

    except Exception:

        proc.terminate()

    try:

        proc.wait(timeout=15)

    except Exception:

        proc.kill()

    logf.close()



    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("PROBE_DONE variant=%s ready=%s login=%s ep=%d err=%s" %

          (a.variant, ready, out["login"], len(out["endpoints"]), out["error"]))





if __name__ == "__main__":

    main()

