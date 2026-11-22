#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# Generate self-hosted-ci.yml for all six JDK branches, replacing the failing
# actions/setup-java@v4 step with self-contained pinned toolchain provisioning.
import os

ROOT = "D:/work/IdeaProjects"

CFG = {
    "17": {"full": "17.0.21+9", "tag": "jdk-17.0.21%2B9",
           "tar": "OpenJDK17U-jdk_x64_linux_hotspot_17.0.21_9.tar.gz"},
    "21": {"full": "21.0.13+9", "tag": "jdk-21.0.13%2B9",
           "tar": "OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz"},
    "25": {"full": "25.0.5+8", "tag": "jdk-25.0.5%2B8",
           "tar": "OpenJDK25U-jdk_x64_linux_hotspot_25.0.5_8.tar.gz"},
}

ENV_STEP = """      - name: Runner environment
        run: |
          set +e
          echo "runner=${RUNNER_NAME} os=${RUNNER_OS} arch=${RUNNER_ARCH}"
          uname -a
          echo "cpus=$(nproc)"
          free -m | head -2
          echo "node=$(node -v 2>&1)  user=$(id -un)  HOME=${HOME}"
          echo "JAVA_HOME=${JAVA_HOME:-<unset>}"
          command -v java && java -version 2>&1 | head -3
          command -v mvn && mvn -v 2>&1 | head -3
"""

CHECKOUT_STEP = """      - name: Checkout
        uses: actions/checkout@v4
"""

JDK_STEP = """      - name: Setup JDK __MAJOR__ (pinned Temurin __FULL__, self-hosted)
        shell: bash
        run: |
          set -euo pipefail
          JDK_MAJOR="__MAJOR__"
          JDK_FULL="__FULL__"
          JDK_TARBALL="__TARBALL__"
          GH_TAG="__GHTAG__"
          CACHE_ROOT="${HOME}/.cache/ci-toolchain"
          STAGE_DIR="/mnt/d/work/runtime-logs/ci-toolchain"
          JDK_HOME="${CACHE_ROOT}/jdk-${JDK_FULL}"

          if [ -x "${JDK_HOME}/bin/java" ]; then
            echo ">> reuse cached JDK ${JDK_FULL} at ${JDK_HOME}"
          else
            mkdir -p "${CACHE_ROOT}"
            TGZ="${CACHE_ROOT}/${JDK_TARBALL}.part"
            rm -f "${TGZ}"
            # Priority 1: tarball pre-staged on the Windows D: drive (verified offline).
            # Priority 2/3: mirrors. Every candidate is gzip-checked before extraction,
            # because a truncated download otherwise fails later with an opaque tar error.
            staged="${STAGE_DIR}/${JDK_TARBALL}"
            good=0
            if [ -s "${staged}" ] && gzip -t "${staged}" >/dev/null 2>&1; then
              echo ">> using pre-staged tarball ${staged}"
              cp "${staged}" "${TGZ}"
              good=1
            else
              [ -e "${staged}" ] && echo "::warning::staged tarball ${staged} missing or corrupt, using mirrors"
              urls=(
                "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/${JDK_MAJOR}/jdk/x64/linux/${JDK_TARBALL}"
                "https://github.com/adoptium/temurin${JDK_MAJOR}-binaries/releases/download/${GH_TAG}/${JDK_TARBALL}"
              )
              for u in "${urls[@]}"; do
                echo ">> fetching ${u}"
                if curl -fsSL --retry 2 --retry-all-errors --connect-timeout 20 --max-time 900 -o "${TGZ}" "${u}" \
                   && gzip -t "${TGZ}" >/dev/null 2>&1; then
                  good=1
                  break
                fi
                echo "::warning::download failed integrity check: ${u}" >&2
                rm -f "${TGZ}"
              done
            fi
            if [ "${good}" -ne 1 ]; then
              echo "::error::no valid Temurin ${JDK_FULL} tarball from staged path or mirrors"
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
"""

