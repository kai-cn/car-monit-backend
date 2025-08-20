package com.ruoyi.web.controller.manager;

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
import com.ruoyi.manager.domain.CarWarningRule;
import com.ruoyi.manager.service.ICarWarningRuleService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 预警规则Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/warningrule")
public class CarWarningRuleController extends BaseController {

    @Autowired
    private ICarWarningRuleService carWarningRuleService;

    /**
     * 查询预警规则列表
     */
    @PreAuthorize("@ss.hasPermi('manager:warningrule:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarWarningRule carWarningRule) {
        startPage();
        // carWarningRule.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarWarningRule> list = carWarningRuleService.selectCarWarningRuleList(carWarningRule);
        return getDataTable(list);
    }

    /**
     * 导出预警规则列表
     */
    @PreAuthorize("@ss.hasPermi('manager:warningrule:export')")
    @Log(title = "预警规则", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarWarningRule carWarningRule) {
        List<CarWarningRule> list = carWarningRuleService.selectCarWarningRuleList(carWarningRule);
        ExcelUtil<CarWarningRule> util = new ExcelUtil<CarWarningRule>(CarWarningRule.class);
        return util.exportExcel(list, "预警规则数据");
    }

    /**
     * 获取预警规则详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carWarningRuleService.selectCarWarningRuleById(id));
    }

    /**
     * 新增预警规则
     */
    @PreAuthorize("@ss.hasPermi('manager:warningrule:add')")
    @Log(title = "预警规则", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarWarningRule carWarningRule) {
        return carWarningRuleService.saveCarWarningRule(carWarningRule);
    }

    /**
     * 修改预警规则
     */
    @PreAuthorize("@ss.hasPermi('manager:warningrule:edit')")
    @Log(title = "预警规则", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarWarningRule carWarningRule) {
        return carWarningRuleService.saveCarWarningRule(carWarningRule);
    }

    /**
     * 删除预警规则
     */
    @PreAuthorize("@ss.hasPermi('manager:warningrule:remove')")
    @Log(title = "预警规则", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carWarningRuleService.deleteCarWarningRuleByIds(ids);
    }

}
