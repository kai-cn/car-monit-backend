#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-sysfile-ctor.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\SysFileServiceImpl.java')
t = p.read_text(encoding='utf-8')
t = t.replace('@AllArgsConstructor\n', '')
t = t.replace('import lombok.AllArgsConstructor;\n', '')
t = t.replace('    private final OssProperties ossProperties;\n',
              '    @Autowired\n    private final OssProperties ossProperties;\n', 1)
t = t.replace('    private final OssTemplate ossTemplate;\n',
              '    @Autowired\n    private final OssTemplate ossTemplate;\n', 1)
p.write_text(t, encoding='utf-8')
print('patched', '@AllArgsConstructor' not in t, t.count('@Autowired'))
