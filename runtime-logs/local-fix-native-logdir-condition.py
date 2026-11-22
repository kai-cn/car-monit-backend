#!/usr/bin/env python3
"""
@description 历史脚本 local-fix-native-logdir-condition.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python local-fix-native-logdir-condition.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：原条件 `matrix.platform == 'linux'` 在 workflow_dispatch 动态矩阵下未生效，

日志目录未创建，process-aot 仍报 /home/ruoyi/logs 不存在。



思路：用 GitHub 原生 runner.os 条件替代 matrix 条件；本地 commit + push。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
REL='.github/workflows/native-image-cloud.yml'
OLD='''      - name: Prepare RuoYi log directories
        if: matrix.platform == 'linux'
'''
NEW='''      - name: Prepare RuoYi log directories
        if: runner.os == 'Linux'
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
    if OLD not in t:
        print('SKIP',wd.name); continue
    p.write_text(t.replace(OLD,NEW,1),encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','ci(native): use runner.os for log-dir step')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
