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
import com.ruoyi.base.domain.OdsSzdnGantry;
import com.ruoyi.base.service.IOdsSzdnGantryService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 门架信息Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/gantry")
public class OdsSzdnGantryController extends BaseController {

    @Autowired
    private IOdsSzdnGantryService odsSzdnGantryService;

    /**
     * 查询门架信息列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnGantry odsSzdnGantry) {
        startPage();
        // odsSzdnGantry.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsSzdnGantry> list = odsSzdnGantryService.selectOdsSzdnGantryList(odsSzdnGantry);
        return getDataTable(list);
    }

    /**
     * 查询门架信息列表:选择门架弹窗
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(OdsSzdnGantry odsSzdnGantry) {
        startPage();
        List<OdsSzdnGantry> list = odsSzdnGantryService.selectOdsSzdnGantryList(odsSzdnGantry);
        return getDataTable(list);
    }


    /**
     * 导出门架信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:export')")
    @Log(title = "门架信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(OdsSzdnGantry odsSzdnGantry) {
        List<OdsSzdnGantry> list = odsSzdnGantryService.selectOdsSzdnGantryList(odsSzdnGantry);
        ExcelUtil<OdsSzdnGantry> util = new ExcelUtil<OdsSzdnGantry>(OdsSzdnGantry.class);
        return util.exportExcel(list, "门架信息数据");
    }

    /**
     * 获取门架信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(odsSzdnGantryService.selectOdsSzdnGantryById(id));
    }

    /**
     * 新增门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:add')")
    @Log(title = "门架信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody OdsSzdnGantry odsSzdnGantry) {
        return odsSzdnGantryService.saveOdsSzdnGantry(odsSzdnGantry);
    }

    /**
     * 修改门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:edit')")
    @Log(title = "门架信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody OdsSzdnGantry odsSzdnGantry) {
        return odsSzdnGantryService.saveOdsSzdnGantry(odsSzdnGantry);
    }

    /**
     * 删除门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:remove')")
    @Log(title = "门架信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return odsSzdnGantryService.deleteOdsSzdnGantryByIds(ids);
    }

}
