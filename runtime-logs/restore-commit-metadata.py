#!/usr/bin/env python3

"""
@description 历史脚本 restore-commit-metadata.py：恢复工作树、提交元数据或容器状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python restore-commit-metadata.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

背景：按提交信息 squash 历史时，所有重建提交被统一写成 CodeBuddy；


源备份引用中保留了原始 author/committer 名称、邮箱和时间。





思路：


1. 读取当前分支与源引用的第一父提交链。


2. 用 (subject, tree) 作为键，按时间顺序把当前提交映射到源提交。


3. squash 后的单个提交会映射到被合并区间中树相同的那个原始提交。


4. 按当前树的顺序重建提交链，但使用映射到的原始 author/committer 元数据。


5. 源中不存在的提交保留当前元数据。


6. 默认 dry-run；--apply 才写远端。拒绝 main/master，force-with-lease。





用法：


  python restore-commit-metadata.py \


    --repo D:/work/IdeaProjects/car-monit-backend-java-V3 \


    --branch car-monit-backend-java-V3 \


    --source-ref refs/backup/squash-car-monit-backend-java-V3-20261121151255 \


    --apply
"""
import argparse

import datetime

import os

import subprocess

import sys





def git(repo, *args, check=True, env=None, input_text=None):

    e = dict(os.environ)

    if env:

        e.update(env)

    r = subprocess.run(['git', '-C', repo, *args], input=input_text,

                       capture_output=True, text=True, encoding='utf-8',

                       errors='replace', env=e)

    if check and r.returncode != 0:

        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')

    return r.stdout.strip()





def rev_list(repo, ref):

    return git(repo, 'rev-list', '--first-parent', ref).splitlines()





def key_and_meta(repo, sha):

    subject = git(repo, 'show', '-s', '--format=%s', sha)

    tree = git(repo, 'rev-parse', f'{sha}^{{tree}}')

    raw = git(repo, 'show', '-s', '--format=%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI', sha)

    an, ae, ad, cn, ce, cd = raw.split('\0')

    body = git(repo, 'show', '-s', '--format=%B', sha).rstrip('\n') or subject

    return (subject, tree), {

        'an': an, 'ae': ae, 'ad': ad,

        'cn': cn, 'ce': ce, 'cd': cd,

        'body': body, 'subject': subject,

    }





def env_for(meta):

    return {

        'GIT_AUTHOR_NAME': meta['an'], 'GIT_AUTHOR_EMAIL': meta['ae'], 'GIT_AUTHOR_DATE': meta['ad'],

        'GIT_COMMITTER_NAME': meta['cn'], 'GIT_COMMITTER_EMAIL': meta['ce'], 'GIT_COMMITTER_DATE': meta['cd'],

    }





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument('--repo', required=True)

    ap.add_argument('--branch', required=True)

    ap.add_argument('--source-ref', required=True)

    ap.add_argument('--remote', default='origin')

    ap.add_argument('--apply', action='store_true')

    args = ap.parse_args()



    if args.branch in {'main', 'master'}:

        print('REFUSE: refusing to rewrite main/master')

        return 2



    git(args.repo, 'fetch', args.remote, args.branch)

    head_ref = f'refs/remotes/{args.remote}/{args.branch}'

    head = git(args.repo, 'rev-parse', head_ref)

    current = rev_list(args.repo, head_ref)

    source = rev_list(args.repo, args.source_ref)



    source_entries = [key_and_meta(args.repo, s) for s in source]

    current_entries = [key_and_meta(args.repo, s) for s in current]



    cursor = 0

    mapping = []

    matched = []

    for key, cur_meta in current_entries:

        found = None

        i = cursor

        while i < len(source_entries):

            skey, smeta = source_entries[i]

            i += 1

            if skey == key:

                found = smeta

                cursor = i

                break

        mapping.append(found or cur_meta)

        matched.append(found is not None)



    restored = sum(matched)

    changed = sum(1 for sha, m in zip(current, mapping)

                  if f'{m["an"]} <{m["ae"]}>' != git(args.repo, 'show', '-s', '--format=%an <%ae>', sha))



    print('branch:', args.branch)

    print('head:', head)

    print('source_ref:', args.source_ref)

    print('current_commits:', len(current))

    print('mapped_to_source:', restored)

    print('metadata_would_change:', changed)

    if not args.apply:

        print('DRY_RUN: no changes made')

        return 0



    oldest_first = list(reversed(list(zip(current, current_entries, mapping))))

    parents_line = git(args.repo, 'rev-list', '--parents', '-n', '1', current[-1]).split()

    parent = parents_line[1] if len(parents_line) > 1 else None

    for sha, (key, cur_meta), meta in oldest_first:

        tree = key[1]

        cmd = ['-c', 'user.name=' + meta['an'], '-c', 'user.email=' + meta['ae'],

               'commit-tree', tree, '-m', cur_meta['body']]

        if parent:

            cmd += ['-p', parent]

        parent = git(args.repo, *cmd, env=env_for(meta))



    backup = f'refs/backup/metadata-{args.branch}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'

    git(args.repo, 'update-ref', backup, head)

    temp_ref = f'refs/heads/restore-metadata-{args.branch}'

    git(args.repo, 'update-ref', temp_ref, parent)

    git(args.repo, 'push', args.remote, f'{temp_ref}:refs/heads/{args.branch}', '--force-with-lease')

    print('NEW_HEAD:', parent)

    print('BACKUP_REF:', backup)

    return 0





if __name__ == '__main__':

    sys.exit(main())

