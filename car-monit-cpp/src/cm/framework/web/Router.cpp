#include "cm/framework/web/Router.hpp"

#include <algorithm>

#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/Convert.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/utils/sql/SqlUtil.hpp"

namespace cm::web {
namespace {

std::vector<std::string> splitSegments(const std::string& path) {
    std::vector<std::string> out;
    std::string cur;
    for (char c : path) {
        if (c == '/') {
            if (!cur.empty()) {
                out.push_back(cur);
                cur.clear();
            }
        } else {
            cur.push_back(c);
        }
    }
    if (!cur.empty()) out.push_back(cur);
    return out;
}

/** 单段通配：* 任意串，? 单个字符 */
bool segmentWildcardMatch(const std::string& pattern, const std::string& text) {
    size_t pi = 0, ti = 0, star = std::string::npos, mark = 0;
    while (ti < text.size()) {
        if (pi < pattern.size() && (pattern[pi] == '?' || pattern[pi] == text[ti])) {
            ++pi;
            ++ti;
        } else if (pi < pattern.size() && pattern[pi] == '*') {
            star = pi++;
            mark = ti;
        } else if (star != std::string::npos) {
            pi = star + 1;
            ti = ++mark;
        } else {
            return false;
        }
    }
    while (pi < pattern.size() && pattern[pi] == '*') ++pi;
    return pi == pattern.size();
}

bool hasWildcard(const std::string& seg) {
    return seg.find('*') != std::string::npos || seg.find('?') != std::string::npos;
}

bool isVar(const std::string& seg) { return seg.size() >= 2 && seg.front() == '{' && seg.back() == '}'; }

std::string varName(const std::string& seg) {
    std::string inner = seg.substr(1, seg.size() - 2);
    size_t colon = inner.find(':');
    return colon == std::string::npos ? inner : inner.substr(0, colon);
}

/** Spring AntPathMatcher 语义（分段）：** 跨段，* 段内 */
bool antMatch(const std::vector<std::string>& pat, size_t pi, const std::vector<std::string>& path, size_t si) {
    while (pi < pat.size()) {
        if (pat[pi] == "**") {
            if (pi + 1 == pat.size()) return true;
            for (size_t k = si; k <= path.size(); ++k) {
                if (antMatch(pat, pi + 1, path, k)) return true;
            }
            return false;
        }
        if (si >= path.size()) return false;
        // {var} 匹配一个完整路径段（Spring @PathVariable），不能按字面量比较
        if (isVar(pat[pi])) {
            ++pi;
            ++si;
            continue;
        }
        if (!segmentWildcardMatch(pat[pi], path[si])) return false;
        ++pi;
        ++si;
    }
    return si == path.size();
}

bool antMatch(const std::string& pattern, const std::string& path) {
    return antMatch(splitSegments(pattern), 0, splitSegments(path), 0);
}

int routeSpecificity(const Route& r) {
    int literals = 0, wildcards = 0, vars = 0;
    for (const auto& s : r.segments) {
        if (s == "**" || hasWildcard(s)) ++wildcards;
        else if (isVar(s)) ++vars;
        else ++literals;
    }
    // 越大越具体
    return literals * 10000 - vars * 100 - wildcards * 10 + static_cast<int>(r.segments.size());
}

} // namespace

std::vector<std::string> Router::splitPath(const std::string& path) {
    return splitSegments(path);
}

long long RequestContext::pathVarLong(const std::string& name) const {
    std::string v = pathVar(name);
    return cm::utils::Convert::toLong(v, 0);
}

cm::core::page::PageDomain RequestContext::pageDomain() const {
    cm::core::page::PageDomain d;
    d.pageNum = cm::utils::Convert::toInt(param("pageNum"), 1);
    d.pageSize = cm::utils::Convert::toInt(param("pageSize"), 10);
    if (auto v = optParam("orderByColumn")) d.orderByColumn = *v;
    d.setIsAsc(param("isAsc"));
    if (auto v = optParam("reasonable")) d.reasonable = cm::utils::Convert::toBool(*v, false);
    return d;
}

cm::db::PageRequest RequestContext::pageRequest() const {
    auto d = pageDomain();
    cm::db::PageRequest pr;
    pr.enabled = true;
    pr.pageNum = d.pageNum.value_or(1);
    pr.pageSize = d.pageSize.value_or(10);
    pr.reasonable = d.getReasonable();
    pr.orderBy = cm::utils::sql::SqlUtil::escapeOrderBySql(d.getOrderBy());
    return pr;
}

RouteBuilder& RouteBuilder::permitAll() { return auth(AuthType::PermitAll); }
RouteBuilder& RouteBuilder::anonymous() { return auth(AuthType::Anonymous); }
RouteBuilder& RouteBuilder::denyAll() { return auth(AuthType::DenyAll); }
RouteBuilder& RouteBuilder::auth(AuthType t) {
    auto& routes = const_cast<std::vector<Route>&>(router_->routes());
    routes[index_].auth = t;
    return *this;
}
RouteBuilder& RouteBuilder::permi(const std::string& permission) {
    auto& routes = const_cast<std::vector<Route>&>(router_->routes());
    routes[index_].required_perms.push_back(permission);
    return *this;
}
RouteBuilder& RouteBuilder::anyPermi(const std::string& permissions) {
    auto& routes = const_cast<std::vector<Route>&>(router_->routes());
    for (const auto& p : cm::utils::Convert::toStrArray(permissions, ",")) {
        if (!p.empty()) routes[index_].any_perms.push_back(cm::utils::StringUtils::trim(p));
    }
    return *this;
}
RouteBuilder& RouteBuilder::role(const std::string& role) {
    auto& routes = const_cast<std::vector<Route>&>(router_->routes());
    routes[index_].required_role = role;
    return *this;
}

RouteBuilder Router::addImpl(const std::string& method, const std::string& pattern, Handler h) {
    Route r;
    r.method = method;
    r.pattern = pattern;
    r.segments = splitSegments(pattern);
    r.handler = std::move(h);
    routes_.push_back(std::move(r));
    return RouteBuilder(this, routes_.size() - 1);
}

RouteBuilder Router::get(const std::string& p, Handler h) { return addImpl("GET", p, std::move(h)); }
RouteBuilder Router::post(const std::string& p, Handler h) { return addImpl("POST", p, std::move(h)); }
RouteBuilder Router::put(const std::string& p, Handler h) { return addImpl("PUT", p, std::move(h)); }
RouteBuilder Router::del(const std::string& p, Handler h) { return addImpl("DELETE", p, std::move(h)); }
RouteBuilder Router::patch(const std::string& p, Handler h) { return addImpl("PATCH", p, std::move(h)); }
void Router::add(const std::string& method, const std::string& pattern, Handler h) {
    addImpl(method, pattern, std::move(h));
}

RouteMatch Router::match(const std::string& method, const std::string& path) const {
    RouteMatch result;
    std::vector<std::string> segs = splitSegments(path);
    std::vector<std::pair<int, size_t>> order;
    for (size_t i = 0; i < routes_.size(); ++i) {
        if (routes_[i].method != method) continue;
        order.emplace_back(routeSpecificity(routes_[i]), i);
    }
    std::stable_sort(order.begin(), order.end(),
                     [](const auto& a, const auto& b) { return a.first > b.first; });

    std::string allowed;
    for (const auto& [score, idx] : order) {
        const Route& r = routes_[idx];
        if (!antMatch(r.segments, 0, segs, 0)) continue;
        // 抽取路径变量
        std::map<std::string, std::string> vars;
        size_t si = 0;
        bool ok = true;
        for (size_t pi = 0; pi < r.segments.size(); ++pi) {
            const std::string& ps = r.segments[pi];
            if (ps == "**") {
                si = segs.size();
                continue;
            }
            if (si >= segs.size()) {
                ok = false;
                break;
            }
            if (isVar(ps)) vars[varName(ps)] = segs[si];
            ++si;
        }
        if (!ok) continue;
        result.matched = true;
        result.route = &r;
        result.path_vars = std::move(vars);
        return result;
    }
    // 方法不支持：找出该路径支持的方法
    for (const auto& r : routes_) {
        if (r.method == method) continue;
        if (antMatch(r.segments, 0, segs, 0)) {
            if (!allowed.empty()) allowed += ", ";
            allowed += r.method;
        }
    }
    if (!allowed.empty()) {
        result.method_not_allowed = true;
        result.allowed_methods = allowed;
    }
    return result;
}

bool Router::anyRouteMatches(const std::string& path) const {
    auto segs = splitSegments(path);
    for (const auto& r : routes_) {
        if (antMatch(r.segments, 0, segs, 0)) return true;
    }
    return false;
}

std::optional<AuthType> Router::urlRule(const std::string& method, const std::string& path) {
    // 顺序严格对应 SecurityConfig：先匹配者生效
    if (path == "/login" || path == "/captchaImage") return AuthType::PermitAll;
    if (method == "GET") {
        if (path == "/") return AuthType::PermitAll;
        if (antMatch("/*.html", path)) return AuthType::PermitAll;
        if (antMatch("/**/*.html", path)) return AuthType::PermitAll;
        if (antMatch("/**/*.css", path)) return AuthType::PermitAll;
        if (antMatch("/**/*.js", path)) return AuthType::PermitAll;
        if (antMatch("/profile/**", path)) return AuthType::PermitAll;
    }
    if (path == "/swagger-ui.html") return AuthType::DenyAll;
    if (antMatch("/swagger-resources/**", path)) return AuthType::DenyAll;
    if (antMatch("/webjars/**", path)) return AuthType::DenyAll;
    if (antMatch("/*/api-docs", path)) return AuthType::DenyAll;
    if (antMatch("/druid/**", path)) return AuthType::DenyAll;
    if (antMatch("/common/download**", path)) return AuthType::Anonymous;
    // AntPathMatcher 整段匹配：/common/download** 不会吞掉 /common/download/resource
    if (antMatch("/common/download/resource**", path)) return AuthType::Authenticated;
    if (antMatch("/system/file/view/**", path)) return AuthType::Anonymous;
    if (antMatch("/system/notice/view/**", path)) return AuthType::Anonymous;
    if (path == "/manager/suspicious/syncSuspiciousCarTask") return AuthType::PermitAll;
    // 没有任何 antMatchers 命中：交给 anyRequest().authenticated()（Server 侧再回落到路由级标记）
    return std::nullopt;
}

AuthType Router::securityRule(const std::string& method, const std::string& path) {
    return urlRule(method, path).value_or(AuthType::Authenticated);
}

Router& router() {
    static Router r;
    return r;
}

} // namespace cm::web
