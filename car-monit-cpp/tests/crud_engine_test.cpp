// CRUD 引擎的纯函数单测：不连数据库，直接把 Spec -> SQL/JSON 的翻译结果钉死。
// 这一层是 base/manager/flow 三个区域 400+ 个同构接口的共同实现，
// 它错了就是成片错，所以每条语义都单独断言。
#include <cstdio>
#include <string>
#include <vector>

#include "cm/framework/db/Row.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

extern int g_fails;
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++g_fails;                                                     \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                        \
    do {                                                                   \
        auto _va = (a);                                                    \
        auto _vb = (b);                                                    \
        if (!(_va == _vb)) {                                               \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b);  \
            ++g_fails;                                                     \
        }                                                                  \
    } while (0)

using namespace cm::web::crud;
using cm::Json;
using cm::web::Router;

static Spec demoSpec() {
    Spec s;
    s.table = "demo_table";
    s.alias = "t";
    s.fields = {
        {"id", "id", Fmt::Long, Cond::Eq, nullptr, true, false},
        {"name", "name", Fmt::Str, Cond::Like, "名称", false, false},
        {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false},
        {"score", "score", Fmt::Double, Cond::None, "得分", false, false},
        {"deleted", "is_deleted", Fmt::Int, Cond::None, nullptr, false, false},
        {"createTime", "create_time", Fmt::DateYmdHms, Cond::DateRange, "创建时间", false, false},
    };
    s.orderBy = "t.create_time desc";
    s.excelSheetName = "示例";
    return s;
}

static void testSelectAndPk() {
    Spec s = demoSpec();
    CK_EQ(s.pkColumn(), std::string("id"));
    CK_EQ(s.pkJson(), std::string("id"));
    CK(!s.pkIsString());
    CK_EQ(s.selectColumns(),
          std::string("t.id, t.name, t.status, t.score, t.is_deleted, t.create_time"));
    CK_EQ(pkLiteral(s, "12"), std::string("12"));
    s.fields[0].fmt = Fmt::Str;  // 主键换成字符串（如 agent_pk）
    CK(s.pkIsString());
    CK_EQ(pkLiteral(s, "A'B"), std::string("'A\\'B'"));  // 必须走 Db::lit 转义
}

static void testBuildWhere() {
    const Spec s = demoSpec();

    Json q = Json::object();
    CK_EQ(buildWhere(s, q), std::string("WHERE 1=1"));

    // 空串不进 WHERE（对应 XML 的 <if test="x != null and x != ''">）
    q["name"] = "";
    CK_EQ(buildWhere(s, q), std::string("WHERE 1=1"));

    q["name"] = "abc";
    CK_EQ(buildWhere(s, q), std::string("WHERE 1=1 and t.name like concat('%', 'abc', '%')"));

    q["status"] = "0";
    CK(buildWhere(s, q).find("and t.status = '0'") != std::string::npos);

    // EqNotNull：只判 null，空串仍然是条件
    Spec s2 = demoSpec();
    s2.fields[2].cond = Cond::EqNotNull;
    Json q2 = Json::object();
    q2["status"] = "";
    CK_EQ(buildWhere(s2, q2), std::string("WHERE 1=1 and t.status = ''"));

    // 注入防护：所有值都必须经过转义
    Json q3 = Json::object();
    q3["status"] = std::string("x' or 1=1 --");
    const std::string w = buildWhere(s, q3);
    CK(w.find("or 1=1") == std::string::npos || w.find("\\'") != std::string::npos);
    CK(w.find("'x\\' or 1=1 --'") != std::string::npos);

    // 日期区间：params.beginTime / endTime
    Json q4 = Json::object();
    Json params = Json::object();
    params["beginTime"] = "2024-01-01";
    params["endTime"] = "2024-01-31";
    q4["params"] = params;
    const std::string w4 = buildWhere(s, q4);
    CK(w4.find("date_format(t.create_time, '%Y%m%d') >= date_format('2024-01-01', '%Y%m%d')") !=
       std::string::npos);
    CK(w4.find("<= date_format('2024-01-31', '%Y%m%d')") != std::string::npos);

    // Raw 风格
    Spec s5 = demoSpec();
    s5.rangeStyle = RangeStyle::Raw;
    CK(buildWhere(s5, q4).find("and t.create_time >= '2024-01-01'") != std::string::npos);

    // extraWhere 恒定附加（del_flag 之类）
    Spec s6 = demoSpec();
    s6.extraWhere = " and t.del_flag = '0'";
    CK_EQ(buildWhere(s6, Json::object()), std::string("WHERE 1=1 and t.del_flag = '0'"));

    // FindInSetCol：XML 写 find_in_set(t.id, #{exceptIds})，左值另有其列
    Spec s7 = demoSpec();
    s7.fields[2].cond = Cond::FindInSetCol;
    s7.fields[2].column = "except_ids";
    s7.fields[2].condColumn = "id";
    Json q7 = Json::object();
    q7["status"] = "1,2";
    CK_EQ(buildWhere(s7, q7),
          std::string("WHERE 1=1 and find_in_set(t.id, '1,2')"));
    // 没给 condColumn 时退化成取本列
    Spec s8 = s7;
    s8.fields[2].condColumn = nullptr;
    CK(buildWhere(s8, q7).find("find_in_set(t.except_ids, '1,2')") != std::string::npos);
}

