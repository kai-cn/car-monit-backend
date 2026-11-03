// 迁移一致性单元测试（对应 Java 侧的 JUnit/断言）
#include <cmath>
#include <cstdio>
#include <string>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/core/domain/R.hpp"
#include "cm/common/core/page/TableDataInfo.hpp"
#include "cm/common/utils/CaptchaUtil.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/FastJson2Compat.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/JavaCollections.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/common/utils/sql/SqlUtil.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/http/HttpRequest.hpp"
#include "cm/framework/security/Jwt.hpp"
#include "cm/framework/security/SecurityUtils.hpp"

// 各测试文件共用的失败计数（tests/*.cpp 通过 extern 引用）
int g_fails = 0;
#define fails g_fails
#define CHECK(x)                                                          \
    do {                                                                  \
        if (!(x)) {                                                       \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);       \
            ++fails;                                                      \
        }                                                                 \
    } while (0)
#define CHECK_EQ(a, b)                                                        \
    do {                                                                      \
        auto _va = (a);                                                       \
        auto _vb = (b);                                                       \
        if (!(_va == _vb)) {                                                  \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b);\
            ++fails;                                                          \
        }                                                                     \
    } while (0)

/** 提取 JSON 对象的键顺序 */
static std::string keyOrder(const cm::Json& j) {
    std::string out;
    for (auto it = j.begin(); it != j.end(); ++it) {
        if (!out.empty()) out += ",";
        out += it.key();
    }
    return out;
}

static void testAjaxResultOrder() {
    auto a = cm::core::domain::AjaxResult::success();
    // Java HashMap(capacity 16) 桶序：msg(108501) 在 code(3059181) 之前
    CHECK_EQ(keyOrder(a.toJson()), std::string("msg,code"));
    CHECK_EQ(a.toJson().dump(), std::string("{\"msg\":\"操作成功\",\"code\":200}"));

    auto e = cm::core::domain::AjaxResult::error("boom");
    CHECK_EQ(keyOrder(e.toJson()), std::string("msg,code"));
    CHECK_EQ(e.toJson().dump(), std::string("{\"msg\":\"boom\",\"code\":500}"));

    auto withData = cm::core::domain::AjaxResult::success();
    withData.put("token", "t");
    CHECK(withData.toJson().contains("token"));
    CHECK_EQ(withData.toJson()["code"], 200);

    auto loginErr = cm::core::domain::AjaxResult::error(
        "对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！");
    CHECK_EQ(loginErr.code(), 500);
}

static void testTableDataInfoOrder() {
    cm::core::page::TableDataInfo t(cm::Json::array(), 7);
    CHECK_EQ(keyOrder(t.toJson()), std::string("total,rows,code,msg"));
    // Java BaseController.getDataTable 会统一填 code=200 / msg=查询成功
    CHECK_EQ(t.toJson().dump(), std::string("{\"total\":7,\"rows\":[],\"code\":200,\"msg\":\"查询成功\"}"));
}

static void testR() {
    auto r = cm::core::domain::R::ok();
    CHECK_EQ(keyOrder(r.toJson()), std::string("code,msg,data"));
    CHECK_EQ(r.toJson().dump(), std::string("{\"code\":200,\"msg\":\"操作成功\",\"data\":null}"));
}

static void testJavaHashAndSetOrder() {
    CHECK_EQ(cm::utils::javaStringHash("code"), 3059181);
    CHECK_EQ(cm::utils::javaStringHash("msg"), 108417);
    auto ordered = cm::utils::javaSetOrder({"b", "a", "c"});
    CHECK_EQ(ordered.size(), size_t(3));
    // Java HashSet 迭代顺序应与插入顺序无关而同哈希有关
    auto ordered2 = cm::utils::javaSetOrder({"c", "a", "b"});
    CHECK(ordered == ordered2);
}

