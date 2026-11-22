#!/usr/bin/env python3

"""
@description 历史脚本 add_wf_to_master.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python add_wf_to_master.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Add the parity workflow file to the default branch (master) so workflow_dispatch is registered.



The workflow body is identical; dispatch will use ref=<feature branch> which carries both the

workflow and scripts/v3/ops/parity/*.

"""

import os, subprocess, sys



repo = r'D:\work\IdeaProjects\car-monit-api-java-V3'

wf_src = r'D:\work\IdeaProjects\car-monit-api-jdk25\.github\workflows\parity-verify-cloud.yml'

relpath = '.github/workflows/parity-verify-cloud.yml'

msg = 'ci(parity): register parity-verify-cloud on default branch for workflow_dispatch'





def git(*a, input=None):

    return subprocess.run(['git', '-C', repo, *a], input=input, capture_output=True, text=True,

                          encoding='utf-8', errors='replace')





base = git('rev-parse', 'FETCH_HEAD').stdout.strip()

print('base master:', base[:7])

# does it already exist?

if git('cat-file', '-e', f'{base}:{relpath}').returncode == 0:

    print('already present on master, skipping')

    sys.exit(0)



content = open(wf_src, encoding='utf-8').read()

blob = git('hash-object', '-w', '--stdin', input=content).stdout.strip()

print('blob:', blob)



env = os.environ.copy()

env['GIT_INDEX_FILE'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'idx_master_parity.idx')

subprocess.run(['git', '-C', repo, 'read-tree', base], env=env, capture_output=True, check=True)

mode = '100644'

subprocess.run(['git', '-C', repo, 'update-index', '--add', '--cacheinfo', f'{mode},{blob},{relpath}'],

               env=env, capture_output=True, check=True)

tree = subprocess.run(['git', '-C', repo, 'write-tree'], env=env, capture_output=True, text=True,

                      check=True).stdout.strip()

os.remove(env['GIT_INDEX_FILE'])

commit = git('commit-tree', tree, '-p', base, '-m', msg)

if commit.returncode != 0:

    print('commit error:', commit.stderr)

    sys.exit(1)

c = commit.stdout.strip()

print('new commit:', c[:7])

git('update-ref', 'refs/heads/master', c)

print('updated refs/heads/master ->', c[:7])

