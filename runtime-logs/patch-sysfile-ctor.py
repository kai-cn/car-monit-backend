#!/usr/bin/env python3
"""
@description 历史脚本 patch-sysfile-ctor.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-sysfile-ctor.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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
