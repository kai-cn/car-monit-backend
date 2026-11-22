#!/usr/bin/env bash
# @description 历史脚本 19-analyze-samples.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash 19-analyze-samples.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# LEGACY-SCRIPT-ANNOTATION
# 文件：19-analyze-samples.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
echo "==== WSL SAMPLES ===="
if [ -f /tmp/resource-samples.log ]; then
  awk -F'[ =|]' '{
    u=0; p=0; a=0;
    for(i=1;i<=NF;i++){
      if($i=="used") u=$(i+1);
      if($i=="proc_mb") p=$(i+1);
      if($i=="avail") a=$(i+1);
    }
    n++;
    if(u>mu) mu=u;
    if(p>mp) mp=p;
    if(n==1||a<la) la=a;
    su+=u; sp+=p;
  } END {
    if(n>0) printf "samples=%d max_used_mb=%d avg_used_mb=%.0f max_proc_mb=%d avg_proc_mb=%.0f min_avail_mb=%d\n", n, mu, su/n, mp, sp/n, la;
  }' /tmp/resource-samples.log
  echo "---- peak lines ----"
  grep -v '^DONE' /tmp/resource-samples.log | sort -t= -k3 -rn | head -3
  echo "---- last ----"
  tail -2 /tmp/resource-samples.log
fi
echo "==== WINDOWS SAMPLES ===="
WIN=/mnt/d/work/runtime-logs/win-mem-samples.log
if [ -f "$WIN" ]; then
  awk -F'[ =]' '{
    v=0; f=0;
    for(i=1;i<=NF;i++){
      if($i=="vmmem_mb") v=$(i+1);
      if($i=="free_gb") f=$(i+1);
    }
    n++;
    if(v>mv) mv=v;
    if(n==1||f<lf) lf=f;
    sv+=v;
  } END {
    if(n>0) printf "samples=%d max_vmmem_mb=%d avg_vmmem_mb=%.0f min_host_free_gb=%.2f\n", n, mv, sv/n, lf;
  }' "$WIN"
  echo "---- last ----"
  tail -2 "$WIN"
fi
