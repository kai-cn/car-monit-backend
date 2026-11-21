# LEGACY-SCRIPT-ANNOTATION
# 文件：car-monit-api-jdk17_b2.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -euo pipefail
JDK_MAJOR="17"
JDK_FULL="17.0.21+9"
JDK_TARBALL="OpenJDK17U-jdk_x64_linux_hotspot_17.0.21_9.tar.gz"
GH_TAG="jdk-17.0.21%2B9"
CACHE_ROOT="${HOME}/.cache/ci-toolchain"
JDK_HOME="${CACHE_ROOT}/jdk-${JDK_FULL}"

if [ -x "${JDK_HOME}/bin/java" ]; then
  echo ">> reuse cached JDK ${JDK_FULL} at ${JDK_HOME}"
else
  mkdir -p "${CACHE_ROOT}"
  TGZ="${CACHE_ROOT}/${JDK_TARBALL}.part"
  urls=(
    "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/${JDK_MAJOR}/jdk/x64/linux/${JDK_TARBALL}"
    "https://github.com/adoptium/temurin${JDK_MAJOR}-binaries/releases/download/${GH_TAG}/${JDK_TARBALL}"
  )
  ok=0
  for u in "${urls[@]}"; do
    echo ">> fetching ${u}"
    if curl -fsSL --retry 2 --connect-timeout 20 --max-time 900 -o "${TGZ}" "${u}"; then
      ok=1
      break
    fi
    echo ">> mirror unavailable: ${u}" >&2
  done
  if [ "${ok}" -ne 1 ]; then
    echo "::error::unable to download Temurin ${JDK_FULL} from any configured mirror"
    exit 1
  fi
  rm -rf "${JDK_HOME}.tmp"
  mkdir -p "${JDK_HOME}.tmp"
  tar -xzf "${TGZ}" -C "${JDK_HOME}.tmp" --strip-components=1
  rm -f "${TGZ}"
  mv "${JDK_HOME}.tmp" "${JDK_HOME}"
  echo ">> installed JDK ${JDK_FULL} at ${JDK_HOME}"
fi

echo "JAVA_HOME=${JDK_HOME}" >> "${GITHUB_ENV}"
echo "${JDK_HOME}/bin" >> "${GITHUB_PATH}"
export JAVA_HOME="${JDK_HOME}"
export PATH="${JDK_HOME}/bin:${PATH}"
java -version 2>&1

