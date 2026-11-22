#!/usr/bin/env python3

"""
@description 历史脚本 add_crosslang_to_master.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python add_crosslang_to_master.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Add crosslang workflow + parity tooling + SQL to backend master (via plumbing, no checkout)."""

import os, subprocess, sys



repo = r'D:\work\IdeaProjects\car-monit-backend-java-V3'

jdk25 = r'D:\work\IdeaProjects\car-monit-backend-jdk25'

repo_root = r'D:\work\IdeaProjects\car-monit-backend-new'



files = {

    # dst path on master : source path on disk

    '.github/workflows/crosslang-parity-cloud.yml': os.path.join(repo_root, '.github/workflows/crosslang-parity-cloud.yml'),

    'scripts/v3/ops/parity/parity_probe.py': os.path.join(jdk25, 'scripts/v3/ops/parity/parity_probe.py'),

    'scripts/v3/ops/parity/parity_compare.py': os.path.join(jdk25, 'scripts/v3/ops/parity/parity_compare.py'),

    'scripts/v3/ops/parity/endpoints/backend.txt': os.path.join(jdk25, 'scripts/v3/ops/parity/endpoints/backend.txt'),

    'scripts/v3/ops/parity/sql/schema_carmonitdb.sql': os.path.join(jdk25, 'scripts/v3/ops/parity/sql/schema_carmonitdb.sql'),

    'scripts/v3/ops/parity/sql/seed_carmonitdb.sql': os.path.join(jdk25, 'scripts/v3/ops/parity/sql/seed_carmonitdb.sql'),

}

msg = 'test(parity): add crosslang Java8-vs-go/python/rust harness + parity tooling to master'





def git(*a, input=None):

    return subprocess.run(['git', '-C', repo, *a], input=input, capture_output=True, text=True,

                          encoding='utf-8', errors='replace')





base = git('rev-parse', 'refs/remotes/origin/master').stdout.strip()

print('base master:', base[:7])

# sanity: base must already contain the registered parity-verify-cloud workflow

if 'parity-verify-cloud.yml' not in git('ls-tree', '-r', '--name-only', base, '.github/workflows/').stdout:

    print('ERROR: base lacks parity-verify-cloud.yml; wrong base (stale ref?)'); sys.exit(1)



blobs = {}

for dst, src in files.items():

    if not os.path.exists(src):

        print('MISSING SRC', src); sys.exit(1)

    content = open(src, encoding='utf-8').read()

    blob = git('hash-object', '-w', '--stdin', input=content).stdout.strip()

    blobs[dst] = blob



env = os.environ.copy()

env['GIT_INDEX_FILE'] = os.path.join(os.environ.get('TEMP', '/tmp'), 'idx_crosslang.idx')

subprocess.run(['git', '-C', repo, 'read-tree', base], env=env, capture_output=True, check=True)

for dst, blob in blobs.items():

    subprocess.run(['git', '-C', repo, 'update-index', '--add', '--cacheinfo', f'100644,{blob},{dst}'],

                   env=env, capture_output=True, check=True)

tree = subprocess.run(['git', '-C', repo, 'write-tree'], env=env, capture_output=True, text=True, check=True).stdout.strip()

os.remove(env['GIT_INDEX_FILE'])

commit = git('commit-tree', tree, '-p', base, '-m', msg)

if commit.returncode != 0:

    print('commit err', commit.stderr); sys.exit(1)

c = commit.stdout.strip()

git('update-ref', 'refs/remotes/origin/master', c)

print('new master commit:', c[:7], 'files:', len(blobs))

