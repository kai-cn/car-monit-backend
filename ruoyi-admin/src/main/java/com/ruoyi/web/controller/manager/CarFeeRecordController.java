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
import com.ruoyi.manager.domain.CarFeeRecord;
import com.ruoyi.manager.service.ICarFeeRecordService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 收费流水Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/feerecord")
public class CarFeeRecordController extends BaseController {

    @Autowired
    private ICarFeeRecordService carFeeRecordService;

    /**
     * 查询收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:feerecord:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarFeeRecord carFeeRecord) {
        startPage();
        // carFeeRecord.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarFeeRecord> list = carFeeRecordService.selectCarFeeRecordList(carFeeRecord);
        return getDataTable(list);
    }

    /**
     * 导出收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:feerecord:export')")
    @Log(title = "收费流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarFeeRecord carFeeRecord) {
        List<CarFeeRecord> list = carFeeRecordService.selectCarFeeRecordList(carFeeRecord);
        ExcelUtil<CarFeeRecord> util = new ExcelUtil<CarFeeRecord>(CarFeeRecord.class);
        return util.exportExcel(list, "收费流水数据");
    }

    /**
     * 获取收费流水详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carFeeRecordService.selectCarFeeRecordById(id));
    }

    /**
     * 新增收费流水
     */
    @PreAuthorize("@ss.hasPermi('manager:feerecord:add')")
    @Log(title = "收费流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarFeeRecord carFeeRecord) {
        return carFeeRecordService.saveCarFeeRecord(carFeeRecord);
    }

    /**
     * 修改收费流水
     */
    @PreAuthorize("@ss.hasPermi('manager:feerecord:edit')")
    @Log(title = "收费流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarFeeRecord carFeeRecord) {
        return carFeeRecordService.saveCarFeeRecord(carFeeRecord);
    }

    /**
     * 删除收费流水
     */
    @PreAuthorize("@ss.hasPermi('manager:feerecord:remove')")
    @Log(title = "收费流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carFeeRecordService.deleteCarFeeRecordByIds(ids);
    }

}
