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
import com.ruoyi.base.domain.BaseOrgInfo;
import com.ruoyi.base.service.IBaseOrgInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 机构信息Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/orginfo")
public class BaseOrgInfoController extends BaseController {

    @Autowired
    private IBaseOrgInfoService baseOrgInfoService;

    /**
     * 查询机构信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:orginfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseOrgInfo baseOrgInfo) {
        startPage();
        // baseOrgInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseOrgInfo> list = baseOrgInfoService.selectBaseOrgInfoList(baseOrgInfo);
        return getDataTable(list);
    }

    /**
     * 导出机构信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:orginfo:export')")
    @Log(title = "机构信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseOrgInfo baseOrgInfo) {
        List<BaseOrgInfo> list = baseOrgInfoService.selectBaseOrgInfoList(baseOrgInfo);
        ExcelUtil<BaseOrgInfo> util = new ExcelUtil<BaseOrgInfo>(BaseOrgInfo.class);
        return util.exportExcel(list, "机构信息数据");
    }

    /**
     * 获取机构信息详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(baseOrgInfoService.selectBaseOrgInfoById(bigId));
    }

    /**
     * 新增机构信息
     */
    @PreAuthorize("@ss.hasPermi('base:orginfo:add')")
    @Log(title = "机构信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseOrgInfo baseOrgInfo) {
        return baseOrgInfoService.saveBaseOrgInfo(baseOrgInfo);
    }

    /**
     * 修改机构信息
     */
    @PreAuthorize("@ss.hasPermi('base:orginfo:edit')")
    @Log(title = "机构信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseOrgInfo baseOrgInfo) {
        return baseOrgInfoService.saveBaseOrgInfo(baseOrgInfo);
    }

    /**
     * 删除机构信息
     */
    @PreAuthorize("@ss.hasPermi('base:orginfo:remove')")
    @Log(title = "机构信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{bigIds}")
    public AjaxResult remove(@PathVariable String[] bigIds) {
        return baseOrgInfoService.deleteBaseOrgInfoByIds(bigIds);
    }

}
