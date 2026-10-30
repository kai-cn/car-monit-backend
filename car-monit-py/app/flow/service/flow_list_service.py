"""审核历史记录 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowListServiceImpl.java

与我的申请同模板，额外一条 :meth:`select_flow_list_list_new`（降序版本的列表）。

``saveFlowList`` 是**流转历史**的唯一写入口：``FlowCurrentNodeServiceImpl`` 每次
提交 / 审核 / 退回 / 委托都调它一次，``shKey`` 存机器码（S/T/F/R/entrust），
``shValue`` 存中文（提交/同意/拒绝/退回/委托）。

``selectFlowListListNew`` 的排序是降序，而 ``selectFlowListList`` 是升序 ——
两条 XML 语句的 ``<if>`` 完全一致，只有 ``order by`` 相反，所以 Mapper 侧共用
一套条件拼装、只换排序串。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import get_eps_id, get_user_id
from app.common.utils.string_utils import get_uuid, is_not_empty
from app.flow.domain.flow_list import FlowList
from app.flow.mapper.flow_list_mapper import FlowListMapper, get_mapper

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"


class FlowListService:
    """Java: ``class FlowListServiceImpl implements IFlowListService``."""

    def __init__(self, mapper: Optional[FlowListMapper] = None) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()

    # ---------------------------------------------------------------- 查询

    # Java: FlowList selectFlowListById(String id)
    def select_flow_list_by_id(self, entity_id: str) -> Optional[FlowList]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowList> selectFlowListList(FlowList flowList)
    def select_flow_list_list(self, query: FlowList) -> List[FlowList]:
        return self._mapper.select_list(query)

    # Java: List<FlowList> selectFlowListListNew(FlowList flowList)
    def select_flow_list_list_new(self, query: FlowList) -> List[FlowList]:
        return self._mapper.select_list_new(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveFlowList(FlowList flowList)
    def save_flow_list(self, flow_list: FlowList) -> AjaxResult:
        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_list.id):
            # 修改
            flow_list.update_by = user_id  # 更新人
            flow_list.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_list)
        else:
            # 新增
            flow_list.id = get_uuid()  # 主键
            flow_list.del_flag = "0"
            flow_list.eps_id = get_eps_id()  # 当前人所在的部门
            flow_list.create_by = user_id  # 创建人
            flow_list.create_time = cur_date  # 创建时间
            flow_list.update_by = user_id  # 更新人
            flow_list.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_list)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_list.id)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteFlowListByIds(String[] ids)
    def delete_flow_list_by_ids(self, ids: Any) -> AjaxResult:
        count = self._mapper.delete_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteFlowListById(String id)
    def delete_flow_list_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowListService] = None


def get_service() -> FlowListService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowListService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = ["FlowListService", "SAVE_SUCCESS_MESSAGE", "get_service", "reset_service"]
