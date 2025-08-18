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
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 异常车辆流水Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/exceptrecord")
public class CarExceptRecordController extends BaseController {

    @Autowired
    private ICarExceptRecordService carExceptRecordService;

    /**
     * 查询异常车辆流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:exceptrecord:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarExceptRecord carExceptRecord) {
        startPage();
        // carExceptRecord.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        return getDataTable(list);
    }

    /**
     * 导出异常车辆流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:exceptrecord:export')")
    @Log(title = "异常车辆流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarExceptRecord carExceptRecord) {
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        ExcelUtil<CarExceptRecord> util = new ExcelUtil<CarExceptRecord>(CarExceptRecord.class);
        return util.exportExcel(list, "异常车辆流水数据");
    }

    /**
     * 获取异常车辆流水详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carExceptRecordService.selectCarExceptRecordById(id));
    }

    /**
     * 新增异常车辆流水
     */
    @PreAuthorize("@ss.hasPermi('manager:exceptrecord:add')")
    @Log(title = "异常车辆流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarExceptRecord carExceptRecord) {
        return carExceptRecordService.saveCarExceptRecord(carExceptRecord);
    }

    /**
     * 修改异常车辆流水
     */
    @PreAuthorize("@ss.hasPermi('manager:exceptrecord:edit')")
    @Log(title = "异常车辆流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarExceptRecord carExceptRecord) {
        return carExceptRecordService.saveCarExceptRecord(carExceptRecord);
    }

    /**
     * 删除异常车辆流水
     */
    @PreAuthorize("@ss.hasPermi('manager:exceptrecord:remove')")
    @Log(title = "异常车辆流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carExceptRecordService.deleteCarExceptRecordByIds(ids);
    }

}
