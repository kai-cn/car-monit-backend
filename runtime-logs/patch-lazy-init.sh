#!/usr/bin/env bash
# @description 历史脚本 patch-lazy-init.sh：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash patch-lazy-init.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# 临时关闭 api 的懒加载(args 索引 26)以验证 Kafka 消费者是否会被创建启动
docker exec k3d-v3-server-0 kubectl patch deployment car-monit-api --type=json \
  -p "[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/args/26\",\"value\":\"--spring.main.lazy-initialization=false\"}]"
docker exec k3d-v3-server-0 kubectl rollout restart deployment/car-monit-api
