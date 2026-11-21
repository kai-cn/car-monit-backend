#pragma once
// 对应 Java: com.ruoyi.web.controller.base.CdcController
//
// 这批端点不是同构 CRUD：数据在 Redis（死信/重试队列）里，且响应是手写 Map，
// 所以逐个手写，不走 CrudSpec 引擎。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerCdcController(Router& r);

} // namespace cm::web
