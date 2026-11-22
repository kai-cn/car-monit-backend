#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：local-junit-smoke.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Run generated JUnit contract/load suites locally against a deterministic stub.

Idea:
- cloud runs already exercised real Java services and language candidates.
- this local rerun verifies the harness itself works end-to-end without Docker:
  start a tiny local HTTP server, generate and compile the JUnit suites, run
  both suites, and save their reports as evidence.
- the stub is not a business service; it only proves the test scripts and Java
  suite are reproducible in the local environment.
"""
import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(r'D:\work\runtime-logs')
JAR = BASE / 'junit-platform-console-standalone.jar'
GEN = BASE / 'generate_junit_suite.py'
ENDPOINTS = BASE / 'api-endpoints-full.txt'
WORK = BASE / 'local-junit-smoke'
OUT = BASE / 'local-rerun-evidence'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({'path': self.path, 'status': 'ok'}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def run(args, env=None):
    e = None
    if env:
        import os
        e = dict(os.environ)
        e.update(env)
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', env=e)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def main():
    WORK.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    generated = WORK / 'generated'
    classes = WORK / 'classes'
    classes.mkdir(exist_ok=True)
    rc, txt = run([sys.executable, str(GEN), '--endpoints', str(ENDPOINTS), '--out', str(generated)])
    assert rc == 0, txt
    srcs = [str(p) for p in generated.glob('*.java')]
    rc, txt = run(['javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8',
                   '-cp', str(JAR), '-d', str(classes)] + srcs)
    assert rc == 0, txt

    server = ThreadingHTTPServer(('127.0.0.1', 19903), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(1)
    env = {'BASE_URL': 'http://127.0.0.1:19903', 'OUT_DIR': str(WORK),
           'VARIANT': 'local-stub', 'LABEL': 'local-junit-smoke',
           'LOAD_THREADS': '2', 'LOAD_SECONDS': '5', 'LOAD_WARMUP_SECONDS': '1'}
    rc1, t1 = run(['java', '-jar', str(JAR), 'execute', '--class-path', str(classes),
                   '--select-class', 'com.ruoyi.parity.generated.EndpointContractTest',
                   '--details=summary', '--reports-dir', str(WORK / 'contract-reports')], env)
    rc2, t2 = run(['java', '-jar', str(JAR), 'execute', '--class-path', str(classes),
                   '--select-class', 'com.ruoyi.parity.generated.EndpointLoadTest',
                   '--details=summary', '--reports-dir', str(WORK / 'load-reports')], env)
    server.shutdown()
    load = json.loads((WORK / 'junit-load.json').read_text(encoding='utf-8'))
    evidence = {'contract_rc': rc1, 'load_rc': rc2, 'load': load,
                'contract_tail': t1[-800:], 'load_tail': t2[-800:]}
    (OUT / 'local-junit-smoke.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUT / 'local-junit-smoke.md').write_text(
        '# Local JUnit smoke\n\n- contract rc: %s\n- load rc: %s\n- total requests: %s\n- errors: %s\n' %
        (rc1, rc2, load.get('total_requests'), load.get('errors')), encoding='utf-8')
    print('contract_rc=%s load_rc=%s total=%s errors=%s' %
          (rc1, rc2, load.get('total_requests'), load.get('errors')))
    assert rc1 == 0 and rc2 == 0, (t1 + t2)[-1200:]


if __name__ == '__main__':
    main()
