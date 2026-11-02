# 端点清单与迁移覆盖（由 scripts/gen_inventory.py 自动生成）

Java 控制器方法总数：**326**；已注册：**48**；未注册：**278**。

| 控制器 | 方法 | 路径 | Java 方法 | @PreAuthorize | C++ 状态 |
|---|---|---|---|---|---|
| BaseConfigServiceAreaController | GET | `/base/configServiceArea/list` | list | base:configServiceArea:list | ❌ |
| BaseConfigServiceAreaController | GET | `/base/configServiceArea/listQuery` | listQuery |  | ❌ |
| BaseConfigServiceAreaController | GET | `/base/configServiceArea/export` | export | base:configServiceArea:export | ❌ |
| BaseConfigServiceAreaController | POST | `/base/configServiceArea` | add | base:configServiceArea:add | ❌ |
| BaseConfigServiceAreaController | PUT | `/base/configServiceArea` | edit | base:configServiceArea:edit | ❌ |
| CarWarningConfigController | GET | `/base/config/list` | list | base:config:list | ❌ |
| CarWarningConfigController | GET | `/base/config/export` | export | base:config:export | ❌ |
| CarWarningConfigController | POST | `/base/config` | add | base:config:add | ❌ |
| CarWarningConfigController | PUT | `/base/config` | edit | base:config:edit | ❌ |
| CdcController | GET | `/base/cdc/status` | getQueueStatus |  | ❌ |
| CdcController | GET | `/base/cdc/dead-letters` | getDeadLetterMessages |  | ❌ |
| CdcController | GET | `/base/cdc/retry-messages` | getRetryMessages |  | ❌ |
| CdcController | POST | `/base/cdc/retry-all` | retryAllDeadMessages |  | ❌ |
| CdcController | DELETE | `/base/cdc/dead-letters/clear` | clearDeadLetterQueue |  | ❌ |
| CdcController | GET | `/base/cdc/config` | getConfig |  | ❌ |
| DwdLcztFwqjcxxController | GET | `/base/fwqjcxx/list` | list |  | ❌ |
| DwdLcztFwqjcxxController | GET | `/base/fwqjcxx/export` | export | base:fwqjcxx:export | ❌ |
| DwdLcztFwqjcxxController | POST | `/base/fwqjcxx` | add | base:fwqjcxx:add | ❌ |
| DwdLcztFwqjcxxController | PUT | `/base/fwqjcxx` | edit | base:fwqjcxx:edit | ❌ |
| DwdLcztSfsjcxxController | GET | `/base/sfsjcxx/list` | list |  | ❌ |
| DwdLcztSfsjcxxController | GET | `/base/sfsjcxx/export` | export | base:sfsjcxx:export | ❌ |
| DwdLcztSfsjcxxController | POST | `/base/sfsjcxx` | add | base:sfsjcxx:add | ❌ |
| DwdLcztSfsjcxxController | PUT | `/base/sfsjcxx` | edit | base:sfsjcxx:edit | ❌ |
| DwdLcztSfzjcxxController | GET | `/base/sfzjcxx/list` | list |  | ❌ |
| DwdLcztSfzjcxxController | GET | `/base/sfzjcxx/export` | export | base:sfzjcxx:export | ❌ |
| DwdLcztSfzjcxxController | POST | `/base/sfzjcxx` | add | base:sfzjcxx:add | ❌ |
| DwdLcztSfzjcxxController | PUT | `/base/sfzjcxx` | edit | base:sfzjcxx:edit | ❌ |
| GeometryController | GET | `/base/geometry/getHenDa` | getHenDa | base:geometry:list | ❌ |
| GeometryController | GET | `/base/geometry/syncAllGeometry` | syncAllGeometry |  | ❌ |
| GeometryController | GET | `/base/geometry/syncAllGeometry1` | syncAllGeometry1 |  | ❌ |
| GeometryController | GET | `/base/geometry/list` | list | base:geometry:list | ❌ |
| GeometryController | GET | `/base/geometry/export` | export | base:geometry:export | ❌ |
| GeometryController | POST | `/base/geometry` | add | base:geometry:add | ❌ |
| GeometryController | PUT | `/base/geometry` | edit | base:geometry:edit | ❌ |
| OdsCxztFwqcllsController | GET | `/manager/fwqclls/list` | list | manager:fwqclls:list | ❌ |
| OdsLwzxsfsjFeeGantryFusion01Controller | GET | `/base/feeGantry/list` | list | base:feeGantry:list | ❌ |
| OdsLwzxsfsjFeeRecords01Controller | GET | `/base/feerecords/list` | list | base:feerecords:list | ❌ |
| OdsLwzxsfsjFeeRecords01Controller | GET | `/base/feerecords/export` | export | base:feerecords:list | ❌ |
| OdsLwzxsfsjFeeStationEnter01Controller | GET | `/base/feeStationEnter/list` | list |  | ❌ |
| OdsLwzxsfsjFeeStationExit01Controller | GET | `/base/feestationexit/list` | list | base:feestationexit:list | ❌ |
| OdsRtSzdnSnapshotFlowAddcodeController | GET | `/base/snapshotflow/list` | list | base:snapshotflow:list | ❌ |
| OdsRtSzdnSnapshotFlowAddcodeController | GET | `/base/snapshotflow/export` | export | base:snapshotflow:list | ❌ |
| OdsRtSzdnSnapshotFlowAddcodeController | GET | `/base/snapshotflow/earliest-time` | getEarliestSnapshottime |  | ❌ |
| OdsRtSzdnSnapshotFlowProvcaptureAddcodeController | GET | `/base/provcapture/list` | list |  | ❌ |
| OdsRtSzdnSnapshotFlowStationcaptureAddcodeController | GET | `/base/stationcapture/list` | list |  | ❌ |
| OdsSzdnGantryController | GET | `/base/gantry/list` | list |  | ❌ |
| OdsSzdnGantryController | GET | `/base/gantry/listAll` | listAll |  | ❌ |
| OdsSzdnGantryController | GET | `/base/gantry/export` | export | base:gantry:export | ❌ |
| OdsSzdnGantryController | POST | `/base/gantry` | add | base:gantry:add | ❌ |
| OdsSzdnGantryController | PUT | `/base/gantry` | edit | base:gantry:edit | ❌ |
| OdsSzdnGantryIpController | GET | `/base/gantryIp/list` | list |  | ❌ |
| OdsSzdnProvinceBorderVehicleWeightNewstructureController | GET | `/base/vehicleweight/list` | list |  | ❌ |
| OdsSzdnSectionController | GET | `/base/section/list` | list |  | ❌ |
| OdsSzdnSectionController | GET | `/base/section/listAll` | listAll |  | ❌ |
| OdsSzdnSectionController | GET | `/base/section/export` | export | base:section:export | ❌ |
| OdsSzdnSectionController | POST | `/base/section` | add | base:section:add | ❌ |
| OdsSzdnSectionController | PUT | `/base/section` | edit | base:section:edit | ❌ |
| OdsSzdnTollController | GET | `/base/toll/list` | list |  | ❌ |
| OdsSzdnTollController | GET | `/base/toll/listAll` | listAll |  | ❌ |
| OdsSzdnTollController | GET | `/base/toll/export` | export | base:toll:export | ❌ |
| OdsSzdnTollController | POST | `/base/toll` | add | base:toll:add | ❌ |
| OdsSzdnTollController | PUT | `/base/toll` | edit | base:toll:edit | ❌ |
| OdsSzdnTollStationIpController | GET | `/base/tollStationIp/list` | list |  | ❌ |
| OdsYhglVBaseOrgController | GET | `/base/org/list` | list |  | ❌ |
| OdsYhglVBaseOrgController | GET | `/base/org/export` | export | base:org:export | ❌ |
| OdsYhglVBaseOrgController | POST | `/base/org` | add | base:org:add | ❌ |
| OdsYhglVBaseOrgController | PUT | `/base/org` | edit | base:org:edit | ❌ |
| ZdataLocationDictController | GET | `/base/location/list` | list |  | ❌ |
| ZdataTrailFittingController | GET | `/base/fitting/list` | list |  | ❌ |
| ZdataTrailTracksController | GET | `/base/trailtracks/list` | list |  | ❌ |
| FlowApplyInfoController | GET | `/flow/applyinfo/list` | list |  | ❌ |
| FlowApplyInfoController | GET | `/flow/applyinfo/listAll` | listAll | flow:applyinfo:list | ❌ |
| FlowApplyInfoController | GET | `/flow/applyinfo/export` | export | flow:applyinfo:export | ❌ |
| FlowApplyInfoController | POST | `/flow/applyinfo` | add | flow:applyinfo:add | ❌ |
| FlowApplyInfoController | PUT | `/flow/applyinfo` | edit | flow:applyinfo:edit | ❌ |
| FlowCurrentNodeController | GET | `/flow/currentnode/list` | list | flow:currentnode:list | ❌ |
| FlowCurrentNodeController | GET | `/flow/currentnode/export` | export | flow:currentnode:export | ❌ |
| FlowCurrentNodeController | POST | `/flow/currentnode` | add | flow:currentnode:add | ❌ |
| FlowCurrentNodeController | PUT | `/flow/currentnode` | edit | flow:currentnode:edit | ❌ |
| FlowCurrentNodeController | PUT | `/flow/currentnode/saveFlowAuit` | saveFlowAuit |  | ❌ |
| FlowCurrentNodeController | POST | `/flow/currentnode/submitReturn` | submitReturn |  | ❌ |
| FlowCurrentNodeController | POST | `/flow/currentnode/submitEntrustFlow` | submitEntrustFlow |  | ❌ |
| FlowListController | GET | `/flow/flowlist/list` | list | flow:flowlist:list | ❌ |
| FlowListController | GET | `/flow/flowlist/listnew` | listnew |  | ❌ |
| FlowListController | GET | `/flow/flowlist/export` | export | flow:flowlist:export | ❌ |
| FlowListController | POST | `/flow/flowlist` | add | flow:flowlist:add | ❌ |
| FlowListController | PUT | `/flow/flowlist` | edit | flow:flowlist:edit | ❌ |
| FlowMessageDisposeController | GET | `/flow/messagedispose/list` | list | flow:messagedispose:list | ❌ |
| FlowMessageDisposeController | GET | `/flow/messagedispose/export` | export | flow:messagedispose:export | ❌ |
| FlowMessageDisposeController | POST | `/flow/messagedispose` | add | flow:messagedispose:add | ❌ |
| FlowMessageDisposeController | PUT | `/flow/messagedispose` | edit | flow:messagedispose:edit | ❌ |
| FlowMessageInfoController | GET | `/flow/messageinfo/list` | list |  | ❌ |
| FlowMessageInfoController | GET | `/flow/messageinfo/listyb` | listyb |  | ❌ |
| FlowMessageInfoController | GET | `/flow/messageinfo/listyj` | listyj |  | ❌ |
| FlowMessageInfoController | GET | `/flow/messageinfo/listxx` | listxx |  | ❌ |
| FlowMessageInfoController | GET | `/flow/messageinfo/export` | export | flow:messageinfo:export | ❌ |
| FlowMessageInfoController | POST | `/flow/messageinfo` | add | flow:messageinfo:add | ❌ |
| FlowMessageInfoController | PUT | `/flow/messageinfo` | edit | flow:messageinfo:edit | ❌ |
| FlowMessageInfoController | GET | `/flow/messageinfo/exportShrz` | exportShrz |  | ❌ |
| FlowNameController | GET | `/flow/flowname/list` | list | flow:flowname:list | ❌ |
| FlowNameController | GET | `/flow/flowname/listQuery` | listQuery |  | ❌ |
| FlowNameController | GET | `/flow/flowname/export` | export | flow:flowname:export | ❌ |
| FlowNameController | POST | `/flow/flowname` | add | flow:flowname:add | ❌ |
| FlowNameController | PUT | `/flow/flowname` | edit | flow:flowname:edit | ❌ |
| FlowNameController | POST | `/flow/flowname/tbFlow` | tbFlow | flow:flowname:edit | ❌ |
| FlowTemplateController | GET | `/flow/flowtemplate/list` | list | flow:flowtemplate:list | ❌ |
| FlowTemplateController | GET | `/flow/flowtemplate/flowlist` | flowlist |  | ❌ |
| FlowTemplateController | GET | `/flow/flowtemplate/export` | export | flow:flowtemplate:export | ❌ |
| FlowTemplateController | POST | `/flow/flowtemplate` | add | flow:flowtemplate:add | ❌ |
| FlowTemplateController | PUT | `/flow/flowtemplate` | edit | flow:flowtemplate:edit | ❌ |
| SysConfigController | GET | `/system/config/list` | list | system:config:list | ✅ |
| SysConfigController | GET | `/system/config/export` | export | system:config:export | ✅ |
| SysConfigController | POST | `/system/config` | add | system:config:add | ✅ |
| SysConfigController | PUT | `/system/config` | edit | system:config:edit | ✅ |
| SysConfigController | DELETE | `/system/config/clearCache` | clearCache | system:config:remove | ✅ |
| SysDeptController | GET | `/system/dept/list` | list | system:dept:list | ❌ |
| SysDeptController | GET | `/system/dept/getList` | getList |  | ❌ |
| SysDeptController | GET | `/system/dept/treeselect` | treeselect |  | ❌ |
| SysDeptController | GET | `/system/dept/treeselectNew` | treeselectNew |  | ❌ |
| SysDeptController | POST | `/system/dept` | add | system:dept:add | ❌ |
| SysDeptController | PUT | `/system/dept` | edit | system:dept:edit | ❌ |
| SysDeptController | GET | `/system/dept/getCompanyList` | getCompanyList |  | ❌ |
| SysDictDataController | GET | `/system/dict/data/list` | list | system:dict:list | ✅ |
| SysDictDataController | GET | `/system/dict/data/export` | export | system:dict:export | ✅ |
| SysDictDataController | POST | `/system/dict/data` | add | system:dict:add | ✅ |
| SysDictDataController | PUT | `/system/dict/data` | edit | system:dict:edit | ✅ |
| SysDictTypeController | GET | `/system/dict/type/list` | list | system:dict:list | ✅ |
| SysDictTypeController | GET | `/system/dict/type/export` | export | system:dict:export | ✅ |
| SysDictTypeController | POST | `/system/dict/type` | add | system:dict:add | ✅ |
| SysDictTypeController | PUT | `/system/dict/type` | edit | system:dict:edit | ✅ |
| SysDictTypeController | DELETE | `/system/dict/type/clearCache` | clearCache | system:dict:remove | ✅ |
| SysDictTypeController | GET | `/system/dict/type/optionselect` | optionselect |  | ✅ |
| SysFileController | GET | `/system/file/list` | list | base:sysflie:list | ✅ |
| SysFileController | POST | `/system/file/uploadByUrl` | uploadByUrl |  | ❌ |
| SysFileController | POST | `/system/file/uploadFileId` | uploadFileId |  | ❌ |
| SysFileController | PUT | `/system/file` | edit |  | ✅ |
| SysFileController | GET | `/system/file/getNewCa` | getNewCa |  | ✅ |
| SysFileController | POST | `/system/file/updateCAFile` | updateCAFile |  | ✅ |
| SysFileController | POST | `/system/file/uploadFile` | upload |  | ❌ |
| SysIndexController | ANY | `/` | index |  | ✅ |
| SysIndexMenuController | GET | `/system/indexmenu/list` | list | system:indexmenu:list | ❌ |
| SysIndexMenuController | GET | `/system/indexmenu/mylist` | getSysIndexMenulist |  | ❌ |
| SysIndexMenuController | GET | `/system/indexmenu/export` | export | system:indexmenu:export | ❌ |
| SysIndexMenuController | POST | `/system/indexmenu` | add | system:indexmenu:add | ❌ |
| SysIndexMenuController | PUT | `/system/indexmenu` | edit | system:indexmenu:edit | ❌ |
| SysLoginController | POST | `/login` | login |  | ✅ |
| SysLoginController | GET | `/getInfo` | getInfo |  | ✅ |
| SysLoginController | GET | `/getRouters` | getRouters |  | ✅ |
| SysMenuController | GET | `/system/menu/list` | list | system:menu:list | ❌ |
| SysMenuController | GET | `/system/menu/treeselect` | treeselect |  | ❌ |
| SysMenuController | POST | `/system/menu` | add | system:menu:add | ❌ |
| SysMenuController | PUT | `/system/menu` | edit | system:menu:edit | ❌ |
| SysNoticeController | GET | `/system/notice/list` | list | system:notice:list | ✅ |
| SysNoticeController | GET | `/system/notice/listquery` | listquery |  | ✅ |
| SysNoticeController | POST | `/system/notice` | add | system:notice:add | ✅ |
| SysNoticeController | PUT | `/system/notice` | edit | system:notice:edit | ✅ |
| SysPostController | GET | `/system/post/list` | list | system:post:list | ❌ |
| SysPostController | GET | `/system/post/export` | export | system:post:export | ❌ |
| SysPostController | POST | `/system/post` | add | system:post:add | ❌ |
| SysPostController | PUT | `/system/post` | edit | system:post:edit | ❌ |
| SysPostController | GET | `/system/post/optionselect` | optionselect |  | ❌ |
| SysProfileController | GET | `/system/user/profile` | profile |  | ❌ |
| SysProfileController | PUT | `/system/user/profile` | updateProfile |  | ❌ |
| SysProfileController | PUT | `/system/user/profile/updatePwd` | updatePwd |  | ❌ |
| SysRoleController | GET | `/system/role/list` | list | system:role:list | ❌ |
| SysRoleController | GET | `/system/role/export` | export | system:role:export | ❌ |
| SysRoleController | POST | `/system/role` | add | system:role:add | ❌ |
| SysRoleController | PUT | `/system/role` | edit | system:role:edit | ❌ |
| SysRoleController | PUT | `/system/role/dataScope` | dataScope | system:role:edit | ❌ |
| SysRoleController | PUT | `/system/role/changeStatus` | changeStatus | system:role:edit | ❌ |
| SysRoleController | GET | `/system/role/optionselect` | optionselect | system:role:query | ❌ |
| SysRoleController | GET | `/system/role/selectlist` | selectlist |  | ❌ |
| SysUpgradeInfoController | GET | `/system/upgradeInfo/list` | list |  | ✅ |
| SysUpgradeInfoController | GET | `/system/upgradeInfo/newest` | newest |  | ✅ |
| SysUpgradeInfoController | GET | `/system/upgradeInfo/export` | export |  | ✅ |
| SysUpgradeInfoController | POST | `/system/upgradeInfo` | add |  | ✅ |
| SysUpgradeInfoController | PUT | `/system/upgradeInfo` | edit |  | ✅ |
| SysUserController | GET | `/system/user/list` | list |  | ❌ |
| SysUserController | GET | `/system/user/listAll` | listAll |  | ❌ |
| SysUserController | GET | `/system/user/listTenantIdAll` | listTenantIdAll |  | ❌ |
| SysUserController | GET | `/system/user/listutil` | listutil |  | ❌ |
| SysUserController | GET | `/system/user/listSameUtil` | listSameUtil |  | ❌ |
| SysUserController | GET | `/system/user/listMy` | listMy |  | ❌ |
| SysUserController | GET | `/system/user/export` | export | system:user:export | ❌ |
| SysUserController | POST | `/system/user/importData` | importData | system:user:import | ❌ |
| SysUserController | GET | `/system/user/importTemplate` | importTemplate |  | ❌ |
| SysUserController | POST | `/system/user` | add | system:user:add | ❌ |
| SysUserController | PUT | `/system/user` | edit | system:user:edit | ❌ |
| SysUserController | PUT | `/system/user/resetPwd` | resetPwd | system:user:resetPwd | ❌ |
| SysUserController | PUT | `/system/user/changeStatus` | changeStatus | system:user:edit | ❌ |
| SysUserController | PUT | `/system/user/bindUky` | bindUky |  | ❌ |
| SysUserController | GET | `/system/user/list/dept` | listByDept |  | ❌ |
| SysUserController | GET | `/system/user/currentUser` | selectCurrentUser |  | ❌ |
| BussTestController | GET | `/manager/busstest/list` | list | manager:busstest:list | ❌ |
| BussTestController | GET | `/manager/busstest/export` | export | manager:busstest:export | ❌ |
| BussTestController | POST | `/manager/busstest` | add | manager:busstest:add | ❌ |
| BussTestController | PUT | `/manager/busstest` | edit | manager:busstest:edit | ❌ |
| BussTestController | POST | `/manager/busstest/syncCurrentTrack` | syncCurrentTrack | manager:busstest:syncTest | ❌ |
| CarAduitFreeController | GET | `/manager/aduitfree/list` | list |  | ❌ |
| CarAduitFreeController | GET | `/manager/aduitfree/export` | export |  | ❌ |
| CarAduitFreeController | POST | `/manager/aduitfree` | add |  | ❌ |
| CarAduitFreeController | PUT | `/manager/aduitfree` | edit |  | ❌ |
| CarAduitFreeController | GET | `/manager/aduitfree/incomeStatics` | incomeStatics |  | ❌ |
| CarAduitFreeController | GET | `/manager/aduitfree/exportIncomeStatics` | exportIncomeStatics |  | ❌ |
| CarAduitFreeController | GET | `/manager/aduitfree/incomeDetailList` | incomeDetailList |  | ❌ |
| CarAduitFreeController | GET | `/manager/aduitfree/exportIncomeDetailList` | exportIncomeDetailList |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/list` | list |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/listCarNo` | listCarNo |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/listCount` | listCount |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/export` | export |  | ❌ |
| CarConfimFreeController | POST | `/manager/confimfree` | add |  | ❌ |
| CarConfimFreeController | PUT | `/manager/confimfree` | edit |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/concernedList` | concernedList |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/exportConcernedList` | exportConcernedList |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/carStatics` | getCarStatics |  | ❌ |
| CarConfimFreeController | GET | `/manager/confimfree/exportCarStatics` | exportCarStatics |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/list` | list |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/listCarNo` | listCarNo |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/listCarOrgId` | listCarOrgId |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/exportOrgId` | exportOrgId |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/listExceptId` | listExceptId |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/exceptRecordCount` | exceptRecordCount |  | ❌ |
| CarExceptRecordController | GET | `/manager/exceptrecord/export` | export |  | ❌ |
| CarExceptRecordController | POST | `/manager/exceptrecord` | add |  | ❌ |
| CarExceptRecordController | PUT | `/manager/exceptrecord` | edit |  | ❌ |
| CarFeeRecordController | GET | `/manager/feerecord/list` | list | manager:feerecord:list | ❌ |
| CarFeeRecordController | GET | `/manager/feerecord/export` | export | manager:feerecord:export | ❌ |
| CarFeeRecordController | POST | `/manager/feerecord` | add | manager:feerecord:add | ❌ |
| CarFeeRecordController | PUT | `/manager/feerecord` | edit | manager:feerecord:edit | ❌ |
| CarInfoController | GET | `/manager/carinfo/list` | list | manager:carinfo:list | ❌ |
| CarInfoController | GET | `/manager/carinfo/listAll` | listAll |  | ❌ |
| CarInfoController | GET | `/manager/carinfo/export` | export | manager:carinfo:export | ❌ |
| CarInfoController | POST | `/manager/carinfo` | add |  | ❌ |
| CarInfoController | PUT | `/manager/carinfo` | edit | manager:carinfo:edit | ❌ |
| CarQueryLogController | GET | `/manager/querylog/list` | list | manager:querylog:list | ❌ |
| CarQueryLogController | POST | `/manager/querylog` | add | manager:querylog:add | ❌ |
| CarQueryLogController | PUT | `/manager/querylog` | edit | manager:querylog:edit | ❌ |
| CarQueryLogController | GET | `/manager/querylog/export` | export | manager:querylog:export | ❌ |
| CarRouteDetailController | GET | `/manager/routedetail/list` | list | manager:routedetail:list | ❌ |
| CarRouteDetailController | GET | `/manager/routedetail/export` | export | manager:routedetail:export | ❌ |
| CarRouteDetailController | POST | `/manager/routedetail` | add | manager:routedetail:add | ❌ |
| CarRouteDetailController | PUT | `/manager/routedetail` | edit | manager:routedetail:edit | ❌ |
| CarRouteInfoController | GET | `/manager/routeinfo/list` | list | manager:routeinfo:list | ❌ |
| CarRouteInfoController | GET | `/manager/routeinfo/export` | export | manager:routeinfo:export | ❌ |
| CarRouteInfoController | POST | `/manager/routeinfo` | add | manager:routeinfo:add | ❌ |
| CarRouteInfoController | PUT | `/manager/routeinfo` | edit | manager:routeinfo:edit | ❌ |
| CarSplitRecordController | GET | `/manager/splitrecord/list` | list | manager:splitrecord:list | ❌ |
| CarSplitRecordController | GET | `/manager/splitrecord/export` | export | manager:splitrecord:export | ❌ |
| CarSplitRecordController | POST | `/manager/splitrecord` | add | manager:splitrecord:add | ❌ |
| CarSplitRecordController | PUT | `/manager/splitrecord` | edit | manager:splitrecord:edit | ❌ |
| CarSuspiciousBackController | GET | `/manager/carsuspiciousback/list` | list | manager:carsuspiciousback:list | ❌ |
| CarSuspiciousBackController | GET | `/manager/carsuspiciousback/export` | export | manager:carsuspiciousback:export | ❌ |
| CarSuspiciousBackController | POST | `/manager/carsuspiciousback` | add | manager:carsuspiciousback:add | ❌ |
| CarSuspiciousBackController | PUT | `/manager/carsuspiciousback` | edit | manager:carsuspiciousback:edit | ❌ |
| CarSuspiciousCheckController | GET | `/manager/suspiciouscheck/list` | list | manager:suspiciouscheck:list | ❌ |
| CarSuspiciousCheckController | GET | `/manager/suspiciouscheck/export` | export | manager:suspiciouscheck:export | ❌ |
| CarSuspiciousCheckController | POST | `/manager/suspiciouscheck` | add | manager:suspiciouscheck:add | ❌ |
| CarSuspiciousCheckController | PUT | `/manager/suspiciouscheck` | edit | manager:suspiciouscheck:edit | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/list` | list | manager:suspicious:list | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/listCarNo` | listCarNo |  | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/listFileCarNo` | listFileCarNo |  | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/exportAbnormalPassage` | exportAbnormalPassage |  | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/listAll` | listAll |  | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/export` | export | manager:suspicious:export | ❌ |
| CarSuspiciousController | POST | `/manager/suspicious` | add | manager:suspicious:add | ❌ |
| CarSuspiciousController | PUT | `/manager/suspicious` | edit | manager:suspicious:edit | ❌ |
| CarSuspiciousController | PUT | `/manager/suspicious/check` | check | manager:suspicious:check | ❌ |
| CarSuspiciousController | POST | `/manager/suspicious/syncSuspiciousCarTask` | syncSuspiciousCarTask |  | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/listHistory` | listHistory | manager:suspicious:list | ❌ |
| CarSuspiciousController | GET | `/manager/suspicious/exportHistory` | exportHistory | manager:suspicious:export | ❌ |
| CarTrackInfoController | GET | `/manager/cartrackinfo/list` | list | manager:cartrackinfo:list | ❌ |
| CarTrackInfoController | GET | `/manager/cartrackinfo/listByCarId` | listByCarId |  | ❌ |
| CarTrackInfoController | GET | `/manager/cartrackinfo/listByCarByTime` | listByCarByTime |  | ❌ |
| CarTrackInfoController | PUT | `/manager/cartrackinfo/changeTrailInfo` | changeTrailInfo |  | ❌ |
| CarTrackInfoController | GET | `/manager/cartrackinfo/carSnapShot` | carSnapShot |  | ❌ |
| CarTrackInfoController | GET | `/manager/cartrackinfo/export` | export | manager:cartrackinfo:export | ❌ |
| CarTrackInfoController | POST | `/manager/cartrackinfo` | add | manager:cartrackinfo:add | ❌ |
| CarTrackInfoController | PUT | `/manager/cartrackinfo` | edit | manager:cartrackinfo:edit | ❌ |
| CarWarningInfoController | GET | `/manager/carwarning/list` | list | manager:carwarning:list | ❌ |
| CarWarningInfoController | GET | `/manager/carwarning/export` | export | manager:carwarning:export | ❌ |
| CarWarningInfoController | POST | `/manager/carwarning` | add | manager:carwarning:add | ❌ |
| CarWarningInfoController | PUT | `/manager/carwarning` | edit | manager:carwarning:edit | ❌ |
| CarWarningRuleController | GET | `/manager/warningrule/list` | list | manager:warningrule:list | ❌ |
| CarWarningRuleController | GET | `/manager/warningrule/export` | export | manager:warningrule:export | ❌ |
| CarWarningRuleController | POST | `/manager/warningrule` | add | manager:warningrule:add | ❌ |
| CarWarningRuleController | PUT | `/manager/warningrule` | edit | manager:warningrule:edit | ❌ |
| CarWhiteInfoController | GET | `/manager/whiteinfo/list` | list | manager:whiteinfo:list | ❌ |
| CarWhiteInfoController | GET | `/manager/whiteinfo/export` | export | manager:whiteinfo:export | ❌ |
| CarWhiteInfoController | POST | `/manager/whiteinfo` | add | manager:whiteinfo:add | ❌ |
| CarWhiteInfoController | PUT | `/manager/whiteinfo` | edit | manager:whiteinfo:edit | ❌ |
| GantryCarController | GET | `/manager/gantrycar/list` | list | manager:gantrycar:list | ❌ |
| GantryCarController | GET | `/manager/gantrycar/export` | export | manager:gantrycar:export | ❌ |
| GantryCarController | POST | `/manager/gantrycar` | add | manager:gantrycar:add | ❌ |
| GantryCarController | PUT | `/manager/gantrycar` | edit | manager:gantrycar:edit | ❌ |
| GantryTradeInfoController | GET | `/manager/gantrytrade/list` | list | manager:gantrytrade:list | ❌ |
| GantryTradeInfoController | GET | `/manager/gantrytrade/export` | export | manager:gantrytrade:export | ❌ |
| GantryTradeInfoController | POST | `/manager/gantrytrade` | add | manager:gantrytrade:add | ❌ |
| GantryTradeInfoController | PUT | `/manager/gantrytrade` | edit | manager:gantrytrade:edit | ❌ |
| BigScreenController | GET | `/manager/bigScreen/carStatistics` | getCarStatistics |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/carLocation` | getCarLocation |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/sectionList` | getSectionList |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/carVoList` | carVoList |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/carAudit` | getCarAudit |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/carWarning` | getCarWarning |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/exceptionCar` | getExceptionCar |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/topTen` | topTen |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/orgList` | getOrgList |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/incomeStatistic` | incomeStatistic |  | ❌ |
| BigScreenController | GET | `/manager/bigScreen/exceptRecordList` | list |  | ❌ |
| CacheController | GET | `/monitor/cache` | getInfo | monitor:cache:list | ✅ |
| ServerController | ANY | `/monitor/server/monitor/server` | getInfo | monitor:server:list | ❌ |
| SysLogininforController | GET | `/monitor/logininfor/list` | list | monitor:logininfor:list | ✅ |
| SysLogininforController | GET | `/monitor/logininfor/export` | export | monitor:logininfor:export | ✅ |
| SysLogininforController | DELETE | `/monitor/logininfor/clean` | clean | monitor:logininfor:remove | ✅ |
| SysOperlogController | GET | `/monitor/operlog/list` | list | monitor:operlog:list | ✅ |
| SysOperlogController | GET | `/monitor/operlog/export` | export | monitor:operlog:export | ✅ |
| SysOperlogController | DELETE | `/monitor/operlog/clean` | clean | monitor:operlog:remove | ✅ |
| SysUserOnlineController | GET | `/monitor/online/list` | list | monitor:online:list | ✅ |
| CaptchaController | GET | `/captchaImage` | getCode |  | ✅ |
| CommonController | GET | `/common/download` | fileDownload |  | ✅ |
| CommonController | POST | `/common/upload` | uploadFile |  | ✅ |
| CommonController | POST | `/common/uploads` | uploadFiles |  | ✅ |
| CommonController | GET | `/common/download/resource` | resourceDownload |  | ✅ |
| TestController | GET | `/test/user/list` | userList |  | ✅ |
| TestController | POST | `/test/user/save` | save |  | ✅ |
| TestController | PUT | `/test/user/update` | update |  | ✅ |
