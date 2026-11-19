#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Validation helper; exits nonzero or reports evidence when an invariant is broken.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Inspect api application.yml middleware blocks to judge startup hard-dependencies."""
import subprocess

repo = r'D:\work\IdeaProjects\car-monit-api-java-V3'
ref = 'refs/remotes/origin/car-monit-api-jdk25:pro-business-api/src/main/resources/application.yml'
yml = subprocess.run(['git', '-C', repo, 'show', ref], capture_output=True, text=True,
                     encoding='utf-8', errors='replace').stdout
lines = yml.splitlines()
# locate top-level middleware sections and print until next top-level key
targets = ('kafka:', 'pulsar:', 'rabbitmq:', 'elasticsearch:', 'optimization:')
i = 0
while i < len(lines):
    ln = lines[i]
    if ln.rstrip() in targets:
        key = ln.rstrip()
        print('=' * 30, key)
        j = i + 1
        while j < len(lines) and (lines[j].startswith(' ') or lines[j].strip() == ''):
            if lines[j].strip():
                print('   ', lines[j].rstrip()[:120])
            j += 1
            if j - i > 40:
                break
        i = j
    else:
        i += 1
