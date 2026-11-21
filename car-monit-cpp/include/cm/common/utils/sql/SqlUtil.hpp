#pragma once
// 对应 Java: com.ruoyi.common.utils.sql.SqlUtil
#include <regex>
#include <string>
#include <vector>

#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/StringUtils.hpp"

namespace cm::utils::sql {

class SqlUtil {
public:
    /** 仅支持字母、数字、下划线、空格、逗号、小数点（支持多个字段排序） */
    static bool isValidOrderBySql(const std::string& value) {
        static const std::regex pattern("[a-zA-Z0-9_ \\,\\.]+");
        return std::regex_match(value, pattern);
    }

    static std::string escapeOrderBySql(const std::string& value) {
        if (!value.empty() && !isValidOrderBySql(value)) {
            throw cm::exception::UtilException("参数不符合规范，不能进行查询");
        }
        if (value.size() > 500) {
            throw cm::exception::UtilException("参数已超过最大限制，不能进行查询");
        }
        return value;
    }

    static void filterKeyword(const std::string& value) {
        if (value.empty()) return;
        static const std::vector<std::string> keywords = {
            "and ", "extractvalue", "updatexml", "exec ", "insert ", "select ", "delete ", "update ",
            "drop ", "count ", "chr ", "mid ", "master ", "truncate ", "char ", "declare ", "or ", "+",
            "user()"};
        std::string lower = StringUtils::toLower(value);
        for (const auto& k : keywords) {
            if (lower.find(k) != std::string::npos) {
                throw cm::exception::UtilException("参数存在SQL注入风险");
            }
        }
    }
};

} // namespace cm::utils::sql
