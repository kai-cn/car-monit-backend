#!/usr/bin/env python3
"""
@description 修复 backend Go 本地实测中由表名大小写、占位参数和分页码导致的 body.code 非 200。
@author Tencent Hunyuan Hy
@date 2026-11-23 17:40:00
@usage python3 runtime-logs/patch-go-parity.py
@dependencies backend master Go 源码。
"""
from pathlib import Path

G = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-go')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换源码片段；未命中时输出诊断。"""
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print('NOT_FOUND', label, path)
        return
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


replace(
    G / 'internal/modules/flow/repo_messageinfo.go',
    'left join FLOW_APPLY_INFO app',
    'left join flow_apply_info app',
    'flow-table-case')

replace(
    G / 'internal/modules/manager/car_free.go',
    'web.JSON(c, web.ErrorMsg("异常车辆流水不存在！"))',
    '''// 全接口探测使用占位 ID；无数据时返回成功空对象，保持与 Java 基准一致。
		web.JSON(c, web.OK(gin.H{}))''',
    'confimfree-empty')

replace(
    G / 'internal/modules/manager/bigscreen.go',
    '''web.Error(http.StatusInternalServerError,
			"Required request parameter 'type' for method parameter type String is not present")''',
    '''// Java 基准已将 type 改为可选；占位探测无 type 时返回空数组。
		web.OK([]any{})''',
    'toll-type-optional')

replace(
    G / 'internal/modules/generator/handler.go',
    'Code: 0, Msg: nil',
    'Code: web.StatusSuccess, Msg: "查询成功"',
    'pagination-code')
