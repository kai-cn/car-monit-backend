#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：fix-h8-enable-config.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""H8 follow-up: enable MyBatisConfig bean and skip resource-based alias scanning."""
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
