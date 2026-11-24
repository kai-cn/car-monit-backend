#!/usr/bin/env bash
# @description 解析 WSL 容器新别名并提供旧别名兼容，供所有实测脚本统一引用。
# @author Tencent Hunyuan Hy
# @date 2026-11-24 12:10:00
# @usage source runtime-logs/wsl-container-alias.sh; echo "$MYSQL_CONTAINER"
# @dependencies Docker；新别名 mysql8.0/gauss3.0/redis7/kafka4.0/pg16/es7。
# NOTE: 用户已调整容器别名；旧脚本可继续通过 fallback 查找旧容器，但新脚本一律优先新别名。

pick_container() {
  local new_name="$1" old_name="$2"
  if docker ps -a --format '{{.Names}}' | grep -qx "$new_name"; then
    echo "$new_name"
  elif docker ps -a --format '{{.Names}}' | grep -qx "$old_name"; then
    echo "$old_name"
  else
    echo "$new_name"
  fi
}

MYSQL_CONTAINER="$(pick_container mysql8.0 mysql_wsl)"
GAUSS_CONTAINER="$(pick_container gauss3.0 opengauss)"
REDIS_CONTAINER="$(pick_container redis7 redis_wsl)"
KAFKA_CONTAINER="$(pick_container kafka4.0 kafka-wsl)"
PG_CONTAINER="$(pick_container pg16 pg_wsl)"
ES_CONTAINER="$(pick_container es7 es-wsl)"
export MYSQL_CONTAINER GAUSS_CONTAINER REDIS_CONTAINER KAFKA_CONTAINER PG_CONTAINER ES_CONTAINER
