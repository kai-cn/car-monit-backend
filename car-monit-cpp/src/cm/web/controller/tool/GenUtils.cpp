// GenUtils 的 C++ 移植，逐行对照 ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java
// 与 com.ruoyi.common.constant.GenConstants。映射表全部按源码字面抄，不做"合理化"修正。
#include "cm/web/controller/tool/GenUtils.hpp"

#include <algorithm>
#include <cctype>
#include <stdexcept>

namespace cm::gen {
namespace {

std::string lowerAll(const std::string& s) {
    std::string o = s;
    for (auto& c : o) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return o;
}

bool endsWithIgnoreCase(const std::string& s, const std::string& suffix) {
    if (suffix.size() > s.size()) return false;
    return lowerAll(s.substr(s.size() - suffix.size())) == lowerAll(suffix);
}

} // namespace

const std::vector<std::string> kColumnTypeStr = {"char", "varchar", "nvarchar", "varchar2"};
const std::vector<std::string> kColumnTypeText = {"tinytext", "text", "mediumtext", "longtext"};
const std::vector<std::string> kColumnTypeTime = {"datetime", "time", "date", "timestamp"};
const std::vector<std::string> kColumnTypeNumber = {
    "tinyint", "smallint", "mediumint", "int", "number", "integer",
    "bit",     "bigint",    "float",     "double", "decimal", "dianis"};
// COLUMNNAME_NOT_EDIT / NOT_LIST / NOT_QUERY：匹配的是**数据库原始列名**（下划线小写），
// 且 Arrays.asList(...).contains() 是大小写敏感的。
const std::vector<std::string> kColumnNameNotEdit = {"id", "create_by", "create_time", "del_flag"};
const std::vector<std::string> kColumnNameNotList = {
    "id", "create_by", "create_time", "del_flag", "update_by", "update_time"};
const std::vector<std::string> kColumnNameNotQuery = {
    "id", "create_by", "create_time", "del_flag", "update_by", "update_time", "remark"};

std::string toCamelCase(const std::string& s) {
    if (s.find('_') == std::string::npos) return s;   // Java: 无下划线原样返回
    std::string o = lowerAll(s);
    for (size_t i = 0; i + 1 < o.size(); ++i) {
        if (o[i] == '_') {
            o.erase(i, 1);
            o[i] = static_cast<char>(std::toupper(static_cast<unsigned char>(o[i])));
        }
    }
    return o;
}

std::string convertToCamelCase(const std::string& s) {
    if (s.empty()) return s;
    if (s.find('_') == std::string::npos)
        return static_cast<char>(std::toupper(static_cast<unsigned char>(s[0]))) + s.substr(1);
    std::string out;
    size_t pos = 0;
    while (pos <= s.size()) {
        size_t next = s.find('_', pos);
        const std::string seg =
            s.substr(pos, next == std::string::npos ? std::string::npos : next - pos);
        if (!seg.empty())
            out += static_cast<char>(std::toupper(static_cast<unsigned char>(seg[0]))) +
                   lowerAll(seg.substr(1));
        if (next == std::string::npos) break;
        pos = next + 1;
    }
    return out;
}

std::string capitalize(const std::string& s) {
    if (s.empty()) return s;
    return static_cast<char>(std::toupper(static_cast<unsigned char>(s[0]))) + s.substr(1);
}

std::string uncapitalize(const std::string& s) {
    if (s.empty()) return s;
    return static_cast<char>(std::tolower(static_cast<unsigned char>(s[0]))) + s.substr(1);
}

std::string getDbType(const std::string& columnType) {
    const size_t p = columnType.find('(');
    if (p > 0 && p != std::string::npos) return columnType.substr(0, p);
    return columnType;
}

long long getColumnLength(const std::string& columnType) {
    const size_t open = columnType.find('(');
    if (open == 0 || open == std::string::npos) return 0;
    const size_t close = columnType.find(')', open);
    if (close == std::string::npos) return 0;
    const std::string inside = columnType.substr(open + 1, close - open - 1);
    // Integer.valueOf("10,2") 在 Java 里抛 NumberFormatException ⇒ 这里必须一样抛，
    // 不能用 stoll 的"遇非数字就停"语义（那会把 "10,2" 悄悄变成 10）
    size_t consumed = 0;
    long long v = 0;
    try {
        v = std::stoll(inside, &consumed);
    } catch (...) {
        throw std::invalid_argument("For input string: \"" + inside + "\"");
    }
    if (consumed != inside.size())
        throw std::invalid_argument("For input string: \"" + inside + "\"");
    return v;
}

std::string replaceText(const std::string& text) {
    // RegExUtils.replaceAll(text, "(?:表|若依)", "")：'表' 是单字符、'若依' 是双字词
    static const std::string kRuoyi = "\xE8\x8B\xA5\xE4\xBE\x9D";   // 若依
    static const std::string kBiao = "\xE8\xA1\xA8";                // 表
    std::string out;
    for (size_t i = 0; i < text.size();) {
        if (text.compare(i, kRuoyi.size(), kRuoyi) == 0) {
            i += kRuoyi.size();
            continue;
        }
        if (text.compare(i, kBiao.size(), kBiao) == 0) {
            i += kBiao.size();
            continue;
        }
        out.push_back(text[i++]);
    }
    return out;
}

std::string getModuleName(const std::string& packageName) {
    const size_t dot = packageName.rfind('.');
    if (dot == std::string::npos) return packageName;
    return packageName.substr(dot + 1);
}

std::string getBusinessName(const std::string& tableName) {
    const size_t us = tableName.rfind('_');
    if (us == std::string::npos) return tableName;
    return tableName.substr(us + 1);
}

TableInit initTable(const std::string& tableName, const std::string& tableComment,
                    const std::string& operName) {
    TableInit t;
    // GenConfig.autoRemovePre = false（generator.yml），所以永远不会删前缀
    t.className = convertToCamelCase(tableName);
    t.packageName = "com.ruoyi.manager";
    t.moduleName = getModuleName(t.packageName);
    t.businessName = getBusinessName(tableName);
    t.functionName = replaceText(tableComment);
    t.functionAuthor = "ruoyi";
    t.createBy = operName;
    return t;
}

ColumnInit initColumnField(const std::string& columnName, const std::string& columnType,
                           bool isPk) {
    ColumnInit c;
    const std::string dataType = getDbType(columnType);
    c.javaField = toCamelCase(columnName);
    c.javaType = "String";                       // 默认值
    c.isInsert = "1";                           // Java 对**每一列**都设 "1"，包括主键和 del_flag
    if (std::find(kColumnNameNotEdit.begin(), kColumnNameNotEdit.end(), columnName) ==
            kColumnNameNotEdit.end() && !isPk)
        c.isEdit = "1";
    if (std::find(kColumnNameNotList.begin(), kColumnNameNotList.end(), columnName) ==
            kColumnNameNotList.end() && !isPk)
        c.isList = "1";
    if (std::find(kColumnNameNotQuery.begin(), kColumnNameNotQuery.end(), columnName) ==
            kColumnNameNotQuery.end() && !isPk)
        c.isQuery = "1";
    if (endsWithIgnoreCase(columnName, "name")) c.queryType = "LIKE";   // 唯一的 queryType 规则

    const auto inList = [&](const std::vector<std::string>& v) {
        return std::find(v.begin(), v.end(), dataType) != v.end();   // 大小写敏感，按源码
    };

    if (inList(kColumnTypeStr) || inList(kColumnTypeText)) {
        long long len = 0;
        try {
            len = getColumnLength(columnType);
        } catch (const std::invalid_argument&) {
            // Java 在这里抛 NumberFormatException → 500。text 类不带括号，不会走到。
            throw;
        }
        c.htmlType = (len >= 500 || inList(kColumnTypeText)) ? "textarea" : "input";
    } else if (inList(kColumnTypeTime)) {
        c.javaType = "Date";
        c.htmlType = "datetime";
    } else if (inList(kColumnTypeNumber)) {
        c.htmlType = "input";
        const size_t open = columnType.find('(');
        const size_t close = columnType.find(')', open == std::string::npos ? 0 : open);
        if (open != std::string::npos && close != std::string::npos && close > open) {
            const std::string inside = columnType.substr(open + 1, close - open - 1);
            std::vector<std::string> parts;
            size_t pos = 0;
            while (pos <= inside.size()) {
                size_t comma = inside.find(',', pos);
                parts.push_back(inside.substr(
                    pos, comma == std::string::npos ? std::string::npos : comma - pos));
                if (comma == std::string::npos) break;
                pos = comma + 1;
            }
            const auto parseInt = [](const std::string& s) {
                size_t consumed = 0;
                try {
                    const long long v = std::stoll(s, &consumed);
                    if (consumed != s.size()) throw std::invalid_argument("");
                    return v;
                } catch (...) {
                    throw std::invalid_argument("For input string: \"" + s + "\"");
                }
            };
            if (parts.size() == 2 && parseInt(parts[1]) > 0) c.javaType = "BigDecimal";
            else if (parts.size() == 1 && parseInt(parts[0]) <= 10) c.javaType = "Integer";
            else c.javaType = "Long";
        } else {
            c.javaType = "Long";   // 没有括号：str == null ⇒ 两个分支都不成立 ⇒ else
        }
    }
    // 其它类型（json/enum/blob…）：javaType 留 String、htmlType **不赋值**（Java 没进任何分支）

    // htmlType 覆盖链：status 是链头，会盖掉上面类型分支的结果
    if (endsWithIgnoreCase(columnName, "status")) c.htmlType = "radio";
    else if (endsWithIgnoreCase(columnName, "type") || endsWithIgnoreCase(columnName, "sex"))
        c.htmlType = "select";
    else if (endsWithIgnoreCase(columnName, "image")) c.htmlType = "imageUpload";
    else if (endsWithIgnoreCase(columnName, "file")) c.htmlType = "fileUpload";
    else if (endsWithIgnoreCase(columnName, "content")) c.htmlType = "editor";
    return c;
}

} // namespace cm::gen
