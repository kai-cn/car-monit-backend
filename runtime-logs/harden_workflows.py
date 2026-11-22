#!/usr/bin/env python3

"""
@description 历史脚本 harden_workflows.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python harden_workflows.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply workflow security hardening rules across branches.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Batch-harden CI/CD workflows across ALL branches of both repos for public-repo safety.



Rules (idempotent):

  R1 self-hosted-ci.yml: remove push trigger + runner input; build on ubuntu-latest;

     deploy jobs -> owner guard + workflow_dispatch only; drop AUTO_DEPLOY_CLUSTER.

  R2 _java/_cpp/_go/_python.yml: runner selection vars -> fixed ubuntu-latest/windows-latest.

  R3 native-image.yml (self-hosted variant): add owner guard to every job.

  R4 native-image-cloud.yml: runner_mode options -> cloud only; add owner guard to jobs.

  R5 deploy-selfhosted.yml / selfhost-canary.yml / cd-standalone self-hosted jobs: owner guard.



Usage:

  python harden_workflows.py --dry-run

  python harden_workflows.py --apply        # creates local commits (no push)

"""

import argparse, os, re, subprocess, sys



REPOS = {

    'api': r'D:\work\IdeaProjects\car-monit-api-java-V3',

    'backend': r'D:\work\IdeaProjects\car-monit-backend-java-V3',

}

OWNER = 'kai-cn'





def git(repo, *args, input=None):

    return subprocess.run(['git', '-C', repo, *args], input=input, capture_output=True,

                          text=True, encoding='utf-8', errors='replace')





def branches(repo):

    out = git(repo, 'for-each-ref', '--format=%(refname)', 'refs/remotes/origin').stdout

    return [b.strip() for b in out.splitlines()

            if b.strip().startswith('refs/remotes/origin/')

            and b.strip() != 'refs/remotes/origin/HEAD']





def show(repo, ref, path):

    r = git(repo, 'show', f'{ref}:{path}')

    return r.stdout if r.returncode == 0 else None





def files(repo, ref, prefix='.github/workflows/'):

    r = git(repo, 'ls-tree', '-r', '--name-only', ref, prefix)

    return [f.strip() for f in r.stdout.splitlines() if f.strip().endswith(('.yml', '.yaml'))]





# --------------------------- transformations ---------------------------

def r1_selfhosted_ci(text):

    # Already hardened (V3): contains owner guard -> skip

    if "github.repository_owner == '" + OWNER + "'" in text:

        return text, False

    orig = text

    # 1) Replace the whole `on:` block (dispatch inputs + push) with dispatch-only deploy_mode.

    text = re.sub(

        r'on:\n(?:.*\n)*?(?=permissions:\n)',

        "on:\n"

        "  workflow_dispatch:\n"

        "    inputs:\n"

        "      deploy_mode:\n"

        "        description: '部署方式（none=只产产物）'\n"

        "        type: choice\n"

        "        options: [none, standalone, cluster]\n"

        "        default: none\n\n",

        text, count=1)

    # 2) build runs-on (dynamic expression) -> ubuntu-latest

    text = re.sub(

        r"runs-on: \$\{\{ inputs\.runner == 'self-hosted'.*?\}\}",

        "runs-on: ubuntu-latest", text)

    # 3) deploy job if-guards: add owner guard, drop push/AUTO_DEPLOY

    text = text.replace(

        "if: github.event_name == 'workflow_dispatch' && inputs.deploy_mode == 'standalone'",

        "if: github.repository_owner == '" + OWNER + "' && github.event_name == 'workflow_dispatch' && inputs.deploy_mode == 'standalone'")

    text = re.sub(

        r"if: \|\n\s*always\(\) && needs\.build\.result == 'success' && \(\n.*?\n.*?\n\s*\)",

        "if: |\n"

        "      github.repository_owner == '" + OWNER + "' && needs.build.result == 'success' &&\n"

        "      github.event_name == 'workflow_dispatch' && inputs.deploy_mode == 'cluster'",

        text, flags=re.S)

    # 4) fix stale header comments that claim push / runner switching

    text = text.replace('# - 构建：托管优先；runner 输入或变量 CI_RUNNER_JSON 可整体切自托管。',

                        '# - 构建：固定 GitHub 托管 runner；不受任何变量/inputs 切到自托管。')

    text = text.replace('# - 产物：push 任意分支产 jar+sha256，artifact 名带 branch+sha 防覆盖，k3d 与单机共用。',

                        '# - 触发：仅 workflow_dispatch；公开后不可信代码不会触达自托管 runner。')

    text = re.sub(r'# - push 自动部署 k3d：设 vars\.AUTO_DEPLOY_CLUSTER=true 开启（默认关）。\n', '', text)

    return text, text != orig





def r2_reusable(text, path):

    orig = text

    # CI_RUNNER_LABELS / CI_RUNNER_JSON dynamic selection -> fixed cloud

    text = re.sub(r"runs-on: \$\{\{ fromJSON\(vars\.CI_RUNNER_LABELS \|\| '\[\"ubuntu-latest\"\]'\) \}\}",

                  "runs-on: ubuntu-latest", text)

    # cpp reusable may use windows in some cells; leave windows-latest literal as-is

    return text, text != orig





