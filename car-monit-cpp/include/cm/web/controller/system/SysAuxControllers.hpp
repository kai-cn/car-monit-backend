#pragma once
#include "cm/framework/web/Router.hpp"

namespace cm::web {
void registerSysConfigController(Router& r);
void registerSysDictTypeController(Router& r);
void registerSysDictDataController(Router& r);
void registerSysNoticeController(Router& r);
void registerSysUpgradeInfoController(Router& r);
void registerSysFileController(Router& r);
} // namespace cm::web
