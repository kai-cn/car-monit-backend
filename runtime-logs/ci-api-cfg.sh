#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
docker exec k3d-v3-server-0 kubectl get deploy car-monit-api -o yaml 2>/dev/null \
  | grep -E 'master.url|driverClassName|p6spy|SPRING_DATASOURCE|TRAFFIC_API_INTERNAL_TOKEN|TRAFFIC_INTERNAL_TOKEN|EXPORT_|ELASTICSEARCH_HOST|SPRING_KAFKA_BOOTSTRAP_SERVERS|SPRING_DATA_REDIS' | head -30
