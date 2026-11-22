# @description 历史脚本 run-wsl-retest4.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File run-wsl-retest4.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Purpose: launch the final WSL local service retest.

# Idea: run the script detached, redirect logs to D drive, and print initial status.

# Risk: writes only local evidence files and starts a temporary local service.

$out = 'D:\work\runtime-logs\wsl-service-retest4.out'

$err = 'D:\work\runtime-logs\wsl-service-retest4.err'

$p = Start-Process -FilePath wsl -ArgumentList @('bash', '/mnt/d/work/runtime-logs/wsl-local-service-retest4.sh') -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden

Write-Output "PID=$($p.Id)"

Start-Sleep -Seconds 30

Get-Content $out -Encoding utf8 -Tail 20 -ErrorAction SilentlyContinue

Get-Content $err -Encoding utf8 -Tail 10 -ErrorAction SilentlyContinue

