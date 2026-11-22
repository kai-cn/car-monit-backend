#!/usr/bin/env python3

"""
@description 历史脚本 local-upgrade-module-compiler.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-upgrade-module-compiler.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

思路：根 POM 已升级，但部分模块自带 compiler plugin 版本会覆盖根配置；


只替换 artifactId 后紧邻的 3.8.1，本地 commit + push。
"""
import os

import re

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

PAT=re.compile(r'(<artifactId>maven-compiler-plugin</artifactId>\s*<version>)3\.8\.1(</version>)')



def git(wd,*args,timeout=240):

    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,

                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode!=0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()



for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    changed=[]

    for p in wd.rglob('pom.xml'):

        t=p.read_text(encoding='utf-8')

        n=PAT.sub(r'\g<1>3.14.0\g<2>',t)

        if n!=t:

            p.write_text(n,encoding='utf-8')

            changed.append(str(p.relative_to(wd)))

    if not changed:

        continue

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','build(pom): upgrade module compiler plugin to 3.14.0')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch,','.join(changed))

