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
import com.ruoyi.manager.domain.CarWhiteInfo;
import com.ruoyi.manager.service.ICarWhiteInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 车俩白名单Controller
 *
 * @author ruoyi
 * @date 2025-09-12
 */
@RestController
@RequestMapping("/manager/whiteinfo")
public class CarWhiteInfoController extends BaseController {

    @Autowired
    private ICarWhiteInfoService carWhiteInfoService;

    /**
     * 查询车俩白名单列表
     */
    @PreAuthorize("@ss.hasPermi('manager:whiteinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarWhiteInfo carWhiteInfo) {
        startPage();
        // carWhiteInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarWhiteInfo> list = carWhiteInfoService.selectCarWhiteInfoList(carWhiteInfo);
        return getDataTable(list);
    }

    /**
     * 导出车俩白名单列表
     */
    @PreAuthorize("@ss.hasPermi('manager:whiteinfo:export')")
    @Log(title = "车俩白名单", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarWhiteInfo carWhiteInfo) {
        List<CarWhiteInfo> list = carWhiteInfoService.selectCarWhiteInfoList(carWhiteInfo);
        ExcelUtil<CarWhiteInfo> util = new ExcelUtil<CarWhiteInfo>(CarWhiteInfo.class);
        return util.exportExcel(list, "车俩白名单数据");
    }

    /**
     * 获取车俩白名单详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carWhiteInfoService.selectCarWhiteInfoById(id));
    }

    /**
     * 新增车俩白名单
     */
    @PreAuthorize("@ss.hasPermi('manager:whiteinfo:add')")
    @Log(title = "车俩白名单", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarWhiteInfo carWhiteInfo) {
        return carWhiteInfoService.saveCarWhiteInfo(carWhiteInfo);
    }

    /**
     * 修改车俩白名单
     */
    @PreAuthorize("@ss.hasPermi('manager:whiteinfo:edit')")
    @Log(title = "车俩白名单", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarWhiteInfo carWhiteInfo) {
        return carWhiteInfoService.saveCarWhiteInfo(carWhiteInfo);
    }

    /**
     * 删除车俩白名单
     */
    @PreAuthorize("@ss.hasPermi('manager:whiteinfo:remove')")
    @Log(title = "车俩白名单", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carWhiteInfoService.deleteCarWhiteInfoByIds(ids);
    }

}
