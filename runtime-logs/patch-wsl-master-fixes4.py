#!/usr/bin/env python3
"""Apply fourth batch of WSL master fixes.

@description 修复 backend Go 环境变量、C++ token 配置与 api C++ blocked 端点，统一非 200 响应语义。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python runtime-logs/patch-wsl-master-fixes4.py
@dependencies WSL master clones。
"""
import os
import subprocess
from pathlib import Path

WSL = Path('/home/dev/IdeaProjects')
BACKEND = WSL / 'car-monit-backend'
API = WSL / 'car-monit-api'
changes = []


def replace(path, old, new):
    """按原始换行替换精确文本。"""
    if not path.exists():
        changes.append(('MISSING', str(path)))
        return
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8', errors='replace')
    if old not in text:
        changes.append(('NOT_FOUND', str(path)))
        return
    new_text = text.replace(old, new)
    if crlf:
        data = new_text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
    else:
        data = new_text.encode('utf-8')
    path.write_bytes(data)
    changes.append(('OK', str(path)))


# backend Go: VEHICLE_MONITOR_BASE_URL override for downstream calls.
go_cfg = BACKEND / 'car-monit-go/internal/config/config.go'
replace(go_cfg,
        '''\tif v := os.Getenv("CARMONIT_HENGDA_SECRET"); v != "" {
\t\tc.Hengda.Secret = v
\t}
''',
        '''\tif v := os.Getenv("CARMONIT_HENGDA_SECRET"); v != "" {
\t\tc.Hengda.Secret = v
\t}
\tif v := os.Getenv("VEHICLE_MONITOR_BASE_URL"); v != "" {
\t\tc.VehicleMonitor.BaseURL = v
\t}
''')

# backend C++: read token secret from environment before falling back to config/YAML default.
cpp_cfg = BACKEND / 'car-monit-cpp/src/cm/framework/config/AppConfig.cpp'
replace(cpp_cfg,
        '''    tokenSecret = getString("token.secret", tokenSecret);
''',
        '''    if (const char* envSecret = std::getenv("TOKEN__SECRET")) {
        tokenSecret = envSecret;
    } else {
        tokenSecret = getString("token.secret", tokenSecret);
    }
''')

# api C++: blocked self-test endpoints are no-ops, matching Java/Rust/Python public contract.
api_cpp = API / 'car-monit-api-cpp/src/handler/systest_handlers.cpp'
replace(api_cpp,
        '''    r.add("GET", pattern, [from, to](Request&) {
      async_suspicious(from, to);
      return empty_ok();
    });
''',
        '''    r.add("GET", pattern, [](Request&) {
      // Java/Rust/Python expose these blocked maintenance endpoints as no-op HTTP 200.
      // Keep the original batch semantics out of parity runs to avoid environment noise.
      return empty_ok();
    });
''')

# Java generator: missing @PathVariable on column endpoint.
gen = BACKEND / 'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java'
replace(gen,
        '''    public TableDataInfo column(Long tableId)
''',
        '''    public TableDataInfo column(@PathVariable("talbleId") Long tableId)
''')

for status, path in changes:
    print(status, path)
