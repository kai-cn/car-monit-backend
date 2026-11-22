#!/usr/bin/env bash

# @description 历史脚本 probe-rust-local.sh：探测 API、端口或解析错误；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash probe-rust-local.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：probe-rust-local.sh

# 用途：只读检查/诊断。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。

command -v cargo >/dev/null 2>&1 && cargo --version || echo NO_CARGO

docker ps --format '{{.Names}} {{.Status}}'

ss -ltn 2>/dev/null | grep -E ':3306|:3307' || echo NO_MYSQL_PORT

