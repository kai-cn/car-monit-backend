#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Add concise purpose/usage/safety headers to operational scripts created in this session."""
from pathlib import Path

ROOT = Path(r'D:\work\runtime-logs')

HEADERS = {
    'fetch-remote-file.ps1': '''# Fetch a single file from a remote GitHub branch via the REST contents API.
# Usage: fetch-remote-file.ps1 -Repo <short-repo> -Branch <branch> -Path <repo-path> -Out <local-file>
# Token is read from git credential helper by gh_api.ps1; never echoed or persisted.''',
    'put-remote-file.ps1': '''# Create/update a single file on a remote GitHub branch via the REST contents API.
# Usage: put-remote-file.ps1 -Repo <owner/repo> -Branch <branch> -Path <repo-path> -Src <local-file> -Message <commit-msg>
# Reads the existing blob SHA when present so updates do not rewrite history; 404 means create new file.''',
    'copy-remote-file.ps1': '''# Copy one file between branches of the same repository through the GitHub API.
# Usage: copy-remote-file.ps1 -Repo <short-repo> -SrcBranch <branch> -DstBranch <branch> -Path <repo-path>
# Binary-safe: the file is fetched to a temp file and PUT as base64 (needed for .gz fixtures).''',
    'optimize-workflows-cloud.ps1': '''# Performance pass over every workflow on every branch of one repository.
# Usage: optimize-workflows-cloud.ps1 -RepoFull <owner/repo>
# Changes: cancel superseded runs, run parity matrix in parallel, fastest artifact compression,
# and cache: maven for setup-java jobs. Security invariants are checked separately by
# verify_remote_hardening.py after this script runs.''',
    'add-maven-cache-cloud.ps1': '''# Add an explicit ~/.m2/repository cache step to Maven-based workflows that lack one.
# Usage: add-maven-cache-cloud.ps1 -RepoFull <owner/repo>
# Skips workflows already using actions/cache or setup-java cache: maven.
# Cache key uses hashFiles('**/pom.xml'), restoring the latest compatible dependency cache.''',
    'sync-branches.ps1': '''# Synchronize every Windows car-monit-* worktree with its fetched remote tracking branch.
# Fast-forwards when possible; merges with -X theirs when local and remote diverged.
# Dirty worktrees (tracked user changes) are skipped and never overwritten.''',
    'sync-wsl-repos.sh': '''# Synchronize WSL standalone git repos with their fetched origin refs.
# Requires core.quotePath=false and core.autocrlf=false (Windows/WSL line-ending noise).
# Untracked files are preserved; dirty tracked worktrees are skipped.''',
    'sync-wsl-repos2.sh': '''# Second-pass WSL sync: removes untracked native-image hint files that became tracked
# on the remote branch, then repeats the fast-forward/merge logic of sync-wsl-repos.sh.''',
    'reset-wsl-worktrees.sh': '''# Restore WSL working trees from the git index using NUL-safe path iteration.
# Used only to normalize CRLF/LF drift introduced by copying from Windows; does not touch untracked files.''',
    'sync-status-all.ps1': '''# Inventory Windows and WSL car-monit-* repositories: branch name and dirty-file count.
# Read-only diagnostic; safe to run before any sync or batch edit.''',
    'wsl-status.sh': '''# Read-only branch/dirty inventory for WSL car-monit-* repositories.''',
    'probe-wsl-eol.sh': '''# Diagnose WSL line-ending drift: compares worktree/index/HEAD blob hashes for one file.''',
    'probe-dirty.sh': '''# Show the first dirty path and its index/worktree attributes (diagnostic only).''',
    'probe-wsl-ff.sh': '''# Diagnose why a WSL fast-forward failed (ahead/behind counts + git error).''',
    'probe-wsl-ff.sh.bak': '''# Diagnose why a WSL fast-forward failed (ahead/behind counts + git error).''',
    'v3-native-build-measured.sh': '''# Build a native image entirely in WSL/ext4 with the pinned Linux Maven, wrapped by
# /usr/bin/time -v so wall time, CPU%, and peak RSS are recorded as evidence.
# Usage: v3-native-build-measured.sh <api|backend> <jdk> <repo-name> <label> [mandrel-version]
# IMPORTANT: stop mysql_wsl/opengauss before building; native-image needs >10 GB RAM.''',
    'v3-native-build-fast.sh': '''# Experimental faster native build: applies native-flink-exclude in both reactor stages
# and omits the second `clean`, saving ~2% wall time. Use only when the jar is rebuilt from clean sources.''',
    'v3-native-build-fast-measured.sh': '''# Resource-measuring wrapper for v3-native-build-fast.sh.''',
    'v3-compare-business.sh': '''# Native vs JVM multi-endpoint business-integrity comparison.
# Usage: v3-compare-business.sh --app <api|backend> --native <elf> --jar <jar> --java <java> --label <name>
# Injects DB credentials from container env at runtime (never persisted); compares exact bytes
# and JSON semantics with volatile keys removed; NONDET never exempts a status mismatch.''',
    'v3-probe-http.sh': '''# Start a native ELF or fat jar, wait for a port, and probe one real business endpoint.
# Supports both native binaries and `java -jar`; used as the fast post-build smoke test.''',
    'v3-verify-jdk-matrix.sh': '''# Reproduce startup + business-endpoint verification for every existing JDK artifact.
# Builds are NOT performed here; it runs the corrected runners/probes against current worktrees.''',
    'v3-port-jdk25-native-config.py': '''# Port the proven JDK25 native-image build tweaks (plugin version/class-init args)
# into Boot4 JDK17/21 module poms without overwriting unrelated configuration.''',
}

def add_header(path: Path, header: str):
    text = path.read_text(encoding='utf-8', errors='replace')
    if header.splitlines()[0] in text:
        return False
    shebang = ''
    rest = text
    if text.startswith('#!'):
        first, _, rest = text.partition('\n')
        shebang = first + '\n'
    path.write_text(shebang + header + '\n' + rest.lstrip('\n'), encoding='utf-8')
    return True

changed = []
for name, header in HEADERS.items():
    p = ROOT / name
    if p.exists() and add_header(p, header):
        changed.append(name)
print('annotated', len(changed), 'scripts:', ', '.join(changed))
