#!/usr/bin/env python3

"""
@description 历史脚本 patch-junit-readiness.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-junit-readiness.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- several branches return 4xx/3xx or throw application-specific errors on


  /captchaImage before the full endpoint suite starts; this is not a service


  startup failure.


- bash /dev/tcp checks that the HTTP port is accepting connections without


  depending on a business endpoint.


- endpoint correctness is measured separately by the JUnit contract suite.
"""
from pathlib import Path

import yaml



FILES = [

    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),

    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),

]

OLD = 'if curl -fsS -o /dev/null http://127.0.0.1:19903/captchaImage; then echo "service ready after ${i}s"; exit 0; fi'

NEW = 'if (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1; then echo "service port ready after ${i}s"; exit 0; fi'



for p in FILES:

    t = p.read_text(encoding='utf-8')

    assert OLD in t, p

    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')

    yaml.safe_load(t)

    print('patched', p)

