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
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 车辆信息Controller
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@RestController
@RequestMapping("/base/geometry")
public class GeometryController extends BaseController {

    @Autowired
    private IGeometryService geometryService;

    /**
     * 查询车辆信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:list')")
    @GetMapping("/list")
    public TableDataInfo list(Geometry geometry) {
        startPage();
        // geometry.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<Geometry> list = geometryService.selectGeometryList(geometry);
        return getDataTable(list);
    }

    /**
     * 导出车辆信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:export')")
    @Log(title = "车辆信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(Geometry geometry) {
        List<Geometry> list = geometryService.selectGeometryList(geometry);
        ExcelUtil<Geometry> util = new ExcelUtil<Geometry>(Geometry.class);
        return util.exportExcel(list, "车辆信息数据");
    }

    /**
     * 获取车辆信息详细信息
     */
    @GetMapping(value = "/{ID}")
    public AjaxResult getInfo(@PathVariable("ID") Integer ID) {
        return AjaxResult.success(geometryService.selectGeometryById(ID));
    }

    /**
     * 新增车辆信息
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:add')")
    @Log(title = "车辆信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody Geometry geometry) {
        return geometryService.saveGeometry(geometry);
    }

    /**
     * 修改车辆信息
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:edit')")
    @Log(title = "车辆信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody Geometry geometry) {
        return geometryService.saveGeometry(geometry);
    }

    /**
     * 删除车辆信息
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:remove')")
    @Log(title = "车辆信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{IDs}")
    public AjaxResult remove(@PathVariable Integer[] IDs) {
        return geometryService.deleteGeometryByIds(IDs);
    }

}
