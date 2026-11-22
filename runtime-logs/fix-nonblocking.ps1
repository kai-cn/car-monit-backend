# @description 历史脚本 fix-nonblocking.ps1：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File fix-nonblocking.ps1 [params]；参数含义见脚本原有注释。
# @dependencies Docker CLI 与已启动的守护进程
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$ErrorActionPreference = 'Stop'
$branches = @('car-monit-api-jdk17', 'car-monit-api-jdk21', 'car-monit-api-jdk25')

$smokeLines = @(
'      - name: Startup prerequisite smoke (add-opens, bytecode, delivery entries)',
'        shell: bash',
'        run: |',
'          set -euo pipefail',
"          cat > /tmp/AddOpensSmoke.java <<'JAVA_EOF'",
'          import java.lang.reflect.Method;',
'          public class AddOpensSmoke {',
'            public static void main(String[] args) throws Exception {',
'              Method m = Object.class.getDeclaredMethod("clone");',
'              m.setAccessible(true);',
'              System.out.println("add-opens is effective");',
'            }',
'          }',
'          JAVA_EOF',
'          javac -d /tmp /tmp/AddOpensSmoke.java',
'          # Orika fails at startup on JDK 17+ without this flag; prove the runner JDK enforces strong encapsulation',
'          if java -cp /tmp AddOpensSmoke >/dev/null 2>&1; then',
'            echo "::error::JDK unexpectedly allows Object#clone reflection without --add-opens"',
'            exit 1',
'          fi',
'          java --add-opens=java.base/java.lang=ALL-UNNAMED -cp /tmp AddOpensSmoke',
'          # regression guard: every delivery entry must carry the required flag',
'          for f in docker/java.Dockerfile deploy/standalone/config/java.env.example \',
'                   deploy/standalone/systemd/car-monit-api-java.service deploy/standalone/README.md; do',
'            grep -q -- ''--add-opens=java.base/java.lang=ALL-UNNAMED'' "$f" || {',
'              echo "::error::$f missing --add-opens flag"',
'              exit 1',
'            }',
'          done',
'          # compiled bytecode must match the branch JDK major version (44 + java.specification.version)',
'          SPEC=$(java -XshowSettings:properties -version 2>&1 | awk ''/java.specification.version/ {print $3}'')',
'          CLASS_FILE=$(find pro-business-api/target/classes -name "*.class" | head -1)',
'          MAJOR=$(javap -verbose "$CLASS_FILE" | awk ''/major version/ {print $3}'')',
'          EXPECTED=$((44 + SPEC))',
'          echo "java.specification.version=$SPEC class_major=$MAJOR expected=$EXPECTED"',
'          [ "$MAJOR" = "$EXPECTED" ] || { echo "::error::bytecode $MAJOR does not match JDK $SPEC"; exit 1; }',
'          echo "startup-prerequisite smoke passed"'
)

foreach ($r in $branches) {
    $root = "d:\work\IdeaProjects\$r"
    $p = "$root\.github\workflows\self-hosted-ci.yml"
    $raw = [System.IO.File]::ReadAllText($p)
    $eol = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
    $lines = @($raw -split "`r?`n")

    # 1) trigger on shared module + delivery files (line-based, EOL agnostic)
    if (-not ($raw.Contains('pro-base-common/**'))) {
        $out = @()
        foreach ($line in $lines) {
            $out += $line
            if ($line -eq '      - pro-business-api/**') {
                $out += @(
                    '      - pro-base-common/**',
                    '      - docker/java.Dockerfile',
                    '      - deploy/standalone/**',
                    '      - .github/workflows/**'
                )
            }
        }
        $lines = $out
    }

    # 2) insert smoke step after the Unit tests step (line-based)
    if (-not ($raw.Contains('Startup prerequisite smoke'))) {
        $idx = [Array]::IndexOf($lines, '      - name: Unit tests')
        if ($idx -lt 0) { throw "Unit tests anchor not found in $r" }
        $insertAt = $idx + 2
        $before = if ($insertAt -gt 0) { $lines[0..($insertAt - 1)] } else { @() }
        $after = if ($insertAt -lt $lines.Count) { $lines[$insertAt..($lines.Count - 1)] } else { @() }
        $lines = @($before) + @('') + @($smokeLines) + @($after)
    }

    $new = ($lines -join $eol)
    [System.IO.File]::WriteAllText($p, $new, (New-Object System.Text.UTF8Encoding($false)))

    # 3) _java.yml: stale Spring Boot version in comments
    $j = "$root\.github\workflows\_java.yml"
    $jt = [System.IO.File]::ReadAllText($j).Replace('Spring Boot 2.7.18', 'Spring Boot 4.1.2')
    [System.IO.File]::WriteAllText($j, $jt, (New-Object System.Text.UTF8Encoding($false)))
}
'patched: self-hosted-ci paths + smoke step + _java.yml stale version'
