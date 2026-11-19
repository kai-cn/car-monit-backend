set +e
echo "runner=${RUNNER_NAME} os=${RUNNER_OS} arch=${RUNNER_ARCH}"
uname -a
echo "cpus=$(nproc)"
free -m | head -2
echo "node=$(node -v 2>&1)  user=$(id -un)  HOME=${HOME}"
echo "JAVA_HOME=${JAVA_HOME:-<unset>}"
command -v java && java -version 2>&1 | head -3
command -v mvn && mvn -v 2>&1 | head -3


