# 附录 C：数据层清单

> 数据库：MySQL 8.x（JDBC URL 指向 `carmonitdb`，`serverTimezone=GMT+8`）。
> 注意：仓库内**没有完整 DDL**；生产 schema 为既有库。Rust 侧 `migrations/` 仅作为**只读快照/校验**，默认不执行。

## 本地库快照（2026-10-31）

| 文件 | 内容 |
|---|---|
| [`schema.carmonitdb.local.sql`](schema.carmonitdb.local.sql) | 本地 `carmonitdb` **84 张表**的 `SHOW CREATE TABLE`（仅结构，含索引/字符集/默认值） |
| [`data.sys_job.local.sql`](data.sys_job.local.sql) | 本地 `sys_job` **19 条**任务数据 |

代码引用表集（78）与本地库（84）对账：

- 交集 **71** 张。
- 代码引用、本地缺失 **7** 张：`geometry_copy1`、`ods_rt_szdn_snapshot_flow_view`、`sys_upgrade_info`、`t_waybill`、`t_waybill_detail`、`t_waybill_item`、`t_waybill_status`（后 4 张为同一表名的解析变体，以 Mapper 原文为准）。
- 本地存在、代码未引用 **13** 张：11 张 `qrtz_*`（实际用 RAM JobStore，不持久化）、`ods_rt_szdn_snapshot_flow_202508`（按月分表产物）、`t_disaster_threshold`。

> 本地快照为开发/测试库，不保证等同生产；索引/外键/字符集与上述 7 张缺失表仍建议以生产 `SHOW CREATE TABLE` 为准。

## 统计

| 项 | 值 |
|---|---:|
| Mapper XML | 75 |
| SQL 语句（select/insert/update/delete） | 481 |
| 出现过的表名（XML 引用） | 76 |
| `@TableName` 声明的表 | 47 |

## 表清单

| 表 | 来源 |
|---|---|
| `base_config_service_area` | @TableName + Mapper XML |
| `buss_test` | @TableName + Mapper XML |
| `car_aduit_free` | @TableName + Mapper XML |
| `car_confim_free` | @TableName + Mapper XML |
| `car_except_record` | @TableName + Mapper XML |
| `car_fee_record` | @TableName + Mapper XML |
| `car_info` | @TableName + Mapper XML |
| `car_query_log` | @TableName + Mapper XML |
| `car_route_detail` | @TableName + Mapper XML |
| `car_route_info` | @TableName + Mapper XML |
| `car_split_record` | @TableName + Mapper XML |
| `car_suspicious` | @TableName + Mapper XML |
| `car_suspicious_back` | @TableName + Mapper XML |
| `car_suspicious_check` | @TableName + Mapper XML |
| `car_track_info` | @TableName + Mapper XML |
| `car_warning_config` | @TableName + Mapper XML |
| `car_warning_info` | @TableName + Mapper XML |
| `car_warning_rule` | @TableName + Mapper XML |
| `car_white_info` | @TableName + Mapper XML |
| `dwd_lczt_fwqjcxx` | @TableName + Mapper XML |
| `dwd_lczt_sfsjcxx` | @TableName + Mapper XML |
| `dwd_lczt_sfzjcxx` | @TableName + Mapper XML |
| `flow_apply_info` | Mapper XML |
| `flow_current_node` | Mapper XML |
| `flow_list` | Mapper XML |
| `flow_message_dispose` | Mapper XML |
| `flow_message_info` | Mapper XML |
| `flow_name` | Mapper XML |
| `flow_template` | Mapper XML |
| `gantry_car` | @TableName + Mapper XML |
| `gantry_trade_info` | @TableName + Mapper XML |
| `gen_table` | Mapper XML |
| `gen_table_column` | Mapper XML |
| `geometry` | @TableName + Mapper XML |
| `geometry_copy1` | Mapper XML |
| `id` | Mapper XML |
| `information_schema` | Mapper XML |
| `ods_cxzt_fwqclls` | @TableName + Mapper XML |
| `ods_lwzxsfsj_fee_gantry_fusion_01` | @TableName + Mapper XML |
| `ods_lwzxsfsj_fee_records_01` | @TableName + Mapper XML |
| `ods_lwzxsfsj_fee_station_enter_01` | @TableName + Mapper XML |
| `ods_lwzxsfsj_fee_station_exit_01` | @TableName + Mapper XML |
| `ods_rt_szdn_snapshot_flow_addcode` | @TableName + Mapper XML |
| `ods_rt_szdn_snapshot_flow_provcapture_addcode` | @TableName + Mapper XML |
| `ods_rt_szdn_snapshot_flow_stationcapture_addcode` | @TableName + Mapper XML |
| `ods_rt_szdn_snapshot_flow_view` | Mapper XML |
| `ods_szdn_gantry` | @TableName + Mapper XML |
| `ods_szdn_gantry_ip` | @TableName + Mapper XML |
| `ods_szdn_province_border_vehicle_weight_newstructure` | @TableName + Mapper XML |
| `ods_szdn_section` | @TableName + Mapper XML |
| `ods_szdn_toll` | @TableName + Mapper XML |
| `ods_szdn_toll_station_ip` | @TableName + Mapper XML |
| `ods_yhgl_v_base_org` | @TableName + Mapper XML |
| `sys_config` | Mapper XML |
| `sys_dept` | Mapper XML |
| `sys_dict_data` | Mapper XML |
| `sys_dict_type` | Mapper XML |
| `sys_file` | Mapper XML |
| `sys_index_menu` | Mapper XML |
| `sys_job` | Mapper XML |
| `sys_job_log` | Mapper XML |
| `sys_logininfor` | Mapper XML |
| `sys_menu` | Mapper XML |
| `sys_notice` | Mapper XML |
| `sys_oper_log` | Mapper XML |
| `sys_post` | Mapper XML |
| `sys_role` | Mapper XML |
| `sys_role_dept` | Mapper XML |
| `sys_role_menu` | Mapper XML |
| `sys_upgrade_info` | Mapper XML |
| `sys_user` | Mapper XML |
| `sys_user_post` | Mapper XML |
| `sys_user_role` | Mapper XML |
| `t_waybill` | @TableName |
| `t_waybill_address` | @TableName |
| `t_waybill_cargo` | @TableName |
| `t_waybill_route` | @TableName |
| `zdata_location_dict` | @TableName + Mapper XML |
| `zdata_trail_fitting` | @TableName + Mapper XML |
| `zdata_trail_tracks` | @TableName + Mapper XML |

