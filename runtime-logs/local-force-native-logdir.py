#!/usr/bin/env python3

"""
@description 历史脚本 local-force-native-logdir.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python local-force-native-logdir.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：workflow_dispatch 动态矩阵下 matrix.platform 条件在本步骤中未生效，


导致 Logback AOT 仍找不到 /home/ruoyi/logs。





思路：删除独立 Prepare 步骤；在 AOT run 块中无条件执行


`sudo mkdir ... || mkdir ...`，chown 失败不影响构建（|| true）。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

REL='.github/workflows/native-image-cloud.yml'

PREP='''      - name: Prepare RuoYi log directories

        if: runner.os == 'Linux'

        shell: bash

        run: |

          # AOT starts the Spring context; Logback writes to /home/ruoyi/logs.

          sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath

          sudo chown -R "$(id -u):$(id -g)" /home/ruoyi



'''

OLD='''          set -euo pipefail

          if [ '${{ matrix.platform }}' = 'linux' ]; then

            sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath

            sudo chown -R "$(id -u):$(id -g)" /home/ruoyi

          fi

'''

NEW='''          set -euo pipefail

          # AOT starts the Spring context and Logback writes to /home/ruoyi/logs.

          sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath || mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath

          sudo chown -R "$(id -u):$(id -g)" /home/ruoyi || true

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

    if not p.exists():

        continue

    t=p.read_text(encoding='utf-8')

    n=t.replace(PREP,'')

    n=n.replace(OLD,NEW,1)

    if n==t:

        print('SKIP',wd.name); continue

    p.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','ci(native): force log dir setup in AOT step')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

