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
import com.ruoyi.base.domain.BaseServiceAreaInfo;
import com.ruoyi.base.service.IBaseServiceAreaInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 服务区基础信息Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/serviceareainfo")
public class BaseServiceAreaInfoController extends BaseController {

    @Autowired
    private IBaseServiceAreaInfoService baseServiceAreaInfoService;

    /**
     * 查询服务区基础信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:serviceareainfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseServiceAreaInfo baseServiceAreaInfo) {
        startPage();
        // baseServiceAreaInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseServiceAreaInfo> list = baseServiceAreaInfoService.selectBaseServiceAreaInfoList(baseServiceAreaInfo);
        return getDataTable(list);
    }

    /**
     * 导出服务区基础信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:serviceareainfo:export')")
    @Log(title = "服务区基础信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseServiceAreaInfo baseServiceAreaInfo) {
        List<BaseServiceAreaInfo> list = baseServiceAreaInfoService.selectBaseServiceAreaInfoList(baseServiceAreaInfo);
        ExcelUtil<BaseServiceAreaInfo> util = new ExcelUtil<BaseServiceAreaInfo>(BaseServiceAreaInfo.class);
        return util.exportExcel(list, "服务区基础信息数据");
    }

    /**
     * 获取服务区基础信息详细信息
     */
    @GetMapping(value = "/{agentPk}")
    public AjaxResult getInfo(@PathVariable("agentPk") String agentPk) {
        return AjaxResult.success(baseServiceAreaInfoService.selectBaseServiceAreaInfoById(agentPk));
    }

    /**
     * 新增服务区基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:serviceareainfo:add')")
    @Log(title = "服务区基础信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseServiceAreaInfo baseServiceAreaInfo) {
        return baseServiceAreaInfoService.saveBaseServiceAreaInfo(baseServiceAreaInfo);
    }

    /**
     * 修改服务区基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:serviceareainfo:edit')")
    @Log(title = "服务区基础信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseServiceAreaInfo baseServiceAreaInfo) {
        return baseServiceAreaInfoService.saveBaseServiceAreaInfo(baseServiceAreaInfo);
    }

    /**
     * 删除服务区基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:serviceareainfo:remove')")
    @Log(title = "服务区基础信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{agentPks}")
    public AjaxResult remove(@PathVariable String[] agentPks) {
        return baseServiceAreaInfoService.deleteBaseServiceAreaInfoByIds(agentPks);
    }

}
