// 来源: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/*ServiceImpl.java 的统一 saveXxx 片段。
// 职责: 流程各表的「UUID 主键 + 审计字段 + del_flag=0」保存逻辑。
// 对应关系: StringUtils.getUUID + epsId/createBy/updateBy + mapper.insert/update。

use serde_json::{json, Value};

use crate::api::support;
use crate::domain::LoginUser;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

/// 各 flow Service 的 `saveXxx`：id 为空 -> 新增（UUID/审计），否则更新。
pub async fn save_flow_entity(
    state: &AppState,
    user: &LoginUser,
    body: &Value,
    table: &str,
) -> Result<AjaxResult, AppError> {
    let id = body
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    let mut entity = body.clone();
    if id.is_empty() {
        let now = support::now_string();
        if let Some(object) = entity.as_object_mut() {
            object.insert("delFlag".to_string(), json!("0"));
            object.insert("epsId".to_string(), json!(user.user.dept_id));
            object.insert("updateBy".to_string(), json!(user.user.user_id));
            object.insert("updateTime".to_string(), json!(now));
        }
        support::save_or_update(state, user, &entity, table, "id", true, true).await
    } else {
        support::save_or_update(state, user, &entity, table, "id", true, false).await
    }
}

/// 批量软删除。
pub async fn delete_flow_ids(
    state: &AppState,
    table: &str,
    ids: &str,
) -> Result<AjaxResult, AppError> {
    let ids = support::ids_param(ids);
    let count = support::soft_delete_by_ids(&state.db, table, "id", &ids).await?;
    Ok(support::success_count(count))
}
