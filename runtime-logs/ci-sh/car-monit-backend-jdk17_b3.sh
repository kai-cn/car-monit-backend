# @description 历史脚本 car-monit-backend-jdk17_b3.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash car-monit-backend-jdk17_b3.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# LEGACY-SCRIPT-ANNOTATION
# 文件：car-monit-backend-jdk17_b3.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -euo pipefail
MVN_VER="3.9.9"
MVN_TARBALL="apache-maven-${MVN_VER}-bin.tar.gz"
CACHE_ROOT="${HOME}/.cache/ci-toolchain"
MVN_HOME="${CACHE_ROOT}/apache-maven-${MVN_VER}"

if [ -x "${MVN_HOME}/bin/mvn" ]; then
  echo ">> reuse cached Maven ${MVN_VER} at ${MVN_HOME}"
else
  mkdir -p "${CACHE_ROOT}"
  TGZ="${CACHE_ROOT}/${MVN_TARBALL}.part"
  urls=(
    "https://repo.huaweicloud.com/apache/maven/maven-3/${MVN_VER}/binaries/${MVN_TARBALL}"
    "https://archive.apache.org/dist/maven/maven-3/${MVN_VER}/binaries/${MVN_TARBALL}"
  )
  ok=0
  for u in "${urls[@]}"; do
    echo ">> fetching ${u}"
    if curl -fsSL --retry 2 --connect-timeout 20 --max-time 600 -o "${TGZ}" "${u}"; then
      ok=1
      break
    fi
    echo ">> mirror unavailable: ${u}" >&2
  done
  if [ "${ok}" -eq 1 ]; then
    rm -rf "${MVN_HOME}.tmp"
    mkdir -p "${MVN_HOME}.tmp"
    tar -xzf "${TGZ}" -C "${MVN_HOME}.tmp" --strip-components=1
    rm -f "${TGZ}"
    mv "${MVN_HOME}.tmp" "${MVN_HOME}"
    echo ">> installed Maven ${MVN_VER} at ${MVN_HOME}"
  elif command -v mvn >/dev/null 2>&1; then
    echo "::warning::Maven mirror download failed; falling back to system mvn"
    MVN_HOME=""
  else
    echo "::error::Maven ${MVN_VER} unavailable from mirrors and no system mvn on PATH"
    exit 1
  fi
fi

if [ -n "${MVN_HOME}" ]; then
  echo "MAVEN_HOME=${MVN_HOME}" >> "${GITHUB_ENV}"
  echo "M2_HOME=${MVN_HOME}" >> "${GITHUB_ENV}"
  echo "${MVN_HOME}/bin" >> "${GITHUB_PATH}"
  export PATH="${MVN_HOME}/bin:${PATH}"
fi
mvn -v

