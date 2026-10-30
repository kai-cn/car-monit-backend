"""Flow constants.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/util/FlowConstant.java

Java 里是一堆 ``public static final String``；Python 侧原样落成模块级常量。
命名**保留** Java 的下划线小写风格（``dev_apply_key`` 而不是 ``DEV_APPLY_KEY``），
这样 grep 时两边一一对上。
"""

from __future__ import annotations

#: 设备申领
# Java: public static final String dev_apply_key
DEV_APPLY_KEY = "dev_apply_key"

#: 技术服务人员申请
# Java: public static final String expert_apply_key
EXPERT_APPLY_KEY = "expert_apply_key"

#: 资源申请
# Java: public static final String res_info_key
RES_INFO_KEY = "res_info_key"

#: 自定义流程
# Java: public static final String zdy_flow
ZDY_FLOW = "zdyFlow"

#: 专家申请指派
# Java: public static final String zdyflow_expert_zp
ZDYFLOW_EXPERT_ZP = "zdyflow_expert_zp"

#: 专家申请计费
# Java: public static final String zdyflow_expert_charge
ZDYFLOW_EXPERT_CHARGE = "zdyflow_expert_charge"

#: 设备申请计费
# Java: public static final String zdyflow_dev_charge
ZDYFLOW_DEV_CHARGE = "zdyflow_dev_charge"

#: 资源申请（计费）
# Java: public static final String zdyflow_res_charge
ZDYFLOW_RES_CHARGE = "zdyflow_res_charge"


__all__ = [
    "DEV_APPLY_KEY",
    "EXPERT_APPLY_KEY",
    "RES_INFO_KEY",
    "ZDY_FLOW",
    "ZDYFLOW_EXPERT_ZP",
    "ZDYFLOW_EXPERT_CHARGE",
    "ZDYFLOW_DEV_CHARGE",
    "ZDYFLOW_RES_CHARGE",
]
