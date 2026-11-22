#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-junit-workflow-fixes.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Fix java-junit-load-cloud workflow for AOT and log directory permissions.

Idea:
- Boot4 `mvn package` triggers process-aot, which needs datastores during build.
  JVM endpoint tests only need the runnable jar, so skip AOT during that build.
- backend Boot2 startup hard-codes /home/ruoyi/logs in some branches. Create it
  with sudo before launching the jar, while keeping LOG_PATH for configurable branches.
- Applies to both backend and api control workflows; patches are idempotent.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
]
OLD_MVN = 'mvn $MAVEN_ARGS -DskipTests -pl "$MODULE" -am package'
NEW_MVN = 'mvn $MAVEN_ARGS -DskipTests -Dspring-boot.aot.skip=true -pl "$MODULE" -am package'
OLD_MKDIR = 'mkdir -p "$LOG_PATH" /home/ruoyi/logs'
NEW_MKDIR = 'sudo mkdir -p "$LOG_PATH" /home/ruoyi/logs; sudo chown -R "$(id -u):$(id -g)" /home/ruoyi "$LOG_PATH"; mkdir -p "$LOG_PATH" /home/ruoyi/logs'

for p in FILES:
    t = p.read_text(encoding='utf-8')
    t = t.replace(OLD_MVN, NEW_MVN).replace(OLD_MKDIR, NEW_MKDIR)
    p.write_text(t, encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
