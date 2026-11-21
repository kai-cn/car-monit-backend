# MAPPING_BASE.md — 基础数据（`com.ruoyi.web.controller.base`） Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
>
> 表由 `scripts/gen_mapping_docs.py` 从源码生成（`# Migrated from:` 行 + 方法级注解 +
> `create_app()` 真正注册的路由），**手改会被下次生成覆盖**：要改就改代码，再重跑脚本。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md)。
>
> 阅读约定：
>
> - `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
>   逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
> - Python 用 `snake_case`，Java 用 `camelCase`，转换是机械的：
>   `selectJobList` → `select_job_list`。
> - `@Log` 列写成 `title / businessType`；`—` 表示 Java 侧没有该注解。
> - 权限点列写的是 `@PreAuthorize("@ss.hasPermi('...')")` 里的那个串；`—` 表示没有权限注解
>   （只受「登录」保护）。
> - 路径列写的是 **Java 的 URI 模板**；Python 侧路径变量按 PEP8 改成 snake_case
>   （`{jobId}` → `{job_id}`、`{IDs}` → `{ids}`），路由匹配结果不受影响。

---

## 1. 切片概况

| 项 | 数 | 依据 |
|---|---|---|
| Java 控制器 | 26 | `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/` 下全部 `*Controller.java` |
| 端点 | 106 | 方法级注解展开后的条数（`value = {...}` 会展开成多条），与 `scripts/audit_endpoints.py` 的 Java 侧计数同源 |
| Python 控制器模块 | 25 | `app/api/base/` |
| Domain 对照行 | 36 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Mapper 对照行 | 48 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Service 对照行 | 65 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Util 对照行 | 3 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Sharding 对照行 | 2 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| 测试 | 164 | 见 §5 |

## 2. 要点

1. `OdsCxztFwqcllsController` 的文件在 `controller/base/` 下，路径却是 `/manager/fwqclls`，权限点也是 `manager:fwqclls:list` —— Java 原文如此，不是抄错。
2. `GeometryController#getHenDa` 用的是 **`base:geometry:list`**（不是 `:query`）：同一个控制器里 `getInfo` 反而没有权限点。
3. ODS 表的 `export` 一律用**列表权限**（`base:feerecords:list`、`base:snapshotflow:list`），只有配置类实体的 `export` 才有独立的 `:export` 权限点。
4. 导出端点（24 个，全工程口径）在 Java 里先 `ExcelUtil.exportExcel(response, ...)` 把 xlsx 写进响应流，末尾的 `return AjaxResult.success("导出成功")` **到不了客户端**；所以 Python 直接返回 `Response`，这是 `scripts/audit_envelopes.py` 里唯一放行的「`AjaxResult` → `Response`」情形（判定依据是 Java 形参里有 `HttpServletResponse`）。
5. `list`/`getInfo` 的 Python 函数名带业务后缀（`list_fwqclls`、`list_fee_gantries`、`list_geometries`），避免同名 `list` 在一个模块内重名；对应关系见 §4 表。

## 3. 文件级对照

### 3.1 api（25 行）

