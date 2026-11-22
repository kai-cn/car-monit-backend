#!/usr/bin/env python3

"""
@description 历史脚本 dedupe-redis-starter.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python dedupe-redis-starter.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

思路：迁移前 pro-base-common 已有带 exclusions 的 Redis starter；替换 Jedis


依赖块后又新增了一个裸 starter，形成重复声明。本脚本只删除最后一个裸块，


保留原有带 exclusions 的版本，避免改变既有排除规则。





风险：若某分支的两个 starter 都是有意保留（不同 exclusions），本脚本会误删；


当前检查条件是 starter 出现两次且存在精确匹配的裸依赖块，实测 9 个 api 分支均成立。
"""
import base64, json, sys, urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'dedup-redis'}

REPO='kai-cn/car-monit-api'

BRANCHES=['master','car-monit-api-java-V3','car-monit-api-java-fix','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','feature/springboot3','feature/springboot3-jdk17','feature-dbupgrade']

PATH='pro-base-common/pom.xml'

ART='<artifactId>spring-boot-starter-data-redis</artifactId>'

DEP='''        <dependency>

            <groupId>org.springframework.boot</groupId>

            <artifactId>spring-boot-starter-data-redis</artifactId>

        </dependency>

'''



def api(u,method='GET',body=None):

    data=json.dumps(body).encode() if body is not None else None

    with urllib.request.urlopen(urllib.request.Request(u,data=data,headers=H,method=method),timeout=60) as r:

        return json.loads(r.read().decode())



for br in BRANCHES:

    obj=api(f'https://api.github.com/repos/{REPO}/contents/{PATH}?ref={br.replace("/","%2F")}')

    t=base64.b64decode(obj['content']).decode()

    if t.count(ART)<2 or DEP not in t:

        print(br,'skip',t.count(ART)); continue

    # remove the last duplicate bare starter block

    idx=t.rfind(DEP)

    n=t[:idx]+t[idx+len(DEP):]

    api(f'https://api.github.com/repos/{REPO}/contents/{PATH}','PUT',{

        'message':'build(pom): remove duplicate Redis starter dependency',

        'content':base64.b64encode(n.encode()).decode(),'sha':obj['sha'],'branch':br})

    print(br,'deduped',t.count(ART),'->',n.count(ART))

