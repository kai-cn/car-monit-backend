#!/usr/bin/env python3
"""在本地临时工作树中补充 POM 说明注释，然后提交并推送到原分支。

思路：
1. 工作树已由 create-pom-upgrade-worktrees.ps1 从最新远端创建，避免影响用户现有工作树。
2. 根 POM 增加一条注释：Spring Boot BOM 是受管依赖的唯一版本来源，显式版本只保留第三方依赖。
3. api 的 pro-base-common 增加一条注释：Redis starter 使用 Lettuce，Jedis 已移除。
4. 每个工作树单独 commit + push HEAD:<branch>；重复执行时若没有新增注释则跳过，不会制造空提交。

风险：push 使用 HTTPS 凭据；为避免卡住，设置 GIT_TERMINAL_PROMPT=0 并给每次 push 设超时。
推送失败会打印错误，不自动 force push，不覆盖远端历史。
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(r'D:\work\IdeaProjects\_pom-upgrade')
REPO_API = r'D:\work\IdeaProjects\car-monit-api'
REPO_BK = r'D:\work\IdeaProjects\car-monit-backend-new'
ROOT_COMMENT = ('    <!-- Spring Boot BOM is the single source of truth for managed dependency versions.\n'
                '         Explicit versions are kept only for dependencies not managed by the BOM. -->\n')
REDIS_COMMENT = ('        <!-- Redis client: spring-boot-starter-data-redis uses Lettuce by default;\n'
                 '             Jedis and its direct JedisCluster usage have been removed. -->\n')
BRANCHES = {
    'api__master': ('master', REPO_API),
    'api__car-monit-api-java-V3': ('car-monit-api-java-V3', REPO_API),
    'api__car-monit-api-java-fix': ('car-monit-api-java-fix', REPO_API),
    'api__car-monit-api-jdk17': ('car-monit-api-jdk17', REPO_API),
    'api__car-monit-api-jdk21': ('car-monit-api-jdk21', REPO_API),
    'api__car-monit-api-jdk25': ('car-monit-api-jdk25', REPO_API),
    'api__feature_springboot3': ('feature/springboot3', REPO_API),
    'api__feature_springboot3-jdk17': ('feature/springboot3-jdk17', REPO_API),
    'api__feature-dbupgrade': ('feature-dbupgrade', REPO_API),
    'bk__master': ('master', REPO_BK),
    'bk__car-monit-backend-java-V3': ('car-monit-backend-java-V3', REPO_BK),
    'bk__car-monit-backend-jdk17': ('car-monit-backend-jdk17', REPO_BK),
    'bk__car-monit-backend-jdk21': ('car-monit-backend-jdk21', REPO_BK),
    'bk__car-monit-backend-jdk25': ('car-monit-backend-jdk25', REPO_BK),
    'bk__feat_backend-full-parity': ('feat/backend-full-parity', REPO_BK),
    'bk__feature-dbupgrade': ('feature-dbupgrade', REPO_BK),
}
ENV = dict(os.environ, GIT_TERMINAL_PROMPT='0')


def git(workdir, *args, timeout=180):
    r = subprocess.run(['git', '-C', str(workdir), *args], capture_output=True,
                       text=True, encoding='utf-8', errors='replace', env=ENV, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()


def insert_after(text, marker, block):
    if block.strip() in text:
        return text
    i = text.find(marker)
    if i < 0:
        return text
    i += len(marker)
    return text[:i] + '\n' + block + text[i:]


for name, (branch, _) in BRANCHES.items():
    wd = ROOT / name
    if not wd.exists():
        print('MISSING', name)
        continue
    changed = False
    root_pom = wd / 'pom.xml'
    if root_pom.exists():
        t = root_pom.read_text(encoding='utf-8')
        n = insert_after(t, '<properties>', ROOT_COMMENT)
        if n != t:
            root_pom.write_text(n, encoding='utf-8')
            changed = True
    if name.startswith('api__'):
        redis_pom = wd / 'pro-base-common' / 'pom.xml'
        if redis_pom.exists():
            t = redis_pom.read_text(encoding='utf-8')
            marker = '<artifactId>spring-boot-starter-data-redis</artifactId>'
            if marker in t and REDIS_COMMENT.strip() not in t:
                n = t.replace(marker, REDIS_COMMENT + marker, 1)
                redis_pom.write_text(n, encoding='utf-8')
                changed = True
    if not changed:
        print('SKIP', branch, 'no new comments')
        continue
    git(wd, 'add', '-A')
    git(wd, 'commit', '-m', 'docs(pom): document Boot BOM and Lettuce migration')
    out = git(wd, 'push', 'origin', f'HEAD:{branch}', timeout=240)
    print('PUSHED', branch, out.replace('\n', ' ')[:160])
