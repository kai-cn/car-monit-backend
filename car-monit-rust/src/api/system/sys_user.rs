// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUserController.java
//       ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml
//       ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserServiceImpl.java
// 职责: 用户管理（多形态列表、CRUD、重置密码、状态、CA 绑定、导入导出）。
// 对应关系: selectUserList -> 自定义 QueryBuilder；insert/update -> 事务维护 user_role/user_post。

use std::collections::HashMap;

use axum::extract::{Multipart, Path, RawQuery, State};
use axum::{Extension, Json, Router};
use serde_json::{json, Map, Value};
use sqlx::mysql::MySql;
use sqlx::{MySqlPool, QueryBuilder};

use crate::api::meta::{self, BusinessType, LogSpec};
use crate::api::support;
use crate::auth::password;
use crate::common::utils::password_invalid;
use crate::db::rows::rows_to_json;
use crate::domain::{LoginUser, SysDept};
use crate::error::AppError;
use crate::response::{AjaxResult, TableDataInfo};
use crate::state::AppState;

const USER_COLUMNS: &str = "u.user_id, u.user_no, u.dept_id, u.nick_name, u.user_name, u.email, \
     u.avatar, u.phonenumber, u.password, u.sex, u.status, u.del_flag, u.login_ip, u.login_date, \
     u.create_by, u.create_time, u.remark, u.user_type, u.cert_entity_id, u.cert_id, u.buss_id, \
     u.buss_name, u.eps_name, ifnull(d.tenant_id, -1) tenant_id, d2.dept_name tenant_name, \
     d.dept_name, d.leader, u.image_id";

/// Java: `selectUserVo`（详情用）—— 比列表多 `d.sub_code`、`d.parent_id`、`d.order_num`、
/// `d.status as dept_status`，这些列经 `deptResult` 落到 `dept` 里，`sub_code` 落到顶层 `subCode`。
const USER_VO_COLUMNS: &str =
    "u.user_id, u.user_no, u.dept_id, u.user_name, u.nick_name, u.email, \
     u.avatar, u.phonenumber, u.password, u.sex, u.status, u.del_flag, u.login_ip, u.login_date, \
     u.create_by, u.create_time, u.remark, u.user_type, u.cert_entity_id, u.cert_id, \
     ifnull(u.buss_id, u.user_name) buss_id, u.buss_name, u.eps_name, \
     ifnull(d.tenant_id, -1) tenant_id, d.sub_code, d.dept_id, d.parent_id, d.dept_name, \
     d.order_num, d.leader, d.status as dept_status, u.image_id";

const USER_FROM: &str = "from sys_user u      left join sys_dept d on u.dept_id = d.dept_id      left join sys_dept d2 on d.tenant_id = d2.dept_id where u.del_flag = '0'";

const ROLE_COLUMNS: &str = "r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope, \
     r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark, \
     null as createBy, null as updateBy, null as updateTime, 0 as flag";

const POST_COLUMNS: &str = "post_id, post_code, post_name, post_sort, status, create_by, \
     create_time, remark";

static LOG_EXPORT: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Export,
    "com.ruoyi.web.controller.system.SysUserController.export()",
);
static LOG_IMPORT: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Import,
    "com.ruoyi.web.controller.system.SysUserController.importData()",
);
static LOG_ADD: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Insert,
    "com.ruoyi.web.controller.system.SysUserController.add()",
);
static LOG_EDIT: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysUserController.edit()",
);
static LOG_REMOVE: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Delete,
    "com.ruoyi.web.controller.system.SysUserController.remove()",
);
static LOG_RESET: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysUserController.resetPwd()",
);
static LOG_STATUS: LogSpec = LogSpec::new(
    "用户管理",
    BusinessType::Update,
    "com.ruoyi.web.controller.system.SysUserController.changeStatus()",
);

pub fn routes() -> Router<AppState> {
    Router::new()
        .route(
            "/system/user/list",
            meta::get_route("/system/user/list", None, None, list),
        )
        .route(
            "/system/user/listAll",
            meta::get_route("/system/user/listAll", None, None, list_all),
        )
        .route(
            "/system/user/listTenantIdAll",
            meta::get_route("/system/user/listTenantIdAll", None, None, list_tenant_all),
        )
        .route(
            "/system/user/listutil",
            meta::get_route("/system/user/listutil", None, None, list_util),
        )
        .route(
            "/system/user/listSameUtil",
            meta::get_route("/system/user/listSameUtil", None, None, list_same_util),
        )
        .route(
            "/system/user/listMy",
            meta::get_route("/system/user/listMy", None, None, list_my),
        )
        .route(
            "/system/user/list/dept",
            meta::get_route("/system/user/list/dept", None, None, list_by_dept),
        )
        .route(
            "/system/user/currentUser",
            meta::get_route("/system/user/currentUser", None, None, current_user),
        )
        .route(
            "/system/user/export",
            meta::get_route(
                "/system/user/export",
                Some("system:user:export"),
                Some(&LOG_EXPORT),
                export,
            ),
        )
        .route(
            "/system/user/importData",
            meta::post_route(
                "/system/user/importData",
                Some("system:user:import"),
                Some(&LOG_IMPORT),
                import_data,
            ),
        )
        .route(
            "/system/user/importTemplate",
            meta::get_route("/system/user/importTemplate", None, None, import_template),
        )
        .route(
            "/system/user/resetPwd",
            meta::put_route(
                "/system/user/resetPwd",
                Some("system:user:resetPwd"),
                Some(&LOG_RESET),
                reset_pwd,
            ),
        )
        .route(
            "/system/user/changeStatus",
            meta::put_route(
                "/system/user/changeStatus",
                Some("system:user:edit"),
                Some(&LOG_STATUS),
                change_status,
            ),
        )
        .route(
            "/system/user/bindUky",
            meta::put_route("/system/user/bindUky", None, None, bind_uky),
        )
        .route(
            "/system/user/getroleUser/{roleCode}",
            meta::get_route(
                "/system/user/getroleUser/{roleCode}",
                None,
                None,
                get_role_user,
            ),
        )
        .route(
            "/system/user/",
            meta::get_route(
                "/system/user/",
                Some("system:user:query"),
                None,
                get_info_root,
            ),
        )
        .route(
            "/system/user/{userIds}",
            meta::get_route(
                "/system/user/{userIds}",
                Some("system:user:query"),
                None,
                get_info,
            ),
        )
        .route(
            "/system/user",
            meta::post_route("/system/user", Some("system:user:add"), Some(&LOG_ADD), add).merge(
                meta::put_route(
                    "/system/user",
                    Some("system:user:edit"),
                    Some(&LOG_EDIT),
                    edit,
                ),
            ),
        )
        .route(
            "/system/user/{userIds}",
            meta::delete_route(
                "/system/user/{userIds}",
                Some("system:user:remove"),
                Some(&LOG_REMOVE),
                remove,
            ),
        )
}

