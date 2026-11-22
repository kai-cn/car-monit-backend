# @description 历史脚本 collect_final3.ps1：收集云端 run、job 或 artifact 状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage powershell -File collect_final3.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Collect run results into a concise report.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$out="D:\work\runtime-logs\final3-results.txt"

$base="D:\work\runtime-logs\gh_api.ps1"

$targets=@(

  @{repo='kai-cn/car-monit-api';id=43905084757;label='API native BUILD'},

  @{repo='kai-cn/car-monit-api';id=43905468152;label='API master'},

  @{repo='kai-cn/car-monit-api';id=43905476617;label='API pr'},

  @{repo='kai-cn/car-monit-backend';id=43905459051;label='BACKEND native BUILD'},

  @{repo='kai-cn/car-monit-backend';id=43904480854;label='BACKEND ci'}

)

function W($m){("{0} {1}" -f (Get-Date -Format HH:mm:ss),$m)|Out-File -FilePath $out -Append -Encoding utf8}

"=== COLLECTOR3 START ===" | Out-File -FilePath $out -Encoding utf8

$deadline=(Get-Date).AddMinutes(80)

$done=$false

while((Get-Date) -lt $deadline){

  $all=$true

  foreach($t in $targets){ $o=& $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)"|ConvertFrom-Json; if($o.status -ne 'completed'){$all=$false;break} }

  if($all){$done=$true;break}

  Start-Sleep -Seconds 30

}

if(-not $done){ W "TIMEOUT"; exit }

foreach($t in $targets){

  $r=& $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)"|ConvertFrom-Json

  W ("RUN {0} id={1} sha={2} => {3}" -f $t.label,$t.id,$r.head_sha.Substring(0,7),$r.conclusion)

  $js=& $base -Method GET -Uri "https://api.github.com/repos/$($t.repo)/actions/runs/$($t.id)/jobs?per_page=30"|ConvertFrom-Json

  foreach($j in $js.jobs){ W ("   {0} => {1}" -f $j.name,$j.conclusion) }

}

W "=== COLLECTOR3 DONE ==="

