#pragma once
// manager 域里“同构 CRUD + 一点前置条件”的那批端点
//
// 这些接口不需要另写 SQL：Java 侧只是在调用原本的分页查询前先给查询对象塞默认值
// （查不到而不是查全表），或者用一条独立的 group by 统计。
// 列定义复用 scripts/gen_crud_spec.py 暴露的 specCarXxx()。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerManagerExtraControllers(Router& r);

} // namespace cm::web
