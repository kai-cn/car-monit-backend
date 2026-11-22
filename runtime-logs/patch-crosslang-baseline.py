#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-baseline.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Fix crosslang baseline JVM build and log directory permissions.

Idea:
- crosslang baseline only needs a runnable JVM jar, not native assets.
- skip process-aot during package for Boot4 branches.
- create /home/ruoyi/logs with sudo before service start because some branches
  have hard-coded logback paths and the runner user cannot create /home/ruoyi.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
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
