package com.ruoyi.web.controller.base;

import java.util.Arrays;
import java.util.List;
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
import com.ruoyi.base.domain.BaseGantrySnapshotFlow;
import com.ruoyi.base.service.IBaseGantrySnapshotFlowService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 门架抓拍流水Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/gantrysnapshotflow")
public class BaseGantrySnapshotFlowController extends BaseController {

    @Autowired
    private IBaseGantrySnapshotFlowService baseGantrySnapshotFlowService;

    /**
     * 查询门架抓拍流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:gantrysnapshotflow:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseGantrySnapshotFlow baseGantrySnapshotFlow) {
        startPage();
        // baseGantrySnapshotFlow.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseGantrySnapshotFlow> list = baseGantrySnapshotFlowService.selectBaseGantrySnapshotFlowList(baseGantrySnapshotFlow);
        return getDataTable(list);
    }

    /**
     * 导出门架抓拍流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:gantrysnapshotflow:export')")
    @Log(title = "门架抓拍流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseGantrySnapshotFlow baseGantrySnapshotFlow) {
        List<BaseGantrySnapshotFlow> list = baseGantrySnapshotFlowService.selectBaseGantrySnapshotFlowList(baseGantrySnapshotFlow);
        ExcelUtil<BaseGantrySnapshotFlow> util = new ExcelUtil<BaseGantrySnapshotFlow>(BaseGantrySnapshotFlow.class);
        return util.exportExcel(list, "门架抓拍流水数据");
    }

    /**
     * 获取门架抓拍流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(baseGantrySnapshotFlowService.selectBaseGantrySnapshotFlowById(bigId));
    }

    /**
     * 新增门架抓拍流水
     */
    @PreAuthorize("@ss.hasPermi('base:gantrysnapshotflow:add')")
    @Log(title = "门架抓拍流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseGantrySnapshotFlow baseGantrySnapshotFlow) {
        return baseGantrySnapshotFlowService.saveBaseGantrySnapshotFlow(baseGantrySnapshotFlow);
    }

    /**
     * 修改门架抓拍流水
     */
    @PreAuthorize("@ss.hasPermi('base:gantrysnapshotflow:edit')")
    @Log(title = "门架抓拍流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseGantrySnapshotFlow baseGantrySnapshotFlow) {
        return baseGantrySnapshotFlowService.saveBaseGantrySnapshotFlow(baseGantrySnapshotFlow);
    }

    /**
     * 删除门架抓拍流水
     */
    @PreAuthorize("@ss.hasPermi('base:gantrysnapshotflow:remove')")
    @Log(title = "门架抓拍流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{bigIds}")
    public AjaxResult remove(@PathVariable String[] bigIds) {
        return baseGantrySnapshotFlowService.deleteBaseGantrySnapshotFlowByIds(bigIds);
    }

}
