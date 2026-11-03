#pragma once
// 对应 Java: com.ruoyi.common.constant.ScheduleConstants
//
// 这里只迁移被实际引用到的 Status 取值；其余字段（MISFIRE_POLICY_* / REQUEST_*）
// 是给 Quartz 调度器用的，C++ 侧没有调度器，加了就是死代码。
namespace cm::constant {

struct ScheduleConstants {
    /** 正常（对应 Java Status.NORMAL） */
    static constexpr const char* NORMAL = "0";
    /** 暂停（对应 Java Status.PAUSE） */
    static constexpr const char* PAUSE = "1";
};

} // namespace cm::constant
