#!/usr/bin/env python3
"""
@description 按父提交精确恢复错误语义，并对确认为真实修复的改动做最小重放。
@author Tencent Hunyuan Hy
@date 2026-11-24 11:30:00
@usage python3 runtime-logs/restore-business-semantics-exact.py
@dependencies git、backend/api master 工作树。
"""
from pathlib import Path
import subprocess

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')


def restore(repo: Path, commit: str, rel: str) -> None:
    """从指定提交的父版本恢复单个文件。"""
    p = repo / rel
    data = subprocess.run(['git', '-C', str(repo), 'show', f'{commit}^:{rel}'],
                          text=True, capture_output=True, check=True).stdout
    p.write_text(data, encoding='utf-8')
    print('RESTORED', commit, rel)


def replace(repo: Path, rel: str, old: str, new: str, label: str, count: int = 1) -> None:
    """在恢复后的文件中重放精确的真实修复。"""
    p = repo / rel
    t = p.read_text(encoding='utf-8')
    found = t.count(old)
    if found != count:
        print('REPLAY_NOT_FOUND_OR_WRONG_COUNT', label, found, p)
        return
    p.write_text(t.replace(old, new, count), encoding='utf-8')
    print('REPLAYED', label, p)


# ---- Java baseline: restore original business errors ----
for rel in [
    'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java',
]:
    restore(B, 'b1f43f39', rel)
for rel in [
    'ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java',
    'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java',
    'ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java',
    'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java',
    'ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java',
]:
    restore(B, '55f3f80b', rel)
for rel in [
    'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java',
    'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java',
    'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarConfimFreeServiceImpl.java',
]:
    restore(B, '2efad537', rel)

# Keep the real primary-key binding fixes for generator column and job log.
replace(B, 'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java',
        'public TableDataInfo columnList(Long tableId)',
        'public TableDataInfo columnList(@PathVariable("talbleId") Long tableId)',
        'java-gen-column-binding')
replace(B, 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java',
        '@GetMapping(value = "/{configId}")',
        '@GetMapping(value = "/{jobLogId}")',
        'java-joblog-binding')

# ---- API Java baseline ----
for rel in [
    'pro-business-api/src/main/java/com/ruoyi/base/controller/LargeScaleQueryController.java',
    'pro-business-api/src/main/java/com/ruoyi/base/controller/UnifiedQueryController.java',
]:
    restore(A, 'f6316c3', rel)

# ---- backend Python: restore whole files whose only parity change was error masking ----
for rel in [
    'car-monit-py/app/api/manager/bigscreen/big_screen_controller.py',
    'car-monit-py/app/api/monitor/sys_job_log_controller.py',
    'car-monit-py/app/common/core/page/table_data_info.py',
    'car-monit-py/app/config/exception_handlers.py',
    'car-monit-py/app/manager/service/bigscreen/big_screen_v3_services.py',
    'car-monit-py/app/manager/service/car_confim_free_service.py',
]:
    restore(B, '2efad537', rel)

# ---- backend Go ----
for rel in [
    'car-monit-go/internal/modules/generator/handler.go',
    'car-monit-go/internal/modules/manager/bigscreen.go',
    'car-monit-go/internal/modules/manager/car_free.go',
    'car-monit-go/internal/modules/manager/car_suspicious.go',
    'car-monit-go/internal/modules/ops/downtemplate.go',
    'car-monit-go/internal/web/errors.go',
]:
    restore(B, '2efad537', rel)

# ---- backend Rust ----
for rel in [
    'car-monit-rust/src/api/generator/gen.rs',
    'car-monit-rust/src/api/manager/bigscreen.rs',
    'car-monit-rust/src/api/manager/car_confim_free.rs',
    'car-monit-rust/src/api/manager/car_suspicious.rs',
    'car-monit-rust/src/api/quartz/job_log.rs',
]:
    restore(B, '904329f2', rel)
restore(B, '904329f2', 'car-monit-rust/src/api/flow/flow_message_info.rs')
replace(B, 'car-monit-rust/src/api/flow/flow_message_info.rs',
        'FLOW_APPLY_INFO app', 'flow_apply_info app', 'rust-flow-table-case', 2)

# ---- backend C++ ----
for rel in [
    'car-monit-cpp/src/cm/web/controller/base/GeometrySyncController.cpp',
    'car-monit-cpp/src/cm/web/controller/common/CommonController.cpp',
    'car-monit-cpp/src/cm/web/controller/common/DownTemplateController.cpp',
    'car-monit-cpp/src/cm/web/controller/flow/FlowExtraControllers.cpp',
    'car-monit-cpp/src/cm/web/controller/manager/ManagerExtraControllers.cpp',
    'car-monit-cpp/src/cm/web/controller/system/SysFileController.cpp',
    'car-monit-cpp/src/cm/web/controller/system/SysNoticeController.cpp',
    'car-monit-cpp/src/cm/web/controller/system/SysUpgradeInfoController.cpp',
    'car-monit-cpp/src/cm/web/controller/tool/GenController.cpp',
]:
    restore(B, '904329f2', rel)

# ---- API multi-language ----
for repo, commit, rels in [
    (A, '8893b55', [
        'car-monit-api-python/pro-business-api/src/main/java/com/ruoyi/base/controller/LargeScaleQueryController.py',
        'car-monit-api-python/pro-business-api/src/main/java/com/ruoyi/base/controller/UnifiedQueryController.py',
        'car-monit-api-cpp/src/handler/optimization_handlers.cpp',
        'car-monit-api-go/internal/handler/query.go',
        'car-monit-api-rust/src/handlers/query.rs',
    ]),
]:
    for rel in rels:
        restore(repo, commit, rel)
