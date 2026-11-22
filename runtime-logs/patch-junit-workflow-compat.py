#!/usr/bin/env python3

"""
@description 历史脚本 patch-junit-workflow-compat.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-junit-workflow-compat.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Java 运行时；Python 3 标准库及脚本原有第三方依赖

Idea:


- Boot2.7 disables circular references by default. Legacy master/V3 branches still


  have known circular dependencies, so pass --spring.main.allow-circular-references=true


  to the JVM jar used only by the test harness.


- Add -DskipTests already exists; also add -Dmaven.test.skip=true is unnecessary.


- Boot4 process-aot is already skipped in build; keep it.
"""
from pathlib import Path

import yaml



FILES = [

    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),

    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),

]

OLD = 'java -jar out/app.jar --server.port=19903 > out/app.log 2>&1 &'

NEW = 'java -jar out/app.jar --server.port=19903 --spring.main.allow-circular-references=true > out/app.log 2>&1 &'



for p in FILES:

    t = p.read_text(encoding='utf-8')

    assert OLD in t, p

    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')

    yaml.safe_load(t)

    print('patched', p)

