#!/usr/bin/env python3

"""
@description 历史脚本 local-rerun-final.py：执行本机复测或打包；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python local-rerun-final.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- regenerate JUnit sources from both endpoint inventories


- compile them with Java 8 target to prove the harness remains portable


- parse all touched workflow YAML files


- check script annotations and collect cloud run status


- write a local evidence JSON/MD report





This does not start services; it verifies local reproducibility of the code and


scripts used by the completed cloud runs.
"""
import json

import subprocess

import sys

from pathlib import Path

import yaml



BASE = Path(r'D:\work\runtime-logs')

GEN = BASE / 'generate_junit_suite.py'

JUNIT_JAR = BASE / 'junit-platform-console-standalone.jar'

CHECK = BASE / 'local-rerun-check'

OUT = BASE / 'local-rerun-evidence'

SURVEY = BASE / 'survey-script-comments.py'





def run(args):

    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')

    return r.returncode, (r.stdout or '') + (r.stderr or '')





def main():

    OUT.mkdir(exist_ok=True)

    results = {}

    for app, endpoints in [

        ('api', BASE / 'api-endpoints-full.txt'),

        ('backend', Path(r'D:\work\IdeaProjects\car-monit-backend-new\scripts\v3\ops\parity\endpoints\backend-full.txt')),

    ]:

        d = CHECK / app

        d.mkdir(parents=True, exist_ok=True)

        rc, txt = run([sys.executable, str(GEN), '--endpoints', str(endpoints), '--out', str(d / 'generated')])

        classes = d / 'classes'

        classes.mkdir(exist_ok=True)

        srcs = [str(p) for p in (d / 'generated').glob('*.java')]

        rc2, txt2 = run(['javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8',

                         '-cp', str(JUNIT_JAR), '-d', str(classes)] + srcs)

        results[app] = {'generate_rc': rc, 'compile_rc': rc2, 'generate': txt.strip(), 'compile': txt2.strip()}



    workflows = [

        r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml',

        r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml',

        r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml',

        r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml',

    ]

    results['workflow_yaml'] = {p: 'OK' if yaml.safe_load(Path(p).read_text(encoding='utf-8')) else 'EMPTY' for p in workflows}



    rc, txt = run([sys.executable, str(SURVEY)])

    results['script_comments'] = {'rc': rc, 'output': txt.strip()}



    for name in ['java-junit-results.json', 'crosslang-full-results.json', 'native-crosslang-status.json', 'java-upgrade-runs.json']:

        p = BASE / name

        if p.exists():

            d = json.loads(p.read_text(encoding='utf-8'))

            if isinstance(d, list):

                results[name] = {'total': len(d), 'success': sum(1 for x in d if x.get('conclusion') == 'success')}

            elif isinstance(d, dict):

                results[name] = d



    (OUT / 'local-rerun-evidence.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = ['# Local final rerun evidence', '',

             '| check | result |', '| --- | --- |']

    for app in ('api', 'backend'):

        lines.append(f"| {app} JUnit generate/compile | {results[app]['generate_rc']}/{results[app]['compile_rc']} |")

    lines.append(f"| workflow YAML | {sum(1 for v in results['workflow_yaml'].values() if v=='OK')}/{len(workflows)} OK |")

    lines.append(f"| script comments | {results['script_comments']['output'].splitlines()[0]} |")

    for name in ['java-junit-results.json', 'crosslang-full-results.json', 'native-crosslang-status.json', 'java-upgrade-runs.json']:

        if name in results:

            v = results[name]

            lines.append(f"| {name} | total={v.get('total')} success={v.get('success')} |")

    (OUT / 'local-rerun-evidence.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('\n'.join(lines))





if __name__ == '__main__':

    main()

