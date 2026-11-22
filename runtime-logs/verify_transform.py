"""
@description 历史脚本 verify_transform.py：验证配置、构建或安全不变量；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python verify_transform.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import sys
sys.argv = ['x']
exec(open(r'D:\work\runtime-logs\harden_workflows.py', encoding='utf-8').read().split('def main()')[0])
import yaml
tests = [
    ('api', '.github/workflows/native-image.yml', 'origin/car-monit-api-jdk17'),
    ('api', '.github/workflows/native-image-cloud.yml', 'origin/car-monit-api-jdk17'),
    ('api', '.github/workflows/deploy-selfhosted.yml', 'origin/master'),
    ('api', '.github/workflows/selfhost-canary.yml', 'origin/master'),
    ('api', '.github/workflows/self-hosted-ci.yml', 'origin/car-monit-api-jdk17'),
    ('api', '.github/workflows/_cpp.yml', 'origin/car-monit-api-jdk17'),
    ('backend', '.github/workflows/native-image.yml', 'origin/car-monit-backend-jdk21'),
    ('backend', '.github/workflows/self-hosted-ci.yml', 'origin/car-monit-backend-jdk21'),
]
all_ok = True
for rn, f, br in tests:
    repo = REPOS[rn]
    c = show(repo, br, f)
    new, ch = apply_rules(f, c)
    try:
        yaml.safe_load(new)
        y = 'OK'
    except Exception as e:
        y = 'FAIL ' + str(e)[:90]
        all_ok = False
    guards = new.count('github.repository_owner')
    print('%-52s changed=%s YAML=%s guards=%d' % (f, ch, y, guards))
print('ALL_OK' if all_ok else 'HAS_FAIL')
