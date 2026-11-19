#!/usr/bin/env python3
from pathlib import Path
p = Path(r'D:\work\runtime-logs\rust-state-check.rs')
t = p.read_text(encoding='utf-8')
if 'use sqlx::ConnectOptions;' not in t:
    t = t.replace('use sqlx::mysql::MySqlPoolOptions;\n',
                  'use sqlx::mysql::MySqlPoolOptions;\nuse sqlx::ConnectOptions;\n', 1)
needle = '''        let pool = MySqlPoolOptions::new()
'''
probe = '''        // Diagnostic: establish one connection outside the pool so the real
        // driver error is reported instead of only "pool timed out".
        let probe = connect_options
            .connect()
            .await
            .map_err(|e| anyhow::anyhow!("MySQL direct connect failed: {}", e))?;
        drop(probe);

'''
assert needle in t
t = t.replace(needle, probe + needle, 1)
p.write_text(t, encoding='utf-8')
print('probe added', 'MySQL direct connect failed' in t)
