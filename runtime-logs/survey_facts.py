#!/usr/bin/env python3

"""
@description 历史脚本 survey_facts.py：只读盘点脚本、注释或配置状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python survey_facts.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Survey branch facts: Boot version, java version, native workflow presence."""

import subprocess



REPOS = {

    'api': (r'D:\work\IdeaProjects\car-monit-api-java-V3',

            ['car-monit-api-jdk17', 'car-monit-api-jdk21', 'car-monit-api-jdk25',

             'car-monit-api-java-V3', 'master', 'car-monit-api-go-V2',

             'car-monit-api-python', 'car-monit-api-cpp']),

    'backend': (r'D:\work\IdeaProjects\car-monit-backend-java-V3',

                ['car-monit-backend-jdk17', 'car-monit-backend-jdk21', 'car-monit-backend-jdk25',

                 'car-monit-backend-java-V3', 'master', 'car-monit-go-V2',

                 'car-monit-py-V2', 'car-monit-rust-V2', 'car-monit-cpp-local']),

}





def git(repo, *args):

    return subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True,

                          encoding='utf-8', errors='replace')





for name, (repo, branches) in REPOS.items():

    print('=' * 80)

    print('REPO', name)

    for b in branches:

        ref = f'refs/remotes/origin/{b}'

        if git(repo, 'rev-parse', '--verify', ref).returncode != 0:

            print(f'  {b:32s} (no branch)')

            continue

        pom = git(repo, 'show', f'{ref}:pom.xml').stdout

        ver = []

        for line in pom.splitlines():

            if any(k in line for k in ('<spring-boot.version>', '<java.version>', '<maven.compiler')):

                ver.append(line.strip())

        has_wf = git(repo, 'cat-file', '-e', f'{ref}:.github/workflows/native-image-cloud.yml').returncode == 0

        has_native_pom = bool(git(repo, 'grep', '-l', '-I', 'native-maven-plugin', ref, '--', 'pom.xml').stdout.strip())

        # language dirs present

        tree = git(repo, 'ls-tree', '--name-only', ref).stdout

        langs = [d for d in ('car-monit-api-go', 'car-monit-api-python', 'car-monit-api-rust',

                             'car-monit-api-cpp', 'car-monit-api-csharp', 'car-monit-api-kotlin',

                             'car-monit-go', 'car-monit-py', 'car-monit-rust', 'car-monit-cpp',

                             'car-monit-csharp', 'car-monit-kotlin') if d in tree.split()]

        print(f'  {b:32s} {" ; ".join(ver)[:70]:70s} nativewf={has_wf} nativepom={has_native_pom} langs={langs}')

