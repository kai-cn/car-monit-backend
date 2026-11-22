#!/usr/bin/env python3

"""
@description 历史脚本 local-upgrade-compiler-plugin.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python local-upgrade-compiler-plugin.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：backend full-parity 分支在云 runner 报


com.sun.tools.javac.code.TypeTag :: UNKNOWN，来自旧 compiler plugin 与 JDK25/Lombok 组合。





思路：


1. 只替换根 POM 中 maven-compiler-plugin 的 <version>3.1</version>。


2. 不动其他插件版本，不强制改 java.version，避免扩大改造面。


3. 本地 commit + push；已是 3.14.0 的分支跳过。
"""
import os

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



for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    p=wd/'pom.xml'

    if not p.exists():

        continue

    t=p.read_text(encoding='utf-8')

    old='<artifactId>maven-compiler-plugin</artifactId>\n                <version>3.1</version>'

    new='<artifactId>maven-compiler-plugin</artifactId>\n                <version>3.14.0</version>'

    if old not in t:

        print('SKIP',wd.name); continue

    p.write_text(t.replace(old,new,1),encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','build(pom): upgrade maven-compiler-plugin to 3.14.0')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

