#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-junit-artifact.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Reuse JUnit jar from baseline artifact to avoid Maven Central 429.

Idea:
- baseline already downloads junit.jar once and uploads out/**.
- add junit.jar explicitly to baseline artifact paths.
- candidates copy baseline/junit.jar to out-junit.jar, with apt fallback.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
]
OLD_PATH = '''            out/junit-contract.json
            out/junit-load.json
            out/*.log'''
NEW_PATH = '''            out/junit-contract.json
            out/junit-load.json
            out/junit.jar
            out/*.log'''
OLD_STEP = '''          set -euo pipefail
          if sudo apt-get update -qq && sudo apt-get install -y -qq junit-platform-console-standalone >/dev/null 2>&1; then
            cp /usr/share/java/junit-platform-console-standalone.jar out-junit.jar
            ls -lh out-junit.jar
            exit 0
          fi
          URL=https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar
          curl -fsSL --retry 5 --retry-delay 5 -o out-junit.jar "$URL"'''
NEW_STEP = '''          set -euo pipefail
          if [ -f baseline/junit.jar ]; then
            cp baseline/junit.jar out-junit.jar
            ls -lh out-junit.jar
            exit 0
          fi
          if sudo apt-get update -qq && sudo apt-get install -y -qq junit-platform-console-standalone >/dev/null 2>&1; then
            cp /usr/share/java/junit-platform-console-standalone.jar out-junit.jar
            ls -lh out-junit.jar
            exit 0
          fi
          URL=https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar
          curl -fsSL --retry 5 --retry-delay 5 -o out-junit.jar "$URL"'''

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD_PATH in t and OLD_STEP in t, p
    t = t.replace(OLD_PATH, NEW_PATH, 1).replace(OLD_STEP, NEW_STEP, 1)
    p.write_text(t, encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
