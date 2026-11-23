#!/usr/bin/env python3
"""Fix final confirmed generator null pointers.

@description 修复 synchDb 与 batchGenCode 空参数空指针，并让 Gen 的 TableDataInfo 返回 code=200。
@author Tencent Hunyuan Hy
@date 2026-11-23 08:10:00
@usage python3 runtime-logs/patch-final-generator.py
@dependencies WSL backend master。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
GEN = B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java'
CTRL = B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java'
TABLE = B / 'ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java'


def replace(path, old, new):
    """Replace exact source text."""
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    t = raw.decode('utf-8', errors='replace')
    if old not in t:
        print('NOT_FOUND', path, old[:60])
        return
    t = t.replace(old, new)
    data = (t.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else t).encode('utf-8')
    path.write_bytes(data)
    print('OK', path)


replace(GEN,
        '''        GenTable table = genTableMapper.selectGenTableByName(tableName);
        List<GenTableColumn> tableColumns = table.getColumns();
''',
        '''        GenTable table = genTableMapper.selectGenTableByName(tableName);
        if (table == null) {
            return;
        }
        List<GenTableColumn> tableColumns = table.getColumns();
''')
replace(CTRL,
        '''        String[] tableNames = Convert.toStrArray(tables);
        byte[] data = genTableService.downloadCode(tableNames);
        genCode(response, data);
''',
        '''        String[] tableNames = Convert.toStrArray(tables);
        if (tableNames.length == 0) {
            genCode(response, new byte[0]);
            return;
        }
        byte[] data = genTableService.downloadCode(tableNames);
        genCode(response, data);
''')
replace(TABLE,
        '''    /** 消息状态码 */
    private int code;
''',
        '''    /** 消息状态码：统一成功口径为 200 */
    private int code = 200;
''')
