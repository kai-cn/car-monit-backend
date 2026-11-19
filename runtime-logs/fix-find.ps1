# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$branches = @('car-monit-api-jdk17', 'car-monit-api-jdk21', 'car-monit-api-jdk25')
foreach ($r in $branches) {
    $p = "d:\work\IdeaProjects\$r\.github\workflows\self-hosted-ci.yml"
    $t = [System.IO.File]::ReadAllText($p)
    $t = $t.Replace(
        'CLASS_FILE=$(find pro-business-api/target/classes -name "*.class" | head -1)',
        "CLASS_FILE=`$(find pro-business-api/target/classes -name '*.class' -print -quit)")
    [System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))
}
'patched find -print -quit (avoid SIGPIPE under pipefail)'
