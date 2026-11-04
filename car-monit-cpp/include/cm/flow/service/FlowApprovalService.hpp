#pragma once
// 对应 Java: com.ruoyi.flow.service.impl.FlowCurrentNodeServiceImpl 的审批三件套
//   saveFlowAuit / submitReturn / submitEntrustFlow
//
// 这三个方法在 Java 里都是 @Transactional(rollbackFor = Exception.class)：
// 它们要在 flow_current_node / flow_list / flow_message_info / flow_message_dispose /
// flow_apply_info 以及"业务表"（表名来自 flow_name.BUSS_NAME）之间连续写，
// 所以 C++ 侧统一用 cm::db::Transaction 包住，异常向上抛即回滚。
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::flow::service {

/** 业务审核：shValue 传 1/2/3（同意/拒绝/退回），也允许直接传 T/F/R */
cm::core::domain::AjaxResult saveFlowAuit(const cm::Json& body);

/** 撤销流程：仅当当前节点是第一个节点（previous_node_oid = '0'）时允许 */
cm::core::domain::AjaxResult submitReturn(const cm::Json& body);

/** 委托-办理流程：把当前节点的审核人改成被委托人，并记一条委托历史 */
cm::core::domain::AjaxResult submitEntrustFlow(const cm::Json& body);

/** 对应 FlowNameServiceImpl.tbFlow：把 create_by=-1 的模板流程按 is_unit=1 的单位逐个补齐，
 *  连带复制节点并把首尾/退回指针重排。Java 的入参没有被读取，且整个方法是 @Transactional。 */
cm::core::domain::AjaxResult tbFlow();

} // namespace cm::flow::service
