# 附录 B：HTTP 接口清单（501 条）

> 由 `tools/gen_baseline.py` 复用 `car-monit-py/scripts/audit_endpoints.py` 的 Java 解析器生成。
> 与 Python 迁移的审计口径一致：类级前缀 + 方法级映射 + 权限点。
> `参数` 列只列非框架参数；`framework` 参数（HttpServletResponse 等）在说明中统一处理。
> 返回 `Rust handler` 为计划的 handler 函数名（snake_case），实际路由注册名以 `src/api/**` 为准。

## 切片统计

| 切片 | 控制器 | 端点 |
|---|---:|---:|
| base | 25 | 106 |
| common | 3 | 6 |
| flow | 7 | 55 |
| generator | 1 | 15 |
| manager | 20 | 160 |
| monitor | 5 | 12 |
| quartz | 2 | 13 |
| system | 15 | 129 |
| tool | 1 | 5 |
| **合计** | **79** | **501** |

## base

### BaseConfigServiceAreaController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/BaseConfigServiceAreaController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/configServiceArea/list` | list → `list` | `base:configServiceArea:list` | — | `baseConfigServiceArea:BaseConfigServiceArea (query)` | `TableDataInfo` |
| 2 | GET | `/base/configServiceArea/listQuery` | listQuery → `list_query` | — | — | `baseConfigServiceArea:BaseConfigServiceArea (query)` | `AjaxResult` |
| 3 | GET | `/base/configServiceArea/export` | export → `export` | `base:configServiceArea:export` | 服务区 / EXPORT | `baseConfigServiceArea:BaseConfigServiceArea (query)` | `AjaxResult` |
| 4 | GET | `/base/configServiceArea/{fwqbm}` | getInfo → `get_info` | — | — | `fwqbm:String (path)` | `AjaxResult` |
| 5 | POST | `/base/configServiceArea` | add → `add` | `base:configServiceArea:add` | 服务区 / INSERT | `baseConfigServiceArea:BaseConfigServiceArea (body)` | `AjaxResult` |
| 6 | PUT | `/base/configServiceArea` | edit → `edit` | `base:configServiceArea:edit` | 服务区 / UPDATE | `baseConfigServiceArea:BaseConfigServiceArea (body)` | `AjaxResult` |
| 7 | DELETE | `/base/configServiceArea/{fwqbms}` | remove → `remove` | `base:configServiceArea:remove` | 服务区 / DELETE | `fwqbms:String[] (path)` | `AjaxResult` |

### CarWarningConfigController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CarWarningConfigController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/config/list` | list → `list` | `base:config:list` | — | `carWarningConfig:CarWarningConfig (query)` | `TableDataInfo` |
| 2 | GET | `/base/config/export` | export → `export` | `base:config:export` | 服务区判定规则 / EXPORT | `carWarningConfig:CarWarningConfig (query)` | `AjaxResult` |
| 3 | GET | `/base/config/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/base/config` | add → `add` | `base:config:add` | 服务区判定规则 / INSERT | `carWarningConfig:CarWarningConfig (body)` | `AjaxResult` |
| 5 | PUT | `/base/config` | edit → `edit` | `base:config:edit` | 服务区判定规则 / UPDATE | `carWarningConfig:CarWarningConfig (body)` | `AjaxResult` |
| 6 | DELETE | `/base/config/{ids}` | remove → `remove` | `base:config:remove` | 服务区判定规则 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CdcController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/CdcController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/cdc/status` | getQueueStatus → `get_queue_status` | — | — | — | `AjaxResult` |
| 2 | GET | `/base/cdc/dead-letters` | getDeadLetterMessages → `get_dead_letter_messages` | — | — | — | `AjaxResult` |
| 3 | GET | `/base/cdc/retry-messages` | getRetryMessages → `get_retry_messages` | — | — | — | `AjaxResult` |
| 4 | POST | `/base/cdc/retry/{messageId}` | retryMessage → `retry_message` | — | — | `messageId:String (path)` | `AjaxResult` |
| 5 | POST | `/base/cdc/retry-all` | retryAllDeadMessages → `retry_all_dead_messages` | — | — | — | `AjaxResult` |
| 6 | DELETE | `/base/cdc/dead-letters/{messageId}` | deleteDeadLetterMessage → `delete_dead_letter_message` | — | — | `messageId:String (path)` | `AjaxResult` |
| 7 | DELETE | `/base/cdc/dead-letters/clear` | clearDeadLetterQueue → `clear_dead_letter_queue` | — | — | — | `AjaxResult` |
| 8 | GET | `/base/cdc/config` | getConfig → `get_config` | — | — | — | `AjaxResult` |

### DwdLcztFwqjcxxController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztFwqjcxxController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/fwqjcxx/list` | list → `list` | — | — | `dwdLcztFwqjcxx:DwdLcztFwqjcxx (query)` | `TableDataInfo` |
| 2 | GET | `/base/fwqjcxx/export` | export → `export` | `base:fwqjcxx:export` | 服务区基础信息 / EXPORT | `dwdLcztFwqjcxx:DwdLcztFwqjcxx (query)` | `AjaxResult` |
| 3 | GET | `/base/fwqjcxx/{agentPk}` | getInfo → `get_info` | — | — | `agentPk:String (path)` | `AjaxResult` |
| 4 | POST | `/base/fwqjcxx` | add → `add` | `base:fwqjcxx:add` | 服务区基础信息 / INSERT | `dwdLcztFwqjcxx:DwdLcztFwqjcxx (body)` | `AjaxResult` |
| 5 | PUT | `/base/fwqjcxx` | edit → `edit` | `base:fwqjcxx:edit` | 服务区基础信息 / UPDATE | `dwdLcztFwqjcxx:DwdLcztFwqjcxx (body)` | `AjaxResult` |
| 6 | DELETE | `/base/fwqjcxx/{agentPks}` | remove → `remove` | `base:fwqjcxx:remove` | 服务区基础信息 / DELETE | `agentPks:String[] (path)` | `AjaxResult` |

### DwdLcztSfsjcxxController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfsjcxxController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/sfsjcxx/list` | list → `list` | — | — | `dwdLcztSfsjcxx:DwdLcztSfsjcxx (query)` | `TableDataInfo` |
| 2 | GET | `/base/sfsjcxx/export` | export → `export` | `base:sfsjcxx:export` | 收费所基础信息 / EXPORT | `dwdLcztSfsjcxx:DwdLcztSfsjcxx (query)` | `AjaxResult` |
| 3 | GET | `/base/sfsjcxx/{agentPk}` | getInfo → `get_info` | — | — | `agentPk:String (path)` | `AjaxResult` |
| 4 | POST | `/base/sfsjcxx` | add → `add` | `base:sfsjcxx:add` | 收费所基础信息 / INSERT | `dwdLcztSfsjcxx:DwdLcztSfsjcxx (body)` | `AjaxResult` |
| 5 | PUT | `/base/sfsjcxx` | edit → `edit` | `base:sfsjcxx:edit` | 收费所基础信息 / UPDATE | `dwdLcztSfsjcxx:DwdLcztSfsjcxx (body)` | `AjaxResult` |
| 6 | DELETE | `/base/sfsjcxx/{agentPks}` | remove → `remove` | `base:sfsjcxx:remove` | 收费所基础信息 / DELETE | `agentPks:String[] (path)` | `AjaxResult` |

### DwdLcztSfzjcxxController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/DwdLcztSfzjcxxController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/sfzjcxx/list` | list → `list` | — | — | `dwdLcztSfzjcxx:DwdLcztSfzjcxx (query)` | `TableDataInfo` |
| 2 | GET | `/base/sfzjcxx/export` | export → `export` | `base:sfzjcxx:export` | 收费站基础信息 / EXPORT | `dwdLcztSfzjcxx:DwdLcztSfzjcxx (query)` | `AjaxResult` |
| 3 | GET | `/base/sfzjcxx/{agentPk}` | getInfo → `get_info` | — | — | `agentPk:String (path)` | `AjaxResult` |
| 4 | POST | `/base/sfzjcxx` | add → `add` | `base:sfzjcxx:add` | 收费站基础信息 / INSERT | `dwdLcztSfzjcxx:DwdLcztSfzjcxx (body)` | `AjaxResult` |
| 5 | PUT | `/base/sfzjcxx` | edit → `edit` | `base:sfzjcxx:edit` | 收费站基础信息 / UPDATE | `dwdLcztSfzjcxx:DwdLcztSfzjcxx (body)` | `AjaxResult` |
| 6 | DELETE | `/base/sfzjcxx/{agentPks}` | remove → `remove` | `base:sfzjcxx:remove` | 收费站基础信息 / DELETE | `agentPks:String[] (path)` | `AjaxResult` |

### GeometryController（9）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/GeometryController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/geometry/getHenDa` | getHenDa → `get_hen_da` | `base:geometry:list` | — | `geometry:Geometry (query)` | `AjaxResult` |
| 2 | GET | `/base/geometry/syncAllGeometry` | syncAllGeometry → `sync_all_geometry` | — | — | — | `AjaxResult` |
| 3 | GET | `/base/geometry/syncAllGeometry1` | syncAllGeometry1 → `sync_all_geometry1` | — | — | `geometry:Geometry (query)` | `AjaxResult` |
| 4 | GET | `/base/geometry/list` | list → `list` | `base:geometry:list` | — | `geometry:Geometry (query)` | `TableDataInfo` |
| 5 | GET | `/base/geometry/export` | export → `export` | `base:geometry:export` | 车辆信息 / EXPORT | `geometry:Geometry (query)` | `AjaxResult` |
| 6 | GET | `/base/geometry/{ID}` | getInfo → `get_info` | — | — | `ID:Integer (path)` | `AjaxResult` |
| 7 | POST | `/base/geometry` | add → `add` | `base:geometry:add` | 车辆信息 / INSERT | `geometry:Geometry (body)` | `AjaxResult` |
| 8 | PUT | `/base/geometry` | edit → `edit` | `base:geometry:edit` | 车辆信息 / UPDATE | `geometry:Geometry (body)` | `AjaxResult` |
| 9 | DELETE | `/base/geometry/{IDs}` | remove → `remove` | `base:geometry:remove` | 车辆信息 / DELETE | `IDs:Integer[] (path)` | `AjaxResult` |

### OdsCxztFwqcllsController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsCxztFwqcllsController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/fwqclls/list` | list → `list` | `manager:fwqclls:list` | — | `odsCxztFwqclls:OdsCxztFwqclls (query)` | `TableDataInfo` |
| 2 | GET | `/manager/fwqclls/{bigId}` | getInfo → `get_info` | — | — | `bigId:Long (path)` | `AjaxResult` |

