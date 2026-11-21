// GenUtils 的纯函数单测：映射表、驼峰规则、htmlType 覆盖链。
// 这些都不需要数据库，所以可以钉死；报告里的"worked cases"逐条对上。
#include "cm/web/controller/tool/GenUtils.hpp"

#include <stdexcept>
#include <string>

extern int g_fails;
#define fails g_fails
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++fails;                                                       \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                            \
    do {                                                                       \
        auto _va = (a);                                                        \
        auto _vb = (b);                                                        \
        if (!(_va == _vb)) {                                                   \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                           \
        }                                                                      \
    } while (0)

using namespace cm::gen;

static std::string javaTypeOf(const std::string& columnType) {
    return initColumnField("some_col", columnType, false).javaType;
}
static std::string htmlTypeOf(const std::string& columnName, const std::string& columnType) {
    return initColumnField(columnName, columnType, false).htmlType;
}

static void testCamelCase() {
    // toCamelCase：无下划线**原样返回**（大小写不动）
    CK_EQ(toCamelCase("USER_NAME"), std::string("userName"));
    CK_EQ(toCamelCase("del_flag"), std::string("delFlag"));
    CK_EQ(toCamelCase("userId"), std::string("userId"));
    CK_EQ(toCamelCase("ID"), std::string("ID"));
    CK_EQ(toCamelCase(""), std::string(""));
    // convertToCamelCase：无下划线只把首字母大写、其余保留
    CK_EQ(convertToCamelCase("userName"), std::string("UserName"));
    CK_EQ(convertToCamelCase("sys_user"), std::string("SysUser"));
    CK_EQ(convertToCamelCase("user_NAME"), std::string("UserName"));   // 每段其余字符会被小写
    CK_EQ(convertToCamelCase("a__b"), std::string("AB"));   // 空段被跳过
    CK_EQ(convertToCamelCase(""), std::string(""));
    // 两个函数对"无下划线"的处理不一致，是 Java 的原样行为
    CK(toCamelCase("userName") != convertToCamelCase("userName"));
}

