"""系统升级信息 服务层.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUpgradeInfoService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUpgradeInfoServiceImpl.java

三个方法直接返回 ``AjaxResult``
------------------------------
===================================  ============================================
方法                                 返回值
===================================  ============================================
``saveSysUpgradeInfo``               ``success("操作成功！", id)`` —— **全角叹号**
``deleteSysUpgradeInfoByIds``        ``success(count)``
``deleteSysUpgradeInfoById``         ``success(count)`` —— 无控制器调用，照留
===================================  ============================================

``count == 0`` 也是成功：这里用的是 ``AjaxResult.success``，**不是** ``toAjax``
（与 ``SysIndexMenuServiceImpl`` 一致，与其它模块相反）。

``saveSysUpgradeInfo`` 与 ``SysIndexMenu`` 的两处差异
-----------------------------------------------------
同样是 ``extends BaseUuidEntity``、同样是"有 id 就改、没 id 就新增"，但：

1. 新增时**多盖一个** ``tenantId = SecurityUtils.getTenantId()``（``SysIndexMenu``
   不盖租户，只盖 ``epsId``）；
2. 改的时候只动 ``updateBy`` / ``updateTime``，**不**回填 ``createTime``。

``saveSysUpgradeInfo`` 的判据
----------------------------
``StringUtils.isNotEmpty(id)`` —— ``""`` / ``"   "`` 都算"没有 id"，走**新增**分支
并生成一个新 UUID（RuoYi 的 ``isNotEmpty`` 会 trim）。

``deleteSysUpgradeInfoById`` 是**孤儿方法**
-----------------------------------------
接口里声明了、实现里也有，但控制器只调 ``deleteSysUpgradeInfoByIds``。
按迁移原则第 4 条照留并标注，不删。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.date_utils import get_timestamp
from app.common.utils.string_utils import get_uuid, is_not_empty
from app.system.domain.sys_upgrade_info import SysUpgradeInfo
from app.system.mapper.sys_upgrade_info_mapper import SysUpgradeInfoMapper


class SysUpgradeInfoService:
    """Java: ``ISysUpgradeInfoService`` (impl: ``SysUpgradeInfoServiceImpl``)."""

    def __init__(self, upgrade_info_mapper: Optional[SysUpgradeInfoMapper] = None) -> None:
        self._upgrade_info_mapper = upgrade_info_mapper or SysUpgradeInfoMapper()

    @property
    def upgrade_info_mapper(self) -> SysUpgradeInfoMapper:
        return self._upgrade_info_mapper

    # Java: SysUpgradeInfo selectSysUpgradeInfoById(String id)
    def select_sys_upgrade_info_by_id(self, id: Any) -> Optional[SysUpgradeInfo]:
        return self._upgrade_info_mapper.select_sys_upgrade_info_by_id(id)

    # Java: List<SysUpgradeInfo> selectSysUpgradeInfoList(SysUpgradeInfo sysUpgradeInfo)
    def select_sys_upgrade_info_list(self, entity: SysUpgradeInfo) -> List[SysUpgradeInfo]:
        """纯转发；``tenantId`` 由**控制器**盖章（本模块与 indexmenu 的又一处不同）。"""
        return self._upgrade_info_mapper.select_sys_upgrade_info_list(entity)

    # Java: SysUpgradeInfo selectSysUpgradeInfoNewest(SysUpgradeInfo sysUpgradeInfo)
    def select_sys_upgrade_info_newest(self, entity: SysUpgradeInfo) -> Optional[SysUpgradeInfo]:
        """取最新一条更新日志（``back_col1 = 1``）；查不到返回 ``None``。"""
        return self._upgrade_info_mapper.select_sys_upgrade_info_newest(entity)

    # Java: AjaxResult saveSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo)
    def save_sys_upgrade_info(self, entity: SysUpgradeInfo) -> AjaxResult:
        """有 ``id`` 就改，没有就新增（新增时补 ``id`` / ``delFlag`` / ``epsId`` /
        ``tenantId`` / 四个审计列）。"""
        user_id = SecurityUtils.get_user_id()
        cur_date = get_timestamp()
        # Java: StringUtils.isNotEmpty(sysUpgradeInfo.getId())
        if is_not_empty(entity.id):
            entity.update_by = user_id
            entity.update_time = cur_date
            self._upgrade_info_mapper.update_sys_upgrade_info(entity)
        else:
            entity.id = get_uuid()
            entity.del_flag = "0"
            entity.eps_id = SecurityUtils.get_eps_id()
            # Java: sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId())
            entity.tenant_id = SecurityUtils.get_tenant_id()
            entity.create_by = user_id
            entity.create_time = cur_date
            entity.update_by = user_id
            entity.update_time = cur_date
            self._upgrade_info_mapper.insert_sys_upgrade_info(entity)
        # Java: AjaxResult.success("操作成功！", sysUpgradeInfo.getId()) —— 全角叹号
        return AjaxResult.success_message_data("操作成功！", entity.id)

    # Java: AjaxResult deleteSysUpgradeInfoByIds(String[] ids)
    def delete_sys_upgrade_info_by_ids(self, ids: Sequence[Any]) -> AjaxResult:
        """软删除（``del_flag = '1'``）；``count == 0`` 也算成功。"""
        count = self._upgrade_info_mapper.delete_sys_upgrade_info_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteSysUpgradeInfoById(String id) —— **无控制器调用**
    def delete_sys_upgrade_info_by_id(self, id: Any) -> AjaxResult:
        """软删除；``count == 0`` 也算成功。孤儿方法，照留。"""
        count = self._upgrade_info_mapper.delete_sys_upgrade_info_by_id(id)
        return AjaxResult.success_data(count)


_SERVICE: Optional[SysUpgradeInfoService] = None


def get_upgrade_info_service() -> SysUpgradeInfoService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysUpgradeInfoService()
    return _SERVICE


def reset_upgrade_info_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysUpgradeInfoService",
    "get_upgrade_info_service",
    "reset_upgrade_info_service",
]
