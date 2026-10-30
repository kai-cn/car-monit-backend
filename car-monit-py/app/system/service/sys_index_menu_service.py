"""用户常用菜单服务层.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysIndexMenuService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysIndexMenuServiceImpl.java

三处"返回 AjaxResult"的方法
--------------------------
与其它模块不同，本模块有 **4** 个方法直接返回 ``AjaxResult`` 而不是 ``int``：

=============================  ==================================================
方法                           返回值
=============================  ==================================================
``saveSysIndexMenu``           ``success("操作成功！", id)`` —— **全角叹号**
``insertSysIndexMenu``         ``success()`` —— 不带 data
``deleteSysIndexMenuByIds``    ``success(count)``
``deleteSysIndexMenuById``     ``success(count)`` —— 即使 ``count == 0`` 也回 200
=============================  ==================================================

``count == 0`` 也是成功：这里用的是 ``AjaxResult.success``，**不是** ``toAjax``。
照抄 —— 改成 ``toAjax`` 会让"删一个不存在的 id"从 200 变 500。

``userId`` 一律来自登录上下文
---------------------------
``selectSysIndexMenuList`` / ``getList`` / ``saveSysIndexMenu`` / ``insertSysIndexMenu``
都在方法开头用 ``SecurityUtils.getUserId()`` **覆盖**实体里的 ``userId`` —— 客户端
传什么都会被无视。照抄（这是权限边界，不是冗余代码）。

``insertSysIndexMenu(String menuIds)`` 的四个细节
------------------------------------------------
1. 判据是 ``isNotBlank``（**trim 后为空**才算空），与 ``saveSysIndexMenu`` 的
   ``isNotEmpty(id)`` 是同一个 RuoYi 工具的两个重载；
2. 先剥**一个**尾逗号：``if (menuIds.endsWith(",")) substring(0, len-1)`` ——
   只剥一个。``"1,2,,"`` → ``"1,2,"`` → ``split`` 得 ``["1","2"]``；
3. ``split(",")`` 是 Java 的 ``String.split``，**丢弃尾部空串**；
4. 每个 id 都"先删后插"：``deleteByMenuUserId``（物理删）→ ``insertSysIndexMenu``。
   **没有** ``@Transactional``（见 COMPATIBILITY §28.3），中途失败会留下半成品。

``Long.parseLong(menuIdStr[i])``
--------------------------------
非数字 -> ``NumberFormatException`` -> HTTP 200 + ``code 500``。Python 用 ``int()``
抛 ``ValueError``，落到同一个通用处理器。

``DateUtils.getTimestamp()``
----------------------------
Java 每行都取同一个 ``curDate``（在循环**外**取得），所以同一批插入的时间戳完全
相同。Python 也是循环外取一次。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.date_utils import get_timestamp
from app.common.utils.string_utils import get_uuid, is_not_blank, is_not_empty, split_regex
from app.system.domain.sys_index_menu import SysIndexMenu
from app.system.mapper.sys_index_menu_mapper import SysIndexMenuMapper


class SysIndexMenuService:
    """Java: ``ISysIndexMenuService`` (impl: ``SysIndexMenuServiceImpl``)."""

    def __init__(self, index_menu_mapper: Optional[SysIndexMenuMapper] = None) -> None:
        self._index_menu_mapper = index_menu_mapper or SysIndexMenuMapper()

    @property
    def index_menu_mapper(self) -> SysIndexMenuMapper:
        return self._index_menu_mapper

    # Java: SysIndexMenu selectSysIndexMenuById(Long id)
    def select_sys_index_menu_by_id(self, id: Any) -> Optional[SysIndexMenu]:
        return self._index_menu_mapper.select_sys_index_menu_by_id(id)

    # Java: List<SysIndexMenu> selectSysIndexMenuList(SysIndexMenu sysIndexMenu)
    def select_sys_index_menu_list(self, entity: SysIndexMenu) -> List[SysIndexMenu]:
        """``userId`` 被登录上下文覆盖 —— 客户端传的值无效。"""
        entity.user_id = SecurityUtils.get_user_id()
        return self._index_menu_mapper.select_sys_index_menu_list(entity)

    # Java: List<SysIndexMenu> getList(SysIndexMenu sysIndexMenu)
    def get_list(self, entity: SysIndexMenu) -> List[SysIndexMenu]:
        """同上；返回的是"我常用的菜单"（SQL 自带 ``limit 9``）。"""
        entity.user_id = SecurityUtils.get_user_id()
        return self._index_menu_mapper.get_list(entity)

    # Java: AjaxResult saveSysIndexMenu(SysIndexMenu sysIndexMenu)
    def save_sys_index_menu(self, entity: SysIndexMenu) -> AjaxResult:
        """有 ``id`` 就改，没有就新增（新增时补 ``id`` / ``delFlag`` / 四个审计列）。"""
        user_id = SecurityUtils.get_user_id()
        cur_date = get_timestamp()
        # Java: StringUtils.isNotEmpty(sysIndexMenu.getId())
        if is_not_empty(entity.id):
            entity.update_by = user_id
            entity.update_time = cur_date
            self._index_menu_mapper.update_sys_index_menu(entity)
        else:
            entity.id = get_uuid()
            entity.del_flag = "0"
            entity.eps_id = SecurityUtils.get_eps_id()
            entity.create_by = user_id
            entity.create_time = cur_date
            entity.update_by = user_id
            entity.update_time = cur_date
            self._index_menu_mapper.insert_sys_index_menu(entity)
        # Java: AjaxResult.success("操作成功！", sysIndexMenu.getId()) —— 全角叹号
        return AjaxResult.success_message_data("操作成功！", entity.id)

    # Java: AjaxResult insertSysIndexMenu(String menuIds)
    def insert_sys_index_menu(self, menu_ids: Optional[str]) -> AjaxResult:
        """把逗号串拆成一个个 ``menuId``，"先删后插"，每行一条记录。"""
        user_id = SecurityUtils.get_user_id()
        cur_date = get_timestamp()
        # Java: StringUtils.isNotBlank(menuIds)
        if is_not_blank(menu_ids):
            # Java: if (menuIds.endsWith(",")) menuIds = menuIds.substring(0, length - 1)
            if menu_ids.endswith(","):
                menu_ids = menu_ids[: len(menu_ids) - 1]
            # Java: String.split(",") —— 丢弃尾部空串
            for part in split_regex(menu_ids, ",", 0):
                entity = SysIndexMenu()
                entity.user_id = user_id
                entity.menu_id = int(part)
                # 先删（物理）
                self._index_menu_mapper.delete_by_menu_user_id(entity)
                entity.del_flag = "0"
                entity.eps_id = SecurityUtils.get_eps_id()
                entity.create_by = user_id
                entity.create_time = cur_date
                entity.update_by = user_id
                entity.update_time = cur_date
                self._index_menu_mapper.insert_sys_index_menu(entity)
        return AjaxResult.success()

    # Java: AjaxResult deleteSysIndexMenuByIds(Long[] ids)
    def delete_sys_index_menu_by_ids(self, ids: Sequence[Any]) -> AjaxResult:
        """软删除（``del_flag = '1'``）；``count == 0`` 也算成功。"""
        count = self._index_menu_mapper.delete_sys_index_menu_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteSysIndexMenuById(Long id)
    def delete_sys_index_menu_by_id(self, id: Any) -> AjaxResult:
        """软删除；``count == 0`` 也算成功。"""
        count = self._index_menu_mapper.delete_sys_index_menu_by_id(id)
        return AjaxResult.success_data(count)


_SERVICE: Optional[SysIndexMenuService] = None


def get_index_menu_service() -> SysIndexMenuService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysIndexMenuService()
    return _SERVICE


def reset_index_menu_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysIndexMenuService",
    "get_index_menu_service",
    "reset_index_menu_service",
]