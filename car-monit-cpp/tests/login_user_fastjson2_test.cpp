// Redis 登录态的 fastjson2 兼容序列化：与 Java 侧 golden 逐字节对比 + 反向兼容 + 字段集守护
//
// golden 来源：tests/golden/login_user_fastjson2.json
//   由真实 ruoyi-common 编译产物 + fastjson2 2.0.43 生成，
//   调用与 FastJson2JsonRedisSerializer.serialize 完全一致：
//     JSON.toJSONString(loginUser, JSONWriter.Feature.WriteClassName)
#include <cstdio>
#include <fstream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "cm/common/core/domain/model/LoginUserFastJson2.hpp"

extern int g_fails;
#define fails g_fails
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++fails;                                                       \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                        \
    do {                                                                   \
        auto _va = (a);                                                    \
        auto _vb = (b);                                                    \
        if (!(_va == _vb)) {                                               \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                       \
        }                                                                  \
    } while (0)

namespace {

std::string readFile(const std::string& name) {
    std::ifstream in(std::string(CM_TEST_SOURCE_DIR) + "/tests/golden/" + name, std::ios::binary);
    if (!in) return std::string();
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

/** 与 golden 完全相同的一份 LoginUser（值必须逐字段对齐，否则字节比较没有意义） */
cm::domain::LoginUser goldenLoginUser() {
    cm::domain::LoginUser lu;
    lu.token = "e3b0c44298fc1c149afbf4c8996fb924";
    lu.sessionId = "6f1c2a9d-1111-2222-3333-444455556666";
    lu.loginTime = 1762500000000LL;
    lu.expireTime = 1762507200000LL;
    lu.ipaddr = "127.0.0.1";
    lu.loginLocation = "内网IP";
    lu.browser = "Chrome 11";
    lu.os = "Windows 10";
    lu.permissions = {"*:*:*"};

    cm::domain::SysUser& u = lu.user;
    u.userId = 1LL;
    u.deptId = 103LL;
    u.userName = "admin";
    u.nickName = "管理员";
    u.userType = "00";
    u.email = "admin@example.com";
    u.phonenumber = "13800000000";
    u.sex = "0";
    u.avatar = "";
    u.status = "0";
    u.delFlag = "0";
    u.loginIp = "127.0.0.1";
    u.loginDate = 1762500000000LL;
    u.createBy = "admin";
    u.createTime = 1762400000000LL;
    u.remark = "备注";

    cm::domain::SysDept d;
    d.deptId = 103LL;
    d.parentId = 100LL;
    d.ancestors = "0,100";
    d.deptName = "研发部门";
    d.orderNum = "1";
    d.leader = "若依";
    d.phone = "15888888888";
    d.email = "ry@qq.com";
    d.status = "0";
    d.delFlag = "0";
    d.createBy = "admin";
    d.createTime = 1762400000000LL;
    u.dept = d;

    cm::domain::SysRole r;
    r.roleId = 2LL;
    r.roleName = "普通角色";
    r.roleKey = "common";
    r.roleSort = "2";
    r.dataScope = "2";
    r.menuCheckStrictly = false;
    r.deptCheckStrictly = false;
    r.status = "0";
    r.delFlag = "0";
    r.flag = false;
    u.roles = std::vector<cm::domain::SysRole>{r};
    return lu;
}

/** 递归收集 JSON 的键名（含嵌套），用于"键集一致"断言 */
void collectKeys(const cm::Json& j, std::set<std::string>& out) {
    if (j.is_object()) {
        for (auto it = j.begin(); it != j.end(); ++it) {
            out.insert(it.key());
            collectKeys(it.value(), out);
        }
    } else if (j.is_array()) {
        for (const auto& e : j) collectKeys(e, out);
    }
}

void testGoldenBytes() {
    const std::string golden = readFile("login_user_fastjson2.json");
    CK(!golden.empty());
    if (golden.empty()) return;
    const std::string actual = cm::domain::loginUserToFastJson2(goldenLoginUser());
    // 逐字节相等。不一致时打印首个差异位置，便于定位
    if (actual != golden) {
        size_t i = 0;
        while (i < actual.size() && i < golden.size() && actual[i] == golden[i]) ++i;
        std::printf("FAIL golden mismatch at %zu\n  want: %s\n  got : %s\n", i,
                    golden.substr(i, 120).c_str(), actual.substr(i, 120).c_str());
        ++fails;
    }
    CK_EQ(actual.size(), golden.size());

    // 空 Set 用例
    const std::string emptyGolden = readFile("login_user_empty.json");
    CK(!emptyGolden.empty());
    cm::domain::LoginUser empty;
    empty.permissions.clear();
    CK_EQ(cm::domain::loginUserToFastJson2(empty), emptyGolden);
}

void testRoundTrip() {
    const std::string golden = readFile("login_user_fastjson2.json");
    if (golden.empty()) return;
    const cm::domain::LoginUser u = cm::domain::loginUserFromFastJson2(golden);
    CK_EQ(u.token.value_or(""), std::string("e3b0c44298fc1c149afbf4c8996fb924"));
    CK_EQ(u.loginTime.value_or(0), 1762500000000LL);
    CK_EQ(u.expireTime.value_or(0), 1762507200000LL);
    CK_EQ(u.browser.value_or(""), std::string("Chrome 11"));
    CK_EQ(u.loginLocation.value_or(""), std::string("内网IP"));
    CK(u.permissions.count("*:*:*") == 1);
    CK_EQ(u.user.userId.value_or(0), 1LL);
    CK_EQ(u.user.userName.value_or(""), std::string("admin"));
    CK_EQ(u.user.nickName.value_or(""), std::string("管理员"));
    // 嵌套 Long 带 L、Date 是 "yyyy-MM-dd HH:mm:ss" 字符串，都必须能读回
    CK_EQ(u.user.deptId.value_or(0), 103LL);
    CK_EQ(u.user.createTime.value_or(0), 1762400000000LL);
    CK_EQ(u.user.loginDate.value_or(0), 1762500000000LL);
    CK(u.user.dept.has_value());
    CK_EQ(u.user.dept->deptName.value_or(""), std::string("研发部门"));
    CK(u.user.roles.has_value() && u.user.roles->size() == 1);
    if (u.user.roles && !u.user.roles->empty()) {
        CK_EQ((*u.user.roles)[0].roleKey.value_or(""), std::string("common"));
        CK_EQ((*u.user.roles)[0].roleId.value_or(0), 2LL);
    }

    // 空 Set 用例：permissions 必须是空集合而不是解析失败
    const std::string emptyGolden = readFile("login_user_empty.json");
    if (!emptyGolden.empty()) {
        const cm::domain::LoginUser e = cm::domain::loginUserFromFastJson2(emptyGolden);
        CK(e.permissions.empty());
        CK(!e.user.userId.has_value());
    }
}

void testKeySets() {
    const std::string golden = readFile("login_user_fastjson2.json");
    if (golden.empty()) return;
    cm::Json want;
    cm::Json got;
    try {
        want = cm::Json::parse(cm::domain::fastJson2ToJson(golden));
        got = cm::Json::parse(cm::domain::fastJson2ToJson(
            cm::domain::loginUserToFastJson2(goldenLoginUser())));
    } catch (...) {
        CK(false);
        return;
    }
    std::set<std::string> wantKeys, gotKeys;
    collectKeys(want, wantKeys);
    collectKeys(got, gotKeys);
    CK(wantKeys == gotKeys);
}

/** 字段集守护：Java 字段总数/字段名集合 与 C++ 侧枚举必须一致。
 *  重新生成 golden 后如果 Java 加了字段而 C++ 没跟上，这里会失败。 */
void testFieldSets() {
    const std::string txt = readFile("login_user_fields.txt");
    CK(!txt.empty());
    if (txt.empty()) return;
    std::istringstream ss(txt);
    std::string line;
    int loginCount = -1, sysCount = -1;
    std::set<std::string> javaLogin, javaSys;
    bool inSys = false;
    while (std::getline(ss, line)) {
        // Java PrintWriter.println 在 Windows 上写 \r\n
        while (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind("LoginUser=", 0) == 0) {
            loginCount = std::stoi(line.substr(10));
            continue;
        }
        if (line.rfind("SysUser=", 0) == 0) {
            sysCount = std::stoi(line.substr(8));
            inSys = true;
            continue;
        }
        if (line.empty()) continue;
        if (inSys) javaSys.insert(line); else javaLogin.insert(line);
    }
    CK_EQ(loginCount, 10);
    CK_EQ(sysCount, 47);
    CK_EQ(javaLogin.size(), static_cast<size_t>(10));
    CK_EQ(javaSys.size(), static_cast<size_t>(47));

    // C++ LoginUser 的字段（与 include/.../LoginUser.hpp 一一对应）
    const std::set<std::string> cppLogin = {
        "token", "sessionId", "loginTime", "expireTime", "ipaddr",
        "loginLocation", "browser", "os", "permissions", "user"};
    CK(cppLogin == javaLogin);

    // C++ SysUser 的字段：40 个自身字段 + BaseEntity 7 个
    const std::set<std::string> cppSys = {
        "userId", "userNo", "deptId", "userName", "nickName", "userType", "email", "phonenumber",
        "sex", "avatar", "password", "confirmPassword", "salt", "status", "delFlag", "loginIp",
        "loginDate", "certId", "certEntityId", "bussId", "bussName", "epsName", "tenantId",
        "tenantName", "roleCode", "dept", "roles", "roleIds", "postIds", "flag", "dataId",
        "subCode", "queryNickName", "excludeSelf", "excludeId", "headOffice",
        "procurementManager", "deptName", "pjFlag", "imageId",
        // BaseEntity
        "searchValue", "createBy", "createTime", "updateBy", "updateTime", "remark", "params"};
    CK_EQ(cppSys.size(), static_cast<size_t>(47));
    CK(cppSys == javaSys);
}

} // namespace

void run_login_user_fastjson2_tests() {
    testGoldenBytes();
    testRoundTrip();
    testKeySets();
    testFieldSets();
}