## Mapper 语句明细

### `ruoyi-system/src/main/resources/mapper/base/BaseConfigServiceAreaMapper.xml`

- namespace：`com.ruoyi.base.mapper.BaseConfigServiceAreaMapper`
- 语句（4）：`select:selectBaseConfigServiceAreaList`, `select:selectBaseConfigServiceAreaById`, `update:deleteBaseConfigServiceAreaById`, `update:deleteBaseConfigServiceAreaByIds`
- 表：`base_config_service_area`, `id`
- 动态标签：if×9, foreach×1, where×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/CarWarningConfigMapper.xml`

- namespace：`com.ruoyi.base.mapper.CarWarningConfigMapper`
- 语句（4）：`select:selectCarWarningConfigList`, `select:selectCarWarningConfigById`, `update:deleteCarWarningConfigById`, `update:deleteCarWarningConfigByIds`
- 表：`base_config_service_area`, `car_warning_config`, `id`
- 动态标签：if×13, foreach×1, where×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/DwdLcztFwqjcxxMapper.xml`

- namespace：`com.ruoyi.base.mapper.DwdLcztFwqjcxxMapper`
- 语句（5）：`select:selectDwdLcztFwqjcxxList`, `select:selectDwdLcztFwqjcxxById`, `update:deleteDwdLcztFwqjcxxById`, `update:deleteDwdLcztFwqjcxxByIds`, `select:selectDwdLcztFwqjcxxListNew`
- 表：`base_config_service_area`, `dwd_lczt_fwqjcxx`, `id`
- 动态标签：if×68, foreach×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/DwdLcztSfsjcxxMapper.xml`

- namespace：`com.ruoyi.base.mapper.DwdLcztSfsjcxxMapper`
- 语句（4）：`select:selectDwdLcztSfsjcxxList`, `select:selectDwdLcztSfsjcxxById`, `update:deleteDwdLcztSfsjcxxById`, `update:deleteDwdLcztSfsjcxxByIds`
- 表：`dwd_lczt_sfsjcxx`, `id`
- 动态标签：if×17, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/DwdLcztSfzjcxxMapper.xml`

