package com.ruoyi.web.controller.manager;

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
import com.ruoyi.manager.domain.GantryTradeInfo;
import com.ruoyi.manager.service.IGantryTradeInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 门架交易查询Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/gantrytrade")
public class GantryTradeInfoController extends BaseController {

    @Autowired
    private IGantryTradeInfoService gantryTradeInfoService;

    /**
     * 查询门架交易查询列表
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrytrade:list')")
    @GetMapping("/list")
    public TableDataInfo list(GantryTradeInfo gantryTradeInfo) {
        startPage();
        // gantryTradeInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<GantryTradeInfo> list = gantryTradeInfoService.selectGantryTradeInfoList(gantryTradeInfo);
        return getDataTable(list);
    }

    /**
     * 导出门架交易查询列表
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrytrade:export')")
    @Log(title = "门架交易查询", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(GantryTradeInfo gantryTradeInfo) {
        List<GantryTradeInfo> list = gantryTradeInfoService.selectGantryTradeInfoList(gantryTradeInfo);
        ExcelUtil<GantryTradeInfo> util = new ExcelUtil<GantryTradeInfo>(GantryTradeInfo.class);
        return util.exportExcel(list, "门架交易查询数据");
    }

    /**
     * 获取门架交易查询详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(gantryTradeInfoService.selectGantryTradeInfoById(id));
    }

    /**
     * 新增门架交易查询
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrytrade:add')")
    @Log(title = "门架交易查询", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody GantryTradeInfo gantryTradeInfo) {
        return gantryTradeInfoService.saveGantryTradeInfo(gantryTradeInfo);
    }

    /**
     * 修改门架交易查询
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrytrade:edit')")
    @Log(title = "门架交易查询", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody GantryTradeInfo gantryTradeInfo) {
        return gantryTradeInfoService.saveGantryTradeInfo(gantryTradeInfo);
    }

    /**
     * 删除门架交易查询
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrytrade:remove')")
    @Log(title = "门架交易查询", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return gantryTradeInfoService.deleteGantryTradeInfoByIds(ids);
    }

}
