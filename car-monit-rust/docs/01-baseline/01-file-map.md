# 附录 A：Java → Rust 文件映射清单

> 由 `tools/gen_baseline.py` 生成。Rust 侧遵循 snake_case，模块按原包镜像；
> `（与实现合并）` 表示该 Java 接口与唯一实现合并为一个 Rust 模块（原项目没有多实现，不为测试强造 trait）。

## 统计

| 模块 | Java 文件数 | 纯逻辑 | 框架契约 | 混合 |
|---|---:|---:|---:|---:|
| ruoyi-admin | 89 | 9 | 80 | 0 |
| ruoyi-common | 137 | 92 | 21 | 24 |
| ruoyi-framework | 48 | 7 | 32 | 9 |
| ruoyi-system | 380 | 129 | 156 | 95 |
| ruoyi-quartz | 23 | 8 | 7 | 8 |
| ruoyi-generator | 19 | 11 | 8 | 0 |
| **合计** | **696** | | | |

## ruoyi-admin（89）

| Java | 职责 | 类型 | Rust 目标 |
|---|---|---|---|
| `ruoyi-admin/src/main/java/com/ruoyi/admin/config/ShardingSphereConfig.java` | 配置装配 | 框架契约 | `src/app/sharding_config.rs（由自研分表路由替代）` |
| `ruoyi-admin/src/main/java/com/ruoyi/RuoYiApplication.java` | 启动类 | 框架契约 | `src/main.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/RuoYiServletInitializer.java` | WAR 部署入口 | 框架契约 | `（不迁移：WAR 部署入口）` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/BaseConfigServiceAreaController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/base_config_service_area_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CarWarningConfigController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/car_warning_config_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CdcController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/cdc_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztFwqjcxxController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/dwd_lczt_fwqjcxx_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfsjcxxController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/dwd_lczt_sfsjcxx_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfzjcxxController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/dwd_lczt_sfzjcxx_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/GeometryController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/geometry_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsCxztFwqcllsController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_cxzt_fwqclls_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_lwzxsfsj_fee_gantry_fusion01_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_lwzxsfsj_fee_records01_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationEnter01Controller.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_lwzxsfsj_fee_station_enter01_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_lwzxsfsj_fee_station_exit01_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_rt_szdn_snapshot_flow_addcode_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_rt_szdn_snapshot_flow_provcapture_addcode_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_rt_szdn_snapshot_flow_stationcapture_addcode_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_szdn_gantry_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryIpController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_szdn_gantry_ip_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnProvinceBorderVehicleWeightNewstructureController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_szdn_province_border_vehicle_weight_newstructure_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnSectionController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_szdn_section_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_szdn_toll_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollStationIpController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_szdn_toll_station_ip_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsYhglVBaseOrgController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/ods_yhgl_v_base_org_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataLocationDictController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/zdata_location_dict_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/zdata_trail_fitting_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailTracksController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/base/zdata_trail_tracks_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CaptchaController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/common/captcha_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CommonController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/common/common_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/DownTemplateController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/common/down_template_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowApplyInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_apply_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowCurrentNodeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_current_node_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowListController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_list_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageDisposeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_message_dispose_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_message_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowNameController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_name_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowTemplateController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/flow/flow_template_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/bigscreen/big_screen_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/BussTestController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/buss_test_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarAduitFreeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_aduit_free_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_confim_free_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_except_record_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarFeeRecordController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_fee_record_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarQueryLogController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_query_log_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteDetailController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_route_detail_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_route_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSplitRecordController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_split_record_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousBackController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_suspicious_back_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousCheckController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_suspicious_check_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_suspicious_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_track_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_warning_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningRuleController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_warning_rule_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWhiteInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/car_white_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryCarController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/gantry_car_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryTradeInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/manager/gantry_trade_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/CacheController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/monitor/cache_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/ServerController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/monitor/server_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysLogininforController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/monitor/sys_logininfor_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysOperlogController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/monitor/sys_operlog_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysUserOnlineController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/monitor/sys_user_online_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_config_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDeptController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_dept_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictDataController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_dict_data_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictTypeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_dict_type_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysFileController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_file_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_index_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexMenuController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_index_menu_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysLoginController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_login_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysMenuController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_menu_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysNoticeController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_notice_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysPostController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_post_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysProfileController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_profile_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysRoleController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_role_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUpgradeInfoController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_upgrade_info_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUserController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/system/sys_user_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/tool/test_controller.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/core/config/SwaggerConfig.java` | 配置装配 | 框架契约 | `src/app/openapi.rs（utoipa）` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ArithmeticUtils.java` | 工具类 | 纯逻辑 | `src/api/util/arithmetic_utils.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/Base64DecodeMultipartFile.java` | 工具类 | 纯逻辑 | `src/api/util/base64_decode_multipart_file.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/CommonUtil.java` | 工具类 | 纯逻辑 | `src/api/util/common_util.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ConstantUtil.java` | 工具类 | 纯逻辑 | `src/api/util/constant_util.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ConvertUpMoney.java` | 工具类 | 纯逻辑 | `src/api/util/convert_up_money.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportEntity.java` | 工具类 | 纯逻辑 | `src/api/util/import_entity.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportErrorEntity.java` | 工具类 | 纯逻辑 | `src/api/util/import_error_entity.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportSysUtil.java` | 工具类 | 纯逻辑 | `src/api/util/import_sys_util.rs` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportUtil.java` | 工具类 | 纯逻辑 | `src/api/util/import_util.rs` |

## ruoyi-common（137）

| Java | 职责 | 类型 | Rust 目标 |
|---|---|---|---|
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/Anonymous.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/anonymous.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/DataScope.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/data_scope.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/DataSource.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/data_source.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/Excel.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/excel.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/Excels.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/excels.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/Log.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/log.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/RateLimiter.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/rate_limiter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/RepeatSubmit.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/repeat_submit.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/annotation/Sensitive.java` | 注解（编译期标记） | 框架契约 | `src/common/annotation/sensitive.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/config/IdWorkerConfig.java` | 配置装配 | 框架契约 | `src/common/config/id_worker_config.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/config/MyBatisPlusHandlerConfig.java` | 配置装配 | 框架契约 | `src/common/config/my_batis_plus_handler_config.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/config/OssAutoConfiguration.java` | 配置装配 | 框架契约 | `src/common/config/oss_auto_configuration.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/config/OssProperties.java` | 配置装配 | 框架契约 | `src/common/config/oss_properties.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/config/RuoYiConfig.java` | 配置装配 | 框架契约 | `src/common/config/ruo_yi_config.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/config/serializer/SensitiveJsonSerializer.java` | 配置装配 | 框架契约 | `src/common/config/serializer/sensitive_json_serializer.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/constant/CacheConstants.java` | 常量 | 纯逻辑 | `src/common/constant/cache_constants.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/constant/Constants.java` | 常量 | 纯逻辑 | `src/common/constant/constants.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/constant/GenConstants.java` | 常量 | 纯逻辑 | `src/common/constant/gen_constants.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/constant/HttpStatus.java` | 常量 | 纯逻辑 | `src/common/constant/http_status.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/constant/ScheduleConstants.java` | 常量 | 纯逻辑 | `src/common/constant/schedule_constants.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/constant/UserConstants.java` | 常量 | 纯逻辑 | `src/common/constant/user_constants.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/controller/BaseController.java` | Controller（HTTP 路由） | 框架契约 | `src/common/core/controller/base_controller.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/AjaxResult.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/ajax_result.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BaseEntity.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_entity.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntity.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_plus_entity.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntityInput.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_plus_entity_input.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntityInputNew.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_plus_entity_input_new.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntityLong.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_plus_entity_long.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntityNew.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_plus_entity_new.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BaseUuidEntity.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/base_uuid_entity.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/Custom.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/custom.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/CustomClass.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/custom_class.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDept.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/entity/sys_dept.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictData.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/entity/sys_dict_data.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDictType.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/entity/sys_dict_type.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysMenu.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/entity/sys_menu.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/entity/sys_role.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysUser.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/entity/sys_user.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/LoginBody.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/model/login_body.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/LoginUser.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/model/login_user.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/model/RegisterBody.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/model/register_body.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/R.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/r.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/TreeEntity.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/tree_entity.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/domain/TreeSelect.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/tree_select.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/page/PageDomain.java` | 框架核心 | 混合 | `src/common/core/page/page_domain.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableDataInfo.java` | 框架核心 | 混合 | `src/common/core/page/table_data_info.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableSupport.java` | 框架核心 | 混合 | `src/common/core/page/table_support.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/redis/RedisCache.java` | 框架核心 | 混合 | `src/common/core/redis/redis_cache.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/text/CharsetKit.java` | 框架核心 | 混合 | `src/common/core/text/charset_kit.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/text/Convert.java` | 框架核心 | 混合 | `src/common/core/text/convert.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/core/text/StrFormatter.java` | 框架核心 | 混合 | `src/common/core/text/str_formatter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/BusinessStatus.java` | 枚举 | 纯逻辑 | `src/common/enums/business_status.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/BusinessStatusEnum.java` | 枚举 | 纯逻辑 | `src/common/enums/business_status_enum.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/BusinessType.java` | 枚举 | 纯逻辑 | `src/common/enums/business_type.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/DataSourceType.java` | 枚举 | 纯逻辑 | `src/common/enums/data_source_type.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/DesensitizedType.java` | 枚举 | 纯逻辑 | `src/common/enums/desensitized_type.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/FlowBusinessTypeEnum.java` | 枚举 | 纯逻辑 | `src/common/enums/flow_business_type_enum.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/FlowTypeEnum.java` | 枚举 | 纯逻辑 | `src/common/enums/flow_type_enum.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/HttpMethod.java` | 枚举 | 纯逻辑 | `src/common/enums/http_method.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/LimitType.java` | 枚举 | 纯逻辑 | `src/common/enums/limit_type.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/OperatorType.java` | 枚举 | 纯逻辑 | `src/common/enums/operator_type.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/enums/UserStatus.java` | 枚举 | 纯逻辑 | `src/common/enums/user_status.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/base/BaseException.java` | 异常类型 | 纯逻辑 | `src/common/exception/base/base_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/BaseException.java` | 异常类型 | 纯逻辑 | `src/common/exception/base_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/CustomException.java` | 异常类型 | 纯逻辑 | `src/common/exception/custom_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/DemoModeException.java` | 异常类型 | 纯逻辑 | `src/common/exception/demo_mode_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileException.java` | 异常类型 | 纯逻辑 | `src/common/exception/file/file_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileNameLengthLimitExceededException.java` | 异常类型 | 纯逻辑 | `src/common/exception/file/file_name_length_limit_exceeded_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileSizeLimitExceededException.java` | 异常类型 | 纯逻辑 | `src/common/exception/file/file_size_limit_exceeded_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileUploadException.java` | 异常类型 | 纯逻辑 | `src/common/exception/file/file_upload_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/file/InvalidExtensionException.java` | 异常类型 | 纯逻辑 | `src/common/exception/file/invalid_extension_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/GlobalException.java` | 异常类型 | 纯逻辑 | `src/common/exception/global_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/job/TaskException.java` | 异常类型 | 纯逻辑 | `src/common/exception/job/task_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/ServiceException.java` | 异常类型 | 纯逻辑 | `src/common/exception/service_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/BlackListException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/black_list_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/CaptchaException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/captcha_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/CaptchaExpireException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/captcha_expire_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/user_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserNotExistsException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/user_not_exists_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserPasswordNotMatchException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/user_password_not_match_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/user/UserPasswordRetryLimitExceedException.java` | 异常类型 | 纯逻辑 | `src/common/exception/user/user_password_retry_limit_exceed_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/exception/UtilException.java` | 异常类型 | 纯逻辑 | `src/common/exception/util_exception.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/filter/PropertyPreExcludeFilter.java` | Servlet 过滤器 | 框架契约 | `src/common/filter/property_pre_exclude_filter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/filter/RepeatableFilter.java` | Servlet 过滤器 | 框架契约 | `src/common/filter/repeatable_filter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/filter/RepeatedlyRequestWrapper.java` | Servlet 过滤器 | 框架契约 | `src/common/filter/repeatedly_request_wrapper.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java` | Servlet 过滤器 | 框架契约 | `src/common/filter/xss_filter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/filter/XssHttpServletRequestWrapper.java` | Servlet 过滤器 | 框架契约 | `src/common/filter/xss_http_servlet_request_wrapper.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/flow/Audit.java` | 其他 | 混合 | `src/common/flow/audit.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/flow/AuditContext.java` | 其他 | 混合 | `src/common/flow/audit_context.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/flow/Flow.java` | 其他 | 混合 | `src/common/flow/flow.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/flow/FlowAttribute.java` | 其他 | 混合 | `src/common/flow/flow_attribute.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/AliyunSMSUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/aliyun_sms_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/Arith.java` | 其他 | 混合 | `src/common/utils/arith.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/bean/BeanUtils.java` | Domain/DTO/VO | 纯逻辑 | `src/common/utils/bean/bean_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/bean/BeanValidators.java` | Domain/DTO/VO | 纯逻辑 | `src/common/utils/bean/bean_validators.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/CommonUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/common_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/DateUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/date_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/DesensitizedUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/desensitized_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/DictUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/dict_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/ExceptionUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/exception_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileTypeUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/file/file_type_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/file/file_upload_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/file/file_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/file/ImageUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/file/image_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/file/MimeTypeUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/file/mime_type_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/html/EscapeUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/html/escape_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/html/HTMLFilter.java` | 其他 | 混合 | `src/common/utils/html/html_filter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/http/HttpHelper.java` | 其他 | 混合 | `src/common/utils/http/http_helper.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/http/HttpUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/http/http_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssEndpoint.java` | 其他 | 混合 | `src/common/utils/http/oss_endpoint.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssTemplate.java` | 其他 | 混合 | `src/common/utils/http/oss_template.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/IdempotentUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/idempotent_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/AddressUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/ip/address_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/IpUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/ip/ip_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/LogUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/log_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/MessageUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/message_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/ModelUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/model_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/MultipartFileUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/multipart_file_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/PageUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/page_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelHandlerAdapter.java` | 其他 | 混合 | `src/common/utils/poi/excel_handler_adapter.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/poi/excel_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/reflect/ReflectUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/reflect/reflect_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/SecuritySHA1Utils.java` | 工具类 | 纯逻辑 | `src/common/utils/security_sha1_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/SecurityUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/security_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/ServletUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/servlet_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/sign/Base64.java` | 其他 | 混合 | `src/common/utils/sign/base64.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/sign/Md5Utils.java` | 工具类 | 纯逻辑 | `src/common/utils/sign/md5_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/SnowflakeIdWorker.java` | 其他 | 混合 | `src/common/utils/snowflake_id_worker.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/spring/SpringUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/spring/spring_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/sql/SqlUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/sql/sql_util.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/StringUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/string_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/Threads.java` | 其他 | 混合 | `src/common/utils/threads.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/IdUtils.java` | 工具类 | 纯逻辑 | `src/common/utils/uuid/id_utils.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/Seq.java` | 其他 | 混合 | `src/common/utils/uuid/seq.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/UUID.java` | 其他 | 混合 | `src/common/utils/uuid/uuid.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/xss/Xss.java` | 其他 | 混合 | `src/common/xss/xss.rs` |
| `ruoyi-common/src/main/java/com/ruoyi/common/xss/XssValidator.java` | 其他 | 混合 | `src/common/xss/xss_validator.rs` |

