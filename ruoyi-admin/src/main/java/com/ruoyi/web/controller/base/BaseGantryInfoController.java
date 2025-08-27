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
import com.ruoyi.base.domain.BaseGantryInfo;
import com.ruoyi.base.service.IBaseGantryInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 门架信息Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/gantryinfo")
public class BaseGantryInfoController extends BaseController {

    @Autowired
    private IBaseGantryInfoService baseGantryInfoService;

    /**
     * 查询门架信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:gantryinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseGantryInfo baseGantryInfo) {
        startPage();
        // baseGantryInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseGantryInfo> list = baseGantryInfoService.selectBaseGantryInfoList(baseGantryInfo);
        return getDataTable(list);
    }

    /**
     * 导出门架信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:gantryinfo:export')")
    @Log(title = "门架信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseGantryInfo baseGantryInfo) {
        List<BaseGantryInfo> list = baseGantryInfoService.selectBaseGantryInfoList(baseGantryInfo);
        ExcelUtil<BaseGantryInfo> util = new ExcelUtil<BaseGantryInfo>(BaseGantryInfo.class);
        return util.exportExcel(list, "门架信息数据");
    }

    /**
     * 获取门架信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(baseGantryInfoService.selectBaseGantryInfoById(id));
    }

    /**
     * 新增门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantryinfo:add')")
    @Log(title = "门架信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseGantryInfo baseGantryInfo) {
        return baseGantryInfoService.saveBaseGantryInfo(baseGantryInfo);
    }

    /**
     * 修改门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantryinfo:edit')")
    @Log(title = "门架信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseGantryInfo baseGantryInfo) {
        return baseGantryInfoService.saveBaseGantryInfo(baseGantryInfo);
    }

    /**
     * 删除门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantryinfo:remove')")
    @Log(title = "门架信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return baseGantryInfoService.deleteBaseGantryInfoByIds(ids);
    }

}
