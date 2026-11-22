#!/usr/bin/env python3
"""
@description 历史脚本 append-author-restore.py：向交接文档追加结构化记录；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python append-author-restore.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

A={
 r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-21.md': '''

## 提交人信息恢复
- squash 后的 631 个重建提交作者/提交者被写成 CodeBuddy，已恢复为原始信息。
- 新增通用脚本 `restore-commit-metadata.py`：按 (subject, tree) 从 source-ref 映射原始 author/committer 名称、邮箱、时间。
- 执行源：`refs/backup/squash-car-monit-backend-java-V3-20261121151255`。
- 当前 head：`ddc149387712592baf6b784e60f9e01cc2fee0f4`；CodeBuddy author/committer 计数为 0。
- 回滚 backup：`refs/backup/metadata-car-monit-backend-java-V3-20261121155316`。
''',
 r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''

## P. 提交人信息恢复
- `restore-commit-metadata.py`：按 (subject, tree) 从备份引用恢复 author/committer；
  默认 dry-run，--apply 才写远端；拒绝 main/master；force-with-lease；自动 backup ref。
- 已对 `car-monit-backend-java-V3` 执行，恢复 631 个提交元信息；当前 head `ddc14938`，
  CodeBuddy author/committer 计数为 0，目标 squash 提交仍为 1 个。
''',
}
for path_str,text in A.items():
    p=Path(path_str)
    if not p.exists():
        print('MISSING',path_str); continue
    cur=p.read_text(encoding='utf-8')
    marker=text.strip().splitlines()[0]
    if marker in cur:
        print('SKIP',p.name); continue
    p.write_text(cur.rstrip()+'\n'+text,encoding='utf-8')
    print('APPENDED',p.name)
