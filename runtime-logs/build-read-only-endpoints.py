#!/usr/bin/env python3
"""
@description 从真实主键端点清单中筛选只读列表、分页与主键详情接口，排除导出/同步/写操作。
@author Tencent Hunyuan Hy
@date 2026-11-24 22:10:00
@usage python3 runtime-logs/build-read-only-endpoints.py
@dependencies runtime-logs/real-key-endpoints 下已生成的端点清单。
"""
import re
from pathlib import Path

BASE = Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs/real-key-endpoints')

# 导出、下载、同步、状态、写操作不是“读取类接口”结构比较范围。
EXCLUDE = (
    '/export', 'download', '/sync', 'synch', 'genCode', 'batchGen',
    '/status', '/approvals', '/retry', '/submit', '/cancel', '/delete',
    '/remove', '/add', '/edit', '/upload', '/import', '/save', '/clean',
)


def keep(endpoint: str) -> bool:
    """判断端点是否属于列表/分页/主键读取。"""
    path = endpoint.split('?', 1)[0]
    if any(token in path for token in EXCLUDE):
        return False
    leaf = path.rstrip('/').split('/')[-1]
    if leaf.startswith('list') or leaf in {'listAll', 'listQuery', 'tree', 'treeselect', 'getInfo', 'profile'}:
        return True
    if re.fullmatch(r'\d+', leaf):
        return True
    if re.fullmatch(r'[0-9a-f]{8,}', leaf):
        return True
    if re.fullmatch(r'[0-9a-f-]{36}', leaf):
        return True
    if leaf.startswith('get') or leaf.startswith('view'):
        return True
    return False


for app in ['backend', 'api']:
    src = BASE / f'{app}-read-realkey.txt'
    dst = BASE / f'{app}-read-only.txt'
    lines = [line.strip() for line in src.read_text(encoding='utf-8').splitlines() if line.strip()]
    selected = [line for line in lines if keep(line)]
    dst.write_text('\n'.join(selected) + '\n', encoding='utf-8')
    print('WROTE', dst, len(selected))
