package com.ruoyi.flow.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.flow.domain.FlowCurrentNode;

import java.util.List;
import java.util.Map;

/**
 * 流程_当前节点Service接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowCurrentNodeService {

    /**
     * 查询流程_当前节点
     * 
     * @param id 流程_当前节点ID
     * @return 流程_当前节点
     */
    FlowCurrentNode selectFlowCurrentNodeById(String id);

    /**
     * 查询流程_当前节点列表
     * 
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    List<FlowCurrentNode> selectFlowCurrentNodeList(FlowCurrentNode flowCurrentNode);

    /**
     * 新增或者修改流程_当前节点
     * 
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    AjaxResult saveFlowCurrentNode(FlowCurrentNode flowCurrentNode);

    /**
     * 批量删除流程_当前节点
     * 
     * @param ids 需要删除的流程_当前节点ID
     * @return 结果
     */
    AjaxResult deleteFlowCurrentNodeByIds(String[] ids);

    /**
     * 删除流程_当前节点信息
     * 
     * @param id 流程_当前节点ID
     * @return 结果
     */
    AjaxResult deleteFlowCurrentNodeById(String id);

    /**
     * 根据单据id : 删除流程_当前节点信息
     *
     * @param billOid
     * @return 结果
     */
    AjaxResult deleteByBillId(String billOid);

    /**
     * 提交流程申请
     * @param flowKey：业务key
     * @param billOid: 业务单据ID
     * @param projectId: 项目权限
     * @param params
     * @return
     */
    AjaxResult saveFlowApply(String flowKey, String billOid, String projectId,Map<String, Object> params);

    /**
     * 业务审核
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    AjaxResult saveFlowAuit(FlowCurrentNode flowCurrentNode);

    /**
     * 业务审核  -- 撤销流程
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    AjaxResult submitReturn(FlowCurrentNode flowCurrentNode);

    /**
     * 委托-办理流程
     * @param flowCurrentNode
     * @return
     */
    AjaxResult submitEntrustFlow(FlowCurrentNode flowCurrentNode);



    /**
     * 根据角色查询用户信息
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    List<FlowCurrentNode> selectUserListByRole(FlowCurrentNode flowCurrentNode);



    /**
     * 发送待办消息
     * @param flowKey：流程key
     * @param billOid：单据ID
     * @param msgType: 消息类型(1:通知业务，2:办理业务)
     * @param empList：处理人集合
     * @param msgTitle：发送消息
     * @param params 其他参数
     * @return
     */
    AjaxResult sendDbMessage(String flowKey, String billOid, String msgType, List<FlowCurrentNode> empList,
                             String msgTitle, Map<String, Object> params);



    /**
     * 处理待办消息
     * @param flowKey：流程key
     * @param billOid：单据ID
     * @param msgType: 消息类型(1:通知业务，2:办理业务)
     * @param params 其他参数
     * @return
     */
    AjaxResult auitDbMessage(String flowKey, String billOid, String msgType, Map<String, Object> params);
}