static void testJwt() {
    // jjwt 把 secret 当作 Base64 解码：26 个字符（无填充）-> 19 字节，末尾组补零输出
    auto key = cm::security::Jwt::decodeJavaBase64("abcdefghijklmnopqrstuvwxyz");
    CHECK(key.has_value());
    CHECK_EQ(key->size(), size_t(19));
    static const unsigned char expect[19] = {0x69, 0xb7, 0x1d, 0x79, 0xf8, 0x21, 0x8a, 0x39, 0x25,
                                             0x9a, 0x7a, 0x29, 0xaa, 0xbb, 0x2d, 0xba, 0xfc, 0x31,
                                             0xcb};
    CHECK(std::string(reinterpret_cast<const char*>(expect), 19) == *key);

    cm::security::Jwt jwt("abcdefghijklmnopqrstuvwxyz");
    std::string token = jwt.createToken("6f9b3c0e-1d2a-4f3b-9c8d-0a1b2c3d4e5f");
    CHECK(!token.empty());
    auto uuid = jwt.parseLoginUserKey(token);
    CHECK(uuid.has_value());
    CHECK_EQ(uuid.value_or(""), std::string("6f9b3c0e-1d2a-4f3b-9c8d-0a1b2c3d4e5f"));

    // 篡改签名必须失败
    std::string bad = token;
    bad.back() = (bad.back() == 'A') ? 'B' : 'A';
    CHECK(!jwt.parseLoginUserKey(bad).has_value());

    // header 必须是 {"alg":"HS512"}
    auto dot = token.find('.');
    CHECK(dot != std::string::npos);
    auto hdr = cm::security::Jwt::base64UrlDecode(token.substr(0, dot));
    CHECK(hdr.has_value());
    CHECK_EQ(hdr.value_or(""), std::string("{\"alg\":\"HS512\"}"));
}

static void testDateFormats() {
    // 2024-05-17 14:15:52 +08:00 == 1715926552000
    long long ms = 1715926552000LL;
    CHECK_EQ(cm::utils::DateUtils::formatJsonDate(ms), std::string("2024-05-17 14:15:52"));
    CHECK_EQ(cm::utils::DateUtils::formatIsoDate(ms),
             std::string("2024-05-17T14:15:52.000+08:00"));
    CHECK_EQ(cm::utils::DateUtils::parseDbDateTime("2024-05-17 14:15:52").value_or(0), ms);
}

static void testSqlEscape() {
    CHECK_EQ(cm::db::Db::lit(std::string("a'b")), std::string("'a\\'b'"));
    CHECK_EQ(cm::db::Db::lit(std::string("a\\b")), std::string("'a\\\\b'"));
    CHECK_EQ(cm::db::Db::lit(std::string("x\ny")), std::string("'x\\ny'"));
    CHECK_EQ(cm::db::Db::litNull(), std::string("NULL"));
    auto lst = cm::db::Db::inList(std::vector<long long>{1, 2});
    CHECK_EQ(lst, std::string("(1,2)"));
}

static void testSqlUtil() {
    CHECK(cm::utils::sql::SqlUtil::isValidOrderBySql("create_time desc"));
    CHECK(!cm::utils::sql::SqlUtil::isValidOrderBySql("a;drop"));
    bool threw = false;
    try {
        cm::utils::sql::SqlUtil::escapeOrderBySql("a;drop");
    } catch (const std::exception&) {
        threw = true;
    }
    CHECK(threw);
    CHECK_EQ(cm::utils::sql::SqlUtil::escapeOrderBySql("create_time desc"),
             std::string("create_time desc"));
}

static void testPasswordMatch() {
    // BCrypt 校验（Java BCryptPasswordEncoder 同源）
    CHECK(cm::security::SecurityUtils::matchesPassword(
        "admin123", "$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2"));
    CHECK(!cm::security::SecurityUtils::matchesPassword(
        "wrong", "$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2"));
}

