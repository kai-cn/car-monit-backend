#!/usr/bin/env python3
"""
@description 将跨语言 workflow 的 baseline JDK 改为 master 实际使用的 JDK8，避免 Boot2 在 JDK25 下缺少 JAXB。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/patch-crosslang-jdk8.py
@dependencies 修改两仓库 master 工作树中的 crosslang workflow。
"""
from pathlib import Path

for p in [Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
          Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')]:
    t = p.read_text(encoding='utf-8')
    t = t.replace("          distribution: temurin\n\n          java-version: '25'\n",
                  "          distribution: corretto\n\n          java-version: '8'\n")
    t = t.replace('Java25 Boot4 baseline branch', 'merged master Java baseline')
    t = t.replace('# 用途：以 Java25 Boot4 为基线，对比 Python/Go/C++ 全接口 + 压测',
                  '# 用途：以合并后的 Java master 为基线，对比 Python/Go/C++/Rust 全接口 + 压测')
    t = t.replace('#   - baseline job 构建 target_ref（默认 *-jdk25）并运行 JUnit 契约/压测',
                  '#   - baseline job 构建 target_ref（默认 master，JDK8）并运行 JUnit 契约/压测')
    t = t.replace('@author AI Assistant', '@author Tencent Hunyuan Hy')
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
