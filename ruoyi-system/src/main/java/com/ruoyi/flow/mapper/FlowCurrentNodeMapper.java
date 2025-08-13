package com.ruoyi.flow.mapper;

import java.util.List;
import com.ruoyi.flow.domain.FlowCurrentNode;
import org.springframework.stereotype.Repository;

/**
 * 流程_当前节点Mapper接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowCurrentNodeMapper 
{
    /**
     * 查询流程_当前节点
     * 
     * @param id 流程_当前节点ID
     * @return 流程_当前节点
     */
    public FlowCurrentNode selectFlowCurrentNodeById(String id);

    /**
     * 查询流程_当前节点列表
     * 
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    public List<FlowCurrentNode> selectFlowCurrentNodeList(FlowCurrentNode flowCurrentNode);

    /**
     * 新增流程_当前节点
     * 
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    public int insertFlowCurrentNode(FlowCurrentNode flowCurrentNode);

    /**
     * 修改流程_当前节点
     * 
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    public int updateFlowCurrentNode(FlowCurrentNode flowCurrentNode);

    /**
     * 删除流程_当前节点
     * 
     * @param id 流程_当前节点ID
     * @return 结果
     */
    public int deleteFlowCurrentNodeById(String id);

    /**
     * 批量删除流程_当前节点
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowCurrentNodeByIds(String[] ids);


    /**
     * 删除流程_当前节点
     *
     * @param billOid；业务流程
     * @return 结果
     */
    public int deleteByBillId(String billOid);


    /**
     * 查询流程_当前节点列表
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    public List<FlowCurrentNode> selectEmpInfoList(FlowCurrentNode flowCurrentNode);


    /**
     * 修改流程_当前节点
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    public int updateFlowTable(FlowCurrentNode flowCurrentNode);


    /**
     * 查询流程_当前节点列表 :根据角色查询
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    public List<FlowCurrentNode> selectUserListByRole(FlowCurrentNode flowCurrentNode);


    /**
     * 查询流程_当前节点列表：根据部门设置的
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    public List<FlowCurrentNode> selectUserListByDept(FlowCurrentNode flowCurrentNode);

}
