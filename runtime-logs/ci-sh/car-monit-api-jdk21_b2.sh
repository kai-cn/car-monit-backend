set -euo pipefail
JDK_MAJOR="21"
JDK_FULL="21.0.13+9"
JDK_TARBALL="OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz"
GH_TAG="jdk-21.0.13%2B9"
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

