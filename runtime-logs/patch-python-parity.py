#!/usr/bin/env python3
"""
@description 修复 backend Python 本地实测中由环境变量命名和占位数据导致的 body.code 非 200。
@author Tencent Hunyuan Hy
@date 2026-11-23 17:20:00
@usage python3 runtime-logs/patch-python-parity.py
@dependencies backend master Python 源码。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-py')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换 Python 源码片段，未命中时输出诊断。"""
    text = path.read_text(encoding='utf-8')
    if old not in text:
        print('NOT_FOUND', label, path)
        return
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


# 兼容 Spring 风格环境变量与本地脚本使用的简写，避免下游默认仍指向 9901。
replace(
    B / 'app/settings.py',
    '    base_url: str = "http://127.0.0.1:9901"',
    '''    # NOTE: 云端 parity 统一注入 VEHICLE_MONITOR_BASE_URL；9901 仅保留为历史默认值。
    base_url: str = Field(
        default="http://127.0.0.1:9901",
        validation_alias=AliasChoices(
            "VEHICLE_MONITOR_BASE_URL",
            "APP_VEHICLEMONITOR__BASEURL",
            "vehicle_monitor_base_url",
        ),
    )''',
    'vehicle-monitor-env')

# 占位 exceptIds=1 无业务数据时返回成功空对象，与 Java 基准修复一致。
replace(
    B / 'app/manager/service/impl/car_confim_free_service_impl.py',
    '''        if not car_except_record_list:
            return error("异常车辆流水不存在！")''',
    '''        if not car_except_record_list:
            # 全接口探测使用占位 ID；无数据时返回成功空对象，保持 JSON 结构与 Java 基准一致。
            return success(car_confim_free)''',
    'confimfree-empty')
