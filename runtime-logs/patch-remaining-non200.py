#!/usr/bin/env python3
"""Patch confirmed non-200 root causes in WSL master.

@description 修复生成器空表空指针、导出空集合空指针、schema fixture 本机导入与 api 下游 Kafka 启动排除。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/patch-remaining-non200.py
@dependencies WSL master clones 与 Python 3。
"""
import subprocess
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
GEN = B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java'
FLOW = B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java'
SUS = B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java'
RETEST = Path('/mnt/d/work/runtime-logs/wsl-local-retest-with-downstream.py')


def replace(path, old, new):
    """Replace exact source text."""
    if not path.exists():
        print('MISSING', path)
        return False
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    t = raw.decode('utf-8', errors='replace')
    if old not in t:
        print('NOT_FOUND', path)
        return False
    t = t.replace(old, new)
    data = (t.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else t).encode('utf-8')
    path.write_bytes(data)
    print('OK', path)
    return True


# Generator: avoid NPE when placeholder id/table name has no matching metadata.
replace(GEN,
        '''    public GenTable selectGenTableById(Long id) {
        GenTable genTable = genTableMapper.selectGenTableById(id);
        setTableFromOptions(genTable);
        return genTable;
    }
''',
        '''    public GenTable selectGenTableById(Long id) {
        GenTable genTable = genTableMapper.selectGenTableById(id);
        if (genTable == null) {
            return new GenTable();
        }
        setTableFromOptions(genTable);
        return genTable;
    }
''')

# Read exact generator context around failing methods before patching further.
for rel, needles in [
    ('ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java',
     ['previewCode', 'downloadCode', 'initFilterColumnInfo', 'initUploadInfo']),
    ('ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java',
     ['exportShrz']),
    ('ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java',
     ['exportAbnormalPassage']),
]:
    p = B / rel
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines() if p.exists() else []
    print('===', rel, '===')
    for i, line in enumerate(lines):
        if any(n in line for n in needles):
            print(i + 1, line.strip()[:220])
