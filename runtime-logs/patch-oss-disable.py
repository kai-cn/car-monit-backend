#!/usr/bin/env python3

"""
@description 历史脚本 patch-oss-disable.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-oss-disable.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

