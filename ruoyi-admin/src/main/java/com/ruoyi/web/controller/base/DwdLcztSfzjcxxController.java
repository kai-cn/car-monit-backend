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
import com.ruoyi.base.domain.DwdLcztSfzjcxx;
import com.ruoyi.base.service.IDwdLcztSfzjcxxService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 收费站基础信息Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/sfzjcxx")
public class DwdLcztSfzjcxxController extends BaseController {

    @Autowired
    private IDwdLcztSfzjcxxService dwdLcztSfzjcxxService;

    /**
     * 查询收费站基础信息列表
     */
    @GetMapping("/list")
    public TableDataInfo list(DwdLcztSfzjcxx dwdLcztSfzjcxx) {
        startPage();
        // dwdLcztSfzjcxx.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<DwdLcztSfzjcxx> list = dwdLcztSfzjcxxService.selectDwdLcztSfzjcxxList(dwdLcztSfzjcxx);
        return getDataTable(list);
    }

    /**
     * 导出收费站基础信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:export')")
    @Log(title = "收费站基础信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(DwdLcztSfzjcxx dwdLcztSfzjcxx) {
        List<DwdLcztSfzjcxx> list = dwdLcztSfzjcxxService.selectDwdLcztSfzjcxxList(dwdLcztSfzjcxx);
        ExcelUtil<DwdLcztSfzjcxx> util = new ExcelUtil<DwdLcztSfzjcxx>(DwdLcztSfzjcxx.class);
        return util.exportExcel(list, "收费站基础信息数据");
    }

    /**
     * 获取收费站基础信息详细信息
     */
    @GetMapping(value = "/{agentPk}")
    public AjaxResult getInfo(@PathVariable("agentPk") String agentPk) {
        return AjaxResult.success(dwdLcztSfzjcxxService.selectDwdLcztSfzjcxxById(agentPk));
    }

    /**
     * 新增收费站基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:add')")
    @Log(title = "收费站基础信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody DwdLcztSfzjcxx dwdLcztSfzjcxx) {
        return dwdLcztSfzjcxxService.saveDwdLcztSfzjcxx(dwdLcztSfzjcxx);
    }

    /**
     * 修改收费站基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:edit')")
    @Log(title = "收费站基础信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody DwdLcztSfzjcxx dwdLcztSfzjcxx) {
        return dwdLcztSfzjcxxService.saveDwdLcztSfzjcxx(dwdLcztSfzjcxx);
    }

    /**
     * 删除收费站基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:sfzjcxx:remove')")
    @Log(title = "收费站基础信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{agentPks}")
    public AjaxResult remove(@PathVariable String[] agentPks) {
        return dwdLcztSfzjcxxService.deleteDwdLcztSfzjcxxByIds(agentPks);
    }

}
