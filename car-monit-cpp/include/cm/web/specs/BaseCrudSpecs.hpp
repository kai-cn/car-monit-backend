// 由 scripts/gen_crud_spec.py 生成，与 src/cm/web/specs/BaseCrudSpecs.cpp 成对。
// 手写控制器通过这里复用同一份列定义，不要再抄一遍字段表。
#pragma once
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

const Spec& specBaseConfigServiceArea();
const Spec& specCarWarningConfig();
const Spec& specDwdLcztFwqjcxx();
const Spec& specDwdLcztSfsjcxx();
const Spec& specDwdLcztSfzjcxx();
const Spec& specGeometry();
const Spec& specOdsCxztFwqclls();
const Spec& specOdsLwzxsfsjFeeGantryFusion01();
const Spec& specOdsLwzxsfsjFeeRecords01();
const Spec& specOdsLwzxsfsjFeeStationEnter01();
const Spec& specOdsLwzxsfsjFeeStationExit01();
const Spec& specOdsRtSzdnSnapshotFlowAddcode();
const Spec& specOdsRtSzdnSnapshotFlowProvcaptureAddcode();
const Spec& specOdsRtSzdnSnapshotFlowStationcaptureAddcode();
const Spec& specOdsSzdnGantry();
const Spec& specOdsSzdnGantryIp();
const Spec& specOdsSzdnProvinceBorderVehicleWeightNewstructure();
const Spec& specOdsSzdnSection();
const Spec& specOdsSzdnToll();
const Spec& specOdsSzdnTollStationIp();
const Spec& specOdsYhglVBaseOrg();
const Spec& specZdataLocationDict();
const Spec& specZdataTrailFitting();
const Spec& specZdataTrailTracks();

} // namespace cm::web::crud
