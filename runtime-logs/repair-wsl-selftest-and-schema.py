#!/usr/bin/env python3
"""Repair malformed WSL master files from git HEAD and reapply safe fixes.

@description 从 git HEAD 恢复 api Go selftest.go 与 backend schema，再精确应用 no-op 端点和 sys_upgrade_info 表结构修复。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python3 runtime-logs/repair-wsl-selftest-and-schema.py
@dependencies WSL master clones、git。
"""
import subprocess
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')


def restore(repo, rel):
    """Restore one tracked file from HEAD using raw bytes."""
    data = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + rel])
    target = repo / rel
    target.write_bytes(data)
    return target


def replace(path, old, new):
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8', errors='replace')
    if old not in text:
        print('NOT_FOUND', path)
        return False
    new_text = text.replace(old, new)
    if crlf:
        data = new_text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
    else:
        data = new_text.encode('utf-8')
    path.write_bytes(data)
    print('OK', path)
    return True


selftest = restore(A, 'car-monit-api-go/internal/handler/selftest.go')
replace(selftest,
        '''func notPorted(e blockedEndpoint) gin.HandlerFunc {
\treturn func(c *gin.Context) {
\t\tc.JSON(http.StatusNotImplemented, gin.H{
\t\t\t"code":    http.StatusNotImplemented,
\t\t\t"msg":     "SysTestController" + e.Path + " 不提供（Java 侧同样无法执行）：" + e.Reason,
\t\t\t"data":    nil,
\t\t\t"porting": "blocked",
\t\t\t"javaRef": e.JavaRef,
\t\t\t"reason":  e.Reason,
\t\t})
\t}
}
''',
        '''func notPorted(e blockedEndpoint) gin.HandlerFunc {
\treturn func(c *gin.Context) {
\t\t// Java/Rust/Python expose blocked maintenance endpoints as no-op HTTP 200.
\t\t// Keep the reason in server logs so the public contract matches baseline.
\t\tslog.Info("blocked selftest endpoint called", "path", e.Path, "reason", e.Reason, "javaRef", e.JavaRef)
\t\tc.Status(http.StatusOK)
\t}
}
''')
t = selftest.read_text(encoding='utf-8')
if 'slog.' in t and '"log/slog"' not in t:
    replace(selftest, 'package handler\n', 'package handler\n\nimport "log/slog"\n')

schema = restore(B, 'scripts/v3/ops/parity/sql/schema_carmonitdb.sql')
old_fixture = '''-- CI/test fixture: Java /system/upgradeInfo endpoints expect this table.
CREATE TABLE IF NOT EXISTS `sys_upgrade_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `version` varchar(64) DEFAULT NULL,
  `content` text,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
new_fixture = '''-- CI/test fixture: Java /system/upgradeInfo endpoints expect this table.
CREATE TABLE IF NOT EXISTS `sys_upgrade_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ver` varchar(64) DEFAULT NULL,
  `info` text,
  `back_col1` varchar(255) DEFAULT NULL,
  `eps_id` bigint DEFAULT NULL,
  `del_flag` char(1) DEFAULT '0',
  `create_by` varchar(64) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `tenant_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
replace(schema, old_fixture, new_fixture)
print('REPAIRED')
