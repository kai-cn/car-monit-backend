#pragma once
// 对应 Java: com.ruoyi.quartz.controller.{SysJobController,SysJobLogController}
//            里依赖调度器的那几个接口
//
// ⚠️ C++ 侧没有 Quartz（也没有 JDBC JobStore），这里只保证 HTTP 契约与数据库副作用一致：
//   * changeStatus 照常 update sys_job.status（Java 的 pauseJob/resumeJob 就是 updateJob + 通知调度器）
//   * clean 照常 truncate sys_job_log
//   * run 无法执行 —— Java 通过反射调 invokeTarget 白名单里的 spring bean，
//     C++ 侧没有这套 bean 目录，宁可显式报错也不假装执行成功。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerQuartzExtraControllers(Router& r);

} // namespace cm::web
