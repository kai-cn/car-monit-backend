#!/usr/bin/env python3
# 审计：Java 实体的字段（Jackson 会全部序列化）与 C++ 生成 spec 实际输出的 JSON 键之差。
# 用法：python scripts/audit_spec_keys.py [--verbose]
import io
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CPP_DIR = HERE.parent
REPO = CPP_DIR.parent

FIELD_RE = re.compile(
    r'(?m)^\s*private\s+(?!static)(?:final\s+)?[\w$<>\[\],.\s]+?\s+([\w$]+)\s*(?:=\s*([^;]+))?;')
SPEC_RE = re.compile(r'const Spec& (spec\w+)\(\)')


def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def json_ignore_names(src):
    """@JsonIgnore 标在哪些字段上（注解与字段之间可能夹着注释）"""
    bad = set()
    for m in FIELD_RE.finditer(src):
        head = src[max(0, m.start() - 300):m.start()]
        if '@JsonIgnore' in head:
            bad.add(m.group(1))
    return bad


def entity_fields(java_path):
    src = read(java_path)
    out = []
    for m in FIELD_RE.finditer(src):
        name, dflt = m.group(1), m.group(2)
        out.append((name, (dflt or '').strip()))
    return out, json_ignore_names(src)


def spec_blocks():
    blocks = {}
    for p in sorted((CPP_DIR / 'src' / 'cm' / 'web' / 'specs').glob('*.cpp')):
        src = read(p)
        for m in SPEC_RE.finditer(src):
            rest = src[m.start():]
            nxt = rest.find('\nconst Spec&', 10)
            body = rest if nxt < 0 else rest[:nxt]
            keys = [k for k in re.findall(r'\{"(\w+)",', body)]
            blocks[m.group(1)] = (p.name, keys)
    return blocks


def main():
    verbose = '--verbose' in sys.argv
    java_entities = {}
    for area in ('ruoyi-system', 'ruoyi-common', 'ruoyi-quartz', 'ruoyi-generator', 'ruoyi-admin'):
        root = REPO / area
        if not root.is_dir():
            continue
        for p in root.rglob('*.java'):
            sp = str(p).replace('\\', '/')
            if '/domain/' not in sp:
                continue
            java_entities[p.stem] = sp

    blocks = spec_blocks()
    total_missing = 0
    lines = []
    for spec, (fname, keys) in sorted(blocks.items()):
        cls = spec[len('spec'):]
        if cls not in java_entities:
            continue
        fields, ignored = entity_fields(java_entities[cls])
        want = [n for n, _ in fields if n not in ignored]
        have = set(keys)
        missing = [n for n in want if n not in have]
        defaults = {n: d for n, d in fields if d and n in want}
        if not missing:
            continue
        total_missing += len(missing)
        lines.append('%-22s %-28s 缺 %2d 键: %s' % (
            fname, cls, len(missing), ', '.join(missing[:10])))
        if verbose and defaults:
            hit = {n: defaults[n] for n in missing if n in defaults}
            if hit:
                lines.append('        其中带 Java 默认值: %s' % hit)
    io.open(str(CPP_DIR / 'logs' / 'missing_keys.txt'), 'w', encoding='utf-8').write(
        '\n'.join(lines) + ('\n合计缺失键 %d\n' % total_missing))
    print('缺失键合计：', total_missing)
    print('详见 logs/missing_keys.txt')


if __name__ == '__main__':
    main()