- namespace：`com.ruoyi.base.mapper.DwdLcztSfzjcxxMapper`
- 语句（4）：`select:selectDwdLcztSfzjcxxList`, `select:selectDwdLcztSfzjcxxById`, `update:deleteDwdLcztSfzjcxxById`, `update:deleteDwdLcztSfzjcxxByIds`
- 表：`dwd_lczt_sfzjcxx`, `id`
- 动态标签：if×17, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml`

- namespace：`com.ruoyi.base.mapper.GeometryMapper`
- 语句（5）：`select:selectGeometryList`, `select:syncAllGeometry`, `select:selectGeometryById`, `update:deleteGeometryById`, `update:deleteGeometryByIds`
- 表：`geometry`, `geometry_copy1`, `id`
- 动态标签：if×6, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsCxztFwqcllsMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsCxztFwqcllsMapper`
- 语句（2）：`select:selectOdsCxztFwqcllsList`, `select:selectOdsCxztFwqcllsById`
- 表：`ods_cxzt_fwqclls`
- 动态标签：if×18
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeGantryFusion01Mapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsLwzxsfsjFeeGantryFusion01Mapper`
- 语句（4）：`select:selectOdsLwzxsfsjFeeGantryFusion01List`, `select:selectOdsLwzxsfsjFeeGantryFusion01ById`, `update:deleteOdsLwzxsfsjFeeGantryFusion01ById`, `update:deleteOdsLwzxsfsjFeeGantryFusion01ByIds`
- 表：`id`, `ods_lwzxsfsj_fee_gantry_fusion_01`
- 动态标签：if×73, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeRecords01Mapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsLwzxsfsjFeeRecords01Mapper`
- 语句（4）：`select:selectOdsLwzxsfsjFeeRecords01List`, `select:selectOdsLwzxsfsjFeeRecords01ById`, `update:deleteOdsLwzxsfsjFeeRecords01ById`, `update:deleteOdsLwzxsfsjFeeRecords01ByIds`
- 表：`id`, `ods_lwzxsfsj_fee_records_01`
- 动态标签：if×132, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationEnter01Mapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsLwzxsfsjFeeStationEnter01Mapper`
- 语句（2）：`select:selectOdsLwzxsfsjFeeStationEnter01List`, `select:selectOdsLwzxsfsjFeeStationEnter01ById`
- 表：`ods_lwzxsfsj_fee_station_enter_01`
- 动态标签：if×33
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationExit01Mapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsLwzxsfsjFeeStationExit01Mapper`
- 语句（4）：`select:selectOdsLwzxsfsjFeeStationExit01List`, `select:selectOdsLwzxsfsjFeeStationExit01ById`, `update:deleteOdsLwzxsfsjFeeStationExit01ById`, `update:deleteOdsLwzxsfsjFeeStationExit01ByIds`
- 表：`id`, `ods_lwzxsfsj_fee_station_exit_01`
- 动态标签：if×65, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper`
- 语句（18）：`select:selectOdsRtSzdnSnapshotFlowAddcodeList`, `select:selectOdsRtSzdnSnapshotFlowAddcodeById`, `select:getTopTen`, `update:deleteOdsRtSzdnSnapshotFlowAddcodeById`, `update:deleteOdsRtSzdnSnapshotFlowAddcodeByIds`, `select:selectShardingList`, `select:selectShardingCount`, `select:checkTableExists`, `update:createShardingTable`, `select:getTableApproximateCount`, `select:selectFromTable`, `select:selectFromView`, `select:statisticsTable`, `select:listShardingTables`, `select:getMaxSnapshottime`, `insert:insertBatchToTable`, `insert:insertToTable`, `select:selectFromTableById`
- 表：`car_warning_info`, `id`, `information_schema`, `ods_rt_szdn_snapshot_flow_addcode`, `ods_rt_szdn_snapshot_flow_view`
- 动态标签：if×103, foreach×2
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper`
- 语句（2）：`select:selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeList`, `select:selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeById`
- 表：`ods_rt_szdn_snapshot_flow_provcapture_addcode`
- 动态标签：if×82
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper`
- 语句（2）：`select:selectOdsRtSzdnSnapshotFlowStationcaptureAddcodeList`, `select:selectOdsRtSzdnSnapshotFlowStationcaptureAddcodeById`
- 表：`ods_rt_szdn_snapshot_flow_stationcapture_addcode`
- 动态标签：if×34
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryIpMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsSzdnGantryIpMapper`
- 语句（2）：`select:selectOdsSzdnGantryIpList`, `select:selectOdsSzdnGantryIpById`
- 表：`ods_szdn_gantry_ip`
- 动态标签：if×7
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsSzdnGantryMapper`
- 语句（5）：`select:selectOdsSzdnGantryList`, `select:selectOdsSzdnGantryById`, `update:deleteOdsSzdnGantryById`, `update:deleteOdsSzdnGantryByIds`, `select:selectOdsSzdnGantryListNew`
- 表：`id`, `ods_szdn_gantry`, `ods_szdn_section`
- 动态标签：if×44, foreach×2
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsSzdnProvinceBorderVehicleWeightNewstructureMapper`
- 语句（2）：`select:selectOdsSzdnProvinceBorderVehicleWeightNewstructureList`, `select:selectOdsSzdnProvinceBorderVehicleWeightNewstructureById`
- 表：`ods_szdn_province_border_vehicle_weight_newstructure`
- 动态标签：if×32
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsSzdnSectionMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsSzdnSectionMapper`
- 语句（5）：`select:selectOdsSzdnSectionList`, `select:selectOdsSzdnSectionById`, `update:deleteOdsSzdnSectionById`, `update:deleteOdsSzdnSectionByIds`, `select:selectOdsSzdnSectionListNew`
- 表：`id`, `ods_szdn_section`
- 动态标签：if×26, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsSzdnTollMapper`
- 语句（5）：`select:selectOdsSzdnTollList`, `select:selectOdsSzdnTollById`, `update:deleteOdsSzdnTollById`, `update:deleteOdsSzdnTollByIds`, `select:selectOdsSzdnTollListNew`
- 表：`id`, `ods_szdn_section`, `ods_szdn_toll`
- 动态标签：if×50, foreach×2
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsSzdnTollStationIpMapper`
- 语句（2）：`select:selectOdsSzdnTollStationIpList`, `select:selectOdsSzdnTollStationIpById`
- 表：`ods_szdn_toll_station_ip`
- 动态标签：if×5
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/OdsYhglVBaseOrgMapper.xml`

