#!/usr/bin/env python3
"""
@description 历史脚本 local-add-native-logdir.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python local-add-native-logdir.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：process-aot 启动 Spring 上下文时 Logback 写 /home/ruoyi/logs，

云 runner 默认无该目录，导致 backend Boot4 构建失败。



思路：

1. 在 AOT + native-image 步骤前插入一条 Linux-only 步骤。

2. 创建 /home/ruoyi/logs 与 /home/ruoyi/uploadPath，并授权给当前用户。

3. 不改其他 native 参数，重复执行跳过。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
REL='.github/workflows/native-image-cloud.yml'
STEP='''      - name: Prepare RuoYi log directories
        if: matrix.platform == 'linux'
        shell: bash
        run: |
          # AOT starts the Spring context; Logback writes to /home/ruoyi/logs.
          sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath
          sudo chown -R "$(id -u):$(id -g)" /home/ruoyi

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
    if 'Prepare RuoYi log directories' in t:
        print('SKIP',wd.name); continue
    marker='      - name: AOT + native-image\n'
    if marker not in t:
        print('NO_MARKER',wd.name); continue
    p.write_text(t.replace(marker,STEP+marker,1),encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','ci(native): prepare RuoYi log dirs before AOT')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
