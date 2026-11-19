#!/usr/bin/env bash
command -v cargo >/dev/null 2>&1 && cargo --version || echo NO_CARGO
docker ps --format '{{.Names}} {{.Status}}'
ss -ltn 2>/dev/null | grep -E ':3306|:3307' || echo NO_MYSQL_PORT
