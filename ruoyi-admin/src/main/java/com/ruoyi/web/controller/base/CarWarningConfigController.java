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
import com.ruoyi.base.domain.CarWarningConfig;
import com.ruoyi.base.service.ICarWarningConfigService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 服务区判定规则Controller
 *
 * @author ruoyi
 * @date 2026-01-27
 */
@RestController
@RequestMapping("/base/config")
public class CarWarningConfigController extends BaseController {

    @Autowired
    private ICarWarningConfigService carWarningConfigService;

    /**
     * 查询服务区判定规则列表
     */
    @PreAuthorize("@ss.hasPermi('base:config:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarWarningConfig carWarningConfig) {
        startPage();
        // carWarningConfig.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarWarningConfig> list = carWarningConfigService.selectCarWarningConfigList(carWarningConfig);
        return getDataTable(list);
    }

    /**
     * 导出服务区判定规则列表
     */
    @PreAuthorize("@ss.hasPermi('base:config:export')")
    @Log(title = "服务区判定规则", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarWarningConfig carWarningConfig) {
        List<CarWarningConfig> list = carWarningConfigService.selectCarWarningConfigList(carWarningConfig);
        ExcelUtil<CarWarningConfig> util = new ExcelUtil<CarWarningConfig>(CarWarningConfig.class);
        return util.exportExcel(list, "服务区判定规则数据");
    }

    /**
     * 获取服务区判定规则详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carWarningConfigService.selectCarWarningConfigById(id));
    }

    /**
     * 新增服务区判定规则
     */
    @PreAuthorize("@ss.hasPermi('base:config:add')")
    @Log(title = "服务区判定规则", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarWarningConfig carWarningConfig) {
        return carWarningConfigService.saveCarWarningConfig(carWarningConfig);
    }

    /**
     * 修改服务区判定规则
     */
    @PreAuthorize("@ss.hasPermi('base:config:edit')")
    @Log(title = "服务区判定规则", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarWarningConfig carWarningConfig) {
        return carWarningConfigService.saveCarWarningConfig(carWarningConfig);
    }

    /**
     * 删除服务区判定规则
     */
    @PreAuthorize("@ss.hasPermi('base:config:remove')")
    @Log(title = "服务区判定规则", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carWarningConfigService.deleteCarWarningConfigByIds(ids);
    }

}
