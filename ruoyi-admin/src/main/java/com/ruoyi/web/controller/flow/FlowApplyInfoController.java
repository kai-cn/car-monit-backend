package com.ruoyi.web.controller.flow;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.flow.domain.FlowApplyInfo;
import com.ruoyi.flow.service.IFlowApplyInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 我的申请Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/applyinfo")
public class FlowApplyInfoController extends BaseController
{
    @Autowired
    private IFlowApplyInfoService flowApplyInfoService;

    /**
     * 查询我的申请列表
     */
    @GetMapping("/list")
    public TableDataInfo list(FlowApplyInfo flowApplyInfo)
    {
        startPage();
        flowApplyInfo.setCreateBy(SecurityUtils.getUserId()); // 查询我的申请
        List<FlowApplyInfo> list = flowApplyInfoService.selectFlowApplyInfoList(flowApplyInfo);
        return getDataTable(list);
    }


    /**
     * 查询全部申请
     */
    @PreAuthorize("@ss.hasPermi('flow:applyinfo:list')")
    @GetMapping("/listAll")
    public TableDataInfo listAll(FlowApplyInfo flowApplyInfo)
    {
        startPage();
        List<FlowApplyInfo> list = flowApplyInfoService.selectFlowApplyInfoList(flowApplyInfo);
        return getDataTable(list);
    }

    /**
     * 导出我的申请列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:applyinfo:export')")
    @Log(title = "我的申请", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowApplyInfo flowApplyInfo)
    {
        List<FlowApplyInfo> list = flowApplyInfoService.selectFlowApplyInfoList(flowApplyInfo);
        ExcelUtil<FlowApplyInfo> util = new ExcelUtil<FlowApplyInfo>(FlowApplyInfo.class);
        return util.exportExcel(list, "我的申请数据");
    }

    /**
     * 获取我的申请详细信息
     */
    // @PreAuthorize("@ss.hasPermi('flow:applyinfo:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowApplyInfoService.selectFlowApplyInfoById(id));
    }

    /**
     * 新增我的申请
     */
    // @PreAuthorize("@ss.hasPermi('flow:applyinfo:add')")
    @Log(title = "我的申请", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowApplyInfo flowApplyInfo)
    {
        return flowApplyInfoService.saveFlowApplyInfo(flowApplyInfo);
    }

    /**
     * 修改我的申请
     */
    // @PreAuthorize("@ss.hasPermi('flow:applyinfo:edit')")
    @Log(title = "我的申请", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowApplyInfo flowApplyInfo)
    {
        return flowApplyInfoService.saveFlowApplyInfo(flowApplyInfo);
    }

    /**
     * 删除我的申请
     */
    // @PreAuthorize("@ss.hasPermi('flow:applyinfo:remove')")
    @Log(title = "我的申请", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowApplyInfoService.deleteFlowApplyInfoByIds(ids);
    }
}
