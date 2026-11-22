#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-aws-sdk-resources.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk25-admin-pom.xml')
t = p.read_text(encoding='utf-8')
marker = '                    <buildArgs>\n'
add = marker + '''                        <buildArg>-H:IncludeResources=com/amazonaws/internal/config/.*</buildArg>
                        <buildArg>-H:IncludeResources=com/amazonaws/util/aws-java-sdk-core-version.properties</buildArg>
'''
assert marker in t
if 'com/amazonaws/internal/config' not in t:
    t = t.replace(marker, add, 1)
p.write_text(t, encoding='utf-8')
print('aws resources added', 'com/amazonaws/internal/config' in t)
