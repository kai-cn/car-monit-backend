set -euo pipefail
JAVA_OUT="$(java -version 2>&1)"
echo "${JAVA_OUT}"
mvn -v
# here-string avoids SIGPIPE false-negatives that ``| grep -q`` triggers under pipefail
grep -qE 'version "17\.' <<< "${JAVA_OUT}" || {
  echo "::error::branch car-monit-api-jdk17 requires JDK 17, runner java differs"
  exit 1
}