## ruoyi-framework（48）

| Java | 职责 | 类型 | Rust 目标 |
|---|---|---|---|
| `ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/DataScopeAspect.java` | AOP 切面 | 框架契约 | `src/framework/aspectj/data_scope_aspect.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/DataSourceAspect.java` | AOP 切面 | 框架契约 | `src/framework/aspectj/data_source_aspect.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/LogAspect.java` | AOP 切面 | 框架契约 | `src/framework/aspectj/log_aspect.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/RateLimiterAspect.java` | AOP 切面 | 框架契约 | `src/framework/aspectj/rate_limiter_aspect.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/ApplicationConfig.java` | 配置装配 | 框架契约 | `src/framework/config/application_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/CaptchaConfig.java` | 配置装配 | 框架契约 | `src/framework/config/captcha_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/DruidConfig.java` | 配置装配 | 框架契约 | `src/framework/config/druid_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/ElasticsearchConfig.java` | 配置装配 | 框架契约 | `src/framework/config/elasticsearch_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/FastJson2JsonRedisSerializer.java` | 配置装配 | 框架契约 | `src/framework/config/fast_json2_json_redis_serializer.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/FilterConfig.java` | 配置装配 | 框架契约 | `src/framework/config/filter_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/I18nConfig.java` | 配置装配 | 框架契约 | `src/framework/config/i18n_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/KafkaConfig.java` | 配置装配 | 框架契约 | `src/framework/config/kafka_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/KaptchaTextCreator.java` | 配置装配 | 框架契约 | `src/framework/config/kaptcha_text_creator.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/MyBatisConfig.java` | 配置装配 | 框架契约 | `src/framework/config/my_batis_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/MyBatisPlusConfig.java` | 配置装配 | 框架契约 | `src/framework/config/my_batis_plus_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/properties/DruidProperties.java` | 配置装配 | 框架契约 | `src/framework/config/properties/druid_properties.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/properties/PermitAllUrlProperties.java` | 配置装配 | 框架契约 | `src/framework/config/properties/permit_all_url_properties.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/RedisConfig.java` | 配置装配 | 框架契约 | `src/framework/config/redis_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/ResourcesConfig.java` | 配置装配 | 框架契约 | `src/framework/config/resources_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java` | 配置装配 | 框架契约 | `src/framework/config/security_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/ServerConfig.java` | 配置装配 | 框架契约 | `src/framework/config/server_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/config/ThreadPoolConfig.java` | 配置装配 | 框架契约 | `src/framework/config/thread_pool_config.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/datasource/DynamicDataSource.java` | 其他 | 混合 | `src/framework/datasource/dynamic_data_source.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/datasource/DynamicDataSourceContextHolder.java` | 其他 | 混合 | `src/framework/datasource/dynamic_data_source_context_holder.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/impl/SameUrlDataInterceptor.java` | 拦截器 | 框架契约 | `src/framework/interceptor/impl/same_url_data_interceptor.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/RepeatSubmitInterceptor.java` | 拦截器 | 框架契约 | `src/framework/interceptor/repeat_submit_interceptor.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/manager/AsyncManager.java` | 后台管理器 | 混合 | `src/framework/manager/async_manager.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/manager/factory/AsyncFactory.java` | 后台管理器 | 混合 | `src/framework/manager/factory/async_factory.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/manager/ShutdownManager.java` | 后台管理器 | 混合 | `src/framework/manager/shutdown_manager.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/security/context/AuthenticationContextHolder.java` | 其他 | 混合 | `src/framework/security/context/authentication_context_holder.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/security/context/PermissionContextHolder.java` | 其他 | 混合 | `src/framework/security/context/permission_context_holder.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/security/filter/JwtAuthenticationTokenFilter.java` | Servlet 过滤器 | 框架契约 | `src/framework/security/filter/jwt_authentication_token_filter.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/AuthenticationEntryPointImpl.java` | 其他 | 混合 | `src/framework/security/handle/authentication_entry_point_impl.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/LogoutSuccessHandlerImpl.java` | 其他 | 混合 | `src/framework/security/handle/logout_success_handler_impl.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Cpu.java` | Domain/DTO/VO | 纯逻辑 | `src/framework/web/domain/server/cpu.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Jvm.java` | Domain/DTO/VO | 纯逻辑 | `src/framework/web/domain/server/jvm.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Mem.java` | Domain/DTO/VO | 纯逻辑 | `src/framework/web/domain/server/mem.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/Sys.java` | Domain/DTO/VO | 纯逻辑 | `src/framework/web/domain/server/sys.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/SysFileInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/framework/web/domain/server/sys_file_info.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/Server.java` | Domain/DTO/VO | 纯逻辑 | `src/framework/web/domain/server.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/exception/GlobalExceptionHandler.java` | 异常类型 | 纯逻辑 | `src/framework/web/exception/global_exception_handler.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/PermissionService.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/permission_service.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysLoginService.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/sys_login_service.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysPasswordService.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/sys_password_service.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysPermissionService.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/sys_permission_service.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysRegisterService.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/sys_register_service.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/TokenService.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/token_service.rs` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/UserDetailsServiceImpl.java` | Service 接口/服务 | 框架契约 | `src/framework/web/service/user_details_service_impl.rs` |

## ruoyi-system（380）

| Java | 职责 | 类型 | Rust 目标 |
|---|---|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/BaseConfigServiceArea.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/base_config_service_area.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/CarParaVO.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/car_para_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/CarVO.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/car_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/CarWarningConfig.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/car_warning_config.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztFwqjcxx.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/dwd_lczt_fwqjcxx.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztSfsjcxx.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/dwd_lczt_sfsjcxx.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztSfzjcxx.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/dwd_lczt_sfzjcxx.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/Geometry.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/geometry.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsCxztFwqclls.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_cxzt_fwqclls.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeGantryFusion01.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_lwzxsfsj_fee_gantry_fusion01.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeRecords01.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_lwzxsfsj_fee_records01.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationEnter01.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_lwzxsfsj_fee_station_enter01.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationExit01.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_lwzxsfsj_fee_station_exit01.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowAddcode.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_rt_szdn_snapshot_flow_addcode.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowProvcaptureAddcode.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_rt_szdn_snapshot_flow_provcapture_addcode.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowStationcaptureAddcode.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_rt_szdn_snapshot_flow_stationcapture_addcode.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantry.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_szdn_gantry.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantryIp.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_szdn_gantry_ip.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnProvinceBorderVehicleWeightNewstructure.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_szdn_province_border_vehicle_weight_newstructure.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnSection.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_szdn_section.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnToll.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_szdn_toll.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnTollStationIp.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_szdn_toll_station_ip.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsYhglVBaseOrg.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/ods_yhgl_v_base_org.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/Path.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/path.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/PathQueryRo.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/path_query_ro.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/PathResult.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/path_result.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/ResData.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/res_data.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/SegmentRoutes.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/segment_routes.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/SuspiciousCarVO.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/suspicious_car_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailBo.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/trail_bo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailDevBO.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/trail_dev_bo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailDevCountBO.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/trail_dev_count_bo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/trail_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataLocationDict.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/zdata_location_dict.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailFitting.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/zdata_trail_fitting.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailTracks.java` | Domain/DTO/VO | 纯逻辑 | `src/base/domain/zdata_trail_tracks.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/elasticsearch/document/SnapshotFlowDocument.java` | Elasticsearch 接入 | 混合 | `src/base/elasticsearch/document/snapshot_flow_document.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/elasticsearch/service/SnapshotFlowElasticsearchService.java` | Elasticsearch 接入 | 混合 | `src/base/elasticsearch/service/snapshot_flow_elasticsearch_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/DebeziumReadonlyKafkaConsumer.java` | Kafka 消费者 | 混合 | `src/base/kafka/consumer/debezium_readonly_kafka_consumer.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/DebeziumSnapshotFlowKafkaConsumer.java` | Kafka 消费者 | 混合 | `src/base/kafka/consumer/debezium_snapshot_flow_kafka_consumer.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/SnapshotFlowKafkaConsumer.java` | Kafka 消费者 | 混合 | `src/base/kafka/consumer/snapshot_flow_kafka_consumer.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/SnapshotFlowKafkaConsumerV2.java` | Kafka 消费者 | 混合 | `src/base/kafka/consumer/snapshot_flow_kafka_consumer_v2.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/BaseConfigServiceAreaMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/base_config_service_area_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/CarWarningConfigMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/car_warning_config_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/DwdLcztFwqjcxxMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/dwd_lczt_fwqjcxx_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/DwdLcztSfsjcxxMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/dwd_lczt_sfsjcxx_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/DwdLcztSfzjcxxMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/dwd_lczt_sfzjcxx_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/GeometryMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/geometry_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsCxztFwqcllsMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_cxzt_fwqclls_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsLwzxsfsjFeeGantryFusion01Mapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_lwzxsfsj_fee_gantry_fusion01_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsLwzxsfsjFeeRecords01Mapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_lwzxsfsj_fee_records01_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsLwzxsfsjFeeStationEnter01Mapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_lwzxsfsj_fee_station_enter01_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsLwzxsfsjFeeStationExit01Mapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_lwzxsfsj_fee_station_exit01_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowAddcodeMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_rt_szdn_snapshot_flow_addcode_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowAddcodeMapperExample.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_rt_szdn_snapshot_flow_addcode_mapper_example.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_rt_szdn_snapshot_flow_provcapture_addcode_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_rt_szdn_snapshot_flow_stationcapture_addcode_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnGantryIpMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_szdn_gantry_ip_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnGantryMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_szdn_gantry_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_szdn_province_border_vehicle_weight_newstructure_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnSectionMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_szdn_section_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnTollMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_szdn_toll_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnTollStationIpMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_szdn_toll_station_ip_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsYhglVBaseOrgMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/ods_yhgl_v_base_org_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/ShardingSnapshotFlowMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/sharding_snapshot_flow_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/SnapshotFlowMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/snapshot_flow_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/ZdataLocationDictMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/zdata_location_dict_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/ZdataTrailFittingMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/zdata_trail_fitting_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/ZdataTrailTracksMapper.java` | Mapper 接口 | 框架契约 | `src/base/mapper/zdata_trail_tracks_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cache/PartitionMappingCache.java` | Service 接口/服务 | 框架契约 | `src/base/service/cache/partition_mapping_cache.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcConfig.java` | CDC 同步服务 | 混合 | `src/base/service/cdc/cdc_config.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcMessage.java` | CDC 同步服务 | 混合 | `src/base/service/cdc/cdc_message.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcRetryTask.java` | CDC 同步服务 | 混合 | `src/base/service/cdc/cdc_retry_task.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcSyncService.java` | CDC 同步服务 | 混合 | `src/base/service/cdc/cdc_sync_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/DeadLetterQueueService.java` | CDC 同步服务 | 混合 | `src/base/service/cdc/dead_letter_queue_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/consistency/DataConsistencyService.java` | 数据一致性任务 | 纯逻辑 | `src/base/service/consistency/data_consistency_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/CrossMonthQueryService.java` | 分表增强查询 | 纯逻辑 | `src/base/service/enhanced/cross_month_query_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/SnapshotFlowEnhancedService.java` | 分表增强查询 | 纯逻辑 | `src/base/service/enhanced/snapshot_flow_enhanced_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/ViewMaintenanceOptimizationService.java` | 分表增强查询 | 纯逻辑 | `src/base/service/enhanced/view_maintenance_optimization_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/ViewMaintenancePerformanceService.java` | 分表增强查询 | 纯逻辑 | `src/base/service/enhanced/view_maintenance_performance_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpBaseInfoApiService.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/http_base_info_api_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeGantryFusion01Service.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/http_ods_lwzxsfsj_fee_gantry_fusion01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeRecords01Service.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/http_ods_lwzxsfsj_fee_records01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeStationExit01Service.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/http_ods_lwzxsfsj_fee_station_exit01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsRtSzdnSnapshotFlowAddcodeService.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/http_ods_rt_szdn_snapshot_flow_addcode_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpSysUtilApiService.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/http_sys_util_api_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/IHenDaApi.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/i_hen_da_api.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/RoadPathApi.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/base/service/forest/road_path_api.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IBaseConfigServiceAreaService.java` | Service 接口/服务 | 框架契约 | `src/base/service/base_config_service_area_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/ICarWarningConfigService.java` | Service 接口/服务 | 框架契约 | `src/base/service/car_warning_config_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztFwqjcxxService.java` | Service 接口/服务 | 框架契约 | `src/base/service/dwd_lczt_fwqjcxx_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztSfsjcxxService.java` | Service 接口/服务 | 框架契约 | `src/base/service/dwd_lczt_sfsjcxx_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztSfzjcxxService.java` | Service 接口/服务 | 框架契约 | `src/base/service/dwd_lczt_sfzjcxx_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IGeometryService.java` | Service 接口/服务 | 框架契约 | `src/base/service/geometry_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IHenDaService.java` | Service 接口/服务 | 框架契约 | `src/base/service/hen_da_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/BaseConfigServiceAreaServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/base_config_service_area_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/CarWarningConfigServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/car_warning_config_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztFwqjcxxServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/dwd_lczt_fwqjcxx_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztSfsjcxxServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/dwd_lczt_sfsjcxx_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztSfzjcxxServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/dwd_lczt_sfzjcxx_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/GeometryServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/geometry_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/HenDaServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/hen_da_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsCxztFwqcllsServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_cxzt_fwqclls_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeGantryFusion01ServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_lwzxsfsj_fee_gantry_fusion01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeRecords01ServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_lwzxsfsj_fee_records01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeStationEnter01ServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_lwzxsfsj_fee_station_enter01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeStationExit01ServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_lwzxsfsj_fee_station_exit01_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowAddcodeServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_rt_szdn_snapshot_flow_addcode_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowProvcaptureAddcodeServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_rt_szdn_snapshot_flow_provcapture_addcode_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowStationcaptureAddcodeServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_rt_szdn_snapshot_flow_stationcapture_addcode_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnGantryIpServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_szdn_gantry_ip_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnGantryServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_szdn_gantry_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnProvinceBorderVehicleWeightNewstructureServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_szdn_province_border_vehicle_weight_newstructure_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnSectionServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_szdn_section_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnTollServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_szdn_toll_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnTollStationIpServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_szdn_toll_station_ip_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsYhglVBaseOrgServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/ods_yhgl_v_base_org_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/PartitionQueryServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/partition_query_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/RoadPathImpl.java` | Service 实现 | 混合 | `src/base/service/impl/road_path_impl.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataLocationDictServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/zdata_location_dict_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailFittingServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/zdata_trail_fitting_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailTracksServiceImpl.java` | Service 实现 | 混合 | `src/base/service/service/zdata_trail_tracks_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsCxztFwqcllsService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_cxzt_fwqclls_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeGantryFusion01Service.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_lwzxsfsj_fee_gantry_fusion01_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeRecords01Service.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_lwzxsfsj_fee_records01_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeStationEnter01Service.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_lwzxsfsj_fee_station_enter01_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeStationExit01Service.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_lwzxsfsj_fee_station_exit01_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowAddcodeService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_rt_szdn_snapshot_flow_addcode_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_rt_szdn_snapshot_flow_provcapture_addcode_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowStationcaptureAddcodeService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_rt_szdn_snapshot_flow_stationcapture_addcode_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnGantryIpService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_szdn_gantry_ip_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnGantryService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_szdn_gantry_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnProvinceBorderVehicleWeightNewstructureService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_szdn_province_border_vehicle_weight_newstructure_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnSectionService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_szdn_section_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnTollService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_szdn_toll_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnTollStationIpService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_szdn_toll_station_ip_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsYhglVBaseOrgService.java` | Service 接口/服务 | 框架契约 | `src/base/service/ods_yhgl_v_base_org_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IPartitionQueryService.java` | Service 接口/服务 | 框架契约 | `src/base/service/partition_query_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IRoadPathService.java` | Service 接口/服务 | 框架契约 | `src/base/service/road_path_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataLocationDictService.java` | Service 接口/服务 | 框架契约 | `src/base/service/zdata_location_dict_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataTrailFittingService.java` | Service 接口/服务 | 框架契约 | `src/base/service/zdata_trail_fitting_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataTrailTracksService.java` | Service 接口/服务 | 框架契约 | `src/base/service/zdata_trail_tracks_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/query/PartitionParallelQueryService.java` | 分区并行查询 | 纯逻辑 | `src/base/service/query/partition_parallel_query_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/sharding/AbstractShardingSyncService.java` | 分表算法/配置 | 混合 | `src/base/service/sharding/abstract_sharding_sync_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/sharding/ShardingIdCacheService.java` | 分表算法/配置 | 混合 | `src/base/service/sharding/sharding_id_cache_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/sharding/ShardingQueryService.java` | 分表算法/配置 | 混合 | `src/base/service/sharding/sharding_query_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/sharding/ShardingSyncService.java` | 分表算法/配置 | 混合 | `src/base/service/sharding/sharding_sync_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/FeeRecordsDayShardingAlgorithm.java` | 分表算法/配置 | 混合 | `src/base/sharding/fee_records_day_sharding_algorithm.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingConfig.java` | 分表算法/配置 | 混合 | `src/base/sharding/sharding_config.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java` | 分表算法/配置 | 混合 | `src/base/sharding/sharding_table_util.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/SnapshotFlowMonthShardingAlgorithm.java` | 分表算法/配置 | 混合 | `src/base/sharding/snapshot_flow_month_sharding_algorithm.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/task/ShardingTableTask.java` | 定时/后台任务 | 混合 | `src/base/task/sharding_table_task.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/task/ViewMaintenanceTask.java` | 定时/后台任务 | 混合 | `src/base/task/view_maintenance_task.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/util/EncryptUtils.java` | 工具类 | 纯逻辑 | `src/base/util/encrypt_utils.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/util/GpsUtil.java` | 工具类 | 纯逻辑 | `src/base/util/gps_util.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/base/util/LonLatPathsUtils.java` | 工具类 | 纯逻辑 | `src/base/util/lon_lat_paths_utils.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/annotation/Trace.java` | 注解（编译期标记） | 框架契约 | `src/common/core/annotation/trace.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/aspect/TraceAspect.java` | AOP 切面 | 框架契约 | `src/common/core/aspect/trace_aspect.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/config/MonitorAutoConfiguration.java` | 配置装配 | 框架契约 | `src/common/core/config/monitor_auto_configuration.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/context/TraceContext.java` | 框架核心 | 混合 | `src/common/core/context/trace_context.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/domain/MonitorResponse.java` | Domain/DTO/VO | 纯逻辑 | `src/common/core/domain/monitor_response.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/exception/BusinessException.java` | 异常类型 | 纯逻辑 | `src/common/core/exception/business_exception.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/exception/GlobalExceptionTraceHandler.java` | 异常类型 | 纯逻辑 | `src/common/core/exception/global_exception_trace_handler.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/filter/TraceIdFilter.java` | Servlet 过滤器 | 框架契约 | `src/common/core/filter/trace_id_filter.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/monitor/AlertEngine.java` | 框架核心 | 混合 | `src/common/core/monitor/alert_engine.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/monitor/MetricCollector.java` | 框架核心 | 混合 | `src/common/core/monitor/metric_collector.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/core/monitor/SqlLogInterceptor.java` | 框架核心 | 混合 | `src/common/core/monitor/sql_log_interceptor.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/common/utils/SnowflakeIdUtil.java` | 工具类 | 纯逻辑 | `src/common/utils/snowflake_id_util.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/EntrustInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/entrust_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowApplyInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_apply_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowCurrentNode.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_current_node.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowList.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_list.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageDispose.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_message_dispose.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_message_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowName.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_name.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowTemplate.java` | Domain/DTO/VO | 纯逻辑 | `src/flow/domain/flow_template.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowApplyInfoMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_apply_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowCurrentNodeMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_current_node_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowListMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_list_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowMessageDisposeMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_message_dispose_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowMessageInfoMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_message_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowNameMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_name_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowTemplateMapper.java` | Mapper 接口 | 框架契约 | `src/flow/mapper/flow_template_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowApplyInfoService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_apply_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowCurrentNodeService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_current_node_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowListService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_list_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowMessageDisposeService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_message_dispose_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowMessageInfoService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_message_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowNameService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_name_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/IFlowTemplateService.java` | Service 接口/服务 | 框架契约 | `src/flow/service/flow_template_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowApplyInfoServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_apply_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowCurrentNodeServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_current_node_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowListServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_list_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowMessageDisposeServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_message_dispose_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowMessageInfoServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_message_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowNameServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_name_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowTemplateServiceImpl.java` | Service 实现 | 混合 | `src/flow/service/service/flow_template_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/util/FlowConstant.java` | 工具类 | 纯逻辑 | `src/flow/util/flow_constant.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/BussTest.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/buss_test.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarAduitFree.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_aduit_free.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarConfimFree.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_confim_free.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarExceptRecord.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_except_record.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarFeeRecord.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_fee_record.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarQueryLog.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_query_log.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteDetail.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_route_detail.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_route_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSplitRecord.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_split_record.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspicious.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_suspicious.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousBack.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_suspicious_back.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousCheck.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_suspicious_check.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarTrackInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_track_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_warning_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningRule.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_warning_rule.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWhiteInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/car_white_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/dto/BigScreenParam.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/dto/big_screen_param.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/dto/CursorPageResult.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/dto/cursor_page_result.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/dto/SnapshotCursorPageQuery.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/dto/snapshot_cursor_page_query.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryCar.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/gantry_car.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryTradeInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/gantry_trade_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/TWaybill.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/t_waybill.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/TWaybillAddress.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/t_waybill_address.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/TWaybillCargo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/t_waybill_cargo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/TWaybillRoute.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/t_waybill_route.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/BaseBigScreenVo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/base_big_screen_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarAuditVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/car_audit_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarInfoVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/car_info_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarLocationParam.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/car_location_param.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarLocationVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/car_location_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarStatisticsVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/car_statistics_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/center/CenterStatisticsVo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/center/center_statistics_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/center/OrderAndEnterpriseInfoVo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/center/order_and_enterprise_info_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/center/OrderAndEnterpriseVo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/center/order_and_enterprise_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/center/OrderDetailVo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/center/order_detail_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/center/TrackPoint.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/center/track_point.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/center/TransitOrderDetailVo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/center/transit_order_detail_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/IncomeStatisticParam.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/income_statistic_param.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/incomeStatisticVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/income_statistic_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/OrgVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/org_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/SectionVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/section_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/TollGantryFwqVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/toll_gantry_fwq_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/TopTenVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/bigscreen/top_ten_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/CarConfimFreeQueryRo.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/car_confim_free_query_ro.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCCarStatisticsDetailVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/pc_car_statistics_detail_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCCarStatisticsVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/pc_car_statistics_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCIncomeStaticsVO.java` | Domain/DTO/VO | 纯逻辑 | `src/manager/domain/vo/pc_income_statics_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/BussTestMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/buss_test_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarAduitFreeMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_aduit_free_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarConfimFreeMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_confim_free_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarExceptRecordMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_except_record_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarFeeRecordMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_fee_record_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarInfoMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarQueryLogMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_query_log_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarRouteDetailMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_route_detail_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarRouteInfoMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_route_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarSplitRecordMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_split_record_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarSuspiciousBackMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_suspicious_back_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarSuspiciousCheckMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_suspicious_check_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarSuspiciousMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_suspicious_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarTrackInfoMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_track_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarWarningInfoMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_warning_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarWarningRuleMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_warning_rule_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/CarWhiteInfoMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/car_white_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/GantryCarMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/gantry_car_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/mapper/GantryTradeInfoMapper.java` | Mapper 接口 | 框架契约 | `src/manager/mapper/gantry_trade_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/IBussTestService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/buss_test_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarAduitFreeService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_aduit_free_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarConfimFreeService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_confim_free_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarExceptRecordService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_except_record_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarFeeRecordService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_fee_record_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarInfoService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarQueryLogService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_query_log_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarRouteDetailService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_route_detail_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarRouteInfoService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_route_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSplitRecordService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_split_record_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousBackService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_suspicious_back_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousCheckService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_suspicious_check_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_suspicious_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarTrackInfoService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_track_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWarningInfoService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_warning_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWarningRuleService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_warning_rule_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWhiteInfoService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/car_white_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/IGantryCarService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/gantry_car_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/IGantryTradeInfoService.java` | Service 接口/服务 | 框架契约 | `src/manager/service/gantry_trade_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/BussTestServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/buss_test_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarAduitFreeServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_aduit_free_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarConfimFreeServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_confim_free_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarExceptRecordServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_except_record_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarFeeRecordServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_fee_record_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarQueryLogServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_query_log_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarRouteDetailServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_route_detail_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarRouteInfoServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_route_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSplitRecordServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_split_record_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousBackServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_suspicious_back_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousCheckServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_suspicious_check_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_suspicious_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarTrackInfoServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_track_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningInfoServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_warning_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningRuleServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_warning_rule_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWhiteInfoServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/car_white_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/GantryCarServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/gantry_car_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/GantryTradeInfoServiceImpl.java` | Service 实现 | 混合 | `src/manager/service/service/gantry_trade_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/ro/UploadByUrlRo.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/ro/upload_by_url_ro.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/ro/UploadRo.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/ro/upload_ro.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysCache.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_cache.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysConfig.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_config.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysFile.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_file.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysIndexMenu.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_index_menu.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysLogininfor.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_logininfor.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysNotice.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_notice.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysOperLog.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_oper_log.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysPost.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_post.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysRoleDept.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_role_dept.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysRoleMenu.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_role_menu.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUpgradeInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_upgrade_info.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUserOnline.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_user_online.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUserPost.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_user_post.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUserRole.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_user_role.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/SysUtil.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/sys_util.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/MetaVo.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/vo/meta_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/RouterVo.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/vo/router_vo.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/SealParmras.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/vo/seal_parmras.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/SealResult.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/vo/seal_result.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/SealResultData.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/vo/seal_result_data.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/UserRoleModel.java` | Domain/DTO/VO | 纯逻辑 | `src/system/domain/vo/user_role_model.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysConfigMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_config_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDeptMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_dept_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDictDataMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_dict_data_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysDictTypeMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_dict_type_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysFileMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_file_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysIndexMenuMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_index_menu_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysLogininforMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_logininfor_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysMenuMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_menu_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysNoticeMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_notice_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysOperLogMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_oper_log_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysPostMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_post_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysRoleDeptMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_role_dept_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysRoleMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_role_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysRoleMenuMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_role_menu_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUpgradeInfoMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_upgrade_info_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_user_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserPostMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_user_post_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUserRoleMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_user_role_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysUtilMapper.java` | Mapper 接口 | 框架契约 | `src/system/mapper/sys_util_mapper.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/forest/FileApi.java` | 外部 HTTP 客户端（Forest） | 框架契约 | `src/system/service/forest/file_api.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SMSServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sms_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysConfigServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_config_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDeptServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_dept_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictDataServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_dict_data_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictTypeServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_dict_type_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_file_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysIndexMenuServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_index_menu_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysLogininforServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_logininfor_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_menu_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysNoticeServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_notice_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysOperLogServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_oper_log_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysPostServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_post_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysRoleServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_role_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUpgradeInfoServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_upgrade_info_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserOnlineServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_user_online_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_user_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUtilServiceImpl.java` | Service 实现 | 混合 | `src/system/service/service/sys_util_service.rs` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysConfigService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_config_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysDeptService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_dept_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysDictDataService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_dict_data_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysDictTypeService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_dict_type_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysFileService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_file_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysIndexMenuService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_index_menu_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysLogininforService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_logininfor_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysMenuService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_menu_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysNoticeService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_notice_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysOperLogService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_oper_log_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysPostService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_post_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysRoleService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_role_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUpgradeInfoService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_upgrade_info_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUserOnlineService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_user_online_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUserService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_user_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/ISysUtilService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sys_util_service.rs（与实现合并）` |
| `ruoyi-system/src/main/java/com/ruoyi/system/service/SMSService.java` | Service 接口/服务 | 框架契约 | `src/system/service/sms_service.rs` |

## ruoyi-quartz（23）

| Java | 职责 | 类型 | Rust 目标 |
|---|---|---|---|
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/config/ScheduleConfig.java` | 配置装配 | 框架契约 | `src/quartz/config/schedule_config.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/quartz/sys_job_controller.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/quartz/sys_job_log_controller.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJob.java` | Domain/DTO/VO | 纯逻辑 | `src/quartz/domain/sys_job.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/domain/SysJobLog.java` | Domain/DTO/VO | 纯逻辑 | `src/quartz/domain/sys_job_log.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/mapper/SysJobLogMapper.java` | Mapper 接口 | 框架契约 | `src/quartz/mapper/sys_job_log_mapper.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/mapper/SysJobMapper.java` | Mapper 接口 | 框架契约 | `src/quartz/mapper/sys_job_mapper.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobLogServiceImpl.java` | Service 实现 | 混合 | `src/quartz/service/service/sys_job_log_service.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/impl/SysJobServiceImpl.java` | Service 实现 | 混合 | `src/quartz/service/service/sys_job_service.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/ISysJobLogService.java` | Service 接口/服务 | 框架契约 | `src/quartz/service/sys_job_log_service.rs（与实现合并）` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/service/ISysJobService.java` | Service 接口/服务 | 框架契约 | `src/quartz/service/sys_job_service.rs（与实现合并）` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/OrgTask.java` | 定时/后台任务 | 混合 | `src/quartz/task/org_task.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/PartitionMaintenanceTask.java` | 定时/后台任务 | 混合 | `src/quartz/task/partition_maintenance_task.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/RyTask.java` | 定时/后台任务 | 混合 | `src/quartz/task/ry_task.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java` | 定时/后台任务 | 混合 | `src/quartz/task/snapshot_flow_sync_task.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/TrackTask.java` | 定时/后台任务 | 混合 | `src/quartz/task/track_task.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java` | 定时/后台任务 | 混合 | `src/quartz/task/vehicle_monitoring_task.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/AbstractQuartzJob.java` | 工具类 | 纯逻辑 | `src/quartz/util/abstract_quartz_job.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/CronUtils.java` | 工具类 | 纯逻辑 | `src/quartz/util/cron_utils.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/JobInvokeUtil.java` | 工具类 | 纯逻辑 | `src/quartz/util/job_invoke_util.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzDisallowConcurrentExecution.java` | 工具类 | 纯逻辑 | `src/quartz/util/quartz_disallow_concurrent_execution.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/QuartzJobExecution.java` | 工具类 | 纯逻辑 | `src/quartz/util/quartz_job_execution.rs` |
| `ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/ScheduleUtils.java` | 工具类 | 纯逻辑 | `src/quartz/util/schedule_utils.rs` |

