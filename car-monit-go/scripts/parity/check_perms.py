#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态比对 Java 控制器注解与 Go 路由注册的权限点 / 操作日志。

背景：双端对拍脚本全部用 admin 登录，admin 拥有 *:*:*，因此“Go 漏挂 @PreAuthorize”
和“Go 漏挂 @Log”在返回体对比里完全隐形。本脚本直接读两侧源码，属于 CI 门禁。

判定口径（宽松但能覆盖真实事故类型）：
1. Java 侧每个**未被注释**的 @PreAuthorize("...hasPermi('P')")，P 必须在 Go 源码里
   以字符串字面量出现过（允许 registerStandard/registerListOnly 用 P+":list" 的拼接形式，
   此时 P 本身会作为调用参数出现）。
2. Java 侧每个**未被注释**的 @Log(title = "T")，T 必须在 Go 源码里以字符串字面量出现过
   （允许 Go 用 registerStandard 的 title 参数传入）。

这是“控制器级”检查：同一控制器的多个端点共用标题时，无法区分是哪一个端点漏挂；
逐端点级比对请配合 scripts/parity/compare_write.py 与无权限账号的运行时检查。

退出码：0 全部命中；1 存在缺失（CI 失败）。
"""

import argparse
import io
import os
import re
import sys

MAPPING = re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\'])?')
REQ_MAPPING = re.compile(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']')
PERM = re.compile(r'@PreAuthorize\s*\(\s*"([^"]*)"')
HAS_PERMI = re.compile(r"hasPermi\s*\(\s*'([^']+)'")
LOG = re.compile(r'@Log\s*\(')
LOG_TITLE = re.compile(r'title\s*=\s*"([^"]*)"')

# 已知且有意为之的差异：Java 有注解但 Go 故意不挂（需在代码 DIFF 注释中说明）。
ALLOW_MISSING_PERMS = set()
ALLOW_MISSING_LOGS = set()

# registerStandard / registerListOnly 用 base+":suffix" 拼权限，此时完整权限串不会出现，
# 但 base 会作为调用参数出现，且源码里存在 Perm(perm+":...") 的拼接写法。
CONCAT_PERM = re.compile(r'middleware\.Perm\(\s*\w+\s*\+\s*"')


def perm_present(go, perm):
    if '"%s"' % perm in go:
        return True
    base = perm.rsplit(':', 1)[0]
    return ('"%s"' % base in go) and bool(CONCAT_PERM.search(go))


def java_declarations(java_root):
    """返回 (perms, titles) —— 只统计未被 // 注释的注解。"""
    perms, titles = set(), set()
    for root, _, files in os.walk(java_root):
        for fn in sorted(files):
            if not fn.endswith('.java'):
                continue
            text = io.open(os.path.join(root, fn), encoding='utf-8', errors='replace').read()
            lines = text.splitlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue
                pm = PERM.search(stripped)
                if pm:
                    sm = HAS_PERMI.search(pm.group(1))
                    if sm:
                        perms.add((fn, sm.group(1)))
                if LOG.search(stripped):
                    block = stripped
                    k = i
                    while ')' not in block[block.find('(') + 1:] and k + 1 < len(lines) and k - i < 6:
                        k += 1
                        block += ' ' + lines[k].strip()
                    tm = LOG_TITLE.search(block)
                    if tm and tm.group(1):
                        titles.add((fn, tm.group(1)))
    return perms, titles


def go_source(go_root):
    buf = []
    for root, _, files in os.walk(go_root):
        for fn in files:
            if fn.endswith('.go') and not fn.endswith('_test.go'):
                buf.append(io.open(os.path.join(root, fn), encoding='utf-8', errors='replace').read())
    return '\n'.join(buf)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--java-root', required=True, help='Java controller 目录')
    ap.add_argument('--go-root', required=True, help='Go internal 目录')
    args = ap.parse_args()

    if not os.path.isdir(args.java_root):
        print('Java 目录不存在: %s' % args.java_root)
        return 2

    perms, titles = java_declarations(args.java_root)
    go = go_source(args.go_root)

    missing_perms = []
    for fn, p in sorted(perms):
        if p in ALLOW_MISSING_PERMS:
            continue
        if not perm_present(go, p):
            missing_perms.append((fn, p))

    missing_logs = []
    for fn, t in sorted(titles):
        if t in ALLOW_MISSING_LOGS:
            continue
        if '"%s"' % t not in go:
            missing_logs.append((fn, t))

    print('Java 权限点 %d 个，缺失 %d 个' % (len(perms), len(missing_perms)))
    for fn, p in missing_perms:
        print('  MISSING PERM  %-40s %s' % (fn, p))

    print('Java 操作日志标题 %d 个，缺失 %d 个' % (len(titles), len(missing_logs)))
    for fn, t in missing_logs:
        print('  MISSING LOG   %-40s %s' % (fn, t))

    return 1 if (missing_perms or missing_logs) else 0


if __name__ == '__main__':
    sys.exit(main())
