"""流程_当前节点 Service —— 审批流的核心.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowCurrentNodeServiceImpl.java

这是本工程唯一"有业务"的 Service：提交 / 同意 / 拒绝 / 退回 / 撤销 / 委托，
以及两个无调用点的待办消息工具方法。916 行 Java 逐段对应到下面 8 个入口：

======================  ==========================================================
入口                     作用
======================  ==========================================================
``saveFlowApply``       提交申请：建当前节点 + 消息 + 待办 + 历史 + 回写业务表
``saveFlowAuit``        审核：删旧节点 + 改消息 + 改申请 + 建下一节点 + 通知申请人
``submitReturn``        撤销：仅当当前节点是首节点，删节点/消息/申请并退回"起草中"
``submitEntrustFlow``   委托：换审核人 + 记一条 entrust 历史 + 追加委托 JSON
``getEmpInfoList``      按节点配置找人（人员 / 角色 / 部门领导 / 分管领导 / 值班人）
``getEmpInfoListReturn`` 退回时找人（从 flow_list 历史里取该节点的操作人）
``sendDbMessage``       独立发待办（无调用点）
``auitDbMessage``       独立办待办（无调用点）
======================  ==========================================================

``saveFlowAuit`` 的状态机
------------------------
``shValue`` 由前端传数字，服务内先翻译成字母：

    1 -> "T"（同意）   2 -> "F"（拒绝，现场把 flowStatus 改成 5）
    3 -> "R"（退回）   其它原样

之后的判定顺序（**顺序即语义**）：

1. ``nextNodeOid != "-1" and shValue == "T"`` -> 找下一节点的审批人；
2. ``returnNodeOid != "0" and shValue == "R"`` -> 找退回节点的原审批人；
3. 若 ``nextNodeOid == "-1" and shValue == "T"`` -> ``flowStatus = 3``（通过）；
4. 若 ``returnNodeOid == "0" and shValue == "R"`` -> ``flowStatus = 4``（退回）。

注意第 2 步用的是 ``previousNodeOid`` 而**不是** ``returnNodeOid``：

    // String returnNodeOid = curflowTemplate.getReturnNodeOid(); // 退回节点 或者 上一个节点
    String returnNodeOid = curflowTemplate.getPreviousNodeOid(); // 上一个节点

注释里的旧写法被留在原地，实际生效的是"上一节点"。照抄。

三处"先删后建"
--------------
* ``flowCurrentNodeMapper.deleteByBillId(billOid)`` 是**物理删**，审核时先把该单据的
  所有当前节点删掉，再把下一节点插进去（所以同一单据的"当前节点"永远只有一批）；
* ``saveFlowAuit`` 里先 ``deleteByBillId`` 再 ``saveFlowApplyInfoNew``，最后才
  ``saveFlowNode``；
* ``submitReturn`` 里删节点 -> 删消息 -> 删待办 -> 删我的申请 -> 业务表改回草稿。

``useIds`` 可能为空数组
-----------------------
``saveFlowAuit`` 在"拒绝 / 退回首节点"时 ``empList`` 是空的，于是
``useIds = new String[0]``，``saveFlowList(mid, useIds)`` 只是空循环 —— 待办不新增，
但消息主体仍被更新。照抄，不要加"空就跳过"的分支。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from app.common.constant.constants import (
    FLOW_ENTRUST_NAME,
    FLOW_RESULT_CONTEXT_PREFIX,
    FLOW_RESULT_CONTEXT_SUFFIX,
    FLOW_RESULT_ENTRUST_KEY,
    dept_duty_emp_role,
    dept_manager_role,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.enums.flow_type_enum import FlowTypeEnum
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import (
    get_eps_id,
    get_user_id,
    get_user_real_name,
)
from app.common.utils.string_utils import (
    get_uuid,
    is_blank,
    is_empty,
    is_not_blank,
    is_not_empty,
    trim,
)
from app.flow.domain.entrust_info import EntrustInfo, dump_entrust_list
from app.flow.domain.flow_apply_info import FlowApplyInfo
from app.flow.domain.flow_current_node import FlowCurrentNode
from app.flow.domain.flow_list import FlowList
from app.flow.domain.flow_message_info import FlowMessageInfo
from app.flow.domain.flow_name import FlowName
from app.flow.domain.flow_template import FlowTemplate
from app.flow.mapper.flow_current_node_mapper import (
    FlowCurrentNodeMapper,
    get_mapper,
)
from app.flow.mapper.flow_name_mapper import FlowNameMapper, get_mapper as get_name_mapper
from app.flow.mapper.flow_template_mapper import (
    FlowTemplateMapper,
    get_mapper as get_template_mapper,
)
from app.flow.service.flow_apply_info_service import (
    FlowApplyInfoService,
    get_service as get_apply_info_service,
)
from app.flow.service.flow_list_service import (
    FlowListService,
    get_service as get_list_service,
)
from app.flow.service.flow_message_dispose_service import (
    FlowMessageDisposeService,
    get_service as get_dispose_service,
)
from app.flow.service.flow_message_info_service import (
    FlowMessageInfoService,
    get_service as get_message_info_service,
)
from app.flow.util.flow_constant import ZDY_FLOW
from app.system.mapper.sys_role_mapper import SysRoleMapper
from app.config.database import transactional

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"

#: 提交成功的提示。
APPLY_SUCCESS_MESSAGE = "流程提交成功！"

#: 审核成功的提示。
AUDIT_SUCCESS_MESSAGE = "审核成功！"

#: 撤销成功的提示。
RETURN_SUCCESS_MESSAGE = "撤销成功！"

#: 待办办理成功的提示。
DISPOSE_SUCCESS_MESSAGE = "流程处理成功！"

# ---- 错误文案（逐字照抄 Java，含标点） ------------------------------------

ERROR_FLOW_NOT_FOUND = "流程不存在，请与管理员联系！"
ERROR_NODE_NOT_FOUND = "节点不存在，请与管理员联系！"
ERROR_NEXT_EMP_NOT_FOUND = "该业务找不到下一审批人，请与管理员联系！"
ERROR_CONTEXT_REQUIRED = "请填写审核结论！"
ERROR_BILL_NOT_FOUND = "业务不存在！"
ERROR_ALREADY_AUDITED = "对不起，该单据已审核，请确定！"
ERROR_NEXT_NODE_NOT_FOUND = "下一个节点不存在，请与管理员联系！"
ERROR_RETURN_NODE_NOT_FOUND = "退回节点不存在，请与管理员联系！"
ERROR_RETURN_ALREADY_REVOKED = "撤销失败，该单据已撤销，请确定！"
ERROR_RETURN_ALREADY_AUDITED = "撤销失败，该单据已审核，请确定！"
ERROR_MISSING_PARAMS = "缺少参数!"
ERROR_CURRENT_NODE_NOT_FOUND = "当前流程节点不存在!"
ERROR_TEMPLATE_NOT_FOUND = "找不到对应的流程节点模板信息!"
ERROR_FLOW_NAME_NOT_FOUND = "找不到对应的流程信息!"
ERROR_APPLY_NOT_FOUND = "找不到对应的流程申请信息!"

#: ``fg_manager`` 在 Java 里是硬编码字面量（不在 Constants 里）。
FG_MANAGER_ROLE = "fg_manager"

#: 审核结论字母码与中文名的映射（``saveFlowList`` 用）。
AUDIT_RESULT_LABELS = {
    "S": "提交",
    "T": "同意",
    "F": "拒绝",
    "R": "退回",
    FLOW_RESULT_ENTRUST_KEY: FLOW_ENTRUST_NAME,
}


class FlowCurrentNodeService:
    """Java: ``class FlowCurrentNodeServiceImpl implements IFlowCurrentNodeService``."""

    def __init__(
        self,
        mapper: Optional[FlowCurrentNodeMapper] = None,
        flow_name_mapper: Optional[FlowNameMapper] = None,
        flow_template_mapper: Optional[FlowTemplateMapper] = None,
        role_mapper: Optional[SysRoleMapper] = None,
        flow_apply_info_service: Optional[FlowApplyInfoService] = None,
        flow_message_info_service: Optional[FlowMessageInfoService] = None,
        flow_message_dispose_service: Optional[FlowMessageDisposeService] = None,
        flow_list_service: Optional[FlowListService] = None,
    ) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()
        self._flow_name_mapper = (
            flow_name_mapper if flow_name_mapper is not None else get_name_mapper()
        )
        self._flow_template_mapper = (
            flow_template_mapper
            if flow_template_mapper is not None
            else get_template_mapper()
        )
        self._role_mapper = role_mapper if role_mapper is not None else SysRoleMapper()
        self._flow_apply_info_service = (
            flow_apply_info_service
            if flow_apply_info_service is not None
            else get_apply_info_service()
        )
        self._flow_message_info_service = (
            flow_message_info_service
            if flow_message_info_service is not None
            else get_message_info_service()
        )
        self._flow_message_dispose_service = (
            flow_message_dispose_service
            if flow_message_dispose_service is not None
            else get_dispose_service()
        )
        self._flow_list_service = (
            flow_list_service if flow_list_service is not None else get_list_service()
        )

    # ---------------------------------------------------------------- 查询

    # Java: FlowCurrentNode selectFlowCurrentNodeById(String id)
    def select_flow_current_node_by_id(
        self, entity_id: str
    ) -> Optional[FlowCurrentNode]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowCurrentNode> selectFlowCurrentNodeList(FlowCurrentNode x)
    def select_flow_current_node_list(
        self, query: FlowCurrentNode
    ) -> List[FlowCurrentNode]:
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: AjaxResult saveFlowCurrentNode(FlowCurrentNode flowCurrentNode)
    def save_flow_current_node(self, flow_current_node: FlowCurrentNode) -> AjaxResult:
        user_id = get_user_id()
        cur_date = get_now_date()
        if is_not_empty(flow_current_node.id):
            # 修改
            flow_current_node.update_by = user_id  # 更新人
            flow_current_node.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_current_node)
        else:
            # 新增
            flow_current_node.id = get_uuid()  # 主键
            flow_current_node.del_flag = "0"
            flow_current_node.eps_id = get_eps_id()  # 当前人所在的部门
            flow_current_node.create_by = user_id  # 创建人
            flow_current_node.create_time = cur_date  # 创建时间
            flow_current_node.update_by = user_id  # 更新人
            flow_current_node.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_current_node)
        return AjaxResult.success_message_data(SAVE_SUCCESS_MESSAGE, flow_current_node.id)

    # Java: void saveFlowNode(FlowTemplate, List<FlowCurrentNode>, String, String)
    def save_flow_node(
        self,
        template: FlowTemplate,
        emp_list: Sequence[FlowCurrentNode],
        bill_oid: str,
        project_id: str,
    ) -> None:
        """把"节点模板 × 审批人"展开成 N 条当前节点记录。"""
        for emp in emp_list:
            node = FlowCurrentNode()
            node.bill_oid = bill_oid  # 单据id
            node.flow_oid = template.flow_oid
            node.current_oid = template.id
            node.node_order = template.node_order
            node.node_key = template.node_key
            node.node_name = template.node_name
            node.config_type = template.config_type
            node.config_id = template.config_id
            node.config_name = template.config_name

            node.auit_emp_oid = emp.auit_emp_oid
            node.auit_emp_name = emp.auit_emp_name

            node.back_col1 = project_id  # 项目权限字段

            self.save_flow_current_node(node)

    # Java: void saveFlowList(FlowTemplate, String, String, String, String)
    def save_flow_list(
        self,
        template: FlowTemplate,
        bill_oid: str,
        flow_key: str,
        auit_result: str,
        auit_context: str,
    ) -> None:
        """插一条审核历史（``shKey`` 机器码 + ``shValue`` 中文）。"""
        flow_list = FlowList()
        flow_list.bill_oid = bill_oid
        flow_list.buss_type = flow_key
        flow_list.flow_ruid = template.flow_oid
        flow_list.current_oid = template.id
        flow_list.sh_user = get_user_real_name()
        flow_list.sh_key = auit_result
        label = AUDIT_RESULT_LABELS.get(auit_result)
        if label is not None:
            flow_list.sh_value = label
        flow_list.sh_context = auit_context
        self._flow_list_service.save_flow_list(flow_list)

    # ---------------------------------------------------------------- 找人

    # Java: List<FlowCurrentNode> getEmpInfoListReturn(String, FlowTemplate, String, String)
    def get_emp_info_list_return(
        self,
        flow_key: str,
        flow_template: FlowTemplate,
        bill_oid: str,
        project_id: str,
    ) -> List[FlowCurrentNode]:
        """退回时的审批人 = 该节点最近一次操作的发起人（取自 ``flow_list``）。"""
        result: List[FlowCurrentNode] = []
        flow_list = FlowList()
        flow_list.bill_oid = bill_oid
        flow_list.current_oid = flow_template.id  # 上一个节点
        temp_list = self._flow_list_service.select_flow_list_list_new(flow_list)
        if len(temp_list) > 0:
            temp_vo = temp_list[0]
            emp_node = FlowCurrentNode()
            emp_node.auit_emp_oid = f"{temp_vo.create_by}"
            emp_node.auit_emp_name = temp_vo.sh_user
            result.append(emp_node)
        return result

    # Java: List<FlowCurrentNode> getEmpInfoList(String, String, FlowTemplate, String, String)
    def get_emp_info_list(
        self,
        flow_key: str,
        table_name: str,
        flow_template: FlowTemplate,
        bill_oid: str,
        project_id: str,
    ) -> List[FlowCurrentNode]:
        """按节点配置找人：``configType == '1'`` 是人员，其余按角色分支。"""
        result: List[FlowCurrentNode] = []
        # 判断是人还是角色  1人员2角色3其他
        config_type = trim(flow_template.config_type)
        # 人员或者角色id
        config_id = trim(flow_template.config_id)

        user_id = get_user_id()

        if is_not_empty(config_id):
            if config_type == "1":
                # 1人员
                emp_node = FlowCurrentNode()
                emp_node.auit_emp_oid = config_id
                emp_node.auit_emp_name = flow_template.config_name
                result.append(emp_node)
            else:
                # 角色
                query_bo = FlowCurrentNode()
                query_bo.role_id = config_id
                query_bo.bill_oid = bill_oid

                # 获取角色对象（注意 Java 用的是**未 trim** 的 configId）
                role = self._role_mapper.select_role_by_id(int(flow_template.config_id))
                if role is not None and role.role_id is not None:
                    if role.role_key == dept_manager_role:
                        # 部门领导审核 : 根据部门设置
                        query_bo.flag = "bmjlAudit"
                        query_bo.role_id = ""
                        query_bo.tenant_id = None
                        query_bo.back_col1 = f"{user_id}"
                    elif role.role_key == FG_MANAGER_ROLE:
                        # 分管领导审核
                        query_bo.flag = "fgldAudit"
                        query_bo.role_id = ""
                        query_bo.tenant_id = None
                        query_bo.back_col1 = f"{user_id}"
                    elif role.role_key == dept_duty_emp_role:
                        # 科室值班人审核 ： 找到归属部门的
                        query_bo.flag = "dutyAudit"
                        query_bo.tenant_id = None
                        query_bo.back_col1 = table_name  # 表名称
                    result = self._mapper.select_emp_info_list(query_bo)
        return result

    # ---------------------------------------------------------------- 提交

    # Java: AjaxResult saveFlowApply(String, String, String, Map<String, Object>)
    @transactional
    def save_flow_apply(
        self,
        flow_key: str,
        bill_oid: str,
        project_id: str,
        params: Optional[Dict[str, Any]],
    ) -> AjaxResult:
        """提交流程申请（业务单据提交时调）。"""
        # 根据流程flowKey 查询流程节点id
        flow_name = FlowName()
        flow_name.flow_key = flow_key

        flow_name_list = self._flow_name_mapper.select_list(flow_name)
        if len(flow_name_list) > 0:
            flow_name = flow_name_list[0]
        else:
            return AjaxResult.error_message(ERROR_FLOW_NOT_FOUND)

        # 根据流程查找第一个节点
        flow_template = FlowTemplate()
        flow_template.flow_oid = flow_name.id
        flow_template.previous_node_oid = "0"
        flow_template_list = self._flow_template_mapper.select_list(flow_template)
        if len(flow_template_list) > 0:
            flow_template = flow_template_list[0]
        else:
            return AjaxResult.error_message(ERROR_NODE_NOT_FOUND)

        # 根据节点查询审核人
        emp_list = self.get_emp_info_list(
            flow_key, flow_name.buss_name, flow_template, bill_oid, project_id
        )
        if len(emp_list) == 0:
            return AjaxResult.error_message(ERROR_NEXT_EMP_NOT_FOUND)

        auit_names = ""  # 处理人名称
        use_ids: List[str] = []
        for emp in emp_list:
            use_ids.append(emp.auit_emp_oid)
            auit_names += f"{emp.auit_emp_name},"

        if auit_names.endswith(","):
            auit_names = auit_names[: len(auit_names) - 1]

        flow_status = f"{FlowTypeEnum.APPROVE.get_code()}"  # 流程状态
        flow_ruid = flow_name.id  # 流程实例ID
        flow_apply_oid = "-1"  # 流程申请ID
        real_name = get_user_real_name()  # 提交人
        buss_type_name = flow_name.flow_title  # 业务名称
        table_name = flow_name.buss_name  # 表名

        # 提交的业务名称
        buss_title = buss_type_name
        if params is not None:
            if params.get("bussTitle") is not None:
                buss_title = str(params.get("bussTitle"))

        msg_title1 = f"【{buss_type_name}】你提交关于{buss_title}的申请！"
        msg_title2 = f"【{buss_type_name}】{real_name}提交关于{buss_title}的申请！"

        # 我的申请插入一条记录
        flow_apply_info = FlowApplyInfo()
        flow_apply_info.bill_oid = bill_oid
        flow_apply_info.buss_type = flow_key
        flow_apply_info.flow_ruid = flow_ruid
        flow_apply_info.msg_type = "1"
        flow_apply_info.flow_status = flow_status
        flow_apply_info.apply_name = real_name
        flow_apply_info.msg_title = msg_title1
        flow_apply_info.back_col1 = auit_names  # 当前处理人

        flow_apply_oid = self._flow_apply_info_service.save_flow_apply_info_new(
            flow_apply_info
        )

        # 插入下一个节点
        self.save_flow_node(flow_template, emp_list, bill_oid, project_id)

        # 发送消息主体
        flow_message_info = FlowMessageInfo()
        flow_message_info.bill_oid = bill_oid
        flow_message_info.buss_type = flow_key
        flow_message_info.flow_ruid = flow_ruid
        flow_message_info.msg_type = "2"
        flow_message_info.apply_name = real_name
        flow_message_info.msg_title = msg_title2
        mid = self._flow_message_info_service.save_flow_message_info(flow_message_info)
        # 发送消息明细
        self._flow_message_dispose_service.save_flow_list(mid, use_ids)

        # 插入审核历史记录
        self.save_flow_list(flow_template, bill_oid, flow_key, "S", "")

        # 反该业务状态
        bo = FlowCurrentNode()
        bo.table_name = table_name
        bo.bill_oid = bill_oid
        bo.flow_key = flow_key
        bo.flow_ruid = flow_ruid
        bo.flow_apply_oid = flow_apply_oid
        bo.flow_status = flow_status
        self._mapper.update_flow_table(bo)

        return AjaxResult.success_message(APPLY_SUCCESS_MESSAGE)

    # ---------------------------------------------------------------- 审核

    # Java: AjaxResult saveFlowAuit(FlowCurrentNode flowCurrentNode)
    @transactional
    def save_flow_auit(self, flow_current_node: FlowCurrentNode) -> AjaxResult:
        """业务审核（同意 / 拒绝 / 退回）。"""
        sh_value = flow_current_node.sh_value
        bill_oid = flow_current_node.bill_oid
        project_id = ""
        flow_status = f"{FlowTypeEnum.APPROVE.get_code()}"  # 流程状态
        if sh_value is not None:
            if sh_value == "1":
                sh_value = "T"
            elif sh_value == "2":
                sh_value = "F"
                flow_status = f"{FlowTypeEnum.STOP.get_code()}"
            elif sh_value == "3":
                sh_value = "R"

        if is_empty(sh_value):
            return AjaxResult.error_message(ERROR_CONTEXT_REQUIRED)

        if is_empty(bill_oid):
            return AjaxResult.error_message(ERROR_BILL_NOT_FOUND)

        # 获取当前节点
        query_bo = FlowCurrentNode()
        query_bo.bill_oid = bill_oid
        query_bo.auit_emp_oid = f"{get_user_id()}"
        current_list = self.select_flow_current_node_list(query_bo)
        new_current: Optional[FlowCurrentNode] = None
        if len(current_list) > 0:
            new_current = current_list[0]
            if is_not_empty(new_current.back_col1):
                project_id = new_current.back_col1
        else:
            return AjaxResult.error_message(ERROR_ALREADY_AUDITED)

        # 当前节点
        cur_flow_template = self._flow_template_mapper.select_by_id(new_current.current_oid)
        next_node_oid = cur_flow_template.next_node_oid  # 等于-1 最后一个节点不需要 查找
        # String returnNodeOid = curflowTemplate.getReturnNodeOid(); // 退回节点 或者 上一个节点
        return_node_oid = cur_flow_template.previous_node_oid  # 上一个节点
        # 当前审核节点
        flow_name = self._flow_name_mapper.select_by_id(cur_flow_template.flow_oid)

        next_flow_template = FlowTemplate()  # 下一个节点信息
        # 根据节点查询审核人
        emp_list: List[FlowCurrentNode] = []
        # 不是下一个节点
        if next_node_oid != "-1" and sh_value == "T":
            # 同意查询下一个人
            next_flow_template = self._flow_template_mapper.select_by_id(next_node_oid)
            if next_flow_template is not None and is_not_empty(next_flow_template.id):
                emp_list = self.get_emp_info_list(
                    flow_name.flow_key,
                    flow_name.buss_name,
                    next_flow_template,
                    bill_oid,
                    project_id,
                )
                if len(emp_list) == 0:
                    return AjaxResult.error_message(ERROR_NEXT_EMP_NOT_FOUND)
            else:
                return AjaxResult.error_message(ERROR_NEXT_NODE_NOT_FOUND)

        elif return_node_oid != "0" and sh_value == "R":
            # 退回查询下一个审核人
            next_flow_template = self._flow_template_mapper.select_by_id(return_node_oid)
            if next_flow_template is not None and is_not_empty(next_flow_template.id):
                emp_list = self.get_emp_info_list_return(
                    flow_name.flow_key, next_flow_template, bill_oid, project_id
                )
                if len(emp_list) == 0:
                    return AjaxResult.error_message(ERROR_NEXT_EMP_NOT_FOUND)
            else:
                return AjaxResult.error_message(ERROR_RETURN_NODE_NOT_FOUND)

        # 处理人名称
        auit_names = ""
        use_ids: List[str] = []
        for emp in emp_list:
            use_ids.append(emp.auit_emp_oid)
            auit_names += f"{emp.auit_emp_name},"

        if auit_names.endswith(","):
            auit_names = auit_names[: len(auit_names) - 1]

        # 审核通过
        if next_node_oid == "-1" and sh_value == "T":
            flow_status = f"{FlowTypeEnum.END.get_code()}"

        # 审核退回
        if return_node_oid == "0" and sh_value == "R":
            flow_status = f"{FlowTypeEnum.RETURN.get_code()}"

        buss_type_name = flow_name.flow_title  # 业务名称
        table_name = flow_name.buss_name  # 表名
        flow_key = flow_name.flow_key  # 流程key
        flow_ruid = flow_name.id  # 流程实例ID
        flow_apply_oid = "-1"  # 流程申请ID

        # 先删除下当前节点（物理删）
        self._mapper.delete_by_bill_id(bill_oid)
        # 修改消息主体
        flow_message_info = FlowMessageInfo()
        flow_message_info.bill_oid = bill_oid
        flow_message_info.msg_type = "2"
        mid = self._flow_message_info_service.save_flow_message_info(flow_message_info)

        # 消息的待办全部设置为自己
        self._flow_message_dispose_service.save_szzd_flow_message_all(
            mid, f"{get_user_id()}"
        )

        # 修改我的我的申请
        flow_apply_info = FlowApplyInfo()
        flow_apply_info.bill_oid = bill_oid
        flow_apply_info.flow_status = flow_status
        flow_apply_info.back_col1 = auit_names
        flow_apply_oid = self._flow_apply_info_service.save_flow_apply_info_new(
            flow_apply_info
        )

        # 申请人ID
        apply_id = self._flow_apply_info_service.select_flow_apply_info_by_id(
            flow_apply_oid
        ).create_by

        # 修改业务状态
        bo = FlowCurrentNode()
        bo.table_name = table_name
        bo.bill_oid = bill_oid
        bo.flow_status = flow_status

        self._mapper.update_flow_table(bo)

        # 插入审核意见
        self.save_flow_list(
            cur_flow_template, bill_oid, flow_key, sh_value, flow_current_node.sh_context
        )

        # 插入下一个节点
        self.save_flow_node(next_flow_template, emp_list, bill_oid, project_id)
        # 发送消息明细
        self._flow_message_dispose_service.save_flow_list(mid, use_ids)

        msg_title1 = ""
        # ------------业务反该区域----------------------------
        if flow_status == f"{FlowTypeEnum.END.get_code()}":
            # 审核通过。。。
            msg_title1 += f"你提交的{buss_type_name}业务已通过，请查看！"

        elif flow_status == f"{FlowTypeEnum.STOP.get_code()}":
            # 审核拒绝。。。
            msg_title1 += f"你提交的{buss_type_name}业务已拒绝，请查看！"

        elif flow_status == f"{FlowTypeEnum.RETURN.get_code()}":
            # 审核退回。。。
            msg_title1 += f"你提交的{buss_type_name}业务已退回，请查看！"

        # 流程结束回调（Java 里同样是三行注释，业务实现已被摘除）
        if flow_key == "expert_apply_key" and flow_status != f"{FlowTypeEnum.APPROVE.get_code()}":
            # 专家申请
            # expertApplyInfoService.callbackMethod(billOid, flowStatus);
            pass
        elif flow_key == "dev_apply_key" and flow_status != f"{FlowTypeEnum.APPROVE.get_code()}":
            # 设备申请
            # devApplyInfoService.callbackMethod(billOid, flowStatus);
            pass
        elif flow_key == "res_info_key" and flow_status != f"{FlowTypeEnum.APPROVE.get_code()}":
            pass

        # 发送消息给申请人
        if msg_title1 != "":
            # 发送消息主体
            gr_flow_message_info = FlowMessageInfo()
            gr_flow_message_info.bill_oid = bill_oid
            gr_flow_message_info.buss_type = flow_key
            gr_flow_message_info.flow_ruid = flow_ruid
            gr_flow_message_info.msg_type = "1"
            # grflowMessageInfo.setApplyName(realName);
            gr_flow_message_info.msg_title = msg_title1
            grmid = self._flow_message_info_service.save_flow_message_info(
                gr_flow_message_info
            )
            gr_use_ids = [f"{apply_id}"]
            # 发送消息明细
            self._flow_message_dispose_service.save_flow_list(grmid, gr_use_ids)

        return AjaxResult.success_message(AUDIT_SUCCESS_MESSAGE)

    # ---------------------------------------------------------------- 撤销

    # Java: AjaxResult submitReturn(FlowCurrentNode flowCurrentNode)
    @transactional
    def submit_return(self, flow_current_node: FlowCurrentNode) -> AjaxResult:
        """撤销流程 —— 只有"当前节点是第一节点"时才允许。"""
        # 根据当前业务ID查询是否是第一个节点
        bill_oid = flow_current_node.bill_oid
        if is_empty(bill_oid):
            return AjaxResult.error_message(ERROR_BILL_NOT_FOUND)

        # 根据当前业务查询节点
        query_bo = FlowCurrentNode()
        query_bo.bill_oid = bill_oid
        current_list = self.select_flow_current_node_list(query_bo)
        new_current: Optional[FlowCurrentNode] = None
        if len(current_list) > 0:
            new_current = current_list[0]
        else:
            return AjaxResult.error_message(ERROR_RETURN_ALREADY_REVOKED)

        # 当前节点
        cur_flow_template = self._flow_template_mapper.select_by_id(new_current.current_oid)
        previous_node_oid = cur_flow_template.previous_node_oid
        if previous_node_oid == "0":
            # 当前审核节点
            flow_name = self._flow_name_mapper.select_by_id(cur_flow_template.flow_oid)

            # 删除当前节点数据（物理删）
            self._mapper.delete_by_bill_id(bill_oid)

            # 修改消息
            flow_message_info = FlowMessageInfo()
            flow_message_info.bill_oid = bill_oid
            flow_message_info.msg_type = "2"
            msg_list = self._flow_message_info_service.select_flow_message_info_list(
                flow_message_info
            )
            if len(msg_list) > 0:
                mid = msg_list[0].id
                self._flow_message_info_service.delete_flow_message_info_by_id(mid)
                # 消息的待办全部设置为自己
                self._flow_message_dispose_service.remove_flow_message(mid, "")

            # 删除我的申请
            # 注意：Java 传的是 flowCurrentNode.getId()（请求体里的 id），不是申请 id
            self._flow_apply_info_service.delete_flow_apply_info_by_id(
                flow_current_node.id
            )

            # 单据状态修改成草稿
            table_name = flow_name.buss_name  # 表名
            bo = FlowCurrentNode()
            bo.table_name = table_name
            bo.bill_oid = bill_oid
            bo.flow_status = f"{FlowTypeEnum.SUBMIT.get_code()}"
            self._mapper.update_flow_table(bo)

        else:
            return AjaxResult.error_message(ERROR_RETURN_ALREADY_AUDITED)

        return AjaxResult.success_message(RETURN_SUCCESS_MESSAGE)

    # ---------------------------------------------------------------- 委托

    # Java: AjaxResult submitEntrustFlow(FlowCurrentNode flowCurrentNode)
    @transactional
    def submit_entrust_flow(self, flow_current_node: FlowCurrentNode) -> AjaxResult:
        """把当前节点委托给他人办理，并在 ``flow_apply_info.entrust_info`` 追加记录。"""
        if (
            is_blank(flow_current_node.entrust_user_id)
            or is_blank(flow_current_node.entrust_user_name)
            or is_blank(flow_current_node.bill_oid)
        ):
            return AjaxResult.error_message(ERROR_MISSING_PARAMS)
        bill_oid = flow_current_node.bill_oid
        user_id = get_user_id()

        # 流程结果(委托)
        flow_result = FLOW_RESULT_ENTRUST_KEY
        # 流程结果内容
        flow_result_context = (
            FLOW_RESULT_CONTEXT_PREFIX
            + flow_current_node.entrust_user_name
            + FLOW_RESULT_CONTEXT_SUFFIX
        )

        # 获取当前流程节点
        query_bo = FlowCurrentNode()
        query_bo.bill_oid = bill_oid
        query_bo.auit_emp_oid = f"{user_id}"
        current_node_list = self.select_flow_current_node_list(query_bo)
        if len(current_node_list) == 0:
            return AjaxResult.error_message(ERROR_CURRENT_NODE_NOT_FOUND)
        current_node = current_node_list[0]

        # 查询当前流程节点对应的流程模板
        flow_template = self._flow_template_mapper.select_by_id(current_node.current_oid)
        if flow_template is None:
            return AjaxResult.error_message(ERROR_TEMPLATE_NOT_FOUND)

        # 查询当前流程信息
        flow_name = self._flow_name_mapper.select_by_id(flow_template.flow_oid)
        if flow_name is None:
            return AjaxResult.error_message(ERROR_FLOW_NAME_NOT_FOUND)

        # 查询流程申请信息
        flow_apply_info = self._flow_apply_info_service.select_by_bill_id(bill_oid)
        if flow_apply_info is None:
            return AjaxResult.error_message(ERROR_APPLY_NOT_FOUND)

        # ---- 更新当前流程节点数据 ----
        # 设置委托审核人id
        current_node.auit_emp_oid = flow_current_node.entrust_user_id
        # 设置委托审核人名称
        current_node.auit_emp_name = flow_current_node.entrust_user_name
        # 设置委托之前的审核人id
        current_node.back_col2 = f"{get_user_id()}"
        # 设置委托之前的审核人名称
        current_node.back_col3 = get_user_real_name()
        self.save_flow_current_node(current_node)

        # ---- 保存流程委托信息 ----
        self.save_flow_list(
            flow_template, bill_oid, flow_name.flow_key, flow_result, flow_result_context
        )

        # ---- 设置流程信息 ----
        # 将流程信息设置为已办理
        message_query_bo = FlowMessageInfo()
        message_query_bo.bill_oid = bill_oid
        message_query_bo.msg_type = "2"
        message_info_id = self._flow_message_info_service.save_flow_message_info(
            message_query_bo
        )

        # 设置当前流程节点的流程消息的处理人全部为当前操作人, 并设置为已处理
        self._flow_message_dispose_service.save_szzd_flow_message_all(
            message_info_id, f"{get_user_id()}"
        )

        # 发送消息给委派的人员
        self._flow_message_dispose_service.save_flow_list(
            message_info_id, [flow_current_node.entrust_user_id]
        )

        # ---- 保存委派的信息记录 ----
        entrust_info_json_str = flow_apply_info.entrust_info

        entrust_info = EntrustInfo()
        # 操作人id
        entrust_info.operator_user_id = f"{get_user_id()}"
        # 操作人
        entrust_info.operator_user_name = get_user_real_name()
        # 委托人id
        entrust_info.entrust_user_id = flow_current_node.entrust_user_id
        # 委托人
        entrust_info.entrust_user_name = flow_current_node.entrust_user_name
        # 操作时间
        entrust_info.operation_time = datetime.now()
        # 流程id
        entrust_info.flow_id = flow_name.id
        # 流程key
        entrust_info.flow_key = flow_name.flow_key
        # 流程模板节点id
        entrust_info.flow_template_id = flow_template.id

        # 更新数据
        update_bo = FlowApplyInfo()
        update_bo.id = flow_apply_info.id
        # 设置当前审核人信息
        update_bo.back_col1 = flow_current_node.entrust_user_name
        if is_not_blank(entrust_info_json_str):
            # 更新委托数据
            entrust_info_list = _parse_entrust_list(entrust_info_json_str)
            if len(entrust_info_list) > 0:
                entrust_info_list.append(entrust_info)
                update_bo.entrust_info = dump_entrust_list(entrust_info_list)
            else:
                # 新增委托数据
                update_bo.entrust_info = dump_entrust_list([entrust_info])
        else:
            # 新增委托数据
            update_bo.entrust_info = dump_entrust_list([entrust_info])
        # 更新流程申请信息, 添加委派信息
        self._flow_apply_info_service.save_flow_apply_info(update_bo)

        return AjaxResult.success()

    # ---------------------------------------------------------------- 待办工具

    # Java: List<FlowCurrentNode> selectUserListByRole(FlowCurrentNode flowCurrentNode)
    def select_user_list_by_role(
        self, flow_current_node: FlowCurrentNode
    ) -> List[FlowCurrentNode]:
        """``dept_manager`` 走"部门设置的分管领导"，其余按角色 + 部门查。"""
        if flow_current_node.role_key == dept_manager_role:
            # 根据部门设置的分管领导
            return self._mapper.select_user_list_by_dept(flow_current_node)
        # 根据角色和部门查询人员
        return self._mapper.select_user_list_by_role(flow_current_node)

    # Java: AjaxResult sendDbMessage(String, String, String, List<FlowCurrentNode>, String, Map)
    def send_db_message(
        self,
        flow_key: str,
        bill_oid: str,
        msg_type: str,
        emp_list: Optional[Sequence[FlowCurrentNode]],
        msg_title: str,
        params: Optional[Dict[str, Any]],
    ) -> AjaxResult:
        """独立发一条待办（无调用点，照抄）。"""
        if emp_list is None or len(emp_list) == 0:
            return AjaxResult.error_message(ERROR_NEXT_EMP_NOT_FOUND)
        real_name = get_user_real_name()  # 提交人

        # 发送消息主体
        flow_message_info = FlowMessageInfo()
        flow_message_info.buss_type = flow_key
        flow_message_info.bill_oid = bill_oid
        flow_message_info.flow_ruid = ZDY_FLOW  # 自定义流程
        flow_message_info.msg_type = msg_type

        flow_message_info.apply_name = real_name
        flow_message_info.msg_title = msg_title
        mid = self._flow_message_info_service.save_flow_message_info(flow_message_info)

        use_ids: List[str] = []
        for emp in emp_list:
            use_ids.append(emp.auit_emp_oid)

        # 发送消息明细
        self._flow_message_dispose_service.save_flow_list(mid, use_ids)

        return AjaxResult.success_message(APPLY_SUCCESS_MESSAGE)

    # Java: AjaxResult auitDbMessage(String, String, String, Map)
    def auit_db_message(
        self,
        flow_key: str,
        bill_oid: str,
        msg_type: str,
        params: Optional[Dict[str, Any]],
    ) -> AjaxResult:
        """独立办一条待办（无调用点，照抄）。"""
        # 修改消息主体
        flow_message_info = FlowMessageInfo()
        flow_message_info.buss_type = flow_key
        flow_message_info.bill_oid = bill_oid
        flow_message_info.msg_type = msg_type
        flow_message_info.flow_ruid = ZDY_FLOW  # 自定义流程
        info_list = self._flow_message_info_service.select_flow_message_info_list(
            flow_message_info
        )
        if info_list is not None and len(info_list) > 0:
            # 消息的待办全部设置为自己
            self._flow_message_dispose_service.save_szzd_flow_message_all(
                info_list[0].id, f"{get_user_id()}"
            )
        else:
            return AjaxResult.error_message(ERROR_NEXT_EMP_NOT_FOUND)
        return AjaxResult.success_message(DISPOSE_SUCCESS_MESSAGE)


def _parse_entrust_list(raw: str) -> List[EntrustInfo]:
    """Java: ``JSON.parseArray(entrustInfoJsonStr, EntrustInfo.class)``。

    fastjson2 对**非法 JSON** 抛 ``JSONException``（HTTP 500）；这里同样让它抛
    （``json.JSONDecodeError``），不一致的只是异常类型。
    """
    payload = json.loads(raw)
    if not isinstance(payload, list):
        return []
    return [EntrustInfo.model_validate(item) for item in payload]


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowCurrentNodeService] = None


def get_service() -> FlowCurrentNodeService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowCurrentNodeService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = [
    "APPLY_SUCCESS_MESSAGE",
    "AUDIT_SUCCESS_MESSAGE",
    "DISPOSE_SUCCESS_MESSAGE",
    "FlowCurrentNodeService",
    "RETURN_SUCCESS_MESSAGE",
    "SAVE_SUCCESS_MESSAGE",
    "get_service",
    "reset_service",
]
