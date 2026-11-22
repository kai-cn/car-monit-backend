#!/usr/bin/env python3

"""
@description 历史脚本 local-fix-unreachable-catch.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-fix-unreachable-catch.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：部分业务逻辑改用 java.util.Base64 / Lettuce 后，try 块不再声明 IOException，


javac 报 "exception java.io.IOException is never thrown"。





思路：


1. 只处理 api__car-monit-api-java-fix 工作树。


2. 把 catch (IOException e) 改为 catch (Exception e)，保持错误日志语义且可通过编译。


3. 本地 commit + push，然后只需重跑该分支。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade\api__car-monit-api-java-fix')

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')



def git(*args,timeout=240):

    r=subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,text=True,

                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode!=0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()



changed=[]

for p in ROOT.rglob('*.java'):

    t=p.read_text(encoding='utf-8')

    n=t.replace('catch (IOException e)','catch (Exception e)')

    if n!=t:

        p.write_text(n,encoding='utf-8')

        changed.append(str(p.relative_to(ROOT)))

if not changed:

    print('NOCHANGE'); raise SystemExit

git('add','-A')

git('commit','-m','fix(java): make legacy IOException catches reachable')

git('push','origin','HEAD:car-monit-api-java-fix')

print('PUSHED',','.join(changed))

