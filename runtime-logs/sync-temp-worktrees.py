#!/usr/bin/env python3

"""
@description 历史脚本 sync-temp-worktrees.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python sync-temp-worktrees.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

思路：


1. 对每个 _pom-upgrade 工作树，先从其 origin 仓库 fetch 对应分支。


2. 若本地有提交，用 git rebase refs/remotes/origin/<branch> 保持线性历史。


3. 冲突则报告并停止该分支，不做 --force 或 reset --hard。
"""
import os

import subprocess

from pathlib import Path



ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')

REPO_API=r'D:\work\IdeaProjects\car-monit-api'

REPO_BK=r'D:\work\IdeaProjects\car-monit-backend-new'

ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')



def run(args,cwd=None,check=True):

    r=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',

                     errors='replace',env=ENV,timeout=240)

    if check and r.returncode!=0:

        raise RuntimeError(f'{" ".join(args)} failed: {r.stderr.strip()}')

    return r



for wd in sorted(ROOT.iterdir()):

    if not wd.is_dir():

        continue

    branch=wd.name.split('__',1)[1].replace('_','/')

    origin=REPO_BK if wd.name.startswith('bk__') else REPO_API

    run(['git','fetch','origin',branch],cwd=origin)

    try:

        run(['git','rebase',f'refs/remotes/origin/{branch}'],cwd=wd)

        print('REBASED',branch)

    except RuntimeError as e:

        print('CONFLICT',branch,e)