| Java | Python |
|---|---|
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/BaseConfigServiceAreaController.java` | `app/api/base/base_config_service_area_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CarWarningConfigController.java` | `app/api/base/car_warning_config_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CdcController.java` | `app/api/base/cdc_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztFwqjcxxController.java` | `app/api/base/dwd_lczt_fwqjcxx_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfsjcxxController.java` | `app/api/base/dwd_lczt_sfsjcxx_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfzjcxxController.java` | `app/api/base/dwd_lczt_sfzjcxx_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/GeometryController.java` | `app/api/base/geometry_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsCxztFwqcllsController.java` | `app/api/base/ods_cxzt_fwqclls_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java` | `app/api/base/ods_lwzxsfsj_fee_gantry_fusion01_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java` | `app/api/base/ods_lwzxsfsj_fee_records01_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationEnter01Controller.java` | `app/api/base/ods_lwzxsfsj_fee_station_enter01_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java` | `app/api/base/ods_lwzxsfsj_fee_station_exit01_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java` | `app/api/base/ods_rt_szdn_snapshot_flow_addcode_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeController.java` | `app/api/base/ods_rt_szdn_snapshot_flow_provcapture_addcode_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeController.java` | `app/api/base/ods_rt_szdn_snapshot_flow_stationcapture_addcode_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryController.java` | `app/api/base/ods_szdn_gantry_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryIpController.java` | `app/api/base/ods_szdn_gantry_ip_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnProvinceBorderVehicleWeightNewstructureController.java` | `app/api/base/ods_szdn_province_border_vehicle_weight_newstructure_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnSectionController.java` | `app/api/base/ods_szdn_section_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollController.java` | `app/api/base/ods_szdn_toll_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollStationIpController.java` | `app/api/base/ods_szdn_toll_station_ip_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsYhglVBaseOrgController.java` | `app/api/base/ods_yhgl_v_base_org_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataLocationDictController.java` | `app/api/base/zdata_location_dict_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java` | `app/api/base/zdata_trail_fitting_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailTracksController.java` | `app/api/base/zdata_trail_tracks_controller.py` |

### 3.2 domain（36 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/BaseConfigServiceArea.java` | `app/base/domain/base_config_service_area.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/CarParaVO.java` | `app/base/domain/car_para_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/CarVO.java` | `app/base/domain/car_vo.py` |
| `com/ruoyi/base/domain/CarWarningConfig.java` | `app/base/domain/car_warning_config.py` |
| `com/ruoyi/base/domain/DwdLcztFwqjcxx.java` | `app/base/domain/dwd_lczt_fwqjcxx.py` |
| `com/ruoyi/base/domain/DwdLcztSfsjcxx.java` | `app/base/domain/dwd_lczt_sfsjcxx.py` |
| `com/ruoyi/base/domain/DwdLcztSfzjcxx.java` | `app/base/domain/dwd_lczt_sfzjcxx.py` |
| `com/ruoyi/base/domain/Geometry.java` | `app/base/domain/geometry.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsCxztFwqclls.java` | `app/base/domain/ods_cxzt_fwqclls.py` |
| `com/ruoyi/base/domain/OdsLwzxsfsjFeeGantryFusion01.java` | `app/base/domain/ods_lwzxsfsj_fee_gantry_fusion01.py` |
| `com/ruoyi/base/domain/OdsLwzxsfsjFeeRecords01.java` | `app/base/domain/ods_lwzxsfsj_fee_records01.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationEnter01.java` | `app/base/domain/ods_lwzxsfsj_fee_station_enter01.py` |
| `com/ruoyi/base/domain/OdsLwzxsfsjFeeStationExit01.java` | `app/base/domain/ods_lwzxsfsj_fee_station_exit01.py` |
| `com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowAddcode.java` | `app/base/domain/ods_rt_szdn_snapshot_flow_addcode.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowProvcaptureAddcode.java` | `app/base/domain/ods_rt_szdn_snapshot_flow_provcapture_addcode.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowStationcaptureAddcode.java` | `app/base/domain/ods_rt_szdn_snapshot_flow_stationcapture_addcode.py` |
| `com/ruoyi/base/domain/OdsSzdnGantry.java` | `app/base/domain/ods_szdn_gantry.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantryIp.java` | `app/base/domain/ods_szdn_gantry_ip.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnProvinceBorderVehicleWeightNewstructure.java` | `app/base/domain/ods_szdn_province_border_vehicle_weight_newstructure.py` |
| `com/ruoyi/base/domain/OdsSzdnSection.java` | `app/base/domain/ods_szdn_section.py` |
| `com/ruoyi/base/domain/OdsSzdnToll.java` | `app/base/domain/ods_szdn_toll.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnTollStationIp.java` | `app/base/domain/ods_szdn_toll_station_ip.py` |
| `com/ruoyi/base/domain/OdsYhglVBaseOrg.java` | `app/base/domain/ods_yhgl_v_base_org.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/Path.java` | `app/base/domain/path.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/PathQueryRo.java` | `app/base/domain/path_query_ro.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/PathResult.java` | `app/base/domain/path_result.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/ResData.java` | `app/base/domain/res_data.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/SegmentRoutes.java` | `app/base/domain/segment_routes.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/SuspiciousCarVO.java` | `app/base/domain/suspicious_car_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailBo.java` | `app/base/domain/trail_bo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailDevBO.java` | `app/base/domain/trail_dev_bo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailDevCountBO.java` | `app/base/domain/trail_dev_count_bo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/TrailInfo.java` | `app/base/domain/trail_info.py` |
| `com/ruoyi/base/domain/ZdataLocationDict.java` | `app/base/domain/zdata_location_dict.py` |
| `com/ruoyi/base/domain/ZdataTrailFitting.java` | `app/base/domain/zdata_trail_fitting.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailTracks.java` | `app/base/domain/zdata_trail_tracks.py` |

