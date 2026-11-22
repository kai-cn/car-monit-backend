#!/usr/bin/env python3

"""
@description 历史脚本 update_master_file.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python update_master_file.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Update an existing remote/local value in place.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Update a single file on backend master via plumbing (no checkout of master)."""

import os, subprocess, sys



repo = r'D:\work\IdeaProjects\car-monit-backend-java-V3'

rel = sys.argv[1]              # e.g. .github/workflows/crosslang-parity-cloud.yml

src = sys.argv[2]              # local path with new content

msg = sys.argv[3] if len(sys.argv) > 3 else 'ci: update ' + rel





def git(*a, input=None):

    return subprocess.run(['git', '-C', repo, *a], input=input, capture_output=True, text=True,

                          encoding='utf-8', errors='replace')





base = git('rev-parse', 'refs/remotes/origin/master').stdout.strip()

print('base master:', base[:7])

content = open(src, encoding='utf-8').read()

blob = git('hash-object', '-w', '--stdin', input=content).stdout.strip()

env = os.environ.copy()

env['GIT_INDEX_FILE'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'idx_upd_%d.idx' % os.getpid())

subprocess.run(['git', '-C', repo, 'read-tree', base], env=env, capture_output=True, check=True)

subprocess.run(['git', '-C', repo, 'update-index', '--add', '--cacheinfo', f'100644,{blob},{rel}'],

               env=env, capture_output=True, check=True)

tree = subprocess.run(['git', '-C', repo, 'write-tree'], env=env, capture_output=True, text=True, check=True).stdout.strip()

os.remove(env['GIT_INDEX_FILE'])

c = git('commit-tree', tree, '-p', base, '-m', msg)

if c.returncode: print('ERR', c.stderr); sys.exit(1)

sha = c.stdout.strip()

git('update-ref', 'refs/remotes/origin/master', sha)

print('new master:', sha[:7])

