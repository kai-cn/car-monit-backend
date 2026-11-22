#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：fix-go-line-endings.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""把 Go 测试文件统一为 LF；gofmt -l 会把 CRLF 视为未格式化。"""
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3\car-monit-go\internal\modules\quartz\tasks_test.go')
data = p.read_bytes().replace(b'\r\n', b'\n')
p.write_bytes(data)
print('LF_ONLY', b'\r\n' not in p.read_bytes())
