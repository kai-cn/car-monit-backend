#!/usr/bin/env python3

"""
@description 历史脚本 survey-java-cloud-workflows.py：只读盘点脚本、注释或配置状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python survey-java-cloud-workflows.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：


1. 遍历两仓库 Java 分支，用 contents API 列出 .github/workflows/*.yml。


2. 优先识别 parity-verify-cloud.yml（业务一致性），其次 native-image-cloud.yml


   （native 构建），最后 ci.yml / build.yml 等普通构建。


3. 下载 workflow 文本，粗判是否包含 workflow_dispatch，以及是否声明 platform/repeat 输入。


4. 输出分派计划；不实际 dispatch，避免误触发。





注意：GitHub /actions/workflows 只列出默认分支可见的 workflow；


分派某个分支时仍用同一个 workflow id，只要该分支上存在同名文件即可。
"""
import base64, json, sys, urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'wf-survey'}

REPOS={

 'kai-cn/car-monit-api':['master','car-monit-api-java-V3','car-monit-api-java-fix','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','feature/springboot3','feature/springboot3-jdk17','feature-dbupgrade'],

 'kai-cn/car-monit-backend':['master','car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','feat/backend-full-parity','feature-dbupgrade'],

}

PREF=['parity-verify-cloud.yml','native-image-cloud.yml','ci.yml','build.yml']



def api(u):

    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as r:

        return json.loads(r.read().decode())



for repo,branches in REPOS.items():

    print('===',repo)

    for br in branches:

        try:

            items=api(f'https://api.github.com/repos/{repo}/contents/.github/workflows?ref={br.replace("/","%2F")}')

        except Exception as e:

            print(br,'NO_WORKFLOWS',e); continue

        files=[x['name'] for x in items if x['name'].endswith(('.yml','.yaml'))]

        pick=next((p for p in PREF if p in files), None)

        info=''

        if pick:

            try:

                obj=api(f'https://api.github.com/repos/{repo}/contents/.github/workflows/{pick}?ref={br.replace("/","%2F")}')

                t=base64.b64decode(obj['content']).decode('utf-8','replace')

                tags=[]

                if 'workflow_dispatch:' in t: tags.append('dispatch')

                if 'platform:' in t: tags.append('platform')

                if 'repeat:' in t: tags.append('repeat')

                info='['+','.join(tags)+']'

            except Exception as e:

                info='[read_fail]'

        print(br,'files='+str(len(files)),'pick='+str(pick),info)

