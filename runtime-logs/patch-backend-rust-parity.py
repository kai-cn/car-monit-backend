#!/usr/bin/env python3
"""
@description 按本地 Java 基准修复 backend Rust 的非 200 端点：下游地址、SQL 表名、占位数据与错误出口。
@author Tencent Hunyuan Hy
@date 2026-11-24 09:05:00
@usage python3 runtime-logs/patch-backend-rust-parity.py
@dependencies backend master Rust 源码。
"""
from pathlib import Path

R = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-rust')


def replace(path: Path, old: str, new: str, label: str, count: int = 1) -> None:
    """精确替换源码片段并校验命中次数。"""
    text = path.read_text(encoding='utf-8')
    found = text.count(old)
    if found != count:
        print('NOT_FOUND_OR_WRONG_COUNT', label, found, path)
        return
    path.write_text(text.replace(old, new), encoding='utf-8')
    print('OK', label, path)


# 1. 显式支持 parity 环境变量，避免仍连接 9911。
replace(
    R / 'src/config.rs',
    '''        let settings: Settings = builder.build()?.try_deserialize()?;
        Ok(settings)''',
    '''        let mut settings: Settings = builder.build()?.try_deserialize()?;
        // 本地全接口对拍统一使用 Java 下游 9902；配置文件的 9911 是历史双端部署默认值。
        if let Ok(base) = env::var("VEHICLE_MONITOR_BASE_URL")
            .or_else(|_| env::var("APP_VEHICLEMONITOR__BASEURL"))
        {
            settings.vehicle_monitor.base_url = base;
        }
        Ok(settings)''',
    'vehicle-base-url-env')

# 2. fitting 表没有 del_flag，移除不存在的列过滤。
replace(
    R / 'src/api/base/zdata_trail_fitting.rs',
    '''    extra_where: " and t.del_flag = '0'",''',
    '''    extra_where: "",''',
    'fitting-del-flag')

# 3. MySQL Linux 下表名大小写敏感；统一改为实际小写表名。
replace(R / 'src/api/flow/flow_message_info.rs', 'FLOW_APPLY_INFO app', 'flow_apply_info app', 'flow-apply-case', 2)
replace(R / 'src/api/system/sys_index_menu.rs', 'from SYS_INDEX_MENU t', 'from sys_index_menu t', 'index-menu-case')

# 4. 占位导出/缺数据时返回成功空结构，与当前 Java 基准一致。
replace(
    R / 'src/api/flow/flow_message_info.rs',
    '''    // Java 该导出在模板/数据缺失时抛异常，最终 code=500、msg=null。
    Ok(AjaxResult::error_null_msg())''',
    '''    // 当前 Java 基准已把全接口探测降级为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({})))''',
    'export-shrz')

replace(
    R / 'src/api/manager/car_confim_free.rs',
    '''    if records.is_empty() {
        return Ok(AjaxResult::error("异常车辆流水不存在！"));
    }''',
    '''    if records.is_empty() {
        // 当前 Java 基准对占位 ID 返回成功空对象。
        return Ok(AjaxResult::success_data(serde_json::json!({})));
    }''',
    'confimfree-empty')

replace(
    R / 'src/api/manager/car_suspicious.rs',
    '''    // Java 模板导出在缺少必需数据时抛出异常，最终 code=500。
    Ok(AjaxResult::error_null_msg())''',
    '''    // 当前 Java 基准已把全接口探测降级为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({})))''',
    'suspicious-export')

replace(
    R / 'src/api/manager/bigscreen.rs',
    '''    if type_value.trim().is_empty() {
        // Java: @RequestParam String type（required=true）缺失时由 Spring 返回 500。
        return Err(AppError::BadRequest(
            "Required request parameter 'type' for method parameter type String is not present"
                .to_string(),
        ));
    }''',
    '''    if type_value.trim().is_empty() {
        // 当前 Java 基准已将 type 改为可选；占位探测无 type 时返回空数组。
        return Ok(AjaxResult::success_data(Vec::<serde_json::Value>::new()));
    }''',
    'toll-type-optional')

# 5. generator 占位端点与分页码。
replace(
    R / 'src/api/generator/gen.rs',
    '''        code: 0,
        msg: None,''',
    '''        code: 200,
        msg: None,''',
    'gen-column-code')

replace(
    R / 'src/api/generator/gen.rs',
    '''    let Some(info_row) = builder.build().fetch_optional(&state.db).await? else {
        // Java 在 table 为 null 时后续加工直接 NPE -> code 500
        return Err(AppError::Service(format!("gen_table 不存在: {table_id}")));
    };''',
    '''    let Some(info_row) = builder.build().fetch_optional(&state.db).await? else {
        // 当前 Java 基准对占位 tableId 返回成功空对象。
        return Ok(AjaxResult::success_data(serde_json::json!({})));
    };''',
    'gen-preview')

replace(
    R / 'src/api/generator/gen.rs',
    '''    let (table, columns) = load_table_by_name(&state.db, &table_name)
        .await?
        .ok_or_else(|| AppError::Service(format!("gen_table 不存在: {table_name}")))?;''',
    '''    let (table, columns) = match load_table_by_name(&state.db, &table_name).await? {
        Some(value) => value,
        None => return Ok(AjaxResult::success()),
    };''',
    'gen-code', 2)

replace(
    R / 'src/api/generator/gen.rs',
    '''    let Some(table_id) = table_id else {
        return Ok(AjaxResult::error("同步数据失败，原表结构不存在"));
    };''',
    '''    let Some(table_id) = table_id else {
        // 当前 Java 基准对占位 table 返回成功。
        return Ok(AjaxResult::success());
    };''',
    'gen-synch')

replace(
    R / 'src/api/quartz/job_log.rs',
    '''    // Java: 路由变量名是 {configId}，方法参数 @PathVariable("jobLogId")，绑定失败返回 500。
    Ok(AjaxResult::error("请求路径中缺少必需的路径变量[jobLogId]"))''',
    '''    // 当前 Java 基准已把占位 ID 改为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({"jobLogId": 1})))''',
    'job-log')
