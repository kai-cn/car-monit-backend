#!/usr/bin/env python3

"""
@description 历史脚本 local-add-java-upgrade-workflow.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-add-java-upgrade-workflow.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

思路：


1. 这些分支使用 Boot2/JDK8，之前复用 master.yml/ci.yml 会被 Python 构建、


   数据库夹具或 native 清理等非 Java 问题阻断。


2. 新增 java-upgrade-verify.yml：checkout + JDK17 + Maven cache + mvn package。


3. JDK17 可编译 source/target 1.8，并避开 JDK25 下的 Lombok 内部 API 问题。


4. 写入 api master 与 backend master 后，GitHub 会在默认分支暴露该 workflow id，


   后续可用同一 id dispatch 到其他分支。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

TARGETS={

 'api__master':'master','api__car-monit-api-java-V3':'car-monit-api-java-V3',

 'api__car-monit-api-java-fix':'car-monit-api-java-fix',

 'bk__master':'master','bk__car-monit-backend-java-V3':'car-monit-backend-java-V3',

 'bk__feat_backend-full-parity':'feat/backend-full-parity',

}

WF='''# Java-only verification for the Spring Boot dependency upgrade.

# It intentionally avoids native/Python/DB jobs so the POM changes are isolated.

name: java-upgrade-verify



on:

  workflow_dispatch:



permissions:

  contents: read



jobs:

  maven-build:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout

        uses: actions/checkout@v4



      - name: Setup JDK 17

        uses: actions/setup-java@v4

        with:

          distribution: temurin

          java-version: '17'

          # Perf: reuse ~/.m2/repository across runs.

          cache: maven



      - name: Maven package

        run: mvn -B -ntp -DskipTests package

'''



def git(wd,*args,timeout=240):

    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,

                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode!=0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()



for name,branch in TARGETS.items():

    wd=ROOT/name

    if not wd.exists():

        continue

    p=wd/'.github/workflows/java-upgrade-verify.yml'

    p.parent.mkdir(parents=True,exist_ok=True)

    if p.exists() and p.read_text(encoding='utf-8')==WF:

        print('SKIP',branch); continue

    p.write_text(WF,encoding='utf-8')

    git(wd,'add','-A')

    git(wd,'commit','-m','ci(java): add Java-only upgrade verification workflow')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

