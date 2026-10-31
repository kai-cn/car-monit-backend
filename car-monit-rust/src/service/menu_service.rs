// 来源: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java
// 职责: 菜单树与前端路由构建（selectMenuTreeByUserId / buildMenus）。
// 对应关系: getChildPerms/recursionFn -> build_tree；buildMenus -> build_menus。

use sqlx::MySqlPool;

use crate::common::constants::{LAYOUT, NO_FRAME, PARENT_VIEW, TYPE_DIR, TYPE_MENU};
use crate::domain::{MetaVo, RouterVo, SysMenu};
use crate::error::AppError;
use crate::repository::menu_repo;

/// Java: SysMenuServiceImpl.selectMenuTreeByUserId
pub async fn select_menu_tree_by_user_id(
    pool: &MySqlPool,
    user_id: i64,
) -> Result<Vec<SysMenu>, AppError> {
    // Java: SecurityUtils.isAdmin(userId) -> userId != null && 1L == userId
    let menus = if user_id == 1 {
        menu_repo::select_menu_tree_all(pool).await?
    } else {
        menu_repo::select_menu_tree_by_user_id(pool, user_id).await?
    };
    Ok(build_tree(menus, 0))
}

/// Java: getChildPerms(list, 0L) + recursionFn —— 只保留 parentId == 0 的根节点。
fn build_tree(menus: Vec<SysMenu>, parent_id: i64) -> Vec<SysMenu> {
    let mut slots: Vec<Option<SysMenu>> = menus.into_iter().map(Some).collect();
    let roots: Vec<usize> = slots
        .iter()
        .enumerate()
        .filter(|(_, menu)| {
            menu.as_ref()
                .is_some_and(|menu| menu.parent_id.unwrap_or(0) == parent_id)
        })
        .map(|(index, _)| index)
        .collect();

    let mut result = Vec::new();
    for index in roots {
        let mut menu = slots[index].take().expect("根节点仍存在");
        fill_children(&mut slots, &mut menu);
        result.push(menu);
    }
    result
}

/// Java: recursionFn —— children 顺序沿用 SQL 的 (parent_id, order_num)。
fn fill_children(slots: &mut [Option<SysMenu>], menu: &mut SysMenu) {
    let Some(menu_id) = menu.menu_id else {
        return;
    };
    let child_indices: Vec<usize> = slots
        .iter()
        .enumerate()
        .filter(|(_, child)| {
            child
                .as_ref()
                .is_some_and(|child| child.parent_id.unwrap_or(0) == menu_id)
        })
        .map(|(index, _)| index)
        .collect();

    let mut children = Vec::with_capacity(child_indices.len());
    for index in child_indices {
        let mut child = slots[index].take().expect("子节点仍存在");
        fill_children(slots, &mut child);
        children.push(child);
    }
    menu.children = children;
}

/// Java: SysMenuServiceImpl.buildMenus
pub fn build_menus(menus: &[SysMenu]) -> Vec<RouterVo> {
    menus.iter().map(build_router).collect()
}

fn build_router(menu: &SysMenu) -> RouterVo {
    let mut router = RouterVo {
        hidden: menu.visible.as_deref() == Some("1"),
        name: get_route_name(menu),
        path: get_router_path(menu),
        component: get_component(menu),
        meta: Some(meta_of(menu)),
        ..Default::default()
    };

    if !menu.children.is_empty() && menu.menu_type.as_deref() == Some(TYPE_DIR) {
        router.always_show = Some(true);
        router.redirect = Some("noRedirect".to_string());
        router.children = Some(build_menus(&menu.children));
    } else if is_menu_frame(menu) {
        // Java: 一级菜单内部跳转 —— meta 置空，子路由承接实际页面。
        router.meta = None;
        let child = RouterVo {
            path: menu.path.clone(),
            component: menu.component.clone(),
            name: capitalize(menu.path.as_deref()),
            meta: Some(meta_of(menu)),
            ..Default::default()
        };
        router.children = Some(vec![child]);
    }

    router
}

fn meta_of(menu: &SysMenu) -> MetaVo {
    MetaVo::new(
        menu.menu_name.clone(),
        menu.icon.clone(),
        menu.is_cache.as_deref() == Some("1"),
    )
}

/// Java: getRouteName —— StringUtils.capitalize(path)，菜单内部跳转为空串。
fn get_route_name(menu: &SysMenu) -> Option<String> {
    if is_menu_frame(menu) {
        return Some(String::new());
    }
    capitalize(menu.path.as_deref())
}

/// Java: getRouterPath
fn get_router_path(menu: &SysMenu) -> Option<String> {
    if menu.parent_id.unwrap_or(0) == 0
        && menu.menu_type.as_deref() == Some(TYPE_DIR)
        && menu.is_frame.as_deref() == Some(NO_FRAME)
    {
        return Some(format!("/{}", menu.path.as_deref().unwrap_or_default()));
    }
    if is_menu_frame(menu) {
        return Some("/".to_string());
    }
    menu.path.clone()
}