static void testBuildInsert() {
    const Spec s = demoSpec();
    Json body = Json::object();
    body["name"] = "n1";
    body["score"] = 12.5;
    const std::string sql = buildInsert(s, body);
    CK_EQ(sql, std::string("INSERT INTO demo_table (name, score) VALUES ('n1', 12.5)"));

    // null 字段跳过（MyBatis-Plus 默认 NOT_NULL 策略）
    Json b2 = Json::object();
    b2["name"] = "n1";
    b2["status"] = nullptr;
    CK_EQ(buildInsert(s, b2), std::string("INSERT INTO demo_table (name) VALUES ('n1')"));

    // 空串照写（Java 侧空串不是 null）
    Json b3 = Json::object();
    b3["status"] = "";
    CK_EQ(buildInsert(s, b3), std::string("INSERT INTO demo_table (status) VALUES ('')"));

    // 自增主键不写入
    Spec s4 = demoSpec();
    s4.fields[0].autoIncrement = true;
    Json b4 = Json::object();
    b4["id"] = 7;
    b4["name"] = "x";
    CK_EQ(buildInsert(s4, b4), std::string("INSERT INTO demo_table (name) VALUES ('x')"));

    // 字符串主键 + IdType.INPUT：主键要写入
    Spec s5 = demoSpec();
    s5.fields[0].fmt = Fmt::Str;
    s5.fields[0].column = "agent_pk";
    s5.fields[0].json = "agentPk";
    Json b5 = Json::object();
    b5["agentPk"] = "PK-1";
    b5["name"] = "x";
    CK_EQ(buildInsert(s5, b5),
          std::string("INSERT INTO demo_table (agent_pk, name) VALUES ('PK-1', 'x')"));
}

static void testBuildUpdate() {
    const Spec s = demoSpec();
    Json body = Json::object();
    body["id"] = 3;
    body["name"] = "renamed";
    CK_EQ(buildUpdate(s, body), std::string("UPDATE demo_table SET name = 'renamed' WHERE id = 3"));

    // 没有主键 -> 空串（调用方据此报“修改失败”，等价 Java 不执行 updateById）
    Json noPk = Json::object();
    noPk["name"] = "x";
    CK_EQ(buildUpdate(s, noPk), std::string(""));

    // null 不更新；主键自身不出现在 SET 里
    Json b2 = Json::object();
    b2["id"] = 3;
    b2["name"] = nullptr;
    b2["status"] = "1";
    CK_EQ(buildUpdate(s, b2), std::string("UPDATE demo_table SET status = '1' WHERE id = 3"));

    // 全 null：生成无副作用语句，保持 affected rows 语义（Java 侧不会执行更新）
    Json b3 = Json::object();
    b3["id"] = 3;
    CK_EQ(buildUpdate(s, b3),
          std::string("UPDATE demo_table SET id = id WHERE id = 3"));
}

