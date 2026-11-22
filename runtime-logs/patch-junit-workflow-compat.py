#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-junit-workflow-compat.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Make JUnit/load workflow compatible with Boot2 circular refs and skip packaged tests.

Idea:
- Boot2.7 disables circular references by default. Legacy master/V3 branches still
  have known circular dependencies, so pass --spring.main.allow-circular-references=true
  to the JVM jar used only by the test harness.
- Add -DskipTests already exists; also add -Dmaven.test.skip=true is unnecessary.
- Boot4 process-aot is already skipped in build; keep it.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
]
OLD = 'java -jar out/app.jar --server.port=19903 > out/app.log 2>&1 &'
NEW = 'java -jar out/app.jar --server.port=19903 --spring.main.allow-circular-references=true > out/app.log 2>&1 &'

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD in t, p
    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
