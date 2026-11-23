#!/usr/bin/env python3
"""
@description 在 WSL 中启动指定服务、按端点清单执行鉴权契约探测，并记录日志、结果和证据。
@author Tencent Hunyuan Hy
@date 2026-11-23 16:50:00
@usage python3 runtime-logs/local-parity-runner.py --app backend --lang java --out runtime-logs/local-parity-matrix/backend/java [--port 19903]
@dependencies Python 3、被测服务可执行文件、JUnit standalone 或内置 HTTP 探测逻辑。
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs')
JUNIT = Path('/mnt/d/work/runtime-logs/junit-platform-console-standalone.jar')
GEN = ROOT / 'generate_junit_suite.py'


def parse_args():
    """解析服务类型、语言、输出目录和可选启动命令。"""
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', choices=['backend', 'api'], required=True)
    ap.add_argument('--lang', choices=['java', 'python', 'go', 'cpp', 'rust'], required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--port', type=int, default=19903)
    ap.add_argument('--start', default='', help='shell command to start service; must stay in foreground')
    ap.add_argument('--skip-start', action='store_true')
    ap.add_argument('--no-contract', action='store_true')
    return ap.parse_args()


def wait_port(port: int, proc, log: Path) -> None:
    """等待 TCP 端口就绪，进程退出时输出日志尾部。"""
    for _ in range(180):
        if subprocess.run(['bash', '-c', f'(echo > /dev/tcp/127.0.0.1/{port}) 2>/dev/null'], capture_output=True).returncode == 0:
            return
        if proc is not None and proc.poll() is not None:
            raise SystemExit('SERVICE_EXITED\n' + log.read_text(encoding='utf-8', errors='replace')[-3000:])
        time.sleep(1)
    raise SystemExit('SERVICE_TIMEOUT')


def get_token(base_url: str) -> str:
    """从服务 /login 获取 Bearer token；无登录端点时返回空串。"""
    user = os.environ.get('CARMONIT_ADMIN_USER', '')
    password = os.environ.get('CARMONIT_ADMIN_PASSWORD', '')
    if not user or not password:
        return ''
    body = json.dumps({'username': user, 'password': password, 'code': '', 'uuid': ''}).encode()
    req = urllib.request.Request(base_url + '/login', data=body,
                                 headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ''
        return ''
    except Exception:
        return ''
    m = re.search(r'"token"\s*:\s*"([^"]+)"', text)
    return m.group(1) if m else ''


def main() -> None:
    """执行一次服务端到端契约探测，并保存 stdout/stderr、JUnit JSON 和摘要。"""
    a = parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for d in ['logs', 'generated', 'classes', 'contract-reports', 'load-reports']:
        (out / d).mkdir(exist_ok=True)
    ep = Path('/home/dev/IdeaProjects/car-monit-backend/scripts/v3/ops/parity/endpoints/backend-full.txt')
    if a.app == 'api':
        ep = Path('/home/dev/IdeaProjects/car-monit-api/scripts/v3/ops/parity/endpoints/api-full.txt')
    env = os.environ.copy()
    env.update({
        'BASE_URL': f'http://127.0.0.1:{a.port}',
        'OUT_DIR': str(out),
        'LOG_PATH': str(out / 'logs'),
        'HTTP_TIMEOUT_MS': '60000',
    })
    proc = None
    log = out / 'service.log'
    if not a.skip_start and a.start:
        lf = log.open('w', encoding='utf-8')
        proc = subprocess.Popen(['bash', '-lc', a.start], stdout=lf, stderr=subprocess.STDOUT, env=env)
        wait_port(a.port, proc, log)
    token = get_token(env['BASE_URL'])
    if token:
        env['ENDPOINT_HEADERS'] = 'Authorization: Bearer ' + token
    (out / 'auth.json').write_text(json.dumps({'token_present': bool(token)}, ensure_ascii=False, indent=2), encoding='utf-8')
    if not a.no_contract:
        subprocess.run(['python3', str(GEN), '--endpoints', str(ep), '--out', str(out / 'generated')], check=True)
        javac = subprocess.run(['javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-cp', str(JUNIT),
                                '-d', str(out / 'classes'), *map(str, (out / 'generated').glob('*.java'))],
                               text=True, capture_output=True)
        (out / 'javac.log').write_text(javac.stdout + javac.stderr, encoding='utf-8')
        if javac.returncode != 0:
            raise SystemExit('JAVAC_FAILED\n' + javac.stderr[-2000:])
        r = subprocess.run(['java', '-jar', str(JUNIT), 'execute', '--class-path', str(out / 'classes'),
                            '--select-class', 'com.ruoyi.parity.generated.EndpointContractTest',
                            '--details=summary', '--reports-dir', str(out / 'contract-reports')],
                           text=True, capture_output=True, env=env)
        (out / 'contract.log').write_text(r.stdout + r.stderr, encoding='utf-8')
        print('CONTRACT_RC', r.returncode)
    if proc is not None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    print('DONE', out)


if __name__ == '__main__':
    main()
