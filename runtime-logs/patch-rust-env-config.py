#!/usr/bin/env python3

"""
@description 历史脚本 patch-rust-env-config.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-rust-env-config.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')

t = p.read_text(encoding='utf-8')

needle = '''        env:

          RUST_LOG: "sqlx::pool=trace,car_monit_rust=info"

          RUST_BACKTRACE: '1'

'''

add = needle + '''          APP_DATABASE__URL: "jdbc:mysql://127.0.0.1:3306/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8"

          APP_DATABASE__USERNAME: root

          APP_DATABASE__PASSWORD: root

          APP_DATABASE__POOL__MINIDLE: '0'

          APP_DATABASE__POOL__MAXACTIVE: '10'

          APP_DATABASE__POOL__MAXWAIT: '30000'

          APP_REDIS__HOST: 127.0.0.1

          APP_REDIS__PORT: '6379'

'''

assert needle in t

p.write_text(t.replace(needle, add, 1), encoding='utf-8')

import yaml

yaml.safe_load(p.read_text(encoding='utf-8'))

print('env added', 'APP_DATABASE__URL' in t)