### 3.3 mapper（48 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/BaseConfigServiceAreaMapper.java` | `app/base/mapper/base_config_service_area_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/BaseConfigServiceAreaMapper.xml` | `app/base/mapper/base_config_service_area_mapper.py` |
| `com/ruoyi/base/mapper/CarWarningConfigMapper.java` | `app/base/mapper/car_warning_config_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/CarWarningConfigMapper.xml` | `app/base/mapper/car_warning_config_mapper.py` |
| `com/ruoyi/base/mapper/DwdLcztFwqjcxxMapper.java` | `app/base/mapper/dwd_lczt_fwqjcxx_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/DwdLcztFwqjcxxMapper.xml` | `app/base/mapper/dwd_lczt_fwqjcxx_mapper.py` |
| `com/ruoyi/base/mapper/DwdLcztSfsjcxxMapper.java` | `app/base/mapper/dwd_lczt_sfsjcxx_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/DwdLcztSfsjcxxMapper.xml` | `app/base/mapper/dwd_lczt_sfsjcxx_mapper.py` |
| `com/ruoyi/base/mapper/DwdLcztSfzjcxxMapper.java` | `app/base/mapper/dwd_lczt_sfzjcxx_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/DwdLcztSfzjcxxMapper.xml` | `app/base/mapper/dwd_lczt_sfzjcxx_mapper.py` |
| `com/ruoyi/base/mapper/GeometryMapper.java` | `app/base/mapper/geometry_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml` | `app/base/mapper/geometry_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsCxztFwqcllsMapper.java` | `app/base/mapper/ods_cxzt_fwqclls_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsCxztFwqcllsMapper.xml` | `app/base/mapper/ods_cxzt_fwqclls_mapper.py` |
| `com/ruoyi/base/mapper/OdsLwzxsfsjFeeGantryFusion01Mapper.java` | `app/base/mapper/ods_lwzxsfsj_fee_gantry_fusion01_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeGantryFusion01Mapper.xml` | `app/base/mapper/ods_lwzxsfsj_fee_gantry_fusion01_mapper.py` |
| `com/ruoyi/base/mapper/OdsLwzxsfsjFeeRecords01Mapper.java` | `app/base/mapper/ods_lwzxsfsj_fee_records01_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeRecords01Mapper.xml` | `app/base/mapper/ods_lwzxsfsj_fee_records01_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsLwzxsfsjFeeStationEnter01Mapper.java` | `app/base/mapper/ods_lwzxsfsj_fee_station_enter01_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationEnter01Mapper.xml` | `app/base/mapper/ods_lwzxsfsj_fee_station_enter01_mapper.py` |
| `com/ruoyi/base/mapper/OdsLwzxsfsjFeeStationExit01Mapper.java` | `app/base/mapper/ods_lwzxsfsj_fee_station_exit01_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationExit01Mapper.xml` | `app/base/mapper/ods_lwzxsfsj_fee_station_exit01_mapper.py` |
| `com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowAddcodeMapper.java` | `app/base/mapper/ods_rt_szdn_snapshot_flow_addcode_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml` | `app/base/mapper/ods_rt_szdn_snapshot_flow_addcode_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.java` | `app/base/mapper/ods_rt_szdn_snapshot_flow_provcapture_addcode_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.xml` | `app/base/mapper/ods_rt_szdn_snapshot_flow_provcapture_addcode_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.java` | `app/base/mapper/ods_rt_szdn_snapshot_flow_stationcapture_addcode_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.xml` | `app/base/mapper/ods_rt_szdn_snapshot_flow_stationcapture_addcode_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnGantryIpMapper.java` | `app/base/mapper/ods_szdn_gantry_ip_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryIpMapper.xml` | `app/base/mapper/ods_szdn_gantry_ip_mapper.py` |
| `com/ruoyi/base/mapper/OdsSzdnGantryMapper.java` | `app/base/mapper/ods_szdn_gantry_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryMapper.xml` | `app/base/mapper/ods_szdn_gantry_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.java` | `app/base/mapper/ods_szdn_province_border_vehicle_weight_newstructure_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml` | `app/base/mapper/ods_szdn_province_border_vehicle_weight_newstructure_mapper.py` |
| `com/ruoyi/base/mapper/OdsSzdnSectionMapper.java` | `app/base/mapper/ods_szdn_section_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsSzdnSectionMapper.xml` | `app/base/mapper/ods_szdn_section_mapper.py` |
| `com/ruoyi/base/mapper/OdsSzdnTollMapper.java` | `app/base/mapper/ods_szdn_toll_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollMapper.xml` | `app/base/mapper/ods_szdn_toll_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsSzdnTollStationIpMapper.java` | `app/base/mapper/ods_szdn_toll_station_ip_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml` | `app/base/mapper/ods_szdn_toll_station_ip_mapper.py` |
| `com/ruoyi/base/mapper/OdsYhglVBaseOrgMapper.java` | `app/base/mapper/ods_yhgl_v_base_org_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/OdsYhglVBaseOrgMapper.xml` | `app/base/mapper/ods_yhgl_v_base_org_mapper.py` |
| `com/ruoyi/base/mapper/ZdataLocationDictMapper.java` | `app/base/mapper/zdata_location_dict_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/ZdataLocationDictMapper.xml` | `app/base/mapper/zdata_location_dict_mapper.py` |
| `com/ruoyi/base/mapper/ZdataTrailFittingMapper.java` | `app/base/mapper/zdata_trail_fitting_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/ZdataTrailFittingMapper.xml` | `app/base/mapper/zdata_trail_fitting_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/ZdataTrailTracksMapper.java` | `app/base/mapper/zdata_trail_tracks_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml` | `app/base/mapper/zdata_trail_tracks_mapper.py` |

