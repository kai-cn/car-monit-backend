#pragma once
// 控制器注册入口：对应 Spring 的 @RestController 组件扫描
//
// 迁移进度：
//   [x] CaptchaController        /captchaImage
//   [x] SysLoginController       /login /getInfo /getRouters
//   [x] SysIndexController       /
//   [ ] 其余 79 个控制器（见 MIGRATION_GUIDE.md 的控制器清单）
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerCaptchaController(Router& r);
void registerLoginController(Router& r);
void registerIndexController(Router& r);

/** 业务域同构 CRUD 的批量注册入口。
 *  实现在 src/cm/web/specs/{Base,Manager,Flow}CrudSpecs.cpp，
 *  由 scripts/gen_crud_spec.py 从 Java 实体 + MyBatis XML + 控制器抽取生成。 */
namespace crud {
void registerBaseArea(Router& r);
void registerManagerArea(Router& r);
void registerFlowArea(Router& r);
} // namespace crud

/** 汇总注册（main.cpp 调用） */
void registerControllers(Router& r);

} // namespace cm::web
