#!/usr/bin/env python3

"""
@description 历史脚本 local-upgrade-compiler-any.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-upgrade-compiler-any.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：java-fix 使用 3.8.1，报错 invalid flag: -proc:full；3.14.0 支持 proc 元素。





思路：


1. 在根 POM 中定位 maven-compiler-plugin 的 <version> 元素。


2. 只要不是 3.14.0 就替换为 3.14.0。


3. 本地 commit + push；已是 3.14.0 的分支跳过。
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



pat=re.compile(r'(<artifactId>maven-compiler-plugin</artifactId>\s*<version>)([^<]+)(</version>)')

for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    p=wd/'pom.xml'

    if not p.exists():

        continue

    t=p.read_text(encoding='utf-8')

    m=pat.search(t)

    if not m or m.group(2)=='3.14.0':

        print('SKIP',wd.name); continue

    n=pat.sub(r'\g<1>3.14.0\g<3>',t,count=1)

    p.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','build(pom): unify maven-compiler-plugin 3.14.0')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch,m.group(2),'->3.14.0')