static void testTypeParsing() {
    CK_EQ(getDbType("varchar(255)"), std::string("varchar"));
    CK_EQ(getDbType("decimal(10,2)"), std::string("decimal"));
    CK_EQ(getDbType("int"), std::string("int"));
    CK_EQ(getDbType("(int)"), std::string("(int)"));   // indexOf("(") > 0，位置 0 不算
    CK_EQ(getColumnLength("varchar(500)"), 500LL);
    CK_EQ(getColumnLength("int"), 0LL);
    bool threw = false;
    try {
        getColumnLength("decimal(10,2)");
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    CK(threw);   // Java 的 Integer.valueOf("10,2") 也是异常 → 500
}

static void testJavaTypeMapping() {
    CK_EQ(javaTypeOf("int"), std::string("Long"));            // 没有括号 ⇒ else
    CK_EQ(javaTypeOf("int(11)"), std::string("Long"));
    CK_EQ(javaTypeOf("int(10)"), std::string("Integer"));
    CK_EQ(javaTypeOf("int(4)"), std::string("Integer"));
    CK_EQ(javaTypeOf("bigint(20)"), std::string("Long"));
    CK_EQ(javaTypeOf("tinyint(1)"), std::string("Integer"));
    CK_EQ(javaTypeOf("decimal(10,2)"), std::string("BigDecimal"));
    CK_EQ(javaTypeOf("decimal(10,0)"), std::string("Long"));  // scale=0 ⇒ 两个分支都不成立
    CK_EQ(javaTypeOf("float"), std::string("Long"));
    CK_EQ(javaTypeOf("double(8,4)"), std::string("BigDecimal"));
    CK_EQ(javaTypeOf("varchar(64)"), std::string("String"));
    CK_EQ(javaTypeOf("datetime"), std::string("Date"));
    CK_EQ(javaTypeOf("json"), std::string("String"));         // 未知类型不赋值，留默认
}

static void testHtmlType() {
    CK_EQ(htmlTypeOf("name", "varchar(100)"), std::string("input"));
    CK_EQ(htmlTypeOf("name", "varchar(500)"), std::string("textarea"));
    CK_EQ(htmlTypeOf("content", "longtext"), std::string("editor"));   // 覆盖链最后赢
    CK_EQ(htmlTypeOf("x", "text"), std::string("textarea"));
    CK_EQ(htmlTypeOf("x", "datetime"), std::string("datetime"));
    CK_EQ(htmlTypeOf("x", "json"), std::string(""));           // Java 压根没赋值
    // 覆盖链：status 在链头，会盖掉类型分支的结果（datetime 命名的 xxx_status 变 radio）
    CK_EQ(htmlTypeOf("order_status", "varchar(1)"), std::string("radio"));
    CK_EQ(htmlTypeOf("audit_status", "datetime"), std::string("radio"));
    CK_EQ(htmlTypeOf("car_type", "int(4)"), std::string("select"));
    CK_EQ(htmlTypeOf("sex", "char(1)"), std::string("select"));
    CK_EQ(htmlTypeOf("avatar_image", "varchar(255)"), std::string("imageUpload"));
    CK_EQ(htmlTypeOf("attach_file", "varchar(255)"), std::string("fileUpload"));
}

static void testFlags() {
    ColumnInit pk = initColumnField("id", "bigint(20)", true);
    CK_EQ(pk.isInsert, std::string("1"));       // 每一列都是 "1"，包括主键
    CK_EQ(pk.isEdit, std::string(""));          // 主键 + 在 NOT_EDIT 名单里 ⇒ 空（Java 从不写 "0"）
    CK_EQ(pk.isList, std::string(""));
    CK_EQ(pk.isQuery, std::string(""));
    CK_EQ(pk.javaField, std::string("id"));

    ColumnInit del = initColumnField("del_flag", "char(1)", false);
    CK_EQ(del.isEdit, std::string(""));
    CK_EQ(del.isList, std::string(""));
    CK_EQ(del.isQuery, std::string(""));
    CK_EQ(del.isInsert, std::string("1"));

    ColumnInit remark = initColumnField("remark", "varchar(500)", false);
    CK_EQ(remark.isEdit, std::string("1"));
    CK_EQ(remark.isList, std::string("1"));
    CK_EQ(remark.isQuery, std::string(""));     // 只在 NOT_QUERY 名单里
    CK_EQ(remark.htmlType, std::string("textarea"));

    ColumnInit nm = initColumnField("user_NAME", "varchar(50)", false);
    CK_EQ(nm.queryType, std::string("LIKE"));   // endsWithIgnoreCase
    CK_EQ(nm.javaField, std::string("userName"));   // toCamelCase 先整体小写
    ColumnInit other = initColumnField("car_no", "varchar(20)", false);
    CK_EQ(other.queryType, std::string(""));    // 唯一的 queryType 规则，没有 EQ/BETWEEN
}

static void testInitTable() {
    TableInit t = initTable("sys_user", "用户表", "admin");
    CK_EQ(t.className, std::string("SysUser"));         // autoRemovePre=false ⇒ sys_ 保留
    CK_EQ(t.packageName, std::string("com.ruoyi.manager"));
    CK_EQ(t.moduleName, std::string("manager"));
    CK_EQ(t.businessName, std::string("user"));
    CK_EQ(t.functionName, std::string("用户"));          // 删掉 '表'
    CK_EQ(t.functionAuthor, std::string("ruoyi"));
    CK_EQ(t.createBy, std::string("admin"));
    CK_EQ(replaceText("若依表 x"), std::string(" x"));
    CK_EQ(getBusinessName("nounder"), std::string("nounder"));
    CK_EQ(getModuleName("nodots"), std::string("nodots"));
    CK_EQ(initTable("car_info", "", "u").functionName, std::string(""));
}

void run_gen_utils_tests() {
    testCamelCase();
    testTypeParsing();
    testJavaTypeMapping();
    testHtmlType();
    testFlags();
    testInitTable();
}
