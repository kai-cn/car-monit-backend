#!/usr/bin/env python3
"""
@description 在跨语言 workflow 的 baseline 构建步骤显式设置 JDK25，避免 Maven 仍使用 setup-java 的 JDK8。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/patch-crosslang-baseline-jdk.py
@dependencies backend/api 两仓库 master 工作树中的 crosslang-full-parity-cloud.yml。
"""
from pathlib import Path

FILES = [
    Path('/home/dev/IdeaProjects/car-monit-backend/.github/workflows/crosslang-full-parity-cloud.yml'),
    Path('/home/dev/IdeaProjects/car-monit-api/.github/workflows/crosslang-full-parity-cloud.yml'),
]
OLD = """      - name: Build baseline and generate JUnit
        shell: bash
        run: |
          set -euo pipefail"""
NEW = """      - name: Build and start Java baseline
        run: |
          set -euo pipefail
          export JAVA_HOME="$JAVA_HOME_25_X64"
          export PATH="$JAVA_HOME/bin:$PATH"
          java -version"""
for p in FILES:
    t = p.read_text(encoding='utf-8')
    if 'export JAVA_HOME="$JAVA_HOME_25_X64"' in t:
        print('SKIP', p)
        continue
    assert OLD in t, p
    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')
    print('PATCHED', p)
