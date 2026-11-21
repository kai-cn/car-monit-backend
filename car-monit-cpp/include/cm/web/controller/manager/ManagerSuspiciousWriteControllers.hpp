#pragma once
// 对应 Java: com.ruoyi.web.controller.manager.CarSuspiciousController 的写侧接口
//   PUT  /manager/suspicious/check               可疑车辆核实
//   POST /manager/suspicious/syncSuspiciousCarTask  外部推送轨迹生成可疑车辆
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerManagerSuspiciousWriteControllers(Router& r);

} // namespace cm::web
