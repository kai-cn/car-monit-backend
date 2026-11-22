#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-rust-env-config.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
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
