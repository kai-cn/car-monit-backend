#pragma once
// Web 层上下文：对应 Spring MVC 的 DispatcherServlet + HandlerMethod 参数解析
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <vector>

#include "cm/common/core/page/PageDomain.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/http/HttpRequest.hpp"
#include "cm/framework/http/HttpResponse.hpp"

namespace cm::web {

/** 安全策略（对应 SecurityConfig 的 antMatchers 规则） */
enum class AuthType {
    Authenticated, // anyRequest().authenticated()
    PermitAll,     // permitAll()
    Anonymous,     // anonymous() == access("isAnonymous()")：只有未登录才放行，带 token 反而 403
    DenyAll        // denyAll()
};

class RequestContext {
public:
    cm::http::HttpRequest req;
    std::map<std::string, std::string> path_vars;
    /** 路由级元数据（权限表达式等） */
    std::vector<std::string> required_perms;

    std::string param(const std::string& name) const {
        if (auto v = req.getParameter(name)) return *v;
        return "";
    }
    std::optional<std::string> optParam(const std::string& name) const { return req.getParameter(name); }
    std::vector<std::string> params(const std::string& name) const { return req.getParameterValues(name); }
    std::string pathVar(const std::string& name) const {
        auto it = path_vars.find(name);
        return it == path_vars.end() ? "" : it->second;
    }
    long long pathVarLong(const std::string& name) const;
    std::string getHeader(const std::string& name) const { return req.getHeader(name); }
    Json body() const { return req.json(); }

    /** 对应 TableSupport.buildPageRequest + SqlUtil.escapeOrderBySql */
    cm::core::page::PageDomain pageDomain() const;
    /** 对应 BaseController.startPage 之后的 PageRequest */
    cm::db::PageRequest pageRequest() const;
};

using Handler = std::function<cm::http::ApiResponse(RequestContext&)>;

struct RouteMatch {
    bool matched{false};
    bool method_not_allowed{false};
    std::string allowed_methods;
    const struct Route* route{nullptr};
    std::map<std::string, std::string> path_vars;
};

/** 链式路由配置（对应 @GetMapping + @PreAuthorize + SecurityConfig） */
class RouteBuilder {
public:
    RouteBuilder(struct Router* router, size_t index) : router_(router), index_(index) {}
    RouteBuilder& permitAll();
    RouteBuilder& anonymous();
    RouteBuilder& denyAll();
    RouteBuilder& auth(AuthType t);
    /** 等价 @PreAuthorize("@ss.hasPermi('system:user:list')") */
    RouteBuilder& permi(const std::string& permission);
    /** 等价 @PreAuthorize("@ss.hasAnyPermi('a,b')") */
    RouteBuilder& anyPermi(const std::string& permissions);
    /** 等价 @PreAuthorize("@ss.hasRole('admin')") */
    RouteBuilder& role(const std::string& role);

private:
    Router* router_;
    size_t index_;
};

struct Route {
    std::string method;
    std::vector<std::string> segments; // "{userId}" 表示路径变量
    Handler handler;
    AuthType auth{AuthType::Authenticated};
    std::vector<std::string> required_perms;
    std::vector<std::string> any_perms;
    std::string required_role;
    std::string pattern;
};

class Router {
public:
    RouteBuilder get(const std::string& pattern, Handler h);
    RouteBuilder post(const std::string& pattern, Handler h);
    RouteBuilder put(const std::string& pattern, Handler h);
    RouteBuilder del(const std::string& pattern, Handler h);
    RouteBuilder patch(const std::string& pattern, Handler h);
    /** 注册所有方法 */
    void add(const std::string& method, const std::string& pattern, Handler h);

    RouteMatch match(const std::string& method, const std::string& path) const;
    /** 仅按路径匹配（用于 Security 先于 404 判定） */
    bool anyRouteMatches(const std::string& path) const;

    /** 对应 SecurityConfig 的静态规则；返回该路径的安全策略（未命中任何 antMatchers 时返回 nullopt） */
    static std::optional<AuthType> urlRule(const std::string& method, const std::string& path);
    /** urlRule 的兜底版本：未命中即 anyRequest().authenticated() */
    static AuthType securityRule(const std::string& method, const std::string& path);

    const std::vector<Route>& routes() const { return routes_; }

private:
    RouteBuilder addImpl(const std::string& method, const std::string& pattern, Handler h);
    static std::vector<std::string> splitPath(const std::string& path);
    std::vector<Route> routes_;
};

/** 全局单例路由表 */
Router& router();

} // namespace cm::web
