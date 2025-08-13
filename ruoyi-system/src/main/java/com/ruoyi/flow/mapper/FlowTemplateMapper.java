package com.ruoyi.flow.mapper;

import com.ruoyi.flow.domain.FlowTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 流程节点Mapper接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowTemplateMapper 
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
     * 新增流程节点
     * 
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public int insertFlowTemplate(FlowTemplate flowTemplate);

    /**
     * 修改流程节点
     * 
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public int updateFlowTemplate(FlowTemplate flowTemplate);

    /**
     * 删除流程节点
     * 
     * @param id 流程节点ID
     * @return 结果
     */
    public int deleteFlowTemplateById(String id);

    /**
     * 批量删除流程节点
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowTemplateByIds(String[] ids);


    /**
     * 节点key 是否存在
     *
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public int isExitsKey(FlowTemplate flowTemplate);


    /**
     * 节点排序 是否存在
     *
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public int isExitsSort(FlowTemplate flowTemplate);
}