### OdsLwzxsfsjFeeGantryFusion01Controller（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/feeGantry/list` | list → `list` | `base:feeGantry:list` | — | `odsLwzxsfsjFeeGantryFusion01:OdsLwzxsfsjFeeGantryFusion01 (query)` | `TableDataInfo` |
| 2 | GET | `/base/feeGantry/{bigId}` | getInfo → `get_info` | — | — | `bigId:String (path)` | `AjaxResult` |

### OdsLwzxsfsjFeeRecords01Controller（3）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/feerecords/list` | list → `list` | `base:feerecords:list` | — | `odsLwzxsfsjFeeRecords01:OdsLwzxsfsjFeeRecords01 (query)` | `TableDataInfo` |
| 2 | GET | `/base/feerecords/export` | export → `export` | `base:feerecords:list` | — | `odsLwzxsfsjFeeRecords01:OdsLwzxsfsjFeeRecords01 (query)` | `AjaxResult` |
| 3 | GET | `/base/feerecords/{bigId}` | getInfo → `get_info` | — | — | `bigId:String (path)` | `AjaxResult` |

### OdsLwzxsfsjFeeStationEnter01Controller（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationEnter01Controller.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/feeStationEnter/list` | list → `list` | — | — | `odsLwzxsfsjFeeStationEnter01:OdsLwzxsfsjFeeStationEnter01 (query)` | `TableDataInfo` |
| 2 | GET | `/base/feeStationEnter/{bigId}` | getInfo → `get_info` | — | — | `bigId:Long (path)` | `AjaxResult` |

### OdsLwzxsfsjFeeStationExit01Controller（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/feestationexit/list` | list → `list` | `base:feestationexit:list` | — | `odsLwzxsfsjFeeStationExit01:OdsLwzxsfsjFeeStationExit01 (query)` | `TableDataInfo` |
| 2 | GET | `/base/feestationexit/{bigId}` | getInfo → `get_info` | — | — | `bigId:String (path)` | `AjaxResult` |

### OdsRtSzdnSnapshotFlowAddcodeController（4）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/snapshotflow/list` | list → `list` | `base:snapshotflow:list` | — | `odsRtSzdnSnapshotFlowAddcode:OdsRtSzdnSnapshotFlowAddcode (query)` | `TableDataInfo` |
| 2 | GET | `/base/snapshotflow/export` | export → `export` | `base:snapshotflow:list` | — | `odsRtSzdnSnapshotFlowAddcode:OdsRtSzdnSnapshotFlowAddcode (query)` | `AjaxResult` |
| 3 | GET | `/base/snapshotflow/{bigId}` | getInfo → `get_info` | — | — | `bigId:String (path)` | `AjaxResult` |
| 4 | GET | `/base/snapshotflow/earliest-time` | getEarliestSnapshottime → `get_earliest_snapshottime` | — | — | — | `AjaxResult` |

### OdsRtSzdnSnapshotFlowProvcaptureAddcodeController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/provcapture/list` | list → `list` | — | — | `odsRtSzdnSnapshotFlowProvcaptureAddcode:OdsRtSzdnSnapshotFlowProvcaptureAddcode (query)` | `TableDataInfo` |
| 2 | GET | `/base/provcapture/{bigId}` | getInfo → `get_info` | — | — | `bigId:Long (path)` | `AjaxResult` |

### OdsRtSzdnSnapshotFlowStationcaptureAddcodeController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/stationcapture/list` | list → `list` | — | — | `odsRtSzdnSnapshotFlowStationcaptureAddcode:OdsRtSzdnSnapshotFlowStationcaptureAddcode (query)` | `TableDataInfo` |
| 2 | GET | `/base/stationcapture/{bigId}` | getInfo → `get_info` | — | — | `bigId:Long (path)` | `AjaxResult` |

### OdsSzdnGantryController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/gantry/list` | list → `list` | — | — | `odsSzdnGantry:OdsSzdnGantry (query)` | `TableDataInfo` |
| 2 | GET | `/base/gantry/listAll` | listAll → `list_all` | — | — | `odsSzdnGantry:OdsSzdnGantry (query)` | `TableDataInfo` |
| 3 | GET | `/base/gantry/export` | export → `export` | `base:gantry:export` | 门架信息 / EXPORT | `odsSzdnGantry:OdsSzdnGantry (query)` | `AjaxResult` |
| 4 | GET | `/base/gantry/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/base/gantry` | add → `add` | `base:gantry:add` | 门架信息 / INSERT | `odsSzdnGantry:OdsSzdnGantry (body)` | `AjaxResult` |
| 6 | PUT | `/base/gantry` | edit → `edit` | `base:gantry:edit` | 门架信息 / UPDATE | `odsSzdnGantry:OdsSzdnGantry (body)` | `AjaxResult` |
| 7 | DELETE | `/base/gantry/{ids}` | remove → `remove` | `base:gantry:remove` | 门架信息 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### OdsSzdnGantryIpController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnGantryIpController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/gantryIp/list` | list → `list` | — | — | `odsSzdnGantryIp:OdsSzdnGantryIp (query)` | `TableDataInfo` |
| 2 | GET | `/base/gantryIp/{id}` | getInfo → `get_info` | — | — | `id:Long (path)` | `AjaxResult` |

### OdsSzdnProvinceBorderVehicleWeightNewstructureController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnProvinceBorderVehicleWeightNewstructureController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/vehicleweight/list` | list → `list` | — | — | `odsSzdnProvinceBorderVehicleWeightNewstructure:OdsSzdnProvinceBorderVehicleWeightNewstructure (query)` | `TableDataInfo` |
| 2 | GET | `/base/vehicleweight/{dataSource}` | getInfo → `get_info` | — | — | `dataSource:String (path)` | `AjaxResult` |

### OdsSzdnSectionController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnSectionController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/section/list` | list → `list` | — | — | `odsSzdnSection:OdsSzdnSection (query)` | `TableDataInfo` |
| 2 | GET | `/base/section/listAll` | listAll → `list_all` | — | — | `odsSzdnSection:OdsSzdnSection (query)` | `TableDataInfo` |
| 3 | GET | `/base/section/export` | export → `export` | `base:section:export` | 路段信息 / EXPORT | `odsSzdnSection:OdsSzdnSection (query)` | `AjaxResult` |
| 4 | GET | `/base/section/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/base/section` | add → `add` | `base:section:add` | 路段信息 / INSERT | `odsSzdnSection:OdsSzdnSection (body)` | `AjaxResult` |
| 6 | PUT | `/base/section` | edit → `edit` | `base:section:edit` | 路段信息 / UPDATE | `odsSzdnSection:OdsSzdnSection (body)` | `AjaxResult` |
| 7 | DELETE | `/base/section/{ids}` | remove → `remove` | `base:section:remove` | 路段信息 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### OdsSzdnTollController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/toll/list` | list → `list` | — | — | `odsSzdnToll:OdsSzdnToll (query)` | `TableDataInfo` |
| 2 | GET | `/base/toll/listAll` | listAll → `list_all` | — | — | `odsSzdnToll:OdsSzdnToll (query)` | `TableDataInfo` |
| 3 | GET | `/base/toll/export` | export → `export` | `base:toll:export` | 收费站基础信息 / EXPORT | `odsSzdnToll:OdsSzdnToll (query)` | `AjaxResult` |
| 4 | GET | `/base/toll/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/base/toll` | add → `add` | `base:toll:add` | 收费站基础信息 / INSERT | `odsSzdnToll:OdsSzdnToll (body)` | `AjaxResult` |
| 6 | PUT | `/base/toll` | edit → `edit` | `base:toll:edit` | 收费站基础信息 / UPDATE | `odsSzdnToll:OdsSzdnToll (body)` | `AjaxResult` |
| 7 | DELETE | `/base/toll/{ids}` | remove → `remove` | `base:toll:remove` | 收费站基础信息 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### OdsSzdnTollStationIpController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsSzdnTollStationIpController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/tollStationIp/list` | list → `list` | — | — | `odsSzdnTollStationIp:OdsSzdnTollStationIp (query)` | `TableDataInfo` |
| 2 | GET | `/base/tollStationIp/{id}` | getInfo → `get_info` | — | — | `id:Long (path)` | `AjaxResult` |

### OdsYhglVBaseOrgController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsYhglVBaseOrgController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/org/list` | list → `list` | — | — | `odsYhglVBaseOrg:OdsYhglVBaseOrg (query)` | `TableDataInfo` |
| 2 | GET | `/base/org/export` | export → `export` | `base:org:export` | 机构信息 / EXPORT | `odsYhglVBaseOrg:OdsYhglVBaseOrg (query)` | `AjaxResult` |
| 3 | GET | `/base/org/{bigId}` | getInfo → `get_info` | — | — | `bigId:String (path)` | `AjaxResult` |
| 4 | POST | `/base/org` | add → `add` | `base:org:add` | 机构信息 / INSERT | `odsYhglVBaseOrg:OdsYhglVBaseOrg (body)` | `AjaxResult` |
| 5 | PUT | `/base/org` | edit → `edit` | `base:org:edit` | 机构信息 / UPDATE | `odsYhglVBaseOrg:OdsYhglVBaseOrg (body)` | `AjaxResult` |
| 6 | DELETE | `/base/org/{bigIds}` | remove → `remove` | `base:org:remove` | 机构信息 / DELETE | `bigIds:String[] (path)` | `AjaxResult` |

### ZdataLocationDictController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataLocationDictController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/location/list` | list → `list` | — | — | `zdataLocationDict:ZdataLocationDict (query)` | `TableDataInfo` |
| 2 | GET | `/base/location/{id}` | getInfo → `get_info` | — | — | `id:Long (path)` | `AjaxResult` |

### ZdataTrailFittingController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailFittingController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/fitting/list` | list → `list` | — | — | `zdataTrailFitting:ZdataTrailFitting (query)` | `TableDataInfo` |
| 2 | GET | `/base/fitting/{cid}` | getInfo → `get_info` | — | — | `cid:String (path)` | `AjaxResult` |

### ZdataTrailTracksController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/ZdataTrailTracksController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/base/trailtracks/list` | list → `list` | — | — | `zdataTrailTracks:ZdataTrailTracks (query)` | `TableDataInfo` |
| 2 | GET | `/base/trailtracks/{uuid}` | getInfo → `get_info` | — | — | `uuid:String (path)` | `AjaxResult` |

## common

### CaptchaController（1）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CaptchaController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/captchaImage` | getCode → `get_code` | — | — | — | `AjaxResult` |

### CommonController（4）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CommonController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/common/download` | fileDownload → `file_download` | — | — | `fileName:String (query)`; `delete:Boolean (query)` | `void` |
| 2 | POST | `/common/upload` | uploadFile → `upload_file` | — | — | `file:MultipartFile (file)` | `AjaxResult` |
| 3 | POST | `/common/uploads` | uploadFiles → `upload_files` | — | — | `files:List<MultipartFile> (query)` | `AjaxResult` |
| 4 | GET | `/common/download/resource` | resourceDownload → `resource_download` | — | — | `resource:String (query)` | `void` |

