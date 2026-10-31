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
import com.ruoyi.manager.domain.CarSuspiciousBack;
import com.ruoyi.manager.service.ICarSuspiciousBackService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 可疑车辆备份Controller
 *
 * @author ruoyi
 * @date 2026-10-31
 */
@RestController
@RequestMapping("/manager/carsuspiciousback")
public class CarSuspiciousBackController extends BaseController {

    @Autowired
    private ICarSuspiciousBackService carSuspiciousBackService;

    /**
     * 查询可疑车辆备份列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carsuspiciousback:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarSuspiciousBack carSuspiciousBack) {
        startPage();
        // carSuspiciousBack.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarSuspiciousBack> list = carSuspiciousBackService.selectCarSuspiciousBackList(carSuspiciousBack);
        return getDataTable(list);
    }

    /**
     * 导出可疑车辆备份列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carsuspiciousback:export')")
    @Log(title = "可疑车辆备份", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarSuspiciousBack carSuspiciousBack) {
        List<CarSuspiciousBack> list = carSuspiciousBackService.selectCarSuspiciousBackList(carSuspiciousBack);
        ExcelUtil<CarSuspiciousBack> util = new ExcelUtil<CarSuspiciousBack>(CarSuspiciousBack.class);
        return util.exportExcel(list, "可疑车辆备份数据");
    }

    /**
     * 获取可疑车辆备份详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carSuspiciousBackService.selectCarSuspiciousBackById(id));
    }

    /**
     * 新增可疑车辆备份
     */
    @PreAuthorize("@ss.hasPermi('manager:carsuspiciousback:add')")
    @Log(title = "可疑车辆备份", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarSuspiciousBack carSuspiciousBack) {
        return carSuspiciousBackService.saveCarSuspiciousBack(carSuspiciousBack);
    }

    /**
     * 修改可疑车辆备份
     */
    @PreAuthorize("@ss.hasPermi('manager:carsuspiciousback:edit')")
    @Log(title = "可疑车辆备份", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarSuspiciousBack carSuspiciousBack) {
        return carSuspiciousBackService.saveCarSuspiciousBack(carSuspiciousBack);
    }

    /**
     * 删除可疑车辆备份
     */
    @PreAuthorize("@ss.hasPermi('manager:carsuspiciousback:remove')")
    @Log(title = "可疑车辆备份", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carSuspiciousBackService.deleteCarSuspiciousBackByIds(ids);
    }

}
