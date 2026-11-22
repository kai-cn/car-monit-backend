#!/usr/bin/env python3
"""把 backend Logback 路径改为可通过 LOG_PATH 覆盖，并在 native AOT 使用临时目录。

背景：/home/ruoyi/logs 在云 runner 上创建/授权未生效；logback.xml 中的
<property name="log.path" value="/home/ruoyi/logs"> 是本地属性，无法被系统属性覆盖。

思路：
1. logback.xml 改为 `${LOG_PATH:-/home/ruoyi/logs}`，保留原默认值。
2. native workflow 的 AOT 步骤设置 LOG_PATH=${{ runner.temp }}/ruoyi-logs。
3. AOT 命令中创建该目录。
4. 本地 commit + push。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')
LOG='ruoyi-admin/src/main/resources/logback.xml'
OLD_PROP='<property name="log.path" value="/home/ruoyi/logs" />'
NEW_PROP='<property name="log.path" value="${LOG_PATH:-/home/ruoyi/logs}" />'
WF='.github/workflows/native-image-cloud.yml'
OLD_STEP='''      - name: AOT + native-image
        shell: bash
        run: |
'''
NEW_STEP='''      - name: AOT + native-image
        shell: bash
        env:
          LOG_PATH: ${{ runner.temp }}/ruoyi-logs
        run: |
          mkdir -p "$LOG_PATH"
'''

def git(wd,*args,timeout=240):
    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,
                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)
    if r.returncode!=0:
        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()

for wd in sorted(ROOT.iterdir()):
    if not wd.is_dir() or not wd.name.startswith('bk__'):
        continue
    changed=False
    p=wd/LOG
    if p.exists() and OLD_PROP in p.read_text(encoding='utf-8'):
        p.write_text(p.read_text(encoding='utf-8').replace(OLD_PROP,NEW_PROP),encoding='utf-8')
        changed=True
    w=wd/WF
    if w.exists() and OLD_STEP in w.read_text(encoding='utf-8'):
        w.write_text(w.read_text(encoding='utf-8').replace(OLD_STEP,NEW_STEP,1),encoding='utf-8')
        changed=True
    if not changed:
        print('SKIP',wd.name); continue
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','fix(native): make Logback path overridable in AOT')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
