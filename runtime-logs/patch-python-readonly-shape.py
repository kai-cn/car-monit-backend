#!/usr/bin/env python3
"""
@description 修复 backend Python 只读端点与 Java 基准的结构差异，保留真实业务错误语义。
@author Tencent Hunyuan Hy
@date 2026-11-24 23:10:00
@usage python3 runtime-logs/patch-python-readonly-shape.py
@dependencies backend master Python 源码。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-py')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换源码片段；未命中时输出诊断。"""
    t = path.read_text(encoding='utf-8')
    if old not in t:
        print('NOT_FOUND', label, path)
        return
    path.write_text(t.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


# 用户资料：Java fastjson2 缓存反序列化后 user/dept/roles 的 params 带 @type 标记。
replace(B / 'app/api/system/sys_profile_controller.py',
        '''    login_user = _current_login_user(request)
    user = login_user.user
    ajax = AjaxResult.success_data(user)''',
        '''    login_user = _current_login_user(request)
    user = login_user.user
    user_payload = user.to_json_dict() if hasattr(user, "to_json_dict") else dict(user)
    user_payload["params"] = {"@type": "java.util.HashMap"}
    if isinstance(user_payload.get("dept"), dict):
        user_payload["dept"]["params"] = {"@type": "java.util.HashMap"}
    for role in user_payload.get("roles") or []:
        if isinstance(role, dict):
            role.setdefault("params", {"@type": "java.util.HashMap"})
    ajax = AjaxResult.success_data(user_payload)''',
        'profile-params')
replace(B / 'app/api/system/sys_login_controller.py',
        '''    # Java SysRole also serializes inherited params as {"@type":"java.util.HashMap"}.''',
        '''    if isinstance(user_payload.get("dept"), dict):
        user_payload["dept"]["params"] = {"@type": "java.util.HashMap"}
    # Java SysRole also serializes inherited params as {"@type":"java.util.HashMap"}.''',
        'getinfo-dept-params')

# ODS 行公共派生字段：Java 实体即使字段为 null 也会序列化。
replace(B / 'app/base/service/forest/forest_client.py',
        '''            for field in ("cid", "enaxlecount", "entryoperatorid", "enweight", "obuid", "obusign"):
                row.setdefault(field, None)''',
        '''            for field in (
                "cid", "enaxlecount", "entryoperatorid", "enweight", "obuid", "obusign",
                "plateColorMark", "plateColorName", "directionStr", "chargeStatus", "entimeStr",
            ):
                row.setdefault(field, None)''',
        'ods-derived-fields')

# Java 真实业务错误：日期格式解析失败必须保留为 500。
replace(B / 'app/api/base/ods_lwzxsfsj_fee_gantry_fusion01_controller.py',
        '''@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取交易流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(_client().select_ods_lwzxsfsj_fee_gantry_fusion01_by_id(big_id))''',
        '''@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取交易流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    row = _client().select_ods_lwzxsfsj_fee_gantry_fusion01_by_id(big_id)
    entime = row.get("entime") if isinstance(row, Mapping) else None
    if isinstance(entime, str) and len(entime) > 10:
        # Java 的 LocalDate 反序列化对带时分秒的值抛 ForestConvertException。
        return AjaxResult.error_message(
            "ForestConvertException: Text '" + entime + "' could not be parsed, unparsed text found at index 10"
        )
    return AjaxResult.success_data(row)''',
        'fee-gantry-date-error')

# 详情数据即使为空也必须保留 data 键，形状与 Java AjaxResult.success(entity) 一致。
replace(B / 'app/api/base/ods_cxzt_fwqclls_controller.py',
        '''    return AjaxResult.success_data(_service().select_by_id(bigId))''',
        '''    row = _service().select_by_id(bigId)
    if row is None:
        from app.base.domain.ods_cxzt_fwqclls import OdsCxztFwqclls
        row = OdsCxztFwqclls(big_id=bigId)
    return AjaxResult.success_data(row)''',
        'fwqclls-data')

# Java 基准的 monitor/jobLog/{id} 是成功详情，不是路径变量错误。
replace(B / 'app/api/monitor/sys_job_log_controller.py',
        '''    raise ServiceException(MISSING_PATH_VARIABLE_MESSAGE)''',
        '''    row = _job_log_service().select_job_log_by_id(config_id)
    return AjaxResult.success_data(row)''',
        'joblog-detail')
