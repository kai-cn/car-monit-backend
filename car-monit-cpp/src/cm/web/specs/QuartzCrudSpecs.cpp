// 由 scripts/gen_crud_spec.py 生成（area=quartz）。
// 重新生成: python scripts/gen_crud_spec.py --area quartz
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
//
// 每个实体的 Spec 通过 spec<Entity>() 暴露（声明见 QuartzCrudSpecs.hpp），
// 手写控制器可以复用同一份列定义，避免把几十个字段再抄一遍。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/specs/QuartzCrudSpecs.hpp"

namespace cm::web::crud {

const Spec& specSysJob() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_job";
        s.alias = "t";
        s.fields = {
            {"createBy", "create_by", Fmt::Str, Cond::None, nullptr, false, false, true, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateBy", "update_by", Fmt::Str, Cond::Eq, nullptr, false, false, false, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", "remark", Fmt::Str, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"jobId", "job_id", Fmt::Long, Cond::None, "任务序号", false, false, true, false},
            {"jobName", "job_name", Fmt::Str, Cond::Eq, "任务名称", false, false, true, true},
            {"jobGroup", "job_group", Fmt::Str, Cond::Eq, "任务组名", false, false, true, true},
            {"invokeTarget", "invoke_target", Fmt::Str, Cond::Eq, "调用目标字符串", false, false, true, true},
            {"cronExpression", "cron_expression", Fmt::Str, Cond::Eq, "执行表达式 ", false, false, true, true},
            {"misfirePolicy", "misfire_policy", Fmt::Str, Cond::Eq, "计划策略 ", false, false, true, true},
            {"concurrent", "concurrent", Fmt::Str, Cond::Eq, "并发执行", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "任务状态", false, false, true, true},
        };
        s.excelSheetName = "定时任务";
        return s;
    }();
    return s;
}

const Spec& specSysJobLog() {
    static const Spec s = [] {
        Spec s;
        s.table = "sys_job_log";
        s.alias = "t";
        s.fields = {
            {"createBy", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::DateRange, nullptr, false, false, false, true, nullptr},
            {"updateBy", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateTime", nullptr, Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr},
            {"jobLogId", "job_log_id", Fmt::Long, Cond::None, "日志序号", false, false, true, true},
            {"jobName", "job_name", Fmt::Str, Cond::Like, "任务名称", false, false, true, true},
            {"jobGroup", "job_group", Fmt::Str, Cond::Eq, "任务组名", false, false, true, true},
            {"invokeTarget", "invoke_target", Fmt::Str, Cond::Like, "调用目标字符串", false, false, true, true},
            {"jobMessage", "job_message", Fmt::Str, Cond::None, "日志信息", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "执行状态", false, false, true, true},
            {"exceptionInfo", "exception_info", Fmt::Str, Cond::None, "异常信息", false, false, true, true},
            {"startTime", nullptr, Fmt::DateIso, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"stopTime", nullptr, Fmt::DateIso, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "create_time desc";
        s.excelSheetName = "任务调度日志";
        return s;
    }();
    return s;
}

void registerQuartzArea(Router& r) {
    {
        // ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJob.java
        // ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml
        Perms p;
        p.list = "monitor:job:list";
        p.query = "monitor:job:query";
        registerCrud(r, "/monitor/job", specSysJob(), p, "jobId");
    }
    {
        // ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJobLog.java
        // ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml
        Perms p;
        p.list = "monitor:job:list";
        p.query = "monitor:job:query";
        registerCrud(r, "/monitor/jobLog", specSysJobLog(), p, "id");
    }
}

} // namespace cm::web::crud
