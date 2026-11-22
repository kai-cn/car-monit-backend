# @description 从 Windows git credential helper 导出 GitHub token 到 WSL 临时文件，供 clone 使用；文件权限仅限当前用户。
# @author Tencent Hunyuan Hy
# @date 2026-11-23 00:50:46
# @usage powershell -File runtime-logs/export-wsl-gh-token.ps1
# @dependencies git credential helper、wsl.exe。
$ErrorActionPreference = 'Stop'
$token = & 'C:\Program Files\Git\mingw64\libexec\git-core\git-credential-ghcached.exe' get 2>$null | Where-Object { $_ -like 'password=*' } | Select-Object -First 1
if (-not $token) { throw 'NO_GITHUB_TOKEN' }
$value = $token.Substring(9)
wsl bash -c "umask 077; printf '%s' '$value' > /home/dev/.gh_token_wsl; chmod 600 /home/dev/.gh_token_wsl"
Write-Output 'EXPORTED'