- namespace：`com.ruoyi.base.mapper.OdsYhglVBaseOrgMapper`
- 语句（4）：`select:selectOdsYhglVBaseOrgList`, `select:selectOdsYhglVBaseOrgById`, `update:deleteOdsYhglVBaseOrgById`, `update:deleteOdsYhglVBaseOrgByIds`
- 表：`id`, `ods_yhgl_v_base_org`
- 动态标签：if×17, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/ShardingSnapshotFlowMapper.xml`

- namespace：`com.ruoyi.base.mapper.ShardingSnapshotFlowMapper`
- 语句（11）：`insert:insert`, `insert:batchInsert`, `select:selectById`, `select:selectByTimeRange`, `select:selectByTimeRangeWithPage`, `select:countByTimeRange`, `update:updateById`, `delete:deleteById`, `select:selectByCondition`, `select:selectByConditionWithPage`, `select:countByCondition`
- 表：`id`
- 动态标签：if×15, foreach×1
- resultMap：0；`<sql>` 片段：2

### `ruoyi-system/src/main/resources/mapper/base/SnapshotFlowMapper.xml`

- namespace：`com.ruoyi.base.mapper.SnapshotFlowMapper`
- 语句（9）：`select:selectByIdWithPartition`, `select:selectByIdWithTimeRange`, `select:selectById`, `select:queryByPartition`, `select:queryByPartitionWithOffset`, `select:countByPartition`, `select:selectByTimeRange`, `select:selectByTimeRangeWithPage`, `select:countByTimeRange`
- 表：`ods_rt_szdn_snapshot_flow_addcode`
- 动态标签：—
- resultMap：1；`<sql>` 片段：0

### `ruoyi-system/src/main/resources/mapper/base/ZdataLocationDictMapper.xml`

- namespace：`com.ruoyi.base.mapper.ZdataLocationDictMapper`
- 语句（4）：`select:selectZdataLocationDictList`, `select:selectZdataLocationDictById`, `update:deleteZdataLocationDictById`, `update:deleteZdataLocationDictByIds`
- 表：`id`, `zdata_location_dict`
- 动态标签：if×15, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/ZdataTrailFittingMapper.xml`

- namespace：`com.ruoyi.base.mapper.ZdataTrailFittingMapper`
- 语句（4）：`select:selectZdataTrailFittingList`, `select:selectZdataTrailFittingById`, `update:deleteZdataTrailFittingById`, `update:deleteZdataTrailFittingByIds`
- 表：`id`, `zdata_trail_fitting`
- 动态标签：if×19, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml`

- namespace：`com.ruoyi.base.mapper.ZdataTrailTracksMapper`
- 语句（5）：`select:selectZdataTrailTracksList`, `select:selectZdataTrailTracksById`, `select:getHistoryTrail`, `select:getCyly`, `delete:removeRealData`
- 表：`zdata_trail_tracks`
- 动态标签：if×20, foreach×2, where×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowApplyInfoMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowApplyInfoMapper`
- 语句（7）：`select:selectFlowApplyInfoList`, `select:selectFlowApplyInfoById`, `insert:insertFlowApplyInfo`, `update:updateFlowApplyInfo`, `update:deleteFlowApplyInfoById`, `update:deleteFlowApplyInfoByIds`, `select:selectByBillId`
- 表：`flow_apply_info`, `id`
- 动态标签：if×86, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowCurrentNodeMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowCurrentNodeMapper`
- 语句（11）：`select:selectFlowCurrentNodeList`, `select:selectFlowCurrentNodeById`, `insert:insertFlowCurrentNode`, `update:updateFlowCurrentNode`, `update:deleteFlowCurrentNodeById`, `update:deleteFlowCurrentNodeByIds`, `delete:deleteByBillId`, `select:selectEmpInfoList`, `update:updateFlowTable`, `select:selectUserListByRole`, `select:selectUserListByDept`
- 表：`flow_current_node`, `id`, `sys_dept`, `sys_user`, `sys_user_role`
- 动态标签：if×96, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowListMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowListMapper`
- 语句（7）：`select:selectFlowListList`, `select:selectFlowListListNew`, `select:selectFlowListById`, `insert:insertFlowList`, `update:updateFlowList`, `update:deleteFlowListById`, `update:deleteFlowListByIds`
- 表：`flow_list`, `id`
- 动态标签：if×91, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowMessageDisposeMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowMessageDisposeMapper`
- 语句（10）：`select:selectFlowMessageDisposeList`, `select:selectFlowMessageDisposeById`, `insert:insertFlowMessageDispose`, `update:updateFlowMessageDispose`, `update:deleteFlowMessageDisposeById`, `update:deleteFlowMessageDisposeByIds`, `delete:removeFlowMessage`, `update:saveSzzdFlowMessage`, `update:saveSzzdFlowMessageAll`, `update:updateBusinessByMessageId`
- 表：`flow_message_dispose`, `id`
- 动态标签：if×53, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowMessageInfoMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowMessageInfoMapper`
- 语句（6）：`select:selectFlowMessageInfoList`, `select:selectFlowMessageInfoById`, `insert:insertFlowMessageInfo`, `update:updateFlowMessageInfo`, `update:deleteFlowMessageInfoById`, `update:deleteFlowMessageInfoByIds`
- 表：`flow_apply_info`, `flow_message_dispose`, `flow_message_info`, `id`
- 动态标签：if×84, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowNameMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowNameMapper`
- 语句（7）：`select:selectFlowNameList`, `select:selectFlowNameById`, `insert:insertFlowName`, `update:updateFlowName`, `update:deleteFlowNameById`, `update:deleteFlowNameByIds`, `select:isExitsKey`
- 表：`flow_name`, `id`, `sys_dept`
- 动态标签：if×50, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/flow/FlowTemplateMapper.xml`

