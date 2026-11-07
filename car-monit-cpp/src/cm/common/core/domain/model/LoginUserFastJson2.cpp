#include "cm/common/core/domain/model/LoginUserFastJson2.hpp"

#include <algorithm>
#include <string>
#include <utility>
#include <vector>

#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/JsonUtils.hpp"

namespace cm::domain {
namespace {

/** 字符串字面量（fastjson2 不转义非 ASCII；控制字符仍需转义） */
std::string q(const std::string& s) { return Json(s).dump(); }

/** 根层 boxed Long：不带 L 后缀 */
std::string rootLong(const std::optional<long long>& v) { return std::to_string(*v); }

/** 嵌套层的 Long：fastjson2 写成 `123L` */
std::string nestedLong(long long v) { return std::to_string(v) + "L"; }

void appendKey(std::string& out, bool& first, const char* key) {
    if (!first) out += ',';
    first = false;
    out += q(key);
    out += ':';
}

/** BaseEntity 段（嵌套层）：Java 的 params 是 new HashMap<>() 非 null，空 Map 也要写 */
void appendBaseEntity(std::vector<std::pair<std::string, std::string>>& kv, const BaseEntity& b) {
    if (b.createBy) kv.emplace_back("createBy", q(*b.createBy));
    if (b.createTime) kv.emplace_back("createTime", q(utils::DateUtils::formatJsonDate(b.createTime)));
    if (b.updateBy) kv.emplace_back("updateBy", q(*b.updateBy));
    if (b.updateTime) kv.emplace_back("updateTime", q(utils::DateUtils::formatJsonDate(b.updateTime)));
    if (b.remark) kv.emplace_back("remark", q(*b.remark));
    if (b.searchValue) kv.emplace_back("searchValue", q(*b.searchValue));
    std::string p = "{\"@type\":\"java.util.HashMap\"";
    if (b.params.is_object()) {
        for (auto it = b.params.begin(); it != b.params.end(); ++it) {
            p += "," + q(it.key()) + ":" + it.value().dump();
        }
    }
    p += "}";
    kv.emplace_back("params", p);
}

std::string objOf(std::vector<std::pair<std::string, std::string>> kv) {
    std::sort(kv.begin(), kv.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    std::string out = "{";
    bool first = true;
    for (const auto& [k, v] : kv) {
        if (!first) out += ',';
        first = false;
        out += q(k) + ":" + v;
    }
    out += '}';
    return out;
}

/** SysDept（嵌套层；Long 带 L，Integer 不带，children 空数组照写） */
std::string sysDeptFastJson2(const SysDept& d) {
    std::vector<std::pair<std::string, std::string>> kv;
    if (d.account) kv.emplace_back("account", q(*d.account));
    if (d.address) kv.emplace_back("address", q(*d.address));
    if (d.ancestors) kv.emplace_back("ancestors", q(*d.ancestors));
    if (d.bankName) kv.emplace_back("bankName", q(*d.bankName));
    {
        // Java: private List<SysDept> children = new ArrayList<>() ⇒ 空数组也输出
        std::string v = "[";
        for (size_t i = 0; i < d.children.size(); ++i) {
            if (i) v += ',';
            v += sysDeptFastJson2(d.children[i]);
        }
        v += "]";
        kv.emplace_back("children", v);
    }
    appendBaseEntity(kv, d);
    if (d.dataId) kv.emplace_back("dataId", q(*d.dataId));
    if (d.deptJc) kv.emplace_back("deptJc", q(*d.deptJc));
    if (d.deptId) kv.emplace_back("deptId", nestedLong(*d.deptId));
    if (d.deptName) kv.emplace_back("deptName", q(*d.deptName));
    if (d.deptSubCode) kv.emplace_back("deptSubCode", q(*d.deptSubCode));
    if (d.delFlag) kv.emplace_back("delFlag", q(*d.delFlag));
    if (d.email) kv.emplace_back("email", q(*d.email));
    if (d.fgldId) kv.emplace_back("fgldId", nestedLong(*d.fgldId));
    if (d.fgldName) kv.emplace_back("fgldName", q(*d.fgldName));
    if (d.flag) kv.emplace_back("flag", q(*d.flag));
    if (d.isUint) kv.emplace_back("isUint", q(*d.isUint));
    if (d.isZbzg) kv.emplace_back("isZbzg", q(*d.isZbzg));
    if (d.leader) kv.emplace_back("leader", q(*d.leader));
    if (d.leaderId) kv.emplace_back("leaderId", nestedLong(*d.leaderId));
    if (d.orderNum) kv.emplace_back("orderNum", q(*d.orderNum));
    if (d.parentId) kv.emplace_back("parentId", nestedLong(*d.parentId));
    if (d.parentName) kv.emplace_back("parentName", q(*d.parentName));
    if (d.phone) kv.emplace_back("phone", q(*d.phone));
    if (d.postalCode) kv.emplace_back("postalCode", q(*d.postalCode));
    if (d.socialCode) kv.emplace_back("socialCode", q(*d.socialCode));
    if (d.status) kv.emplace_back("status", q(*d.status));
    if (d.subCode) kv.emplace_back("subCode", q(*d.subCode));
    if (d.tenantId) kv.emplace_back("tenantId", nestedLong(*d.tenantId));
    // Integer（不是 Long）：不带 L
    if (d.treeLeavel) kv.emplace_back("treeLeavel", std::to_string(*d.treeLeavel));
    return objOf(std::move(kv));
}

/** SysRole（嵌套层；boolean 默认值照写，Long 带 L） */
std::string sysRoleFastJson2(const SysRole& r) {
    std::vector<std::pair<std::string, std::string>> kv;
    kv.emplace_back("admin", r.isAdmin() ? "true" : "false");
    if (r.dataScope) kv.emplace_back("dataScope", q(*r.dataScope));
    if (r.delFlag) kv.emplace_back("delFlag", q(*r.delFlag));
    kv.emplace_back("deptCheckStrictly", r.deptCheckStrictly ? "true" : "false");
    if (r.deptIds && !r.deptIds->empty()) {
        std::string v = "[";
        for (size_t i = 0; i < r.deptIds->size(); ++i) {
            if (i) v += ',';
            // 数组元素（Long[]）不带 L，与 List<Long> 一致
            v += std::to_string((*r.deptIds)[i]);
        }
        v += "]";
        kv.emplace_back("deptIds", v);
    }
    kv.emplace_back("flag", r.flag ? "true" : "false");
    kv.emplace_back("menuCheckStrictly", r.menuCheckStrictly ? "true" : "false");
    if (r.menuIds && !r.menuIds->empty()) {
        std::string v = "[";
        for (size_t i = 0; i < r.menuIds->size(); ++i) {
            if (i) v += ',';
            v += std::to_string((*r.menuIds)[i]);
        }
        v += "]";
        kv.emplace_back("menuIds", v);
    }
    appendBaseEntity(kv, r);
    if (r.roleId) kv.emplace_back("roleId", nestedLong(*r.roleId));
    if (r.roleKey) kv.emplace_back("roleKey", q(*r.roleKey));
    if (r.roleName) kv.emplace_back("roleName", q(*r.roleName));
    if (r.roleSort) kv.emplace_back("roleSort", q(*r.roleSort));
    if (r.status) kv.emplace_back("status", q(*r.status));
    return objOf(std::move(kv));
}

/** SysUser（嵌套层）。键必须按字母序，且与 Java 的 47 个字段（含 BaseEntity）一一对应。 */
std::string sysUserFastJson2(const SysUser& u) {
    std::vector<std::pair<std::string, std::string>> kv;
    // primitive / 派生属性：默认值照写
    kv.emplace_back("admin", u.isAdmin() ? "true" : "false");
    kv.emplace_back("pjFlag", std::to_string(u.pjFlag));
    if (u.avatar) kv.emplace_back("avatar", q(*u.avatar));
    if (u.bussId) kv.emplace_back("bussId", q(*u.bussId));
    if (u.bussName) kv.emplace_back("bussName", q(*u.bussName));
    if (u.certEntityId) kv.emplace_back("certEntityId", q(*u.certEntityId));
    if (u.certId) kv.emplace_back("certId", q(*u.certId));
    if (u.confirmPassword) kv.emplace_back("confirmPassword", q(*u.confirmPassword));
    // BaseEntity
    if (u.createBy) kv.emplace_back("createBy", q(*u.createBy));
    if (u.createTime) kv.emplace_back("createTime", q(utils::DateUtils::formatJsonDate(u.createTime)));
    if (u.dataId) kv.emplace_back("dataId", q(*u.dataId));
    if (u.delFlag) kv.emplace_back("delFlag", q(*u.delFlag));
    if (u.dept) kv.emplace_back("dept", sysDeptFastJson2(*u.dept));
    if (u.deptId) kv.emplace_back("deptId", nestedLong(*u.deptId));
    if (u.deptName) kv.emplace_back("deptName", q(*u.deptName));
    if (u.email) kv.emplace_back("email", q(*u.email));
    if (u.epsName) kv.emplace_back("epsName", q(*u.epsName));
    if (u.excludeId) kv.emplace_back("excludeId", nestedLong(*u.excludeId));
    if (u.excludeSelf) kv.emplace_back("excludeSelf", *u.excludeSelf ? "true" : "false");
    if (u.flag) kv.emplace_back("flag", q(*u.flag));
    if (u.headOffice) kv.emplace_back("headOffice", *u.headOffice ? "true" : "false");
    if (u.imageId) kv.emplace_back("imageId", q(*u.imageId));
    if (u.loginDate) kv.emplace_back("loginDate", q(utils::DateUtils::formatJsonDate(u.loginDate)));
    if (u.loginIp) kv.emplace_back("loginIp", q(*u.loginIp));
    if (u.nickName) kv.emplace_back("nickName", q(*u.nickName));
    // params：Java 侧 new HashMap<>() 非 null，空 Map 也要写（带 @type）
    {
        std::string p = "{\"@type\":\"java.util.HashMap\"";
        if (u.params.is_object()) {
            for (auto it = u.params.begin(); it != u.params.end(); ++it) {
                p += "," + q(it.key()) + ":" + it.value().dump();
            }
        }
        p += "}";
        kv.emplace_back("params", p);
    }
    if (u.password) kv.emplace_back("password", q(*u.password));
    if (u.phonenumber) kv.emplace_back("phonenumber", q(*u.phonenumber));
    if (u.postIds && !u.postIds->empty()) {
        std::string v = "[";
        for (size_t i = 0; i < u.postIds->size(); ++i) {
            if (i) v += ',';
            v += nestedLong((*u.postIds)[i]);
        }
        v += "]";
        kv.emplace_back("postIds", v);
    }
    if (u.procurementManager) {
        kv.emplace_back("procurementManager", *u.procurementManager ? "true" : "false");
    }
    if (u.queryNickName) kv.emplace_back("queryNickName", q(*u.queryNickName));
    if (u.remark) kv.emplace_back("remark", q(*u.remark));
    if (u.roleCode) kv.emplace_back("roleCode", q(*u.roleCode));
    if (u.roleIds && !u.roleIds->empty()) {
        std::string v = "[";
        for (size_t i = 0; i < u.roleIds->size(); ++i) {
            if (i) v += ',';
            v += nestedLong((*u.roleIds)[i]);
        }
        v += "]";
        kv.emplace_back("roleIds", v);
    }
    if (u.roles && !u.roles->empty()) {
        std::string v = "[";
        for (size_t i = 0; i < u.roles->size(); ++i) {
            if (i) v += ',';
            v += sysRoleFastJson2((*u.roles)[i]);
        }
        v += "]";
        kv.emplace_back("roles", v);
    }
    if (u.salt) kv.emplace_back("salt", q(*u.salt));
    if (u.searchValue) kv.emplace_back("searchValue", q(*u.searchValue));
    if (u.sex) kv.emplace_back("sex", q(*u.sex));
    if (u.status) kv.emplace_back("status", q(*u.status));
    if (u.subCode) kv.emplace_back("subCode", q(*u.subCode));
    if (u.tenantId) kv.emplace_back("tenantId", nestedLong(*u.tenantId));
    if (u.tenantName) kv.emplace_back("tenantName", q(*u.tenantName));
    if (u.updateBy) kv.emplace_back("updateBy", q(*u.updateBy));
    if (u.updateTime) kv.emplace_back("updateTime", q(utils::DateUtils::formatJsonDate(u.updateTime)));
    if (u.userId) kv.emplace_back("userId", nestedLong(*u.userId));
    if (u.userName) kv.emplace_back("userName", q(*u.userName));
    if (u.userNo) kv.emplace_back("userNo", nestedLong(*u.userNo));
    if (u.userType) kv.emplace_back("userType", q(*u.userType));

    std::sort(kv.begin(), kv.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    std::string out = "{";
    bool first = true;
    for (const auto& [k, v] : kv) {
        if (!first) out += ',';
        first = false;
        out += q(k) + ":" + v;
    }
    out += '}';
    return out;
}

} // namespace

std::string loginUserToFastJson2(const LoginUser& u) {
    // 键集 = 10 个字段（null 省略）+ 5 个 getter 派生属性（getAuthorities() 返回 null，不输出）
    std::vector<std::pair<std::string, std::string>> kv;
    // 派生：UserDetails 的四个布尔，恒 true
    kv.emplace_back("accountNonExpired", "true");
    kv.emplace_back("accountNonLocked", "true");
    kv.emplace_back("credentialsNonExpired", "true");
    kv.emplace_back("enabled", "true");
    if (u.browser) kv.emplace_back("browser", q(*u.browser));
    // 根层 boxed Long 不带 L（实测 fastjson2 行为）
    if (u.expireTime) kv.emplace_back("expireTime", rootLong(u.expireTime));
    if (u.ipaddr) kv.emplace_back("ipaddr", q(*u.ipaddr));
    if (u.loginLocation) kv.emplace_back("loginLocation", q(*u.loginLocation));
    if (u.loginTime) kv.emplace_back("loginTime", rootLong(u.loginTime));
    if (u.os) kv.emplace_back("os", q(*u.os));
    // Set -> Set[...]；空集也输出 Set[]
    {
        std::string v = "Set[";
        bool first = true;
        for (const auto& p : u.permissions) {
            if (!first) v += ',';
            first = false;
            v += q(p);
        }
        v += "]";
        kv.emplace_back("permissions", v);
    }
    if (u.sessionId) kv.emplace_back("sessionId", q(*u.sessionId));
    if (u.token) kv.emplace_back("token", q(*u.token));
    kv.emplace_back("user", sysUserFastJson2(u.user));
    // 派生：getUsername() -> user.getUserName()
    if (u.user.userName) kv.emplace_back("username", q(*u.user.userName));
    // 派生：getPassword() -> user.getPassword()，null 时整个键省略

    std::sort(kv.begin(), kv.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    std::string out = "{\"@type\":\"com.ruoyi.common.core.domain.model.LoginUser\"";
    for (const auto& [k, v] : kv) out += "," + q(k) + ":" + v;
    out += '}';
    return out;
}

std::string fastJson2ToJson(const std::string& text) {
    // 复用通用的 fastjson2 规范化（Set[...] / ArrayList[...] / JSONObject{...} / 1L / 1.5F / 1.5D），
    // 不在这里另写一份：两套实现漂移会直接导致"Java 写的值某天读不出来"
    return cm::utils::normalizeFastJson2(text);
}

LoginUser loginUserFromFastJson2(const std::string& text) {
    LoginUser u;
    try {
        u = LoginUser::fromJson(cm::utils::parse_cached_json(text));
    } catch (...) {
        // 解析失败按"无登录态"处理（与 Redis 里没有该键等价）
    }
    return u;
}

} // namespace cm::domain