### DownTemplateController（1）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/DownTemplateController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/downTemplate/{type}` | downExcel → `down_excel` | — | — | `type:String (path)` | `AjaxResult` |

## flow

### FlowApplyInfoController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowApplyInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/applyinfo/list` | list → `list` | — | — | `flowApplyInfo:FlowApplyInfo (query)` | `TableDataInfo` |
| 2 | GET | `/flow/applyinfo/listAll` | listAll → `list_all` | `flow:applyinfo:list` | — | `flowApplyInfo:FlowApplyInfo (query)` | `TableDataInfo` |
| 3 | GET | `/flow/applyinfo/export` | export → `export` | — | 我的申请 / EXPORT | `flowApplyInfo:FlowApplyInfo (query)` | `AjaxResult` |
| 4 | GET | `/flow/applyinfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/flow/applyinfo` | add → `add` | — | 我的申请 / INSERT | `flowApplyInfo:FlowApplyInfo (body)` | `AjaxResult` |
| 6 | PUT | `/flow/applyinfo` | edit → `edit` | — | 我的申请 / UPDATE | `flowApplyInfo:FlowApplyInfo (body)` | `AjaxResult` |
| 7 | DELETE | `/flow/applyinfo/{ids}` | remove → `remove` | — | 我的申请 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### FlowCurrentNodeController（10）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowCurrentNodeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/currentnode/list` | list → `list` | — | — | `flowCurrentNode:FlowCurrentNode (query)` | `TableDataInfo` |
| 2 | GET | `/flow/currentnode/export` | export → `export` | — | 流程_当前节点 / EXPORT | `flowCurrentNode:FlowCurrentNode (query)` | `AjaxResult` |
| 3 | GET | `/flow/currentnode/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | GET | `/flow/currentnode/getInfoByBillId/{billOid}` | getInfoByBillId → `get_info_by_bill_id` | — | — | `billOid:String (path)` | `AjaxResult` |
| 5 | POST | `/flow/currentnode` | add → `add` | — | 流程_当前节点 / INSERT | `flowCurrentNode:FlowCurrentNode (body)` | `AjaxResult` |
| 6 | PUT | `/flow/currentnode` | edit → `edit` | — | 流程_当前节点 / UPDATE | `flowCurrentNode:FlowCurrentNode (body)` | `AjaxResult` |
| 7 | DELETE | `/flow/currentnode/{ids}` | remove → `remove` | — | 流程_当前节点 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 8 | PUT | `/flow/currentnode/saveFlowAuit` | saveFlowAuit → `save_flow_auit` | — | — | `flowCurrentNode:FlowCurrentNode (body)` | `AjaxResult` |
| 9 | POST | `/flow/currentnode/submitReturn` | submitReturn → `submit_return` | — | — | `flowCurrentNode:FlowCurrentNode (body)` | `AjaxResult` |
| 10 | POST | `/flow/currentnode/submitEntrustFlow` | submitEntrustFlow → `submit_entrust_flow` | — | — | `flowCurrentNode:FlowCurrentNode (body)` | `AjaxResult` |

### FlowListController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowListController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/flowlist/list` | list → `list` | — | — | `flowList:FlowList (query)` | `TableDataInfo` |
| 2 | GET | `/flow/flowlist/listnew` | listnew → `listnew` | — | — | `flowList:FlowList (query)` | `AjaxResult` |
| 3 | GET | `/flow/flowlist/export` | export → `export` | — | 审核历史记录 / EXPORT | `flowList:FlowList (query)` | `AjaxResult` |
| 4 | GET | `/flow/flowlist/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/flow/flowlist` | add → `add` | — | 审核历史记录 / INSERT | `flowList:FlowList (body)` | `AjaxResult` |
| 6 | PUT | `/flow/flowlist` | edit → `edit` | — | 审核历史记录 / UPDATE | `flowList:FlowList (body)` | `AjaxResult` |
| 7 | DELETE | `/flow/flowlist/{ids}` | remove → `remove` | — | 审核历史记录 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### FlowMessageDisposeController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageDisposeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/messagedispose/list` | list → `list` | — | — | `flowMessageDispose:FlowMessageDispose (query)` | `TableDataInfo` |
| 2 | GET | `/flow/messagedispose/export` | export → `export` | — | 系统消息处理人 / EXPORT | `flowMessageDispose:FlowMessageDispose (query)` | `AjaxResult` |
| 3 | GET | `/flow/messagedispose/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/flow/messagedispose` | add → `add` | — | 系统消息处理人 / INSERT | `flowMessageDispose:FlowMessageDispose (body)` | `AjaxResult` |
| 5 | PUT | `/flow/messagedispose` | edit → `edit` | — | 系统消息处理人 / UPDATE | `flowMessageDispose:FlowMessageDispose (body)` | `AjaxResult` |
| 6 | DELETE | `/flow/messagedispose/{ids}` | remove → `remove` | — | 系统消息处理人 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 7 | DELETE | `/flow/messagedispose/delmes/{mid}` | removeFlowMessage → `remove_flow_message` | — | — | `mid:String (path)` | `AjaxResult` |
| 8 | DELETE | `/flow/messagedispose/szzdmes/{mid}` | szzdFlowMessage → `szzd_flow_message` | — | — | `mid:String (path)` | `AjaxResult` |

### FlowMessageInfoController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/messageinfo/list` | list → `list` | — | — | `flowMessageInfo:FlowMessageInfo (query)` | `TableDataInfo` |
| 2 | GET | `/flow/messageinfo/listyb` | listyb → `listyb` | — | — | `flowMessageInfo:FlowMessageInfo (query)` | `TableDataInfo` |
| 3 | GET | `/flow/messageinfo/listyj` | listyj → `listyj` | — | — | `flowMessageInfo:FlowMessageInfo (query)` | `TableDataInfo` |
| 4 | GET | `/flow/messageinfo/listxx` | listxx → `listxx` | — | — | `flowMessageInfo:FlowMessageInfo (query)` | `TableDataInfo` |
| 5 | GET | `/flow/messageinfo/export` | export → `export` | — | 系统内部消息 / EXPORT | `flowMessageInfo:FlowMessageInfo (query)` | `AjaxResult` |
| 6 | GET | `/flow/messageinfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 7 | DELETE | `/flow/messageinfo/{ids}` | remove → `remove` | — | 系统内部消息 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 8 | GET | `/flow/messageinfo/exportShrz` | exportShrz → `export_shrz` | — | 导出审核日志 / EXPORT | `flowMessageInfo:FlowMessageInfo (query)` | `AjaxResult` |

### FlowNameController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowNameController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/flowname/list` | list → `list` | `flow:flowname:list` | — | `flowName:FlowName (query)` | `TableDataInfo` |
| 2 | GET | `/flow/flowname/listQuery` | listQuery → `list_query` | — | — | `flowName:FlowName (query)` | `TableDataInfo` |
| 3 | GET | `/flow/flowname/export` | export → `export` | `flow:flowname:export` | 流程名称 / EXPORT | `flowName:FlowName (query)` | `AjaxResult` |
| 4 | GET | `/flow/flowname/{id}` | getInfo → `get_info` | `flow:flowname:query` | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/flow/flowname` | add → `add` | `flow:flowname:add` | 流程名称 / INSERT | `flowName:FlowName (body)` | `AjaxResult` |
| 6 | PUT | `/flow/flowname` | edit → `edit` | `flow:flowname:edit` | 流程名称 / UPDATE | `flowName:FlowName (body)` | `AjaxResult` |
| 7 | DELETE | `/flow/flowname/{ids}` | remove → `remove` | `flow:flowname:remove` | 流程名称 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 8 | POST | `/flow/flowname/tbFlow` | tbFlow → `tb_flow` | `flow:flowname:edit` | 同步其他单位的工作流 / UPDATE | `flowName:FlowName (body)` | `AjaxResult` |

### FlowTemplateController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowTemplateController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/flow/flowtemplate/list` | list → `list` | — | — | `flowTemplate:FlowTemplate (query)` | `TableDataInfo` |
| 2 | GET | `/flow/flowtemplate/flowlist` | flowlist → `flowlist` | — | — | `flowTemplate:FlowTemplate (query)` | `AjaxResult` |
| 3 | GET | `/flow/flowtemplate/export` | export → `export` | — | 流程节点 / EXPORT | `flowTemplate:FlowTemplate (query)` | `AjaxResult` |
| 4 | GET | `/flow/flowtemplate/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/flow/flowtemplate` | add → `add` | — | 流程节点 / INSERT | `flowTemplate:FlowTemplate (body)` | `AjaxResult` |
| 6 | PUT | `/flow/flowtemplate` | edit → `edit` | — | 流程节点 / UPDATE | `flowTemplate:FlowTemplate (body)` | `AjaxResult` |
| 7 | DELETE | `/flow/flowtemplate/{ids}` | remove → `remove` | — | 流程节点 / DELETE | `ids:String[] (path)` | `AjaxResult` |

## generator

### GenController（15）

`ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/tool/gen/list` | genList → `gen_list` | `tool:gen:list` | — | `genTable:GenTable (query)` | `TableDataInfo` |
| 2 | GET | `/tool/gen/all/list` | getAllGenerateTableList → `get_all_generate_table_list` | — | — | `genTable:GenTable (query)` | `AjaxResult` |
| 3 | GET | `/tool/gen/{talbleId}` | getInfo → `get_info` | `tool:gen:query` | — | `talbleId:Long (path)` | `AjaxResult` |
| 4 | GET | `/tool/gen/db/list` | dataList → `data_list` | `tool:gen:list` | — | `genTable:GenTable (query)` | `TableDataInfo` |
| 5 | GET | `/tool/gen/column/{talbleId}` | columnList → `column_list` | `tool:gen:list` | — | `tableId:Long (query)` | `TableDataInfo` |
| 6 | POST | `/tool/gen/getColumnList` | getColumnList → `get_column_list` | — | — | `genTableColumn:GenTableColumn (body)` | `TableDataInfo` |
| 7 | POST | `/tool/gen/getAllColumnList` | getAllColumnList → `get_all_column_list` | — | — | `genTableColumn:GenTableColumn (body)` | `AjaxResult` |
| 8 | POST | `/tool/gen/importTable` | importTableSave → `import_table_save` | `tool:gen:list` | 代码生成 / IMPORT | `tables:String (query)` | `AjaxResult` |
| 9 | PUT | `/tool/gen` | editSave → `edit_save` | `tool:gen:edit` | 代码生成 / UPDATE | `genTable:GenTable (body)` | `AjaxResult` |
| 10 | DELETE | `/tool/gen/{tableIds}` | remove → `remove` | `tool:gen:remove` | 代码生成 / DELETE | `tableIds:Long[] (path)` | `AjaxResult` |
| 11 | GET | `/tool/gen/preview/{tableId}` | preview → `preview` | `tool:gen:preview` | — | `tableId:Long (path)` | `AjaxResult` |
| 12 | GET | `/tool/gen/download/{tableName}` | download → `download` | `tool:gen:code` | 代码生成 / GENCODE | `tableName:String (path)` | `void` |
| 13 | GET | `/tool/gen/genCode/{tableName}` | genCode → `gen_code` | `tool:gen:code` | 代码生成 / GENCODE | `tableName:String (path)` | `AjaxResult` |
| 14 | GET | `/tool/gen/synchDb/{tableName}` | synchDb → `synch_db` | `tool:gen:edit` | 代码生成 / UPDATE | `tableName:String (path)` | `AjaxResult` |
| 15 | GET | `/tool/gen/batchGenCode` | batchGenCode → `batch_gen_code` | `tool:gen:code` | 代码生成 / GENCODE | `tables:String (query)` | `void` |