/// Java: getComponent
fn get_component(menu: &SysMenu) -> Option<String> {
    if menu.component.as_deref().is_some_and(|c| !c.is_empty()) && !is_menu_frame(menu) {
        return menu.component.clone();
    }
    if menu.component.as_deref().is_none_or(|c| c.is_empty()) && is_parent_view(menu) {
        return Some(PARENT_VIEW.to_string());
    }
    Some(LAYOUT.to_string())
}

/// Java: isMenuFrame —— 一级菜单且非外链。
fn is_menu_frame(menu: &SysMenu) -> bool {
    menu.parent_id.unwrap_or(0) == 0
        && menu.menu_type.as_deref() == Some(TYPE_MENU)
        && menu.is_frame.as_deref() == Some(NO_FRAME)
}

/// Java: isParentView
fn is_parent_view(menu: &SysMenu) -> bool {
    menu.parent_id.unwrap_or(0) != 0 && menu.menu_type.as_deref() == Some(TYPE_DIR)
}

/// Java: org.apache.commons.lang3.StringUtils.capitalize
fn capitalize(value: Option<&str>) -> Option<String> {
    let value = value?;
    let mut chars = value.chars();
    match chars.next() {
        Some(first) => {
            let mut out: String = first.to_uppercase().collect();
            out.push_str(chars.as_str());
            Some(out)
        }
        None => Some(String::new()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn menu(
        id: i64,
        parent: i64,
        name: &str,
        menu_type: &str,
        path: &str,
        component: Option<&str>,
        is_frame: &str,
    ) -> SysMenu {
        SysMenu {
            menu_id: Some(id),
            parent_id: Some(parent),
            menu_name: Some(name.to_string()),
            menu_type: Some(menu_type.to_string()),
            path: Some(path.to_string()),
            component: component.map(str::to_string),
            is_frame: Some(is_frame.to_string()),
            is_cache: Some("0".to_string()),
            visible: Some("0".to_string()),
            icon: Some("system".to_string()),
            ..Default::default()
        }
    }

    #[test]
    fn tree_keeps_only_roots_with_ordered_children() {
        let menus = vec![
            menu(1, 0, "系统管理", "M", "system", None, "1"),
            menu(
                2,
                1,
                "用户管理",
                "C",
                "user",
                Some("system/user/index"),
                "1",
            ),
            menu(3, 0, "监控", "M", "monitor", None, "1"),
        ];
        let tree = build_tree(menus, 0);
        assert_eq!(tree.len(), 2);
        assert_eq!(tree[0].menu_id, Some(1));
        assert_eq!(tree[0].children.len(), 1);
        assert_eq!(tree[0].children[0].menu_id, Some(2));
    }

    #[test]
    fn directory_router_gets_layout_and_children() {
        let menus = vec![
            menu(1, 0, "系统管理", "M", "system", None, "1"),
            menu(
                2,
                1,
                "用户管理",
                "C",
                "user",
                Some("system/user/index"),
                "1",
            ),
            menu(
                3,
                1,
                "角色管理",
                "C",
                "role",
                Some("system/role/index"),
                "1",
            ),
        ];
        let routers = build_menus(&build_tree(menus, 0));
        let value = serde_json::to_value(&routers[0]).expect("json");
        assert_eq!(
            value,
            json!({
                "name": "System",
                "path": "/system",
                "hidden": false,
                "redirect": "noRedirect",
                "component": "Layout",
                "alwaysShow": true,
                "meta": {"title": "系统管理", "icon": "system", "noCache": false, "link": null},
                "children": [
                    {
                        "name": "User",
                        "path": "user",
                        "hidden": false,
                        "component": "system/user/index",
                        "meta": {"title": "用户管理", "icon": "system", "noCache": false, "link": null}
                    },
                    {
                        "name": "Role",
                        "path": "role",
                        "hidden": false,
                        "component": "system/role/index",
                        "meta": {"title": "角色管理", "icon": "system", "noCache": false, "link": null}
                    }
                ]
            })
        );
    }

    #[test]
    fn top_level_menu_frame_is_wrapped() {
        let menus = vec![menu(1, 0, "首页", "C", "index", Some("index"), "1")];
        let routers = build_menus(&menus);
        let value = serde_json::to_value(&routers[0]).expect("json");
        assert_eq!(
            value,
            json!({
                "hidden": false,
                "path": "/",
                "component": "Layout",
                "children": [{
                    "name": "Index",
                    "path": "index",
                    "hidden": false,
                    "component": "index",
                    "meta": {"title": "首页", "icon": "system", "noCache": false, "link": null}
                }]
            })
        );
    }

    #[test]
    fn nested_directory_without_component_uses_parent_view() {
        let menus = vec![
            menu(1, 0, "系统管理", "M", "system", None, "1"),
            menu(2, 1, "日志", "M", "log", None, "1"),
            menu(
                3,
                2,
                "操作日志",
                "C",
                "operlog",
                Some("monitor/operlog/index"),
                "1",
            ),
        ];
        let routers = build_menus(&build_tree(menus, 0));
        let child = &routers[0].children.as_ref().expect("children")[0];
        assert_eq!(child.component.as_deref(), Some("ParentView"));
        assert_eq!(child.path.as_deref(), Some("log"));
    }
}
