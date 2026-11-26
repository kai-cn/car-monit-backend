package com.ruoyi.common.utils;

import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;

import com.ruoyi.common.exception.CustomException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.util.PatternMatchUtils;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.exception.ServiceException;

/**
 * 安全服务工具类
 * 
 * @author ruoyi
 */
public class SecurityUtils
{


    /**
     * 获取用户账户
     **/
    public static String getUsername()
    {
        try
        {
            return getLoginUser().getUsername();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取用户id
     **/
    public static Long getUserId()
    {
        try
        {
            Object userObj = getAuthentication().getPrincipal();
            if (null == userObj) {
                return -1L;
            }
            LoginUser loginUser = (LoginUser)userObj;
            return loginUser.getUser().getUserId();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取用户真实姓名
     **/
    public static String getUserRealName()
    {
        try
        {
            Object userObj = getAuthentication().getPrincipal();
            if (null == userObj) {
                return "用户";
            }
            LoginUser loginUser = (LoginUser)userObj;
            return loginUser.getUser().getNickName();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取用户当前所在部门
     **/
    public static Long getEpsId()
    {
        try
        {
            Object userObj = getAuthentication().getPrincipal();
            if (null == userObj) {
                return -1L;
            }
            LoginUser loginUser = (LoginUser)userObj;
            return loginUser.getUser().getDeptId();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取用户当前所在部门名称
     **/
    public static String getEps()
    {
        try
        {
            Object userObj = getAuthentication().getPrincipal();
            if (null == userObj) {
                return "";
            }
            LoginUser loginUser = (LoginUser)userObj;
            return loginUser.getUser().getEpsName();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取用户当前所在租户
     **/
    public static Long getTenantId()
    {
        try
        {
            Object userObj = getAuthentication().getPrincipal();
            if (null == userObj) {
                return -1L;
            }
            LoginUser loginUser = (LoginUser)userObj;
            return loginUser.getUser().getTenantId();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取用户当前所在部门编码
     **/
    public static String getDeptSubCode()
    {
        try
        {
            Object userObj = getAuthentication().getPrincipal();
            if (null == userObj) {
                return "-1";
            }
            LoginUser loginUser = (LoginUser)userObj;
            return loginUser.getUser().getSubCode();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户账户异常", HttpStatus.UNAUTHORIZED);
        }
    }



    /**
     * 获取用户
     **/
    public static LoginUser getLoginUser()
    {
        try
        {
            return (LoginUser) getAuthentication().getPrincipal();
        }
        catch (Exception e)
        {
            throw new CustomException("获取用户信息异常", HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * 获取Authentication
     */
    public static Authentication getAuthentication()
    {
        return SecurityContextHolder.getContext().getAuthentication();
    }

    /**
     * 生成BCryptPasswordEncoder密码
     *
     * @param password 密码
     * @return 加密字符串
     */
    public static String encryptPassword(String password)
    {
        BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();
        return passwordEncoder.encode(password);
    }

    /**
     * 判断密码是否相同
     *
     * @param rawPassword 真实密码
     * @param encodedPassword 加密后字符
     * @return 结果
     */
    public static boolean matchesPassword(String rawPassword, String encodedPassword)
    {
        BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }

    /**
     * 是否为管理员
     * 
     * @param userId 用户ID
     * @return 结果
     */
    public static boolean isAdmin(Long userId)
    {
        return userId != null && 1L == userId;
    }

    /**
     * 验证用户是否具备某权限
     * 
     * @param permission 权限字符串
     * @return 用户是否具备某权限
     */
    public static boolean hasPermi(String permission)
    {
        return hasPermi(getLoginUser().getPermissions(), permission);
    }

    /**
     * 判断是否包含权限
     * 
     * @param authorities 权限列表
     * @param permission 权限字符串
     * @return 用户是否具备某权限
     */
    public static boolean hasPermi(Collection<String> authorities, String permission)
    {
        return authorities.stream().filter(StringUtils::hasText)
                .anyMatch(x -> Constants.ALL_PERMISSION.equals(x) || PatternMatchUtils.simpleMatch(x, permission));
    }

    /**
     * 验证用户是否拥有某个角色
     * 
     * @param role 角色标识
     * @return 用户是否具备某角色
     */
    public static boolean hasRole(String role)
    {
        List<SysRole> roleList = getLoginUser().getUser().getRoles();
        Collection<String> roles = roleList.stream().map(SysRole::getRoleKey).collect(Collectors.toSet());
        return hasRole(roles, role);
    }

    /**
     * 判断是否包含角色
     * 
     * @param roles 角色列表
     * @param role 角色
     * @return 用户是否具备某角色权限
     */
    public static boolean hasRole(Collection<String> roles, String role)
    {
        return roles.stream().filter(StringUtils::hasText)
                .anyMatch(x -> Constants.SUPER_ADMIN.equals(x) || PatternMatchUtils.simpleMatch(x, role));
    }

}
