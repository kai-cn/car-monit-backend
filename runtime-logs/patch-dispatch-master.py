#!/usr/bin/env python3
"""
@description 将跨语言派发脚本的基线分支与凭据读取路径切换到合并后的 backend master runtime-logs。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/patch-dispatch-master.py
@dependencies Python 3 标准库。
"""
import re
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs\dispatch-crosslang-full.py')
t = p.read_text(encoding='utf-8')
t = t.replace(r"sys.path.insert(0, r'D:\work\runtime-logs')",
              r"sys.path.insert(0, r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')")
t = re.sub(r"\('kai-cn/car-monit-backend',\s*'[^']+',\s*'backend'\)",
           "('kai-cn/car-monit-backend', 'master', 'backend')", t)
t = re.sub(r"\('kai-cn/car-monit-api',\s*'[^']+',\s*'api'\)",
           "('kai-cn/car-monit-api', 'master', 'api')", t)
t = t.replace("f'{app}-java25-crosslang-full'", "f'{app}-java-master-crosslang-full'")
p.write_text(t, encoding='utf-8')
print('PATCHED_DISPATCH_MASTER')
