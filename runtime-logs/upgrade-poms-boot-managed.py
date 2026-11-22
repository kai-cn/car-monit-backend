#!/usr/bin/env python3

"""
@description 历史脚本 upgrade-poms-boot-managed.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python upgrade-poms-boot-managed.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：


1. Boot2 最终版固定为 2.7.18；api master/java-V3/java-fix 的 parent 从


   2.4.5 升到 2.7.18，backend master/java-V3 的 BOM 从 2.5.15 升到 2.7.18。


2. 移除 backend 中与 Boot BOM 重复的 spring-framework-bom 与显式 spring 版本，


   避免多个 BOM 争夺版本控制权。


3. 对所有 Java POM，仅删除 Boot 已管理依赖的显式版本（starter、spring-*、


   mysql connector、spring-kafka 等）；非 Boot 管理依赖保留原版本。


4. 斜杠分支使用未编码的 git ref 路径，contents API 的 ref 查询才用 URL 编码。





风险：若某分支实际使用 Boot 未管理的同名 artifact，删版本会导致构建失败；


因此只处理白名单中的 groupId:artifactId，不做全量版本删除。
"""
import base64, json, re, sys, urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token



H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',

   'X-GitHub-Api-Version':'2022-11-28','User-Agent':'boot-bom-refactor'}

REPOS={

 'kai-cn/car-monit-api':{

   'boot2':['master','car-monit-api-java-V3','car-monit-api-java-fix'],

   'all':['master','car-monit-api-java-V3','car-monit-api-java-fix','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','feature/springboot3','feature/springboot3-jdk17','feature-dbupgrade'],

 },

 'kai-cn/car-monit-backend':{

   'boot2':['master','car-monit-backend-java-V3'],

   'all':['master','car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','feat/backend-full-parity','feature-dbupgrade'],

 },

}

BOOT2='2.7.18'

MANAGED={

 ('org.springframework.boot','spring-boot-starter-amqp'),

 ('org.springframework.boot','spring-boot-starter-data-redis'),

 ('org.springframework.kafka','spring-kafka'),

 ('org.springframework','spring-core'),('org.springframework','spring-web'),

 ('org.springframework','spring-context'),('org.springframework','spring-beans'),

 ('mysql','mysql-connector-java'),('com.mysql','mysql-connector-j'),

}



def api(u, method='GET', body=None):

    data=json.dumps(body).encode() if body is not None else None

    req=urllib.request.Request(u,data=data,headers=H,method=method)

    with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())



def put(repo,br,path,text,sha,msg):

    api(f'https://api.github.com/repos/{repo}/contents/{path}','PUT',{

        'message':msg,'content':base64.b64encode(text.encode()).decode(),'sha':sha,'branch':br})



def pom_paths(repo,br):

    ref=api(f'https://api.github.com/repos/{repo}/git/ref/heads/{br}')['object']['sha']

    tree=api(f'https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1')

    return [x['path'] for x in tree.get('tree',[]) if x['path'].endswith('pom.xml')]



def strip_managed_versions(text):

    pattern=re.compile(r'(<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>)([\s\S]*?)(</dependency>)',re.S)

    def repl(m):

        g,a=m.group(2),m.group(3)

        if (g,a) in MANAGED and a!='spring-boot-dependencies':

            body=re.sub(r'\s*<version>[^<]*</version>','',m.group(4))

            return m.group(1)+body+m.group(5)

        return m.group(0)

    return pattern.sub(repl,text)



for repo,cfg in REPOS.items():

    print('===',repo)

    for br in cfg['all']:

        try: paths=pom_paths(repo,br)

        except Exception as e:

            print(br,'ERROR',e); continue

        changed=[]

        for path in paths:

            try:

                obj=api(f'https://api.github.com/repos/{repo}/contents/{path}?ref={br.replace("/","%2F")}')

            except Exception:

                continue

            t=base64.b64decode(obj['content']).decode('utf-8')

            n=t

            if path=='pom.xml' and br in cfg['boot2']:

                n=n.replace('<artifactId>spring-boot-starter-parent</artifactId>\n        <version>2.4.5</version>',

                            f'<artifactId>spring-boot-starter-parent</artifactId>\n        <version>{BOOT2}</version>')

                if repo.endswith('backend'):

                    n=re.sub(r'<version>2\.5\.15</version>',f'<version>{BOOT2}</version>',n)

                    n=re.sub(r'\s*<spring-framework\.version>[^<]*</spring-framework\.version>','',n)

                    n=re.sub(r'<dependency>\s*<groupId>org\.springframework</groupId>\s*<artifactId>spring-framework-bom</artifactId>[\s\S]*?</dependency>','',n,count=1)

            n=strip_managed_versions(n)

            if n!=t:

                put(repo,br,path,n,obj['sha'],'build(pom): align dependencies with Spring Boot BOM')

                changed.append(path)

        print(br,','.join(changed) if changed else 'none')

