#!/usr/bin/env python3

"""
@description 历史脚本 local-pin-lombok-dm.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-pin-lombok-dm.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：backend 使用 spring-boot-dependencies BOM import，子 POM 的 lombok.version 属性


不会覆盖导入 BOM 内的版本；因此 Boot2 BOM 的旧 Lombok 仍生效，JDK25 报 TypeTag UNKNOWN。





思路：


1. 若根 POM 有 lombok.version 属性且仓库使用 lombok。


2. 在 dependencyManagement/dependencies 开头插入 org.projectlombok:lombok


   的显式版本 ${lombok.version}。当前 POM 显式条目优先于 imported BOM。


3. 本地 commit + push；重复执行跳过。
"""
import os

import re

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

ENTRY='''            <dependency>

                <groupId>org.projectlombok</groupId>

                <artifactId>lombok</artifactId>

                <version>${lombok.version}</version>

            </dependency>

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

    p=wd/'pom.xml'

    if not p.exists():

        continue

    t=p.read_text(encoding='utf-8')

    if '<lombok.version>' not in t:

        continue

    if not any('org.projectlombok' in x.read_text(encoding='utf-8',errors='ignore') for x in wd.rglob('pom.xml')):

        continue

    m=re.search(r'(<dependencyManagement>\s*<dependencies>)',t)

    if not m:

        print('NO_DM',wd.name); continue

    dm_start=m.end(1)

    if t[dm_start:dm_start+500].find('<artifactId>lombok</artifactId>')>=0:

        print('SKIP',wd.name); continue

    n=t[:dm_start]+'\n'+ENTRY+t[dm_start:]

    p.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','build(pom): pin Lombok in dependencyManagement')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

