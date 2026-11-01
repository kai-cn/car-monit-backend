// 来源: ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml
//       ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml
//       ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
// 职责: 登录/鉴权所需的最小查询集，SQL 与 mapper 保持一致。
// 对应关系: selectUserByUserName/selectRolePermissionByUserId/selectMenuPermsByUserId。

use chrono::NaiveDateTime;

use sqlx::{MySqlPool, Row};

use crate::domain::{SysDept, SysRole, SysUser};
use crate::error::AppError;

/// Java: selectUserByUserName（selectUserVo + where user_name = ?）
/// selectUserVo 关联 dept 与 roles；这里拆成用户主表 + 角色子查询，结果等价。
pub async fn select_user_by_user_name(
    pool: &MySqlPool,
    user_name: &str,
) -> Result<Option<SysUser>, AppError> {
    let row = sqlx::query(
        r#"
        select u.user_id, u.user_no, u.dept_id, u.user_name, u.nick_name, u.user_type,
               u.email, u.phonenumber, u.sex, u.avatar, u.password, u.status, u.del_flag,
               u.login_ip, u.login_date, u.create_by, u.create_time, u.update_by,
               u.update_time, u.remark, u.cert_entity_id, u.cert_id,
               ifnull(u.buss_id, u.user_name) as buss_id, u.buss_name, u.eps_name,
               ifnull(d.tenant_id, -1) as tenant_id, d.sub_code,
               d.parent_id as dept_parent_id, d.dept_name, d.order_num, d.leader,
               d.status as dept_status
        from sys_user u
                 left join sys_dept d on u.dept_id = d.dept_id
        where u.user_name = ?
        "#,
    )
    .bind(user_name)
    .fetch_optional(pool)
    .await?;

    let Some(row) = row else {
        return Ok(None);
    };

    let dept_id: Option<i64> = row.try_get("dept_id")?;
    let parent_id: Option<i64> = row.try_get("dept_parent_id")?;
    let dept_name: Option<String> = row.try_get("dept_name")?;
    let order_num: Option<i32> = row.try_get("order_num")?;
    let leader: Option<String> = row.try_get("leader")?;
    let dept_status: Option<String> = row.try_get("dept_status")?;
    let tenant_id: Option<i64> = row.try_get("tenant_id")?;
    let sub_code: Option<String> = row.try_get("sub_code")?;

    // Java: <association property="dept" column="dept_id">，deptId 取用户行的 dept_id。
    let dept = dept_id.map(|id| SysDept {
        dept_id: Some(id),
        parent_id,
        dept_name,
        order_num: order_num.map(|n| n.to_string()),
        leader,
        status: dept_status,
        // Java deptResult 只映射 deptId/parentId/deptName/orderNum/leader/status。
        ..Default::default()
    });

    let user_id: Option<i64> = row.try_get("user_id")?;
    let mut user = SysUser {
        user_id,
        user_no: row.try_get("user_no")?,
        dept_id,
        user_name: row.try_get("user_name")?,
        nick_name: row.try_get("nick_name")?,
        user_type: row.try_get("user_type")?,
        email: row.try_get("email")?,
        phonenumber: row.try_get("phonenumber")?,
        sex: row.try_get("sex")?,
        avatar: row.try_get("avatar")?,
        password: row.try_get("password")?,
        status: row.try_get("status")?,
        del_flag: row.try_get("del_flag")?,
        login_ip: row.try_get("login_ip")?,
        login_date: row.try_get::<Option<NaiveDateTime>, _>("login_date")?,
        create_by: row.try_get("create_by")?,
        create_time: row.try_get::<Option<NaiveDateTime>, _>("create_time")?,
        // selectUserVo 未查询 u.update_by/u.update_time。
        update_by: None,
        update_time: None,
        remark: row.try_get("remark")?,
        cert_entity_id: row.try_get("cert_entity_id")?,
        cert_id: row.try_get("cert_id")?,
        buss_id: row.try_get("buss_id")?,
        buss_name: row.try_get("buss_name")?,
        eps_name: row.try_get("eps_name")?,
        tenant_id,
        sub_code: sub_code.clone(),
        dept,
        ..Default::default()
    };

    if let Some(user_id) = user.user_id {
        // Java: <collection property="roles"> —— selectUserVo 未过滤 del_flag。
        user.roles = select_roles_for_user(pool, user_id).await?;
    }

    Ok(Some(user))
}

/// Java: selectUserVo 的 role 关联（select distinct r... where ur.user_id = ?）。
pub async fn select_roles_for_user(
    pool: &MySqlPool,
    user_id: i64,
) -> Result<Vec<SysRole>, AppError> {
    let rows = sqlx::query(
        r#"
        select distinct r.role_id, r.role_name, r.role_key, r.role_sort,
               r.data_scope, r.status
        from sys_role r
                 left join sys_user_role ur on ur.role_id = r.role_id
                 left join sys_user u on u.user_id = ur.user_id
                 left join sys_dept d on u.dept_id = d.dept_id
        where ur.user_id = ?
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await?;

    rows.into_iter()
        .map(|row| {
            let role_sort: Option<i32> = row.try_get("role_sort")?;
            Ok(SysRole {
                role_id: row.try_get("role_id")?,
                role_name: row.try_get("role_name")?,
                role_key: row.try_get("role_key")?,
                role_sort: role_sort.map(|n| n.to_string()),
                data_scope: row.try_get("data_scope")?,
                status: row.try_get("status")?,
                ..Default::default()
            })
        })
        .collect()
}

/// Java: SysPermissionService.getRolePermission -> selectRolePermissionByUserId
/// 返回 role_key（管理员在调用方短路为 "admin"）。
pub async fn select_role_keys_for_user(
    pool: &MySqlPool,
    user_id: i64,
) -> Result<Vec<String>, AppError> {
    let rows = sqlx::query(
        r#"
        select distinct r.role_key
        from sys_role r
                 left join sys_user_role ur on ur.role_id = r.role_id
                 left join sys_user u on u.user_id = ur.user_id
                 left join sys_dept d on u.dept_id = d.dept_id
        where r.del_flag = '0'
          and ur.user_id = ?
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await?;

    let mut keys: Vec<String> = Vec::new();
    for row in rows {
        let key: Option<String> = row.try_get("role_key")?;
        if let Some(key) = key.filter(|k| !k.trim().is_empty()) {
            if !keys.contains(&key) {
                keys.push(key);
            }
        }
    }
    Ok(keys)
}

/// Java: SysPermissionService.getMenuPermission -> selectMenuPermsByUserId
/// Java 可能返回 null 行；Rust 侧过滤空值（前端只使用非空权限标识）。
pub async fn select_menu_perms_for_user(
    pool: &MySqlPool,
    user_id: i64,
) -> Result<Vec<String>, AppError> {
    let rows = sqlx::query(
        r#"
        select distinct m.perms
        from sys_menu m
                 left join sys_role_menu rm on m.menu_id = rm.menu_id
                 left join sys_user_role ur on rm.role_id = ur.role_id
                 left join sys_role r on r.role_id = ur.role_id
        where m.status = '0'
          and r.status = '0'
          and ur.user_id = ?
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await?;

    let mut perms: Vec<String> = Vec::new();
    for row in rows {
        let perm: Option<String> = row.try_get("perms")?;
        if let Some(perm) = perm.filter(|p| !p.trim().is_empty()) {
            if !perms.contains(&perm) {
                perms.push(perm);
            }
        }
    }
    Ok(perms)
}
