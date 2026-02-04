package com.ruoyi.web.controller.base;

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
import com.ruoyi.base.domain.BaseConfigServiceArea;
import com.ruoyi.base.service.IBaseConfigServiceAreaService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 服务区Controller
 *
 * @author ruoyi
 * @date 2026-02-02
 */
@RestController
@RequestMapping("/base/configServiceArea")
public class BaseConfigServiceAreaController extends BaseController {

    @Autowired
    private IBaseConfigServiceAreaService baseConfigServiceAreaService;

    /**
     * 查询服务区列表
     */
    @PreAuthorize("@ss.hasPermi('base:configServiceArea:list')")
    @GetMapping("/list")
    public TableDataInfo list(BaseConfigServiceArea baseConfigServiceArea) {
        startPage();
        // baseConfigServiceArea.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BaseConfigServiceArea> list = baseConfigServiceAreaService.selectBaseConfigServiceAreaList(baseConfigServiceArea);
        return getDataTable(list);
    }




    /**
     * 查询服务区列表
     */
    @GetMapping("/listQuery")
    public AjaxResult listQuery(BaseConfigServiceArea baseConfigServiceArea) {
        List<BaseConfigServiceArea> list = baseConfigServiceAreaService.selectBaseConfigServiceAreaList(baseConfigServiceArea);
        return AjaxResult.success(list);
    }


    /**
     * 导出服务区列表
     */
    @PreAuthorize("@ss.hasPermi('base:configServiceArea:export')")
    @Log(title = "服务区", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BaseConfigServiceArea baseConfigServiceArea) {
        List<BaseConfigServiceArea> list = baseConfigServiceAreaService.selectBaseConfigServiceAreaList(baseConfigServiceArea);
        ExcelUtil<BaseConfigServiceArea> util = new ExcelUtil<BaseConfigServiceArea>(BaseConfigServiceArea.class);
        return util.exportExcel(list, "服务区数据");
    }

    /**
     * 获取服务区详细信息
     */
    @GetMapping(value = "/{fwqbm}")
    public AjaxResult getInfo(@PathVariable("fwqbm") String fwqbm) {
        return AjaxResult.success(baseConfigServiceAreaService.selectBaseConfigServiceAreaById(fwqbm));
    }

    /**
     * 新增服务区
     */
    @PreAuthorize("@ss.hasPermi('base:configServiceArea:add')")
    @Log(title = "服务区", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BaseConfigServiceArea baseConfigServiceArea) {
        return baseConfigServiceAreaService.saveBaseConfigServiceArea(baseConfigServiceArea);
    }

    /**
     * 修改服务区
     */
    @PreAuthorize("@ss.hasPermi('base:configServiceArea:edit')")
    @Log(title = "服务区", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BaseConfigServiceArea baseConfigServiceArea) {
        return baseConfigServiceAreaService.saveBaseConfigServiceArea(baseConfigServiceArea);
    }

    /**
     * 删除服务区
     */
    @PreAuthorize("@ss.hasPermi('base:configServiceArea:remove')")
    @Log(title = "服务区", businessType = BusinessType.DELETE)
    @DeleteMapping("/{fwqbms}")
    public AjaxResult remove(@PathVariable String[] fwqbms) {
        return baseConfigServiceAreaService.deleteBaseConfigServiceAreaByIds(fwqbms);
    }

}
