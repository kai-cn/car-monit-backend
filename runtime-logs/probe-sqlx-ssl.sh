#!/usr/bin/env bash
grep -R "ssl-mode" /home/dev/.cargo/registry/src/*/sqlx-core-*/src/mysql 2>/dev/null | head -20 || true
