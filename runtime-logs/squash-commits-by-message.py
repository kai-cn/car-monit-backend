#!/usr/bin/env python3
"""把指定分支上提交信息精确匹配的提交合并为一个提交（通用脚本）。

设计思路：
1. 从远端引用读取第一父提交链，按提交信息首行精确匹配目标消息。
2. 支持目标提交分散在多个连续区间：每个区间重建为一个新提交，使用区间内
   最新提交的树对象，父提交是上一段重建后的提交。
3. 非目标提交以原树对象、原提交信息重建，保证文件内容不变。
4. 默认 dry-run；只有 --apply 才创建 backup ref、更新远端分支。
5. 使用 --force-with-lease，避免覆盖他人推送；拒绝 main/master 分支。

用法示例：
  python squash-commits-by-message.py \
    --repo D:/work/IdeaProjects/car-monit-backend-java-V3 \
    --branch car-monit-backend-java-V3 \
    --message "docs(scripts): add rationale and risk notes to historical scripts" \
    --new-message "docs(scripts): add rationale and risk notes to historical scripts" \
    --apply

风险：历史会被重写，提交 id 改变；务必确认分支不是 main/master，且已了解影响。
"""
import argparse
import datetime
import subprocess
import sys


def git(repo, *args, check=True):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if check and r.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()


def commit_subject(repo, sha):
    return git(repo, 'show', '-s', '--format=%s', sha)


def commit_body(repo, sha):
    return git(repo, 'show', '-s', '--format=%B', sha)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, help='local git repository path')
    ap.add_argument('--branch', required=True, help='remote branch name to rewrite')
    ap.add_argument('--message', required=True, help='exact commit subject to squash')
    ap.add_argument('--new-message', default=None, help='message for the squashed commit')
    ap.add_argument('--remote', default='origin')
    ap.add_argument('--apply', action='store_true', help='actually rewrite and force-with-lease push')
    args = ap.parse_args()

    if args.branch in {'main', 'master'}:
        print('REFUSE: refusing to rewrite main/master')
        return 2

    new_message = args.new_message or args.message
    ref = f'refs/remotes/{args.remote}/{args.branch}'
    git(args.repo, 'fetch', args.remote, args.branch)

    original_head = git(args.repo, 'rev-parse', ref)
    newest_first = git(args.repo, 'rev-list', '--first-parent', original_head).splitlines()
    if not newest_first:
        print('ERROR: empty history')
        return 2

    oldest_first = list(reversed(newest_first))
    parents_line = git(args.repo, 'rev-list', '--parents', '-n', '1', oldest_first[0]).split()
    parent = parents_line[1] if len(parents_line) > 1 else None
    squashed = 0
    rebuilt = 0
    plan = []

    i = 0
    while i < len(oldest_first):
        sha = oldest_first[i]
        if commit_subject(args.repo, sha) == args.message:
            block = []
            while i < len(oldest_first) and commit_subject(args.repo, oldest_first[i]) == args.message:
                block.append(oldest_first[i])
                i += 1
            newest_in_block = block[-1]
            plan.append(('SQUASH', len(block), newest_in_block, new_message))
            if args.apply:
                tree = git(args.repo, 'rev-parse', f'{newest_in_block}^{{tree}}')
                cmd = ['-c', 'user.name=CodeBuddy', '-c', 'user.email=codebuddy@example.com',
                       'commit-tree', tree, '-m', new_message]
                if parent:
                    cmd += ['-p', parent]
                parent = git(args.repo, *cmd)
            squashed += len(block)
            rebuilt += 1
        else:
            plan.append(('KEEP', 1, sha, commit_subject(args.repo, sha)))
            if args.apply:
                tree = git(args.repo, 'rev-parse', f'{sha}^{{tree}}')
                body = commit_body(args.repo, sha).rstrip('\n') or commit_subject(args.repo, sha)
                cmd = ['-c', 'user.name=CodeBuddy', '-c', 'user.email=codebuddy@example.com',
                       'commit-tree', tree, '-m', body]
                if parent:
                    cmd += ['-p', parent]
                parent = git(args.repo, *cmd)
            rebuilt += 1
            i += 1

    print('branch:', args.branch)
    print('original_head:', original_head)
    print('matching_commits:', squashed)
    print('rebuilt_commits:', rebuilt)
    for action, count, sha, msg in plan:
        print(f'{action:6} x{count:<3} {sha[:8]} {msg[:90]}')

    if not args.apply:
        print('DRY_RUN: no changes made')
        return 0
    if squashed == 0:
        print('NO_MATCH: no commits squashed')
        return 0

    backup = f'refs/backup/squash-{args.branch}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    git(args.repo, 'update-ref', backup, original_head)
    temp_ref = f'refs/heads/squash-{args.branch}'
    git(args.repo, 'update-ref', temp_ref, parent)
    git(args.repo, 'push', args.remote, f'{temp_ref}:refs/heads/{args.branch}', '--force-with-lease')
    print('NEW_HEAD:', parent)
    print('BACKUP_REF:', backup)
    return 0


if __name__ == '__main__':
    sys.exit(main())
