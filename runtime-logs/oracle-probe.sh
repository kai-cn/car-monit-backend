#!/bin/sh

# @description 历史脚本 oracle-probe.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash oracle-probe.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

ORACLE_HOME=/home/oracle/app/oracle/product/11.2.0/dbhome_2

ORACLE_SID=helowin

PATH=$ORACLE_HOME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

export ORACLE_HOME ORACLE_SID PATH

cd /tmp

sqlplus -S / as sysdba @/tmp/oracle-probe.sql

