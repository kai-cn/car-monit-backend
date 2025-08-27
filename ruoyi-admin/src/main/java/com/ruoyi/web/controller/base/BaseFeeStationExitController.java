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
import com.ruoyi.base.domain.BaseFeeStationExit;
import com.ruoyi.base.service.IBaseFeeStationExitService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 收费站出口流水Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/feestationexit")
public class BaseFeeStationExitController extends BaseController {

    @Autowired
    private IBaseFeeStationExitService baseFeeStationExitService;

    /**
     * 查询收费站出口流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feestationexit:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseFeeStationExit baseFeeStationExit) {
        startPage();
        // baseFeeStationExit.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseFeeStationExit> list = baseFeeStationExitService.selectBaseFeeStationExitList(baseFeeStationExit);
        return getDataTable(list);
    }

    /**
     * 导出收费站出口流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feestationexit:export')")
    @Log(title = "收费站出口流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseFeeStationExit baseFeeStationExit) {
        List<BaseFeeStationExit> list = baseFeeStationExitService.selectBaseFeeStationExitList(baseFeeStationExit);
        ExcelUtil<BaseFeeStationExit> util = new ExcelUtil<BaseFeeStationExit>(BaseFeeStationExit.class);
        return util.exportExcel(list, "收费站出口流水数据");
    }

    /**
     * 获取收费站出口流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(baseFeeStationExitService.selectBaseFeeStationExitById(bigId));
    }

    /**
     * 新增收费站出口流水
     */
    @PreAuthorize("@ss.hasPermi('base:feestationexit:add')")
    @Log(title = "收费站出口流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseFeeStationExit baseFeeStationExit) {
        return baseFeeStationExitService.saveBaseFeeStationExit(baseFeeStationExit);
    }

    /**
     * 修改收费站出口流水
     */
    @PreAuthorize("@ss.hasPermi('base:feestationexit:edit')")
    @Log(title = "收费站出口流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseFeeStationExit baseFeeStationExit) {
        return baseFeeStationExitService.saveBaseFeeStationExit(baseFeeStationExit);
    }

    /**
     * 删除收费站出口流水
     */
    @PreAuthorize("@ss.hasPermi('base:feestationexit:remove')")
    @Log(title = "收费站出口流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{bigIds}")
    public AjaxResult remove(@PathVariable String[] bigIds) {
        return baseFeeStationExitService.deleteBaseFeeStationExitByIds(bigIds);
    }

}
