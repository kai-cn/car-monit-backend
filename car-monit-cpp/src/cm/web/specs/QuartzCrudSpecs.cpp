// 由 scripts/gen_crud_spec.py 生成（area=quartz）。
// 重新生成: python scripts/gen_crud_spec.py --area quartz
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

void registerQuartzArea(Router& r) {
    {
        // ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJob.java
        // ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml
        Spec s;
        s.table = "sys_job";
        s.alias = "t";
        s.fields = {
            {"jobId", "job_id", Fmt::Long, Cond::None, "任务序号", false, false},
            {"jobName", "job_name", Fmt::Str, Cond::Eq, "任务名称", false, false},
            {"jobGroup", "job_group", Fmt::Str, Cond::Eq, "任务组名", false, false},
            {"invokeTarget", "invoke_target", Fmt::Str, Cond::Eq, "调用目标字符串", false, false},
            {"cronExpression", "cron_expression", Fmt::Str, Cond::Eq, "执行表达式 ", false, false},
            {"concurrent", "concurrent", Fmt::Str, Cond::Eq, "并发执行", false, false},
            {"status", "status", Fmt::Str, Cond::Eq, "任务状态", false, false},
        };
        s.excelSheetName = "定时任务";
        Perms p;
        p.list = "monitor:job:list";
        p.query = "monitor:job:query";
        registerCrud(r, "/monitor/job", s, p, "jobId");
    }
    {
        // ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJobLog.java
        // ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml
        Spec s;
        s.table = "sys_job_log";
        s.alias = "t";
        s.fields = {
            {"jobLogId", "job_log_id", Fmt::Long, Cond::None, "日志序号", false, false},
            {"jobName", "job_name", Fmt::Str, Cond::Like, "任务名称", false, false},
            {"jobGroup", "job_group", Fmt::Str, Cond::Eq, "任务组名", false, false},
            {"invokeTarget", "invoke_target", Fmt::Str, Cond::Like, "调用目标字符串", false, false},
            {"jobMessage", "job_message", Fmt::Str, Cond::None, "日志信息", false, false},
            {"status", "status", Fmt::Str, Cond::Eq, "执行状态", false, false},
            {"exceptionInfo", "exception_info", Fmt::Str, Cond::None, "异常信息", false, false},
        };
        s.orderBy = "create_time desc";
        s.excelSheetName = "任务调度日志";
        Perms p;
        p.list = "monitor:job:list";
        p.query = "monitor:job:query";
        registerCrud(r, "/monitor/jobLog", s, p, "id");
    }
}

} // namespace cm::web::crud
