#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-oss-disable.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path

pom = Path(r'D:\work\runtime-logs\bk25-admin-pom.xml')
t = pom.read_text(encoding='utf-8')
for line in [
    '                        <buildArg>-H:IncludeResources=com/amazonaws/internal/config/.*</buildArg>\n',
    '                        <buildArg>-H:IncludeResources=com/amazonaws/util/aws-java-sdk-core-version.properties</buildArg>\n',
]:
    t = t.replace(line, '')
pom.write_text(t, encoding='utf-8')

wf = Path(r'D:\work\runtime-logs\bk-parity-oss.yml')
w = wf.read_text(encoding='utf-8')
needle = '  MODULE: ruoyi-admin\n'
if 'OSS_ENABLE' not in w:
    w = w.replace(needle, needle + "  # OSS/S3 is not needed by the 2 parity endpoints; native AWS SDK v1 init is unsupported.\n  OSS_ENABLE: 'false'\n", 1)
wf.write_text(w, encoding='utf-8')

import yaml
yaml.safe_load(w)
print('aws args removed', 'com/amazonaws/internal/config' not in t, 'OSS_ENABLE' in w)
