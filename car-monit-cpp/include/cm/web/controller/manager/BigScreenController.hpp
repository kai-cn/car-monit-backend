#pragma once
// 对应 Java: com.ruoyi.web.controller.manager.bigscreen.BigScreenController
//
// 大屏里“纯查库 + 投影成小 VO”的那几个接口。依赖外部路网/HTTP 的
// （raodTrailList、carLocation 的实时定位等）不在这里，见 COMPATIBILITY.md。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerBigScreenController(Router& r);

} // namespace cm::web
