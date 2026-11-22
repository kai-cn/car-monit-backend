#!/usr/bin/env python3
"""
@description 历史脚本 local-inline-native-logdir.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python local-inline-native-logdir.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：独立 Prepare 步骤在 workflow_dispatch 动态矩阵下未执行；

为确保目录存在，直接在 AOT 命令开头按 matrix.platform 条件创建目录。



思路：在 `set -euo pipefail` 后插入 Linux-only mkdir/chown；Windows 不执行。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
REL='.github/workflows/native-image-cloud.yml'
OLD='''      - name: AOT + native-image
        shell: bash
        run: |
          set -euo pipefail
'''
NEW='''      - name: AOT + native-image
        shell: bash
        run: |
          set -euo pipefail
          if [ '${{ matrix.platform }}' = 'linux' ]; then
            sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath
            sudo chown -R "$(id -u):$(id -g)" /home/ruoyi
          fi
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
    if "sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath\n            sudo chown" in t and OLD not in t:
        print('SKIP',wd.name); continue
    if OLD not in t:
        print('NO_MARKER',wd.name); continue
    p.write_text(t.replace(OLD,NEW,1),encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','ci(native): inline log dir setup into AOT step')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
