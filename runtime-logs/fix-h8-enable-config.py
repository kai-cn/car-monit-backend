#!/usr/bin/env python3

"""
@description 历史脚本 fix-h8-enable-config.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python fix-h8-enable-config.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\MyBatisConfig-remote-check.java')

t = p.read_text(encoding='utf-8')

t = t.replace('//@Configuration //mybatisplus 生效后不需要再配置mybatis',

              '@Configuration // H8: native needs explicit alias registration here')

t = t.replace('        typeAliasesPackage = setTypeAliasesPackage(typeAliasesPackage);',

              '        // H8: package scanning uses **/*.class resources, unavailable in native images.\n'

              '        // Explicit Class[] aliases below replace it for both JVM and native.\n'

              '        // typeAliasesPackage = setTypeAliasesPackage(typeAliasesPackage);')

p.write_text(t, encoding='utf-8')

print('enabled', '@Configuration // H8' in t, 'scan skipped', '// typeAliasesPackage = setTypeAliasesPackage' in t)

