#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""认证态全端点探针：登录 -> 携带 Bearer token 逐端点 GET -> 记录 RuoYi 业务码。

与 parity_probe.py 的区别：
  * parity_probe.py 只做免认证 GET，仅覆盖 /captchaImage、/ 两个端点；
  * 本探针支持用管理员账号登录，覆盖需要认证的全部业务端点，并对
    RuoYi「HTTP 200 但 body.code=401/403/500」的假绿做绝对失败断言。

设计要点：
  * 纯标准库，无 Windows 依赖，可在 GitHub runner (ubuntu-latest) 直接运行；
  * 认证方式按语言区分：
      - java   : POST /login 需要先取 /captchaImage 的 uuid，并从 Redis 读
                 captcha_codes:<uuid> 得到验证码答案（docker exec redis-cli）；
      - go/rust: POST /login 仅需 username/password（无验证码）；
      - python : 先尝试无验证码登录；若返回 code 需要验证码，再走 Redis 兜底。
  * 每个端点记录 status / 业务code / bytes / sha256 / latency / body 片段；
  * 绝对失败：业务 code ∈ {401,403,500} 或 HTTP>=500 -> endpoint 标 auth_fail；
  * 进程树 RSS 采样、稳定性二次探测沿用 parity_probe 的做法。

用法：
  python parity_auth_probe.py --variant java8 --label java8 \\
    --cmd "java -jar out/baseline.jar --server.port=19903" --port 19903 \\
    --endpoints scripts/v3/ops/parity/endpoints/backend-full.txt \\
    --auth-lang java --user admin --password '__SET_CARMONIT_ADMIN_PASSWORD__' \\
    --out out/java8.json --mode full --ready-timeout 300
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, signal, socket, subprocess, sys, threading, time
from pathlib import Path

IS_WIN = os.name == 'nt'

# ---------------------------------------------------------------- 进程树 RSS
def _tree_rss_linux(root_pid):
    try:
        pids = {}
        for d in os.listdir('/proc'):
            if not d.isdigit():
                continue
            pid = int(d)
            try:
                stat = open('/proc/%d/stat' % pid).read()
                ppid = int(stat.rsplit(')', 1)[1].split()[1])
                pids[pid] = ppid
            except Exception:
                continue
        want = {root_pid}
        changed = True
        while changed:
            changed = False
            for pid, ppid in pids.items():
                if ppid in want and pid not in want:
                    want.add(pid); changed = True
        total = 0.0
        for pid in want:
            try:
                for line in open('/proc/%d/status' % pid):
                    if line.startswith('VmRSS:'):
                        total += int(line.split()[1]) / 1024.0
                        break
            except Exception:
                pass
        return total if total > 0 else None
    except Exception:
        return None


def rss_mb(pid):
    if IS_WIN:
        return None, None
    cur = _tree_rss_linux(pid)
    return cur, cur


def port_open(port, timeout=1.0):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=timeout):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------- HTTP
def http_req(port, path, token=None, method='GET', body=None, timeout=20):
    import urllib.request, urllib.error
    url = 'http://127.0.0.1:%d%s' % (port, path)
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(); status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read(); status = e.code
    except Exception as e:
        return 0, b'', round((time.time() - t0) * 1000, 2), None, str(e)[:150]
    return status, raw, round((time.time() - t0) * 1000, 2), None, None


def parse_biz_code(raw):
    """解析 RuoYi AjaxResult 的 body.code；非 JSON/裸数组返回 None。"""
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    if isinstance(obj, dict) and 'code' in obj:
        try:
            return int(obj['code'])
        except Exception:
            return None
    return None


# ---------------------------------------------------------------- 认证
def redis_get_captcha(uuid, container='rd'):
    """从 docker redis 容器读 captcha_codes:<uuid>（Java 登录用）。"""
    key = 'captcha_codes:' + uuid
    cmds = [
        ['docker', 'exec', container, 'redis-cli', '-n', '0', '--raw', 'GET', key],
        ['docker', 'exec', container, 'redis-cli', 'GET', key],
    ]
    for cmd in cmds:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            val = (out.stdout or '').strip().strip('"').strip()
            if val and val.lower() not in ('nil', '(nil)'):
                return val
        except Exception:
            continue
    return ''


