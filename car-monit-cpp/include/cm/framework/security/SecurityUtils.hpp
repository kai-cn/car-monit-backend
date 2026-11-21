#pragma once
// 对应 Java: com.ruoyi.common.utils.SecurityUtils
//
// Java 侧从 SecurityContextHolder（ThreadLocal）取 Authentication；
// C++ 侧用 thread_local 保存当前请求的 LoginUser，由认证中间件在请求开始时设置。
#include <optional>
#include <string>

#include "cm/common/core/domain/model/LoginUser.hpp"

namespace cm::security {

class SecurityUtils {
public:
    // ---- 上下文（对应 SecurityContextHolder） ----
    static void setLoginUser(const cm::domain::LoginUser& user);
    static void clear();
    static bool isAuthenticated();
    static std::optional<cm::domain::LoginUser> current(); // 不抛异常

    /** 对应 getLoginUser()：无认证时抛 CustomException("获取用户信息异常", 401) */
    static cm::domain::LoginUser getLoginUser();
    /** 对应 getUsername()：取 user.userName */
    static std::string getUsername();
    /** 对应 getUserId()：principal 为空返回 -1（Java 语义） */
    static long long getUserId();
    /** 对应 getUserRealName()：nickName，principal 为空返回 "用户" */
    static std::string getUserRealName();
    /** 对应 getEpsId()：deptId，principal 为空返回 -1 */
    static long long getEpsId();
    /** 对应 getEps()：epsName，principal 为空返回 "" */
    static std::string getEps();
    /** 对应 getTenantId()：tenantId，principal 为空返回 -1 */
    static long long getTenantId();
    /** 对应 getDeptSubCode()：subCode，principal 为空返回 "-1" */
    static std::string getDeptSubCode();

    // ---- 密码 ----
    static std::string encryptPassword(const std::string& password);
    static bool matchesPassword(const std::string& rawPassword, const std::string& encodedPassword);
    static bool isAdmin(std::optional<long long> userId);
    static bool isAdmin(long long userId) { return userId == 1L; }

    // ---- 权限 ----
    /** 对应 hasPermi(String)：PatternMatchUtils.simpleMatch(x, permission) */
    static bool hasPermi(const std::string& permission);
    /** 对应 hasRole(String)：roleKey 为 admin 或 simpleMatch */
    static bool hasRole(const std::string& role);

    /** Spring PatternMatchUtils.simpleMatch */
    static bool simpleMatch(const std::string& pattern, const std::string& str);
};

} // namespace cm::security
