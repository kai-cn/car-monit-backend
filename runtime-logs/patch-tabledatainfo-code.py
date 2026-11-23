#!/usr/bin/env python3
"""Align TableDataInfo success code with body.code criterion.

@description 将 TableDataInfo 默认 code 改为 200，使分页接口在 body.code 判据下计为成功。
@author Tencent Hunyuan Hy
@date 2026-11-23 08:10:00
@usage python3 runtime-logs/patch-tabledatainfo-code.py
@dependencies WSL backend master。
"""
from pathlib import Path

p = Path('/home/dev/IdeaProjects/car-monit-backend/ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java')
raw = p.read_bytes()
crlf = b'\r\n' in raw
t = raw.decode('utf-8', errors='replace')
old = "    /** 消息状态码 */\r\n    private int code;" if crlf else "    /** 消息状态码 */\n    private int code;"
new = "    /** 消息状态码：统一成功口径为 200 */\r\n    private int code = 200;" if crlf else "    /** 消息状态码：统一成功口径为 200 */\n    private int code = 200;"
if old not in t:
    raise SystemExit('NOT_FOUND')
t = t.replace(old, new)
p.write_bytes(t.encode('utf-8'))
print('OK', p)