def add_job_owner_guard(text, already_marker='github.repository_owner'):

    """Add owner guard to self-hosted/dynamic-runner jobs, merging into an existing `if:`."""

    if already_marker in text:

        return text, False

    orig = text

    lines = text.splitlines(keepends=True)

    guard = f"github.repository_owner == '{OWNER}'"

    # Pass 1: identify target job line ranges (2-space indented job keys under `jobs:`).

    in_jobs = False

    job_ranges = []       # (start_idx, end_idx, indent)

    cur = None

    for i, line in enumerate(lines):

        if re.match(r'^jobs:\s*$', line):

            in_jobs = True

            continue

        if not in_jobs:

            continue

        if re.match(r'^\S', line):        # top-level key -> left jobs block

            break

        m = re.match(r'^(  )([A-Za-z0-9_-]+):\s*$', line)

        if m:

            if cur:

                job_ranges.append((cur[0], i, cur[1]))

            cur = (i, m.group(1))

    if cur:

        job_ranges.append((cur[0], len(lines), cur[1]))

    # Pass 2: for each target job, merge guard into existing `if:` or insert one.

    edits = []  # (idx, replacement_line) or (idx, None, insert_line)

    for start, end, indent in job_ranges:

        block = lines[start:end]

        runs_idx = next((start + j for j, l in enumerate(block)

                         if re.search(r'runs-on:.*(inputs\.runner_label|self-hosted|inputs\.linux_runner|inputs\.windows_runner)', l)), None)

        if runs_idx is None:

            continue

        job_if_indent = indent + '  '

        if_idx = next((start + j for j, l in enumerate(block)

                       if re.match(r'^' + re.escape(job_if_indent) + r'if:', l)), None)

        if if_idx is not None:

            line = lines[if_idx]

            newline = '\n' if line.endswith('\n') else ''

            body = line.rstrip('\n')

            # multiline `if: |` -> append a new guarded line is unsafe; wrap by adding owner line as first line of block scalar

            if body.rstrip().endswith('|') or body.rstrip().endswith('>'):

                scalar_indent = re.match(r'\s*', lines[if_idx+1]).group(0)

                edits.append((if_idx + 1, None, f"{scalar_indent}{guard} &&\n"))

            else:

                edits.append((if_idx, body + f' && {guard}' + newline, None))

        else:

            edits.append((runs_idx, None, f"{job_if_indent}if: {guard}\n"))

    # Apply edits from bottom to top so indices stay valid.

    for item in sorted(edits, key=lambda x: x[0], reverse=True):

        idx = item[0]

        if item[2] is not None:

            lines.insert(idx, item[2])

        else:

            lines[idx] = item[1]

    return ''.join(lines), ''.join(lines) != orig





def apply_rules(path, text):

    base = os.path.basename(path)

    changed = False

    if base == 'self-hosted-ci.yml':

        text, c = r1_selfhosted_ci(text); changed |= c

    elif base in ('_java.yml', '_cpp.yml', '_go.yml', '_python.yml'):

        text, c = r2_reusable(text, path); changed |= c

    if base in ('native-image.yml', 'native-image-cloud.yml', 'deploy-selfhosted.yml', 'selfhost-canary.yml'):

        text, c = add_job_owner_guard(text); changed |= c

    # native-image-cloud: restrict runner_mode to cloud only

    if base == 'native-image-cloud.yml':

        orig = text

        text = text.replace('options: [cloud, self-hosted]', 'options: [cloud]')

        changed |= text != orig

    return text, changed





def apply_to_branch(repo, br, mods):

    """Create a commit on top of br via git plumbing (no checkout / no worktree change)."""

    base = git(repo, 'rev-parse', br).stdout.strip()

    # Write new blobs

    updates = []

    for path, newtext in mods:

        h = git(repo, 'hash-object', '-w', '--stdin', input=newtext)

        if h.returncode != 0:

            raise RuntimeError('hash-object failed: ' + h.stderr)

        updates.append((path, h.stdout.strip()))

    # Build a temp index from base tree, apply updates, write tree

    tmp_index = os.path.join(os.environ.get('TEMP', '/tmp'), f'harden_idx_{os.getpid()}_{abs(hash(br))}.idx')

    env = os.environ.copy()

    env['GIT_INDEX_FILE'] = tmp_index

    subprocess.run(['git', '-C', repo, 'read-tree', base], env=env, capture_output=True, check=True)

    for path, blob in updates:

        mode = git(repo, 'ls-tree', base, '--', path).stdout.split()[0]

        subprocess.run(['git', '-C', repo, 'update-index', '--add', '--cacheinfo', f'{mode},{blob},{path}'],

                       env=env, capture_output=True, check=True)

    tree = subprocess.run(['git', '-C', repo, 'write-tree'], env=env, capture_output=True, text=True, check=True).stdout.strip()

    os.remove(tmp_index)

    # Commit

    msg = 'ci(hardening): force cloud runners + owner guards across all workflows'

    commit = git(repo, 'commit-tree', tree, '-p', base, '-m', msg)

    if commit.returncode != 0:

        raise RuntimeError('commit-tree failed: ' + commit.stderr)

    return commit.stdout.strip(), base





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument('--apply', action='store_true')

    ap.add_argument('--dry-run', action='store_true')

    args = ap.parse_args()



    for reponame, repo in REPOS.items():

        print(f'\n===== {reponame} =====')

        plan = []

        for br in branches(repo):

            short = br.replace('origin/', '')

            mods = []

            for f in files(repo, br):

                content = show(repo, br, f)

                if content is None:

                    continue

                new, ch = apply_rules(f, content)

                if ch:

                    mods.append((f, new))

            if mods:

                print(f'  {short:35s} {len(mods)} file(s): ' + ', '.join(os.path.basename(f) for f, _ in mods))

                plan.append((br, mods))

            else:

                print(f'  {short:35s} -')

        if args.apply:

            for br, mods in plan:

                try:

                    commit, base = apply_to_branch(repo, br, mods)

                    # Update local remote-tracking ref to the new commit (fast-forward)

                    git(repo, 'update-ref', br, commit)

                    print(f'  COMMITTED {br}: {base[:7]} -> {commit[:7]}')

                except Exception as e:

                    print(f'  ERROR {br}: {e}')





if __name__ == '__main__':

    main()