fn push_user_filters(builder: &mut QueryBuilder<'_, MySql>, params: &HashMap<String, String>) {
    let text = |key: &str| {
        params
            .get(key)
            .map(|value| value.trim())
            .filter(|value| !value.is_empty())
    };
    if let Some(value) = params.get("userId").filter(|value| !value.is_empty()) {
        builder.push(" and u.user_id = ");
        builder.push_bind(value.clone());
    }
    if let Some(value) = text("userNo") {
        builder.push(" and u.user_no = ");
        builder.push_bind(value.to_string());
    }
    if let Some(value) = text("userName") {
        builder.push(" and u.user_name like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    if let Some(value) = text("status") {
        builder.push(" and u.status = ");
        builder.push_bind(value.to_string());
    }
    if let Some(value) = text("phonenumber") {
        builder.push(" and u.phonenumber like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    if let Some(value) = text("params[beginTime]") {
        builder.push(" and date_format(u.create_time,'%y%m%d') >= date_format(");
        builder.push_bind(value.to_string());
        builder.push(", '%y%m%d')");
    }
    if let Some(value) = text("params[endTime]") {
        builder.push(" and date_format(u.create_time,'%y%m%d') <= date_format(");
        builder.push_bind(value.to_string());
        builder.push(", '%y%m%d')");
    }
    if let Some(value) = params
        .get("deptId")
        .filter(|value| !value.is_empty() && *value != "0")
    {
        builder.push(" and (u.dept_id = ");
        builder.push_bind(value.clone());
        builder.push(" or u.dept_id in (select t.dept_id from sys_dept t where find_in_set(");
        builder.push_bind(value.clone());
        builder.push(", t.ancestors)))");
    }
    for (key, column) in [
        ("userType", "u.user_type"),
        ("certEntityId", "u.cert_entity_id"),
        ("certId", "u.cert_id"),
        ("bussId", "u.buss_id"),
    ] {
        if let Some(value) = text(key) {
            builder.push(format!(" and {column} = "));
            builder.push_bind(value.to_string());
        }
    }
    for (key, column) in [("bussName", "u.buss_name"), ("epsName", "u.eps_name")] {
        if let Some(value) = text(key) {
            builder.push(format!(" and {column} like concat('%', "));
            builder.push_bind(value.to_string());
            builder.push(", '%')");
        }
    }
    if let Some(value) = text("tenantId") {
        builder.push(" and d.tenant_id = ");
        builder.push_bind(value.to_string());
    }
    if let Some(value) = text("roleCode") {
        builder.push(
            " and exists (select 1 from sys_user_role t1, sys_role t2 \
             where t2.del_flag = '0' and t2.role_id = t1.role_id and t1.user_id = u.user_id \
             and t2.role_key = ",
        );
        builder.push_bind(value.to_string());
        builder.push(")");
    }
    let flag = params.get("flag").cloned().unwrap_or_default();
    if flag == "sjzbDept" || flag == "sjzbDeptCg" {
        builder.push(
            " and exists (select 1 from sys_dept tb, sys_dept tb1 \
             where tb.del_flag = '0' and tb.del_flag = '0' and tb1.dept_id = tb.parent_id \
             and tb.dept_id = ",
        );
        builder.push_bind(params.get("dataId").cloned().unwrap_or_default());
        builder.push(" and tb1.dept_id = d.tenant_id)");
    }
    if flag == "sjzbDeptCg" || flag == "myDeptCg" {
        builder.push(
            " and exists (select 1 from sys_user_role sr, sys_role r where r.role_id = sr.role_id \
             and r.role_key = 'cgjl_manager' and sr.user_id = u.user_id)",
        );
    }
    if let Some(value) = text("queryNickName") {
        builder.push(" and u.nick_name like concat('%', ");
        builder.push_bind(value.to_string());
        builder.push(", '%')");
    }
    if let Some(value) = params.get("excludeId").filter(|value| !value.is_empty()) {
        builder.push(" and u.user_id != ");
        builder.push_bind(value.clone());
    }
}

async fn query_users(
    state: &AppState,
    params: &HashMap<String, String>,
    page: Option<&crate::common::page::PageDomain>,
) -> Result<(i64, Vec<Value>), AppError> {
    let mut count_builder = QueryBuilder::<MySql>::new(format!("select count(0) {USER_FROM}"));
    push_user_filters(&mut count_builder, params);
    let total: i64 = count_builder
        .build_query_scalar()
        .fetch_one(&state.db)
        .await?;

    let mut builder = QueryBuilder::<MySql>::new(format!("select {USER_COLUMNS} {USER_FROM}"));
    push_user_filters(&mut builder, params);

    if let Some(page) = page {
        let (offset, limit) = page.resolve(total);
        builder.push(" limit ");
        builder.push_bind(limit);
        builder.push(" offset ");
        builder.push_bind(offset);
    }
    let rows = builder.build().fetch_all(&state.db).await?;
    let mut data = rows_to_json(&rows);
    shape_user_rows(&mut data);
    Ok((total, data))
}

/// Java Jackson 的 SysUser 键序：BaseEntity（含 params）→ 声明顺序 → 关联对象 → 派生 getter。
/// `/system/user/list` 一类 VO 没有 params 键，重排时自动跳过。
pub(crate) const USER_KEYS: &[&str] = &[
    "createBy",
    "createTime",
    "updateBy",
    "updateTime",
    "remark",
    "params",
    "userId",
    "userNo",
    "deptId",
    "userName",
    "nickName",
    "userType",
    "email",
    "phonenumber",
    "sex",
    "avatar",
    "confirmPassword",
    "salt",
    "status",
    "delFlag",
    "loginIp",
    "loginDate",
    "certId",
    "certEntityId",
    "bussId",
    "bussName",
    "epsName",
    "tenantId",
    "tenantName",
    "roleCode",
    "dept",
    "roles",
    "roleIds",
    "postIds",
    "flag",
    "dataId",
    "subCode",
    "queryNickName",
    "excludeSelf",
    "excludeId",
    "headOffice",
    "procurementManager",
    "deptName",
    "pjFlag",
    "imageId",
    "admin",
];

/// Java SysPost：postSort 为 String，flag 为 boolean。
fn shape_post_rows(mut rows: Vec<Value>) -> Vec<Value> {
    support::apply_formats(
        &mut rows,
        &[
            ("postSort", support::FieldFormat::String),
            ("flag", support::FieldFormat::Bool),
        ],
    );
    for row in &mut rows {
        if let Some(object) = row.as_object_mut() {
            object.entry("updateBy").or_insert(Value::Null);
            object.entry("updateTime").or_insert(Value::Null);
            object.entry("flag").or_insert(Value::Bool(false));
        }
    }
    for row in rows.iter_mut() {
        *row = support::reorder_keys(row.take(), super::sys_post::POST_KEYS);
    }
    rows
}

/// Java SysUserResult：BaseEntity 空字段 + 关联 dept（deptResult 只映射 VO 选中的列）。
fn shape_user_rows(rows: &mut [Value]) {
    for row in rows {
        {
            let Some(object) = row.as_object_mut() else {
                continue;
            };
            object.remove("password");
            let dept_id = object.get("deptId").cloned().unwrap_or(Value::Null);
            let dept_name = object.remove("deptName").unwrap_or(Value::Null);
            let leader = object.remove("leader").unwrap_or(Value::Null);
            // Java: deptResult 的 parent_id / order_num / dept_status 只进 dept，顶层没有这些属性。
            let parent_id = object.remove("parentId").unwrap_or(Value::Null);
            let order_num = object.remove("orderNum").unwrap_or(Value::Null);
            let dept_status = object.remove("deptStatus").unwrap_or(Value::Null);
            let user_id = object.get("userId").and_then(Value::as_i64);
            for key in [
                "updateBy",
                "updateTime",
                "confirmPassword",
                "salt",
                "roleCode",
                "roleIds",
                "postIds",
                "flag",
                "dataId",
                "subCode",
                "tenantName",
                "queryNickName",
                "excludeSelf",
                "excludeId",
                "headOffice",
                "procurementManager",
            ] {
                object.entry(key).or_insert(Value::Null);
            }
            // Java: SysUser.deptName 不在 resultMap 里，任何查询都是 null（值只进 dept.deptName）。
            object.insert("deptName".to_string(), Value::Null);
            // Java: `private int pjFlag`（原始类型）没有 setter 调用，出参恒为 0。
            object.insert("pjFlag".to_string(), json!(0));
            object.insert("admin".to_string(), Value::Bool(user_id == Some(1)));
            object.entry("roles").or_insert_with(|| json!([]));
            if let Some(text) = object
                .get("loginDate")
                .and_then(Value::as_str)
                .map(str::to_string)
            {
                // Java: loginDate 是裸 `Date`，没有 @JsonFormat → Jackson 写 ISO 带毫秒与本机偏移。
                if let Some(iso) = java_iso_datetime(&text) {
                    object.insert("loginDate".to_string(), Value::String(iso));
                }
            }
            let mut dept = serde_json::to_value(SysDept::default()).unwrap_or(json!({}));
            if let Some(map) = dept.as_object_mut() {
                if !dept_id.is_null() {
                    map.insert("deptId".to_string(), dept_id);
                }
                if !dept_name.is_null() {
                    map.insert("deptName".to_string(), dept_name);
                }
                if !leader.is_null() {
                    map.insert("leader".to_string(), leader);
                }
                if !parent_id.is_null() {
                    map.insert("parentId".to_string(), parent_id);
                }
                if !order_num.is_null() {
                    // Java: SysDept.orderNum 是 `String`，数字列也要按字符串出参。
                    let order_num = match order_num {
                        Value::Number(number) => Value::String(number.to_string()),
                        other => other,
                    };
                    map.insert("orderNum".to_string(), order_num);
                }
                if !dept_status.is_null() {
                    map.insert("status".to_string(), dept_status);
                }
            }
            let dept = support::reorder_keys(dept, super::sys_dept::DEPT_KEYS);
            object.insert("dept".to_string(), dept);
        }
        *row = support::reorder_keys(row.take(), USER_KEYS);
    }
}

/// `yyyy-MM-dd HH:mm:ss`（rows.rs 的墙上时钟写法）→ Jackson 的 ISO 带毫秒与本机偏移。
fn java_iso_datetime(text: &str) -> Option<String> {
    let naive = chrono::NaiveDateTime::parse_from_str(text, "%Y-%m-%d %H:%M:%S").ok()?;
    let local = chrono::TimeZone::from_local_datetime(&chrono::Local, &naive).earliest()?;
    Some(local.to_rfc3339_opts(chrono::SecondsFormat::Millis, false))
}

async fn list(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    params.insert("userType".to_string(), "1".to_string());
    let page = support::page_domain(&raw);
    let (total, rows) = query_users(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_all(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    if let Some(tenant_id) = user.user.tenant_id {
        params.insert("tenantId".to_string(), tenant_id.to_string());
    }
    let page = support::page_domain(&raw);
    let (total, rows) = query_users(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_tenant_all(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    params
        .entry("tenantId".to_string())
        .or_insert_with(|| "-1".to_string());
    let page = support::page_domain(&raw);
    let (total, rows) = query_users(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_util(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    let flag = params.get("flag").cloned().unwrap_or_default();
    let tenant_id = user.user.tenant_id.unwrap_or_default();
    match flag.as_str() {
        "myDept" | "myDeptCg" => {
            params.insert("status".to_string(), "0".to_string());
            params.insert("userType".to_string(), "1".to_string());
            params.insert("tenantId".to_string(), tenant_id.to_string());
        }
        "sjzbDept" | "sjzbDeptCg" => {
            params.insert("dataId".to_string(), tenant_id.to_string());
        }
        "allDept" => {}
        _ => {
            params.insert("userId".to_string(), "-1".to_string());
        }
    }
    let page = support::page_domain(&raw);
    let (total, rows) = query_users(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_same_util(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    params.insert("status".to_string(), "0".to_string());
    params.insert("userType".to_string(), "1".to_string());
    if let Some(tenant_id) = user.user.tenant_id {
        params.insert("tenantId".to_string(), tenant_id.to_string());
    }
    if let Some(dept_id) = user.user.dept_id {
        params.insert("deptId".to_string(), dept_id.to_string());
    }
    let page = support::page_domain(&raw);
    let (total, rows) = query_users(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_my(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    params.insert(
        "userId".to_string(),
        user.user.user_id.unwrap_or_default().to_string(),
    );
    let page = support::page_domain(&raw);
    let (total, rows) = query_users(&state, &params, Some(&page)).await?;
    Ok(TableDataInfo::new(total, rows))
}

async fn list_by_dept(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    RawQuery(raw): RawQuery,
) -> Result<TableDataInfo<Value>, AppError> {
    let mut params = support::query_map(&raw);
    if let Some(dept_id) = user.user.dept_id {
        params.insert("deptId".to_string(), dept_id.to_string());
    }
    let exclude_self = params
        .get("excludeSelf")
        .map(|value| value == "true")
        .unwrap_or(false);
    if exclude_self {
        params.insert(
            "excludeId".to_string(),
            user.user.user_id.unwrap_or_default().to_string(),
        );
    }
    params.insert("userType".to_string(), "1".to_string());
    let page = support::page_domain(&raw);
    let (total, mut rows) = query_users(&state, &params, Some(&page)).await?;
    // Java: listByDept 查完之后把 dept.deptName 回填到顶层 deptName（其它列表端点不回填）。
    for row in rows.iter_mut() {
        let name = row
            .get("dept")
            .and_then(|dept| dept.get("deptName"))
            .and_then(Value::as_str)
            .filter(|text| !text.trim().is_empty())
            .map(str::to_string);
        if let (Some(object), Some(name)) = (row.as_object_mut(), name) {
            object.insert("deptName".to_string(), Value::String(name));
        }
    }
    Ok(TableDataInfo::new(total, rows))
}

async fn current_user(Extension(user): Extension<LoginUser>) -> Result<AjaxResult, AppError> {
    // Java: SecurityUtils.getLoginUser().getUser() —— 登录态里的 user 对象；
    // dept/roles 未加载时为 null，password 有 @JsonIgnore 不输出。
    let mut value = serde_json::to_value(user.user.for_http())?;
    if let Some(object) = value.as_object_mut() {
        object.remove("password");
        object.remove("params");
        let admin = user.user.is_admin();
        object.insert("admin".to_string(), Value::Bool(admin));
        object.insert("dept".to_string(), Value::Null);
        object.insert("roles".to_string(), Value::Null);
    }
    let value = support::reorder_keys(value, USER_KEYS);
    Ok(AjaxResult::success_data(value))
}

async fn get_role_user(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Path(role_code): Path<String>,
) -> Result<AjaxResult, AppError> {
    let mut params = HashMap::new();
    params.insert("roleCode".to_string(), role_code);
    if let Some(tenant_id) = user.user.tenant_id {
        params.insert("tenantId".to_string(), tenant_id.to_string());
    }
    let (_, rows) = query_users(&state, &params, None).await?;
    Ok(AjaxResult::success_data(rows))
}

async fn export(
    State(state): State<AppState>,
    RawQuery(raw): RawQuery,
) -> Result<AjaxResult, AppError> {
    let params = support::query_map(&raw);
    let (_, rows) = query_users(&state, &params, None).await?;
    let headers = [
        "用户序号",
        "用户编码",
        "部门编号",
        "登录名称",
        "用户名称",
        "用户类型",
        "用户邮箱",
        "手机号码",
        "用户性别",
        "帐号状态",
        "最后登录IP",
        "最后登录时间",
        "证书Id",
        "证书实体Id",
        "业务id",
        "业务名称",
        "单位名称",
        "租户单位id",
        "租户单位名称",
        "角色编码",
        "部门名称",
        "部门负责人",
    ]
    .map(str::to_string);
    let fields = [
        "userId",
        "userNo",
        "deptId",
        "userName",
        "nickName",
        "userType",
        "email",
        "phonenumber",
        "sex",
        "status",
        "loginIp",
        "loginDate",
        "certId",
        "certEntityId",
        "bussId",
        "bussName",
        "epsName",
        "tenantId",
        "tenantName",
        "roleCode",
        "deptName",
        "leader",
    ];
    let data = rows
        .iter()
        .map(|row| {
            let mut values = support::pick_fields(row, &fields);
            if let Some(Value::String(text)) = values.get(5).cloned() {
                values[5] = Value::String(match text.as_str() {
                    "1" => "机构用户".to_string(),
                    "2" => "专家".to_string(),
                    "3" => "供应商".to_string(),
                    _ => text,
                });
            }
            if let Some(Value::String(text)) = values.get(8).cloned() {
                values[8] = Value::String(match text.as_str() {
                    "0" => "男".to_string(),
                    "1" => "女".to_string(),
                    "2" => "未知".to_string(),
                    _ => text,
                });
            }
            if let Some(Value::String(text)) = values.get(9).cloned() {
                values[9] = Value::String(match text.as_str() {
                    "0" => "正常".to_string(),
                    "1" => "停用".to_string(),
                    _ => text,
                });
            }
            values
        })
        .collect::<Vec<_>>();
    support::export_excel(&state, "用户数据", &headers, &data)
}

async fn import_template(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let headers = [
        "用户序号",
        "用户编码",
        "部门编号",
        "登录名称",
        "用户名称",
        "用户类型",
        "用户邮箱",
        "手机号码",
        "用户性别",
        "帐号状态",
        "证书Id",
        "证书实体Id",
        "业务id",
        "业务名称",
        "单位名称",
        "租户单位id",
        "租户单位名称",
        "角色编码",
    ]
    .map(str::to_string);
    support::export_excel(&state, "用户数据", &headers, &[])
}

/// Java: getInfo(userId=null) —— 只返回可分配角色与岗位。
async fn get_info_root(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let roles = sqlx::query(&format!(
        "select distinct {ROLE_COLUMNS} from sys_role r where r.del_flag = '0' order by r.role_sort"
    ))
    .fetch_all(&state.db)
    .await?;
    let posts = sqlx::query(
        "select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark          from sys_post",
    )
    .fetch_all(&state.db)
    .await?;
    let mut ajax = AjaxResult::success();
    let mut role_values =
        crate::api::system::sys_role::role_rows(crate::db::rows::rows_to_json(&roles));
    role_values.retain(|role| role.get("roleId").and_then(Value::as_i64) != Some(1));
    ajax.insert_value("roles", json!(role_values));
    ajax.insert_value(
        "posts",
        json!(shape_post_rows(crate::db::rows::rows_to_json(&posts))),
    );
    Ok(ajax)
}

async fn get_info(
    State(state): State<AppState>,
    Path(user_id): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable(required = false) Long userId` —— 空串等价 null（跳过查用户），
    // 非数字则先被 Spring 的类型转换拦下。
    let user_id = if user_id.trim().is_empty() {
        String::new()
    } else {
        support::path_long("userId", &user_id)?.to_string()
    };
    let roles = sqlx::query(&format!(
        "select distinct {ROLE_COLUMNS} from sys_role r where r.del_flag = '0' order by r.role_sort"
    ))
    .fetch_all(&state.db)
    .await?;
    let posts = sqlx::query(&format!("select {POST_COLUMNS} from sys_post"))
        .fetch_all(&state.db)
        .await?;

    let mut ajax = AjaxResult::success();
    let mut role_values = crate::api::system::sys_role::role_rows(rows_to_json(&roles));
    if user_id.trim() != "1" {
        role_values.retain(|role| role.get("roleId").and_then(Value::as_i64) != Some(1));
    }
    ajax.insert_value("roles", json!(role_values));
    ajax.insert_value("posts", json!(shape_post_rows(rows_to_json(&posts))));
    if !user_id.is_empty() {
        let row = sqlx::query(&format!(
            "select {USER_VO_COLUMNS} from sys_user u \
             left join sys_dept d on u.dept_id = d.dept_id \
             left join sys_dept d2 on d.tenant_id = d2.dept_id where u.user_id = ?"
        ))
        .bind(&user_id)
        .fetch_optional(&state.db)
        .await?;
        let mut wrapper = vec![row
            .map(|row| crate::db::rows::row_to_json(&row))
            .unwrap_or(Value::Null)];
        shape_user_rows(&mut wrapper);
        let mut user = wrapper.pop().unwrap_or(Value::Null);
        // getInfo 的 selectUserVo 取 d.sub_code；列表 VO 不取（保持 null）。
        if let Value::Object(object) = &mut user {
            let dept_id = object.get("deptId").and_then(Value::as_i64);
            if let Some(dept_id) = dept_id {
                let sub_code: Option<String> =
                    sqlx::query_scalar("select sub_code from sys_dept where dept_id = ?")
                        .bind(dept_id)
                        .fetch_optional(&state.db)
                        .await?
                        .flatten();
                object.insert("subCode".to_string(), json!(sub_code));
            }
        }
        if let Value::Object(object) = &mut user {
            let assoc = sqlx::query(
                "select distinct r.role_id, r.role_name, r.role_key, r.role_sort,                  r.data_scope, r.status from sys_role r                  left join sys_user_role ur on ur.role_id = r.role_id                  where ur.user_id = ?",
            )
            .bind(&user_id)
            .fetch_all(&state.db)
            .await?;
            let assoc_rows = rows_to_json(&assoc);
            let mut roles_value = Vec::with_capacity(assoc_rows.len());
            for row in &assoc_rows {
                // Java RoleResult 只映射 6 个列，其余 SysRole 字段为默认值。
                let mut role = serde_json::to_value(crate::domain::SysRole::default())?;
                if let Some(map) = role.as_object_mut() {
                    for key in [
                        "roleId",
                        "roleName",
                        "roleKey",
                        "roleSort",
                        "dataScope",
                        "status",
                    ] {
                        let mut value = row.get(key).cloned().unwrap_or(Value::Null);
                        if key == "roleSort" {
                            if let Some(text) = value.as_i64() {
                                value = Value::String(text.to_string());
                            }
                        }
                        map.insert(key.to_string(), value);
                    }
                    let admin = row.get("roleId").and_then(Value::as_i64) == Some(1);
                    map.insert("admin".to_string(), Value::Bool(admin));
                }
                roles_value.push(support::reorder_keys(
                    role,
                    crate::api::system::sys_role::ROLE_KEYS,
                ));
            }
            object.insert("roles".to_string(), json!(roles_value));
        }
        let post_ids: Vec<i64> =
            sqlx::query_scalar("select post_id from sys_user_post where user_id = ?")
                .bind(&user_id)
                .fetch_all(&state.db)
                .await?;
        let role_ids: Vec<i64> =
            sqlx::query_scalar("select role_id from sys_user_role where user_id = ?")
                .bind(&user_id)
                .fetch_all(&state.db)
                .await?;
        ajax.insert_value("data", user);
        ajax.insert_value("postIds", json!(post_ids));
        ajax.insert_value("roleIds", json!(role_ids));
    }
    Ok(ajax)
}

fn text(body: &Value, key: &str) -> String {
    body.get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_string()
}

fn id_list(body: &Value, key: &str) -> Option<Vec<i64>> {
    body.get(key).and_then(Value::as_array).map(|items| {
        items
            .iter()
            .filter_map(|item| {
                item.as_i64()
                    .or_else(|| item.as_str().and_then(|text| text.parse().ok()))
            })
            .collect()
    })
}

/// Java: insert/update 的实体字段白名单（roleIds/postIds 等 @TableField(exist=false) 不入库）。
fn entity_from_body(body: &Value) -> Value {
    const FIELDS: &[&str] = &[
        "userNo",
        "deptId",
        "userName",
        "nickName",
        "password",
        "userType",
        "email",
        "phonenumber",
        "sex",
        "avatar",
        "status",
        "remark",
        "certEntityId",
        "certId",
        "bussId",
        "bussName",
        "epsName",
        "tenantId",
        "imageId",
        "createBy",
        "createTime",
        "updateBy",
        "updateTime",
        "loginIp",
        "loginDate",
    ];
    let mut map = Map::new();
    for field in FIELDS {
        if let Some(value) = body.get(*field) {
            if !value.is_null() {
                map.insert((*field).to_string(), value.clone());
            }
        }
    }
    Value::Object(map)
}

/// Java: `insertUser`/`updateUser` 里的 `sysDept.getDeptName()`——部门行不存在时 Java 直接 NPE，
/// 响应是 `{"msg":null,"code":500}`。返回 `false` 表示该情形，调用方据此回空 msg。
async fn apply_dept(state: &AppState, entity: &mut Value) -> Result<bool, AppError> {
    let Some(dept_id) = entity.get("deptId").and_then(Value::as_i64) else {
        return Ok(true);
    };
    let dept: Option<(Option<String>, Option<i64>)> =
        sqlx::query_as("select dept_name, tenant_id from sys_dept where dept_id = ?")
            .bind(dept_id)
            .fetch_optional(&state.db)
            .await?;
    let Some((name, tenant_id)) = dept else {
        return Ok(false);
    };
    if let Some(object) = entity.as_object_mut() {
        if let Some(name) = name {
            object.insert("bussName".to_string(), Value::String(name));
        }
        if let Some(tenant_id) = tenant_id {
            object.insert("tenantId".to_string(), json!(tenant_id));
        }
    }
    Ok(true)
}

async fn insert_relations(
    tx: &mut sqlx::Transaction<'_, MySql>,
    table: &str,
    column: &str,
    user_id: i64,
    ids: &[i64],
) -> Result<(), AppError> {
    if ids.is_empty() {
        return Ok(());
    }
    let mut builder =
        QueryBuilder::<MySql>::new(format!("insert into {table}(user_id, {column}) "));
    builder.push_values(ids, |mut bind, id| {
        bind.push_bind(user_id).push_bind(*id);
    });
    builder.build().execute(&mut **tx).await?;
    Ok(())
}

async fn insert_user_row(
    tx: &mut sqlx::Transaction<'_, MySql>,
    entity: &Value,
) -> Result<i64, AppError> {
    let Some(object) = entity.as_object() else {
        return Err(AppError::BadRequest("请求体必须是 JSON 对象".to_string()));
    };
    let mut builder = QueryBuilder::<MySql>::new("insert into sys_user (");
    let mut first = true;
    for (key, value) in object.iter() {
        if value.is_null() {
            continue;
        }
        if !first {
            builder.push(", ");
        }
        first = false;
        builder.push(support::column_name(key));
    }
    if first {
        return Err(AppError::Service("新增失败：没有可写入的字段".to_string()));
    }
    builder.push(", create_time) values (");
    let mut first = true;
    for value in object.values() {
        if value.is_null() {
            continue;
        }
        if !first {
            builder.push(", ");
        }
        first = false;
        support::bind_value(&mut builder, value);
    }
    builder.push(", sysdate())");
    builder.build().execute(&mut **tx).await?;
    // LAST_INSERT_ID() 的列元信息是 BIGINT UNSIGNED，只能按 u64 取回。
    let id: u64 = sqlx::query_scalar("select last_insert_id()")
        .fetch_one(&mut **tx)
        .await?;
    Ok(id as i64)
}

async fn unique_value(
    pool: &MySqlPool,
    column: &str,
    value: &str,
) -> Result<Option<i64>, AppError> {
    if value.is_empty() {
        return Ok(None);
    }
    let sql = format!("select user_id from sys_user where {column} = ? and del_flag = '0' limit 1");
    Ok(sqlx::query_scalar(&sql)
        .bind(value)
        .fetch_optional(pool)
        .await?)
}

async fn add(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let user_name = text(&body, "userName");
    let verb = "新增用户";
    if unique_value(&state.db, "user_name", &user_name)
        .await?
        .is_some()
    {
        return Ok(AjaxResult::error(format!(
            "{verb}'{user_name}'失败，登录账号已存在"
        )));
    }
    let phone = text(&body, "phonenumber");
    let email = text(&body, "email");
    if let Some(found) = unique_value(&state.db, "phonenumber", &phone).await? {
        if found != 0 && !phone.is_empty() {
            return Ok(AjaxResult::error(format!(
                "{verb}'{user_name}'失败，手机号码已存在"
            )));
        }
    }
    if let Some(found) = unique_value(&state.db, "email", &email).await? {
        if found != 0 && !email.is_empty() {
            return Ok(AjaxResult::error(format!(
                "{verb}'{user_name}'失败，邮箱账号已存在"
            )));
        }
    }
    let raw_password = text(&body, "password");
    if password_invalid(&raw_password) {
        return Ok(AjaxResult::error(
            "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号",
        ));
    }

    let mut entity = entity_from_body(&body);
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "createBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
        object.insert(
            "password".to_string(),
            Value::String(password::encode(&raw_password)?),
        );
    }
    if !apply_dept(&state, &mut entity).await? {
        return Ok(AjaxResult::error_null_msg());
    }

    let role_ids = id_list(&body, "roleIds").unwrap_or_default();
    let post_ids = id_list(&body, "postIds").unwrap_or_default();
    let mut tx = state.db.begin().await?;
    let user_id = insert_user_row(&mut tx, &entity).await?;
    insert_relations(&mut tx, "sys_user_role", "role_id", user_id, &role_ids).await?;
    insert_relations(&mut tx, "sys_user_post", "post_id", user_id, &post_ids).await?;
    tx.commit().await?;
    Ok(support::to_ajax(1))
}

fn check_user_allowed(body: &Value) -> Result<(), AppError> {
    if body.get("userId").and_then(Value::as_i64) == Some(1) {
        return Err(AppError::Service("不允许操作超级管理员用户".to_string()));
    }
    Ok(())
}

async fn edit(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    check_user_allowed(&body)?;
    let user_id = body
        .get("userId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("userId不能为空".to_string()))?;
    let user_name = text(&body, "userName");
    let verb = "修改用户";
    let phone = text(&body, "phonenumber");
    let email = text(&body, "email");
    if let Some(found) = unique_value(&state.db, "phonenumber", &phone).await? {
        if found != user_id && !phone.is_empty() {
            return Ok(AjaxResult::error(format!(
                "{verb}'{user_name}'失败，手机号码已存在"
            )));
        }
    }
    if let Some(found) = unique_value(&state.db, "email", &email).await? {
        if found != user_id && !email.is_empty() {
            return Ok(AjaxResult::error(format!(
                "{verb}'{user_name}'失败，邮箱账号已存在"
            )));
        }
    }

    let mut entity = entity_from_body(&body);
    if let Some(object) = entity.as_object_mut() {
        object.insert(
            "updateBy".to_string(),
            Value::String(user.user.user_name.clone().unwrap_or_default()),
        );
    }
    if !apply_dept(&state, &mut entity).await? {
        return Ok(AjaxResult::error_null_msg());
    }
    let role_ids = id_list(&body, "roleIds");
    let post_ids = id_list(&body, "postIds");

    let mut tx = state.db.begin().await?;
    if let Some(role_ids) = role_ids {
        sqlx::query("delete from sys_user_role where user_id = ?")
            .bind(user_id)
            .execute(&mut *tx)
            .await?;
        insert_relations(&mut tx, "sys_user_role", "role_id", user_id, &role_ids).await?;
    }
    if let Some(post_ids) = post_ids {
        sqlx::query("delete from sys_user_post where user_id = ?")
            .bind(user_id)
            .execute(&mut *tx)
            .await?;
        insert_relations(&mut tx, "sys_user_post", "post_id", user_id, &post_ids).await?;
    }
    update_user_row(&mut tx, &entity, user_id).await?;
    tx.commit().await?;
    Ok(support::to_ajax(1))
}

async fn update_user_row(
    tx: &mut sqlx::Transaction<'_, MySql>,
    entity: &Value,
    user_id: i64,
) -> Result<u64, AppError> {
    let Some(object) = entity.as_object() else {
        return Ok(0);
    };
    let mut builder = QueryBuilder::<MySql>::new("update sys_user set ");
    let mut first = true;
    for (key, value) in object.iter() {
        if value.is_null() {
            continue;
        }
        if !first {
            builder.push(", ");
        }
        first = false;
        builder.push(format!("{} = ", support::column_name(key)));
        support::bind_value(&mut builder, value);
    }
    if first {
        return Ok(0);
    }
    builder.push(" where user_id = ");
    builder.push_bind(user_id);
    Ok(builder.build().execute(&mut **tx).await?.rows_affected())
}

async fn remove(
    State(state): State<AppState>,
    Path(user_ids): Path<String>,
) -> Result<AjaxResult, AppError> {
    // Java: `@PathVariable Long[] userIds` —— 任一段转不成 Long 就整体失败，文案带整段原文。
    let ids = support::path_long_list("userIds", &user_ids)?
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
    for id in &ids {
        if id == "1" {
            return Err(AppError::Service("不允许操作超级管理员用户".to_string()));
        }
    }
    let mut tx = state.db.begin().await?;
    let mut builder = QueryBuilder::<MySql>::new("delete from sys_user_role where user_id in (");
    let mut separated = builder.separated(", ");
    for id in &ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    builder.build().execute(&mut *tx).await?;
    let mut builder = QueryBuilder::<MySql>::new("delete from sys_user_post where user_id in (");
    let mut separated = builder.separated(", ");
    for id in &ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    builder.build().execute(&mut *tx).await?;
    let mut builder =
        QueryBuilder::<MySql>::new("update sys_user set del_flag = '1' where user_id in (");
    let mut separated = builder.separated(", ");
    for id in &ids {
        separated.push_bind(id.clone());
    }
    builder.push(")");
    let rows = builder.build().execute(&mut *tx).await?.rows_affected();
    tx.commit().await?;
    Ok(support::to_ajax(rows))
}

async fn reset_pwd(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let raw_password = text(&body, "password");
    if password_invalid(&raw_password) {
        return Ok(AjaxResult::error(
            "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号",
        ));
    }
    check_user_allowed(&body)?;
    let user_id = body
        .get("userId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("userId不能为空".to_string()))?;
    let rows = sqlx::query("update sys_user set password = ?, update_by = ? where user_id = ?")
        .bind(password::encode(&raw_password)?)
        .bind(user.user.user_name.clone().unwrap_or_default())
        .bind(user_id)
        .execute(&state.db)
        .await?
        .rows_affected();
    Ok(support::to_ajax(rows))
}

async fn change_status(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    check_user_allowed(&body)?;
    let user_id = body
        .get("userId")
        .and_then(Value::as_i64)
        .ok_or_else(|| AppError::Service("userId不能为空".to_string()))?;
    let mut entity = json!({
        "status": body.get("status").cloned().unwrap_or(Value::Null),
        "updateBy": user.user.user_name.clone().unwrap_or_default(),
    });
    if let Some(cert_entity_id) = body.get("certEntityId") {
        entity["certEntityId"] = cert_entity_id.clone();
    }
    if let Some(cert_id) = body.get("certId") {
        entity["certId"] = cert_id.clone();
    }
    let mut tx = state.db.begin().await?;
    let rows = update_user_row(&mut tx, &entity, user_id).await?;
    tx.commit().await?;
    Ok(support::to_ajax(rows))
}

async fn bind_uky(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    Json(body): Json<Value>,
) -> Result<AjaxResult, AppError> {
    let user_id = body
        .get("userId")
        .and_then(Value::as_i64)
        .or(user.user.user_id);
    let cert_entity_id = text(&body, "certEntityId");
    let cert_id = text(&body, "certId");
    if cert_entity_id.is_empty() {
        return Ok(AjaxResult::error("唯一实体标识不能为空"));
    }
    if cert_id.is_empty() {
        return Ok(AjaxResult::error("密码卡/USD-Key序列号不能为空"));
    }
    if let Some(found) = unique_value(&state.db, "cert_entity_id", &cert_entity_id).await? {
        if Some(found) != user_id {
            return Ok(AjaxResult::error("唯一实体标识已绑定，请确认！"));
        }
    }
    if let Some(found) = unique_value(&state.db, "cert_id", &cert_id).await? {
        if Some(found) != user_id {
            return Ok(AjaxResult::error("密码卡/USD-Key序列号已绑定，请确认！"));
        }
    }
    let Some(user_id) = user_id else {
        return Ok(AjaxResult::error("操作失败"));
    };
    let rows = sqlx::query(
        "update sys_user set cert_id = ?, cert_entity_id = ?, update_by = ? where user_id = ?",
    )
    .bind(cert_id)
    .bind(cert_entity_id)
    .bind(user.user.user_name.clone().unwrap_or_default())
    .bind(user_id)
    .execute(&state.db)
    .await?
    .rows_affected();
    Ok(support::to_ajax(rows))
}

async fn import_data(
    State(state): State<AppState>,
    Extension(user): Extension<LoginUser>,
    mut multipart: Multipart,
) -> Result<AjaxResult, AppError> {
    let mut file_bytes = Vec::new();
    let mut update_support = false;
    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|err| AppError::BadRequest(err.to_string()))?
    {
        match field.name() {
            Some("file") | Some("files") => {
                file_bytes = field
                    .bytes()
                    .await
                    .map_err(|err| AppError::BadRequest(err.to_string()))?
                    .to_vec();
            }
            Some("updateSupport") => {
                update_support = field
                    .text()
                    .await
                    .map(|text| text == "true")
                    .unwrap_or(false);
            }
            _ => {}
        }
    }
    let rows = crate::common::excel::read_rows(&file_bytes)?;
    if rows.is_empty() {
        return Err(AppError::Service("导入用户数据不能为空！".to_string()));
    }
    let header = rows[0].clone();
    let init_password = support::config_value(&state.db, "sys.user.initPassword").await?;
    let mut success = 0;
    let mut failures = Vec::new();
    for row in rows.iter().skip(1) {
        if row.iter().all(|cell| cell.trim().is_empty()) {
            continue;
        }
        let mut body = Map::new();
        for (index, name) in header.iter().enumerate() {
            let Some(cell) = row.get(index) else { continue };
            let field = match name.trim() {
                "用户编码" => "userNo",
                "部门编号" => "deptId",
                "登录名称" => "userName",
                "用户名称" => "nickName",
                "用户类型" => "userType",
                "用户邮箱" => "email",
                "手机号码" => "phonenumber",
                "用户性别" => "sex",
                "帐号状态" => "status",
                "证书Id" => "certId",
                "证书实体Id" => "certEntityId",
                "业务id" => "bussId",
                "业务名称" => "bussName",
                "单位名称" => "epsName",
                "租户单位id" => "tenantId",
                "租户单位名称" => "tenantName",
                "角色编码" => "roleCode",
                _ => continue,
            };
            if cell.trim().is_empty() {
                continue;
            }
            let value = match field {
                "userNo" | "deptId" | "tenantId" => match cell.trim().parse::<i64>() {
                    Ok(number) => json!(number),
                    Err(_) => json!(cell.trim()),
                },
                _ => json!(cell.trim()),
            };
            body.insert(field.to_string(), value);
        }
        let user_name = body
            .get("userName")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let existing = support::scalar_i64(
            &state.db,
            "select user_id from sys_user where user_name = ?",
            &user_name,
        )
        .await?;
        let body_value = Value::Object(body);
        let result = if existing.is_none() {
            let mut entity = entity_from_body(&body_value);
            if let Some(object) = entity.as_object_mut() {
                object.insert(
                    "password".to_string(),
                    Value::String(password::encode(&init_password)?),
                );
                object.insert(
                    "createBy".to_string(),
                    Value::String(user.user.user_name.clone().unwrap_or_default()),
                );
            }
            apply_dept(&state, &mut entity).await?;
            let mut tx = state.db.begin().await?;
            insert_user_row(&mut tx, &entity).await?;
            tx.commit().await?;
            Ok(())
        } else if update_support {
            let mut entity = entity_from_body(&body_value);
            if let Some(object) = entity.as_object_mut() {
                object.insert(
                    "updateBy".to_string(),
                    Value::String(user.user.user_name.clone().unwrap_or_default()),
                );
            }
            apply_dept(&state, &mut entity).await?;
            let mut tx = state.db.begin().await?;
            update_user_row(&mut tx, &entity, existing.unwrap_or_default()).await?;
            tx.commit().await?;
            Ok(())
        } else {
            Err(format!("账号 {user_name} 已存在"))
        };
        match result {
            Ok(()) => success += 1,
            Err(message) => failures.push(message),
        }
    }
    if !failures.is_empty() {
        return Err(AppError::Service(format!(
            "很抱歉，导入失败！共 {} 条数据格式不正确，错误如下：{}",
            failures.len(),
            failures.join("；")
        )));
    }
    Ok(AjaxResult::success_msg(format!(
        "恭喜您，数据已全部导入成功！共 {success} 条"
    )))
}
