#!/usr/bin/env python3

"""
@description 历史脚本 scan-all-workflows.py：扫描远端或本地状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python scan-all-workflows.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

Uses the fixed-account cached token from gh_cred.py (no account-picker dialogs).


Checks:


  1. YAML parses.


  2. Top-level/job/step keys are valid GitHub Actions keys.


  3. `cache:` is only inside `with:` (a previous pass put it at step level).
"""
import base64

import json

import sys

import urllib.request

from pathlib import Path



sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token  # noqa: E402

import yaml  # noqa: E402



TOKEN = get_token()

HEADERS = {'Authorization': 'Bearer ' + TOKEN,

           'Accept': 'application/vnd.github+json',

           'X-GitHub-Api-Version': '2022-11-28',

           'User-Agent': 'workflow-scan'}



TOP_KEYS = {'name', 'run-name', 'on', True, 'permissions', 'env', 'defaults',

            'concurrency', 'jobs'}

JOB_KEYS = {'name', 'needs', 'permissions', 'if', 'runs-on', 'environment',

            'concurrency', 'outputs', 'env', 'defaults', 'timeout-minutes',

            'continue-on-error', 'container', 'services', 'strategy', 'steps',

            'uses', 'with', 'secrets', 'inherit'}

STEP_KEYS = {'id', 'if', 'name', 'uses', 'run', 'working-directory', 'shell',

             'with', 'env', 'continue-on-error', 'timeout-minutes'}





def api(uri):

    req = urllib.request.Request(uri, headers=HEADERS)

    with urllib.request.urlopen(req, timeout=60) as r:

        return json.loads(r.read().decode('utf-8'))





def branches(repo):

    out = []

    page = 1

    while True:

        data = api(f'https://api.github.com/repos/{repo}/branches?per_page=100&page={page}')

        if not data:

            break

        out += [b['name'] for b in data]

        if len(data) < 100:

            break

        page += 1

    return out





def workflow_paths(repo, branch):

    enc = branch.replace('/', '%2F')

    data = api(f'https://api.github.com/repos/{repo}/contents/.github/workflows?ref={enc}')

    return [item['path'] for item in data if item['path'].endswith(('.yml', '.yaml'))]





def fetch(repo, branch, path):

    enc = branch.replace('/', '%2F')

    data = api(f'https://api.github.com/repos/{repo}/contents/{path}?ref={enc}')

    return base64.b64decode(data['content']).decode('utf-8', errors='replace')





def check(repo, branch, path, text):

    errs = []

    try:

        doc = yaml.safe_load(text)

    except Exception as e:

        return [f'YAML: {e}']

    if not isinstance(doc, dict):

        return ['root is not a mapping']

    for k in doc:

        if k not in TOP_KEYS:

            errs.append(f'unexpected top-level key: {k}')

    jobs = doc.get('jobs')

    if not isinstance(jobs, dict):

        return errs + ['jobs is not a mapping']

    for jname, job in jobs.items():

        if not isinstance(job, dict):

            errs.append(f'job[{jname}] is not a mapping')

            continue

        for k in job:

            if k not in JOB_KEYS:

                errs.append(f'job[{jname}] unexpected key: {k}')

        steps = job.get('steps')

        if isinstance(steps, list):

            for i, step in enumerate(steps):

                if not isinstance(step, dict):

                    errs.append(f'job[{jname}].steps[{i}] is not a mapping')

                    continue

                for k in step:

                    if k not in STEP_KEYS:

                        errs.append(f'job[{jname}].steps[{i}] unexpected key: {k} '

                                    f'(name={step.get("name") or step.get("uses") or step.get("run", "")[:40]})')

    return errs





total = 0

bad = 0

for repo in ('kai-cn/car-monit-api', 'kai-cn/car-monit-backend'):

    bs = branches(repo)

    print(f'REPO {repo}: branches={len(bs)}')

    for br in bs:

        try:

            paths = workflow_paths(repo, br)

        except Exception as e:

            print(f'  LIST_FAIL {br}: {e}')

            continue

        for p in paths:

            total += 1

            try:

                text = fetch(repo, br, p)

            except Exception as e:

                print(f'  FETCH_FAIL {br}/{p}: {e}')

                continue

            errs = check(repo, br, p, text)

            if errs:

                bad += 1

                print(f'BAD {br}/{p}')

                for e in errs[:8]:

                    print('   ', e)

print(f'SCANNED={total} BAD={bad}')

