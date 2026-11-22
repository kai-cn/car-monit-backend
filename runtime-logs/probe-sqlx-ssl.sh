#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：probe-sqlx-ssl.sh
# 用途：只读检查/诊断。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。
grep -R "ssl-mode" /home/dev/.cargo/registry/src/*/sqlx-core-*/src/mysql 2>/dev/null | head -20 || true
