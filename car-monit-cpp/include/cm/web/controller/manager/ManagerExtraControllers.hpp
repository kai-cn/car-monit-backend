#pragma once
// manager 域里“同构 CRUD + 一点前置条件”的那批端点
//
// 这些接口不需要另写 SQL：Java 侧只是在调用原本的分页查询前先给查询对象塞默认值
// （查不到而不是查全表），或者用一条独立的 group by 统计。
// 列定义复用 scripts/gen_crud_spec.py 暴露的 specCarXxx()。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web {

void registerManagerExtraControllers(Router& r);

/** 可疑车辆“备份表”查询的 spec 变体：Java 的 selectCarSuspiciousListHistroy 与
 *  selectCarSuspiciousList 的 <if> 条件逐条相同，只有 FROM（car_suspicious_back）
 *  和 order by（t.id）不同，所以不另写一份列定义。
 *  listHistory 与 exportHistory 共用（后者是模板导出，走另一个控制器文件）。 */
const cm::web::crud::Spec& suspiciousHistorySpec();

} // namespace cm::web
