# @description 历史脚本 18-win-sample.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File 18-win-sample.ps1 [params]；参数含义见脚本原有注释。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION

# 文件：18-win-sample.ps1

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

$log = 'D:\work\runtime-logs\win-mem-samples.log'

Remove-Item $log -ErrorAction SilentlyContinue

1..200 | ForEach-Object {

    $vm = (Get-Process vmmemWSL -ErrorAction SilentlyContinue).WorkingSet64 / 1MB

    $free = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB

    "$(Get-Date -Format HH:mm:ss) vmmem_mb=$([math]::Round($vm,0)) free_gb=$([math]::Round($free/1024,2))" |

        Out-File -Append -FilePath $log -Encoding UTF8

    Start-Sleep -Seconds 3

}

