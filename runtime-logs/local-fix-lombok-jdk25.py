#!/usr/bin/env python3

"""
@description 历史脚本 local-fix-lombok-jdk25.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python local-fix-lombok-jdk25.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：Boot2 BOM 自带较旧 Lombok，在 JDK25 云 runner 上注解处理不生效，


导致 @AllArgsConstructor 不生成构造器，报 FlowTypeEnum 构造器不存在。





思路：


1. 若仓库任一 POM 使用 org.projectlombok:lombok 且根 POM 没有 lombok.version，


   在 <properties> 中加 lombok.version=1.18.48（仍由 BOM 管理依赖，仅覆盖属性）。


2. 若根 POM 的 maven-compiler-plugin 有 <configuration> 且没有 <proc>，加 <proc>full</proc>。


3. 本地 commit + push；已有正确配置的分支跳过，不制造空提交。
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



def uses_lombok(wd):

    return any('org.projectlombok' in p.read_text(encoding='utf-8',errors='ignore') for p in wd.rglob('pom.xml'))



for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    root=wd/'pom.xml'

    if not root.exists() or not uses_lombok(wd):

        continue

    t=root.read_text(encoding='utf-8')

    n=t

    if '<lombok.version>' not in n:

        n=n.replace('<properties>', '<properties>\n        <lombok.version>1.18.48</lombok.version>',1)

    if '<artifactId>maven-compiler-plugin</artifactId>' in n and '<proc>' not in n:

        idx=n.index('<artifactId>maven-compiler-plugin</artifactId>')

        cfg=n.find('<configuration>',idx)

        if cfg>=0:

            ins=cfg+len('<configuration>')

            n=n[:ins]+'\n                    <proc>full</proc>'+n[ins:]

    if n==t:

        print('SKIP',wd.name); continue

    root.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','build(pom): Lombok 1.18.48 and full annotation processing')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

