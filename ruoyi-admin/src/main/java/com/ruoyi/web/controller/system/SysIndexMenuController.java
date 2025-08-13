package com.ruoyi.web.controller.system;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.system.domain.SysIndexMenu;
import com.ruoyi.system.service.ISysIndexMenuService;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 用户常用菜单Controller
 * 
 * @author ruoyi
 * @date 2021-08-20
 */
@RestController
@RequestMapping("/system/indexmenu")
public class SysIndexMenuController extends BaseController
{
    @Autowired
    private ISysIndexMenuService sysIndexMenuService;

    /**
     * 查询用户常用菜单列表
     */
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:list')")
    @GetMapping("/list")
    public TableDataInfo list(SysIndexMenu sysIndexMenu)
    {
        startPage();
        List<SysIndexMenu> list = sysIndexMenuService.selectSysIndexMenuList(sysIndexMenu);
        return getDataTable(list);
    }

    /**
     * 分页查询
     * @param sysIndexMenu 用户常用菜单
     * @return
     */
    @ApiOperation(value = "查询", notes = "查询")
    @GetMapping("/mylist" )
    public AjaxResult getSysIndexMenulist(SysIndexMenu sysIndexMenu) {
        Long userId = SecurityUtils.getUserId();
        sysIndexMenu.setUserId(userId);
        return AjaxResult.success(sysIndexMenuService.getList(sysIndexMenu));
    }

    /**
     * 导出用户常用菜单列表
     */
    @PreAuthorize("@ss.hasPermi('system:indexmenu:export')")
    @Log(title = "用户常用菜单", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(SysIndexMenu sysIndexMenu)
    {
        List<SysIndexMenu> list = sysIndexMenuService.selectSysIndexMenuList(sysIndexMenu);
        ExcelUtil<SysIndexMenu> util = new ExcelUtil<SysIndexMenu>(SysIndexMenu.class);
        return util.exportExcel(list, "用户常用菜单数据");
    }

    /**
     * 获取用户常用菜单详细信息
     */
    @PreAuthorize("@ss.hasPermi('system:indexmenu:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id)
    {
        return AjaxResult.success(sysIndexMenuService.selectSysIndexMenuById(id));
    }

    /**
     * 新增用户常用菜单
     */
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:add')")
    @Log(title = "用户常用菜单", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody SysIndexMenu sysIndexMenu)
    {
        String menuIds = sysIndexMenu.getMenuIds();
        return sysIndexMenuService.insertSysIndexMenu(menuIds);
    }

    /**
     * 修改用户常用菜单
     */
    @PreAuthorize("@ss.hasPermi('system:indexmenu:edit')")
    @Log(title = "用户常用菜单", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody SysIndexMenu sysIndexMenu)
    {
        return sysIndexMenuService.saveSysIndexMenu(sysIndexMenu);
    }

    /**
     * 删除用户常用菜单
     */
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:remove')")
    @Log(title = "用户常用菜单", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids)
    {
        return sysIndexMenuService.deleteSysIndexMenuByIds(ids);
    }
}