## manager

### BigScreenController（12）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/bigScreen/carStatistics` | getCarStatistics → `get_car_statistics` | — | — | `param:IncomeStatisticParam (query)` | `AjaxResult` |
| 2 | GET | `/manager/bigScreen/carLocation` | getCarLocation → `get_car_location` | — | — | `param:CarLocationParam (query)` | `AjaxResult` |
| 3 | GET | `/manager/bigScreen/sectionList` | getSectionList → `get_section_list` | — | — | — | `AjaxResult` |
| 4 | GET | `/manager/bigScreen/tollGantryFwqList` | getTollList → `get_toll_list` | — | — | `sectionCode:String (query required=false)`; `type:String (query)` | `AjaxResult` |
| 5 | GET | `/manager/bigScreen/carVoList` | carVoList → `car_vo_list` | — | — | — | `AjaxResult` |
| 6 | GET | `/manager/bigScreen/carAudit` | getCarAudit → `get_car_audit` | — | — | `param:IncomeStatisticParam (query)` | `AjaxResult` |
| 7 | GET | `/manager/bigScreen/carWarning` | getCarWarning → `get_car_warning` | — | — | `param:CarLocationParam (query)` | `AjaxResult` |
| 8 | GET | `/manager/bigScreen/exceptionCar` | getExceptionCar → `get_exception_car` | — | — | — | `AjaxResult` |
| 9 | GET | `/manager/bigScreen/topTen` | topTen → `top_ten` | — | — | — | `AjaxResult` |
| 10 | GET | `/manager/bigScreen/orgList` | getOrgList → `get_org_list` | — | — | — | `AjaxResult` |
| 11 | GET | `/manager/bigScreen/incomeStatistic` | incomeStatistic → `income_statistic` | — | — | `param:IncomeStatisticParam (query)` | `AjaxResult` |
| 12 | GET | `/manager/bigScreen/exceptRecordList` | list → `list` | — | — | `carExceptRecord:CarExceptRecord (query)` | `TableDataInfo` |

### BussTestController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/BussTestController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/busstest/list` | list → `list` | `manager:busstest:list` | — | `bussTest:BussTest (query)` | `TableDataInfo` |
| 2 | GET | `/manager/busstest/export` | export → `export` | `manager:busstest:export` | 业务测试 / EXPORT | `bussTest:BussTest (query)` | `AjaxResult` |
| 3 | GET | `/manager/busstest/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/busstest` | add → `add` | `manager:busstest:add` | 业务测试 / INSERT | `bussTest:BussTest (body)` | `AjaxResult` |
| 5 | PUT | `/manager/busstest` | edit → `edit` | `manager:busstest:edit` | 业务测试 / UPDATE | `bussTest:BussTest (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/busstest/{ids}` | remove → `remove` | `manager:busstest:remove` | 业务测试 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 7 | POST | `/manager/busstest/syncCurrentTrack` | syncCurrentTrack → `sync_current_track` | `manager:busstest:syncTest` | — | — | `void` |

### CarAduitFreeController（10）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarAduitFreeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/aduitfree/list` | list → `list` | — | — | `carAduitFree:CarAduitFree (query)` | `TableDataInfo` |
| 2 | GET | `/manager/aduitfree/export` | export → `export` | — | 补缴处理 / EXPORT | `carAduitFree:CarAduitFree (query)` | `AjaxResult` |
| 3 | GET | `/manager/aduitfree/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/aduitfree` | add → `add` | — | 补缴处理 / INSERT | `carAduitFree:CarAduitFree (body)` | `AjaxResult` |
| 5 | PUT | `/manager/aduitfree` | edit → `edit` | — | 补缴处理 / UPDATE | `carAduitFree:CarAduitFree (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/aduitfree/{ids}` | remove → `remove` | — | 补缴处理 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 7 | GET | `/manager/aduitfree/incomeStatics` | incomeStatics → `income_statics` | — | — | `queryRo:CarConfimFreeQueryRo (query)` | `TableDataInfo` |
| 8 | GET | `/manager/aduitfree/exportIncomeStatics` | exportIncomeStatics → `export_income_statics` | — | — | `queryRo:CarConfimFreeQueryRo (query)` | `AjaxResult` |
| 9 | GET | `/manager/aduitfree/incomeDetailList` | incomeDetailList → `income_detail_list` | — | — | `carConfimFree:CarConfimFree (query)` | `TableDataInfo` |
| 10 | GET | `/manager/aduitfree/exportIncomeDetailList` | exportIncomeDetailList → `export_income_detail_list` | — | — | `carConfimFree:CarConfimFree (query)` | `AjaxResult` |

