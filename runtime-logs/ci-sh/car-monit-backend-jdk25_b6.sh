# @description 历史脚本 car-monit-backend-jdk25_b6.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash car-monit-backend-jdk25_b6.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：car-monit-backend-jdk25_b6.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

docker exec k3d-v3-server-0 kubectl create deployment v3-ci-probe \

  --image=rancher/mirrored-pause:3.6 --replicas=3 \

  --dry-run=client -o yaml | docker exec -i k3d-v3-server-0 kubectl apply -f -

docker exec k3d-v3-server-0 kubectl rollout status deployment/v3-ci-probe --timeout=240s

docker exec k3d-v3-server-0 kubectl get pods -l app=v3-ci-probe -o wide



