#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-henda-native-optional.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\HenDaServiceImpl.java')
t = p.read_text(encoding='utf-8')
t = t.replace('''    @Autowired
    private IHenDaApi henDaApi;
''', '''    // Forest dynamic proxy is unavailable in native images; keep the JVM path unchanged
    // but allow native startup when the proxy bean cannot be created.
    @Autowired(required = false)
    private IHenDaApi henDaApi;
''', 1)
needle = '''    public JSONObject getPileToLonLat(String roadCode, String pile, String direction) {
        try {
'''
replacement = '''    public JSONObject getPileToLonLat(String roadCode, String pile, String direction) {
        if (henDaApi == null) {
            // Native image limitation: Forest client not injected. Return null just like
            // the existing error path so callers already tolerate a missing coordinate.
            return null;
        }
        try {
'''
assert needle in t
t = t.replace(needle, replacement, 1)
p.write_text(t, encoding='utf-8')
print('patched', '@Autowired(required = false)' in t, 'henDaApi == null' in t)