### CarConfimFreeController（13）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/confimfree/list` | list → `list` | — | — | `carConfimFree:CarConfimFree (query)` | `TableDataInfo` |
| 2 | GET | `/manager/confimfree/listCarNo` | listCarNo → `list_car_no` | — | — | `carConfimFree:CarConfimFree (query)` | `TableDataInfo` |
| 3 | GET | `/manager/confimfree/listCount` | listCount → `list_count` | — | — | `carConfimFree:CarConfimFree (query)` | `AjaxResult` |
| 4 | GET | `/manager/confimfree/export` | export → `export` | — | 确认补缴 / EXPORT | `carConfimFree:CarConfimFree (query)` | `AjaxResult` |
| 5 | GET | `/manager/confimfree/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 6 | POST | `/manager/confimfree` | add → `add` | — | 确认补缴 / INSERT | `carConfimFree:CarConfimFree (body)` | `AjaxResult` |
| 7 | PUT | `/manager/confimfree` | edit → `edit` | — | 确认补缴 / UPDATE | `carConfimFree:CarConfimFree (body)` | `AjaxResult` |
| 8 | DELETE | `/manager/confimfree/{ids}` | remove → `remove` | — | 确认补缴 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 9 | GET | `/manager/confimfree/except/{exceptIds}` | getExceptIds → `get_except_ids` | — | — | `exceptIds:String (path)` | `AjaxResult` |
| 10 | GET | `/manager/confimfree/concernedList` | concernedList → `concerned_list` | — | — | `carConfimFree:CarConfimFree (query)` | `TableDataInfo` |
| 11 | GET | `/manager/confimfree/exportConcernedList` | exportConcernedList → `export_concerned_list` | — | — | `carConfimFree:CarConfimFree (query)` | `AjaxResult` |
| 12 | GET | `/manager/confimfree/carStatics` | getCarStatics → `get_car_statics` | — | — | `queryRo:CarConfimFreeQueryRo (query)` | `TableDataInfo` |
| 13 | GET | `/manager/confimfree/exportCarStatics` | exportCarStatics → `export_car_statics` | — | — | `queryRo:CarConfimFreeQueryRo (query)` | `AjaxResult` |

### CarExceptRecordController（13）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/exceptrecord/list` | list → `list` | — | — | `carExceptRecord:CarExceptRecord (query)` | `TableDataInfo` |
| 2 | GET | `/manager/exceptrecord/listCarNo` | listCarNo → `list_car_no` | — | — | `carExceptRecord:CarExceptRecord (query)` | `TableDataInfo` |
| 3 | GET | `/manager/exceptrecord/listCarOrgId` | listCarOrgId → `list_car_org_id` | — | — | `carExceptRecord:CarExceptRecord (query)` | `TableDataInfo` |
| 4 | GET | `/manager/exceptrecord/exportOrgId` | exportOrgId → `export_org_id` | — | 异常车辆流水 / EXPORT | `carExceptRecord:CarExceptRecord (query)` | `AjaxResult` |
| 5 | GET | `/manager/exceptrecord/listExceptId` | listExceptId → `list_except_id` | — | — | `carExceptRecord:CarExceptRecord (query)` | `TableDataInfo` |
| 6 | GET | `/manager/exceptrecord/exceptRecordCount` | exceptRecordCount → `except_record_count` | — | — | `carExceptRecord:CarExceptRecord (query)` | `AjaxResult` |
| 7 | GET | `/manager/exceptrecord/export` | export → `export` | — | 异常车辆流水 / EXPORT | `carExceptRecord:CarExceptRecord (query)` | `AjaxResult` |
| 8 | GET | `/manager/exceptrecord/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 9 | POST | `/manager/exceptrecord` | add → `add` | — | 异常车辆流水 / INSERT | `carExceptRecord:CarExceptRecord (body)` | `AjaxResult` |
| 10 | PUT | `/manager/exceptrecord` | edit → `edit` | — | 异常车辆流水 / UPDATE | `carExceptRecord:CarExceptRecord (body)` | `AjaxResult` |
| 11 | DELETE | `/manager/exceptrecord/{ids}` | remove → `remove` | — | 异常车辆流水 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 12 | GET | `/manager/exceptrecord/getConfirmId/{id}` | getConfirmId → `get_confirm_id` | — | — | `id:String (path)` | `AjaxResult` |
| 13 | POST | `/manager/exceptrecord/import` | doImport → `do_import` | — | 新增流水导入 / IMPORT | `file:MultipartFile (query)` | `AjaxResult` |

### CarFeeRecordController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarFeeRecordController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/feerecord/list` | list → `list` | `manager:feerecord:list` | — | `carFeeRecord:CarFeeRecord (query)` | `TableDataInfo` |
| 2 | GET | `/manager/feerecord/export` | export → `export` | `manager:feerecord:export` | 收费流水 / EXPORT | `carFeeRecord:CarFeeRecord (query)` | `AjaxResult` |
| 3 | GET | `/manager/feerecord/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/feerecord` | add → `add` | `manager:feerecord:add` | 收费流水 / INSERT | `carFeeRecord:CarFeeRecord (body)` | `AjaxResult` |
| 5 | PUT | `/manager/feerecord` | edit → `edit` | `manager:feerecord:edit` | 收费流水 / UPDATE | `carFeeRecord:CarFeeRecord (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/feerecord/{ids}` | remove → `remove` | `manager:feerecord:remove` | 收费流水 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarInfoController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/carinfo/list` | list → `list` | `manager:carinfo:list` | — | `carInfo:CarInfo (query)` | `TableDataInfo` |
| 2 | GET | `/manager/carinfo/listAll` | listAll → `list_all` | — | — | `carInfo:CarInfo (query)` | `TableDataInfo` |
| 3 | GET | `/manager/carinfo/export` | export → `export` | `manager:carinfo:export` | 车辆信息 / EXPORT | `carInfo:CarInfo (query)` | `AjaxResult` |
| 4 | GET | `/manager/carinfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/manager/carinfo` | add → `add` | — | 车辆信息 / INSERT | `carInfo:CarInfo (body)` | `AjaxResult` |
| 6 | PUT | `/manager/carinfo` | edit → `edit` | `manager:carinfo:edit` | 车辆信息 / UPDATE | `carInfo:CarInfo (body)` | `AjaxResult` |
| 7 | DELETE | `/manager/carinfo/{ids}` | remove → `remove` | `manager:carinfo:remove` | 车辆信息 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 8 | POST | `/manager/carinfo/import` | doImport → `do_import` | — | 车辆信息 / IMPORT | `file:MultipartFile (query)` | `AjaxResult` |

### CarQueryLogController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarQueryLogController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/querylog/list` | list → `list` | `manager:querylog:list` | — | `carQueryLog:CarQueryLog (query)` | `TableDataInfo` |
| 2 | GET | `/manager/querylog/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 3 | POST | `/manager/querylog` | add → `add` | `manager:querylog:add` | 查询日志 / INSERT | `carQueryLog:CarQueryLog (body)` | `AjaxResult` |
| 4 | PUT | `/manager/querylog` | edit → `edit` | `manager:querylog:edit` | 查询日志 / UPDATE | `carQueryLog:CarQueryLog (body)` | `AjaxResult` |
| 5 | DELETE | `/manager/querylog/{ids}` | remove → `remove` | `manager:querylog:remove` | 查询日志 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 6 | GET | `/manager/querylog/export` | export → `export` | `manager:querylog:export` | 日志信息 / EXPORT | `carQueryLog:CarQueryLog (query)` | `AjaxResult` |

### CarRouteDetailController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteDetailController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/routedetail/list` | list → `list` | `manager:routedetail:list` | — | `carRouteDetail:CarRouteDetail (query)` | `TableDataInfo` |
| 2 | GET | `/manager/routedetail/export` | export → `export` | `manager:routedetail:export` | 常用路线明细 / EXPORT | `carRouteDetail:CarRouteDetail (query)` | `AjaxResult` |
| 3 | GET | `/manager/routedetail/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/routedetail` | add → `add` | `manager:routedetail:add` | 常用路线明细 / INSERT | `carRouteDetail:CarRouteDetail (body)` | `AjaxResult` |
| 5 | PUT | `/manager/routedetail` | edit → `edit` | `manager:routedetail:edit` | 常用路线明细 / UPDATE | `carRouteDetail:CarRouteDetail (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/routedetail/{ids}` | remove → `remove` | `manager:routedetail:remove` | 常用路线明细 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarRouteInfoController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/routeinfo/list` | list → `list` | `manager:routeinfo:list` | — | `carRouteInfo:CarRouteInfo (query)` | `TableDataInfo` |
| 2 | GET | `/manager/routeinfo/export` | export → `export` | `manager:routeinfo:export` | 常用路线 / EXPORT | `carRouteInfo:CarRouteInfo (query)` | `AjaxResult` |
| 3 | GET | `/manager/routeinfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/routeinfo` | add → `add` | `manager:routeinfo:add` | 常用路线 / INSERT | `carRouteInfo:CarRouteInfo (body)` | `AjaxResult` |
| 5 | PUT | `/manager/routeinfo` | edit → `edit` | `manager:routeinfo:edit` | 常用路线 / UPDATE | `carRouteInfo:CarRouteInfo (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/routeinfo/{ids}` | remove → `remove` | `manager:routeinfo:remove` | 常用路线 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarSplitRecordController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSplitRecordController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/splitrecord/list` | list → `list` | `manager:splitrecord:list` | — | `carSplitRecord:CarSplitRecord (query)` | `TableDataInfo` |
| 2 | GET | `/manager/splitrecord/export` | export → `export` | `manager:splitrecord:export` | 拆分流水 / EXPORT | `carSplitRecord:CarSplitRecord (query)` | `AjaxResult` |
| 3 | GET | `/manager/splitrecord/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/splitrecord` | add → `add` | `manager:splitrecord:add` | 拆分流水 / INSERT | `carSplitRecord:CarSplitRecord (body)` | `AjaxResult` |
| 5 | PUT | `/manager/splitrecord` | edit → `edit` | `manager:splitrecord:edit` | 拆分流水 / UPDATE | `carSplitRecord:CarSplitRecord (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/splitrecord/{ids}` | remove → `remove` | `manager:splitrecord:remove` | 拆分流水 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarSuspiciousBackController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousBackController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/carsuspiciousback/list` | list → `list` | `manager:carsuspiciousback:list` | — | `carSuspiciousBack:CarSuspiciousBack (query)` | `TableDataInfo` |
| 2 | GET | `/manager/carsuspiciousback/export` | export → `export` | `manager:carsuspiciousback:export` | 可疑车辆备份 / EXPORT | `carSuspiciousBack:CarSuspiciousBack (query)` | `AjaxResult` |
| 3 | GET | `/manager/carsuspiciousback/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/carsuspiciousback` | add → `add` | `manager:carsuspiciousback:add` | 可疑车辆备份 / INSERT | `carSuspiciousBack:CarSuspiciousBack (body)` | `AjaxResult` |
| 5 | PUT | `/manager/carsuspiciousback` | edit → `edit` | `manager:carsuspiciousback:edit` | 可疑车辆备份 / UPDATE | `carSuspiciousBack:CarSuspiciousBack (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/carsuspiciousback/{ids}` | remove → `remove` | `manager:carsuspiciousback:remove` | 可疑车辆备份 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarSuspiciousCheckController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousCheckController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/suspiciouscheck/list` | list → `list` | `manager:suspiciouscheck:list` | — | `carSuspiciousCheck:CarSuspiciousCheck (query)` | `TableDataInfo` |
| 2 | GET | `/manager/suspiciouscheck/export` | export → `export` | `manager:suspiciouscheck:export` | 可疑车辆人工核实 / EXPORT | `carSuspiciousCheck:CarSuspiciousCheck (query)` | `AjaxResult` |
| 3 | GET | `/manager/suspiciouscheck/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/suspiciouscheck` | add → `add` | `manager:suspiciouscheck:add` | 可疑车辆人工核实 / INSERT | `carSuspiciousCheck:CarSuspiciousCheck (body)` | `AjaxResult` |
| 5 | PUT | `/manager/suspiciouscheck` | edit → `edit` | `manager:suspiciouscheck:edit` | 可疑车辆人工核实 / UPDATE | `carSuspiciousCheck:CarSuspiciousCheck (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/suspiciouscheck/{ids}` | remove → `remove` | `manager:suspiciouscheck:remove` | 可疑车辆人工核实 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarSuspiciousController（15）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/suspicious/list` | list → `list` | `manager:suspicious:list` | — | `carSuspicious:CarSuspicious (query)` | `TableDataInfo` |
| 2 | GET | `/manager/suspicious/listCarNo` | listCarNo → `list_car_no` | — | — | `carSuspicious:CarSuspicious (query)` | `TableDataInfo` |
| 3 | GET | `/manager/suspicious/listFileCarNo` | listFileCarNo → `list_file_car_no` | — | — | `carSuspicious:CarSuspicious (query)` | `TableDataInfo` |
| 4 | GET | `/manager/suspicious/exportAbnormalPassage` | exportAbnormalPassage → `export_abnormal_passage` | — | — | `carSuspiciousId:String (query)` | `void` |
| 5 | GET | `/manager/suspicious/listAll` | listAll → `list_all` | — | — | `carSuspicious:CarSuspicious (query)` | `TableDataInfo` |
| 6 | GET | `/manager/suspicious/export` | export → `export` | `manager:suspicious:export` | 可疑车辆 / EXPORT | `carSuspicious:CarSuspicious (query)` | `AjaxResult` |
| 7 | GET | `/manager/suspicious/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 8 | POST | `/manager/suspicious` | add → `add` | `manager:suspicious:add` | 可疑车辆 / INSERT | `carSuspicious:CarSuspicious (body)` | `AjaxResult` |
| 9 | PUT | `/manager/suspicious` | edit → `edit` | `manager:suspicious:edit` | 可疑车辆 / UPDATE | `carSuspicious:CarSuspicious (body)` | `AjaxResult` |
| 10 | DELETE | `/manager/suspicious/{ids}` | remove → `remove` | `manager:suspicious:remove` | 可疑车辆 / DELETE | `ids:String[] (path)` | `AjaxResult` |
| 11 | PUT | `/manager/suspicious/check` | check → `check` | — | 可疑车辆 / UPDATE | `carSuspicious:CarSuspicious (body)` | `AjaxResult` |
| 12 | POST | `/manager/suspicious/syncSuspiciousCarTask` | syncSuspiciousCarTask → `sync_suspicious_car_task` | — | — | `suspiciousCarVO:SuspiciousCarVO (body)` | `AjaxResult` |
| 13 | GET | `/manager/suspicious/listHistory` | listHistory → `list_history` | `manager:suspicious:list` | — | `carSuspicious:CarSuspicious (query)` | `TableDataInfo` |
| 14 | GET | `/manager/suspicious/history/{id}` | gethistoryInfo → `gethistory_info` | — | — | `id:String (path)` | `AjaxResult` |
| 15 | GET | `/manager/suspicious/exportHistory` | exportHistory → `export_history` | `manager:suspicious:export` | 可疑车辆 / EXPORT | `carSuspicious:CarSuspicious (query)` | `AjaxResult` |

### CarTrackInfoController（10）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/cartrackinfo/list` | list → `list` | `manager:cartrackinfo:list` | — | `carTrackInfo:CarTrackInfo (query)` | `TableDataInfo` |
| 2 | GET | `/manager/cartrackinfo/listByCarId` | listByCarId → `list_by_car_id` | — | — | `zdataTrailTracks:ZdataTrailTracks (query)` | `TableDataInfo` |
| 3 | GET | `/manager/cartrackinfo/listByCarByTime` | listByCarByTime → `list_by_car_by_time` | — | — | `zdataTrailTracks:ZdataTrailTracks (query)` | `TableDataInfo` |
| 4 | PUT | `/manager/cartrackinfo/changeTrailInfo` | changeTrailInfo → `change_trail_info` | — | 车辆行驶轨迹 / UPDATE | `trailInfo:TrailInfo (body)` | `AjaxResult` |
| 5 | GET | `/manager/cartrackinfo/carSnapShot` | carSnapShot → `car_snap_shot` | — | — | `trailBo:TrailBo (query)` | `AjaxResult` |
| 6 | GET | `/manager/cartrackinfo/export` | export → `export` | `manager:cartrackinfo:export` | 车辆行驶轨迹 / EXPORT | `carTrackInfo:CarTrackInfo (query)` | `AjaxResult` |
| 7 | GET | `/manager/cartrackinfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 8 | POST | `/manager/cartrackinfo` | add → `add` | `manager:cartrackinfo:add` | 车辆行驶轨迹 / INSERT | `carTrackInfo:CarTrackInfo (body)` | `AjaxResult` |
| 9 | PUT | `/manager/cartrackinfo` | edit → `edit` | `manager:cartrackinfo:edit` | 车辆行驶轨迹 / UPDATE | `carTrackInfo:CarTrackInfo (body)` | `AjaxResult` |
| 10 | DELETE | `/manager/cartrackinfo/{ids}` | remove → `remove` | `manager:cartrackinfo:remove` | 车辆行驶轨迹 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarWarningInfoController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/carwarning/list` | list → `list` | — | — | `carWarningInfo:CarWarningInfo (query)` | `TableDataInfo` |
| 2 | GET | `/manager/carwarning/export` | export → `export` | `manager:carwarning:export` | 预警车辆 / EXPORT | `carWarningInfo:CarWarningInfo (query)` | `AjaxResult` |
| 3 | GET | `/manager/carwarning/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/carwarning` | add → `add` | `manager:carwarning:add` | 预警车辆 / INSERT | `carWarningInfo:CarWarningInfo (body)` | `AjaxResult` |
| 5 | PUT | `/manager/carwarning` | edit → `edit` | `manager:carwarning:edit` | 预警车辆 / UPDATE | `carWarningInfo:CarWarningInfo (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/carwarning/{ids}` | remove → `remove` | `manager:carwarning:remove` | 预警车辆 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarWarningRuleController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningRuleController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/warningrule/list` | list → `list` | `manager:warningrule:list` | — | `carWarningRule:CarWarningRule (query)` | `TableDataInfo` |
| 2 | GET | `/manager/warningrule/export` | export → `export` | `manager:warningrule:export` | 预警规则 / EXPORT | `carWarningRule:CarWarningRule (query)` | `AjaxResult` |
| 3 | GET | `/manager/warningrule/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/warningrule` | add → `add` | `manager:warningrule:add` | 预警规则 / INSERT | `carWarningRule:CarWarningRule (body)` | `AjaxResult` |
| 5 | PUT | `/manager/warningrule` | edit → `edit` | `manager:warningrule:edit` | 预警规则 / UPDATE | `carWarningRule:CarWarningRule (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/warningrule/{ids}` | remove → `remove` | `manager:warningrule:remove` | 预警规则 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### CarWhiteInfoController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWhiteInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/whiteinfo/list` | list → `list` | `manager:whiteinfo:list` | — | `carWhiteInfo:CarWhiteInfo (query)` | `TableDataInfo` |
| 2 | GET | `/manager/whiteinfo/export` | export → `export` | `manager:whiteinfo:export` | 车俩白名单 / EXPORT | `carWhiteInfo:CarWhiteInfo (query)` | `AjaxResult` |
| 3 | GET | `/manager/whiteinfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/whiteinfo` | add → `add` | `manager:whiteinfo:add` | 车俩白名单 / INSERT | `carWhiteInfo:CarWhiteInfo (body)` | `AjaxResult` |
| 5 | PUT | `/manager/whiteinfo` | edit → `edit` | `manager:whiteinfo:edit` | 车俩白名单 / UPDATE | `carWhiteInfo:CarWhiteInfo (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/whiteinfo/{ids}` | remove → `remove` | `manager:whiteinfo:remove` | 车俩白名单 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### GantryCarController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryCarController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/gantrycar/list` | list → `list` | `manager:gantrycar:list` | — | `gantryCar:GantryCar (query)` | `TableDataInfo` |
| 2 | GET | `/manager/gantrycar/export` | export → `export` | `manager:gantrycar:export` | 门架拍识查询 / EXPORT | `gantryCar:GantryCar (query)` | `AjaxResult` |
| 3 | GET | `/manager/gantrycar/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/gantrycar` | add → `add` | `manager:gantrycar:add` | 门架拍识查询 / INSERT | `gantryCar:GantryCar (body)` | `AjaxResult` |
| 5 | PUT | `/manager/gantrycar` | edit → `edit` | `manager:gantrycar:edit` | 门架拍识查询 / UPDATE | `gantryCar:GantryCar (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/gantrycar/{ids}` | remove → `remove` | `manager:gantrycar:remove` | 门架拍识查询 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### GantryTradeInfoController（6）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryTradeInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/manager/gantrytrade/list` | list → `list` | `manager:gantrytrade:list` | — | `gantryTradeInfo:GantryTradeInfo (query)` | `TableDataInfo` |
| 2 | GET | `/manager/gantrytrade/export` | export → `export` | `manager:gantrytrade:export` | 门架交易查询 / EXPORT | `gantryTradeInfo:GantryTradeInfo (query)` | `AjaxResult` |
| 3 | GET | `/manager/gantrytrade/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 4 | POST | `/manager/gantrytrade` | add → `add` | `manager:gantrytrade:add` | 门架交易查询 / INSERT | `gantryTradeInfo:GantryTradeInfo (body)` | `AjaxResult` |
| 5 | PUT | `/manager/gantrytrade` | edit → `edit` | `manager:gantrytrade:edit` | 门架交易查询 / UPDATE | `gantryTradeInfo:GantryTradeInfo (body)` | `AjaxResult` |
| 6 | DELETE | `/manager/gantrytrade/{ids}` | remove → `remove` | `manager:gantrytrade:remove` | 门架交易查询 / DELETE | `ids:String[] (path)` | `AjaxResult` |

## monitor

### CacheController（1）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/CacheController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/cache` | getInfo → `get_info` | `monitor:cache:list` | — | — | `AjaxResult` |

### ServerController（1）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/ServerController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/server` | getInfo → `get_info` | `monitor:server:list` | — | — | `AjaxResult` |

### SysLogininforController（4）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysLogininforController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/logininfor/list` | list → `list` | `monitor:logininfor:list` | — | `logininfor:SysLogininfor (query)` | `TableDataInfo` |
| 2 | GET | `/monitor/logininfor/export` | export → `export` | `monitor:logininfor:export` | 登录日志 / EXPORT | `logininfor:SysLogininfor (query)` | `AjaxResult` |
| 3 | DELETE | `/monitor/logininfor/{infoIds}` | remove → `remove` | `monitor:logininfor:remove` | 登录日志 / DELETE | `infoIds:Long[] (path)` | `AjaxResult` |
| 4 | DELETE | `/monitor/logininfor/clean` | clean → `clean` | `monitor:logininfor:remove` | 登录日志 / CLEAN | — | `AjaxResult` |

### SysOperlogController（4）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysOperlogController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/operlog/list` | list → `list` | `monitor:operlog:list` | — | `operLog:SysOperLog (query)` | `TableDataInfo` |
| 2 | GET | `/monitor/operlog/export` | export → `export` | `monitor:operlog:export` | 操作日志 / EXPORT | `operLog:SysOperLog (query)` | `AjaxResult` |
| 3 | DELETE | `/monitor/operlog/{operIds}` | remove → `remove` | `monitor:operlog:remove` | — | `operIds:Long[] (path)` | `AjaxResult` |
| 4 | DELETE | `/monitor/operlog/clean` | clean → `clean` | `monitor:operlog:remove` | 操作日志 / CLEAN | — | `AjaxResult` |

### SysUserOnlineController（2）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysUserOnlineController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/online/list` | list → `list` | `monitor:online:list` | — | `ipaddr:String (query)`; `userName:String (query)` | `TableDataInfo` |
| 2 | DELETE | `/monitor/online/{tokenId}` | forceLogout → `force_logout` | `monitor:online:forceLogout` | 在线用户 / FORCE | `tokenId:String (path)` | `AjaxResult` |

## quartz

### SysJobController（8）

`ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/job/list` | list → `list` | `monitor:job:list` | — | `sysJob:SysJob (query)` | `TableDataInfo` |
| 2 | GET | `/monitor/job/export` | export → `export` | `monitor:job:export` | 定时任务 / EXPORT | `sysJob:SysJob (query)` | `AjaxResult` |
| 3 | GET | `/monitor/job/{jobId}` | getInfo → `get_info` | `monitor:job:query` | — | `jobId:Long (path)` | `AjaxResult` |
| 4 | POST | `/monitor/job` | add → `add` | `monitor:job:add` | 定时任务 / INSERT | `sysJob:SysJob (body)` | `AjaxResult` |
| 5 | PUT | `/monitor/job` | edit → `edit` | `monitor:job:edit` | 定时任务 / UPDATE | `sysJob:SysJob (body)` | `AjaxResult` |
| 6 | PUT | `/monitor/job/changeStatus` | changeStatus → `change_status` | `monitor:job:changeStatus` | 定时任务 / UPDATE | `job:SysJob (body)` | `AjaxResult` |
| 7 | PUT | `/monitor/job/run` | run → `run` | `monitor:job:changeStatus` | 定时任务 / UPDATE | `job:SysJob (body)` | `AjaxResult` |
| 8 | DELETE | `/monitor/job/{jobIds}` | remove → `remove` | `monitor:job:remove` | 定时任务 / DELETE | `jobIds:Long[] (path)` | `AjaxResult` |

### SysJobLogController（5）

`ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/monitor/jobLog/list` | list → `list` | `monitor:job:list` | — | `sysJobLog:SysJobLog (query)` | `TableDataInfo` |
| 2 | GET | `/monitor/jobLog/export` | export → `export` | `monitor:job:export` | 任务调度日志 / EXPORT | `sysJobLog:SysJobLog (query)` | `AjaxResult` |
| 3 | GET | `/monitor/jobLog/{configId}` | getInfo → `get_info` | `monitor:job:query` | — | `jobLogId:Long (path)` | `AjaxResult` |
| 4 | DELETE | `/monitor/jobLog/{jobLogIds}` | remove → `remove` | `monitor:job:remove` | 定时任务调度日志 / DELETE | `jobLogIds:Long[] (path)` | `AjaxResult` |
| 5 | DELETE | `/monitor/jobLog/clean` | clean → `clean` | `monitor:job:remove` | 调度日志 / CLEAN | — | `AjaxResult` |

## system

### SysConfigController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/config/list` | list → `list` | `system:config:list` | — | `config:SysConfig (query)` | `TableDataInfo` |
| 2 | GET | `/system/config/export` | export → `export` | `system:config:export` | 参数管理 / EXPORT | `config:SysConfig (query)` | `AjaxResult` |
| 3 | GET | `/system/config/{configId}` | getInfo → `get_info` | `system:config:query` | — | `configId:Long (path)` | `AjaxResult` |
| 4 | GET | `/system/config/configKey/{configKey}` | getConfigKey → `get_config_key` | — | — | `configKey:String (path)` | `AjaxResult` |
| 5 | POST | `/system/config` | add → `add` | `system:config:add` | 参数管理 / INSERT | `config:SysConfig (body)` | `AjaxResult` |
| 6 | PUT | `/system/config` | edit → `edit` | `system:config:edit` | 参数管理 / UPDATE | `config:SysConfig (body)` | `AjaxResult` |
| 7 | DELETE | `/system/config/{configIds}` | remove → `remove` | `system:config:remove` | 参数管理 / DELETE | `configIds:Long[] (path)` | `AjaxResult` |
| 8 | DELETE | `/system/config/clearCache` | clearCache → `clear_cache` | `system:config:remove` | 参数管理 / CLEAN | — | `AjaxResult` |

### SysDeptController（11）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDeptController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/dept/list` | list → `list` | `system:dept:list` | — | `dept:SysDept (query)` | `AjaxResult` |
| 2 | GET | `/system/dept/getList` | getList → `get_list` | — | — | `dept:SysDept (query)` | `AjaxResult` |
| 3 | GET | `/system/dept/list/exclude/{deptId}` | excludeChild → `exclude_child` | `system:dept:list` | — | `deptId:Long (path required=false)` | `AjaxResult` |
| 4 | GET | `/system/dept/{deptId}` | getInfo → `get_info` | `system:dept:query` | — | `deptId:Long (path)` | `AjaxResult` |
| 5 | GET | `/system/dept/treeselect` | treeselect → `treeselect` | — | — | `dept:SysDept (query)` | `AjaxResult` |
| 6 | GET | `/system/dept/treeselectNew` | treeselectNew → `treeselect_new` | — | — | `dept:SysDept (query)` | `AjaxResult` |
| 7 | GET | `/system/dept/roleDeptTreeselect/{roleId}` | roleDeptTreeselect → `role_dept_treeselect` | — | — | `roleId:Long (path)` | `AjaxResult` |
| 8 | POST | `/system/dept` | add → `add` | `system:dept:add` | 部门管理 / INSERT | `dept:SysDept (body)` | `AjaxResult` |
| 9 | PUT | `/system/dept` | edit → `edit` | `system:dept:edit` | 部门管理 / UPDATE | `dept:SysDept (body)` | `AjaxResult` |
| 10 | DELETE | `/system/dept/{deptId}` | remove → `remove` | `system:dept:remove` | 部门管理 / DELETE | `deptId:Long (path)` | `AjaxResult` |
| 11 | GET | `/system/dept/getCompanyList` | getCompanyList → `get_company_list` | — | — | — | `AjaxResult` |

### SysDictDataController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictDataController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/dict/data/list` | list → `list` | `system:dict:list` | — | `dictData:SysDictData (query)` | `TableDataInfo` |
| 2 | GET | `/system/dict/data/export` | export → `export` | `system:dict:export` | 字典数据 / EXPORT | `dictData:SysDictData (query)` | `AjaxResult` |
| 3 | GET | `/system/dict/data/{dictCode}` | getInfo → `get_info` | `system:dict:query` | — | `dictCode:Long (path)` | `AjaxResult` |
| 4 | GET | `/system/dict/data/type/{dictType}` | dictType → `dict_type` | — | — | `dictType:String (path)` | `AjaxResult` |
| 5 | GET | `/system/dict/data/typemore/{dictType}` | dictTypeMore → `dict_type_more` | — | — | `dictType:String (path)` | `AjaxResult` |
| 6 | POST | `/system/dict/data` | add → `add` | `system:dict:add` | 字典数据 / INSERT | `dict:SysDictData (body)` | `AjaxResult` |
| 7 | PUT | `/system/dict/data` | edit → `edit` | `system:dict:edit` | 字典数据 / UPDATE | `dict:SysDictData (body)` | `AjaxResult` |
| 8 | DELETE | `/system/dict/data/{dictCodes}` | remove → `remove` | `system:dict:remove` | 字典类型 / DELETE | `dictCodes:Long[] (path)` | `AjaxResult` |

### SysDictTypeController（8）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictTypeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/dict/type/list` | list → `list` | `system:dict:list` | — | `dictType:SysDictType (query)` | `TableDataInfo` |
| 2 | GET | `/system/dict/type/export` | export → `export` | `system:dict:export` | 字典类型 / EXPORT | `dictType:SysDictType (query)` | `AjaxResult` |
| 3 | GET | `/system/dict/type/{dictId}` | getInfo → `get_info` | `system:dict:query` | — | `dictId:Long (path)` | `AjaxResult` |
| 4 | POST | `/system/dict/type` | add → `add` | `system:dict:add` | 字典类型 / INSERT | `dict:SysDictType (body)` | `AjaxResult` |
| 5 | PUT | `/system/dict/type` | edit → `edit` | `system:dict:edit` | 字典类型 / UPDATE | `dict:SysDictType (body)` | `AjaxResult` |
| 6 | DELETE | `/system/dict/type/{dictIds}` | remove → `remove` | `system:dict:remove` | 字典类型 / DELETE | `dictIds:Long[] (path)` | `AjaxResult` |
| 7 | DELETE | `/system/dict/type/clearCache` | clearCache → `clear_cache` | `system:dict:remove` | 字典类型 / CLEAN | — | `AjaxResult` |
| 8 | GET | `/system/dict/type/optionselect` | optionselect → `optionselect` | — | — | — | `AjaxResult` |

### SysFileController（17）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysFileController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/file/list` | list → `list` | `base:sysflie:list` | — | `sysFile:SysFile (query)` | `TableDataInfo` |
| 2 | GET | `/system/file/getInfoById/{id}` | getInfoById → `get_info_by_id` | — | — | `id:Long (path)` | `AjaxResult` |
| 3 | GET | `/system/file/{ids}` | getInfo → `get_info` | — | — | `ids:String (path)` | `AjaxResult` |
| 4 | POST | `/system/file/upload` | upload → `upload` | — | 文件 / INSERT | `files:MultipartFile[] (query)` | `AjaxResult` |
| 5 | POST | `/system/file/uploadByUrl` | uploadByUrl → `upload_by_url` | — | 文件 / INSERT | `uploadRo:UploadRo (body)` | `AjaxResult` |
| 6 | POST | `/system/file/uploadSupplier` | uploadSupplier → `upload_supplier` | — | 文件 / INSERT | `files:MultipartFile[] (query)`; `bussNames:String[] (query)` | `AjaxResult` |
| 7 | POST | `/system/file/uploadPdf` | uploadPdf → `upload_pdf` | — | 文件 / INSERT | `files:MultipartFile[] (query)` | `AjaxResult` |
| 8 | GET | `/system/file/{bucket}/{fileName}` | file → `file` | — | — | `bucket:String (path)`; `fileName:String (path)` | `void` |
| 9 | GET | `/system/file/view/{bucket}/{fileName}` | fileview → `fileview` | — | — | `bucket:String (path)`; `fileName:String (path)` | `void` |
| 10 | DELETE | `/system/file/del/{id}` | removeById → `remove_by_id` | — | 文件 / DELETE | `id:Long (path)` | `AjaxResult` |
| 11 | DELETE | `/system/file/{ids}` | remove → `remove` | `base:supplier:remove` | 文件 / DELETE | `ids:Long[] (path)` | `AjaxResult` |
| 12 | POST | `/system/file/uploadFileId` | uploadFileId → `upload_file_id` | — | 文件 / INSERT | `sysFile:SysFile (body)` | `AjaxResult` |
| 13 | POST | `/system/file/uploadFileEnc` | uploadFileEnc → `upload_file_enc` | — | 文件 / INSERT | `files:MultipartFile[] (query)` | `AjaxResult` |
| 14 | PUT | `/system/file` | edit → `edit` | — | 文件管理 / UPDATE | `sysFile:SysFile (body)` | `AjaxResult` |
| 15 | GET | `/system/file/getNewCa` | getNewCa → `get_new_ca` | — | — | `sysFile:SysFile (query)` | `AjaxResult` |
| 16 | POST | `/system/file/updateCAFile` | updateCAFile → `update_ca_file` | — | 文件 / UPDATE | `sysFile:SysFile (body)` | `AjaxResult` |
| 17 | POST | `/system/file/uploadFile` | upload → `upload` | — | — | — | `AjaxResult` |

### SysIndexController（5）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/` | index → `index` | — | — | — | `String` |
| 2 | POST | `/` | index → `index` | — | — | — | `String` |
| 3 | PUT | `/` | index → `index` | — | — | — | `String` |
| 4 | DELETE | `/` | index → `index` | — | — | — | `String` |
| 5 | PATCH | `/` | index → `index` | — | — | — | `String` |

### SysIndexMenuController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexMenuController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/indexmenu/list` | list → `list` | — | — | `sysIndexMenu:SysIndexMenu (query)` | `TableDataInfo` |
| 2 | GET | `/system/indexmenu/mylist` | getSysIndexMenulist → `get_sys_index_menulist` | — | — | `sysIndexMenu:SysIndexMenu (query)` | `AjaxResult` |
| 3 | GET | `/system/indexmenu/export` | export → `export` | `system:indexmenu:export` | 用户常用菜单 / EXPORT | `sysIndexMenu:SysIndexMenu (query)` | `AjaxResult` |
| 4 | GET | `/system/indexmenu/{id}` | getInfo → `get_info` | `system:indexmenu:query` | — | `id:Long (path)` | `AjaxResult` |
| 5 | POST | `/system/indexmenu` | add → `add` | — | 用户常用菜单 / INSERT | `sysIndexMenu:SysIndexMenu (body)` | `AjaxResult` |
| 6 | PUT | `/system/indexmenu` | edit → `edit` | `system:indexmenu:edit` | 用户常用菜单 / UPDATE | `sysIndexMenu:SysIndexMenu (body)` | `AjaxResult` |
| 7 | DELETE | `/system/indexmenu/{ids}` | remove → `remove` | — | 用户常用菜单 / DELETE | `ids:Long[] (path)` | `AjaxResult` |

### SysLoginController（3）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysLoginController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | POST | `/login` | login → `login` | — | — | `loginBody:LoginBody (body)` | `AjaxResult` |
| 2 | GET | `/getInfo` | getInfo → `get_info` | — | — | — | `AjaxResult` |
| 3 | GET | `/getRouters` | getRouters → `get_routers` | — | — | — | `AjaxResult` |

### SysMenuController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysMenuController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/menu/list` | list → `list` | `system:menu:list` | — | `menu:SysMenu (query)` | `AjaxResult` |
| 2 | GET | `/system/menu/{menuId}` | getInfo → `get_info` | `system:menu:query` | — | `menuId:Long (path)` | `AjaxResult` |
| 3 | GET | `/system/menu/treeselect` | treeselect → `treeselect` | — | — | `menu:SysMenu (query)` | `AjaxResult` |
| 4 | GET | `/system/menu/roleMenuTreeselect/{roleId}` | roleMenuTreeselect → `role_menu_treeselect` | — | — | `roleId:Long (path)` | `AjaxResult` |
| 5 | POST | `/system/menu` | add → `add` | `system:menu:add` | 菜单管理 / INSERT | `menu:SysMenu (body)` | `AjaxResult` |
| 6 | PUT | `/system/menu` | edit → `edit` | `system:menu:edit` | 菜单管理 / UPDATE | `menu:SysMenu (body)` | `AjaxResult` |
| 7 | DELETE | `/system/menu/{menuId}` | remove → `remove` | `system:menu:remove` | 菜单管理 / DELETE | `menuId:Long (path)` | `AjaxResult` |

### SysNoticeController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysNoticeController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/notice/list` | list → `list` | — | — | `notice:SysNotice (query)` | `TableDataInfo` |
| 2 | GET | `/system/notice/listquery` | listquery → `listquery` | — | — | `notice:SysNotice (query)` | `TableDataInfo` |
| 3 | GET | `/system/notice/{noticeId}` | getInfo → `get_info` | — | — | `noticeId:Long (path)` | `AjaxResult` |
| 4 | GET | `/system/notice/view/{noticeId}` | getViewInfo → `get_view_info` | — | — | `noticeId:Long (path)` | `AjaxResult` |
| 5 | POST | `/system/notice` | add → `add` | `system:notice:add` | 通知公告 / INSERT | `notice:SysNotice (body)` | `AjaxResult` |
| 6 | PUT | `/system/notice` | edit → `edit` | `system:notice:edit` | 通知公告 / UPDATE | `notice:SysNotice (body)` | `AjaxResult` |
| 7 | DELETE | `/system/notice/{noticeIds}` | remove → `remove` | `system:notice:remove` | 通知公告 / DELETE | `noticeIds:Long[] (path)` | `AjaxResult` |

### SysPostController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysPostController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/post/list` | list → `list` | `system:post:list` | — | `post:SysPost (query)` | `TableDataInfo` |
| 2 | GET | `/system/post/export` | export → `export` | `system:post:export` | 岗位管理 / EXPORT | `post:SysPost (query)` | `AjaxResult` |
| 3 | GET | `/system/post/{postId}` | getInfo → `get_info` | `system:post:query` | — | `postId:Long (path)` | `AjaxResult` |
| 4 | POST | `/system/post` | add → `add` | `system:post:add` | 岗位管理 / INSERT | `post:SysPost (body)` | `AjaxResult` |
| 5 | PUT | `/system/post` | edit → `edit` | `system:post:edit` | 岗位管理 / UPDATE | `post:SysPost (body)` | `AjaxResult` |
| 6 | DELETE | `/system/post/{postIds}` | remove → `remove` | `system:post:remove` | 岗位管理 / DELETE | `postIds:Long[] (path)` | `AjaxResult` |
| 7 | GET | `/system/post/optionselect` | optionselect → `optionselect` | — | — | — | `AjaxResult` |

### SysProfileController（4）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysProfileController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/user/profile` | profile → `profile` | — | — | — | `AjaxResult` |
| 2 | PUT | `/system/user/profile` | updateProfile → `update_profile` | — | 个人信息 / UPDATE | `user:SysUser (body)` | `AjaxResult` |
| 3 | PUT | `/system/user/profile/updatePwd` | updatePwd → `update_pwd` | — | 个人信息 / UPDATE | `oldPassword:String (query)`; `newPassword:String (query)` | `AjaxResult` |
| 4 | POST | `/system/user/profile/avatar` | avatar → `avatar` | — | 用户头像 / UPDATE | `file:MultipartFile (query)` | `AjaxResult` |

### SysRoleController（10）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysRoleController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/role/list` | list → `list` | — | — | `role:SysRole (query)` | `TableDataInfo` |
| 2 | GET | `/system/role/export` | export → `export` | `system:role:export` | 角色管理 / EXPORT | `role:SysRole (query)` | `AjaxResult` |
| 3 | GET | `/system/role/{roleId}` | getInfo → `get_info` | `system:role:query` | — | `roleId:Long (path)` | `AjaxResult` |
| 4 | POST | `/system/role` | add → `add` | `system:role:add` | 角色管理 / INSERT | `role:SysRole (body)` | `AjaxResult` |
| 5 | PUT | `/system/role` | edit → `edit` | `system:role:edit` | 角色管理 / UPDATE | `role:SysRole (body)` | `AjaxResult` |
| 6 | PUT | `/system/role/dataScope` | dataScope → `data_scope` | `system:role:edit` | 角色管理 / UPDATE | `role:SysRole (body)` | `AjaxResult` |
| 7 | PUT | `/system/role/changeStatus` | changeStatus → `change_status` | `system:role:edit` | 角色管理 / UPDATE | `role:SysRole (body)` | `AjaxResult` |
| 8 | DELETE | `/system/role/{roleIds}` | remove → `remove` | `system:role:remove` | 角色管理 / DELETE | `roleIds:Long[] (path)` | `AjaxResult` |
| 9 | GET | `/system/role/optionselect` | optionselect → `optionselect` | `system:role:query` | — | — | `AjaxResult` |
| 10 | GET | `/system/role/selectlist` | selectlist → `selectlist` | — | — | `role:SysRole (query)` | `AjaxResult` |

### SysUpgradeInfoController（7）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUpgradeInfoController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/upgradeInfo/list` | list → `list` | — | — | `sysUpgradeInfo:SysUpgradeInfo (query)` | `TableDataInfo` |
| 2 | GET | `/system/upgradeInfo/newest` | newest → `newest` | — | — | `sysUpgradeInfo:SysUpgradeInfo (query)` | `AjaxResult` |
| 3 | GET | `/system/upgradeInfo/export` | export → `export` | — | 系统升级信息 / EXPORT | `sysUpgradeInfo:SysUpgradeInfo (query)` | `AjaxResult` |
| 4 | GET | `/system/upgradeInfo/{id}` | getInfo → `get_info` | — | — | `id:String (path)` | `AjaxResult` |
| 5 | POST | `/system/upgradeInfo` | add → `add` | — | 系统升级信息 / INSERT | `sysUpgradeInfo:SysUpgradeInfo (body)` | `AjaxResult` |
| 6 | PUT | `/system/upgradeInfo` | edit → `edit` | — | 系统升级信息 / UPDATE | `sysUpgradeInfo:SysUpgradeInfo (body)` | `AjaxResult` |
| 7 | DELETE | `/system/upgradeInfo/{ids}` | remove → `remove` | — | 系统升级信息 / DELETE | `ids:String[] (path)` | `AjaxResult` |

### SysUserController（20）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUserController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/system/user/list` | list → `list` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 2 | GET | `/system/user/listAll` | listAll → `list_all` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 3 | GET | `/system/user/listTenantIdAll` | listTenantIdAll → `list_tenant_id_all` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 4 | GET | `/system/user/listutil` | listutil → `listutil` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 5 | GET | `/system/user/listSameUtil` | listSameUtil → `list_same_util` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 6 | GET | `/system/user/listMy` | listMy → `list_my` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 7 | GET | `/system/user/export` | export → `export` | `system:user:export` | 用户管理 / EXPORT | `user:SysUser (query)` | `AjaxResult` |
| 8 | POST | `/system/user/importData` | importData → `import_data` | `system:user:import` | 用户管理 / IMPORT | `file:MultipartFile (file)`; `updateSupport:boolean (query)` | `AjaxResult` |
| 9 | GET | `/system/user/importTemplate` | importTemplate → `import_template` | — | — | — | `AjaxResult` |
| 10 | GET | `/system/user/` | getInfo → `get_info` | `system:user:query` | — | `userId:Long (path required=false)` | `AjaxResult` |
| 11 | GET | `/system/user/{userId}` | getInfo → `get_info` | `system:user:query` | — | `userId:Long (path required=false)` | `AjaxResult` |
| 12 | POST | `/system/user` | add → `add` | `system:user:add` | 用户管理 / INSERT | `user:SysUser (body)` | `AjaxResult` |
| 13 | PUT | `/system/user` | edit → `edit` | `system:user:edit` | 用户管理 / UPDATE | `user:SysUser (body)` | `AjaxResult` |
| 14 | DELETE | `/system/user/{userIds}` | remove → `remove` | `system:user:remove` | 用户管理 / DELETE | `userIds:Long[] (path)` | `AjaxResult` |
| 15 | PUT | `/system/user/resetPwd` | resetPwd → `reset_pwd` | `system:user:resetPwd` | 用户管理 / UPDATE | `user:SysUser (body)` | `AjaxResult` |
| 16 | PUT | `/system/user/changeStatus` | changeStatus → `change_status` | `system:user:edit` | 用户管理 / UPDATE | `user:SysUser (body)` | `AjaxResult` |
| 17 | PUT | `/system/user/bindUky` | bindUky → `bind_uky` | — | — | `user:SysUser (body)` | `AjaxResult` |
| 18 | GET | `/system/user/getroleUser/{roleCode}` | getroleUser → `getrole_user` | — | — | `roleCode:String (path)` | `AjaxResult` |
| 19 | GET | `/system/user/list/dept` | listByDept → `list_by_dept` | — | — | `user:SysUser (query)` | `TableDataInfo` |
| 20 | GET | `/system/user/currentUser` | selectCurrentUser → `select_current_user` | — | — | — | `AjaxResult` |

## tool

### TestController（5）

`ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java`

| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |
|---:|---|---|---|---|---|---|---|
| 1 | GET | `/test/user/list` | userList → `user_list` | — | — | — | `R<List<UserEntity>>` |
| 2 | GET | `/test/user/{userId}` | getUser → `get_user` | — | — | `userId:Integer (path)` | `R<UserEntity>` |
| 3 | POST | `/test/user/save` | save → `save` | — | — | `user:UserEntity (query)` | `R<String>` |
| 4 | PUT | `/test/user/update` | update → `update` | — | — | `user:UserEntity (body)` | `R<String>` |
| 5 | DELETE | `/test/user/{userId}` | delete → `delete` | — | — | `userId:Integer (path)` | `R<String>` |
