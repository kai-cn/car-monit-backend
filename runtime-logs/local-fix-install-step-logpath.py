#!/usr/bin/env python3

"""
@description 历史脚本 local-fix-install-step-logpath.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-fix-install-step-logpath.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：process-aot 绑定在 prepare-package，mvn install 阶段就会执行；


之前只在后续 AOT 步骤设置 LOG_PATH，来不及影响 install 中的 AOT。





思路：


1. 给 Install reactor modules (JVM jar) 步骤增加 env LOG_PATH=runner.temp/ruoyi-logs。


2. 在该步骤 run 开头创建目录，再执行 mvn install。


3. 本地 commit + push。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

REL='.github/workflows/native-image-cloud.yml'

OLD='''      - name: Install reactor modules (JVM jar)

        shell: bash

        run: |

          set -euo pipefail

          mvn $MAVEN_ARGS -DskipTests install -pl "${{ steps.meta.outputs.module }}" -am

'''

NEW='''      - name: Install reactor modules (JVM jar)

        shell: bash

        env:

          LOG_PATH: ${{ runner.temp }}/ruoyi-logs

        run: |

          set -euo pipefail

          mkdir -p "$LOG_PATH"

          mvn $MAVEN_ARGS -DskipTests install -pl "${{ steps.meta.outputs.module }}" -am

'''



def git(wd,*args,timeout=240):

    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,

                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode!=0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()



for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    p=wd/REL

    if not p.exists() or OLD not in p.read_text(encoding='utf-8'):

        print('SKIP',wd.name); continue

    p.write_text(p.read_text(encoding='utf-8').replace(OLD,NEW,1),encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','ci(native): set LOG_PATH during reactor install AOT')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

