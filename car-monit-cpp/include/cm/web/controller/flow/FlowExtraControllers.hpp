#pragma once
// flow 域里非同构 CRUD 的控制器注册入口（审批流相关）
//
// 这些端点要么返回“查询结果 + 手工拼的伪行”，要么直接写 flow_message_dispose，
// 不能靠 CrudSpec 引擎产出，所以逐个手写。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerFlowExtraControllers(Router& r);

} // namespace cm::web
