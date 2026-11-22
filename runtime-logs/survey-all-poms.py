#!/usr/bin/env python3

"""
@description 历史脚本 survey-all-poms.py：只读盘点脚本、注释或配置状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python survey-all-poms.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：


1. 用 git ref API 取分支 HEAD，再用 recursive tree API 列出全部 pom.xml。


2. 逐个读取 POM，提取 parent/BOM 的 Spring Boot 版本。


3. 只汇报与本次升级相关的显式版本（Boot starter、spring-*、mysql、kafka、


   Redis 客户端）以及是否出现 jedis/lettuce。


4. 脚本只读，不对远端做任何写操作；用于确认改造范围与幂等性。





注意：旧脚本曾把带斜杠分支名 URL-encode 后传给 git ref 路径导致 404；


若复用本脚本，保持 git ref 路径未编码、contents 查询参数编码。
"""
import base64, json, re, sys, urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'pom-full-survey'}

BRANCHES={

 'kai-cn/car-monit-api':['master','car-monit-api-java-V3','car-monit-api-java-fix','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','feature/springboot3','feature/springboot3-jdk17','feature-dbupgrade'],

 'kai-cn/car-monit-backend':['master','car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','feat/backend-full-parity','feature-dbupgrade'],

}



def api(u):

    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as r:

        return json.loads(r.read())



def branch_sha(repo,br):

    d=api(f'https://api.github.com/repos/{repo}/git/ref/heads/{br.replace("/","%2F")}')

    return d['object']['sha']



def poms(repo,br):

    sha=branch_sha(repo,br)

    t=api(f'https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1')

    return [x['path'] for x in t.get('tree',[]) if x['path'].endswith('pom.xml')]



def get_file(repo,br,path):

    d=api(f'https://api.github.com/repos/{repo}/contents/{path}?ref={br.replace("/","%2F")}')

    return base64.b64decode(d['content']).decode('utf-8','replace')



def summarize(text):

    lines=[]

    parent=re.search(r'<parent>[\s\S]{0,600}?<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([^<]+)',text)

    bom=re.search(r'<artifactId>spring-boot-dependencies</artifactId>\s*<version>([^<]+)',text)

    lines.append('boot_parent='+(parent.group(1) if parent else '-')+' boot_bom='+(bom.group(1) if bom else '-'))

    for m in re.finditer(r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>',text):

        g,a,v=m.groups()

        if g in {'org.springframework.boot','org.springframework','mysql','org.apache.kafka','redis.clients','io.lettuce','commons-io'} or 'redis' in a.lower() or 'jedis' in a.lower():

            lines.append(f'{g}:{a}={v}')

    return lines



for repo,branches in BRANCHES.items():

    print('===',repo)

    for br in branches:

        try: ps=poms(repo,br)

        except Exception as e:

            print(br,'ERROR',e); continue

        print(br,'poms='+str(len(ps)))

        for p in ps:

            try: t=get_file(repo,br,p)

            except Exception as e:

                print('  ',p,'FETCH_FAIL',e); continue

            s=summarize(t)

            if len(s)>1 or 'jedis' in t.lower() or 'lettuce' in t.lower():

                print('  ',p)

                for x in s: print('     ',x)

                if 'jedis' in t.lower(): print('      JEDIS_REFERENCES')

                if 'lettuce' in t.lower(): print('      LETTUCE_REFERENCES')

