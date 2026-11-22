#!/usr/bin/env python3
"""从 Boot2/JDK8 分支移除 proc=full，避免 javac 8 报 invalid flag。

背景：proc=full 是 JDK21+ 的 javac 选项；Boot2 分支在云 runner 使用 JDK8，
maven-compiler-plugin 3.14.0 会把它作为 -proc:full 传给 javac 8，导致编译失败。

思路：
1. 只处理根 POM 中 java.version 为 1.8/8 的工作树。
2. 删除 <proc>full</proc>，保留其他 compiler 配置。
3. 本地 commit + push；Boot3/Boot4 分支不动。
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

for wd in sorted(ROOT.iterdir()):
    if not wd.is_dir():
        continue
    p=wd/'pom.xml'
    if not p.exists():
        continue
    t=p.read_text(encoding='utf-8')
    if not re.search(r'<java\.version>(1\.8|8)</java\.version>',t):
        continue
    if '<proc>full</proc>' not in t:
        continue
    p.write_text(t.replace('                    <proc>full</proc>\n',''),encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','build(pom): remove proc=full from Boot2 JDK8 build')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
