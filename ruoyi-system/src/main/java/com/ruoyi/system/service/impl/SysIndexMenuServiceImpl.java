package com.ruoyi.system.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.system.mapper.SysIndexMenuMapper;
import com.ruoyi.system.domain.SysIndexMenu;
import com.ruoyi.system.service.ISysIndexMenuService;

import java.util.List;

/**
 * 用户常用菜单Service业务层处理
 * 
 * @author ruoyi
 * @date 2021-08-20
 */
@Service
public class SysIndexMenuServiceImpl implements ISysIndexMenuService 
{
    @Autowired
    private SysIndexMenuMapper sysIndexMenuMapper;

    /**
     * 查询用户常用菜单
     * 
     * @param id 用户常用菜单ID
     * @return 用户常用菜单
     */
    @Override
    public SysIndexMenu selectSysIndexMenuById(Long id)
    {
        return sysIndexMenuMapper.selectSysIndexMenuById(id);
    }

    /**
     * 查询用户常用菜单列表
     * 
     * @param sysIndexMenu 用户常用菜单
     * @return 用户常用菜单
     */
    @Override
    public List<SysIndexMenu> selectSysIndexMenuList(SysIndexMenu sysIndexMenu)
    {
        Long userId = SecurityUtils.getUserId();
        sysIndexMenu.setUserId(userId);
        return sysIndexMenuMapper.selectSysIndexMenuList(sysIndexMenu);
    }

    /**
     * 查询list
     * @param sysIndexMenu
     * @return
     */
    public List<SysIndexMenu> getList(SysIndexMenu sysIndexMenu)
    {
        // 用戶id
        Long userId = SecurityUtils.getUserId();
        sysIndexMenu.setUserId(userId);
        return sysIndexMenuMapper.getList(sysIndexMenu);
    }

    /**
     * 新增或者修改用户常用菜单
     *
     * @param sysIndexMenu 用户常用菜单
     * @return 结果
     */
    public AjaxResult saveSysIndexMenu(SysIndexMenu sysIndexMenu)
    {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(sysIndexMenu.getId()))
        {
            // 修改
            sysIndexMenu.setUpdateBy(userId); // 更新人
            sysIndexMenu.setUpdateTime(curDate); // 更新时间
            sysIndexMenuMapper.updateSysIndexMenu(sysIndexMenu);
        }
        else
        {
            // 新增
            sysIndexMenu.setId(StringUtils.getUUID()); // 主键
            sysIndexMenu.setDelFlag("0");
            sysIndexMenu.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            sysIndexMenu.setCreateBy(userId); // 创建人
            sysIndexMenu.setCreateTime(curDate); // 创建时间
            sysIndexMenu.setUpdateBy(userId); // 更新人
            sysIndexMenu.setUpdateTime(curDate); // 更新时间
            sysIndexMenuMapper.insertSysIndexMenu(sysIndexMenu);
        }
        return AjaxResult.success("操作成功！",sysIndexMenu.getId());
    }

    @Override
    public AjaxResult insertSysIndexMenu(String menuIds) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotBlank(menuIds)) {
            if (menuIds.endsWith(",")) {
                menuIds = menuIds.substring(0, menuIds.length() - 1);
            }
            String[] menuIdStr = menuIds.split(",");
            for (int i=0;i<menuIdStr.length;i++)
            {
                SysIndexMenu bo = new SysIndexMenu();
                bo.setUserId(userId);
                bo.setMenuId(Long.parseLong(menuIdStr[i]));
                // 先删
                sysIndexMenuMapper.deleteByMenuUserId(bo);
                bo.setDelFlag("0");
                bo.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
                bo.setCreateBy(userId); // 创建人
                bo.setCreateTime(curDate); // 创建时间
                bo.setUpdateBy(userId); // 更新人
                bo.setUpdateTime(curDate); // 更新时间
                sysIndexMenuMapper.insertSysIndexMenu(bo);
            }
        }
        return AjaxResult.success();
    }


    /**
     * 批量删除用户常用菜单
     * 
     * @param ids 需要删除的用户常用菜单ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteSysIndexMenuByIds(Long[] ids)
    {
        int count = sysIndexMenuMapper.deleteSysIndexMenuByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除用户常用菜单信息
     * 
     * @param id 用户常用菜单ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteSysIndexMenuById(Long id)
    {
        int count = sysIndexMenuMapper.deleteSysIndexMenuById(id);
        return AjaxResult.success(count);
    }
}
