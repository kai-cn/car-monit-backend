#!/usr/bin/env python3

"""
@description 历史脚本 survey_boot.py：只读盘点脚本、注释或配置状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python survey_boot.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Survey spring-boot version + native profile + language endpoint coverage."""

import subprocess, re



REPOS = {

    'api': (r'D:\work\IdeaProjects\car-monit-api-java-V3',

            ['car-monit-api-jdk17', 'car-monit-api-jdk21', 'car-monit-api-jdk25', 'master']),

    'backend': (r'D:\work\IdeaProjects\car-monit-backend-java-V3',

                ['car-monit-backend-jdk17', 'car-monit-backend-jdk21', 'car-monit-backend-jdk25', 'master']),

}





def git(repo, *args, input=None):

    return subprocess.run(['git', '-C', repo, *args], input=input, capture_output=True, text=True,

                          encoding='utf-8', errors='replace')





for name, (repo, branches) in REPOS.items():

    print('=' * 70)

    print('REPO', name)

    for b in branches:

        ref = f'refs/remotes/origin/{b}'

        pom = git(repo, 'show', f'{ref}:pom.xml').stdout

        # find spring-boot parent or version

        sb = re.search(r'<spring-boot[^>]*version>([^<]+)<', pom)

        parent_sb = re.search(r'spring-boot-starter-parent', pom)

        native_profile = git(repo, 'show', f'{ref}:pro-business-api/pom.xml').stdout if name == 'api' \
            else git(repo, 'show', f'{ref}:ruoyi-admin/pom.xml').stdout

        has_native_profile = '<id>native</id>' in native_profile or 'native-maven-plugin' in native_profile

        print(f'  {b:30s} spring-boot={"YES("+sb.group(1)+")" if sb else ("parent" if parent_sb else "?")} nativeProfile={has_native_profile}')

