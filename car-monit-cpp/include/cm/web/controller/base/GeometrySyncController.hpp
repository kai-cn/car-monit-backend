#pragma once
// /base/geometry 的 3 条 HenDa 同步接口 + /base/snapshotflow/earliest-time
// 全是出站 HTTP，失败路径才是本地可观测的行为，详见实现文件头部说明。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerGeometrySyncController(Router& r);

} // namespace cm::web
