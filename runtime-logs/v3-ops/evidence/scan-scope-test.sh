#!/usr/bin/env bash
# @description 历史脚本 scan-scope-test.sh：扫描远端或本地状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash scan-scope-test.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION
# 文件：scan-scope-test.sh
# 用途：只读检查/诊断。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：通常只读；若脚本内有明确写操作以其自身说明为准。
# Compare MyBatis-Plus AOT scan scope before/after the CollectUtils patch,
# using the real JDK21 native-image classpath captured from an actual build.
set -u

J=/home/dev/tools/mandrel-21/bin
T=/mnt/d/work/runtime-logs/v3-ops/tmp-aot
CPF=/mnt/d/work/runtime-logs/v3-ops/evidence/classpath-api-jdk21-linux.txt
PATCH=/mnt/d/work/runtime-logs/v3-ops/patch/mybatis-aot

CP=$(paste -sd: "$CPF")
NI=$(ls /home/dev/tools/mandrel-21/lib/svm/builder/native-image*.jar 2>/dev/null | head -1)
echo "svm jar: ${NI:-none}"
echo "classpath entries: $(wc -l < "$CPF")"

"$J/javac" -d "$T" "$T/TestScanScope.java" 2>&1 | head -3

echo "=== ORIGINAL ==="
"$J/java" -cp "$T:$CP${NI:+:$NI}" TestScanScope 2>&1 | head -4

echo "=== PATCHED ==="
"$J/java" -cp "$T:$PATCH:$CP${NI:+:$NI}" TestScanScope 2>&1 | head -4
