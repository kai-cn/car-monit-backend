-- 0001: 基线校验
--
-- 本仓库不包含 carmonitdb 的全量 DDL（由 DBA / 现有部署提供 carmonitdb.sql）。
-- 该迁移不修改结构，只校验连接的是包含若依基础表的业务库，避免把迁移邮戳打到错误的 schema 上。
SELECT 1 FROM sys_user LIMIT 1;
