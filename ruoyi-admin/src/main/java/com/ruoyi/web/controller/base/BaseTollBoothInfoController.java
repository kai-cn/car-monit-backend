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
import com.ruoyi.base.domain.BaseTollBoothInfo;
import com.ruoyi.base.service.IBaseTollBoothInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 收费所基础信息Controller
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@RestController
@RequestMapping("/base/tollboothinfo")
public class BaseTollBoothInfoController extends BaseController {

    @Autowired
    private IBaseTollBoothInfoService baseTollBoothInfoService;

    /**
     * 查询收费所基础信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:tollboothinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseTollBoothInfo baseTollBoothInfo) {
        startPage();
        // baseTollBoothInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseTollBoothInfo> list = baseTollBoothInfoService.selectBaseTollBoothInfoList(baseTollBoothInfo);
        return getDataTable(list);
    }

    /**
     * 导出收费所基础信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:tollboothinfo:export')")
    @Log(title = "收费所基础信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseTollBoothInfo baseTollBoothInfo) {
        List<BaseTollBoothInfo> list = baseTollBoothInfoService.selectBaseTollBoothInfoList(baseTollBoothInfo);
        ExcelUtil<BaseTollBoothInfo> util = new ExcelUtil<BaseTollBoothInfo>(BaseTollBoothInfo.class);
        return util.exportExcel(list, "收费所基础信息数据");
    }

    /**
     * 获取收费所基础信息详细信息
     */
    @GetMapping(value = "/{agentPk}")
    public AjaxResult getInfo(@PathVariable("agentPk") String agentPk) {
        return AjaxResult.success(baseTollBoothInfoService.selectBaseTollBoothInfoById(agentPk));
    }

    /**
     * 新增收费所基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:tollboothinfo:add')")
    @Log(title = "收费所基础信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseTollBoothInfo baseTollBoothInfo) {
        return baseTollBoothInfoService.saveBaseTollBoothInfo(baseTollBoothInfo);
    }

    /**
     * 修改收费所基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:tollboothinfo:edit')")
    @Log(title = "收费所基础信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseTollBoothInfo baseTollBoothInfo) {
        return baseTollBoothInfoService.saveBaseTollBoothInfo(baseTollBoothInfo);
    }

    /**
     * 删除收费所基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:tollboothinfo:remove')")
    @Log(title = "收费所基础信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{agentPks}")
    public AjaxResult remove(@PathVariable String[] agentPks) {
        return baseTollBoothInfoService.deleteBaseTollBoothInfoByIds(agentPks);
    }

}
