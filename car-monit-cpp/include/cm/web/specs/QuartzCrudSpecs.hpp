// 由 scripts/gen_crud_spec.py 生成，与 src/cm/web/specs/QuartzCrudSpecs.cpp 成对。
// 手写控制器通过这里复用同一份列定义，不要再抄一遍字段表。
#pragma once
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

const Spec& specSysJob();
const Spec& specSysJobLog();

} // namespace cm::web::crud
