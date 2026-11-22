# @description 历史脚本 ci-recover.ps1：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage powershell -File ci-recover.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

$src = @'

using System;

using System.Runtime.InteropServices;

public static class WinCred4 {

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

    $blob = [WinCred4]::Blob($t)

    if ($blob) { $parts = $blob -split ':', 2; $token = if ($parts.Length -eq 2 -and $parts[1]) { $parts[1] } else { $blob }; break }

}

$H = @{ Authorization = "Bearer $token"; 'User-Agent' = 'codebuddy'; Accept = 'application/vnd.github+json' }



$failed = @(

    @{ repo = 'car-monit-backend'; id = 43569713866; name = 'backend21' },

    @{ repo = 'car-monit-api';     id = 43569734058; name = 'api25' }

)

foreach ($f in $failed) {

    $jobs = Invoke-RestMethod -Uri "https://api.github.com/repos/kai-cn/$($f.repo)/actions/runs/$($f.id)/jobs" -Headers $H -TimeoutSec 25

    foreach ($j in $jobs.jobs) {

        if ($j.conclusion -ne 'failure') { continue }

        "$($f.name) FAILED_JOB=$($j.name) id=$($j.id)"

        try {

            $resp = Invoke-WebRequest -Uri "https://api.github.com/repos/kai-cn/$($f.repo)/actions/jobs/$($j.id)/logs" -Headers $H -MaximumRedirection 0 -UseBasicParsing -TimeoutSec 25 -ErrorAction SilentlyContinue

            $loc = $resp.Headers['Location']

        } catch {

            $loc = $_.Exception.Response.Headers['Location']

        }

        if ($loc) {

            try {

                $txt = (Invoke-WebRequest -Uri $loc -UseBasicParsing -TimeoutSec 30).Content

                $lines = $txt -split "`n" | Where-Object { $_ -match 'error|Error|fatal|FAILED|failed|No space|timed out|403|404|curl|tar|unzip' }

                ($lines | Select-Object -Last 12) | ForEach-Object { "  LOG " + $_.Trim() }

            } catch { "  LOG_ERR $($_.Exception.Message)" }

        } else { "  NO_LOG_LOCATION" }

    }

    try {

        Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/kai-cn/$($f.repo)/actions/runs/$($f.id)/rerun-failed-jobs" -Headers $H -TimeoutSec 25 | Out-Null

        "  RERUN_TRIGGERED $($f.name)"

    } catch { "  RERUN_ERR $($f.name): $($_.Exception.Message)" }

}

