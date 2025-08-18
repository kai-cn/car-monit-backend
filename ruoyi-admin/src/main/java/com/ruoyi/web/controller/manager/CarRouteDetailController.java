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
import com.ruoyi.manager.domain.CarRouteDetail;
import com.ruoyi.manager.service.ICarRouteDetailService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 常用路线明细Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/routedetail")
public class CarRouteDetailController extends BaseController {

    @Autowired
    private ICarRouteDetailService carRouteDetailService;

    /**
     * 查询常用路线明细列表
     */
    @PreAuthorize("@ss.hasPermi('manager:routedetail:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarRouteDetail carRouteDetail) {
        startPage();
        // carRouteDetail.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarRouteDetail> list = carRouteDetailService.selectCarRouteDetailList(carRouteDetail);
        return getDataTable(list);
    }

    /**
     * 导出常用路线明细列表
     */
    @PreAuthorize("@ss.hasPermi('manager:routedetail:export')")
    @Log(title = "常用路线明细", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarRouteDetail carRouteDetail) {
        List<CarRouteDetail> list = carRouteDetailService.selectCarRouteDetailList(carRouteDetail);
        ExcelUtil<CarRouteDetail> util = new ExcelUtil<CarRouteDetail>(CarRouteDetail.class);
        return util.exportExcel(list, "常用路线明细数据");
    }

    /**
     * 获取常用路线明细详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carRouteDetailService.selectCarRouteDetailById(id));
    }

    /**
     * 新增常用路线明细
     */
    @PreAuthorize("@ss.hasPermi('manager:routedetail:add')")
    @Log(title = "常用路线明细", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarRouteDetail carRouteDetail) {
        return carRouteDetailService.saveCarRouteDetail(carRouteDetail);
    }

    /**
     * 修改常用路线明细
     */
    @PreAuthorize("@ss.hasPermi('manager:routedetail:edit')")
    @Log(title = "常用路线明细", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarRouteDetail carRouteDetail) {
        return carRouteDetailService.saveCarRouteDetail(carRouteDetail);
    }

    /**
     * 删除常用路线明细
     */
    @PreAuthorize("@ss.hasPermi('manager:routedetail:remove')")
    @Log(title = "常用路线明细", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carRouteDetailService.deleteCarRouteDetailByIds(ids);
    }

}
