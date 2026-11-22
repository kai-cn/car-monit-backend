#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-oss-native-only.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk-parity-oss.yml')
t = p.read_text(encoding='utf-8')
t = t.replace("  # OSS/S3 is not needed by the 2 parity endpoints; native AWS SDK v1 init is unsupported.\n", '')
t = t.replace("  OSS_ENABLE: 'false'\n", '')
t = t.replace('--cmd "\\"$NATIVE\\" --server.port=19902"',
              '--cmd "env OSS_ENABLE=false \\"$NATIVE\\" --server.port=19902"')
p.write_text(t, encoding='utf-8')
import yaml
yaml.safe_load(t)
print('native-only', 'env OSS_ENABLE=false' in t, 'global OSS' not in t)
