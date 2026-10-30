"""流程节点 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowTemplateServiceImpl.java

四个入口，共用一段"新增/修改"模板（``saveFlowTemplate`` 多两道查重）：

    if (flowTemplateMapper.isExitsKey(flowTemplate) > 0)   return error("节点key存在重复");
    if (flowTemplateMapper.isExitsSort(flowTemplate) > 0)  return error("节点顺序存在重复");
    ... upsert ...
    saveFlow(flowTemplate.getFlowOid());   // 设置节点上下顺序

``saveFlowTemplateNew`` 是"同步其他单位工作流"用的**免查重**版本，且新增时把
``create_by`` 写死 ``-2L``（``saveFlowTemplate`` 写的是当前用户，``FlowName`` 那边
写 ``-1L``）。三个魔数各有出处，照抄。

``saveFlow(flowOid)`` 是链路重算器
---------------------------------
按 ``order by t.NODE_ORDER ,t.id`` 取全部节点，逐条回写三个指针：

* 首个节点：``previous_node_oid = "0"``、``return_node_oid = "0"``；
* 末个节点：``next_node_oid = "-1"``；
* 其它节点：``previous_node_oid`` = 上一条的 id；``return_node_oid`` = 以
  ``return_num`` 当 ``node_order`` 查出来的节点，查不到就是**首个节点**。

注意循环里复用的 ``queryBo`` 会**保留**上一次的 ``node_order``（Java 直接
``setNodeOrder`` 覆盖同一个对象），Python 侧共用同一个查询对象，行为一致。

删除后的把戏
------------
    int count = flowTemplateMapper.deleteFlowTemplateByIds(ids);
    saveFlow(this.selectFlowTemplateById(ids[0]).getFlowOid());

先删、后查。详情语句不带 ``del_flag`` 条件，所以已逻辑删的行仍能查出来，
``getFlowOid()`` 不会 NPE —— 这是**依赖**删除语句是逻辑删才成立的写法，照抄。
若 ``ids[0]`` 是一条从未存在的 id，Java 会 NPE，这里同样会抛 ``AttributeError``。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import get_eps_id, get_user_id
from app.common.utils.string_utils import get_uuid, is_not_empty
from app.flow.domain.flow_template import FlowTemplate
from app.flow.mapper.flow_template_mapper import FlowTemplateMapper, get_mapper

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"

#: 节点 key 重复的提示（Java 原文，注意"key"是小写）。
DUPLICATE_KEY_MESSAGE = "节点key存在重复"

#: 节点顺序重复的提示。
DUPLICATE_SORT_MESSAGE = "节点顺序存在重复"

#: 首个节点的 ``previousNodeOid`` / ``returnNodeOid`` 哨兵。
FIRST_NODE_SENTINEL = "0"

#: 末个节点的 ``nextNodeOid`` 哨兵。
LAST_NODE_SENTINEL = "-1"

#: ``saveFlowTemplateNew`` 新增时的 ``createBy``（同步标记）。
SYNC_CREATE_BY = -2


class FlowTemplateService:
    """Java: ``class FlowTemplateServiceImpl implements IFlowTemplateService``."""

    def __init__(self, mapper: Optional[FlowTemplateMapper] = None) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()

    # ---------------------------------------------------------------- 查询

    # Java: FlowTemplate selectFlowTemplateById(String id)
    def select_flow_template_by_id(self, entity_id: str) -> Optional[FlowTemplate]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowTemplate> selectFlowTemplateList(FlowTemplate flowTemplate)
    def select_flow_template_list(self, query: FlowTemplate) -> List[FlowTemplate]:
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveFlowTemplate(FlowTemplate flowTemplate)
    def save_flow_template(self, flow_template: FlowTemplate) -> AjaxResult:
        # 节点顺序 和 key 不能重复
        if self._mapper.is_exits_key(flow_template) > 0:
            return AjaxResult.error_message(DUPLICATE_KEY_MESSAGE)

        if self._mapper.is_exits_sort(flow_template) > 0:
            return AjaxResult.error_message(DUPLICATE_SORT_MESSAGE)

        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_template.id):
            # 修改
            flow_template.update_by = user_id  # 更新人
            flow_template.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_template)
        else:
            # 新增
            flow_template.id = get_uuid()  # 主键
            flow_template.del_flag = "0"
            flow_template.eps_id = get_eps_id()  # 当前人所在的部门
            flow_template.create_by = user_id  # 创建人
            flow_template.create_time = cur_date  # 创建时间
            flow_template.update_by = user_id  # 更新人
            flow_template.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_template)
        self.save_flow(flow_template.flow_oid)  # 设置节点上下顺序

        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_template.id)

    # Java: AjaxResult saveFlowTemplateNew(FlowTemplate flowTemplate)
    def save_flow_template_new(self, flow_template: FlowTemplate) -> AjaxResult:
        """免查重的 upsert（``create_by`` 固定 ``-2``），供"同步其他单位"使用。"""
        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_template.id):
            # 修改
            flow_template.update_by = user_id  # 更新人
            flow_template.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_template)
        else:
            # 新增
            flow_template.id = get_uuid()  # 主键
            flow_template.del_flag = "0"
            flow_template.eps_id = get_eps_id()  # 当前人所在的部门
            flow_template.create_by = SYNC_CREATE_BY  # 创建人
            flow_template.create_time = cur_date  # 创建时间
            flow_template.update_by = user_id  # 更新人
            flow_template.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_template)

        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_template.id)

    # Java: void saveFlow(String flowOid)
    def save_flow(self, flow_oid: str) -> None:
        """按 ``NODE_ORDER`` 重算每个节点的上一节点 / 下一节点 / 退回节点。"""
        if is_not_empty(flow_oid):
            query_bo = FlowTemplate()
            query_bo.flow_oid = flow_oid
            result_list = self.select_flow_template_list(query_bo)

            first_id = "-1"  # 第一个节点
            for index, node in enumerate(result_list):
                pre_node = ""  # 上一个节点
                next_node = ""  # 下一个节点
                return_node = ""  # 退回节点
                if index == 0:
                    pre_node = FIRST_NODE_SENTINEL
                    return_node = FIRST_NODE_SENTINEL

                    first_id = node.id  # 第一个节点
                else:
                    pre_node = result_list[index - 1].id

                    # 根据退回 num 查询（注意 query_bo 会被后续轮次沿用）
                    query_bo.node_order = node.return_num
                    return_list = self.select_flow_template_list(query_bo)
                    if len(return_list) > 0:
                        return_node = return_list[0].id
                    else:
                        return_node = first_id

                if index == len(result_list) - 1:
                    next_node = LAST_NODE_SENTINEL
                else:
                    next_node = result_list[index + 1].id
                node.previous_node_oid = pre_node
                node.next_node_oid = next_node
                node.return_node_oid = return_node
                self._mapper.update_by_id(node)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteFlowTemplateByIds(String[] ids)
    def delete_flow_template_by_ids(self, ids: Any) -> AjaxResult:
        count = self._mapper.delete_by_ids(ids)
        # 先删后查（见模块文档：依赖"逻辑删"才成立）
        self.save_flow(self.select_flow_template_by_id(ids[0]).flow_oid)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteFlowTemplateById(String id)
    def delete_flow_template_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        self.save_flow(self.select_flow_template_by_id(entity_id).flow_oid)
        return AjaxResult.success_data(count)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowTemplateService] = None


def get_service() -> FlowTemplateService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowTemplateService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = [
    "DUPLICATE_KEY_MESSAGE",
    "DUPLICATE_SORT_MESSAGE",
    "FIRST_NODE_SENTINEL",
    "FlowTemplateService",
    "LAST_NODE_SENTINEL",
    "SAVE_SUCCESS_MESSAGE",
    "SYNC_CREATE_BY",
    "get_service",
    "reset_service",
]
