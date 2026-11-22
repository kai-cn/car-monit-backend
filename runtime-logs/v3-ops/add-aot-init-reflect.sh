#!/usr/bin/env bash
# @description 历史脚本 add-aot-init-reflect.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash add-aot-init-reflect.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
import json
from pathlib import Path
root=Path('/home/dev/IdeaProjects')
entries=[
 {'name':'com.ruoyi.RuoYiApplication__ApplicationContextInitializer','allDeclaredMethods':True,'allDeclaredConstructors':True},
 {'name':'com.ruoyi.RuoYiApplication__BeanFactoryRegistrations','allDeclaredMethods':True,'allDeclaredConstructors':True},
]
for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):
    p=root/repo/'ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json'
    data=json.loads(p.read_text(encoding='utf-8')); existing={e['name'] for e in data}
    for e in entries:
        if e['name'] not in existing: data.append(e)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PATCHED',p)
PY