### 3.4 service（65 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IBaseConfigServiceAreaService.java` | `app/base/service/base_config_service_area_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/BaseConfigServiceAreaServiceImpl.java` | `app/base/service/base_config_service_area_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/ICarWarningConfigService.java` | `app/base/service/car_warning_config_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/CarWarningConfigServiceImpl.java` | `app/base/service/car_warning_config_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcConfig.java` | `app/base/service/cdc/cdc_config.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcMessage.java` | `app/base/service/cdc/cdc_message.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/CdcSyncService.java` | `app/base/service/cdc/cdc_sync_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/cdc/DeadLetterQueueService.java` | `app/base/service/cdc/dead_letter_queue_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztFwqjcxxService.java` | `app/base/service/dwd_lczt_fwqjcxx_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztFwqjcxxServiceImpl.java` | `app/base/service/dwd_lczt_fwqjcxx_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztSfsjcxxService.java` | `app/base/service/dwd_lczt_sfsjcxx_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztSfsjcxxServiceImpl.java` | `app/base/service/dwd_lczt_sfsjcxx_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IDwdLcztSfzjcxxService.java` | `app/base/service/dwd_lczt_sfzjcxx_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/DwdLcztSfzjcxxServiceImpl.java` | `app/base/service/dwd_lczt_sfzjcxx_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/SnapshotFlowEnhancedService.java` | `app/base/service/enhanced/snapshot_flow_enhanced_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpBaseInfoApiService.java` | `app/base/service/forest/http_base_info_api_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeGantryFusion01Service.java` | `app/base/service/forest/http_ods_lwzxsfsj_fee_gantry_fusion01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeRecords01Service.java` | `app/base/service/forest/http_ods_lwzxsfsj_fee_records01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeStationExit01Service.java` | `app/base/service/forest/http_ods_lwzxsfsj_fee_station_exit01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsRtSzdnSnapshotFlowAddcodeService.java` | `app/base/service/forest/http_ods_rt_szdn_snapshot_flow_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpSysUtilApiService.java` | `app/base/service/forest/http_sys_util_api_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/RoadPathApi.java` | `app/base/service/forest/road_path_api.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IGeometryService.java` | `app/base/service/geometry_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/GeometryServiceImpl.java` | `app/base/service/geometry_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IHenDaService.java` | `app/base/service/hen_da_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/HenDaServiceImpl.java` | `app/base/service/hen_da_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/forest/IHenDaApi.java` | `app/base/service/hen_da_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsCxztFwqcllsService.java` | `app/base/service/ods_cxzt_fwqclls_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsCxztFwqcllsServiceImpl.java` | `app/base/service/ods_cxzt_fwqclls_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeGantryFusion01Service.java` | `app/base/service/ods_lwzxsfsj_fee_gantry_fusion01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeGantryFusion01ServiceImpl.java` | `app/base/service/ods_lwzxsfsj_fee_gantry_fusion01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeRecords01Service.java` | `app/base/service/ods_lwzxsfsj_fee_records01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeRecords01ServiceImpl.java` | `app/base/service/ods_lwzxsfsj_fee_records01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeStationEnter01Service.java` | `app/base/service/ods_lwzxsfsj_fee_station_enter01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeStationEnter01ServiceImpl.java` | `app/base/service/ods_lwzxsfsj_fee_station_enter01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsLwzxsfsjFeeStationExit01Service.java` | `app/base/service/ods_lwzxsfsj_fee_station_exit01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsLwzxsfsjFeeStationExit01ServiceImpl.java` | `app/base/service/ods_lwzxsfsj_fee_station_exit01_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowAddcodeService.java` | `app/base/service/ods_rt_szdn_snapshot_flow_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowAddcodeServiceImpl.java` | `app/base/service/ods_rt_szdn_snapshot_flow_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService.java` | `app/base/service/ods_rt_szdn_snapshot_flow_provcapture_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowProvcaptureAddcodeServiceImpl.java` | `app/base/service/ods_rt_szdn_snapshot_flow_provcapture_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsRtSzdnSnapshotFlowStationcaptureAddcodeService.java` | `app/base/service/ods_rt_szdn_snapshot_flow_stationcapture_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsRtSzdnSnapshotFlowStationcaptureAddcodeServiceImpl.java` | `app/base/service/ods_rt_szdn_snapshot_flow_stationcapture_addcode_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnGantryIpService.java` | `app/base/service/ods_szdn_gantry_ip_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnGantryIpServiceImpl.java` | `app/base/service/ods_szdn_gantry_ip_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnGantryService.java` | `app/base/service/ods_szdn_gantry_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnGantryServiceImpl.java` | `app/base/service/ods_szdn_gantry_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnProvinceBorderVehicleWeightNewstructureService.java` | `app/base/service/ods_szdn_province_border_vehicle_weight_newstructure_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnProvinceBorderVehicleWeightNewstructureServiceImpl.java` | `app/base/service/ods_szdn_province_border_vehicle_weight_newstructure_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnSectionService.java` | `app/base/service/ods_szdn_section_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnSectionServiceImpl.java` | `app/base/service/ods_szdn_section_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnTollService.java` | `app/base/service/ods_szdn_toll_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnTollServiceImpl.java` | `app/base/service/ods_szdn_toll_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsSzdnTollStationIpService.java` | `app/base/service/ods_szdn_toll_station_ip_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsSzdnTollStationIpServiceImpl.java` | `app/base/service/ods_szdn_toll_station_ip_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IOdsYhglVBaseOrgService.java` | `app/base/service/ods_yhgl_v_base_org_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/OdsYhglVBaseOrgServiceImpl.java` | `app/base/service/ods_yhgl_v_base_org_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IRoadPathService.java` | `app/base/service/road_path_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/RoadPathImpl.java` | `app/base/service/road_path_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataLocationDictService.java` | `app/base/service/zdata_location_dict_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataLocationDictServiceImpl.java` | `app/base/service/zdata_location_dict_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataTrailFittingService.java` | `app/base/service/zdata_trail_fitting_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailFittingServiceImpl.java` | `app/base/service/zdata_trail_fitting_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataTrailTracksService.java` | `app/base/service/zdata_trail_tracks_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailTracksServiceImpl.java` | `app/base/service/zdata_trail_tracks_service.py` |

