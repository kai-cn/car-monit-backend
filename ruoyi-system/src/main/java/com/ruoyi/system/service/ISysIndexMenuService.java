package com.ruoyi.system.service;

import java.util.List;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.system.domain.SysIndexMenu;

/**
 * 用户常用菜单Service接口
 * 
 * @author ruoyi
 * @date 2021-08-20
 */
public interface ISysIndexMenuService 
{
    /**
     * 查询用户常用菜单
     * 
     * @param id 用户常用菜单ID
     * @return 用户常用菜单
     */
    public SysIndexMenu selectSysIndexMenuById(Long id);

    /**
     * 查询用户常用菜单列表
     * 
     * @param sysIndexMenu 用户常用菜单
     * @return 用户常用菜单集合
     */
    public List<SysIndexMenu> selectSysIndexMenuList(SysIndexMenu sysIndexMenu);

    public List<SysIndexMenu> getList(SysIndexMenu sysIndexMenu);
    /**
     * 新增或者修改用户常用菜单
     * 
     * @param sysIndexMenu 用户常用菜单
     * @return 结果
     */
    public AjaxResult saveSysIndexMenu(SysIndexMenu sysIndexMenu);

    public AjaxResult insertSysIndexMenu(String menuIds);

    /**
     * 批量删除用户常用菜单
     * 
     * @param ids 需要删除的用户常用菜单ID
     * @return 结果
     */
    public AjaxResult deleteSysIndexMenuByIds(Long[] ids);

    /**
     * 删除用户常用菜单信息
     * 
     * @param id 用户常用菜单ID
     * @return 结果
     */
    public AjaxResult deleteSysIndexMenuById(Long id);
}
