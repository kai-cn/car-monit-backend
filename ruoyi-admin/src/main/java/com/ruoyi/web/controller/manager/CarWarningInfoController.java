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
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.service.ICarWarningInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 预警车辆Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/carwarning")
public class CarWarningInfoController extends BaseController {

    @Autowired
    private ICarWarningInfoService carWarningInfoService;

    /**
     * 查询预警车辆列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarWarningInfo carWarningInfo) {
        startPage();
        // carWarningInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarWarningInfo> list = carWarningInfoService.selectCarWarningInfoList(carWarningInfo);
        return getDataTable(list);
    }

    /**
     * 导出预警车辆列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:export')")
    @Log(title = "预警车辆", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarWarningInfo carWarningInfo) {
        List<CarWarningInfo> list = carWarningInfoService.selectCarWarningInfoList(carWarningInfo);
        ExcelUtil<CarWarningInfo> util = new ExcelUtil<CarWarningInfo>(CarWarningInfo.class);
        return util.exportExcel(list, "预警车辆数据");
    }

    /**
     * 获取预警车辆详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carWarningInfoService.selectCarWarningInfoById(id));
    }

    /**
     * 新增预警车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:add')")
    @Log(title = "预警车辆", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarWarningInfo carWarningInfo) {
        return carWarningInfoService.saveCarWarningInfo(carWarningInfo);
    }

    /**
     * 修改预警车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:edit')")
    @Log(title = "预警车辆", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarWarningInfo carWarningInfo) {
        return carWarningInfoService.saveCarWarningInfo(carWarningInfo);
    }

    /**
     * 删除预警车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:remove')")
    @Log(title = "预警车辆", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carWarningInfoService.deleteCarWarningInfoByIds(ids);
    }

}