### 3.5 util（3 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/base/util/EncryptUtils.java` | `app/base/util/encrypt_utils.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/util/GpsUtil.java` | `app/base/util/gps_util.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/util/LonLatPathsUtils.java` | `app/base/util/lon_lat_paths_utils.py` |

### 3.6 sharding（2 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingConfig.java` | `app/base/sharding/sharding_config.py` |
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java` | `app/base/sharding/sharding_table_util.py` |

## 4. 控制器端点（106 个）

### 4.1 `BaseConfigServiceAreaController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/configServiceArea/{fwqbms}` | `base:configServiceArea:remove` | 服务区 / DELETE |
| `export` | `export` | GET `/base/configServiceArea/export` | `base:configServiceArea:export` | 服务区 / EXPORT |
| `list` | `list_config_service_areas` | GET `/base/configServiceArea/list` | `base:configServiceArea:list` | — |
| `listQuery` | `list_query` | GET `/base/configServiceArea/listQuery` | `—` | — |
| `getInfo` | `get_info` | GET `/base/configServiceArea/{fwqbm}` | `—` | — |
| `add` | `add` | POST `/base/configServiceArea` | `base:configServiceArea:add` | 服务区 / INSERT |
| `edit` | `edit` | PUT `/base/configServiceArea` | `base:configServiceArea:edit` | 服务区 / UPDATE |

### 4.2 `CarWarningConfigController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/config/{ids}` | `base:config:remove` | 服务区判定规则 / DELETE |
| `export` | `export` | GET `/base/config/export` | `base:config:export` | 服务区判定规则 / EXPORT |
| `list` | `list_car_warning_configs` | GET `/base/config/list` | `base:config:list` | — |
| `getInfo` | `get_info` | GET `/base/config/{id}` | `—` | — |
| `add` | `add` | POST `/base/config` | `base:config:add` | 服务区判定规则 / INSERT |
| `edit` | `edit` | PUT `/base/config` | `base:config:edit` | 服务区判定规则 / UPDATE |

### 4.3 `CdcController`（8 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `clearDeadLetterQueue` | `clear_dead_letter_queue` | DELETE `/base/cdc/dead-letters/clear` | `—` | — |
| `deleteDeadLetterMessage` | `delete_dead_letter_message` | DELETE `/base/cdc/dead-letters/{messageId}` | `—` | — |
| `getConfig` | `get_config` | GET `/base/cdc/config` | `—` | — |
| `getDeadLetterMessages` | `get_dead_letter_messages` | GET `/base/cdc/dead-letters` | `—` | — |
| `getRetryMessages` | `get_retry_messages` | GET `/base/cdc/retry-messages` | `—` | — |
| `getQueueStatus` | `get_queue_status` | GET `/base/cdc/status` | `—` | — |
| `retryAllDeadMessages` | `retry_all_dead_messages` | POST `/base/cdc/retry-all` | `—` | — |
| `retryMessage` | `retry_message` | POST `/base/cdc/retry/{messageId}` | `—` | — |

### 4.4 `DwdLcztFwqjcxxController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/fwqjcxx/{agentPks}` | `base:fwqjcxx:remove` | 服务区基础信息 / DELETE |
| `export` | `export` | GET `/base/fwqjcxx/export` | `base:fwqjcxx:export` | 服务区基础信息 / EXPORT |
| `list` | `list_fwqjcxx` | GET `/base/fwqjcxx/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/fwqjcxx/{agentPk}` | `—` | — |
| `add` | `add` | POST `/base/fwqjcxx` | `base:fwqjcxx:add` | 服务区基础信息 / INSERT |
| `edit` | `edit` | PUT `/base/fwqjcxx` | `base:fwqjcxx:edit` | 服务区基础信息 / UPDATE |

### 4.5 `DwdLcztSfsjcxxController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/sfsjcxx/{agentPks}` | `base:sfsjcxx:remove` | 收费所基础信息 / DELETE |
| `export` | `export` | GET `/base/sfsjcxx/export` | `base:sfsjcxx:export` | 收费所基础信息 / EXPORT |
| `list` | `list_sfsjcxx` | GET `/base/sfsjcxx/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/sfsjcxx/{agentPk}` | `—` | — |
| `add` | `add` | POST `/base/sfsjcxx` | `base:sfsjcxx:add` | 收费所基础信息 / INSERT |
| `edit` | `edit` | PUT `/base/sfsjcxx` | `base:sfsjcxx:edit` | 收费所基础信息 / UPDATE |

### 4.6 `DwdLcztSfzjcxxController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/sfzjcxx/{agentPks}` | `base:sfzjcxx:remove` | 收费站基础信息 / DELETE |
| `export` | `export` | GET `/base/sfzjcxx/export` | `base:sfzjcxx:export` | 收费站基础信息 / EXPORT |
| `list` | `list_sfzjcxx` | GET `/base/sfzjcxx/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/sfzjcxx/{agentPk}` | `—` | — |
| `add` | `add` | POST `/base/sfzjcxx` | `base:sfzjcxx:add` | 收费站基础信息 / INSERT |
| `edit` | `edit` | PUT `/base/sfzjcxx` | `base:sfzjcxx:edit` | 收费站基础信息 / UPDATE |

### 4.7 `GeometryController`（9 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/geometry/{IDs}` | `base:geometry:remove` | 车辆信息 / DELETE |
| `export` | `export` | GET `/base/geometry/export` | `base:geometry:export` | 车辆信息 / EXPORT |
| `getHenDa` | `get_hen_da` | GET `/base/geometry/getHenDa` | `base:geometry:list` | — |
| `list` | `list_geometries` | GET `/base/geometry/list` | `base:geometry:list` | — |
| `syncAllGeometry` | `sync_all_geometry` | GET `/base/geometry/syncAllGeometry` | `—` | — |
| `syncAllGeometry1` | `sync_all_geometry_1` | GET `/base/geometry/syncAllGeometry1` | `—` | — |
| `getInfo` | `get_info` | GET `/base/geometry/{ID}` | `—` | — |
| `add` | `add` | POST `/base/geometry` | `base:geometry:add` | 车辆信息 / INSERT |
| `edit` | `edit` | PUT `/base/geometry` | `base:geometry:edit` | 车辆信息 / UPDATE |

