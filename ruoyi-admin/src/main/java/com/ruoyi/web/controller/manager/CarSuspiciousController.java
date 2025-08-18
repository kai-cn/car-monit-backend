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
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 可疑车辆Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/suspicious")
public class CarSuspiciousController extends BaseController {

    @Autowired
    private ICarSuspiciousService carSuspiciousService;

    /**
     * 查询可疑车辆列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarSuspicious carSuspicious) {
        startPage();
        // carSuspicious.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        return getDataTable(list);
    }

    /**
     * 导出可疑车辆列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:export')")
    @Log(title = "可疑车辆", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarSuspicious carSuspicious) {
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        ExcelUtil<CarSuspicious> util = new ExcelUtil<CarSuspicious>(CarSuspicious.class);
        return util.exportExcel(list, "可疑车辆数据");
    }

    /**
     * 获取可疑车辆详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carSuspiciousService.selectCarSuspiciousById(id));
    }

    /**
     * 新增可疑车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:add')")
    @Log(title = "可疑车辆", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarSuspicious carSuspicious) {
        return carSuspiciousService.saveCarSuspicious(carSuspicious);
    }

    /**
     * 修改可疑车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:edit')")
    @Log(title = "可疑车辆", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarSuspicious carSuspicious) {
        return carSuspiciousService.saveCarSuspicious(carSuspicious);
    }

    /**
     * 删除可疑车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:remove')")
    @Log(title = "可疑车辆", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carSuspiciousService.deleteCarSuspiciousByIds(ids);
    }

}
