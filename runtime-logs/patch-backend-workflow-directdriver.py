#!/usr/bin/env python3

"""
@description 历史脚本 patch-backend-workflow-directdriver.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-backend-workflow-directdriver.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

from pathlib import Path

p = Path(r'D:\work\runtime-logs\remote-parity-bk25.yml')

t = p.read_text(encoding='utf-8')

t = t.replace('jdbc:p6spy:mysql://127.0.0.1:3306/carmonitdb', 'jdbc:mysql://127.0.0.1:3306/carmonitdb')

needle = '          SPRING__DATASOURCE__DRUID__MASTER__PASSWORD: root\n'

add = needle + '          SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME: com.mysql.cj.jdbc.Driver\n'

t = t.replace(needle, add)

p.write_text(t, encoding='utf-8')

print('patched workflow', t.count('com.mysql.cj.jdbc.Driver'))

