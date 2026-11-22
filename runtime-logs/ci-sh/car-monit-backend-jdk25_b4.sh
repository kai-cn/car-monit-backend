# LEGACY-SCRIPT-ANNOTATION
# 文件：car-monit-backend-jdk25_b4.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -euo pipefail
JAVA_OUT="$(java -version 2>&1)"
echo "${JAVA_OUT}"
mvn -v
# here-string avoids SIGPIPE false-negatives that ``| grep -q`` triggers under pipefail
grep -qE 'version "25\.' <<< "${JAVA_OUT}" || {
  echo "::error::branch car-monit-backend-jdk25 requires JDK 25, runner java differs"
  exit 1
}



