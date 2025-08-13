package com.ruoyi.system.mapper;

import java.util.List;
import com.ruoyi.system.domain.SysIndexMenu;
import org.springframework.stereotype.Repository;

/**
 * 用户常用菜单Mapper接口
 * 
 * @author ruoyi
 * @date 2021-08-20
 */
@Repository
public interface SysIndexMenuMapper 
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
     * 新增用户常用菜单
     * 
     * @param sysIndexMenu 用户常用菜单
     * @return 结果
     */
    public int insertSysIndexMenu(SysIndexMenu sysIndexMenu);

    /**
     * 修改用户常用菜单
     * 
     * @param sysIndexMenu 用户常用菜单
     * @return 结果
     */
    public int updateSysIndexMenu(SysIndexMenu sysIndexMenu);

    /**
     * 删除用户常用菜单
     * 
     * @param id 用户常用菜单ID
     * @return 结果
     */
    public int deleteSysIndexMenuById(Long id);

    /**
     * 批量删除用户常用菜单
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteSysIndexMenuByIds(Long[] ids);

    public int deleteByMenuUserId(SysIndexMenu sysIndexMenu);
}
