#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-baseline-robust.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Make crosslang baseline wait for real HTTP readiness and fail with logs.

Idea:
- TCP readiness alone can pass before Spring MVC is ready or after the process
  is about to exit; require a successful HTTP response from a light endpoint.
- If the service exits, dump the app log immediately so the real cause is visible.
- Use the same JVM compatibility flags proven by Java JUnit workflow.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
]
OLD = 'for i in $(seq 1 180); do (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1 && break; sleep 1; done'
NEW = '''for i in $(seq 1 180); do
            if curl -fsS -o /dev/null http://127.0.0.1:19903/; then echo "HTTP ready after ${i}s"; break; fi
            if ! kill -0 "$(cat out/app.pid)" 2>/dev/null; then echo "service exited"; tail -n 160 out/app.log; exit 1; fi
            sleep 1
          done'''
OLD_JAVA = 'java -jar out/app.jar --server.port=19903 > out/app.log 2>&1 &'
NEW_JAVA = ('java -jar out/app.jar --server.port=19903 --spring.main.allow-circular-references=true '
            '--spring.main.lazy-initialization=true '
            '--spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration '
            '> out/app.log 2>&1 &')

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD in t, p
    t = t.replace(OLD, NEW, 1)
    t = t.replace(OLD_JAVA, NEW_JAVA, 1)
    p.write_text(t, encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