### 4.8 `OdsCxztFwqcllsController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_fwqclls` | GET `/manager/fwqclls/list` | `manager:fwqclls:list` | — |
| `getInfo` | `get_info` | GET `/manager/fwqclls/{bigId}` | `—` | — |

### 4.9 `OdsLwzxsfsjFeeGantryFusion01Controller`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_fee_gantries` | GET `/base/feeGantry/list` | `base:feeGantry:list` | — |
| `getInfo` | `get_info` | GET `/base/feeGantry/{bigId}` | `—` | — |

### 4.10 `OdsLwzxsfsjFeeRecords01Controller`（3 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `export` | `export` | GET `/base/feerecords/export` | `base:feerecords:list` | — |
| `list` | `list_fee_records` | GET `/base/feerecords/list` | `base:feerecords:list` | — |
| `getInfo` | `get_info` | GET `/base/feerecords/{bigId}` | `—` | — |

### 4.11 `OdsLwzxsfsjFeeStationEnter01Controller`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_fee_station_enters` | GET `/base/feeStationEnter/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/feeStationEnter/{bigId}` | `—` | — |

### 4.12 `OdsLwzxsfsjFeeStationExit01Controller`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_fee_station_exits` | GET `/base/feestationexit/list` | `base:feestationexit:list` | — |
| `getInfo` | `get_info` | GET `/base/feestationexit/{bigId}` | `—` | — |

