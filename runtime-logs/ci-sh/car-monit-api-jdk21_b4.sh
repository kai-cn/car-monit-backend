set -euo pipefail
JAVA_OUT="$(java -version 2>&1)"
echo "${JAVA_OUT}"
mvn -v
# here-string avoids SIGPIPE false-negatives that ``| grep -q`` triggers under pipefail
grep -qE 'version "21\.' <<< "${JAVA_OUT}" || {
  echo "::error::branch car-monit-api-jdk21 requires JDK 21, runner java differs"
  exit 1
}



