package com.ruoyi.flow.service;

import java.util.List;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.flow.domain.FlowTemplate;

/**
 * 流程节点Service接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowTemplateService 
{
    /**
     * 查询流程节点
     * 
     * @param id 流程节点ID
     * @return 流程节点
     */
    public FlowTemplate selectFlowTemplateById(String id);

    /**
     * 查询流程节点列表
     * 
     * @param flowTemplate 流程节点
     * @return 流程节点集合
     */
    public List<FlowTemplate> selectFlowTemplateList(FlowTemplate flowTemplate);

    /**
     * 新增或者修改流程节点
     * 
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public AjaxResult saveFlowTemplate(FlowTemplate flowTemplate);


    /**
     * 新增或者修改流程节点
     *
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public AjaxResult saveFlowTemplateNew(FlowTemplate flowTemplate);

    public void saveFlow(String flowOid);

    /**
     * 批量删除流程节点
     * 
     * @param ids 需要删除的流程节点ID
     * @return 结果
     */
    public AjaxResult deleteFlowTemplateByIds(String[] ids);

    /**
     * 删除流程节点信息
     * 
     * @param id 流程节点ID
     * @return 结果
     */
    public AjaxResult deleteFlowTemplateById(String id);
}
