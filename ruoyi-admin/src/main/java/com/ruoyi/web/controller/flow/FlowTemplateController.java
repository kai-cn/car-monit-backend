package com.ruoyi.web.controller.flow;

import java.util.ArrayList;
import java.util.List;

import com.ruoyi.common.utils.CommonUtil;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.flow.domain.FlowTemplate;
import com.ruoyi.flow.service.IFlowTemplateService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 流程节点Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/flowtemplate")
public class FlowTemplateController extends BaseController
{
    @Autowired
    private IFlowTemplateService flowTemplateService;

    /**
     * 查询流程节点列表
     */
   // @PreAuthorize("@ss.hasPermi('flow:flowtemplate:list')")
    @GetMapping("/list")
    public TableDataInfo list(FlowTemplate flowTemplate)
    {
        startPage();
        List<FlowTemplate> list = flowTemplateService.selectFlowTemplateList(flowTemplate);
        return getDataTable(list);
    }

    /**
     * 获取流程
     * @param flowTemplate
     * @return
     */
    @GetMapping("/flowlist")
    public AjaxResult flowlist(FlowTemplate flowTemplate)
    {
        List<FlowTemplate> rtnlist = new ArrayList<>();
        if(CommonUtil.isNotBlank(flowTemplate.getFlowOid())){
            List<FlowTemplate> list = flowTemplateService.selectFlowTemplateList(flowTemplate);
            FlowTemplate firstbo = new FlowTemplate();
            firstbo.setId("-1");
            firstbo.setNodeOrder(-1);
            firstbo.setNodeKey("tj");
            firstbo.setNodeName("申请人提交");
            rtnlist.add(firstbo);

            for (FlowTemplate rtnvo:list){
                rtnlist.add(rtnvo);
            }
        }

        return AjaxResult.success(rtnlist);
    }


    /**
     * 导出流程节点列表
     */
   // @PreAuthorize("@ss.hasPermi('flow:flowtemplate:export')")
    @Log(title = "流程节点", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowTemplate flowTemplate)
    {
        List<FlowTemplate> list = flowTemplateService.selectFlowTemplateList(flowTemplate);
        ExcelUtil<FlowTemplate> util = new ExcelUtil<FlowTemplate>(FlowTemplate.class);
        return util.exportExcel(list, "流程节点数据");
    }

    /**
     * 获取流程节点详细信息
     */
   // @PreAuthorize("@ss.hasPermi('flow:flowtemplate:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowTemplateService.selectFlowTemplateById(id));
    }

    /**
     * 新增流程节点
     */
    // @PreAuthorize("@ss.hasPermi('flow:flowtemplate:add')")
    @Log(title = "流程节点", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowTemplate flowTemplate)
    {
        return flowTemplateService.saveFlowTemplate(flowTemplate);
    }

    /**
     * 修改流程节点
     */
    //@PreAuthorize("@ss.hasPermi('flow:flowtemplate:edit')")
    @Log(title = "流程节点", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowTemplate flowTemplate)
    {
        return flowTemplateService.saveFlowTemplate(flowTemplate);
    }

    /**
     * 删除流程节点
     */
    //@PreAuthorize("@ss.hasPermi('flow:flowtemplate:remove')")
    @Log(title = "流程节点", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowTemplateService.deleteFlowTemplateByIds(ids);
    }
}
