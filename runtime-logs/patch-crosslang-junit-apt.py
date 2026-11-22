#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-junit-apt.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-crosslang-junit-apt.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

Idea:


- Ubuntu runners provide junit-platform-console-standalone in apt.


- copy /usr/share/java/junit-platform-console-standalone.jar into workspace.


- keep URL retry as a fallback if apt package is unavailable.
"""
from pathlib import Path

import yaml



FILES = [

    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),

    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),

]

OLD = '''          set -euo pipefail

          URL=https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar

          for i in 1 2 3 4; do

            if curl -fsSL -o out-junit.jar "$URL"; then exit 0; fi

            echo "junit download retry $i"; sleep $((i*5))

          done

          URL=https://repo2.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar

          curl -fsSL --retry 3 --retry-delay 5 -o out-junit.jar "$URL"'''

NEW = '''          set -euo pipefail

          if sudo apt-get update -qq && sudo apt-get install -y -qq junit-platform-console-standalone >/dev/null 2>&1; then

            cp /usr/share/java/junit-platform-console-standalone.jar out-junit.jar

            ls -lh out-junit.jar

            exit 0

          fi

          URL=https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar

          curl -fsSL --retry 5 --retry-delay 5 -o out-junit.jar "$URL"'''



for p in FILES:

    t = p.read_text(encoding='utf-8')

    assert OLD in t, p

    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')

    yaml.safe_load(t)

    print('patched', p)

