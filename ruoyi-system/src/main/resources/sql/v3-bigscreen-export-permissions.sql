-- =============================================================================
-- 大屏 V3 导出权限初始化（MySQL / RuoYi sys_menu + sys_role_menu）
--
-- 背景：BigScreenExportController 的 /display、/full 已加 @PreAuthorize：
--   /display 需要 manager:bigscreen:export
--   /full    需要 manager:bigscreen:export + manager:bigscreen:exportFull
--   /approvals/** 需要 manager:bigscreen:exportApprove
-- 上线前必须执行本脚本，否则非超管角色即使登录也点不了导出。
--
-- 幂等：重复执行不会重复插入菜单或授权。
-- 说明：userId=1 的超管持有 *:*:*，不受菜单授权影响；下面仍补齐授权，便于审计。
--
-- 执行后校验：
--   SELECT menu_id, menu_name, perms FROM sys_menu
--    WHERE perms LIKE 'manager:bigscreen:export%';
--   SELECT r.role_key, m.perms FROM sys_role_menu rm
--     JOIN sys_role r ON r.role_id = rm.role_id
--     JOIN sys_menu m ON m.menu_id = rm.menu_id
--    WHERE m.perms LIKE 'manager:bigscreen:export%';
-- =============================================================================

SET NAMES utf8mb4;

-- 挂到现有“大屏”目录下；找不到则挂根目录（parent_id=0）
SET @parent_id := (
    SELECT menu_id FROM sys_menu
     WHERE menu_type = 'M' AND (menu_name = '大屏' OR path = 'bigscreen')
     ORDER BY menu_id LIMIT 1
);
SET @parent_id := IFNULL(@parent_id, 0);

-- 1) 菜单：大屏导出
INSERT INTO sys_menu
    (menu_name, parent_id, order_num, path, component, query, is_frame, is_cache,
     menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
SELECT '大屏导出', @parent_id, 90, 'bigscreen-export', 'manager/bigscreen/export/index', '', 1, 0,
       'C', '0', '0', 'manager:bigscreen:export', 'download', 'admin', NOW(), '', NULL,
       '大屏 V3 导出入口（展示字段/全字段）'
  FROM DUAL
 WHERE NOT EXISTS (
       SELECT 1 FROM sys_menu
        WHERE perms = 'manager:bigscreen:export' AND menu_type = 'C'
 );
SET @export_menu_id := (
    SELECT menu_id FROM sys_menu
     WHERE perms = 'manager:bigscreen:export' AND menu_type = 'C'
     ORDER BY menu_id LIMIT 1
);

-- 2) 按钮：全字段导出
INSERT INTO sys_menu
    (menu_name, parent_id, order_num, path, component, query, is_frame, is_cache,
     menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
SELECT '全字段导出', @export_menu_id, 1, '', '', '', 1, 0,
       'F', '0', '0', 'manager:bigscreen:exportFull', '#', 'admin', NOW(), '', NULL,
       '全字段海量导出（GaussDB 游标）'
  FROM DUAL
 WHERE NOT EXISTS (
       SELECT 1 FROM sys_menu
        WHERE perms = 'manager:bigscreen:exportFull'
 );
SET @export_full_menu_id := (
    SELECT menu_id FROM sys_menu WHERE perms = 'manager:bigscreen:exportFull' ORDER BY menu_id LIMIT 1
);

-- 3) 按钮：导出审批
INSERT INTO sys_menu
    (menu_name, parent_id, order_num, path, component, query, is_frame, is_cache,
     menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
SELECT '导出审批', @export_menu_id, 2, '', '', '', 1, 0,
       'F', '0', '0', 'manager:bigscreen:exportApprove', '#', 'admin', NOW(), '', NULL,
       '全字段导出审批（通过/驳回）'
  FROM DUAL
 WHERE NOT EXISTS (
       SELECT 1 FROM sys_menu
        WHERE perms = 'manager:bigscreen:exportApprove'
 );
SET @export_approve_menu_id := (
    SELECT menu_id FROM sys_menu WHERE perms = 'manager:bigscreen:exportApprove' ORDER BY menu_id LIMIT 1
);

-- 4) 角色授权
--    默认只授予超管角色；如需授予业务角色，把角色标识加入下面的变量（逗号分隔），
--    例如：SET @grant_role_keys := 'admin,bigscreen_export';
SET @grant_role_keys := 'admin';

INSERT INTO sys_role_menu (role_id, menu_id)
SELECT r.role_id, m.menu_id
  FROM sys_role r
  JOIN sys_menu m
    ON m.menu_id IN (@export_menu_id, @export_full_menu_id, @export_approve_menu_id)
 WHERE r.del_flag = '0'
   AND FIND_IN_SET(r.role_key, @grant_role_keys) > 0
   AND NOT EXISTS (
       SELECT 1 FROM sys_role_menu rm
        WHERE rm.role_id = r.role_id AND rm.menu_id = m.menu_id
 );

-- 5) 结果核对
SELECT menu_id, menu_name, parent_id, menu_type, perms
  FROM sys_menu
 WHERE perms LIKE 'manager:bigscreen:export%'
 ORDER BY menu_id;

SELECT r.role_id, r.role_key, r.role_name, m.perms
  FROM sys_role_menu rm
  JOIN sys_role r ON r.role_id = rm.role_id
  JOIN sys_menu m ON m.menu_id = rm.menu_id
 WHERE m.perms LIKE 'manager:bigscreen:export%'
 ORDER BY r.role_id, m.perms;
