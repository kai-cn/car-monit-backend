package com.ruoyi.system.service;

import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.system.domain.SysUserOnline;

import java.util.List;

/**
 * 在线用户 服务层
 * 
 * @author ruoyi
 */
public interface ISysUserOnlineService
{
    /**
     * 通过登录地址/用户名称查询信息
     *
     * @param ipaddr 登录地址
     * @param userName 用户名称
     * @return 在线用户信息
     */
    public List<SysUserOnline> selectOnlineByInfo(String ipaddr, String userName);



    /**
     * 设置在线用户信息
     * 
     * @param user 用户信息
     * @return 在线用户
     */
    public SysUserOnline loginUserToUserOnline(LoginUser user);
    /**
     *  在线用户信息
     *
     */
    List<SysUserOnline> selectUserOnlineList();
}
