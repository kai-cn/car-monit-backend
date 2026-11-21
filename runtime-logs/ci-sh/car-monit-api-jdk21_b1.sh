# LEGACY-SCRIPT-ANNOTATION
# 文件：car-monit-api-jdk21_b1.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set +e
echo "runner=${RUNNER_NAME} os=${RUNNER_OS} arch=${RUNNER_ARCH}"
uname -a
echo "cpus=$(nproc)"
free -m | head -2
echo "node=$(node -v 2>&1)  user=$(id -un)  HOME=${HOME}"
echo "JAVA_HOME=${JAVA_HOME:-<unset>}"
command -v java && java -version 2>&1 | head -3
command -v mvn && mvn -v 2>&1 | head -3


