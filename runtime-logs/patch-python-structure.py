#!/usr/bin/env python3
"""
@description 修复 backend Python 与 Java 基准的 JSON 结构差异，重点覆盖分页、空数据和占位导出端点。
@author Tencent Hunyuan Hy
@date 2026-11-23 17:30:00
@usage python3 runtime-logs/patch-python-structure.py
@dependencies backend master Python 源码。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-py')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换源码片段；未命中时输出诊断。"""
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print('NOT_FOUND', label, path)
        return
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


# 占位导出任务/下载令牌：返回与 Java 基准一致的成功空对象。
for rel in ['app/manager/service/bigscreen/big_screen_export_service.py',
            'app/api/manager/bigscreen/big_screen_export_controller.py']:
    p = B / rel
    if p.exists():
        t = p.read_text(encoding='utf-8')
        t = t.replace('"task not found"', '"NOT_FOUND"')
        t = t.replace('"下载令牌无效或已过期"', '""')
        p.write_text(t, encoding='utf-8')
        print('EXPORT_PLACEHOLDER', p)

# 分页对象默认 code=200，并补齐 Java 基准 msg 字段。
p = B / 'app/common/core/page/table_data_info.py'
t = p.read_text(encoding='utf-8')
if 'self.msg: Optional[str] = None' in t:
    t = t.replace('self.msg: Optional[str] = None', 'self.msg: Optional[str] = "查询成功"', 1)
p.write_text(t, encoding='utf-8')
print('TABLE_MSG', p)
