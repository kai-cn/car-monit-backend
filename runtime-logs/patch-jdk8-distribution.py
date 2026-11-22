#!/usr/bin/env python3

"""
@description 历史脚本 patch-jdk8-distribution.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-jdk8-distribution.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
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

