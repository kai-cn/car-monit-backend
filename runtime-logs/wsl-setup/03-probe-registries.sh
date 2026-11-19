#!/usr/bin/env bash
for h in ghcr.io docker.m.daocloud.io hub-mirror.c.163.com registry.cn-hangzhou.aliyuncs.com docker.1panel.live dockerproxy.net registry.docker-cn.com; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "https://$h/v2/" 2>/dev/null || printf 'FAIL')
  printf '%s=%s\n' "$h" "$code"
done
