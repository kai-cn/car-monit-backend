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
    /** 部门状态：停用（Java UserConstants.DEPT_DISABLE） */
    static constexpr const char* DEPT_DISABLE = "1";
    // 与 Java UserConstants 一致：YES_FRAME="0" / NO_FRAME="1"（is_frame 列的取值语义反直觉，
    // 但这是 RuoYi 的定义，菜单外链判定用的就是它）
    static constexpr const char* YES_FRAME = "0";
    static constexpr const char* NO_FRAME = "1";
    static constexpr const char* NO = "N";
    /** 正常状态 */
    static constexpr const char* NORMAL = "0";
    /** 异常状态 */
    static constexpr const char* EXCEPTION = "1";
};

} // namespace cm::constant
