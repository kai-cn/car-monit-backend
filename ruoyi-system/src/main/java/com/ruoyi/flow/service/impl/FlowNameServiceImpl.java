package com.ruoyi.flow.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysDept;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.flow.domain.FlowName;
import com.ruoyi.flow.domain.FlowTemplate;
import com.ruoyi.flow.mapper.FlowNameMapper;
import com.ruoyi.flow.service.IFlowNameService;
import com.ruoyi.flow.service.IFlowTemplateService;
import com.ruoyi.system.service.ISysDeptService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 流程名称Service业务层处理
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowNameServiceImpl implements IFlowNameService 
{
    @Autowired
    private FlowNameMapper flowNameMapper;

    @Autowired
    private IFlowTemplateService flowTemplateService;

    @Autowired
    private ISysDeptService deptService;



    /**
     * 查询流程名称
     * 
     * @param id 流程名称ID
     * @return 流程名称
     */
    @Override
    public FlowName selectFlowNameById(String id)
    {
        return flowNameMapper.selectFlowNameById(id);
    }

    /**
     * 查询流程名称列表
     * 
     * @param flowName 流程名称
     * @return 流程名称
     */
    @Override
    public List<FlowName> selectFlowNameList(FlowName flowName)
    {
        return flowNameMapper.selectFlowNameList(flowName);
    }

    /**
     * 新增或者修改流程名称
     *
     * @param flowName 流程名称
     * @return 结果
     */
    public AjaxResult saveFlowName(FlowName flowName)
    {

       /* // 新增
        if (StringUtils.isEmpty(flowName.getId())){
            flowName.setTenantId(SecurityUtils.getTenantId()); // 当前租户
        }*/


        if (flowNameMapper.isExitsKey(flowName) > 0){
            return AjaxResult.error("节点key存在重复");
        }

        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowName.getId()))
        {
            // 修改
            flowName.setUpdateBy(userId); // 更新人
            flowName.setUpdateTime(curDate); // 更新时间
            flowNameMapper.updateFlowName(flowName);
        }
        else
        {
            // 新增
            flowName.setId(StringUtils.getUUID()); // 主键
            flowName.setDelFlag("0");
            flowName.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowName.setCreateBy(-1L); // 创建人
            flowName.setCreateTime(curDate); // 创建时间
            flowName.setUpdateBy(userId); // 更新人
            flowName.setUpdateTime(curDate); // 更新时间
            flowNameMapper.insertFlowName(flowName);
        }
        return AjaxResult.success("操作成功！",flowName.getId());
    }






    /**
     * 批量删除流程名称
     * 
     * @param ids 需要删除的流程名称ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowNameByIds(String[] ids)
    {
        int count = flowNameMapper.deleteFlowNameByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除流程名称信息
     * 
     * @param id 流程名称ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowNameById(String id)
    {
        int count = flowNameMapper.deleteFlowNameById(id);
        return AjaxResult.success(count);
    }

    /**
     * 同步其他单位的工作流
     *
     * @param flowName 流程名称
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult tbFlow(FlowName flowName){

        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();

        // 先查询流程名称
        FlowName queryBO = new FlowName();
        queryBO.setCreateBy(-1L);
        List<FlowName> list =  flowNameMapper.selectFlowNameList(queryBO);

        // 查询要同步的单位
        SysDept queryBo = new SysDept();
        queryBo.setIsUint("1");
        List<SysDept> deptLit = deptService.selectDeptList(queryBo);
        for (int i=0;i<list.size();i++){
            FlowName tempFlowName = list.get(i);
            //查询自己的配置信息
            FlowTemplate queryFlowTemplate = new FlowTemplate();
            queryFlowTemplate.setFlowOid(tempFlowName.getId());
            List<FlowTemplate> flowTemplateList =flowTemplateService.selectFlowTemplateList(queryFlowTemplate);

            for (SysDept deptBo : deptLit) {
                // 判断是否已存在
                FlowName folwDeptBO = new FlowName();
                folwDeptBO.setTenantId(deptBo.getDeptId());
                folwDeptBO.setFlowKey(tempFlowName.getFlowKey());
                if (flowNameMapper.selectFlowNameList(folwDeptBO).size() == 0) {

                    // 新增 流程
                    FlowName addFlowName = new FlowName();
                    addFlowName.setFlowKey(tempFlowName.getFlowKey());
                    addFlowName.setFlowTitle(tempFlowName.getFlowTitle());
                    addFlowName.setFlowContext(tempFlowName.getFlowContext());
                    addFlowName.setBussName(tempFlowName.getBussName());
                    addFlowName.setSort(tempFlowName.getSort());

                    addFlowName.setId(StringUtils.getUUID()); // 主键
                    addFlowName.setDelFlag("0");
                    addFlowName.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
                    addFlowName.setCreateBy(userId); // 创建人
                    addFlowName.setCreateTime(curDate); // 创建时间
                    addFlowName.setUpdateBy(userId); // 更新人
                    addFlowName.setUpdateTime(curDate); // 更新时间
                    addFlowName.setTenantId(deptBo.getDeptId());
                    addFlowName.setFlowBusinessType("1");
                    flowNameMapper.insertFlowName(addFlowName);


                    for (FlowTemplate addFlowTemplate:flowTemplateList){
                        addFlowTemplate.setId(""); // 主键
                        addFlowTemplate.setFlowOid(addFlowName.getId()); // 流程key
                        addFlowTemplate.setNextNodeOid("");
                        addFlowTemplate.setPreviousNodeOid("");
                        flowTemplateService.saveFlowTemplateNew(addFlowTemplate);
                    }
                    flowTemplateService.saveFlow(addFlowName.getId()); // 设置节点上下顺序
                }
            }
        }
        return AjaxResult.success("同步成功！");
    }
}
