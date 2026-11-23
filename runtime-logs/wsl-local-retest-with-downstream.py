#!/usr/bin/env python3
"""Run local backend contract/load retest with api downstream.

@description 在 WSL 中启动 api 下游和当前 backend jar，按 body.code 判据生成契约与压测证据。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/wsl-local-retest-with-downstream.py
@dependencies WSL Docker/MySQL/Redis、当前 backend jar、api jar、JUnit standalone。
"""
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path('/mnt/d/work/runtime-logs')
OUT = ROOT / 'wsl-final-retest-with-downstream'
BACKEND_JAR = Path('/home/dev/local-package/backend-master/ruoyi-admin/target/ruoyi-admin.jar')
API_JAR = Path('/home/dev/IdeaProjects/car-monit-api/pro-business-api/target/pro-business-api-1.0.jar')
JUNIT = ROOT / 'junit-platform-console-standalone.jar'
EP = Path('/home/dev/IdeaProjects/car-monit-backend/scripts/v3/ops/parity/endpoints/backend-full.txt')
OUT.mkdir(parents=True, exist_ok=True)
for d in ['logs', 'generated', 'classes', 'contract-reports', 'load-reports']:
    (OUT / d).mkdir(exist_ok=True)


def run(cmd, **kw):
    """Run command and fail with bounded output."""
    r = subprocess.run(cmd, text=True, capture_output=True, **kw)
    if r.returncode != 0:
        raise SystemExit('CMD_FAIL ' + ' '.join(map(str, cmd[:3])) + '\n' + (r.stdout + r.stderr)[-2000:])
    return r.stdout


for name in ['mysql_wsl', 'redis_wsl']:
    subprocess.run(['docker', 'start', name], capture_output=True)
for _ in range(60):
    if subprocess.run(['docker', 'exec', 'mysql_wsl', 'mysql', '-uroot', '-proot', '-e', 'select 1'], capture_output=True).returncode == 0:
        break
    time.sleep(1)

base_env = os.environ.copy()
base_env.update({
    'SPRING__REDIS__HOST': '127.0.0.1',
    'SPRING__REDIS__PORT': '6379',
    'TOKEN__SECRET': 'junit-cloud-secret-deterministic-0123456789abcdef',
    'SPRING_ELASTICSEARCH_URIS': 'http://172.18.0.1:9200',
    'ELASTICSEARCH_URIS': 'http://172.18.0.1:9200',
    'ES_HOSTS': 'http://172.18.0.1:9200',
    'ELASTICSEARCH_HOST': '172.18.0.1',
    'ELASTICSEARCH_PORT': '9200',
})
if os.environ.get('EXPORT_DOWNLOAD_SECRET'):
    base_env['EXPORT_DOWNLOAD_SECRET'] = os.environ['EXPORT_DOWNLOAD_SECRET']
api_log = (OUT / 'api.log').open('w', encoding='utf-8')
api_env = base_env.copy()
api_env.update({
    'SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL': 'jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false',
    'SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME': 'postgres',
    'SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD': 'postgres',
})
api = subprocess.Popen(['java', '-jar', str(API_JAR), '--server.port=9902',
                        '--spring.main.allow-circular-references=true',
                        '--spring.main.lazy-initialization=true',
                        '--spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration'],
                       stdout=api_log, stderr=subprocess.STDOUT, env=api_env)
for _ in range(120):
    if subprocess.run(['bash', '-c', '(echo > /dev/tcp/127.0.0.1/9902) 2>/dev/null'], capture_output=True).returncode == 0:
        break
    time.sleep(1)

env = base_env.copy()
env.update({
    'BASE_URL': 'http://127.0.0.1:19903',
    'OUT_DIR': str(OUT),
    'LOG_PATH': str(OUT / 'logs'),
    'HTTP_TIMEOUT_MS': '60000',
    'VEHICLE_MONITOR_BASE_URL': 'http://127.0.0.1:9902',
    'SPRING__DATASOURCE__DRUID__MASTER__URL': 'jdbc:mysql://127.0.0.1:3307/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8',
    'SPRING__DATASOURCE__DRUID__MASTER__USERNAME': 'root',
    'SPRING__DATASOURCE__DRUID__MASTER__PASSWORD': 'root',
    'SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME': 'com.mysql.cj.jdbc.Driver',
})
app_log = (OUT / 'app.log').open('w', encoding='utf-8')
proc = subprocess.Popen(['java', '-jar', str(BACKEND_JAR), '--server.port=19903',
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
    api.terminate()
    raise SystemExit('APP_TIMEOUT')

if not env.get('ENDPOINT_HEADERS'):
    user = env.get('CARMONIT_ADMIN_USER', '')
    password = env.get('CARMONIT_ADMIN_PASSWORD', '')
    if not user or not password:
        raise SystemExit('NO_ADMIN_CREDENTIALS')
    token_helper = Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs/junit-auth-token.py')
    if not token_helper.exists():
        token_helper = ROOT / 'junit-auth-token.py'
    token = run(['python3', str(token_helper),
                 '--base-url', 'http://127.0.0.1:19903']).strip()
    if not token:
        raise SystemExit('NO_TOKEN')
    env['ENDPOINT_HEADERS'] = 'Authorization: Bearer ' + token

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
api.terminate()
print('LOCAL_RETEST_DONE', OUT)