MAVEN_STEP = """      - name: Setup Maven 3.9.9 (self-hosted, with system fallback)
        shell: bash
        run: |
          set -euo pipefail
          MVN_VER="3.9.9"
          MVN_TARBALL="apache-maven-${MVN_VER}-bin.tar.gz"
          CACHE_ROOT="${HOME}/.cache/ci-toolchain"
          STAGE_DIR="/mnt/d/work/runtime-logs/ci-toolchain"
          MVN_HOME="${CACHE_ROOT}/apache-maven-${MVN_VER}"

          if [ -x "${MVN_HOME}/bin/mvn" ]; then
            echo ">> reuse cached Maven ${MVN_VER} at ${MVN_HOME}"
          else
            mkdir -p "${CACHE_ROOT}"
            TGZ="${CACHE_ROOT}/${MVN_TARBALL}.part"
            rm -f "${TGZ}"
            staged="${STAGE_DIR}/${MVN_TARBALL}"
            good=0
            if [ -s "${staged}" ] && gzip -t "${staged}" >/dev/null 2>&1; then
              echo ">> using pre-staged tarball ${staged}"
              cp "${staged}" "${TGZ}"
              good=1
            else
              urls=(
                "https://repo.huaweicloud.com/apache/maven/maven-3/${MVN_VER}/binaries/${MVN_TARBALL}"
                "https://archive.apache.org/dist/maven/maven-3/${MVN_VER}/binaries/${MVN_TARBALL}"
              )
              for u in "${urls[@]}"; do
                echo ">> fetching ${u}"
                if curl -fsSL --retry 2 --retry-all-errors --connect-timeout 20 --max-time 600 -o "${TGZ}" "${u}" \
                   && gzip -t "${TGZ}" >/dev/null 2>&1; then
                  good=1
                  break
                fi
                echo "::warning::download failed integrity check: ${u}" >&2
                rm -f "${TGZ}"
              done
            fi
            if [ "${good}" -eq 1 ]; then
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
              echo "::error::Maven ${MVN_VER} unavailable and no system mvn on PATH"
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
"""

ASSERT_STEP = """      - name: Assert toolchain matches branch
        run: |
          set -euo pipefail
          JAVA_OUT="$(java -version 2>&1)"
          echo "${JAVA_OUT}"
          mvn -v
          # here-string avoids SIGPIPE false-negatives that ``| grep -q`` triggers under pipefail
          grep -qE 'version "__MAJOR__\\.' <<< "${JAVA_OUT}" || {
            echo "::error::branch __BRANCH__ requires JDK __MAJOR__, runner java differs"
            exit 1
          }
"""

ENSURE_K3D = """      - name: Ensure k3d cluster is running (WSL restart resilience)
        run: |
          set -euo pipefail
          if ! docker info >/dev/null 2>&1; then
            echo ">> docker daemon down, attempting to start it"
            sudo -n systemctl start docker 2>/dev/null || true
            for i in $(seq 1 12); do
              docker info >/dev/null 2>&1 && break
              sleep 5
            done
          fi
          docker info >/dev/null 2>&1 || {
            echo "::error::docker daemon unavailable on the self-hosted runner"
            exit 1
          }
          RUNNING="$(docker ps --format '{{.Names}}' 2>/dev/null || true)"
          PRESENT="$(docker ps -a --format '{{.Names}}' 2>/dev/null || true)"
          for c in k3d-v3-server-0 k3d-v3-agent-0 k3d-v3-agent-1; do
            if grep -Fxq -- "${c}" <<< "${RUNNING}"; then
              echo "${c}: already running"
            elif grep -Fxq -- "${c}" <<< "${PRESENT}"; then
              echo "${c}: starting"
              docker start "${c}" || true
            else
              echo "::warning::${c}: container not found (cluster may need recreation)"
            fi
          done
          for i in $(seq 1 24); do
            if docker exec k3d-v3-server-0 kubectl get nodes >/dev/null 2>&1; then
              echo "k3d cluster API ready"
              exit 0
            fi
            sleep 5
          done
          echo "::error::k3d cluster API did not become ready within 120s"
          exit 1
"""


