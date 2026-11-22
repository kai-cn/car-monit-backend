#!/usr/bin/env bash

# @description 历史脚本 list-cl-classes.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash list-cl-classes.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: List repositories, classes, branches, or workflow files.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

unzip -l /home/dev/.m2/repository/commons-logging/commons-logging/1.3.6/commons-logging-1.3.6.jar | grep 'impl/'

