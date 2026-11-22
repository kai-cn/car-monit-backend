#!/usr/bin/env python3
"""
@description 历史脚本 local-preserve-jvm-jar.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python local-preserve-jvm-jar.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：Build native binary 使用 `native:compile` 带 clean，会删除 target 下的 jar；

后续 Locate jar + native 再 `ls target/*.jar` 就失败。



思路：

1. 在 Build fat jar 步骤末尾把 jar 复制到 $RUNNER_TEMP/jvm-baseline.jar，并输出路径。

2. Locate 步骤优先读上一步输出的 jar 路径；不存在才回退到 target/*.jar。

3. 只改 backend 临时工作树中的 parity-verify-cloud.yml；本地 commit + push。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
REL='.github/workflows/parity-verify-cloud.yml'
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
OLD_BUILD='''      - name: Build fat jar (JVM baseline)
        shell: bash
        run: |
          set -euo pipefail
          mvn $MAVEN_ARGS -DskipTests -pl "$MODULE" -am package
          ls -lh "$MODULE"/target/*.jar
'''
NEW_BUILD='''      - name: Build fat jar (JVM baseline)
        id: jvmjar
        shell: bash
        run: |
          set -euo pipefail
          mvn $MAVEN_ARGS -DskipTests -pl "$MODULE" -am package
          ls -lh "$MODULE"/target/*.jar
          jar=$(ls "$MODULE"/target/*.jar | grep -v original | head -1)
          # Native build uses clean; preserve the JVM baseline jar outside target.
          cp "$jar" "$RUNNER_TEMP/jvm-baseline.jar"
          echo "jar=$RUNNER_TEMP/jvm-baseline.jar" >> "$GITHUB_OUTPUT"
'''
OLD_LOC='''          jar=$(ls "$MODULE"/target/*.jar | grep -v original | head -1)
          echo "jar=$jar" >> "$GITHUB_OUTPUT"
'''
NEW_LOC='''          jar="${{ steps.jvmjar.outputs.jar }}"
          if [ -z "$jar" ] || [ ! -f "$jar" ]; then
            jar=$(ls "$MODULE"/target/*.jar | grep -v original | head -1)
          fi
          echo "jar=$jar" >> "$GITHUB_OUTPUT"
'''

def git(wd,*args,timeout=240):
    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,
                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)
    if r.returncode!=0:
        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()

for wd in sorted(ROOT.iterdir()):
    if not wd.is_dir():
        continue
    p=wd/REL
    if not p.exists():
        continue
    t=p.read_text(encoding='utf-8')
    n=t
    if OLD_BUILD in n:
        n=n.replace(OLD_BUILD,NEW_BUILD,1)
    if OLD_LOC in n:
        n=n.replace(OLD_LOC,NEW_LOC,1)
    if n==t:
        print('SKIP',wd.name); continue
    p.write_text(n,encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','ci(parity): preserve JVM jar before native clean')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
