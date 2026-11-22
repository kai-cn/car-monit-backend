#!/usr/bin/env python3

"""
@description 历史脚本 deploy_parity_to_branch.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python deploy_parity_to_branch.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Deploy a harness/workflow file set to a branch via API or git plumbing.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Copy parity workflow + tooling + SQL from a source branch to a target branch (plumbing).



Usage: python deploy_parity_to_branch.py <repo_key> <target_branch>

  repo_key: api | backend

"""

import os, subprocess, sys



REPOS = {

    'api': dict(path=r'D:\work\IdeaProjects\car-monit-api-java-V3',

                src_branch='refs/remotes/origin/car-monit-api-jdk25',

                files=['.github/workflows/parity-verify-cloud.yml',

                       'scripts/v3/ops/parity/parity_probe.py',

                       'scripts/v3/ops/parity/parity_compare.py',

                       'scripts/v3/ops/parity/endpoints/api.txt',

                       'scripts/v3/ops/parity/sql/schema_jl_data01.sql',

                       'scripts/v3/ops/parity/sql/seed_jl_data01.sql.gz',

                       'scripts/v3/ops/parity/sql/mysql_dict.sql']),

    'backend': dict(path=r'D:\work\IdeaProjects\car-monit-backend-java-V3',

                    src_branch='refs/remotes/origin/car-monit-backend-jdk25',

                    files=['.github/workflows/parity-verify-cloud.yml',

                           'scripts/v3/ops/parity/parity_probe.py',

                           'scripts/v3/ops/parity/parity_compare.py',

                           'scripts/v3/ops/parity/endpoints/backend.txt',

                           'scripts/v3/ops/parity/sql/schema_carmonitdb.sql',

                           'scripts/v3/ops/parity/sql/seed_carmonitdb.sql']),

}



key = sys.argv[1]

target = sys.argv[2]

cfg = REPOS[key]

repo = cfg['path']

src = cfg['src_branch']

tref = f'refs/remotes/origin/{target}'





def git(*a, input=None):

    return subprocess.run(['git', '-C', repo, *a], input=input, capture_output=True,

                          encoding=None if isinstance(input, bytes) else 'utf-8',

                          text=not isinstance(input, bytes), errors='replace')





base = git('rev-parse', tref).stdout.strip()

if not base:

    print('no target ref', tref); sys.exit(1)

print(f'{key}/{target}: base={base[:7]}')



blobs = {}

for f in cfg['files']:

    # Read raw bytes (binary-safe) so .gz blobs are not corrupted by text decoding.

    content = subprocess.run(['git', '-C', repo, 'show', f'{src}:{f}'], capture_output=True)

    if content.returncode != 0:

        print('SKIP missing', f); continue

    # hash-object with binary input

    h = subprocess.run(['git', '-C', repo, 'hash-object', '-w', '--stdin'],

                       input=content.stdout, capture_output=True)

    blob = h.stdout.decode().strip()

    blobs[f] = blob



env = os.environ.copy()

env['GIT_INDEX_FILE'] = os.path.join(os.environ.get('TEMP', '/tmp'), f'idx_dep_{key}_{target}.idx')

subprocess.run(['git', '-C', repo, 'read-tree', base], env=env, capture_output=True, check=True)

for f, blob in blobs.items():

    subprocess.run(['git', '-C', repo, 'update-index', '--add', '--cacheinfo', f'100644,{blob},{f}'],

                   env=env, capture_output=True, check=True)

tree = subprocess.run(['git', '-C', repo, 'write-tree'], env=env, capture_output=True, text=True, check=True).stdout.strip()

os.remove(env['GIT_INDEX_FILE'])

c = git('commit-tree', tree, '-p', base, '-m', 'test(parity): add cloud native-vs-jvm parity harness')

if c.returncode:

    print('ERR', c.stderr); sys.exit(1)

sha = c.stdout.strip()

git('update-ref', tref, sha)

print(f'committed {target} -> {sha[:7]} ({len(blobs)} files)')

