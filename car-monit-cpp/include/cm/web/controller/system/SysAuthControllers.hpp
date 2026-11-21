#pragma once
// system 权限域控制器的注册入口：对应 Spring 的 @RestController 扫描
//
// 这批控制器不是 RuoYi 代码生成器产出的同构 CRUD（有树形构建、数据权限、
// 唯一性校验、密码策略等业务分支），所以逐个手写，不走 CrudSpec 引擎。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerSysMenuController(Router& r);
void registerSysDeptController(Router& r);
void registerSysRoleController(Router& r);
void registerSysPostExtraController(Router& r);
void registerSysIndexMenuController(Router& r);
void registerSysProfileController(Router& r);
void registerSysUserController(Router& r);

} // namespace cm::web
