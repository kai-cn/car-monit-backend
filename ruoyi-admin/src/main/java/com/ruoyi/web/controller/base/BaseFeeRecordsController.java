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
import com.ruoyi.base.domain.BaseFeeRecords;
import com.ruoyi.base.service.IBaseFeeRecordsService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 基础-收费流水Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/feerecords")
public class BaseFeeRecordsController extends BaseController {

    @Autowired
    private IBaseFeeRecordsService baseFeeRecordsService;

    /**
     * 查询基础-收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseFeeRecords baseFeeRecords) {
        startPage();
        // baseFeeRecords.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseFeeRecords> list = baseFeeRecordsService.selectBaseFeeRecordsList(baseFeeRecords);
        return getDataTable(list);
    }

    /**
     * 导出基础-收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:export')")
    @Log(title = "基础-收费流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseFeeRecords baseFeeRecords) {
        List<BaseFeeRecords> list = baseFeeRecordsService.selectBaseFeeRecordsList(baseFeeRecords);
        ExcelUtil<BaseFeeRecords> util = new ExcelUtil<BaseFeeRecords>(BaseFeeRecords.class);
        return util.exportExcel(list, "基础-收费流水数据");
    }

    /**
     * 获取基础-收费流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(baseFeeRecordsService.selectBaseFeeRecordsById(bigId));
    }

    /**
     * 新增基础-收费流水
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:add')")
    @Log(title = "基础-收费流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseFeeRecords baseFeeRecords) {
        return baseFeeRecordsService.saveBaseFeeRecords(baseFeeRecords);
    }

    /**
     * 修改基础-收费流水
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:edit')")
    @Log(title = "基础-收费流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseFeeRecords baseFeeRecords) {
        return baseFeeRecordsService.saveBaseFeeRecords(baseFeeRecords);
    }

    /**
     * 删除基础-收费流水
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:remove')")
    @Log(title = "基础-收费流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{bigIds}")
    public AjaxResult remove(@PathVariable String[] bigIds) {
        return baseFeeRecordsService.deleteBaseFeeRecordsByIds(bigIds);
    }

}
