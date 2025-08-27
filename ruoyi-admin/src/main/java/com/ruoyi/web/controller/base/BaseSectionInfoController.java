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
import com.ruoyi.base.domain.BaseSectionInfo;
import com.ruoyi.base.service.IBaseSectionInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 路段信息Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/sectioninfo")
public class BaseSectionInfoController extends BaseController {

    @Autowired
    private IBaseSectionInfoService baseSectionInfoService;

    /**
     * 查询路段信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:sectioninfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseSectionInfo baseSectionInfo) {
        startPage();
        // baseSectionInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseSectionInfo> list = baseSectionInfoService.selectBaseSectionInfoList(baseSectionInfo);
        return getDataTable(list);
    }

    /**
     * 导出路段信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:sectioninfo:export')")
    @Log(title = "路段信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseSectionInfo baseSectionInfo) {
        List<BaseSectionInfo> list = baseSectionInfoService.selectBaseSectionInfoList(baseSectionInfo);
        ExcelUtil<BaseSectionInfo> util = new ExcelUtil<BaseSectionInfo>(BaseSectionInfo.class);
        return util.exportExcel(list, "路段信息数据");
    }

    /**
     * 获取路段信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(baseSectionInfoService.selectBaseSectionInfoById(id));
    }

    /**
     * 新增路段信息
     */
    @PreAuthorize("@ss.hasPermi('base:sectioninfo:add')")
    @Log(title = "路段信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseSectionInfo baseSectionInfo) {
        return baseSectionInfoService.saveBaseSectionInfo(baseSectionInfo);
    }

    /**
     * 修改路段信息
     */
    @PreAuthorize("@ss.hasPermi('base:sectioninfo:edit')")
    @Log(title = "路段信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseSectionInfo baseSectionInfo) {
        return baseSectionInfoService.saveBaseSectionInfo(baseSectionInfo);
    }

    /**
     * 删除路段信息
     */
    @PreAuthorize("@ss.hasPermi('base:sectioninfo:remove')")
    @Log(title = "路段信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return baseSectionInfoService.deleteBaseSectionInfoByIds(ids);
    }

}
