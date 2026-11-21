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
import com.ruoyi.base.domain.OdsYhglVBaseOrg;
import com.ruoyi.base.service.IOdsYhglVBaseOrgService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 机构信息Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/org")
public class OdsYhglVBaseOrgController extends BaseController {

    @Autowired
    private IOdsYhglVBaseOrgService odsYhglVBaseOrgService;

    @Autowired
    private com.ruoyi.manager.service.bigscreen.DictVersionService dictVersionService;

    /**
     * 查询机构信息列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsYhglVBaseOrg odsYhglVBaseOrg) {
        startPage();
        // odsYhglVBaseOrg.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsYhglVBaseOrg> list = odsYhglVBaseOrgService.selectOdsYhglVBaseOrgList(odsYhglVBaseOrg);
        return getDataTable(list);
    }

    /**
     * 导出机构信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:org:export')")
    @Log(title = "机构信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(OdsYhglVBaseOrg odsYhglVBaseOrg) {
        List<OdsYhglVBaseOrg> list = odsYhglVBaseOrgService.selectOdsYhglVBaseOrgList(odsYhglVBaseOrg);
        ExcelUtil<OdsYhglVBaseOrg> util = new ExcelUtil<OdsYhglVBaseOrg>(OdsYhglVBaseOrg.class);
        return util.exportExcel(list, "机构信息数据");
    }

    /**
     * 获取机构信息详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(odsYhglVBaseOrgService.selectOdsYhglVBaseOrgById(bigId));
    }

    /**
     * 新增机构信息
     */
    @PreAuthorize("@ss.hasPermi('base:org:add')")
    @Log(title = "机构信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody OdsYhglVBaseOrg odsYhglVBaseOrg) {
        return bumpAfter(odsYhglVBaseOrgService.saveOdsYhglVBaseOrg(odsYhglVBaseOrg));
    }

    /**
     * 修改机构信息
     */
    @PreAuthorize("@ss.hasPermi('base:org:edit')")
    @Log(title = "机构信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody OdsYhglVBaseOrg odsYhglVBaseOrg) {
        return bumpAfter(odsYhglVBaseOrgService.saveOdsYhglVBaseOrg(odsYhglVBaseOrg));
    }

    /**
     * 删除机构信息
     */
    @PreAuthorize("@ss.hasPermi('base:org:remove')")
    @Log(title = "机构信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{bigIds}")
    public AjaxResult remove(@PathVariable String[] bigIds) {
        return bumpAfter(odsYhglVBaseOrgService.deleteOdsYhglVBaseOrgByIds(bigIds));
    }

    private AjaxResult bumpAfter(AjaxResult result) {
        try {
            dictVersionService.bump(
                    com.ruoyi.manager.service.bigscreen.DictVersionService.ORG);
        } catch (RuntimeException e) {
            logger.warn("[字典版本] 机构主动失效失败 reason={}", e.getMessage());
        }
        return result;
    }

}
