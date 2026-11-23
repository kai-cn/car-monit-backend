#!/usr/bin/env python3
"""
@description 修正跨语言 baseline：安装 JDK25、设置 MAVEN_ARGS、创建日志目录并跳过 AOT。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/patch-crosslang-baseline-jdk2.py
@dependencies backend/api 两仓库 master 工作树中的 crosslang-full-parity-cloud.yml。
"""
from pathlib import Path

FILES = [
    Path('/home/dev/IdeaProjects/car-monit-backend/.github/workflows/crosslang-full-parity-cloud.yml'),
    Path('/home/dev/IdeaProjects/car-monit-api/.github/workflows/crosslang-full-parity-cloud.yml'),
]
OLD_SETUP = """      - uses: actions/setup-java@v4
        with:
          distribution: corretto
          java-version: '8'
          cache: maven
      - name: Start datastores"""
NEW_SETUP = """      - uses: actions/setup-java@v4
        with:
          distribution: corretto
          java-version: '8'
          cache: maven
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '25'
      - name: Start datastores"""
OLD_BUILD = """      - name: Build and start Java baseline
        run: |
          set -euo pipefail
          export JAVA_HOME="$JAVA_HOME_25_X64"
          export PATH="$JAVA_HOME/bin:$PATH"
          java -version
          cd src"""
NEW_BUILD = """      - name: Build baseline and generate JUnit
        run: |
          set -euo pipefail
          sudo mkdir -p /home/ruoyi/logs
          sudo chown -R "$USER" /home/ruoyi
          export JAVA_HOME="$JAVA_HOME_25_X64"
          export PATH="$JAVA_HOME/bin:$PATH"
          export MAVEN_ARGS="$MAVEN_ARGS -Dspring-boot.aot.skip=true"
          java -version
          cd src"""
for p in FILES:
    t = p.read_text(encoding='utf-8')
    if 'java-version: \'25\'' not in t:
        assert OLD_SETUP in t, ('setup', p)
        t = t.replace(OLD_SETUP, NEW_SETUP, 1)
    if 'export MAVEN_ARGS="$MAVEN_ARGS -Dspring-boot.aot.skip=true"' not in t:
        if OLD_BUILD in t:
            t = t.replace(OLD_BUILD, NEW_BUILD, 1)
        else:
            old = """      - name: Build baseline and generate JUnit
        shell: bash
        run: |
          set -euo pipefail
          cd src"""
            new = """      - name: Build baseline and generate JUnit
        shell: bash
        run: |
          set -euo pipefail
          sudo mkdir -p /home/ruoyi/logs
          sudo chown -R "$USER" /home/ruoyi
          export JAVA_HOME="$JAVA_HOME_25_X64"
          export PATH="$JAVA_HOME/bin:$PATH"
          export MAVEN_ARGS="$MAVEN_ARGS -Dspring-boot.aot.skip=true"
          java -version
          cd src"""
            assert old in t, ('build', p)
            t = t.replace(old, new, 1)
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
