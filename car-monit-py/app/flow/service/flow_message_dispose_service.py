"""系统消息处理人 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowMessageDisposeServiceImpl.java

这个 Service 里有三组"按 ``mid`` 批量动待办"的方法，语义各不相同，**不要合并**：

============================  =========================================================
方法                           语义
============================  =========================================================
``removeFlowMessage``         **物理删**（``delete from``），可带 ``bussId`` 只删自己那条
``saveSzzdFlowMessage``       只把自己那条置为已办理（``MSG_STATUS='1'``），不换处理人
``saveSzzdFlowMessageAll``    把所有"未办理"的处理人都改成 ``bussId`` 并置为已办理
============================  =========================================================

``mid`` 为空时写死 ``-1``
-------------------------
``removeFlowMessage`` / ``saveSzzdFlowMessage`` / ``saveSzzdFlowMessageAll`` 开头都是

    if (StringUtils.isEmpty(mid)) { mid = "-1"; }

即"空 mid"变成一条**查不到的**主键，从而影响 0 行 —— 靠 WHERE 不命中来挡参数校验，
而不是提前 return。照抄：直接拼进 SQL，返回 ``success(0)``。

``saveSzzdFlowMessageAll`` 还会补 ``bussId="-1"``
--------------------------------------------------
``bussId`` 为空时它**不是**跳过条件，而是把新处理人写成 ``-1``（见 XML：
``set BUSS_ID = #{bussId}``）。这个差异只在"撤销 / 委托"里踩到，照抄。

``saveFlowList(mid, userIds)`` 是"先删后插"
-------------------------------------------
对每个处理人：先 ``removeFlowMessage(mid, userId)`` 物理删掉旧行，再
``saveFlowMessageDispose`` 插一条 ``msgStatus="2"``（未办理）。所以重复调用是幂等的
（不会堆积重复待办），代价是行 id 每次都变。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import get_eps_id, get_user_id
from app.common.utils.string_utils import get_uuid, is_empty, is_not_empty
from app.flow.domain.flow_message_dispose import FlowMessageDispose
from app.flow.mapper.flow_message_dispose_mapper import (
    FlowMessageDisposeMapper,
    get_mapper,
)

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"

#: 空 ``mid`` 的替身（Java 里就地改成这个值，见模块文档）。
EMPTY_MID = "-1"

#: 空 ``bussId`` 在 ``saveSzzdFlowMessageAll`` 里的替身。
EMPTY_BUSS_ID = "-1"

#: 新待办的处理状态：2 = 未办理。
MSG_STATUS_UNDONE = "2"


class FlowMessageDisposeService:
    """Java: ``class FlowMessageDisposeServiceImpl implements IFlowMessageDisposeService``."""

    def __init__(self, mapper: Optional[FlowMessageDisposeMapper] = None) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()

    # ---------------------------------------------------------------- 查询

    # Java: FlowMessageDispose selectFlowMessageDisposeById(String id)
    def select_flow_message_dispose_by_id(
        self, entity_id: str
    ) -> Optional[FlowMessageDispose]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowMessageDispose> selectFlowMessageDisposeList(FlowMessageDispose x)
    def select_flow_message_dispose_list(
        self, query: FlowMessageDispose
    ) -> List[FlowMessageDispose]:
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveFlowMessageDispose(FlowMessageDispose flowMessageDispose)
    def save_flow_message_dispose(
        self, flow_message_dispose: FlowMessageDispose
    ) -> AjaxResult:
        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_message_dispose.id):
            # 修改
            flow_message_dispose.update_by = user_id  # 更新人
            flow_message_dispose.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_message_dispose)
        else:
            # 新增
            flow_message_dispose.id = get_uuid()  # 主键
            flow_message_dispose.del_flag = "0"
            flow_message_dispose.eps_id = get_eps_id()  # 当前人所在的部门
            flow_message_dispose.create_by = user_id  # 创建人
            flow_message_dispose.create_time = cur_date  # 创建时间
            flow_message_dispose.update_by = user_id  # 更新人
            flow_message_dispose.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_message_dispose)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_message_dispose.id)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteFlowMessageDisposeByIds(String[] ids)
    def delete_flow_message_dispose_by_ids(self, ids: Any) -> AjaxResult:
        count = self._mapper.delete_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteFlowMessageDisposeById(String id)
    def delete_flow_message_dispose_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # Java: AjaxResult removeFlowMessage(String mid, String bussId)
    def remove_flow_message(self, mid: str, buss_id: Optional[str]) -> AjaxResult:
        """**物理删**掉一条（或某人的）待办；``mid`` 为空时退化为 ``-1``。"""
        real_mid = EMPTY_MID if is_empty(mid) else mid
        # Java 只在 bussId 非空时才把它加进条件
        real_buss_id = buss_id if is_not_empty(buss_id) else None
        count = self._mapper.remove_flow_message(real_mid, real_buss_id)
        return AjaxResult.success_data(count)

    # Java: AjaxResult saveSzzdFlowMessage(String mid, String bussId)
    def save_szzd_flow_message(self, mid: str, buss_id: Optional[str]) -> AjaxResult:
        """把自己那条待办置为已办理（不换处理人）。"""
        real_mid = EMPTY_MID if is_empty(mid) else mid
        real_buss_id = buss_id if is_not_empty(buss_id) else None
        count = self._mapper.save_szzd_flow_message(real_mid, real_buss_id)
        return AjaxResult.success_data(count)

    # Java: AjaxResult saveSzzdFlowMessageAll(String mid, String bussId)
    def save_szzd_flow_message_all(self, mid: str, buss_id: Optional[str]) -> AjaxResult:
        """把这条消息里所有"未办理"的处理人改成 ``bussId`` 并置为已办理。"""
        real_mid = EMPTY_MID if is_empty(mid) else mid
        real_buss_id = buss_id if is_not_empty(buss_id) else EMPTY_BUSS_ID
        count = self._mapper.save_szzd_flow_message_all(real_mid, real_buss_id)
        return AjaxResult.success_data(count)

    # Java: void saveFlowList(String mid, String[] userIds)
    def save_flow_list(self, mid: str, user_ids: Sequence[str]) -> None:
        """给这批处理人各插一条未办理待办（先按 ``mid + 处理人`` 物理删旧行）。"""
        for user_id in user_ids:
            dispose_bo = FlowMessageDispose()
            dispose_bo.mid = mid  # 外键
            dispose_bo.msg_status = MSG_STATUS_UNDONE  # 未处理
            dispose_bo.buss_id = user_id  # 处理人usr
            # 先删除
            self.remove_flow_message(mid, user_id)
            # 在新增
            self.save_flow_message_dispose(dispose_bo)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowMessageDisposeService] = None


def get_service() -> FlowMessageDisposeService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowMessageDisposeService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = [
    "EMPTY_BUSS_ID",
    "EMPTY_MID",
    "FlowMessageDisposeService",
    "MSG_STATUS_UNDONE",
    "SAVE_SUCCESS_MESSAGE",
    "get_service",
    "reset_service",
]