- namespace：`com.ruoyi.flow.mapper.FlowTemplateMapper`
- 语句（8）：`select:selectFlowTemplateList`, `select:selectFlowTemplateById`, `insert:insertFlowTemplate`, `update:updateFlowTemplate`, `update:deleteFlowTemplateById`, `update:deleteFlowTemplateByIds`, `select:isExitsKey`, `select:isExitsSort`
- 表：`flow_template`, `id`
- 动态标签：if×79, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/BussTestMapper.xml`

- namespace：`com.ruoyi.manager.mapper.BussTestMapper`
- 语句（4）：`select:selectBussTestList`, `select:selectBussTestById`, `update:deleteBussTestById`, `update:deleteBussTestByIds`
- 表：`buss_test`, `id`
- 动态标签：if×21, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarAduitFreeMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarAduitFreeMapper`
- 语句（10）：`select:selectCarAduitFreeList`, `select:selectCarAduitFreeById`, `select:getCarAudit`, `select:incomeStatistic`, `select:selectAuditCount`, `select:PCIncomeStatics`, `select:incomeDetailList`, `update:deleteCarAduitFreeById`, `update:deleteCarAduitFreeByIds`, `delete:deleteCarAduitFreeByConfirmId`
- 表：`car_aduit_free`, `car_confim_free`, `car_except_record`, `id`, `sys_dept`
- 动态标签：if×45, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarConfimFreeMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarConfimFreeMapper`
- 语句（11）：`select:selectCarConfimFreeList`, `select:selectCarConfimFreeById`, `select:getCarStatistics`, `select:getCarConfirm`, `select:selectCarConfimFreeByExceptIds`, `select:selectOrgId`, `select:getPCCarStatistics`, `select:selectConcernedList`, `update:deleteCarConfimFreeById`, `update:deleteCarConfimFreeByIds`, `select:listCount`
- 表：`car_confim_free`, `car_except_record`, `car_info`, `id`, `sys_dept`
- 动态标签：if×61, foreach×2
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarExceptRecordMapper`
- 语句（12）：`select:selectCarExceptRecordList`, `select:selectCarExceptRecordById`, `select:buildPCCarStatisticsVO`, `select:buildPCCarStatisticsVODetail`, `update:deleteCarExceptRecordById`, `update:deleteCarExceptRecordByIds`, `update:updateStatusByExceptId`, `delete:deleteCarExceptRecordByCarId`, `select:exceptRecordCount`, `select:isExitsTime`, `select:exceptRecordList`, `select:selectCarExceptRecordListNew`
- 表：`car_confim_free`, `car_except_record`, `car_info`, `id`, `sys_dept`, `sys_user`
- 动态标签：if×72, foreach×4
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarFeeRecordMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarFeeRecordMapper`
- 语句（4）：`select:selectCarFeeRecordList`, `select:selectCarFeeRecordById`, `update:deleteCarFeeRecordById`, `update:deleteCarFeeRecordByIds`
- 表：`car_fee_record`, `id`
- 动态标签：if×23, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarInfoMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarInfoMapper`
- 语句（7）：`select:selectCarInfoList`, `select:selectCarInfoById`, `select:getCarLocation`, `select:selectCarVoList`, `update:deleteCarInfoById`, `update:deleteCarInfoByIds`, `select:isExitsCar`
- 表：`car_except_record`, `car_info`, `id`, `sys_dept`, `sys_user`, `zdata_trail_tracks`
- 动态标签：if×70, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarQueryLogMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarQueryLogMapper`
- 语句（4）：`select:selectCarQueryLogList`, `select:selectCarQueryLogById`, `update:deleteCarQueryLogById`, `update:deleteCarQueryLogByIds`
- 表：`car_query_log`, `id`
- 动态标签：if×9, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarRouteDetailMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarRouteDetailMapper`
- 语句（4）：`select:selectCarRouteDetailList`, `select:selectCarRouteDetailById`, `update:deleteCarRouteDetailById`, `update:deleteCarRouteDetailByIds`
- 表：`car_route_detail`, `id`
- 动态标签：if×31, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarRouteInfoMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarRouteInfoMapper`
- 语句（4）：`select:selectCarRouteInfoList`, `select:selectCarRouteInfoById`, `update:deleteCarRouteInfoById`, `update:deleteCarRouteInfoByIds`
- 表：`car_route_info`, `id`
- 动态标签：if×22, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarSplitRecordMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarSplitRecordMapper`
- 语句（4）：`select:selectCarSplitRecordList`, `select:selectCarSplitRecordById`, `update:deleteCarSplitRecordById`, `update:deleteCarSplitRecordByIds`
- 表：`car_split_record`, `id`
- 动态标签：if×22, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousBackMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarSuspiciousBackMapper`
- 语句（4）：`select:selectCarSuspiciousBackList`, `select:selectCarSuspiciousBackById`, `update:deleteCarSuspiciousBackById`, `update:deleteCarSuspiciousBackByIds`
- 表：`car_suspicious_back`, `id`
- 动态标签：if×47, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousCheckMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarSuspiciousCheckMapper`
- 语句（5）：`select:selectCarSuspiciousCheckList`, `select:selectCarSuspiciousCheckById`, `update:deleteCarSuspiciousCheckById`, `update:deleteCarSuspiciousCheckByIds`, `delete:deleteCarSuspiciousCheckBySuspiciousId`
- 表：`car_suspicious_check`, `id`
- 动态标签：if×18, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarSuspiciousMapper`
- 语句（9）：`select:selectCarSuspiciousList`, `select:selectCarSuspiciousById`, `select:selectCarSuspiciousListLimit10`, `update:deleteCarSuspiciousById`, `update:deleteCarSuspiciousByIds`, `select:selectCarSuspiciousListHistroy`, `select:selectCarSuspiciousHistoryById`, `insert:changeCarSuspicious`, `delete:deleteChangeCarSuspicious`
- 表：`car_suspicious`, `car_suspicious_back`, `id`
- 动态标签：if×100, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarTrackInfoMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarTrackInfoMapper`
- 语句（4）：`select:selectCarTrackInfoList`, `select:selectCarTrackInfoById`, `update:deleteCarTrackInfoById`, `update:deleteCarTrackInfoByIds`
- 表：`car_track_info`, `id`
- 动态标签：if×22, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarWarningInfoMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarWarningInfoMapper`
- 语句（6）：`select:selectCarWarningInfoList`, `select:selectCarWarningInfoById`, `select:selectCarWarningInfoListLimit100`, `update:deleteCarWarningInfoById`, `update:deleteCarWarningInfoByIds`, `delete:deleteCarWarningInfoByUUid`
- 表：`car_info`, `car_warning_info`, `id`
- 动态标签：if×41, foreach×4
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarWarningRuleMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarWarningRuleMapper`
- 语句（4）：`select:selectCarWarningRuleList`, `select:selectCarWarningRuleById`, `update:deleteCarWarningRuleById`, `update:deleteCarWarningRuleByIds`
- 表：`car_warning_rule`, `id`
- 动态标签：if×19, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/CarWhiteInfoMapper.xml`

- namespace：`com.ruoyi.manager.mapper.CarWhiteInfoMapper`
- 语句（4）：`select:selectCarWhiteInfoList`, `select:selectCarWhiteInfoById`, `update:deleteCarWhiteInfoById`, `update:deleteCarWhiteInfoByIds`
- 表：`car_white_info`, `id`, `sys_dept`, `sys_user`
- 动态标签：if×15, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/GantryCarMapper.xml`

