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
import com.ruoyi.base.domain.BaseSfzjcxx;
import com.ruoyi.base.service.IBaseSfzjcxxService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 收费站基础信息位置Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/sfzjcxx")
public class BaseSfzjcxxController extends BaseController {

    @Autowired
    private IBaseSfzjcxxService baseSfzjcxxService;

    /**
     * 查询收费站基础信息位置列表
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseSfzjcxx baseSfzjcxx) {
        startPage();
        // baseSfzjcxx.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseSfzjcxx> list = baseSfzjcxxService.selectBaseSfzjcxxList(baseSfzjcxx);
        return getDataTable(list);
    }

    /**
     * 导出收费站基础信息位置列表
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:export')")
    @Log(title = "收费站基础信息位置", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseSfzjcxx baseSfzjcxx) {
        List<BaseSfzjcxx> list = baseSfzjcxxService.selectBaseSfzjcxxList(baseSfzjcxx);
        ExcelUtil<BaseSfzjcxx> util = new ExcelUtil<BaseSfzjcxx>(BaseSfzjcxx.class);
        return util.exportExcel(list, "收费站基础信息位置数据");
    }

    /**
     * 获取收费站基础信息位置详细信息
     */
    @GetMapping(value = "/{agentPk}")
    public AjaxResult getInfo(@PathVariable("agentPk") String agentPk) {
        return AjaxResult.success(baseSfzjcxxService.selectBaseSfzjcxxById(agentPk));
    }

    /**
     * 新增收费站基础信息位置
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:add')")
    @Log(title = "收费站基础信息位置", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseSfzjcxx baseSfzjcxx) {
        return baseSfzjcxxService.saveBaseSfzjcxx(baseSfzjcxx);
    }

    /**
     * 修改收费站基础信息位置
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:edit')")
    @Log(title = "收费站基础信息位置", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseSfzjcxx baseSfzjcxx) {
        return baseSfzjcxxService.saveBaseSfzjcxx(baseSfzjcxx);
    }

    /**
     * 删除收费站基础信息位置
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:remove')")
    @Log(title = "收费站基础信息位置", businessType = BusinessType.DELETE)
    @DeleteMapping("/{agentPks}")
    public AjaxResult remove(@PathVariable String[] agentPks) {
        return baseSfzjcxxService.deleteBaseSfzjcxxByIds(agentPks);
    }

}
