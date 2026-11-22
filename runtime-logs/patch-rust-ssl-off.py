#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-rust-ssl-off.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\rust-state.rs')
t = p.read_text(encoding='utf-8')
needle = '''        url.set_password(Some(&settings.database.password))
            .map_err(|_| anyhow::anyhow!("database.password 非法"))?;
'''
add = needle + '''
        // Cloud MySQL uses useSSL=false; sqlx defaults to ssl-mode=PREFERRED,
        // which can hang during TLS negotiation and surface as a pool timeout.
        if settings.database.url.contains("useSSL=false") {
            url.query_pairs_mut().append_pair("ssl-mode", "disabled");
        }
'''
assert needle in t
p.write_text(t.replace(needle, add, 1), encoding='utf-8')
print('patched', 'ssl-mode' in t)
