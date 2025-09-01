package com.ruoyi.web.controller.base;

import java.util.Arrays;
import java.util.List;

import com.ruoyi.base.domain.OdsLwzxsfsjFeeGantryFusion01;
import com.ruoyi.base.service.IOdsLwzxsfsjFeeGantryFusion01Service;
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
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 交易流水Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/manager/feeGantry")
public class OdsLwzxsfsjFeeGantryFusion01Controller extends BaseController {

    @Autowired
    private IOdsLwzxsfsjFeeGantryFusion01Service odsLwzxsfsjFeeGantryFusion01Service;

    /**
     * 查询交易流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:01:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01) {
        startPage();
        // odsLwzxsfsjFeeGantryFusion01.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsLwzxsfsjFeeGantryFusion01> list = odsLwzxsfsjFeeGantryFusion01Service.selectOdsLwzxsfsjFeeGantryFusion01List(odsLwzxsfsjFeeGantryFusion01);
        return getDataTable(list);
    }

    /**
     * 导出交易流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:01:export')")
    @Log(title = "交易流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01) {
        List<OdsLwzxsfsjFeeGantryFusion01> list = odsLwzxsfsjFeeGantryFusion01Service.selectOdsLwzxsfsjFeeGantryFusion01List(odsLwzxsfsjFeeGantryFusion01);
        ExcelUtil<OdsLwzxsfsjFeeGantryFusion01> util = new ExcelUtil<OdsLwzxsfsjFeeGantryFusion01>(OdsLwzxsfsjFeeGantryFusion01.class);
        return util.exportExcel(list, "交易流水数据");
    }

    /**
     * 获取交易流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(odsLwzxsfsjFeeGantryFusion01Service.selectOdsLwzxsfsjFeeGantryFusion01ById(bigId));
    }

    /**
     * 新增交易流水
     */
    @PreAuthorize("@ss.hasPermi('manager:01:add')")
    @Log(title = "交易流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01) {
        return odsLwzxsfsjFeeGantryFusion01Service.saveOdsLwzxsfsjFeeGantryFusion01(odsLwzxsfsjFeeGantryFusion01);
    }

    /**
     * 修改交易流水
     */
    @PreAuthorize("@ss.hasPermi('manager:01:edit')")
    @Log(title = "交易流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01) {
        return odsLwzxsfsjFeeGantryFusion01Service.saveOdsLwzxsfsjFeeGantryFusion01(odsLwzxsfsjFeeGantryFusion01);
    }

    /**
     * 删除交易流水
     */
    @PreAuthorize("@ss.hasPermi('manager:01:remove')")
    @Log(title = "交易流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{bigIds}")
    public AjaxResult remove(@PathVariable String[] bigIds) {
        return odsLwzxsfsjFeeGantryFusion01Service.deleteOdsLwzxsfsjFeeGantryFusion01ByIds(bigIds);
    }

}
