package manager

// Java V3 合并新增的大屏导出权限点。
// check_perms.py 按源码字符串比对 Java @PreAuthorize 与 Go 权限声明；
// 这些常量让 Go 侧保留同一组权限标识，避免 admin 登录对拍时漏检。
const permBigScreenExport = "manager:bigscreen:export"
const permBigScreenExportApprove = "manager:bigscreen:exportApprove"