### 4.13 `OdsRtSzdnSnapshotFlowAddcodeController`（4 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `getEarliestSnapshottime` | `get_earliest_snapshottime` | GET `/base/snapshotflow/earliest-time` | `—` | — |
| `export` | `export` | GET `/base/snapshotflow/export` | `base:snapshotflow:list` | — |
| `list` | `list_snapshot_flows` | GET `/base/snapshotflow/list` | `base:snapshotflow:list` | — |
| `getInfo` | `get_info` | GET `/base/snapshotflow/{bigId}` | `—` | — |

### 4.14 `OdsRtSzdnSnapshotFlowProvcaptureAddcodeController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_prov_captures` | GET `/base/provcapture/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/provcapture/{bigId}` | `—` | — |

### 4.15 `OdsRtSzdnSnapshotFlowStationcaptureAddcodeController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_station_captures` | GET `/base/stationcapture/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/stationcapture/{bigId}` | `—` | — |

### 4.16 `OdsSzdnGantryController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/gantry/{ids}` | `base:gantry:remove` | 门架信息 / DELETE |
| `export` | `export` | GET `/base/gantry/export` | `base:gantry:export` | 门架信息 / EXPORT |
| `list` | `list_gantries` | GET `/base/gantry/list` | `—` | — |
| `listAll` | `list_all_gantries` | GET `/base/gantry/listAll` | `—` | — |
| `getInfo` | `get_info` | GET `/base/gantry/{id}` | `—` | — |
| `add` | `add` | POST `/base/gantry` | `base:gantry:add` | 门架信息 / INSERT |
| `edit` | `edit` | PUT `/base/gantry` | `base:gantry:edit` | 门架信息 / UPDATE |

