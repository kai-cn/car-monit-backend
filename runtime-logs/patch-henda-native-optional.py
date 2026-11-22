#!/usr/bin/env python3

"""
@description 历史脚本 patch-henda-native-optional.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-henda-native-optional.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

