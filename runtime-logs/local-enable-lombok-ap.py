#!/usr/bin/env python3
"""
@description 历史脚本 local-enable-lombok-ap.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python local-enable-lombok-ap.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：native-image-cloud 在 JDK25 下构建 Boot2 分支时，Lombok 生成的 getter/

构造器/log 字段未出现（OssTemplate、RedisConfig、AliyunSMSUtil 等报错），

说明注解处理路径不稳定。显式 annotationProcessorPaths 可强制使用项目锁定的 Lombok。



思路：

1. 只处理根 POM 中 maven-compiler-plugin 的 configuration。

2. 若已有 annotationProcessorPaths 则跳过，避免破坏 Boot3/Boot4 配置。

3. 插入 path 指向 org.projectlombok:lombok:${lombok.version}。

4. 不添加 proc=full，避免 Boot2/JDK17 云验证出现 invalid flag。

5. 本地 commit + push。
"""
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
BLOCK='''                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                            <version>${lombok.version}</version>
                        </path>
                    </annotationProcessorPaths>
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
    if not p.exists() or '<lombok.version>' not in p.read_text(encoding='utf-8'):
        continue
    t=p.read_text(encoding='utf-8')
    if 'annotationProcessorPaths' in t:
        print('SKIP',wd.name); continue
    m=re.search(r'(<artifactId>maven-compiler-plugin</artifactId>[\s\S]{0,500}?<configuration>)',t)
    if not m:
        print('NO_COMPILER',wd.name); continue
    n=t[:m.end(1)]+'\n'+BLOCK+t[m.end(1):]
    p.write_text(n,encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','build(pom): declare Lombok annotation processor path')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