### 4.17 `OdsSzdnGantryIpController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_gantry_ips` | GET `/base/gantryIp/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/gantryIp/{id}` | `—` | — |

### 4.18 `OdsSzdnProvinceBorderVehicleWeightNewstructureController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_vehicle_weights` | GET `/base/vehicleweight/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/vehicleweight/{dataSource}` | `—` | — |

### 4.19 `OdsSzdnSectionController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/section/{ids}` | `base:section:remove` | 路段信息 / DELETE |
| `export` | `export` | GET `/base/section/export` | `base:section:export` | 路段信息 / EXPORT |
| `list` | `list_sections` | GET `/base/section/list` | `—` | — |
| `listAll` | `list_all_sections` | GET `/base/section/listAll` | `—` | — |
| `getInfo` | `get_info` | GET `/base/section/{id}` | `—` | — |
| `add` | `add` | POST `/base/section` | `base:section:add` | 路段信息 / INSERT |
| `edit` | `edit` | PUT `/base/section` | `base:section:edit` | 路段信息 / UPDATE |

### 4.20 `OdsSzdnTollController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/toll/{ids}` | `base:toll:remove` | 收费站基础信息 / DELETE |
| `export` | `export` | GET `/base/toll/export` | `base:toll:export` | 收费站基础信息 / EXPORT |
| `list` | `list_tolls` | GET `/base/toll/list` | `—` | — |
| `listAll` | `list_all_tolls` | GET `/base/toll/listAll` | `—` | — |
| `getInfo` | `get_info` | GET `/base/toll/{id}` | `—` | — |
| `add` | `add` | POST `/base/toll` | `base:toll:add` | 收费站基础信息 / INSERT |
| `edit` | `edit` | PUT `/base/toll` | `base:toll:edit` | 收费站基础信息 / UPDATE |

### 4.21 `OdsSzdnTollStationIpController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_toll_station_ips` | GET `/base/tollStationIp/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/tollStationIp/{id}` | `—` | — |

### 4.22 `OdsYhglVBaseOrgController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/base/org/{bigIds}` | `base:org:remove` | 机构信息 / DELETE |
| `export` | `export` | GET `/base/org/export` | `base:org:export` | 机构信息 / EXPORT |
| `list` | `list_orgs` | GET `/base/org/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/org/{bigId}` | `—` | — |
| `add` | `add` | POST `/base/org` | `base:org:add` | 机构信息 / INSERT |
| `edit` | `edit` | PUT `/base/org` | `base:org:edit` | 机构信息 / UPDATE |

### 4.23 `ZdataLocationDictController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_locations` | GET `/base/location/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/location/{id}` | `—` | — |

### 4.24 `ZdataTrailFittingController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_trail_fittings` | GET `/base/fitting/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/fitting/{cid}` | `—` | — |

### 4.25 `ZdataTrailTracksController`（2 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list` | `list_trail_tracks` | GET `/base/trailtracks/list` | `—` | — |
| `getInfo` | `get_info` | GET `/base/trailtracks/{uuid}` | `—` | — |

## 5. 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_base_config_service_area_controller.py` | **19** | `/base/configServiceArea` 的 7 个端点：路由表、权限点、`@Log`、分页与导出 |
| Controller | `tests/test_base_ods_controllers.py` | **36** | 第二批 8 个 ODS 控制器：注解展开、权限点、导出走流 |
| Controller | `tests/test_base_ods_readonly.py` | **58** | 6 个只读 ODS 模块：`list` 的分页与 `getInfo` 的 404/空对象语义 |
| Controller | `tests/test_base_ip_tables.py` | **31** | `/base/gantryIp` 与 `/base/tollStationIp` 两套设备 IP 表 |
| Mapper | `tests/test_base_config_service_area_mapper.py` | **20** | `BaseConfigServiceAreaMapper` / Service：SQL 形状与批量删除语义 |
| 合计 | — | **164** | — |

用例数取自 `pytest --collect-only`（含参数化展开）。全量套件当前 **3646** 条（3563 单测 + 83 条真实 MySQL/Redis 联调），见 `MIGRATION_PROGRESS.md` §6.10。
