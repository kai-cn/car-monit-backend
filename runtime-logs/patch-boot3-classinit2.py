#!/usr/bin/env python3

"""
@description 历史脚本 patch-boot3-classinit2.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-boot3-classinit2.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

from pathlib import Path

p = Path(r'D:\work\runtime-logs\api-boot3-module-pom.xml')

t = p.read_text(encoding='utf-8')

old = '--initialize-at-build-time=org.springframework.util.ClassUtils,org.springframework.util.ConcurrentReferenceHashMap$ReferenceType'

new = '--initialize-at-build-time=org.springframework.util.ClassUtils,org.springframework.util.ConcurrentReferenceHashMap,org.springframework.util.ConcurrentReferenceHashMap$ReferenceType'

if new not in t:

    t = t.replace(old, new, 1)

p.write_text(t, encoding='utf-8')

print('patched', new in t)