- namespace：`com.ruoyi.manager.mapper.GantryCarMapper`
- 语句（4）：`select:selectGantryCarList`, `select:selectGantryCarById`, `update:deleteGantryCarById`, `update:deleteGantryCarByIds`
- 表：`gantry_car`, `id`
- 动态标签：if×21, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/manager/GantryTradeInfoMapper.xml`

- namespace：`com.ruoyi.manager.mapper.GantryTradeInfoMapper`
- 语句（4）：`select:selectGantryTradeInfoList`, `select:selectGantryTradeInfoById`, `update:deleteGantryTradeInfoById`, `update:deleteGantryTradeInfoByIds`
- 表：`gantry_trade_info`, `id`
- 动态标签：if×22, foreach×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysConfigMapper`
- 语句（7）：`select:selectConfig`, `select:selectConfigList`, `select:checkConfigKeyUnique`, `insert:insertConfig`, `update:updateConfig`, `delete:deleteConfigById`, `delete:deleteConfigByIds`
- 表：`id`, `sys_config`
- 动态标签：if×25, foreach×1, where×2, set×1
- resultMap：1；`<sql>` 片段：2

### `ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysDeptMapper`
- 语句（16）：`select:selectDeptList`, `select:selectDeptListByRoleId`, `select:selectDeptById`, `select:checkDeptExistUser`, `select:hasChildByDeptId`, `select:selectChildrenDeptById`, `select:selectNormalChildrenDeptById`, `select:checkDeptNameUnique`, `insert:insertDept`, `update:updateDept`, `update:updateDeptChildren`, `update:updateDeptStatus`, `delete:deleteDeptById`, `select:selectTenantId`, `update:updateTenantId`, `delete:deleteDeptAll`
- 表：`id`, `sys_dept`, `sys_role_dept`, `sys_user`
- 动态标签：if×90, foreach×2, set×2
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysDictDataMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysDictDataMapper`
- 语句（11）：`select:selectDictDataList`, `select:selectDictDataByType`, `select:selectDictDataByTypeMore`, `select:selectDictLabel`, `select:selectDictDataById`, `select:countDictDataByType`, `delete:deleteDictDataById`, `delete:deleteDictDataByIds`, `update:updateDictData`, `update:updateDictDataType`, `insert:insertDictData`
- 表：`id`, `sys_dict_data`
- 动态标签：if×33, foreach×2, where×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysDictTypeMapper`
- 语句（9）：`select:selectDictTypeList`, `select:selectDictTypeAll`, `select:selectDictTypeById`, `select:selectDictTypeByType`, `select:checkDictTypeUnique`, `delete:deleteDictTypeById`, `delete:deleteDictTypeByIds`, `update:updateDictType`, `insert:insertDictType`
- 表：`id`, `sys_dict_type`
- 动态标签：if×20, foreach×1, where×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysFileMapper`
- 语句（9）：`select:selectSysFileList`, `select:selectSysFileById`, `select:selectSysFileByIds`, `insert:insertSysFile`, `update:updateSysFile`, `update:deleteSysFileById`, `update:deleteSysFileByIds`, `delete:deleteSysFileByIdNew`, `update:updateCAFile`
- 表：`id`, `sys_file`, `sys_user`
- 动态标签：if×52, foreach×2, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysIndexMenuMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysIndexMenuMapper`
- 语句（8）：`select:selectSysIndexMenuList`, `select:getList`, `select:selectSysIndexMenuById`, `insert:insertSysIndexMenu`, `update:updateSysIndexMenu`, `update:deleteSysIndexMenuById`, `update:deleteSysIndexMenuByIds`, `delete:deleteByMenuUserId`
- 表：`id`, `sys_index_menu`, `sys_menu`, `sys_role_menu`
- 动态标签：if×35, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysLogininforMapper`
- 语句（4）：`insert:insertLogininfor`, `select:selectLogininforList`, `delete:deleteLogininforByIds`, `update:cleanLogininfor`
- 表：`id`, `sys_logininfor`
- 动态标签：if×5, foreach×1, where×1
- resultMap：1；`<sql>` 片段：0

### `ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysMenuMapper`
- 语句（14）：`select:selectMenuList`, `select:selectMenuTreeAll`, `select:selectMenuListByUserId`, `select:selectMenuTreeByUserId`, `select:selectMenuListByRoleId`, `select:selectMenuPerms`, `select:selectMenuPermsByUserId`, `select:selectMenuPermsByRoleId`, `select:selectMenuById`, `select:hasChildByMenuId`, `select:checkMenuNameUnique`, `update:updateMenu`, `insert:insertMenu`, `delete:deleteMenuById`
- 表：`id`, `sys_menu`, `sys_role`, `sys_role_menu`, `sys_user`, `sys_user_role`
- 动态标签：if×51, where×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysNoticeMapper`
- 语句（6）：`select:selectNoticeById`, `select:selectNoticeList`, `insert:insertNotice`, `update:updateNotice`, `delete:deleteNoticeById`, `delete:deleteNoticeByIds`
- 表：`id`, `sys_notice`
- 动态标签：if×33, foreach×1, where×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysOperLogMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysOperLogMapper`
- 语句（5）：`insert:insertOperlog`, `select:selectOperLogList`, `delete:deleteOperLogByIds`, `select:selectOperLogById`, `update:cleanOperLog`
- 表：`id`, `sys_oper_log`
- 动态标签：if×7, foreach×2, where×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysPostMapper`
- 语句（11）：`select:selectPostList`, `select:selectPostAll`, `select:selectPostById`, `select:selectPostListByUserId`, `select:selectPostsByUserName`, `select:checkPostNameUnique`, `select:checkPostCodeUnique`, `update:updatePost`, `insert:insertPost`, `delete:deletePostById`, `delete:deletePostByIds`
- 表：`id`, `sys_post`, `sys_user`, `sys_user_post`
- 动态标签：if×23, foreach×1, where×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysRoleDeptMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysRoleDeptMapper`
- 语句（4）：`delete:deleteRoleDeptByRoleId`, `select:selectCountRoleDeptByDeptId`, `delete:deleteRoleDept`, `insert:batchRoleDept`
- 表：`sys_role_dept`
- 动态标签：foreach×2
- resultMap：1；`<sql>` 片段：0

### `ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysRoleMapper`
- 语句（12）：`select:selectRoleList`, `select:selectRolePermissionByUserId`, `select:selectRoleAll`, `select:selectRoleListByUserId`, `select:selectRoleById`, `select:selectRolesByUserName`, `select:checkRoleNameUnique`, `select:checkRoleKeyUnique`, `insert:insertRole`, `update:updateRole`, `delete:deleteRoleById`, `delete:deleteRoleByIds`
- 表：`id`, `sys_dept`, `sys_role`, `sys_user`, `sys_user_role`
- 动态标签：if×34, foreach×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysRoleMenuMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysRoleMenuMapper`
- 语句（4）：`select:checkMenuExistRole`, `delete:deleteRoleMenuByRoleId`, `delete:deleteRoleMenu`, `insert:batchRoleMenu`
- 表：`sys_role_menu`
- 动态标签：foreach×2
- resultMap：1；`<sql>` 片段：0