static void testFastJson2Compat() {
    // Java 侧 FastJson2JsonRedisSerializer(WriteClassName) 写出的会话值不是严格 JSON：
    // 集合带 Set[] 前缀、Long 带 L 后缀、Map 带 @type。C++ 必须读得懂，否则 401。
    const std::string java =
        R"({"@type":"com.ruoyi.common.core.domain.model.LoginUser","permissions":Set["*:*:*"],)"
        R"("deptId":25367L,"tenantId":-1L,"expireTime":1793674574544,)"
        R"("password":"$2a$10$3ylyFvNhQQtBg/n2RkeT..B7RIm8vge70pOvZ.ZY15ZoNcfPiT1OK",)"
        R"("params":{"@type":"java.util.HashMap"},"admin":true,"flag":false,"note":null})";
    cm::Json j = cm::utils::parse_cached_json(java);
    CHECK_EQ(j["permissions"].dump(), std::string("[\"*:*:*\"]"));
    CHECK_EQ(j["deptId"].get<long long>(), 25367LL);
    CHECK_EQ(j["tenantId"].get<long long>(), -1LL);
    CHECK_EQ(j["expireTime"].get<long long>(), 1793674574544LL);
    CHECK(j["admin"].get<bool>());
    CHECK(!j["flag"].get<bool>());
    CHECK(j["note"].is_null());
    // 字符串字面量里的 1L / Set[ 一律不许动
    CHECK_EQ(cm::utils::normalizeFastJson2(R"({"b":"1L","c":"Set[","a":1L})"),
             std::string(R"({"b":"1L","c":"Set[","a":1})"));
    // true/false/null 是 JSON 字面量，不能被当成类型前缀
    CHECK_EQ(cm::utils::normalizeFastJson2("[true,false,null]"), std::string("[true,false,null]"));
    // 已经是严格 JSON 时逐字节不变
    CHECK_EQ(cm::utils::normalizeFastJson2(R"({"a":[1,2],"b":3.5})"),
             std::string(R"({"a":[1,2],"b":3.5})"));
}

static void testSimpleMatch() {
    CHECK(cm::security::SecurityUtils::simpleMatch("system:user:*", "system:user:list"));
    // PatternMatchUtils 只做 * / ? 通配，不识别 ":"，故 "*:*:*" 不匹配无冒号串
    CHECK(!cm::security::SecurityUtils::simpleMatch("*:*:*", "anything"));
    CHECK(!cm::security::SecurityUtils::simpleMatch("system:user:list", "system:user:add"));
    CHECK(cm::security::SecurityUtils::simpleMatch("*", "anything"));
}

static void testIds() {
    auto u = cm::utils::uuid();
    CHECK_EQ(u.size(), size_t(36));
    auto s = cm::utils::simpleUuid();
    CHECK_EQ(s.size(), size_t(32));
    CHECK(!cm::utils::internalIp("8.8.8.8"));
    CHECK(cm::utils::internalIp("127.0.0.1"));
    CHECK(cm::utils::internalIp("192.168.1.5"));
    CHECK(cm::utils::internalIp("10.0.0.1"));
    CHECK(cm::utils::internalIp("172.20.1.1"));
    CHECK(!cm::utils::internalIp("172.36.1.1"));
}

static void testCaptcha() {
    for (int i = 0; i < 200; ++i) {
        auto c = cm::utils::CaptchaUtil::randomMath();
        CHECK(!c.text.empty());
        CHECK(!c.code.empty());
        CHECK(c.text.find("=?") != std::string::npos);
    }
    auto png = cm::utils::CaptchaUtil::renderPng("3*5=?");
    CHECK(png.size() > 100);
    // PNG magic
    CHECK(static_cast<unsigned char>(png[0]) == 0x89);
    CHECK(png.substr(1, 3) == "PNG");
}

static void testStringUtils() {
    CHECK_EQ(cm::utils::StringUtils::toUnderScoreCase("createTime"), std::string("create_time"));
    CHECK(cm::utils::StringUtils::isBlank(std::string("   ")));
    CHECK(!cm::utils::StringUtils::isBlank(std::string("x")));
}

/** 请求 URI 的百分号解码：Tomcat/Spring 会把路径解码后交给 @PathVariable，C++ 必须一致 */
static void testUrlDecode() {
    CHECK_EQ(cm::http::HttpRequest::urlDecode("%20"), std::string(" "));
    CHECK_EQ(cm::http::HttpRequest::urlDecode("/profile/a%20b.jpeg"), std::string("/profile/a b.jpeg"));
    CHECK_EQ(cm::http::HttpRequest::urlDecode("%E4%BA%91AK7388"), std::string("云AK7388"));
    CHECK_EQ(cm::http::HttpRequest::urlDecode("a+b"), std::string("a b"));  // 查询串：+ 是空格
    CHECK_EQ(cm::http::HttpRequest::percentDecode("a+b", false), std::string("a+b"));  // 路径：+ 原样
    CHECK_EQ(cm::http::HttpRequest::percentDecode("/p/a%20b.jpeg", false), std::string("/p/a b.jpeg"));
    CHECK_EQ(cm::http::HttpRequest::urlDecode("100%"), std::string("100%"));  // 残缺转义原样保留
    std::vector<std::pair<std::string, std::string>> params;
    cm::http::HttpRequest::parseUrlEncoded("carNo=%E4%BA%91AK7388&status=0", params);
    CHECK_EQ(params.size(), size_t(2));
    CHECK_EQ(params[0].first, std::string("carNo"));
    CHECK_EQ(params[0].second, std::string("云AK7388"));
    CHECK_EQ(params[1].second, std::string("0"));
}

void run_crypto_tests();
void run_crud_engine_tests();

int main() {
    testAjaxResultOrder();
    testTableDataInfoOrder();
    testR();
    testJavaHashAndSetOrder();
    testJwt();
    testDateFormats();
    testSqlEscape();
    testSqlUtil();
    testPasswordMatch();
    testFastJson2Compat();
    testSimpleMatch();
    testIds();
    testCaptcha();
    testStringUtils();
    testUrlDecode();
    run_crypto_tests();
    run_crud_engine_tests();
    if (fails == 0) {
        std::printf("ALL TESTS PASSED\n");
        return 0;
    }
    std::printf("%d test(s) failed\n", fails);
    return 1;
}
