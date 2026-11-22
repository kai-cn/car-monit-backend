#!/usr/bin/env python3

"""
@description 历史脚本 local-fix-dependency-management.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python local-fix-dependency-management.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

背景：上一轮把受管依赖的 <version> 从所有 dependency 块删除，根 POM 的


dependencyManagement 条目也变成无版本状态。Maven 会把这些空条目当作版本定义，


导致子模块继承不到 Spring Boot BOM 的版本，报：


'dependencies.dependency.version ... is missing'。





思路：


1. 只在 <dependencyManagement>...</dependencyManagement> 段内操作。


2. 仅删除白名单中 groupId:artifactId 且块内没有 <version> 的条目。


3. 模块 POM 里的依赖声明保持不变；版本继续由 Spring Boot parent/BOM 提供。


4. 每个 worktree 本地 commit + push，重复执行不会制造空提交。
"""
import os

import re

import subprocess

from pathlib import Path



ROOT = Path(r'D:\work\IdeaProjects\_pom-upgrade')

MANAGED = {

    ('org.springframework.boot','spring-boot-starter-amqp'),

    ('org.springframework.boot','spring-boot-starter-data-redis'),

    ('org.springframework.kafka','spring-kafka'),

    ('org.springframework','spring-core'),('org.springframework','spring-web'),

    ('org.springframework','spring-context'),('org.springframework','spring-beans'),

    ('mysql','mysql-connector-java'),('com.mysql','mysql-connector-j'),

}

ENV = dict(os.environ, GIT_TERMINAL_PROMPT='0')





def git(wd, *args, timeout=240):

    r = subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,

                       encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode != 0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()





def clean_dm(text):

    m = re.search(r'(<dependencyManagement>)([\s\S]*?)(</dependencyManagement>)', text)

    if not m:

        return text

    dm = m.group(2)

    dep_re = re.compile(r'[ \t]*<dependency>[\s\S]*?</dependency>\n?')



    def repl(mm):

        block = mm.group(0)

        g = re.search(r'<groupId>([^<]+)</groupId>', block)

        a = re.search(r'<artifactId>([^<]+)</artifactId>', block)

        if not g or not a:

            return block

        if (g.group(1), a.group(1)) in MANAGED and '<version>' not in block:

            return ''

        return block



    new_dm = dep_re.sub(repl, dm)

    return text[:m.start(2)] + new_dm + text[m.end(2):]





for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    changed = []

    for pom in wd.rglob('pom.xml'):

        t = pom.read_text(encoding='utf-8')

        n = clean_dm(t)

        if n != t:

            pom.write_text(n, encoding='utf-8')

            changed.append(str(pom.relative_to(wd)))

    if not changed:

        print('SKIP', wd.name)

        continue

    git(wd, 'add', '-A')

    git(wd, 'commit', '-m', 'build(pom): remove empty managed dependency entries')

    out = git(wd, 'push', 'origin', 'HEAD:' + wd.name.split('__', 1)[1].replace('_', '/'))

    print('PUSHED', wd.name, ','.join(changed))

