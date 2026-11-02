#pragma once
// 对应 Java: com.ruoyi.common.constant.UserConstants
#include <string>

namespace cm::constant {

struct UserConstants {
    /** 校验返回结果码 */
    static constexpr const char* UNIQUE_OLD = "0";
    static constexpr const char* NOT_UNIQUE_OLD = "1";
    /** 是否为系统默认（是） */
    static constexpr const char* YES = "Y";
    static constexpr const char* NO = "N";
    /** 正常状态 */
    static constexpr const char* NORMAL = "0";
    /** 异常状态 */
    static constexpr const char* EXCEPTION = "1";
};

} // namespace cm::constant
