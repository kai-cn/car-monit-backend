package com.ruoyi.flow.mapper;

import com.ruoyi.flow.domain.FlowName;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 流程名称Mapper接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowNameMapper 
{
    /**
     * 查询流程名称
     * 
     * @param id 流程名称ID
     * @return 流程名称
     */
    public FlowName selectFlowNameById(String id);

    /**
     * 查询流程名称列表
     * 
     * @param flowName 流程名称
     * @return 流程名称集合
     */
    public List<FlowName> selectFlowNameList(FlowName flowName);

    /**
     * 新增流程名称
     * 
     * @param flowName 流程名称
     * @return 结果
     */
    public int insertFlowName(FlowName flowName);

    /**
     * 修改流程名称
     * 
     * @param flowName 流程名称
     * @return 结果
     */
    public int updateFlowName(FlowName flowName);

    /**
     * 删除流程名称
     * 
     * @param id 流程名称ID
     * @return 结果
     */
    public int deleteFlowNameById(String id);

    /**
     * 批量删除流程名称
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowNameByIds(String[] ids);


    /**
     * 节点key 是否存在
     *
     * @param flowName 流程节点
     * @return 结果
     */
    public int isExitsKey(FlowName flowName);
}
