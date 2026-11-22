#!/usr/bin/env python3

"""
@description 历史脚本 local-fix-redis-cluster-provider.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python local-fix-redis-cluster-provider.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

思路：只处理 api 工作树中的 RedisClusterProvider.java；


LettuceClusterClient 实现 AutoCloseable，原 close() 语义保持不变。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

REL='pro-base-common/src/main/java/com/ruoyi/common/core/redis/RedisClusterProvider.java'

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

    p=wd/REL

    if not p.exists() or 'JedisCluster' not in p.read_text(encoding='utf-8'):

        continue

    t=p.read_text(encoding='utf-8')

    n=t.replace('import redis.clients.jedis.JedisCluster;','import com.ruoyi.common.core.redis.LettuceClusterClient;')

    n=n.replace('JedisCluster','LettuceClusterClient')

    p.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','fix(redis): migrate RedisClusterProvider to Lettuce')

    git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

