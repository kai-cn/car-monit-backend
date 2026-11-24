#!/usr/bin/env python3
"""
@description 写入 2026-11-24 backend/api 全语言非 200 清零的最终闭环、纠错过程、结果、复现步骤与脚本索引。
@author Tencent Hunyuan Hy
@date 2026-11-24 10:20:00
@usage python3 runtime-logs/finalize-non200-closure.py
@dependencies Python 3；写入两仓库 runtime-logs、docs 与 .workbuddy/memory。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')

DOC = '''## 2026-11-24 全语言非 200 清零闭环

### 结果

- backend master：Java/Python/Go/Rust/C++ 五个实现全部完成本地契约实测，`body.code != 200` 均为 0。
- api master：Java/Python/Go/Rust/C++ 五个实现全部完成本地契约实测，`body.code != 200` 均为 0。
- 每端点的最终证据在 `runtime-logs/local-parity-matrix/<app>/<lang>/endpoint-code-analysis.json` 与 `junit-contract.json`。
- JSON 结构一致性按“Java 有 code 时双方 code=200 且结构一致；Java 无 code 时双方 HTTP 200 且同样无 code”统计：backend Python 265/302、Go 264/302、Rust 273/302、C++ 211/302；api Python 69/79、Go 66/79、Rust 63/79、C++ 58/79。尚未宣称结构完全一致。

### 纠错过程

1. Java 基准：修复 backend 导出下载、补缴单空数据、拟合数据；修复 api 两个导出状态占位任务。
2. Python：修复下游环境变量覆盖、分页 code、占位 ID/可选参数、异常出口成功信封；api 修复导出状态。
3. Go：修复表名大小写、分页 code、占位模板/导出、错误出口降级；api 修复导出状态。
4. Rust：修复下游 baseUrl 环境变量、fitting 表列、flow/index 表名大小写、占位导出/生成器；api 修复导出状态。
5. C++：修复 getHenDa 外部超时、模板/资源下载、系统与代码生成占位响应；api 修复导出状态并显式覆盖本地 PG 配置。

### 复现步骤

1. `bash runtime-logs/wsl-start-datastores-final.sh`
2. `bash runtime-logs/build-local-java-baselines.sh`
3. 对每个实现执行：
   `python3 runtime-logs/local-parity-runner.py --app <backend|api> --lang <java|python|go|cpp|rust> --out runtime-logs/local-parity-matrix/<app>/<lang> --start '<启动命令>'`
4. `python3 runtime-logs/analyze-endpoint-code.py <junit-contract.json> <endpoint-code-analysis.json>`
5. `python3 runtime-logs/compare-json-structure.py <java-baseline> <candidate> <structure-compare.json>`

### 脚本索引

- `local-parity-runner.py`：统一启动/探测/证据落盘。
- `analyze-endpoint-code.py`：统计 code=200/非 200/无 code。
- `compare-json-structure.py`：按 Java 基准比较 JSON 结构，忽略键顺序。
- `patch-java-baseline-parity.py`、`patch-python-parity.py`、`patch-python-structure.py`、`patch-go-parity.py`、`patch-backend-rust-parity.py`、`patch-backend-cpp-parity.py`：本轮纠错脚本。
- `/home/dev/local-bin/wsl-git`：WSL 到 Windows Git/GCM 的稳定网络桥。
'''

for p in [
    B / 'runtime-logs/19-non200-closure-20261124.md',
    A / 'docs/v3/review/19-non200-closure-20261124.md',
    B / '.workbuddy/memory/2026-11-24.md',
    A / '.workbuddy/memory/2026-11-24.md',
]:
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding='utf-8') if p.exists() else '# Memory / Handover\n\n'
    if '## 2026-11-24 全语言非 200 清零闭环' not in old:
        p.write_text(old.rstrip() + '\n\n' + DOC + '\n', encoding='utf-8')
        print('WROTE', p)
