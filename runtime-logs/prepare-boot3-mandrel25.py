#!/usr/bin/env python3

"""
@description 历史脚本 prepare-boot3-mandrel25.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python prepare-boot3-mandrel25.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

from pathlib import Path

base = Path(r'D:\work\runtime-logs')



# poms: add proc=full for javac25, keep each branch's java.version

for name in ('api-boot3-jdk21-pom.xml', 'api-boot3-pom.xml'):

    p = base / name

    t = p.read_text(encoding='utf-8')

    needle = '                    <parameters>true</parameters>'

    if '<proc>full</proc>' not in t:

        t = t.replace(needle, needle + '\n                    <proc>full</proc>', 1)

    p.write_text(t, encoding='utf-8')

    print('POM', name, 'java.version', '17' if '<java.version>17' in t else '21')



# workflow: use Mandrel 25 while pom still targets 17/21

p = base / 'api-boot3-workflow.yml'

t = p.read_text(encoding='utf-8')

old = '          java-version: ${{ needs.prepare.outputs.jdk }}'

new = "          java-version: '25'  # Mandrel25 toolchain; pom release remains branch JDK"

if old in t:

    t = t.replace(old, new, 1)

p.write_text(t, encoding='utf-8')

print('WORKFLOW patched', "java-version: '25'" in t)

