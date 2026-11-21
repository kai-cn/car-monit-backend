#!/bin/sh
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
ORACLE_HOME=/home/oracle/app/oracle/product/11.2.0/dbhome_2
ORACLE_SID=helowin
PATH=$ORACLE_HOME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export ORACLE_HOME ORACLE_SID PATH
cd /tmp
sqlplus -S / as sysdba @/tmp/oracle-probe.sql