def build(repo, major, old_text):
    prefix = old_text.split("\njobs:\n", 1)[0].rstrip("\n")
    # Strip any pre-existing top-level `env:` block so regeneration is idempotent.
    kept, skipping = [], False
    for line in prefix.split("\n"):
        if line == "env:":
            skipping = True
            continue
        if skipping:
            if line.startswith(" ") or line.startswith("\t") or line.strip() == "" or line.startswith("#"):
                continue
            skipping = False
        kept.append(line)
    prefix = "\n".join(kept).rstrip("\n")
    # insert a global memory cap right after the permissions block
    prefix = prefix + "\n\nenv:\n  MAVEN_OPTS: -Xmx768m\n"

    c = CFG[major]
    branch = f"car-monit-{repo}-jdk{major}"
    label = "wsl-k3s" if repo == "backend" else "wsl-k3s-api"
    probe = "v3-ci-probe" if repo == "backend" else "v3-api-ci-probe"
    if repo == "backend":
        compile_step = "      - name: Compile V3 modules\n        run: mvn -B -q -DskipTests -pl ruoyi-common,ruoyi-system,ruoyi-framework,ruoyi-admin -am compile\n"
        test_step = "      - name: Unit tests\n        run: mvn -B -q -pl ruoyi-common,ruoyi-system -am test\n"
    else:
        compile_step = "      - name: Compile V3 api module\n        run: mvn -B -q -DskipTests -pl pro-business-api -am compile\n"
        test_step = "      - name: Unit tests\n        run: mvn -B -q -DskipTests=false -pl pro-business-api -am test\n"

    jdk = (JDK_STEP.replace("__MAJOR__", major).replace("__FULL__", c["full"])
           .replace("__TARBALL__", c["tar"]).replace("__GHTAG__", c["tag"]))
    assertion = (ASSERT_STEP.replace("__MAJOR__", major).replace("__BRANCH__", branch))

    steps = (ENV_STEP + "\n" + CHECKOUT_STEP + "\n" + jdk + "\n" + MAVEN_STEP + "\n"
             + assertion + "\n" + compile_step + "\n" + test_step)

    jobs = f"""
jobs:
  build:
    name: compile-and-test
    runs-on: [self-hosted, linux, x64, {label}]
    timeout-minutes: 45
    steps:
{steps}
  deploy:
    name: deploy-to-k3s
    needs: build
    runs-on: [self-hosted, linux, x64, {label}]
    timeout-minutes: 15
    steps:
{ENSURE_K3D}
      - name: Verify cluster (1 control-plane + 2 agents)
        run: docker exec k3d-v3-server-0 kubectl get nodes

      - name: Roll out demo workload on 3 nodes
        run: |
          docker exec k3d-v3-server-0 kubectl create deployment {probe} \\
            --image=rancher/mirrored-pause:3.6 --replicas=3 \\
            --dry-run=client -o yaml | docker exec -i k3d-v3-server-0 kubectl apply -f -
          docker exec k3d-v3-server-0 kubectl rollout status deployment/{probe} --timeout=240s
          docker exec k3d-v3-server-0 kubectl get pods -l app={probe} -o wide
"""
    return prefix + "\n" + jobs.lstrip("\n")


for repo in ("backend", "api"):
    for major in ("17", "21", "25"):
        path = os.path.join(ROOT, f"car-monit-{repo}-jdk{major}", ".github", "workflows", "self-hosted-ci.yml")
        with open(path, "r", encoding="utf-8", newline="") as f:
            old = f.read().replace("\r\n", "\n")
        new = build(repo, major, old)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("WROTE", path, len(new), "bytes")
