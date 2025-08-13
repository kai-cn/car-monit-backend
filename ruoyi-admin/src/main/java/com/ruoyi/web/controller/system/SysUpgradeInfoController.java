package com.ruoyi.web.controller.system;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.system.domain.SysUpgradeInfo;
import com.ruoyi.system.service.ISysUpgradeInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 系统升级信息Controller
 *
 * @author ruoyi
 * @date 2022-01-10
 */
@RestController
@RequestMapping("/system/upgradeInfo")
public class SysUpgradeInfoController extends BaseController {
    @Autowired
    private ISysUpgradeInfoService sysUpgradeInfoService;

    /**
     * 查询系统升级信息列表
     */
    @GetMapping("/list")
    public TableDataInfo list(SysUpgradeInfo sysUpgradeInfo) {
        startPage();
        sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<SysUpgradeInfo> list = sysUpgradeInfoService.selectSysUpgradeInfoList(sysUpgradeInfo);
        return getDataTable(list);
    }

    @GetMapping("/newest")
    public AjaxResult newest(SysUpgradeInfo sysUpgradeInfo) {
        SysUpgradeInfo newest = sysUpgradeInfoService.selectSysUpgradeInfoNewest(sysUpgradeInfo);
        return AjaxResult.success(newest);
    }

    /**
     * 导出系统升级信息列表
     */
    @Log(title = "系统升级信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(SysUpgradeInfo sysUpgradeInfo) {
        List<SysUpgradeInfo> list = sysUpgradeInfoService.selectSysUpgradeInfoList(sysUpgradeInfo);
        ExcelUtil<SysUpgradeInfo> util = new ExcelUtil<SysUpgradeInfo>(SysUpgradeInfo.class);
        return util.exportExcel(list, "系统升级信息数据");
    }

    /**
     * 获取系统升级信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(sysUpgradeInfoService.selectSysUpgradeInfoById(id));
    }

    /**
     * 新增系统升级信息
     */
    @Log(title = "系统升级信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody SysUpgradeInfo sysUpgradeInfo) {
        return sysUpgradeInfoService.saveSysUpgradeInfo(sysUpgradeInfo);
    }

    /**
     * 修改系统升级信息
     */
    @Log(title = "系统升级信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody SysUpgradeInfo sysUpgradeInfo) {
        return sysUpgradeInfoService.saveSysUpgradeInfo(sysUpgradeInfo);
    }

    /**
     * 删除系统升级信息
     */
    @Log(title = "系统升级信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return sysUpgradeInfoService.deleteSysUpgradeInfoByIds(ids);
    }
}
