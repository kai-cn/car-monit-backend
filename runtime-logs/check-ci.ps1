# @description 历史脚本 check-ci.ps1：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage powershell -File check-ci.ps1 [params]；参数含义见脚本原有注释。
# @dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
$ErrorActionPreference = 'Continue'

function Get-GcmCredential {
    # Fixed account (kai-cn) cached token; avoids GCM account picker dialogs.
    $tok = & python -c "import sys; sys.path.insert(0, r'D:\work\runtime-logs'); import gh_cred; sys.stdout.write(gh_cred.get_token())"
    if ($LASTEXITCODE -ne 0) { return '' }
    return $tok
}

$src = @'
using System;
using System.Runtime.InteropServices;
public static class WinCred {
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

$token = Get-GcmCredential
if (-not $token) {
    foreach ($t in @('git:https://github.com', 'GitHub - https://api.github.com/kai-cn')) {
        $blob = [WinCred]::Blob($t)
        if ($blob) {
            # GCM blobs are usually "username:token" or plain token
            $parts = $blob -split ':', 2
            $token = if ($parts.Length -eq 2 -and $parts[1]) { $parts[1] } else { $blob }
            break
        }
    }
}
if (-not $token) { 'NO_TOKEN'; exit 2 }

$H = @{ Authorization = "Bearer $token"; 'User-Agent' = 'codebuddy'; Accept = 'application/vnd.github+json' }
foreach ($repo in @('car-monit-backend', 'car-monit-api')) {
    try {
        $r = Invoke-RestMethod -Uri "https://api.github.com/repos/kai-cn/$repo/actions/runs?per_page=8" -Headers $H -TimeoutSec 30
        "$repo total_runs=$($r.total_count)"
        foreach ($w in $r.workflow_runs) {
            "  id=$($w.id) | $($w.name) | $($w.head_branch) | status=$($w.status) | conclusion=$($w.conclusion) | sha=$($w.head_sha.Substring(0,7)) | created=$($w.created_at)"
        }
    } catch {
        "$repo API_ERR $($_.Exception.Message)"
    }
}
