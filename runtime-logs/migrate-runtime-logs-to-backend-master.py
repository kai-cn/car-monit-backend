#!/usr/bin/env python3
"""
@description 将历史 runtime-logs 中的脚本、证据、yml 和 md 合并到 backend master 工作树，并按内容去重文档。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/migrate-runtime-logs-to-backend-master.py
@dependencies Python 3 标准库；只处理本地两个固定目录，不访问 GitHub API。
"""
import hashlib
import shutil
from pathlib import Path

SRC = Path(r'D:\work\runtime-logs')
REPO = Path(r'D:\work\IdeaProjects\car-monit-backend-new')
DST = REPO / 'runtime-logs'
DOCS = REPO / 'docs'
ALLOWED = {'.py', '.ps1', '.sh', '.yml', '.yaml', '.md', '.json', '.txt', '.tsv', '.xml', '.result'}
SKIP_DIRS = {'__pycache__', '.git', 'node_modules', 'venv', 'cicd-artifacts'}
SKIP_PREFIX = ('junit-bk', 'junit3-', 'junit-api-', 'crosslang-evidence', 'local-rerun-check', 'local-junit-smoke')


def digest(path: Path) -> str:
    """计算文件 SHA-256，用于识别完全相同文档，仅保留一份。"""
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def skipped(path: Path) -> bool:
    """过滤运行产物、临时目录和第三方目录，避免把大文件纳入 git。"""
    rel = path.relative_to(SRC).as_posix()
    return any(part in SKIP_DIRS for part in path.parts) or rel.startswith(SKIP_PREFIX)


def main() -> None:
    """迁移允许类型文件、替换注释作者、删除与 docs 内容重复的 md，并写出迁移报告。"""
    DST.mkdir(parents=True, exist_ok=True)
    docs_hashes = {digest(p) for p in DOCS.rglob('*.md') if p.is_file()}
    copied, skipped_md, author_fixed = [], [], []
    for p in sorted(SRC.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in ALLOWED or skipped(p):
            continue
        rel = p.relative_to(SRC)
        target = DST / rel
        if p.suffix.lower() == '.md' and digest(p) in docs_hashes:
            skipped_md.append(rel.as_posix())
            if target.exists():
                target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        copied.append(rel.as_posix())
        if p.suffix.lower() in {'.py', '.ps1', '.sh', '.yml', '.yaml'}:
            text = target.read_text(encoding='utf-8', errors='replace')
            if '@author AI Assistant' in text:
                target.write_text(text.replace('@author AI Assistant', '@author Tencent Hunyuan Hy'), encoding='utf-8')
                author_fixed.append(rel.as_posix())

    # 目标目录中已经存在但与 docs 完全重复的 md 也只保留一份。
    docs_hashes = {digest(p) for p in DOCS.rglob('*.md') if p.is_file()}
    for p in sorted(DST.rglob('*.md')):
        if p.is_file() and digest(p) in docs_hashes:
            p.unlink()
            skipped_md.append(p.relative_to(DST).as_posix())

    report = {
        'copied': len(copied), 'duplicate_md_skipped': len(skipped_md),
        'authors_normalized': len(author_fixed),
        'copied_files': copied, 'duplicate_md': skipped_md,
    }
    (DST / 'migration-report.json').write_text(
        __import__('json').dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('COPIED', len(copied), 'DUP_MD', len(skipped_md), 'AUTHORS', len(author_fixed))


if __name__ == '__main__':
    main()
