# @description 历史脚本 car-monit-api-jdk17_b4.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash car-monit-api-jdk17_b4.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION

# 文件：car-monit-api-jdk17_b4.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

set -euo pipefail

JAVA_OUT="$(java -version 2>&1)"

echo "${JAVA_OUT}"

mvn -v

# here-string avoids SIGPIPE false-negatives that ``| grep -q`` triggers under pipefail

grep -qE 'version "17\.' <<< "${JAVA_OUT}" || {

  echo "::error::branch car-monit-api-jdk17 requires JDK 17, runner java differs"

  exit 1

}