### `ruoyi-system/src/main/resources/mapper/system/SysUpgradeInfoMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysUpgradeInfoMapper`
- 语句（7）：`select:selectSysUpgradeInfoList`, `select:selectSysUpgradeInfoById`, `select:selectSysUpgradeInfoNewest`, `insert:insertSysUpgradeInfo`, `update:updateSysUpgradeInfo`, `update:deleteSysUpgradeInfoById`, `update:deleteSysUpgradeInfoByIds`
- 表：`id`, `sys_upgrade_info`
- 动态标签：if×39, foreach×1, trim×3
- resultMap：1；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysUserMapper`
- 语句（23）：`select:selectUserList`, `select:selectUserByUserName`, `select:selectUserByCertEntityID`, `select:selectUserById`, `select:checkUserNameUnique`, `select:checkPhoneUnique`, `select:checkEmailUnique`, `insert:insertUser`, `update:updateUser`, `update:updateUserInfoByBussId`, `update:updateUserStatus`, `update:updateUserPwd`, `update:updateUserAvatar`, `update:resetUserPwd`, `delete:deleteUserById`, `delete:deleteUserByIds`, `delete:deleteUserByBussId`, `delete:deleteUserByBussIds`, `select:existsByBussId`, `update:updateUserInfoByBussIdAndUserType`, `select:selectPwdJudge`, `select:getSendUserInfosByEpsId`, `select:selectByRoleKey`
- 表：`id`, `sys_dept`, `sys_role`, `sys_user`, `sys_user_role`
- 动态标签：if×147, foreach×2, trim×5
- resultMap：3；`<sql>` 片段：1

### `ruoyi-system/src/main/resources/mapper/system/SysUserPostMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysUserPostMapper`
- 语句（4）：`delete:deleteUserPostByUserId`, `select:countUserPostById`, `delete:deleteUserPost`, `insert:batchUserPost`
- 表：`sys_user_post`
- 动态标签：foreach×2
- resultMap：1；`<sql>` 片段：0

### `ruoyi-system/src/main/resources/mapper/system/SysUserRoleMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysUserRoleMapper`
- 语句（8）：`select:getUserRoleMap`, `delete:deleteUserRoleByUserId`, `select:countUserRoleByRoleId`, `select:countUserRoleByRoleIdUserId`, `delete:deleteUserRole`, `insert:batchUserRole`, `delete:deleteUserRoleInfo`, `delete:deleteUserRoleInfos`
- 表：`sys_user`, `sys_user_role`
- 动态标签：foreach×3
- resultMap：2；`<sql>` 片段：0

### `ruoyi-system/src/main/resources/mapper/system/SysUtilMapper.xml`

- namespace：`com.ruoyi.system.mapper.SysUtilMapper`
- 语句（1）：`select:getBussCode`
- 表：—
- 动态标签：—
- resultMap：1；`<sql>` 片段：0

### `ruoyi-quartz/src/main/resources/mapper/quartz/SysJobLogMapper.xml`

- namespace：`com.ruoyi.quartz.mapper.SysJobLogMapper`
- 语句（7）：`select:selectJobLogList`, `select:selectJobLogAll`, `select:selectJobLogById`, `delete:deleteJobLogById`, `delete:deleteJobLogByIds`, `update:cleanJobLog`, `insert:insertJobLog`
- 表：`id`, `sys_job_log`
- 动态标签：if×20, foreach×1, where×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-quartz/src/main/resources/mapper/quartz/SysJobMapper.xml`

