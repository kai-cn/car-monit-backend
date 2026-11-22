#!/usr/bin/env python3
"""
@description 历史脚本 patch-crosslang-baseline.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-crosslang-baseline.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

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
