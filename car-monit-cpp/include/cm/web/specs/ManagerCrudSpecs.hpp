// 由 scripts/gen_crud_spec.py 生成，与 src/cm/web/specs/ManagerCrudSpecs.cpp 成对。
// 手写控制器通过这里复用同一份列定义，不要再抄一遍字段表。
#pragma once
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

const Spec& specBussTest();
const Spec& specCarAduitFree();
const Spec& specCarConfimFree();
const Spec& specCarExceptRecord();
const Spec& specCarFeeRecord();
const Spec& specCarInfo();
const Spec& specCarQueryLog();
const Spec& specCarRouteDetail();
const Spec& specCarRouteInfo();
const Spec& specCarSplitRecord();
const Spec& specCarSuspiciousBack();
const Spec& specCarSuspiciousCheck();
const Spec& specCarSuspicious();
const Spec& specCarTrackInfo();
const Spec& specCarWarningInfo();
const Spec& specCarWarningRule();
const Spec& specCarWhiteInfo();
const Spec& specGantryCar();
const Spec& specGantryTradeInfo();

} // namespace cm::web::crud
