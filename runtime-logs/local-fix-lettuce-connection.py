#!/usr/bin/env python3

"""
@description 历史脚本 local-fix-lettuce-connection.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python local-fix-lettuce-connection.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：云 runner 报 RedisClusterCommands.getStatefulConnection() 不存在。


Lettuce 的 sync() 接口在部分版本没有这个方法；连接对象应在 connect() 时单独保存。





思路：


1. 增加 StatefulRedisClusterConnection 字段。


2. 构造时先 connect()，再从 connection.sync() 获取命令接口。


3. close() 关闭保存的连接并 shutdown client。


4. 仅修改 api 临时工作树中的 LettuceClusterClient.java，本地 commit + push。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

REL='pro-base-common/src/main/java/com/ruoyi/common/core/redis/LettuceClusterClient.java'

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

IMPORT='import io.lettuce.core.cluster.StatefulRedisClusterConnection;\n'

FIELD='    private final StatefulRedisClusterConnection<String, String> connection;\n'



def git(wd,*args,timeout=240):

    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,

                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)

    if r.returncode!=0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()



for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir() or not wd.name.startswith('api__'):

        continue

    p=wd/REL

    if not p.exists():

        print('MISSING',wd.name); continue

    t=p.read_text(encoding='utf-8')

    if 'StatefulRedisClusterConnection' in t:

        print('SKIP',wd.name); continue

    n=t.replace('import io.lettuce.core.cluster.RedisClusterClient;\n',

                'import io.lettuce.core.cluster.RedisClusterClient;\n'+IMPORT,1)

    n=n.replace('    private final RedisClusterClient client;\n',

                '    private final RedisClusterClient client;\n'+FIELD,1)

    n=n.replace('        this.client = RedisClusterClient.create(nodes);\n        this.commands = client.connect().sync();\n',

                '        this.client = RedisClusterClient.create(nodes);\n'

                '        this.connection = client.connect();\n'

                '        this.commands = connection.sync();\n',1)

    n=n.replace('        commands.getStatefulConnection().close();\n',

                '        connection.close();\n',1)

    if n==t:

        print('NOCHANGE',wd.name); continue

    p.write_text(n,encoding='utf-8')

    branch=wd.name.split('__',1)[1].replace('_','/')

    git(wd,'add','-A')

    git(wd,'commit','-m','fix(redis): keep Lettuce cluster connection reference')

    out=git(wd,'push','origin','HEAD:'+branch)

    print('PUSHED',branch)

