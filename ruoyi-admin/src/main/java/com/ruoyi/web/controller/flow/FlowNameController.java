package com.ruoyi.web.controller.flow;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.flow.domain.FlowName;
import com.ruoyi.flow.service.IFlowNameService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 流程名称Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/flowname")
public class FlowNameController extends BaseController
{
    @Autowired
    private IFlowNameService flowNameService;

    /**
     * 查询流程名称列表  -- 管理员
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:list')")
    @GetMapping("/list")
    public TableDataInfo list(FlowName flowName)
    {
        startPage();
        List<FlowName> list = flowNameService.selectFlowNameList(flowName);
        return getDataTable(list);
    }


    /**
     * 查询流程名称列表  -- 单位查询自己的
     */
    @GetMapping("/listQuery")
    public TableDataInfo listQuery(FlowName flowName)
    {
        startPage();
        flowName.setTenantId(SecurityUtils.getTenantId());  // 查询单位自己的流程
        List<FlowName> list = flowNameService.selectFlowNameList(flowName);
        return getDataTable(list);
    }


    /**
     * 导出流程名称列表
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:export')")
    @Log(title = "流程名称", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowName flowName)
    {
        List<FlowName> list = flowNameService.selectFlowNameList(flowName);
        ExcelUtil<FlowName> util = new ExcelUtil<FlowName>(FlowName.class);
        return util.exportExcel(list, "流程名称数据");
    }

    /**
     * 获取流程名称详细信息
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowNameService.selectFlowNameById(id));
    }

    /**
     * 新增流程名称
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:add')")
    @Log(title = "流程名称", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowName flowName)
    {
        return flowNameService.saveFlowName(flowName);
    }

    /**
     * 修改流程名称
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:edit')")
    @Log(title = "流程名称", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowName flowName)
    {
        return flowNameService.saveFlowName(flowName);
    }

    /**
     * 删除流程名称
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:remove')")
    @Log(title = "流程名称", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowNameService.deleteFlowNameByIds(ids);
    }


    /**
     * 同步其他单位的工作流
     */
    @PreAuthorize("@ss.hasPermi('flow:flowname:edit')")
    @Log(title = "同步其他单位的工作流", businessType = BusinessType.UPDATE)
    @PostMapping("/tbFlow")
    public AjaxResult tbFlow(@RequestBody FlowName flowName)
    {
        return flowNameService.tbFlow(flowName);
    }

}
