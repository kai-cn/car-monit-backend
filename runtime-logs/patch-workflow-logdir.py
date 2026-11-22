#!/usr/bin/env python3
"""
@description 修复跨语言 workflow 中 /home/ruoyi/logs 的创建权限，避免基线启动前失败。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/patch-workflow-logdir.py
@dependencies 修改两仓库 master 工作树中的 workflow。
"""
from pathlib import Path

for p in [Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
          Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')]:
    t = p.read_text(encoding='utf-8')
    old = '          mkdir -p "$LOG_PATH" /home/ruoyi/logs\n'
    new = '          sudo mkdir -p "$LOG_PATH" /home/ruoyi/logs; sudo chown -R "$(id -u):$(id -g)" "$LOG_PATH" /home/ruoyi; mkdir -p "$LOG_PATH" /home/ruoyi/logs\n'
    assert old in t
    p.write_text(t.replace(old, new, 1), encoding='utf-8')
    print('PATCHED', p)
