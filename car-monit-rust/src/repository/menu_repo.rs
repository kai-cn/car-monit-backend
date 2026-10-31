// 来源: ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
// 职责: 菜单树查询（selectMenuTreeAll / selectMenuTreeByUserId）。
// 对应关系: 列与 SysMenuResult 对齐。

use chrono::NaiveDateTime;
use sqlx::{MySqlPool, Row};

use crate::domain::SysMenu;
use crate::error::AppError;

fn map_menu(row: &sqlx::mysql::MySqlRow) -> Result<SysMenu, AppError> {
    Ok(SysMenu {
        menu_id: row.try_get("menu_id")?,
        parent_id: row.try_get("parent_id")?,
        menu_name: row.try_get("menu_name")?,
        path: row.try_get("path")?,
        component: row.try_get("component")?,
        visible: row.try_get("visible")?,
        status: row.try_get("status")?,
        perms: row.try_get("perms")?,
        // DB 里是 INT，Java 实体是 String，MyBatis 自动转换；这里显式转换。
        is_frame: row
            .try_get::<Option<i64>, _>("is_frame")?
            .map(|n| n.to_string()),
        is_cache: row
            .try_get::<Option<i64>, _>("is_cache")?
            .map(|n| n.to_string()),
        menu_type: row.try_get("menu_type")?,
        icon: row.try_get("icon")?,
        order_num: row
            .try_get::<Option<i32>, _>("order_num")?
            .map(|n| n.to_string()),
        create_time: row.try_get::<Option<NaiveDateTime>, _>("create_time")?,
        ..Default::default()
    })
}

/// Java: selectMenuTreeAll —— 管理员：全部目录/菜单，按 parent_id、order_num 排序。
pub async fn select_menu_tree_all(pool: &MySqlPool) -> Result<Vec<SysMenu>, AppError> {
    let rows = sqlx::query(
        r#"
        select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component,
               m.visible, m.status, ifnull(m.perms, '') as perms, m.is_frame,
               m.is_cache, m.menu_type, m.icon, m.order_num, m.create_time
        from sys_menu m
        where m.menu_type in ('M', 'C')
          and m.status = 0
        order by m.parent_id, m.order_num
        "#,
    )
    .fetch_all(pool)
    .await?;

    rows.iter().map(map_menu).collect()
}

/// Java: selectMenuTreeByUserId —— 普通用户：仅已分配且角色启用的目录/菜单。
pub async fn select_menu_tree_by_user_id(
    pool: &MySqlPool,
    user_id: i64,
) -> Result<Vec<SysMenu>, AppError> {
    let rows = sqlx::query(
        r#"
        select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component,
               m.visible, m.status, ifnull(m.perms, '') as perms, m.is_frame,
               m.is_cache, m.menu_type, m.icon, m.order_num, m.create_time
        from sys_menu m
                 left join sys_role_menu rm on m.menu_id = rm.menu_id
                 left join sys_user_role ur on rm.role_id = ur.role_id
                 left join sys_role ro on ur.role_id = ro.role_id
                 left join sys_user u on ur.user_id = u.user_id
        where u.user_id = ?
          and m.menu_type in ('M', 'C')
          and m.status = 0
          and ro.status = 0
        order by m.parent_id, m.order_num
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await?;

    rows.iter().map(map_menu).collect()
}
