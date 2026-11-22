#!/usr/bin/env python3
"""把 Boot2.7 不再管理的 mysql:mysql-connector-java 换成 com.mysql:mysql-connector-j。

背景：Boot 2.7 的 BOM 管理新坐标 com.mysql:mysql-connector-j；旧坐标无版本会报
'dependencies.dependency.version for mysql:mysql-connector-java is missing'。

思路：
1. 遍历所有本地 Java 工作树的 POM。
2. 只替换 dependency 块中 groupId=mysql、artifactId=mysql-connector-java 的坐标。
3. 不改其他 mysql 相关属性；未使用的旧属性保留，避免扩大变更。
4. 本地 commit + push；重复执行跳过。
"""
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
OLD='''<dependency>
            <groupId>mysql</groupId>
            <artifactId>mysql-connector-java</artifactId>'''
NEW='''<dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>'''

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
    for pom in wd.rglob('pom.xml'):
        t=pom.read_text(encoding='utf-8')
        n=t.replace(OLD,NEW)
        if n!=t:
            pom.write_text(n,encoding='utf-8')
            changed.append(str(pom.relative_to(wd)))
    if not changed:
        continue
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','build(pom): use Boot-managed MySQL connector coordinates')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch,','.join(changed))
