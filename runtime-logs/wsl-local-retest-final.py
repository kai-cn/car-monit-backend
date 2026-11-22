#!/usr/bin/env python3
"""
@description 在 WSL 中用本地 MySQL/Redis 和已打包 jar 运行全接口契约与压测复测。
@author AI Assistant
@date 2026-11-23
@usage python3 runtime-logs/wsl-local-retest-final.py
@dependencies WSL Docker MySQL/Redis、Java8、JUnit console jar、backend master 本地 jar。
"""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path('/mnt/d/work/runtime-logs')
OUT = ROOT / 'wsl-final-retest'
JUNIT = ROOT / 'junit-platform-console-standalone.jar'
JAR = Path('/home/dev/local-package/backend-master/ruoyi-admin/target/ruoyi-admin.jar')
EP = Path('/home/dev/IdeaProjects/car-monit-backend/scripts/v3/ops/parity/endpoints/backend-full.txt')
OUT.mkdir(parents=True, exist_ok=True)
for d in ['logs', 'generated', 'classes', 'contract-reports', 'load-reports']:
    (OUT / d).mkdir(exist_ok=True)


def run(cmd, **kw):
    """执行外部命令并打印非敏感输出摘要。"""
    r = subprocess.run(cmd, text=True, capture_output=True, **kw)
    if r.returncode != 0:
        raise SystemExit('CMD_FAIL ' + ' '.join(map(str, cmd[:3])) + '\n' + (r.stdout + r.stderr)[-2000:])
    return r.stdout


if not JAR.exists():
    raise SystemExit('NO_JAR ' + str(JAR))
run(['docker', 'start', 'mysql_wsl'], check=False) if False else None
subprocess.run(['docker', 'start', 'mysql_wsl'], capture_output=True)
subprocess.run(['docker', 'start', 'redis_wsl'], capture_output=True)
for _ in range(60):
    if subprocess.run(['docker', 'exec', 'mysql_wsl', 'mysql', '-uroot', '-proot', '-e', 'select 1'], capture_output=True).returncode == 0:
        break
    time.sleep(1)
if subprocess.run(['bash', '-c', '(echo > /dev/tcp/127.0.0.1/6379) 2>/dev/null'], capture_output=True).returncode != 0:
    subprocess.run(['docker', 'run', '-d', '--name', 'redis_wsl', '-p', '6379:6379', 'redis:7-alpine'], capture_output=True)

env = os.environ.copy()
env.update({
    'BASE_URL': 'http://127.0.0.1:19903',
    'OUT_DIR': str(OUT),
    'LOG_PATH': str(OUT / 'logs'),
    'HTTP_TIMEOUT_MS': '60000',
    'SPRING__DATASOURCE__DRUID__MASTER__URL': 'jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8',
    'SPRING__DATASOURCE__DRUID__MASTER__USERNAME': 'root',
    'SPRING__DATASOURCE__DRUID__MASTER__PASSWORD': 'root',
    'SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME': 'com.mysql.cj.jdbc.Driver',
    'SPRING__REDIS__HOST': '127.0.0.1',
    'SPRING__REDIS__PORT': '6379',
    'TOKEN__SECRET': 'junit-cloud-secret-deterministic-0123456789abcdef',
})
app_log = (OUT / 'app.log').open('w', encoding='utf-8')
proc = subprocess.Popen(['java', '-jar', str(JAR), '--server.port=19903',
                         '--spring.main.allow-circular-references=true',
                         '--spring.main.lazy-initialization=true',
                         '--spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration'],
                        stdout=app_log, stderr=subprocess.STDOUT, env=env)
ready = False
for _ in range(180):
    if subprocess.run(['bash', '-c', '(echo > /dev/tcp/127.0.0.1/19903) 2>/dev/null'], capture_output=True).returncode == 0:
        ready = True
        break
    if proc.poll() is not None:
        raise SystemExit('APP_EXITED\n' + (OUT / 'app.log').read_text(encoding='utf-8', errors='replace')[-3000:])
    time.sleep(1)
if not ready:
    proc.terminate()
    raise SystemExit('APP_TIMEOUT')

run(['python3', str(ROOT / 'generate_junit_suite.py'), '--endpoints', str(EP), '--out', str(OUT / 'generated')])
run(['javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-cp', str(JUNIT), '-d', str(OUT / 'classes'), *map(str, (OUT / 'generated').glob('*.java'))])
for cls, name in [('EndpointContractTest', 'contract'), ('EndpointLoadTest', 'load')]:
    java_env = env.copy()
    if name == 'load':
        java_env.update({'LOAD_THREADS': '4', 'LOAD_SECONDS': '15', 'LOAD_WARMUP_SECONDS': '1'})
    r = subprocess.run(['java', '-jar', str(JUNIT), 'execute', '--class-path', str(OUT / 'classes'),
                        '--select-class', 'com.ruoyi.parity.generated.' + cls,
                        '--details=summary', '--reports-dir', str(OUT / (name + '-reports'))],
                       text=True, capture_output=True, env=java_env)
    (OUT / (name + '.log')).write_text(r.stdout + r.stderr, encoding='utf-8')
    print(name, 'rc', r.returncode)
proc.terminate()
summary = {
    'jar': str(JAR),
    'contract_log_tail': (OUT / 'contract.log').read_text(encoding='utf-8', errors='replace')[-1000:],
    'load_log_tail': (OUT / 'load.log').read_text(encoding='utf-8', errors='replace')[-1000:],
}
(OUT / 'local-retest-summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print('LOCAL_RETEST_DONE', OUT)
