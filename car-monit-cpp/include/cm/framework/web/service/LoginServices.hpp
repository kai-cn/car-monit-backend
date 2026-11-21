#pragma once
// 对应 Java:
//   com.ruoyi.framework.web.service.SysLoginService
//   com.ruoyi.framework.web.service.SysPermissionService
//   com.ruoyi.framework.web.service.SysPasswordService
//   com.ruoyi.framework.web.service.UserDetailsServiceImpl
#include <set>
#include <string>

#include "cm/common/core/domain/entity/SysUser.hpp"
#include "cm/common/core/domain/model/LoginUser.hpp"
#include "cm/framework/http/HttpRequest.hpp"

namespace cm::security {

/** 对应 SysPermissionService */
class SysPermissionService {
public:
    /** 角色集合：admin -> {"admin"}，否则 sys_role.role_key */
    static std::set<std::string> getRolePermission(const cm::domain::SysUser& user);
    /** 权限集合：admin -> {"*:*:*"}，否则 sys_menu.perms */
    static std::set<std::string> getMenuPermission(const cm::domain::SysUser& user);
};

/** 对应 SysPasswordService（RuoYi 默认走 DaoAuthenticationProvider，保留该类以对齐结构） */
class SysPasswordService {
public:
    void validate(const cm::domain::SysUser& user, const std::string& username,
                  const std::string& password);
    static bool matches(const cm::domain::SysUser& user, const std::string& rawPassword);
    static void clearLoginRecordCache(const std::string& loginName);
    static std::string getCacheKey(const std::string& username);
};

/** 对应 UserDetailsServiceImpl */
class UserDetailsService {
public:
    /** 不存在/已删除/已停用时抛异常（语义同 Java） */
    static cm::domain::LoginUser loadUserByUsername(const std::string& username);
    static cm::domain::LoginUser createLoginUser(const cm::domain::SysUser& user);
};

/** 对应 SysLoginService */
class SysLoginService {
public:
    /** 登录校验，成功返回 token；失败抛出对应异常（由 ExceptionMapper 统一转 AjaxResult） */
    static std::string login(const std::string& username, const std::string& password,
                             const std::string& code, const std::string& uuid,
                             const cm::http::HttpRequest& request);

    /** 对应 AsyncFactory.recordLogininfor（同步写库，语义一致） */
    static void recordLogininfor(const std::string& username, const std::string& status,
                                 const std::string& message, const cm::http::HttpRequest& request);
};

} // namespace cm::security
