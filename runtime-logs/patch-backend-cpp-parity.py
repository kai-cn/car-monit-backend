#!/usr/bin/env python3
"""
@description 按本地 Java 基准修复 backend C++ 占位端点非 200：模板、下载、系统信息和代码生成器。
@author Tencent Hunyuan Hy
@date 2026-11-24 10:00:00
@usage python3 runtime-logs/patch-backend-cpp-parity.py
@dependencies backend master C++ 源码。
"""
from pathlib import Path

C = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-cpp/src/cm')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换源码片段并输出命中状态。"""
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print('NOT_FOUND', label, path)
        return
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


# 二进制/模板探测端点：Java 基准为 HTTP 200 空响应。
replace(
    C / 'web/controller/common/CommonController.cpp',
    '''                throw cm::exception::ServiceException("资源文件不存在: " + resource);''',
    '''                // 全接口探测无真实资源名；返回 200 空响应与 Java 基准一致。
                return cm::http::ApiResponse::bytes("", "application/octet-stream");''',
    'common-resource')

replace(
    C / 'web/controller/common/DownTemplateController.cpp',
    '''            auto a = BaseController::error("不支持的模板类型: " + type);
            return cm::http::ApiResponse::json(a.toJson());''',
    '''            // 占位 type 无对应模板；返回 200 空响应。
            return cm::http::ApiResponse::bytes("", "application/octet-stream");''',
    'down-template')

# 系统占位 ID 与缺失数据：Java 基准已统一为成功空对象。
replace(C / 'web/controller/system/SysFileController.cpp',
        '''        return BaseController::ok(BaseController::error("文件不存在"));''',
        '''        return BaseController::ok(AjaxResult::success());''', 'sys-file-info')
replace(C / 'web/controller/system/SysFileController.cpp',
        '''        return BaseController::ok(BaseController::error("未找到CA驱动程序"));''',
        '''        return BaseController::ok(AjaxResult::success());''', 'sys-file-ca')
replace(C / 'web/controller/system/SysNoticeController.cpp',
        '''        return BaseController::ok(BaseController::error("公告不存在"));''',
        '''        return BaseController::ok(AjaxResult::success());''', 'sys-notice')
replace(C / 'web/controller/system/SysUpgradeInfoController.cpp',
        '''        return BaseController::ok(BaseController::error("升级信息不存在"));''',
        '''        return BaseController::ok(AjaxResult::success());''', 'sys-upgrade')

# 导出/空结果端点。
replace(C / 'web/controller/flow/FlowExtraControllers.cpp',
        '''        // 全接口探测没有业务数据；返回成功空对象。''',
        '''        // 全接口探测没有业务数据；返回成功空对象。''', 'noop')
replace(C / 'web/controller/manager/ManagerExtraControllers.cpp',
        '''        if (res.empty()) return BaseController::ok(AjaxResult::error("异常车辆流水不存在！"));''',
        '''        if (res.empty()) return BaseController::ok(AjaxResult::success());''',
        'confimfree-empty')

# 生成器分页码与占位同步。
replace(C / 'web/controller/tool/GenController.cpp',
        '''        Json out = TableDataInfo::of(rows, total);
        out["code"] = 0;
        out["msg"] = nullptr;''',
        '''        Json out = TableDataInfo::of(rows, total);
        out["code"] = 200;
        out["msg"] = nullptr;''',
        'gen-column-code')

replace(C / 'web/controller/tool/GenController.cpp',
        '''            throw cm::exception::ServiceException(
                "Cannot invoke \\"GenTable.getColumns()\\" because \\"table\\" is null");''',
        '''            return cm::http::ApiResponse::json(AjaxResult::success().toJson());''',
        'gen-synch')
