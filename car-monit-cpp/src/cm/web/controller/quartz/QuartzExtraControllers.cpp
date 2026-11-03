// 对应 Java: com.ruoyi.quartz.controller.SysJobController#changeStatus / #run
//            com.ruoyi.quartz.controller.SysJobLogController#clean
#include "cm/web/controller/quartz/QuartzExtraControllers.hpp"

#include <cstdlib>
#include <string>

#include "cm/common/constant/ScheduleConstants.hpp"
#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::constant::ScheduleConstants;
using cm::core::domain::AjaxResult;
using cm::db::Db;

} // namespace

void registerQuartzExtraControllers(Router& r) {
    // PUT /monitor/job/changeStatus
    // Java: selectJobById(jobId) -> newJob.setStatus(job.status) -> pauseJob/resumeJob -> updateJob
    //       状态既不是 0 也不是 1 时 rows 保持 0，toAjax(0) => {"code":500,"msg":"操作失败"}
    r.put("/monitor/job/changeStatus", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const Json body = ctx.body();
        if (!body.contains("jobId") || body["jobId"].is_null())
            return BaseController::ok(BaseController::toAjax(false));
        const long long jobId = body["jobId"].is_string()
                                    ? std::atoll(body["jobId"].get<std::string>().c_str())
                                    : body["jobId"].get<long long>();
        const std::string status =
            body.contains("status") && body["status"].is_string() ? body["status"].get<std::string>()
                                                                  : std::string();

        // 查不到任务时 Java 在 newJob.setStatus(...) 处抛 NPE
        cm::db::Result found;
        if (!Db::instance().query("select job_id from sys_job where job_id = " + Db::lit(jobId), found) ||
            found.rows.empty()) {
            throw cm::exception::NullPointerException();
        }

        const bool resume = status == ScheduleConstants::NORMAL;
        const bool pause = status == ScheduleConstants::PAUSE;
        if (!resume && !pause) return BaseController::ok(BaseController::toAjax(false));

        long long rows = 0;
        Db::instance().execute("update sys_job set status = " + Db::lit(status) +
                                   " where job_id = " + Db::lit(jobId),
                               &rows);
        // 调度器侧的 pauseJob/resumeJob 在 C++ 无对应实现（见头文件说明）
        return BaseController::ok(BaseController::toAjax(rows > 0));
    });

    // PUT /monitor/job/run —— ❌ 不做：需要反射调度 invokeTarget 白名单里的 spring bean
    r.put("/monitor/job/run", [](RequestContext&) -> cm::http::ApiResponse {
        return BaseController::ok(
            AjaxResult::error("C++ 侧未实现 Quartz 触发器，无法立即执行任务（见 COMPATIBILITY.md）"));
    });

    // DELETE /monitor/jobLog/clean —— Java: <update id="cleanJobLog">truncate table sys_job_log
    r.del("/monitor/jobLog/clean", [](RequestContext&) -> cm::http::ApiResponse {
        Db::instance().execute("truncate table sys_job_log");
        return BaseController::ok(BaseController::success());
    }).permi("monitor:job:remove");
}

} // namespace cm::web
