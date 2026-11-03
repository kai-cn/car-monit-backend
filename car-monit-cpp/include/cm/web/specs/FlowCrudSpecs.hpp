// 由 scripts/gen_crud_spec.py 生成，与 src/cm/web/specs/FlowCrudSpecs.cpp 成对。
// 手写控制器通过这里复用同一份列定义，不要再抄一遍字段表。
#pragma once
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

const Spec& specFlowApplyInfo();
const Spec& specFlowCurrentNode();
const Spec& specFlowList();
const Spec& specFlowMessageDispose();
const Spec& specFlowMessageInfo();
const Spec& specFlowName();
const Spec& specFlowTemplate();

} // namespace cm::web::crud
