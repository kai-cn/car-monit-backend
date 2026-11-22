#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：survey-java-poms.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
import base64, json, re, sys, urllib.request
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'pom-survey'}
BRANCHES={
 'kai-cn/car-monit-api':['master','main','car-monit-api-java-V3','car-monit-api-java-fix','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','feature/springboot3','feature/springboot3-jdk17','feature-dbupgrade'],
 'kai-cn/car-monit-backend':['master','main','car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','feat/backend-full-parity','feature-dbupgrade'],
}
for repo,branches in BRANCHES.items():
    print('===',repo)
    for br in branches:
        enc=br.replace('/','%2F')
        u=f'https://api.github.com/repos/{repo}/contents/pom.xml?ref={enc}'
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as r:
                obj=json.loads(r.read())
            t=base64.b64decode(obj['content']).decode('utf-8','replace')
        except Exception as e:
            print(br,'NO_POM',e)
            continue
        boot=re.findall(r'<spring-boot\.version>([^<]+)',t)
        parent=re.findall(r'<parent>[\s\S]{0,400}?<artifactId>([^<]+)',t)[:1]
        jedis='jedis' in t
        lettuce='lettuce' in t
        print(br,'boot='+(boot[0] if boot else '-'),'parent='+(parent[0] if parent else '-'),'jedis='+str(jedis),'lettuce='+str(lettuce))