static void testRowToJson() {
    const Spec s = demoSpec();
    cm::db::Row row({"id", "name", "status", "score", "is_deleted", "create_time"},
                    {std::string("7"), std::string("货车"), std::string("0"), std::string("12.50"),
                     std::nullopt, std::string("2024-05-17 14:15:52")});
    Json j = rowToJson(s, row);
    CK_EQ(j["id"], 7);
    CK_EQ(j["name"], std::string("货车"));
    CK_EQ(j["score"], 12.5);
    CK(j["deleted"].is_null());  // DB NULL -> JSON null（不是 0，也不是 ""）
    CK_EQ(j["createTime"], std::string("2024-05-17 14:15:52"));

    // 字段顺序 = Java 声明顺序（Jackson 对 POJO 按声明序输出）
    std::string order;
    for (auto it = j.begin(); it != j.end(); ++it) {
        if (!order.empty()) order += ",";
        order += it.key();
    }
    CK_EQ(order, std::string("id,name,status,score,deleted,createTime"));

    // NULL 数字列不能变成 0
    cm::db::Row row2({"id", "name", "status", "score", "is_deleted", "create_time"},
                     {std::nullopt, std::nullopt, std::nullopt, std::nullopt, std::nullopt,
                      std::nullopt});
    Json j2 = rowToJson(s, row2);
    CK(j2["id"].is_null());
    CK(j2["score"].is_null());
    CK(j2["createTime"].is_null());
}

static void testRouteShape() {
    // 路由匹配顺序：/list /export 不能被 /{id} 吞掉（Spring 字面量优先）
    Router r;
    Spec s = demoSpec();
    Perms p;
    p.list = "demo:list";
    p.query = "demo:query";
    registerCrud(r, "/demo", s, p, "id");

    auto m1 = r.match("GET", "/demo/list");
    CK(m1.matched);
    CK(m1.route != nullptr);
    if (m1.route) CK_EQ(m1.route->pattern, std::string("/demo/list"));

    auto m2 = r.match("GET", "/demo/export");
    CK(m2.matched);
    if (m2.route) CK_EQ(m2.route->pattern, std::string("/demo/export"));

    auto m3 = r.match("GET", "/demo/123");
    CK(m3.matched);
    if (m3.route) CK_EQ(m3.route->pattern, std::string("/demo/{id}"));
    CK_EQ(m3.path_vars.count("id") ? m3.path_vars.at("id") : std::string(""), std::string("123"));

    auto m4 = r.match("DELETE", "/demo/1,2,3");
    CK(m4.matched);
    if (m4.route) CK_EQ(m4.route->pattern, std::string("/demo/{id}"));

    // POST/PUT 打在 base 上
    CK(r.match("POST", "/demo").matched);
    CK(r.match("PUT", "/demo").matched);

    // 权限串落到路由元数据上
    auto list_route = r.match("GET", "/demo/list").route;
    CK(list_route != nullptr);
    if (list_route) {
        CK_EQ(list_route->required_perms.size(), size_t(1));
        if (!list_route->required_perms.empty()) {
            CK_EQ(list_route->required_perms[0], std::string("demo:list"));
        }
    }
    // add/edit/remove 没有给权限串 -> 不注册 permi（与 Java 无 @PreAuthorize 一致）
    auto add_route = r.match("POST", "/demo").route;
    CK(add_route != nullptr);
    if (add_route) CK(add_route->required_perms.empty());
}

void run_crud_engine_tests() {
    testSelectAndPk();
    testBuildWhere();
    testBuildInsert();
    testBuildUpdate();
    testRowToJson();
    testRouteShape();
}
