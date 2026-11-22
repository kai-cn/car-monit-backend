#!/usr/bin/env python3
"""简化 LettuceClusterClient，避免依赖跨版本不稳定的连接类型。

背景：Boot2/Boot3 的 Lettuce 版本中 StatefulRedisClusterConnection 包路径/方法不稳定，
云 runner 报 cannot find symbol。原 JedisCluster 也没有显式关闭，故保留最小语义即可。

思路：
1. 删除 StatefulRedisClusterConnection import 和字段。
2. 构造时 client.connect().sync() 获取命令接口。
3. close() 仅 client.shutdown()；不调用命令接口的专用方法。
4. 本地 commit + push 到每个 api 分支。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
REL='pro-base-common/src/main/java/com/ruoyi/common/core/redis/LettuceClusterClient.java'
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

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
        continue
    t=p.read_text(encoding='utf-8')
    if 'StatefulRedisClusterConnection' not in t:
        print('SKIP',wd.name); continue
    n=t.replace('import io.lettuce.core.cluster.StatefulRedisClusterConnection;\n','')
    n=n.replace('    private final StatefulRedisClusterConnection<String, String> connection;\n','')
    n=n.replace('        this.connection = client.connect();\n        this.commands = connection.sync();\n',
                '        this.commands = client.connect().sync();\n')
    n=n.replace('        connection.close();\n','')
    p.write_text(n,encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','fix(redis): avoid version-specific Lettuce connection API')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
