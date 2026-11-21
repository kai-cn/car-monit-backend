// 对应 Java: com.ruoyi.common.core.page.PageDomain 的静态工具
#include "cm/common/core/page/PageDomain.hpp"

#include "cm/common/utils/StringUtils.hpp"

namespace cm::core::page {

std::string PageDomain::toUnderScoreCase(const std::string& s) {
    return cm::utils::StringUtils::toUnderScoreCase(s);
}

} // namespace cm::core::page
