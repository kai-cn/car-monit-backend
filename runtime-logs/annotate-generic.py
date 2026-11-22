#!/usr/bin/env python3

"""
@description 历史脚本 annotate-generic.py：批量补充脚本或代码注释；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python annotate-generic.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Add a short purpose/risk header to ad-hoc operational scripts that still lack one."""

from pathlib import Path



ROOTS = [Path(r'D:\work\runtime-logs'), Path(r'D:\work\runtime-logs\v3-ops')]

PREFIX_PURPOSE = {

    'patch': 'Apply a targeted configuration/source patch produced during the native/CICD investigation.',

    'add': 'Add a missing option, resource, or reflection/config entry required by a later build step.',

    'fix': 'Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.',

    'apply': 'Apply a generated configuration to local or remote branches.',

    'probe': 'Read-only diagnostic: inspect state, logs, or environment without modifying the target.',

    'check': 'Validation helper; exits nonzero or reports evidence when an invariant is broken.',

    'compare': 'Compare two artifacts/branches/logs and emit a structured verdict.',

    'copy': 'Copy a file or configuration between locations, preserving binary content where needed.',

    'create': 'Create a git ref/branch or other remote object through the GitHub API.',

    'deploy': 'Deploy a harness/workflow file set to a branch via API or git plumbing.',

    'dump': 'Print a file section for diagnosis.',

    'fetch': 'Fetch remote content through the GitHub API using git-credential-derived token.',

    'filter': 'Filter long logs down to relevant error/status lines.',

    'grep': 'Extract structured matches (paths/options) from long command lines or logs.',

    'list': 'List repositories, classes, branches, or workflow files.',

    'put': 'Create/update a remote file via the GitHub contents API.',

    'run': 'Run a build/verification command with a fixed environment and write evidence.',

    'save': 'Persist a job log or artifact for later inspection.',

    'scan': 'Scan branches/workflows for a pattern or risk.',

    'set': 'Write GitHub Secrets or local configuration from runtime-supplied values only.',

    'sync': 'Synchronize local and remote branches/worktrees; skips dirty user work.',

    'update': 'Update an existing remote/local value in place.',

    'verify': 'Read-only verification of a security or build invariant.',

    'watch': 'Long-running monitor for GitHub Actions status.',

    'audit': 'Read-only audit of repository workflows or credentials exposure.',

    'harden': 'Apply workflow security hardening rules across branches.',

    'download': 'Download a build artifact or log through the GitHub API.',

    'collect': 'Collect run results into a concise report.',

    'auto': 'Automation helper created during the public-repo CICD session; inspect before running.',

    'bg': 'Background wrapper for a long-running monitor/build.',

    'checkports': 'Check that required local service ports are available before starting a service.',

    'build': 'Build command wrapper used by the native/CICD verification flow.',

    'v3': 'Native-image matrix helper; see docs/v3/final-jdk-matrix-verification-20261116.md.',

}



def purpose(name: str) -> str:

    stem = name.lower().replace('.ps1','').replace('.py','').replace('.sh','')

    for key in sorted(PREFIX_PURPOSE, key=len, reverse=True):

        if stem.startswith(key):

            return PREFIX_PURPOSE[key]

    return 'Operational helper created during the native/CICD verification session.'



def annotated(text: str) -> bool:

    head = '\n'.join(text.splitlines()[:6])

    return '# Purpose: ' in head or head.lstrip().startswith('"""') or '# Usage:' in head



changed = []

for root in ROOTS:

    if not root.exists():

        continue

    for p in sorted(root.iterdir()):

        if p.suffix.lower() not in ('.sh', '.py', '.ps1') or not p.is_file():

            continue

        text = p.read_text(encoding='utf-8', errors='replace')

        if annotated(text):

            continue

        header = ('# Operational helper — native/CICD verification session (2026-11-16~17).\n'

                  f'# Purpose: {purpose(p.name)}\n'

                  '# Risk: may call GitHub API or modify local/remote files; inspect before running.\n')

        if text.startswith('#!'):

            first, _, rest = text.partition('\n')

            text = first + '\n' + header + rest.lstrip('\n')

        else:

            text = header + text.lstrip('\n')

        p.write_text(text, encoding='utf-8')

        changed.append(str(p))

print('annotated', len(changed), 'scripts')

for c in changed[:40]:

    print(' ', c)

