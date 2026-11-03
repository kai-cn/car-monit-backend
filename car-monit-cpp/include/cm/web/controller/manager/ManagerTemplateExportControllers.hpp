#pragma once
// 对应 Java: CarExceptRecordController#listCarOrgId / #exportOrgId、
//            CarConfimFreeController#exportConcernedList / #exportCarStatics、
//            CarAduitFreeController#exportIncomeStatics / #exportIncomeDetailList
#include "cm/framework/web/Router.hpp"

namespace cm::web {

void registerManagerTemplateExportControllers(Router& r);

} // namespace cm::web