def login(port, lang, user, password):
    """返回 (token, info)。lang ∈ java|go|rust|python。"""
    # Java（及 python 兜底）需要验证码：先取 /captchaImage
    captcha_needed = lang in ('java', 'python')
    code, uuid = '', ''
    if captcha_needed:
        st, raw, _, _, err = http_req(port, '/captchaImage')
        try:
            obj = json.loads(raw)
            uuid = obj.get('uuid', '')
        except Exception:
            uuid = ''
        if uuid:
            code = redis_get_captcha(uuid)
    body = {'username': user, 'password': password}
    if captcha_needed:
        body['code'] = code
        body['uuid'] = uuid
    st, raw, _, _, err = http_req(port, '/login', method='POST', body=body)
    biz = parse_biz_code(raw)
    try:
        obj = json.loads(raw)
    except Exception:
        obj = {}
    token = obj.get('token') if isinstance(obj, dict) else None
    info = {'http': st, 'code': biz, 'captcha_uuid': uuid, 'captcha': code,
            'msg': obj.get('msg') if isinstance(obj, dict) else None, 'err': err}
    if not token:
        # python 可能不需要验证码：去掉 code/uuid 再试一次
        if captcha_needed and lang == 'python':
            st, raw, _, _, err = http_req(port, '/login', method='POST',
                                          body={'username': user, 'password': password})
            try:
                token = json.loads(raw).get('token')
            except Exception:
                token = None
            info['retry_nocaptcha'] = {'http': st, 'token': bool(token)}
    return token, info


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', required=True)
    ap.add_argument('--label', default='auth')
    ap.add_argument('--cmd', required=True)
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--endpoints', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--auth-lang', default='java', choices=['java', 'go', 'rust', 'python'])
    ap.add_argument('--user', default='admin')
    ap.add_argument('--password', default='')
    ap.add_argument('--password-env', default='AUTH_PASS',
                    help='env var to read password from (avoids argv exposure)')
    ap.add_argument('--ready-timeout', type=int, default=300)
    ap.add_argument('--mode', choices=['full', 'lite'], default='full')
    ap.add_argument('--check-stability', action='store_true')
    a = ap.parse_args()
    # 密码优先从环境变量读取，避免出现在 argv/进程列表；argv 值仅作本地测试兜底
    password = os.environ.get(a.password_env) or a.password or '__SET_CARMONIT_ADMIN_PASSWORD__'

    endpoints = [l.strip() for l in Path(a.endpoints).read_text(encoding='utf-8').splitlines()
                 if l.strip() and not l.startswith('#')]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    out = {'label': a.label, 'variant': a.variant, 'auth_lang': a.auth_lang,
           'endpoint_count': len(endpoints), 'startup_ms': None, 'peak_rss_mb': None,
           'login': None, 'endpoints': [], 'error': None,
           'auth_fail_count': 0, 'diff_ready': 0}

    t0 = time.time()
    if IS_WIN:
        proc = subprocess.Popen(a.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        proc = subprocess.Popen(a.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                start_new_session=True)
    logf = open(a.out + '.app.log', 'wb')
    peak = [0.0]
    stop = threading.Event()

    def sampler():
        while not stop.is_set():
            cur, pk = rss_mb(proc.pid)
            v = pk or cur
            if v and v > peak[0]:
                peak[0] = v
            time.sleep(0.5)

    def pump():
        try:
            for chunk in iter(lambda: proc.stdout.read(4096), b''):
                logf.write(chunk); logf.flush()
        except Exception:
            pass

    threading.Thread(target=sampler, daemon=True).start()
    threading.Thread(target=pump, daemon=True).start()

    ready = False
    while time.time() - t0 < a.ready_timeout:
        if proc.poll() is not None:
            out['error'] = 'process exited early rc=%s' % proc.returncode
            break
        if port_open(a.port):
            ready = True
            break
        time.sleep(0.3)
    out['startup_ms'] = int((time.time() - t0) * 1000)
    out['peak_rss_mb'] = round(peak[0], 1)

    if ready:
        token, login_info = login(a.port, a.auth_lang, a.user, password)
        out['login'] = login_info
        if not token:
            out['error'] = 'login failed: %s' % json.dumps(login_info, ensure_ascii=False)[:300]
        else:
            rows = []
            for ep in endpoints:
                # 支持 "METHOD PATH" 前缀，默认 GET
                parts = ep.split(None, 1)
                method, path = (parts[0].upper(), parts[1]) if len(parts) == 2 and parts[0].upper() in (
                    'GET', 'POST', 'PUT', 'DELETE') else ('GET', ep)
                st, raw, ms, _, err = http_req(a.port, path, token=token, method=method)
                biz = parse_biz_code(raw)
                sha = hashlib.sha256(raw).hexdigest()[:16] if raw else ''
                stable = True
                sha2 = sha
                if a.check_stability and method == 'GET':
                    st2, raw2, _, _, _ = http_req(a.port, path, token=token, method=method)
                    sha2 = hashlib.sha256(raw2).hexdigest()[:16] if raw2 else ''
                    stable = (st == st2 and sha == sha2)
                # 绝对失败断言：RuoYi 业务码 401/403/500 或 HTTP>=500
                auth_fail = (biz in (401, 403, 500)) or (st >= 500) or (st == 401)
                if auth_fail:
                    out['auth_fail_count'] += 1
                # 可作为对比输入的端点：HTTP 200 且业务码 200 或非 RuoYi 信封（如裸对象）
                if st == 200 and biz in (None, 200):
                    out['diff_ready'] += 1
                rows.append({'endpoint': path, 'method': method, 'status': st, 'biz_code': biz,
                             'bytes': len(raw), 'latency_ms': ms, 'sha256': sha, 'sha256_2nd': sha2,
                             'stable': stable, 'auth_fail': auth_fail,
                             'body': raw.decode('utf-8', 'replace')[:6000] if a.mode == 'full' else '',
                             'error': err})
            out['endpoints'] = rows
    elif not out['error']:
        out['error'] = 'not ready within %ss' % a.ready_timeout

    stop.set()
    try:
        if IS_WIN:
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try: proc.terminate()
        except Exception: pass
    try: proc.wait(timeout=15)
    except Exception:
        try: proc.kill()
        except Exception: pass
    try: logf.close()
    except Exception: pass

    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('AUTH_PROBE_DONE variant=%s ready=%s ep=%d diff_ready=%d auth_fail=%d err=%s' % (
        a.variant, ready, len(out['endpoints']), out['diff_ready'], out['auth_fail_count'], out['error']))


if __name__ == '__main__':
    main()
