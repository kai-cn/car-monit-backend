#pragma once
// 对应 Java: com.ruoyi.generator.util.GenUtils + GenConstants + GenConfig
//
// 这一层刻意做成**纯函数**：类型映射表、驼峰规则、htmlType 覆盖链都是从 GenUtils
// 逐行抄下来的，单测可以直接钉住（tests/gen_utils_test.cpp），不必连数据库才能验证。
//
// 配置值取自 ruoyi-generator/src/main/resources/generator.yml（@PropertySource 加载，
// GenConfig 用静态字段接）：author=ruoyi，packageName=com.ruoyi.manager，
// autoRemovePre=false，tablePrefix=sys_。autoRemovePre=false 意味着 tablePrefix 永不生效，
// 类名里保留 `sys_` 段 —— 这条如果按"合理预期"去删前缀就与 Java 不同了。
#include <string>
#include <vector>

namespace cm::gen {

extern const std::vector<std::string> kColumnTypeStr;    ///< char/varchar/nvarchar/varchar2
extern const std::vector<std::string> kColumnTypeText;   ///< tinytext/text/mediumtext/longtext
extern const std::vector<std::string> kColumnTypeTime;   ///< datetime/time/date/timestamp
extern const std::vector<std::string> kColumnTypeNumber; ///< tinyint…decimal
extern const std::vector<std::string> kColumnNameNotEdit;
extern const std::vector<std::string> kColumnNameNotList;
extern const std::vector<std::string> kColumnNameNotQuery;

/** StringUtils.toCamelCase：**没有下划线时原样返回（大小写不动）**；
 *  有下划线则整体转小写再把每个下划线后的首字母大写。USER_NAME->userName，但 ID->ID。 */
std::string toCamelCase(const std::string& s);

/** StringUtils.convertToCamelCase：**没有下划线时只把首字母大写、其余原样保留**（userName->UserName）；
 *  有下划线则按下划线切段、跳过空段、每段"首字母大写 + 其余小写"（user_NAME->User_name）。
 *  两个函数对"无下划线"的处理不一致，这是 Java 的原样行为。 */
std::string convertToCamelCase(const std::string& s);

std::string capitalize(const std::string& s);
std::string uncapitalize(const std::string& s);

/** columnType 里 '(' 在**位置 > 0** 时才截断（indexOf("(") > 0，不是 >= 0） */
std::string getDbType(const std::string& columnType);

/** 括号里的第一段；抛 std::invalid_argument 复现 Java 的 NumberFormatException
 *  （decimal(10,2) 走到这里就会炸，Java 也是 500） */
long long getColumnLength(const std::string& columnType);

/** RegExUtils.replaceAll(text, "(?:表|若依)", "")：删掉所有 '表' 字符和 '若依' 词 */
std::string replaceText(const std::string& text);

std::string getModuleName(const std::string& packageName);
std::string getBusinessName(const std::string& tableName);

/** initTable 的 7 个赋值（其余列保持 null，由 insertGenTable 的 <if> 跳过 ⇒ 落到 DDL 默认值） */
struct TableInit {
    std::string className;
    std::string packageName;
    std::string moduleName;
    std::string businessName;
    std::string functionName;   ///< tableComment 为 null 时保持空（对应 Java 的 null）
    std::string functionAuthor;
    std::string createBy;
};
TableInit initTable(const std::string& tableName, const std::string& tableComment,
                    const std::string& operName);

/** initColumnField 的产出。空串 = Java 那边是 null 或 ""，insert 的
 *  `<if test="x != null and x != ''">` 会把这一列整条省掉（不是写空串）。 */
struct ColumnInit {
    std::string javaField;
    std::string javaType;     ///< 恒有值：String / Long / Integer / BigDecimal / Date
    std::string isInsert;     ///< "1"（每一列都是）
    std::string isEdit;       ///< "1" 或空 —— 注意 Java 从不写 "0"
    std::string isList;
    std::string isQuery;
    std::string queryType;    ///< 只有 "LIKE" 或空
    std::string htmlType;     ///< 未知类型时是空（Java 连赋值都没做）
};

/** dataType 命中 STR∪TEXT / TIME / NUMBER / 其它 四条分支 + htmlType 覆盖链 + 三个 flag 表 */
ColumnInit initColumnField(const std::string& columnName, const std::string& columnType,
                           bool isPk);

} // namespace cm::gen
