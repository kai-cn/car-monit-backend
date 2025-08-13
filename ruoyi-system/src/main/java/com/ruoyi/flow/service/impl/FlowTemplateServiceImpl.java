package com.ruoyi.flow.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.flow.domain.FlowTemplate;
import com.ruoyi.flow.mapper.FlowTemplateMapper;
import com.ruoyi.flow.service.IFlowTemplateService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 流程节点Service业务层处理
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowTemplateServiceImpl implements IFlowTemplateService 
{
    @Autowired
    private FlowTemplateMapper flowTemplateMapper;

    /**
     * 查询流程节点
     * 
     * @param id 流程节点ID
     * @return 流程节点
     */
    @Override
    public FlowTemplate selectFlowTemplateById(String id)
    {
        return flowTemplateMapper.selectFlowTemplateById(id);
    }

    /**
     * 查询流程节点列表
     * 
     * @param flowTemplate 流程节点
     * @return 流程节点
     */
    @Override
    public List<FlowTemplate> selectFlowTemplateList(FlowTemplate flowTemplate)
    {
        return flowTemplateMapper.selectFlowTemplateList(flowTemplate);
    }

    /**
     * 新增或者修改流程节点
     *
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public AjaxResult saveFlowTemplate(FlowTemplate flowTemplate)
    {

        // 节点顺序 和 key 不能重复
        if (flowTemplateMapper.isExitsKey(flowTemplate) > 0){
            return AjaxResult.error("节点key存在重复");
        }

        if (flowTemplateMapper.isExitsSort(flowTemplate) > 0){
            return AjaxResult.error("节点顺序存在重复");
        }

        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowTemplate.getId()))
        {
            // 修改
            flowTemplate.setUpdateBy(userId); // 更新人
            flowTemplate.setUpdateTime(curDate); // 更新时间
            flowTemplateMapper.updateFlowTemplate(flowTemplate);
        }
        else
        {
            // 新增
            flowTemplate.setId(StringUtils.getUUID()); // 主键
            flowTemplate.setDelFlag("0");
            flowTemplate.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowTemplate.setCreateBy(userId); // 创建人
            flowTemplate.setCreateTime(curDate); // 创建时间
            flowTemplate.setUpdateBy(userId); // 更新人
            flowTemplate.setUpdateTime(curDate); // 更新时间
            flowTemplateMapper.insertFlowTemplate(flowTemplate);
        }
        saveFlow(flowTemplate.getFlowOid()); // 设置节点上下顺序

        return AjaxResult.success("操作成功！",flowTemplate.getId());
    }


    /**
     * 新增或者修改流程节点
     *
     * @param flowTemplate 流程节点
     * @return 结果
     */
    public AjaxResult saveFlowTemplateNew(FlowTemplate flowTemplate)
    {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowTemplate.getId()))
        {
            // 修改
            flowTemplate.setUpdateBy(userId); // 更新人
            flowTemplate.setUpdateTime(curDate); // 更新时间
            flowTemplateMapper.updateFlowTemplate(flowTemplate);
        }
        else
        {
            // 新增
            flowTemplate.setId(StringUtils.getUUID()); // 主键
            flowTemplate.setDelFlag("0");
            flowTemplate.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowTemplate.setCreateBy(-2L); // 创建人
            flowTemplate.setCreateTime(curDate); // 创建时间
            flowTemplate.setUpdateBy(userId); // 更新人
            flowTemplate.setUpdateTime(curDate); // 更新时间
            flowTemplateMapper.insertFlowTemplate(flowTemplate);
        }

        return AjaxResult.success("操作成功！",flowTemplate.getId());
    }

    /**
     * 设置节点上下顺序
     * @param flowOid
     */
    public void saveFlow(String flowOid){
        if (StringUtils.isNotEmpty(flowOid))
        {
            FlowTemplate queryBo =new FlowTemplate();
            queryBo.setFlowOid(flowOid);
            List<FlowTemplate> resultList = this.selectFlowTemplateList(queryBo);

            String firstId = "-1";  // 第一个节点
            for (int i=0;i<resultList.size();i++)
            {
                String preNode = ""; // 上一个节点
                String nextNode = ""; // 下一个节点
                String returnNode = ""; // 退回节点
                FlowTemplate v = resultList.get(i);
                if (i == 0)
                {
                    preNode = "0";
                    returnNode = "0";

                    firstId = v.getId();  // 第一个节点
                }
                else
                {
                    preNode = resultList.get(i-1).getId();

                    // 根据退回num 查询
                    queryBo.setNodeOrder(v.getReturnNum());
                    List<FlowTemplate> returnList = this.selectFlowTemplateList(queryBo);
                    if (returnList.size() > 0)
                    {
                        returnNode = returnList.get(0).getId();
                    }
                    else
                    {
                        returnNode = firstId;
                    }

                }

                if (i == resultList.size() - 1)
                {
                    nextNode = "-1";
                }
                else
                {
                    nextNode = resultList.get(i+1).getId();
                }
                v.setPreviousNodeOid(preNode);
                v.setNextNodeOid(nextNode);
                v.setReturnNodeOid(returnNode);
                flowTemplateMapper.updateFlowTemplate(v);
            }
        }
    }

    /**
     * 批量删除流程节点
     * 
     * @param ids 需要删除的流程节点ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowTemplateByIds(String[] ids)
    {
        int count = flowTemplateMapper.deleteFlowTemplateByIds(ids);
        saveFlow(this.selectFlowTemplateById(ids[0]).getFlowOid()); // 设置节点上下顺序
        return AjaxResult.success(count);
    }

    /**
     * 删除流程节点信息
     * 
     * @param id 流程节点ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowTemplateById(String id)
    {
        int count = flowTemplateMapper.deleteFlowTemplateById(id);
        saveFlow(this.selectFlowTemplateById(id).getFlowOid()); // 设置节点上下顺序
        return AjaxResult.success(count);
    }
}
