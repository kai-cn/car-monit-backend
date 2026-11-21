#pragma once
// 对应 Java: CarTrackInfoController#changeTrailInfo + CarSuspiciousController 的
//             listFileCarNo / history/{id}
//
// 三条都建立在同一套"桩号→经纬度"几何计算上（见 cm/base/service/TrailGeometry.hpp），
// 所以单独成一个文件而不是塞进 ManagerExtraControllers。
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerManagerTrailInfoControllers(Router& r);

} // namespace cm::web
