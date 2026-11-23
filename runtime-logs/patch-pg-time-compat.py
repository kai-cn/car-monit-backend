#!/usr/bin/env python3
"""Patch PostgreSQL-compatible time interval SQL in api master.

@description 将 now()-180/now()-3 改为 PostgreSQL interval 写法，保留 MySQL 语义并支持本地 PG 下游。
@author Tencent Hunyuan Hy
@date 2026-11-23 08:32:28
@usage python3 runtime-logs/patch-pg-time-compat.py
@dependencies WSL api master。
"""
from pathlib import Path

A = Path('/home/dev/IdeaProjects/car-monit-api')
paths = [
    A / 'pro-business-api/src/main/java/com/ruoyi/base/mapper/xml/ZdataTrailTracksMapper.xml',
    A / 'car-monit-api-python/pro-business-api/src/main/resources/com/ruoyi/base/mapper/xml/ZdataTrailTracksMapper.xml',
]


def replace(path, old, new):
    """Replace exact SQL text while preserving line endings."""
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    t = raw.decode('utf-8', errors='replace')
    if old not in t:
        print('NOT_FOUND', path, old)
        return
    t = t.replace(old, new)
    data = (t.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else t).encode('utf-8')
    path.write_bytes(data)
    print('OK', path)


for p in paths:
    replace(p, 'now() - 180', "now() - interval '180 days'")
    replace(p, 'now() - 3', "now() - interval '3 days'")

for p in [A / 'car-monit-api-go/internal/repo/zdata_trail_tracks.go',
          A / 'car-monit-api-cpp/src/service/track.cpp']:
    replace(p, 'now() - 180', "now() - interval '180 days'")
    replace(p, 'now() - 3', "now() - interval '3 days'")
    replace(p, 'now()-180', "now()-interval '180 days'")
    replace(p, 'now()-3', "now()-interval '3 days'")
