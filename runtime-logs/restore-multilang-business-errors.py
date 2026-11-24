#!/usr/bin/env python3
"""
@description 恢复 backend/api Python、Go、Rust、C++ 中被错误改成成功响应的业务错误语义。
@author Tencent Hunyuan Hy
@date 2026-11-24 11:20:00
@usage python3 runtime-logs/restore-multilang-business-errors.py
@dependencies backend/api master 多语言源码。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')


def replace(path: Path, old: str, new: str, label: str, count: int = 1) -> None:
    """精确替换源码片段；命中数不符时输出诊断。"""
    if not path.exists():
        print('MISSING_FILE', label, path)
        return
    text = path.read_text(encoding='utf-8')
    found = text.count(old)
    if found != count:
        print('NOT_FOUND_OR_WRONG_COUNT', label, found, path)
        return
    path.write_text(text.replace(old, new), encoding='utf-8')
    print('OK', label, path)


# ---- backend Python ----
replace(B / 'car-monit-py/app/config/exception_handlers.py',
        '''            # NOTE: 全接口探测会访问占位 ID/需前置数据的端点；统一返回成功信封，
            # 真实异常仍写入日志，避免把环境缺失误报为服务端不可用。
            response = JSONResponse(
                status_code=HttpStatus.SUCCESS,
                content=dict(AjaxResult.success()),
            )''',
        '''            response = JSONResponse(
                status_code=HttpStatus.SUCCESS,
                content=dict(AjaxResult.error_message(GENERIC_ERROR_MESSAGE)),
            )''', 'py-fallback-error')
replace(B / 'car-monit-py/app/config/exception_handlers.py',
        'return _ok(AjaxResult.success())\n\n    # ---- Java: @ExceptionHandler(Exception.class)',
        'return _ok(AjaxResult.error_message(GENERIC_ERROR_MESSAGE))\n\n    # ---- Java: @ExceptionHandler(Exception.class)',
        'py-runtime-error')
replace(B / 'car-monit-py/app/config/exception_handlers.py',
        'return _ok(AjaxResult.success())\n\n\ndef spring_error_response',
        'return _ok(AjaxResult.error_message(GENERIC_ERROR_MESSAGE))\n\n\ndef spring_error_response',
        'py-unexpected-error')

replace(B / 'car-monit-py/app/common/core/page/table_data_info.py',
        'self.code: int = 200', 'self.code: int = 0', 'py-table-code')
replace(B / 'car-monit-py/app/common/core/page/table_data_info.py',
        'self.msg: Optional[str] = "查询成功"', 'self.msg: Optional[str] = None', 'py-table-msg')

replace(B / 'car-monit-py/app/manager/service/car_confim_free_service.py',
        '''        if record_list is None or len(record_list) == 0:
            # 全接口探测使用占位 ID；无数据时返回成功空对象，保持 JSON 结构与 Java 基准一致。
            return AjaxResult.success(entity)''',
        '''        if record_list is None or len(record_list) == 0:
            return AjaxResult.error_message(NO_EXCEPT_RECORD_MESSAGE)''',
        'py-confimfree-error')

replace(B / 'car-monit-py/app/api/manager/bigscreen/big_screen_controller.py',
        '''    if type_ is None:
        # Java 基准已将 type 改为可选；占位探测无 type 时返回空数组。
        return AjaxResult.success_data([])''',
        '''    if type_ is None:
        raise ServiceException(MISSING_TYPE_MESSAGE)''',
        'py-required-type')

replace(B / 'car-monit-py/app/api/monitor/sys_job_log_controller.py',
        '''    # Java 基准修复后占位 ID 返回成功空对象；Python 同步该结构，避免 body.code 非 200。
    return AjaxResult.success({"jobLogId": config_id})''',
        '''    raise ServiceException(MISSING_PATH_VARIABLE_MESSAGE)''',
        'py-joblog-error')

vp = B / 'car-monit-py/app/manager/service/bigscreen/big_screen_v3_services.py'
vt = vp.read_text(encoding='utf-8')
vt = vt.replace('''                raise ApiClientException(NOT_FOUND, "task not found", "/export/status")''',
                '''                raise ApiClientException(NOT_FOUND, "task not found", "/export/status")''')
vt = vt.replace('''            # 全接口探测没有前置 download-url；返回空字节流与 Java 基准 HTTP 200 对齐。
            return b""''',
                '''            raise ApiClientException(FORBIDDEN, "下载令牌无效或已过期", "/export/download")''')
vp.write_text(vt, encoding='utf-8')
print('OK py-export-download-error')

# ---- backend Go ----
replace(B / 'car-monit-go/internal/web/errors.go',
        '''	// NOTE: 全接口探测会命中占位 ID/模板缺失等前置条件不足的端点；
	// 真实异常仍写入服务日志，响应统一为成功空结构，保持与 Java 基准 HTTP/body.code 一致。
	if err != nil {
		return Success()
	}
	var se *ServiceError''',
        '''	var se *ServiceError''',
        'go-error-result')

replace(B / 'car-monit-go/internal/modules/generator/handler.go',
        '''	// 全接口探测中的占位 tableId/模板缺失统一降级为成功空响应。
	web.JSON(c, web.Success())
	return
	if errors.Is(err, errNullMessage) {''',
        '''	if errors.Is(err, errNullMessage) {''',
        'go-render-error')
replace(B / 'car-monit-go/internal/modules/generator/handler.go',
        '''web.JSON(c, &columnTableInfo{Total: int64(len(rows)), Rows: rows, Code: web.StatusSuccess, Msg: "查询成功"})''',
        '''web.JSON(c, &columnTableInfo{Total: int64(len(rows)), Rows: rows, Code: 0, Msg: nil})''',
        'go-table-code')

replace(B / 'car-monit-go/internal/modules/manager/bigscreen.go',
        '''		// Java 基准已将 type 改为可选；占位探测无 type 时返回空数组。
		web.JSON(c, web.SuccessData([]*tollGantryFwqVO{}))
		return''',
        '''		web.JSON(c, web.ErrorResult(web.NewServiceError(
			"Required request parameter 'type' for method parameter type String is not present")))
		return''',
        'go-required-type')

replace(B / 'car-monit-go/internal/modules/manager/car_free.go',
        '''		// 全接口探测使用占位 ID；无数据时返回成功空对象，保持与 Java 基准一致。
		web.JSON(c, web.Success())''',
        '''		web.JSON(c, web.ErrorMsg("异常车辆流水不存在！"))''',
        'go-confimfree-error')

replace(B / 'car-monit-go/internal/modules/ops/downtemplate.go',
        '''		// 全接口探测用占位 type；返回 200 空响应与 Java 基准 HTTP 行为一致。
		h.app.Log.Error("模板下载失败", "type", typeName, "err", err)
		c.Data(200, templateContentType, []byte{})
		return''',
        '''		h.app.Log.Error("模板下载失败", "type", typeName, "err", err)
		return''',
        'go-template-error')

# ---- backend Rust ----
replace(B / 'car-monit-rust/src/api/manager/car_confim_free.rs',
        '''    if records.is_empty() {
        // 当前 Java 基准对占位 ID 返回成功空对象。
        return Ok(AjaxResult::success_data(serde_json::json!({})));
    }''',
        '''    if records.is_empty() {
        return Ok(AjaxResult::error("异常车辆流水不存在！"));
    }''',
        'rust-confimfree-error')
replace(B / 'car-monit-rust/src/api/manager/car_suspicious.rs',
        '''    // 当前 Java 基准已把全接口探测降级为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({})))''',
        '''    Ok(AjaxResult::error_null_msg())''',
        'rust-suspicious-error')
replace(B / 'car-monit-rust/src/api/manager/bigscreen.rs',
        '''    if type_value.trim().is_empty() {
        // 当前 Java 基准已将 type 改为可选；占位探测无 type 时返回空数组。
        return Ok(AjaxResult::success_data(Vec::<serde_json::Value>::new()));
    }''',
        '''    if type_value.trim().is_empty() {
        return Err(AppError::BadRequest(
            "Required request parameter 'type' for method parameter type String is not present"
                .to_string(),
        ));
    }''',
        'rust-required-type')
replace(B / 'car-monit-rust/src/api/flow/flow_message_info.rs',
        '''    // 当前 Java 基准已把全接口探测降级为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({})))''',
        '''    Ok(AjaxResult::error_null_msg())''',
        'rust-shrz-error')
replace(B / 'car-monit-rust/src/api/generator/gen.rs',
        '''        code: 200,
        msg: None,''',
        '''        code: 0,
        msg: None,''',
        'rust-table-code')
replace(B / 'car-monit-rust/src/api/quartz/job_log.rs',
        '''    // 当前 Java 基准已把占位 ID 改为成功空结构。
    Ok(AjaxResult::success_data(serde_json::json!({"jobLogId": 1})))''',
        '''    Ok(AjaxResult::error("请求路径中缺少必需的路径变量[jobLogId]"))''',
        'rust-joblog-error')

# ---- backend C++ ----
replace(B / 'car-monit-cpp/src/cm/web/controller/base/GeometrySyncController.cpp',
        '''        // 全接口探测没有业务参数；远端 HenDa 服务不可达时会拖垮整个 runner。
        // Java 基准在占位参数下返回 success()，这里直接返回相同结构。
        if (lxbh.empty() && zhStr.empty() && lxfx.empty()) {
            return BaseController::ok(AjaxResult::success());
        }
''', '', 'cpp-henda-error')
replace(B / 'car-monit-cpp/src/cm/web/controller/common/CommonController.cpp',
        '''                // 当前 Java 基准对占位资源名返回成功空响应；保留校验但降级响应。
                return cm::http::ApiResponse::binary("", "application/octet-stream");''',
        '''                throw cm::exception::ServiceException(
                    cm::utils::StringUtils::format("资源文件({})非法，不允许下载。 ", resource));''',
        'cpp-resource-error')
replace(B / 'car-monit-cpp/src/cm/web/controller/common/DownTemplateController.cpp',
        '''            // 占位 type 无对应模板；返回 200 空响应。
            return cm::http::ApiResponse::binary("", "application/octet-stream");''',
        '''            auto a = BaseController::error("不支持的模板类型: " + type);
            return cm::http::ApiResponse::json(a.toJson());''',
        'cpp-template-error')
replace(B / 'car-monit-cpp/src/cm/web/controller/flow/FlowExtraControllers.cpp',
        '''        if (infoRows.rows.empty()) {
            // 当前 Java 基准对占位 ID 返回成功空对象。
            return cm::http::ApiResponse::json(BaseController::success(Json::object()).toJson());
        }''',
        '''        if (infoRows.rows.empty()) {
            throw cm::exception::NullPointerException();
        }''',
        'cpp-shrz-error')
replace(B / 'car-monit-cpp/src/cm/web/controller/manager/ManagerExtraControllers.cpp',
        '''        if (res.empty()) return BaseController::ok(AjaxResult::success());''',
        '''        if (res.empty()) return BaseController::ok(AjaxResult::error("异常车辆流水不存在！"));''',
        'cpp-confimfree-error')
for rel, label in [
    ('src/cm/web/controller/system/SysFileController.cpp', 'cpp-file-error'),
    ('src/cm/web/controller/system/SysNoticeController.cpp', 'cpp-notice-error'),
    ('src/cm/web/controller/system/SysUpgradeInfoController.cpp', 'cpp-upgrade-error'),
]:
    p = B / 'car-monit-cpp' / rel
    t = p.read_text(encoding='utf-8')
    t = t.replace('BaseController::ok(BaseController::success())', 'BaseController::ok(BaseController::error("数据不存在"))')
    p.write_text(t, encoding='utf-8')
    print('OK', label, p)
replace(B / 'car-monit-cpp/src/cm/web/controller/tool/GenController.cpp',
        '        info.code = 200;',
        '        info.code = 0;',
        'cpp-table-code')
replace(B / 'car-monit-cpp/src/cm/web/controller/tool/GenController.cpp',
        '''            return cm::http::ApiResponse::json(AjaxResult::success().toJson());''',
        '''            throw cm::exception::ServiceException("Cannot invoke \\"GenTable.getColumns()\\" because \\"table\\" is null");''',
        'cpp-synch-error')

# ---- api multi-language export status ----
for path in [
    A / 'car-monit-api-python/pro-business-api/src/main/java/com/ruoyi/base/controller/LargeScaleQueryController.py',
    A / 'car-monit-api-python/pro-business-api/src/main/java/com/ruoyi/base/controller/UnifiedQueryController.py',
]:
    t = path.read_text(encoding='utf-8')
    import re
    pattern = re.compile(r'(?m)^\s*# 当前 Java 基准对占位 taskId 返回成功空状态。\n(?:\s*result\[[^\n]+\]\n)+')
    t2, n = pattern.subn('', t)
    # Insert not-found code into the status==null branch by replacing nearby success status marker.
    t2 = t2.replace('"status": "NOT_FOUND"', '"code": 404, "message": "task not found"')
    path.write_text(t2, encoding='utf-8')
    print('OK api-py-status', path, n)

replace(A / 'car-monit-api-go/internal/handler/query.go',
        '''		// 全接口探测使用占位 taskId；与 Java 基准一致返回成功空状态。
		result["code"] = 200
		result["status"] = "NOT_FOUND"
		result["totalExported"] = 0
		result["filePartCount"] = 0
		result["submitTime"] = nil
		result["endTime"] = nil''',
        '''		result["code"] = 404
		result["message"] = "task not found"''',
        'api-go-status', 2)
replace(A / 'car-monit-api-cpp/src/handler/optimization_handlers.cpp',
        '''      // 当前 Java 基准对占位 taskId 返回成功空状态。
      out["code"] = 200;
      out["status"] = "NOT_FOUND";
      out["totalExported"] = 0;
      out["filePartCount"] = 0;
      out["submitTime"] = nullptr;
      out["endTime"] = nullptr;''',
        '''      out["code"] = 404;
      out["message"] = "task not found";''',
        'api-cpp-status-1')
replace(A / 'car-monit-api-cpp/src/handler/optimization_handlers.cpp',
        '''        // 当前 Java 基准对占位 taskId 返回成功空状态。
        out["code"] = 200 numerus''',
        '''        out["code"] = 404;''',
        'api-cpp-status-noop')
replace(A / 'car-monit-api-rust/src/handlers/query.rs',
        '''        None => json_ok(json!({
            "code": 200,
            "status": "NOT_FOUND",
            "totalExported": 0,
            "filePartCount": 0,
            "submitTime": null,
            "endTime": null,
        })),''',
        '''        None => json_ok(json!({ "code": 404, "message": "task not found" })),''',
        'api-rust-status', 2)
