package com.ruoyi.flow.service;

import java.util.List;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.flow.domain.FlowName;

/**
 * 流程名称Service接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowNameService 
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
     * 新增或者修改流程名称
     * 
     * @param flowName 流程名称
     * @return 结果
     */
    public AjaxResult saveFlowName(FlowName flowName);

    /**
     * 批量删除流程名称
     * 
     * @param ids 需要删除的流程名称ID
     * @return 结果
     */
    public AjaxResult deleteFlowNameByIds(String[] ids);

    /**
     * 删除流程名称信息
     * 
     * @param id 流程名称ID
     * @return 结果
     */
    public AjaxResult deleteFlowNameById(String id);

    /**
     * 同步其他单位的工作流
     *
     * @param flowName 流程名称
     * @return 结果
     */
    public AjaxResult tbFlow(FlowName flowName);
}
