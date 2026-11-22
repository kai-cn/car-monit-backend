#!/usr/bin/env python3

"""
@description 历史脚本 patch-boot3-allnested.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-boot3-allnested.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

from pathlib import Path

p = Path(r'D:\work\runtime-logs\api-boot3-module-pom.xml')

t = p.read_text(encoding='utf-8')

classes = [

'org.springframework.util.ConcurrentReferenceHashMap',

'org.springframework.util.ConcurrentReferenceHashMap$EntryIterator',

'org.springframework.util.ConcurrentReferenceHashMap$ReferenceManager',

'org.springframework.util.ConcurrentReferenceHashMap$ReferenceType',

'org.springframework.util.ConcurrentReferenceHashMap$1',

'org.springframework.util.ConcurrentReferenceHashMap$2',

'org.springframework.util.ConcurrentReferenceHashMap$3',

'org.springframework.util.ConcurrentReferenceHashMap$4',

'org.springframework.util.ConcurrentReferenceHashMap$5',

'org.springframework.util.ConcurrentReferenceHashMap$Reference',

'org.springframework.util.ConcurrentReferenceHashMap$Task',

'org.springframework.util.ConcurrentReferenceHashMap$TaskOption',

'org.springframework.util.ConcurrentReferenceHashMap$EntrySet',

'org.springframework.util.ConcurrentReferenceHashMap$WeakEntryReference',

'org.springframework.util.ConcurrentReferenceHashMap$Entry',

'org.springframework.util.ConcurrentReferenceHashMap$Entries',

'org.springframework.util.ConcurrentReferenceHashMap$SoftEntryReference',

'org.springframework.util.ConcurrentReferenceHashMap$Restructure',

'org.springframework.util.ConcurrentReferenceHashMap$Segment',

]

start = t.find('--initialize-at-build-time=org.springframework.util.ClassUtils,')

end = t.find('</buildArg>', start)

old = t[start:end]

new = '--initialize-at-build-time=org.springframework.util.ClassUtils,' + ','.join(classes)

t = t[:start] + new + t[end:]

p.write_text(t, encoding='utf-8')

print('patched', len(classes), 'classes')