- namespace：`com.ruoyi.quartz.mapper.SysJobMapper`
- 语句（7）：`select:selectJobList`, `select:selectJobAll`, `select:selectJobById`, `delete:deleteJobById`, `delete:deleteJobByIds`, `update:updateJob`, `insert:insertJob`
- 表：`id`, `sys_job`
- 动态标签：if×33, foreach×1, where×1, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-generator/src/main/resources/mapper/generator/GenTableColumnMapper.xml`

- namespace：`com.ruoyi.generator.mapper.GenTableColumnMapper`
- 语句（8）：`select:selectGenTableColumnListByTableId`, `select:selectDbTableColumnsByName`, `select:selectGenTableColumnListByTableColumnIds`, `select:selectGenTableColumnList`, `insert:insertGenTableColumn`, `update:updateGenTableColumn`, `delete:deleteGenTableColumnByIds`, `delete:deleteGenTableColumns`
- 表：`gen_table_column`, `id`, `information_schema`
- 动态标签：if×58, foreach×3, where×2, set×1
- resultMap：1；`<sql>` 片段：1

### `ruoyi-generator/src/main/resources/mapper/generator/GenTableMapper.xml`

- namespace：`com.ruoyi.generator.mapper.GenTableMapper`
- 语句（10）：`select:selectGenTableList`, `select:selectDbTableList`, `select:selectDbTableListByNames`, `select:selectTableByName`, `select:selectGenTableById`, `select:selectGenTableByName`, `select:selectGenTableAll`, `insert:insertGenTable`, `update:updateGenTable`, `delete:deleteGenTableByIds`
- 表：`gen_table`, `gen_table_column`, `id`, `information_schema`
- 动态标签：if×50, foreach×2, where×1, set×1
- resultMap：2；`<sql>` 片段：1
