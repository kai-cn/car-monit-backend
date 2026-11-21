#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：03-probe-registries.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
for h in ghcr.io docker.m.daocloud.io hub-mirror.c.163.com registry.cn-hangzhou.aliyuncs.com docker.1panel.live dockerproxy.net registry.docker-cn.com; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "https://$h/v2/" 2>/dev/null || printf 'FAIL')
  printf '%s=%s\n' "$h" "$code"
done
