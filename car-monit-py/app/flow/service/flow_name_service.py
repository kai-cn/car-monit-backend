"""流程名称 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowNameServiceImpl.java

``saveFlowName`` 与其它模板的两处不同：

1. 先查重：``isExitsKey(flowName) > 0`` 直接 ``error("节点key存在重复")``
   （查重 SQL 固定 ``create_by = -1``，即只查**系统预置**流程）；
2. 新增时 ``createBy`` 写死 ``-1L`` 而不是当前用户 —— 这是"系统预置"标记，后两条
   同步逻辑都靠它识别源流程。

``tbFlow`` 是"把系统预置流程同步到所有单位"
--------------------------------------------
    queryBO.setCreateBy(-1L) -> 源流程（系统预置）
    queryBo.setIsUint("1")   -> 目标部门（``is_uint = '1'``）
    对每个 (源流程 × 目标部门)：
        若该部门下没有同 key 的流程：
            复制 flow_name（tenantId=部门 id、flowBusinessType="1"）
            把源流程的每个节点复制一份（id 清空、flowOid 指向新流程、
            next/previous 清空，走 saveFlowTemplateNew 免查重）
            再 saveFlow(新流程 id) 重算链路

三个照抄点：

* ``flowBusinessType`` 固定写 ``"1"``，**不**从源流程复制；
* 节点复制时只清 ``nextNodeOid`` / ``previousNodeOid``，``returnNum`` /
  ``returnNodeOid`` 原样带过去（``saveFlow`` 之后会被重算）；
* ``tbFlow(flowName)`` 的入参**完全没用**，同步的永远是全部系统预置流程。

事务：Java 上是 ``@Transactional``，Python 侧没有声明式事务（与其它 Service 一致，
依赖连接自动提交）。失败时同样会留下部分同步结果 —— 这一点与 Java 在
``rollbackFor = Exception.class`` 下的表现不同，记录在 ``COMPATIBILITY.md``。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import get_eps_id, get_user_id
from app.common.utils.string_utils import get_uuid, is_not_empty
from app.flow.domain.flow_name import FlowName
from app.flow.domain.flow_template import FlowTemplate
from app.flow.mapper.flow_name_mapper import FlowNameMapper, get_mapper
from app.flow.service.flow_template_service import (
    FlowTemplateService,
    get_service as get_template_service,
)
from app.system.service.sys_dept_service import SysDeptService
from app.config.database import transactional

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"

#: 流程 key 重复的提示。
DUPLICATE_KEY_MESSAGE = "节点key存在重复"

#: ``tbFlow`` 完成的提示。
SYNC_SUCCESS_MESSAGE = "同步成功！"

#: ``saveFlowName`` 新增时的 ``createBy``（系统预置标记）。
SYSTEM_CREATE_BY = -1

#: 同步出来的流程固定写这个业务类型。
SYNCED_FLOW_BUSINESS_TYPE = "1"

#: 目标部门的标志位：``is_uint = '1'``。
UNIT_DEPT_FLAG = "1"


class FlowNameService:
    """Java: ``class FlowNameServiceImpl implements IFlowNameService``."""

    def __init__(
        self,
        mapper: Optional[FlowNameMapper] = None,
        template_service: Optional[FlowTemplateService] = None,
        dept_service: Optional[SysDeptService] = None,
    ) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()
        self._template_service = (
            template_service if template_service is not None else get_template_service()
        )
        self._dept_service = dept_service if dept_service is not None else SysDeptService()

    # ---------------------------------------------------------------- 查询

    # Java: FlowName selectFlowNameById(String id)
    def select_flow_name_by_id(self, entity_id: str) -> Optional[FlowName]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowName> selectFlowNameList(FlowName flowName)
    def select_flow_name_list(self, query: FlowName) -> List[FlowName]:
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveFlowName(FlowName flowName)
    def save_flow_name(self, flow_name: FlowName) -> AjaxResult:
        if self._mapper.is_exits_key(flow_name) > 0:
            return AjaxResult.error_message(DUPLICATE_KEY_MESSAGE)

        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_name.id):
            # 修改
            flow_name.update_by = user_id  # 更新人
            flow_name.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_name)
        else:
            # 新增
            flow_name.id = get_uuid()  # 主键
            flow_name.del_flag = "0"
            flow_name.eps_id = get_eps_id()  # 当前人所在的部门
            flow_name.create_by = SYSTEM_CREATE_BY  # 创建人
            flow_name.create_time = cur_date  # 创建时间
            flow_name.update_by = user_id  # 更新人
            flow_name.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_name)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_name.id)

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteFlowNameByIds(String[] ids)
    def delete_flow_name_by_ids(self, ids: Any) -> AjaxResult:
        count = self._mapper.delete_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteFlowNameById(String id)
    def delete_flow_name_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 同步

    # Java: AjaxResult tbFlow(FlowName flowName)
    @transactional
    def tb_flow(self, flow_name: FlowName) -> AjaxResult:
        """把系统预置流程复制到所有 ``is_uint = '1'`` 的部门（入参不用）。"""
        user_id = get_user_id()
        cur_date = get_now_date()

        # 先查询流程名称（create_by = -1 即系统预置）
        query_bo = FlowName()
        query_bo.create_by = SYSTEM_CREATE_BY
        flow_name_list = self._mapper.select_list(query_bo)

        # 查询要同步的单位
        dept_query = SysDept()
        dept_query.is_uint = UNIT_DEPT_FLAG
        dept_list = self._dept_service.select_dept_list(dept_query)

        for temp_flow_name in flow_name_list:
            # 查询自己的配置信息
            query_flow_template = FlowTemplate()
            query_flow_template.flow_oid = temp_flow_name.id
            flow_template_list = self._template_service.select_flow_template_list(
                query_flow_template
            )

            for dept_bo in dept_list:
                # 判断是否已存在
                flow_dept_bo = FlowName()
                flow_dept_bo.tenant_id = dept_bo.dept_id
                flow_dept_bo.flow_key = temp_flow_name.flow_key
                if len(self._mapper.select_list(flow_dept_bo)) == 0:
                    # 新增 流程
                    add_flow_name = FlowName()
                    add_flow_name.flow_key = temp_flow_name.flow_key
                    add_flow_name.flow_title = temp_flow_name.flow_title
                    add_flow_name.flow_context = temp_flow_name.flow_context
                    add_flow_name.buss_name = temp_flow_name.buss_name
                    add_flow_name.sort = temp_flow_name.sort

                    add_flow_name.id = get_uuid()  # 主键
                    add_flow_name.del_flag = "0"
                    add_flow_name.eps_id = get_eps_id()  # 当前人所在的部门
                    add_flow_name.create_by = user_id  # 创建人
                    add_flow_name.create_time = cur_date  # 创建时间
                    add_flow_name.update_by = user_id  # 更新人
                    add_flow_name.update_time = cur_date  # 更新时间
                    add_flow_name.tenant_id = dept_bo.dept_id
                    add_flow_name.flow_business_type = SYNCED_FLOW_BUSINESS_TYPE
                    self._mapper.insert(add_flow_name)

                    for add_flow_template in flow_template_list:
                        add_flow_template.id = ""  # 主键
                        add_flow_template.flow_oid = add_flow_name.id  # 流程key
                        add_flow_template.next_node_oid = ""
                        add_flow_template.previous_node_oid = ""
                        self._template_service.save_flow_template_new(add_flow_template)
                    # 设置节点上下顺序
                    self._template_service.save_flow(add_flow_name.id)
        return AjaxResult.success_message(SYNC_SUCCESS_MESSAGE)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowNameService] = None


def get_service() -> FlowNameService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowNameService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = [
    "DUPLICATE_KEY_MESSAGE",
    "FlowNameService",
    "SAVE_SUCCESS_MESSAGE",
    "SYNCED_FLOW_BUSINESS_TYPE",
    "SYNC_CREATE_BY",
    "SYNC_SUCCESS_MESSAGE",
    "SYSTEM_CREATE_BY",
    "UNIT_DEPT_FLAG",
    "get_service",
    "reset_service",
]
