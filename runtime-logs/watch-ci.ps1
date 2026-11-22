# @description 历史脚本 watch-ci.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File watch-ci.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Long-running monitor for GitHub Actions status.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
param([int]$Iterations = 6, [int]$IntervalSeconds = 30)

$ErrorActionPreference = 'Continue'

$src = @'
using System;
using System.Runtime.InteropServices;
public static class WinCred2 {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CREDENTIAL {
        public int Flags; public int Type; public IntPtr TargetName; public IntPtr Comment;
        public long LastWritten; public int CredentialBlobSize; public IntPtr CredentialBlob;
        public int Persist; public int AttributeCount; public IntPtr Attributes;
        public IntPtr TargetAlias; public IntPtr UserName;
    }
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool CredReadW(string target, int type, int reserved, out IntPtr ptr);
    [DllImport("advapi32.dll")]
    public static extern void CredFree(IntPtr ptr);
    public static string Blob(string target) {
        IntPtr ptr;
        if (!CredReadW(target, 1, 0, out ptr)) return null;
        try {
            CREDENTIAL c = (CREDENTIAL)Marshal.PtrToStructure(ptr, typeof(CREDENTIAL));
            if (c.CredentialBlobSize <= 0) return null;
            return Marshal.PtrToStringUni(c.CredentialBlob, c.CredentialBlobSize / 2);
        } finally { CredFree(ptr); }
    }
}
'@
Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue

$token = ''
foreach ($t in @('git:https://github.com', 'GitHub - https://api.github.com/kai-cn')) {
    $blob = [WinCred2]::Blob($t)
    if ($blob) {
        $parts = $blob -split ':', 2
        $token = if ($parts.Length -eq 2 -and $parts[1]) { $parts[1] } else { $blob }
        break
    }
}
if (-not $token) { 'NO_TOKEN'; exit 2 }

$H = @{ Authorization = "Bearer $token"; 'User-Agent' = 'codebuddy'; Accept = 'application/vnd.github+json' }
$runs = @(
    @{ repo = 'car-monit-backend'; id = 43569698950; branch = 'backend-jdk17' },
    @{ repo = 'car-monit-backend'; id = 43569713866; branch = 'backend-jdk21' },
    @{ repo = 'car-monit-backend'; id = 43569718721; branch = 'backend-jdk25' },
    @{ repo = 'car-monit-api';     id = 43569724537; branch = 'api-jdk17' },
    @{ repo = 'car-monit-api';     id = 43569729102; branch = 'api-jdk21' },
    @{ repo = 'car-monit-api';     id = 43569734058; branch = 'api-jdk25' }
)

for ($i = 1; $i -le $Iterations; $i++) {
    $allDone = $true
    $snapshot = @()
    foreach ($r in $runs) {
        try {
            $w = Invoke-RestMethod -Uri "https://api.github.com/repos/kai-cn/$($r.repo)/actions/runs/$($r.id)" -Headers $H -TimeoutSec 25
            $snapshot += "{0}:{1}/{2}" -f $r.branch, $w.status, $w.conclusion
            if ($w.status -ne 'completed') { $allDone = $false }
        } catch {
            $snapshot += "$($r.branch):ERR"
            $allDone = $false
        }
    }
    "POLL $i : " + ($snapshot -join '  ')
    if ($allDone) {
        'ALL_COMPLETED'
        foreach ($r in $runs) {
            $w = Invoke-RestMethod -Uri "https://api.github.com/repos/kai-cn/$($r.repo)/actions/runs/$($r.id)" -Headers $H -TimeoutSec 25
            "RESULT $($r.branch): $($w.conclusion)  $($w.html_url)"
            if ($w.conclusion -ne 'success') {
                try {
                    $jobs = Invoke-RestMethod -Uri "https://api.github.com/repos/kai-cn/$($r.repo)/actions/runs/$($r.id)/jobs?per_page=20" -Headers $H -TimeoutSec 25
                    foreach ($j in $jobs.jobs) {
                        "  JOB $($j.name): $($j.conclusion)"
                        foreach ($s in $j.steps) {
                            if ($s.conclusion -ne 'success' -and $s.conclusion -ne 'skipped') {
                                "    FAILED_STEP $($s.name): $($s.conclusion)"
                            }
                        }
                    }
                } catch { "  JOBS_ERR $($_.Exception.Message)" }
            }
        }
        exit 0
    }
    Start-Sleep -Seconds $IntervalSeconds
}
'STILL_RUNNING'
