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
import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.service.IOdsSzdnSectionService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 路段信息Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/section")
public class OdsSzdnSectionController extends BaseController {

    @Autowired
    private IOdsSzdnSectionService odsSzdnSectionService;

    /**
     * 查询路段信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:section:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnSection odsSzdnSection) {
        startPage();
        // odsSzdnSection.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsSzdnSection> list = odsSzdnSectionService.selectOdsSzdnSectionList(odsSzdnSection);
        return getDataTable(list);
    }


    /**
     * 查询路段信息列表：选择弹窗
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(OdsSzdnSection odsSzdnSection) {
        startPage();
        List<OdsSzdnSection> list = odsSzdnSectionService.selectOdsSzdnSectionList(odsSzdnSection);
        return getDataTable(list);
    }


    /**
     * 导出路段信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:section:export')")
    @Log(title = "路段信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(OdsSzdnSection odsSzdnSection) {
        List<OdsSzdnSection> list = odsSzdnSectionService.selectOdsSzdnSectionList(odsSzdnSection);
        ExcelUtil<OdsSzdnSection> util = new ExcelUtil<OdsSzdnSection>(OdsSzdnSection.class);
        return util.exportExcel(list, "路段信息数据");
    }

    /**
     * 获取路段信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(odsSzdnSectionService.selectOdsSzdnSectionById(id));
    }

    /**
     * 新增路段信息
     */
    @PreAuthorize("@ss.hasPermi('base:section:add')")
    @Log(title = "路段信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody OdsSzdnSection odsSzdnSection) {
        return odsSzdnSectionService.saveOdsSzdnSection(odsSzdnSection);
    }

    /**
     * 修改路段信息
     */
    @PreAuthorize("@ss.hasPermi('base:section:edit')")
    @Log(title = "路段信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody OdsSzdnSection odsSzdnSection) {
        return odsSzdnSectionService.saveOdsSzdnSection(odsSzdnSection);
    }

    /**
     * 删除路段信息
     */
    @PreAuthorize("@ss.hasPermi('base:section:remove')")
    @Log(title = "路段信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return odsSzdnSectionService.deleteOdsSzdnSectionByIds(ids);
    }

}
