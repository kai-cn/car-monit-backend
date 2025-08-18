package com.ruoyi.web.controller.manager;

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
import com.ruoyi.manager.domain.CarSplitRecord;
import com.ruoyi.manager.service.ICarSplitRecordService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 拆分流水Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/splitrecord")
public class CarSplitRecordController extends BaseController {

    @Autowired
    private ICarSplitRecordService carSplitRecordService;

    /**
     * 查询拆分流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:splitrecord:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarSplitRecord carSplitRecord) {
        startPage();
        // carSplitRecord.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarSplitRecord> list = carSplitRecordService.selectCarSplitRecordList(carSplitRecord);
        return getDataTable(list);
    }

    /**
     * 导出拆分流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:splitrecord:export')")
    @Log(title = "拆分流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarSplitRecord carSplitRecord) {
        List<CarSplitRecord> list = carSplitRecordService.selectCarSplitRecordList(carSplitRecord);
        ExcelUtil<CarSplitRecord> util = new ExcelUtil<CarSplitRecord>(CarSplitRecord.class);
        return util.exportExcel(list, "拆分流水数据");
    }

    /**
     * 获取拆分流水详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carSplitRecordService.selectCarSplitRecordById(id));
    }

    /**
     * 新增拆分流水
     */
    @PreAuthorize("@ss.hasPermi('manager:splitrecord:add')")
    @Log(title = "拆分流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarSplitRecord carSplitRecord) {
        return carSplitRecordService.saveCarSplitRecord(carSplitRecord);
    }

    /**
     * 修改拆分流水
     */
    @PreAuthorize("@ss.hasPermi('manager:splitrecord:edit')")
    @Log(title = "拆分流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarSplitRecord carSplitRecord) {
        return carSplitRecordService.saveCarSplitRecord(carSplitRecord);
    }

    /**
     * 删除拆分流水
     */
    @PreAuthorize("@ss.hasPermi('manager:splitrecord:remove')")
    @Log(title = "拆分流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carSplitRecordService.deleteCarSplitRecordByIds(ids);
    }

}
