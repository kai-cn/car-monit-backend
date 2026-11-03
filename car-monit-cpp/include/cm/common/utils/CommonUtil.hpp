#pragma once
// 对应 Java: com.ruoyi.common.utils.CommonUtil（ruoyi-common 模块，不是 web 下同名类）
//
// 这几个字符串工具在大屏/可疑车辆等接口里充当"参数过滤"的判定，
// 空参与非空参的分支结果差别很大，所以按 Java 逐行抄，不做"顺手改良"。
#include <string>

#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"

namespace cm::utils {

class CommonUtil {
public:
    /** 对应 CommonUtil.isNull(Object)：null -> ""，否则 toString().trim() */
    static std::string isNull(const Json& j, const std::string& key) {
        auto it = j.find(key);
        if (it == j.end() || it->is_null()) return std::string();
        if (it->is_string()) return StringUtils::trim(it->get<std::string>());
        return StringUtils::trim(it->dump());
    }

    static std::string isNull(const std::string& v) { return StringUtils::trim(v); }

    /** 对应 deleteEnd(Object)：只去掉**一个**结尾逗号（不是全部），并先 trim */
    static std::string deleteEnd(const std::string& v) {
        std::string s = isNull(v);
        if (!s.empty() && s.back() == ',') s.pop_back();
        return s;
    }

    /**
     * 对应 isExitsStr(sqlStr, paraStr)：数据串里是否包含参数串（逗号分隔）的任意一项。
     * ⚠️ 参数为空时返回 true（放行）；非空时按**子串**匹配，不是按整段相等匹配。
     */
    static bool isExitsStr(const std::string& sqlStr, const std::string& paraStr) {
        std::string para = deleteEnd(paraStr);
        const std::string data = isNull(sqlStr);
        if (StringUtils::isBlank(para)) return true;

        size_t pos = 0;
        while (true) {
            size_t comma = para.find(',', pos);
            std::string item = para.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
            // Java 是 data.indexOf(item) > -1：空串的 indexOf 返回 0，也算命中，
            // 所以 "a,,b" 这种带空项的参数会直接放行 —— 照抄，不"修正"
            if (data.find(item) != std::string::npos) return true;
            if (comma == std::string::npos) break;
            pos = comma + 1;
        }
        return false;
    }
};

} // namespace cm::utils
