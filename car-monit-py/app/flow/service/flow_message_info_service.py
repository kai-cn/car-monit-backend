"""系统内部消息 Service.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowMessageInfoServiceImpl.java

``saveFlowMessageInfo`` 是本包最常被调用的写方法，语义是"**按业务单据 + 消息类型
+ 业务类型** upsert，然后把这批处理人写成待办"，返回消息主键：

    querybo.setBillOid(...); querybo.setMsgType(...); querybo.setBussType(...);
    List<FlowMessageInfo> queryList = this.selectFlowMessageInfoList(querybo);
    if (queryList.size() > 0) { flowMessageInfo.setId(queryList.get(0).getId()); }
    ...
    for (FlowMessageDispose disposeBo : disposeList) {
        disposeBo.setMid(flowMessageInfo.getId());
        disposeBo.setMsgStatus("2");                       // 未处理
        flowMessageDisposeService.saveFlowMessageDispose(disposeBo);
    }

注意三点
--------
1. ``bussType`` 参与查重（Java 注释写明"要加上 BussType 否则会得到别的类型的数据"）。
   但 ``FlowCurrentNodeServiceImpl#saveFlowAuit`` 里查待办时只传 ``billOid + msgType``，
   不传 ``bussType`` —— 两处条件不一致是现状。
2. ``disposeList`` 若为空，**不报错**，消息主体照样落库。
3. ``dealBusinessMessage`` 没有任何调用点（唯一写 ``hangTime`` 的地方），照抄保留。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils.date_utils import get_now_date
from app.common.utils.security_utils import get_eps_id, get_user_id
from app.common.utils.string_utils import get_uuid, is_not_empty
from app.flow.domain.flow_message_dispose import FlowMessageDispose
from app.flow.domain.flow_message_info import FlowMessageInfo
from app.flow.mapper.flow_message_dispose_mapper import (
    FlowMessageDisposeMapper,
    get_mapper as get_dispose_mapper,
)
from app.flow.mapper.flow_message_info_mapper import FlowMessageInfoMapper, get_mapper
from app.flow.service.flow_message_dispose_service import (
    MSG_STATUS_UNDONE,
    FlowMessageDisposeService,
    get_service as get_dispose_service,
)

#: Java: ``AjaxResult.success("操作成功！", ...)`` 的文案（**带全角感叹号**）。
SAVE_SUCCESS_MESSAGE = "操作成功！"

#: 已办理（``dealBusinessMessage`` 里写的值）。
MSG_STATUS_DONE = "1"


class FlowMessageInfoService:
    """Java: ``class FlowMessageInfoServiceImpl implements IFlowMessageInfoService``."""

    def __init__(
        self,
        mapper: Optional[FlowMessageInfoMapper] = None,
        dispose_mapper: Optional[FlowMessageDisposeMapper] = None,
        dispose_service: Optional[FlowMessageDisposeService] = None,
    ) -> None:
        self._mapper = mapper if mapper is not None else get_mapper()
        self._dispose_mapper = (
            dispose_mapper if dispose_mapper is not None else get_dispose_mapper()
        )
        self._dispose_service = (
            dispose_service if dispose_service is not None else get_dispose_service()
        )

    # ---------------------------------------------------------------- 查询

    # Java: FlowMessageInfo selectFlowMessageInfoById(String id)
    def select_flow_message_info_by_id(self, entity_id: str) -> Optional[FlowMessageInfo]:
        return self._mapper.select_by_id(entity_id)

    # Java: List<FlowMessageInfo> selectFlowMessageInfoList(FlowMessageInfo x)
    def select_flow_message_info_list(self, query: FlowMessageInfo) -> List[FlowMessageInfo]:
        return self._mapper.select_list(query)

    # ---------------------------------------------------------------- 保存

    # Java: String saveFlowMessageInfo(FlowMessageInfo flowMessageInfo)
    def save_flow_message_info(self, flow_message_info: FlowMessageInfo) -> str:
        """按 ``billOid + msgType + bussType`` upsert，返回消息主键。"""
        user_id = get_user_id()
        cur_date = get_now_date()

        # 根据 billOid 查询是否有消息，要加上 BussType 否则会得到别的类型的数据
        query_bo = FlowMessageInfo()
        query_bo.bill_oid = flow_message_info.bill_oid
        # 消息类型(1:通知业务，2:办理业务)
        query_bo.msg_type = flow_message_info.msg_type
        query_bo.buss_type = flow_message_info.buss_type
        query_list = self.select_flow_message_info_list(query_bo)
        if len(query_list) > 0:
            flow_message_info.id = query_list[0].id

        if is_not_empty(flow_message_info.id):
            # 修改
            flow_message_info.update_by = user_id  # 更新人
            flow_message_info.update_time = cur_date  # 更新时间
            self._mapper.update_by_id(flow_message_info)
        else:
            # 新增
            flow_message_info.id = get_uuid()  # 主键
            flow_message_info.del_flag = "0"
            flow_message_info.eps_id = get_eps_id()  # 当前人所在的部门
            flow_message_info.create_by = user_id  # 创建人
            flow_message_info.create_time = cur_date  # 创建时间
            flow_message_info.update_by = user_id  # 更新人
            flow_message_info.update_time = cur_date  # 更新时间
            self._mapper.insert(flow_message_info)

        # 新增明细
        dispose_list = flow_message_info.dispose_list
        if dispose_list is not None and len(dispose_list) > 0:
            for dispose_bo in dispose_list:
                dispose_bo.mid = flow_message_info.id  # 外键
                dispose_bo.msg_status = MSG_STATUS_UNDONE  # 未处理
                # disposeBo.setBussId(); 处理人usr
                self._dispose_service.save_flow_message_dispose(dispose_bo)
        return flow_message_info.id

    # ---------------------------------------------------------------- 删除

    # Java: AjaxResult deleteFlowMessageInfoByIds(String[] ids)
    def delete_flow_message_info_by_ids(self, ids: Any) -> AjaxResult:
        count = self._mapper.delete_by_ids(ids)
        return AjaxResult.success_data(count)

    # Java: AjaxResult deleteFlowMessageInfoById(String id)
    def delete_flow_message_info_by_id(self, entity_id: str) -> AjaxResult:
        count = self._mapper.delete_by_id(entity_id)
        return AjaxResult.success_data(count)

    # ---------------------------------------------------------------- 业务消息

    # Java: void dealBusinessMessage(String messageDisposeId)
    def deal_business_message(self, message_dispose_id: str) -> None:
        """把某条消息里所有待办回写为"已办理 + 处理时间"。

        无调用点（见模块文档），保留以便与 Java 的调用面一致。
        """
        flow_message_dispose = self._dispose_service.select_flow_message_dispose_by_id(
            message_dispose_id
        )
        if flow_message_dispose is not None:
            message_id = flow_message_dispose.mid
            # 更新所有的消息详情信息
            update_bo = FlowMessageDispose()
            # 处理人
            update_bo.buss_name = str(get_user_id())
            # 消息状态 1 => 已办理, 2 => 未办理
            update_bo.msg_status = MSG_STATUS_DONE
            # 处理时间
            update_bo.hang_time = get_now_date()
            # 消息id
            update_bo.mid = message_id

            # 更新处理消息
            self._dispose_mapper.update_business_by_message_id(update_bo)


#: 模块级单例（与 Service 里的 ``@Autowired`` 一一对应）。
_DEFAULT_SERVICE: Optional[FlowMessageInfoService] = None


def get_service() -> FlowMessageInfoService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = FlowMessageInfoService()
    return _DEFAULT_SERVICE


def reset_service() -> None:
    global _DEFAULT_SERVICE
    _DEFAULT_SERVICE = None


__all__ = [
    "FlowMessageInfoService",
    "MSG_STATUS_DONE",
    "SAVE_SUCCESS_MESSAGE",
    "get_service",
    "reset_service",
]
