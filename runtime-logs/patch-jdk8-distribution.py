#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-jdk8-distribution.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Use Corretto for JDK8 (Temurin 8 download was transiently corrupt)."""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
]
OLD = '          distribution: temurin\n          java-version: ${{ inputs.jdk }}'
NEW = '          distribution: ${{ inputs.jdk == \'8\' && \'corretto\' || \'temurin\' }}\n          java-version: ${{ inputs.jdk }}'

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD in t, p
    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')
    yaml.safe_load(p.read_text(encoding='utf-8'))
    print('patched', p)
