#!/usr/bin/env python3
"""
@description 恢复 backend/api Java 基准中被错误改成成功响应的业务错误语义，保留真实绑定修复。
@author Tencent Hunyuan Hy
@date 2026-11-24 11:10:00
@usage python3 runtime-logs/restore-java-business-errors.py
@dependencies backend/api master Java 源码。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换 Java 源码片段；未命中时输出诊断。"""
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print('NOT_FOUND', label, path)
        return
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


# backend: required query parameter is a real business error.
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java',
    '@RequestParam(value = "type", required = false, defaultValue = "") String type',
    '@RequestParam String type',
    'required-type')

# backend: upstream API error must remain an error.
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java',
    '''            logger.warn("[拟合轨迹] api 查询失败 code={} msg={}，降级为空分页", e.getCode(), e.getMessage());
            return FlowApiSupport.page(null);''',
    '''            logger.warn("[拟合轨迹] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);''',
    'fitting-upstream-error')

# backend: big-screen export status/download business errors.
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java',
    '''            // 全接口探测使用占位 taskId；未找到任务时仍返回成功空状态，避免基准 body.code 非 200。
            Map<String, Object> empty = new HashMap<>();
            empty.put("taskId", taskId);
            empty.put("status", "NOT_FOUND");
            return AjaxResult.success(empty);''',
    '''            return error(e);''',
    'export-status-error')
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java',
    '''            log.warn("[导出下载] code={} msg={}，全接口探测降级为空响应", e.getCode(), e.getMessage());''',
    '''            log.warn("[导出下载] code={} msg={}", e.getCode(), e.getMessage());''',
    'export-download-log')
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java',
    '''            response.setStatus(200);
            response.setContentType("application/json;charset=UTF-8");
            try
            {
                response.getWriter().write(JSON.toJSONString(AjaxResult.success()));''',
    '''            response.setStatus(e.getCode() == ApiErrorCode.FORBIDDEN ? 403 : 404);
            response.setContentType("application/json;charset=UTF-8");
            try
            {
                response.getWriter().write(JSON.toJSONString(AjaxResult.error(e.getMessage())));''',
    'export-download-error')

# backend: no exception records is a business error.
replace(
    B / 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarConfimFreeServiceImpl.java',
    '''        if (carExceptRecordList == null || carExceptRecordList.isEmpty())
        {
            // 全接口探测使用占位 ID；无数据时返回成功空对象，保持 JSON 结构与有数据时一致。
            return AjaxResult.success(carConfimFree);
        }''',
    '''        if (null != carExceptRecordList && carExceptRecordList.size() > 0)
        {
        }
        else
        {
            return AjaxResult.error("异常车辆流水不存在！");
        }''',
    'confimfree-error')

# backend: original TableDataInfo code default semantics.
replace(
    B / 'ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java',
    '''    /** 消息状态码：统一成功口径为 200 */
    private int code = 200;''',
    '''    /** 消息状态码 */
    private int code;''',
    'table-code')

# backend: generator null data must remain an error.
replace(
    B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java',
    '''        String[] tableNames = StringUtils.isEmpty(tables) ? new String[0] : Convert.toStrArray(tables);
        if (tableNames.length == 0) {
            genCode(response, new byte[0]);
            return;
        }
        byte[] data = genTableService.downloadCode(tableNames);
        genCode(response, data == null ? new byte[0] : data);''',
    '''        String[] tableNames = Convert.toStrArray(tables);
        byte[] data = genTableService.downloadCode(tableNames);
        genCode(response, data);''',
    'batch-gen-error')

# backend: empty generator rows are real error states.
gp = B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java'
gt = gp.read_text(encoding='utf-8')
gt = gt.replace('''        if (genTable == null) {
            return new GenTable();
        }
''', '', 1)
gt = gt.replace('''        if (table == null) {
            return dataMap;
        }
''', '', 1)
gt = gt.replace('''        if (table == null) {
            return;
        }
''', '', 3)
gp.write_text(gt, encoding='utf-8')
print('OK gen-null-errors')

# backend: null export data must not be wrapped as success.
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java',
    '''        if (messageInfo == null) {
            return AjaxResult.success(map);
        }
''',
    '',
    'flow-shrz-error')
replace(
    B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java',
    '''        if (carSuspicious == null) {
            carSuspicious = new CarSuspicious();
        }
''',
    '',
    'suspicious-export-error')

# api: unknown export task must remain 404/task not found.
for p in [
    A / 'pro-business-api/src/main/java/com/ruoyi/base/controller/LargeScaleQueryController.java',
    A / 'pro-business-api/src/main/java/com/ruoyi/base/controller/UnifiedQueryController.java',
]:
    t = p.read_text(encoding='utf-8')
    old = '''            // 全接口探测使用占位 taskId；未命中时返回成功空状态，保持 JSON 结构与有任务时一致。
            result.put("code", 200);
            result.put("status", "NOT_FOUND");
            result.put("totalExported", 0);
            result.put("filePartCount", 0);
            result.put("submitTime", null);
            result.put("endTime", null);'''
    new = '''            result.put("code", 404);
            result.put("message", "task not found");'''
    if old in t:
        p.write_text(t.replace(old, new, 1), encoding='utf-8')
        print('OK api-task-error', p)
    else:
        old2 = '''            // 全接口探测使用占位 taskId；未命中时返回成功空状态，保持 JSON 结构与有任务时一致。
            result.put("code", 200);
            result.put("status", "NOT_FOUND");
            result.put("totalExported", 0);
            result.put("filePartCount", 0);
            result.put("submitTime", null);
            result.put("endTime", null);
            return result;'''
    # Unified variant has 12-space indentation.
    old2 = old2.replace('            ', '        ')
    new2 = '''        result.put("code", 404);
        result.put("message", "task not found");
        return result;'''
    if old2 in t:
        p.write_text(t.replace(old2, new2, 1), encoding='utf-8')
        print('OK api-task-error-unified', p)
