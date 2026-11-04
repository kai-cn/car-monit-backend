#pragma once
// SysFileController 的 9 个上传/下载端点（对象存储侧），与已存在的 CRUD 部分分开注册。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerSysFileUploadController(Router& r);

} // namespace cm::web
