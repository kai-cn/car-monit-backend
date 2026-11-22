#!/usr/bin/env python3

"""
@description 历史脚本 patch-aws-sdk-resources.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-aws-sdk-resources.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

