#!/usr/bin/env python3

"""
@description 历史脚本 local-align-backend-bom.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python local-align-backend-bom.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：feat/backend-full-parity 未包含在首轮 Boot2 升级列表中，BOM 仍是 2.5.15，


不管理 com.mysql:mysql-connector-j；切换到新坐标后报 version missing。





思路：


1. 只替换 spring-boot-dependencies 块附近的 2.5.15。


2. 不动 spring-framework BOM 与其他第三方版本。


3. 本地 commit + push；已是 2.7.18 的分支跳过。
"""
import os

import re

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')



def git(wd,*args,timeout=240):

    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,

                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode!=0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()



pat=re.compile(r'(<artifactId>spring-boot-dependencies</artifactId>\s*<version>)2\.5\.15(</version>)')

for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir() or not wd.name.startswith('bk__'):

        continue

    p=wd/'pom.xml'

    if not p.exists():

        continue

    t=p.read_text(encoding='utf-8')

    n=pat.sub(r'\g<1>2.7.18\g<2>',t)

    if n==t:

        print('SKIP',wd.name); continue

    p.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','build(pom): align backend BOM to Boot 2.7.18')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

