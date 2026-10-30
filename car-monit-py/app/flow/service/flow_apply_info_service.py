"""我的申请 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowApplyInfoServiceImpl.java

模板与 ``manager`` 包一致（``isNotEmpty(id)`` 分流 + 四个审计字段自己赋值），
唯一的额外方法 :meth:`save_flow_apply_info_new` 是"按业务单据 upsert"：

    # 根据业务查询是否有记录
    querybo.setBillOid(flowApplyInfo.getBillOid());
    List<FlowApplyInfo> queryList = this.selectFlowApplyInfoList(querybo);
    if (queryList.size() > 0) { flowApplyInfo.setId(queryList.get(0).getId()); }

它把 ``FlowCurrentNodeServiceImpl`` 里的四五个调用点都收敛成一句，并**返回主键**
（而不是 ``AjaxResult``），所以调用方拿到的 ``flowApplyOid`` 直接进
``flow_current_node`` / 业务表的 ``flow_apply_oid`` 列。

两处照抄的细节
--------------
1. ``selectByBillId`` 在 Java 里是 ``selectOne``：多于一行会抛
   ``TooManyResultsException``。Python 侧取首行（见 Mapper 的说明）。
2. ``deleteFlowApplyInfoById`` / ``ByIds`` 只返回影响行数，**不**级联删消息 /
   当前节点 —— 撤销流程时的级联是 ``FlowCurrentNodeServiceImpl#submitReturn``
   自己按顺序做的。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import get_eps_id, get_user_id
from app.common.utils.string_utils import get_uuid, is_not_empty
from app.flow.domain.flow_apply_info import FlowApplyInfo
from app.flow.mapper.flow_apply_info_mapper import FlowApplyInfoMapper, get_mapper

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"


class FlowApplyInfoService:
    """Java: ``class FlowApplyInfoServiceImpl implements IFlowApplyInfoService``."""

    def __init__(self, mapper: Optional[FlowApplyInfoMapper] = None) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()

    # ---------------------------------------------------------------- 查询

    # Java: FlowApplyInfo selectFlowApplyInfoById(String id)
    def select_flow_apply_info_by_id(self, entity_id: str) -> Optional[FlowApplyInfo]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowApplyInfo> selectFlowApplyInfoList(FlowApplyInfo flowApplyInfo)
    def select_flow_apply_info_list(self, query: FlowApplyInfo) -> List[FlowApplyInfo]:
        return self._mapper.select_list(query)

    # Java: FlowApplyInfo selectByBillId(String billId)
    def select_by_bill_id(self, bill_id: str) -> Optional[FlowApplyInfo]:
        return self._mapper.select_by_bill_id(bill_id)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveFlowApplyInfo(FlowApplyInfo flowApplyInfo)
    def save_flow_apply_info(self, flow_apply_info: FlowApplyInfo) -> AjaxResult:
        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_apply_info.id):
            # 修改
            flow_apply_info.update_by = user_id  # 更新人
            flow_apply_info.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_apply_info)
        else:
            # 新增
            flow_apply_info.id = get_uuid()  # 主键
            flow_apply_info.del_flag = "0"
            flow_apply_info.eps_id = get_eps_id()  # 当前人所在的部门
            flow_apply_info.create_by = user_id  # 创建人
            flow_apply_info.create_time = cur_date  # 创建时间
            flow_apply_info.update_by = user_id  # 更新人
            flow_apply_info.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_apply_info)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_apply_info.id)

    # Java: String saveFlowApplyInfoNew(FlowApplyInfo flowApplyInfo)
    def save_flow_apply_info_new(self, flow_apply_info: FlowApplyInfo) -> str:
        """按 ``billOid`` upsert，返回主键（Java 返回 ``String``，不是 ``AjaxResult``）。"""
        user_id = get_user_id()
        cur_date = get_now_date()

        # 根据业务查询是否有记录
        query_bo = FlowApplyInfo()
        query_bo.bill_oid = flow_apply_info.bill_oid
        query_list = self.select_flow_apply_info_list(query_bo)
        if len(query_list) > 0:
            flow_apply_info.id = query_list[0].id

        if is_not_empty(flow_apply_info.id):
            # 修改
            flow_apply_info.update_by = user_id
            flow_apply_info.update_time = cur_date
            self._mapper.update_by_id(flow_apply_info)
        else:
            # 新增
            flow_apply_info.id = get_uuid()
            flow_apply_info.del_flag = "0"
            flow_apply_info.eps_id = get_eps_id()
            flow_apply_info.create_by = user_id
            flow_apply_info.create_time = cur_date
            flow_apply_info.update_by = user_id
            flow_apply_info.update_time = cur_date
            self._mapper.insert(flow_apply_info)
        return flow_apply_info.id

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteFlowApplyInfoByIds(String[] ids)
    def delete_flow_apply_info_by_ids(self, ids: Any) -> AjaxResult:
        count = self._mapper.delete_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteFlowApplyInfoById(String id)
    def delete_flow_apply_info_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowApplyInfoService] = None


def get_service() -> FlowApplyInfoService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowApplyInfoService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = ["FlowApplyInfoService", "SAVE_SUCCESS_MESSAGE", "get_service", "reset_service"]