## ruoyi-generator（19）

| Java | 职责 | 类型 | Rust 目标 |
|---|---|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/config/GenConfig.java` | 配置装配 | 框架契约 | `src/generator/config/gen_config.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java` | Controller（HTTP 路由） | 框架契约 | `src/api/generator/gen_controller.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/DictionaryInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/dictionary_info.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenColumnDialog.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/gen_column_dialog.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateRichTextInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/generate_rich_text_info.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateUploadInfo.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/generate_upload_info.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTable.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/gen_table.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTableColumn.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/gen_table_column.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/LinkTableField.java` | Domain/DTO/VO | 纯逻辑 | `src/generator/domain/link_table_field.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableColumnMapper.java` | Mapper 接口 | 框架契约 | `src/generator/mapper/gen_table_column_mapper.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableMapper.java` | Mapper 接口 | 框架契约 | `src/generator/mapper/gen_table_mapper.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableColumnServiceImpl.java` | Service 接口/服务 | 框架契约 | `src/generator/service/gen_table_column_service.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java` | Service 接口/服务 | 框架契约 | `src/generator/service/gen_table_service.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableColumnService.java` | Service 接口/服务 | 框架契约 | `src/generator/service/gen_table_column_service.rs（与实现合并）` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableService.java` | Service 接口/服务 | 框架契约 | `src/generator/service/gen_table_service.rs（与实现合并）` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/enumeration/LinkTableFiledTypeEnum.java` | 工具类 | 纯逻辑 | `src/generator/util/enumeration/link_table_filed_type_enum.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java` | 工具类 | 纯逻辑 | `src/generator/util/gen_utils.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityInitializer.java` | 工具类 | 纯逻辑 | `src/generator/util/velocity_initializer.rs` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityUtils.java` | 工具类 | 纯逻辑 | `src/generator/util/velocity_utils.rs` |
