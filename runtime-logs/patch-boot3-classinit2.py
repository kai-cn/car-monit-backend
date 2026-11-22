#!/usr/bin/env python3
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
