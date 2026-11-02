#pragma once
// 对应 Java: com.ruoyi.common.core.page.PageDomain
#include <optional>
#include <string>

namespace cm::core::page {

class PageDomain {
public:
    std::optional<int> pageNum;
    std::optional<int> pageSize;
    std::optional<std::string> orderByColumn;
    std::string isAsc{"asc"};
    std::optional<bool> reasonable;

    std::string getOrderBy() const {
        if (!orderByColumn || orderByColumn->empty()) return "";
        return toUnderScoreCase(*orderByColumn) + " " + isAsc;
    }

    void setIsAsc(const std::string& v) {
        if (!v.empty()) {
            if (v == "ascending") isAsc = "asc";
            else if (v == "descending") isAsc = "desc";
            else isAsc = v;
        }
    }

    bool getReasonable() const { return reasonable.value_or(true); }

    static std::string toUnderScoreCase(const std::string& s);
};

} // namespace cm::core::page
