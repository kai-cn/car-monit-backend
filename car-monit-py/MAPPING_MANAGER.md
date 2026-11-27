# MAPPING_MANAGER.md — 车辆监控业务（`com.ruoyi.web.controller.manager`） Java ↔ Python 对照表

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
| Java 控制器 | 21 | `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/` 下全部 `*Controller.java` |
| 端点 | 170 | 方法级注解展开后的条数（`value = {...}` 会展开成多条），与 `scripts/audit_endpoints.py` 的 Java 侧计数同源 |
| Python 控制器模块 | 21 | `app/api/manager/bigscreen/` |
| Domain 对照行 | 34 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Mapper 对照行 | 38 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Service 对照行 | 38 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| 测试 | 83 | 见 §5 |

## 2. 要点

1. `bigscreen/BigScreenController` 单独一层路径（`/manager/bigScreen/**`），Python 侧对应 `app/api/manager/bigscreen/big_screen_controller.py`，目录也照搬。
2. `BussTestController#syncCurrentTrack` 是 `void`：Java 只往响应里写一个空体，Python 返回 `Response(status_code=200)`（`COMPATIBILITY.md` 有登记）。
3. 绝大多数 `export` 是**先写 Excel 再返回**（`AjaxResult` 到不了客户端），`exportAbnormalPassage` 则是 `void` —— 两种都按「写流」处理。
4. `CarExceptRecordController` 的导入端点把文案提成了模块级常量（`TEMPLATE_INVALID_MESSAGE` 等），文案与 Java 一字不差，由 `scripts/audit_messages.py` 双向比对守住。
5. 业务校验**直接返回 `AjaxResult`**（不是抛异常），文案里的错别字照抄：`可疑车俩不存在！`（“车俩”）、`录入区间时间重复！`、`车牌号存在重复，请确定！` —— Python 用同名常量保存，一字不差，由 `scripts/audit_messages.py` 守住。

## 3. 文件级对照

### 3.1 api（21 行）

| Java | Python |
|---|---|
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java` | `app/api/manager/bigscreen/big_screen_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java` | `app/api/manager/bigscreen/big_screen_export_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/BussTestController.java` | `app/api/manager/buss_test_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarAduitFreeController.java` | `app/api/manager/car_aduit_free_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarConfimFreeController.java` | `app/api/manager/car_confim_free_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarExceptRecordController.java` | `app/api/manager/car_except_record_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarFeeRecordController.java` | `app/api/manager/car_fee_record_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarInfoController.java` | `app/api/manager/car_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarQueryLogController.java` | `app/api/manager/car_query_log_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteDetailController.java` | `app/api/manager/car_route_detail_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarRouteInfoController.java` | `app/api/manager/car_route_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSplitRecordController.java` | `app/api/manager/car_split_record_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousBackController.java` | `app/api/manager/car_suspicious_back_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousCheckController.java` | `app/api/manager/car_suspicious_check_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java` | `app/api/manager/car_suspicious_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java` | `app/api/manager/car_track_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningInfoController.java` | `app/api/manager/car_warning_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWarningRuleController.java` | `app/api/manager/car_warning_rule_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWhiteInfoController.java` | `app/api/manager/car_white_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryCarController.java` | `app/api/manager/gantry_car_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryTradeInfoController.java` | `app/api/manager/gantry_trade_info_controller.py` |

### 3.2 domain（34 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/BussTest.java` | `app/manager/domain/buss_test.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarAduitFree.java` | `app/manager/domain/car_aduit_free.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarConfimFree.java` | `app/manager/domain/car_confim_free.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarExceptRecord.java` | `app/manager/domain/car_except_record.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarFeeRecord.java` | `app/manager/domain/car_fee_record.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarInfo.java` | `app/manager/domain/car_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarQueryLog.java` | `app/manager/domain/car_query_log.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteDetail.java` | `app/manager/domain/car_route_detail.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteInfo.java` | `app/manager/domain/car_route_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSplitRecord.java` | `app/manager/domain/car_split_record.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspicious.java` | `app/manager/domain/car_suspicious.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousBack.java` | `app/manager/domain/car_suspicious_back.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousCheck.java` | `app/manager/domain/car_suspicious_check.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarTrackInfo.java` | `app/manager/domain/car_track_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningInfo.java` | `app/manager/domain/car_warning_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningRule.java` | `app/manager/domain/car_warning_rule.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWhiteInfo.java` | `app/manager/domain/car_white_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryCar.java` | `app/manager/domain/gantry_car.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryTradeInfo.java` | `app/manager/domain/gantry_trade_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarAuditVO.java` | `app/manager/domain/vo/bigscreen/car_audit_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarInfoVO.java` | `app/manager/domain/vo/bigscreen/car_info_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarLocationParam.java` | `app/manager/domain/vo/bigscreen/car_location_param.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarLocationVO.java` | `app/manager/domain/vo/bigscreen/car_location_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/CarStatisticsVO.java` | `app/manager/domain/vo/bigscreen/car_statistics_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/IncomeStatisticParam.java` | `app/manager/domain/vo/bigscreen/income_statistic_param.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/incomeStatisticVO.java` | `app/manager/domain/vo/bigscreen/income_statistic_param.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/OrgVO.java` | `app/manager/domain/vo/bigscreen/org_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/SectionVO.java` | `app/manager/domain/vo/bigscreen/section_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/TollGantryFwqVO.java` | `app/manager/domain/vo/bigscreen/toll_gantry_fwq_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/bigscreen/TopTenVO.java` | `app/manager/domain/vo/bigscreen/top_ten_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/CarConfimFreeQueryRo.java` | `app/manager/domain/vo/car_confim_free_query_ro.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCCarStatisticsVO.java` | `app/manager/domain/vo/pc_car_statistics_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCCarStatisticsDetailVO.java` | `app/manager/domain/vo/pc_car_statistics_vo.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/domain/vo/PCIncomeStaticsVO.java` | `app/manager/domain/vo/pc_income_statics_vo.py` |

### 3.3 mapper（38 行）

| Java | Python |
|---|---|
| `com/ruoyi/manager/mapper/BussTestMapper.java` | `app/manager/mapper/buss_test_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/BussTestMapper.xml` | `app/manager/mapper/buss_test_mapper.py` |
| `com/ruoyi/manager/mapper/CarAduitFreeMapper.java` | `app/manager/mapper/car_aduit_free_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarAduitFreeMapper.xml` | `app/manager/mapper/car_aduit_free_mapper.py` |
| `com/ruoyi/manager/mapper/CarConfimFreeMapper.java` | `app/manager/mapper/car_confim_free_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarConfimFreeMapper.xml` | `app/manager/mapper/car_confim_free_mapper.py` |
| `com/ruoyi/manager/mapper/CarExceptRecordMapper.java` | `app/manager/mapper/car_except_record_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml` | `app/manager/mapper/car_except_record_mapper.py` |
| `com/ruoyi/manager/mapper/CarFeeRecordMapper.java` | `app/manager/mapper/car_fee_record_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarFeeRecordMapper.xml` | `app/manager/mapper/car_fee_record_mapper.py` |
| `com/ruoyi/manager/mapper/CarInfoMapper.java` | `app/manager/mapper/car_info_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarInfoMapper.xml` | `app/manager/mapper/car_info_mapper.py` |
| `com/ruoyi/manager/mapper/CarQueryLogMapper.java` | `app/manager/mapper/car_query_log_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarQueryLogMapper.xml` | `app/manager/mapper/car_query_log_mapper.py` |
| `com/ruoyi/manager/mapper/CarRouteDetailMapper.java` | `app/manager/mapper/car_route_detail_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarRouteDetailMapper.xml` | `app/manager/mapper/car_route_detail_mapper.py` |
| `com/ruoyi/manager/mapper/CarRouteInfoMapper.java` | `app/manager/mapper/car_route_info_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarRouteInfoMapper.xml` | `app/manager/mapper/car_route_info_mapper.py` |
| `com/ruoyi/manager/mapper/CarSplitRecordMapper.java` | `app/manager/mapper/car_split_record_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarSplitRecordMapper.xml` | `app/manager/mapper/car_split_record_mapper.py` |
| `com/ruoyi/manager/mapper/CarSuspiciousBackMapper.java` | `app/manager/mapper/car_suspicious_back_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousBackMapper.xml` | `app/manager/mapper/car_suspicious_back_mapper.py` |
| `com/ruoyi/manager/mapper/CarSuspiciousCheckMapper.java` | `app/manager/mapper/car_suspicious_check_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousCheckMapper.xml` | `app/manager/mapper/car_suspicious_check_mapper.py` |
| `com/ruoyi/manager/mapper/CarSuspiciousMapper.java` | `app/manager/mapper/car_suspicious_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousMapper.xml` | `app/manager/mapper/car_suspicious_mapper.py` |
| `com/ruoyi/manager/mapper/CarTrackInfoMapper.java` | `app/manager/mapper/car_track_info_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarTrackInfoMapper.xml` | `app/manager/mapper/car_track_info_mapper.py` |
| `com/ruoyi/manager/mapper/CarWarningInfoMapper.java` | `app/manager/mapper/car_warning_info_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarWarningInfoMapper.xml` | `app/manager/mapper/car_warning_info_mapper.py` |
| `com/ruoyi/manager/mapper/CarWarningRuleMapper.java` | `app/manager/mapper/car_warning_rule_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarWarningRuleMapper.xml` | `app/manager/mapper/car_warning_rule_mapper.py` |
| `com/ruoyi/manager/mapper/CarWhiteInfoMapper.java` | `app/manager/mapper/car_white_info_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/CarWhiteInfoMapper.xml` | `app/manager/mapper/car_white_info_mapper.py` |
| `com/ruoyi/manager/mapper/GantryCarMapper.java` | `app/manager/mapper/gantry_car_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/GantryCarMapper.xml` | `app/manager/mapper/gantry_car_mapper.py` |
| `com/ruoyi/manager/mapper/GantryTradeInfoMapper.java` | `app/manager/mapper/gantry_trade_info_mapper.py` |
| `ruoyi-system/src/main/resources/mapper/manager/GantryTradeInfoMapper.xml` | `app/manager/mapper/gantry_trade_info_mapper.py` |

### 3.4 service（38 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/IBussTestService.java` | `app/manager/service/buss_test_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/BussTestServiceImpl.java` | `app/manager/service/buss_test_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarAduitFreeService.java` | `app/manager/service/car_aduit_free_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarAduitFreeServiceImpl.java` | `app/manager/service/car_aduit_free_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarConfimFreeService.java` | `app/manager/service/car_confim_free_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarConfimFreeServiceImpl.java` | `app/manager/service/car_confim_free_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarExceptRecordService.java` | `app/manager/service/car_except_record_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarExceptRecordServiceImpl.java` | `app/manager/service/car_except_record_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarFeeRecordService.java` | `app/manager/service/car_fee_record_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarFeeRecordServiceImpl.java` | `app/manager/service/car_fee_record_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarInfoService.java` | `app/manager/service/car_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java` | `app/manager/service/car_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarQueryLogService.java` | `app/manager/service/car_query_log_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarQueryLogServiceImpl.java` | `app/manager/service/car_query_log_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarRouteDetailService.java` | `app/manager/service/car_route_detail_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarRouteDetailServiceImpl.java` | `app/manager/service/car_route_detail_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarRouteInfoService.java` | `app/manager/service/car_route_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarRouteInfoServiceImpl.java` | `app/manager/service/car_route_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSplitRecordService.java` | `app/manager/service/car_split_record_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSplitRecordServiceImpl.java` | `app/manager/service/car_split_record_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousBackService.java` | `app/manager/service/car_suspicious_back_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousBackServiceImpl.java` | `app/manager/service/car_suspicious_back_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousCheckService.java` | `app/manager/service/car_suspicious_check_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousCheckServiceImpl.java` | `app/manager/service/car_suspicious_check_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarSuspiciousService.java` | `app/manager/service/car_suspicious_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java` | `app/manager/service/car_suspicious_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarTrackInfoService.java` | `app/manager/service/car_track_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarTrackInfoServiceImpl.java` | `app/manager/service/car_track_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWarningInfoService.java` | `app/manager/service/car_warning_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningInfoServiceImpl.java` | `app/manager/service/car_warning_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWarningRuleService.java` | `app/manager/service/car_warning_rule_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningRuleServiceImpl.java` | `app/manager/service/car_warning_rule_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWhiteInfoService.java` | `app/manager/service/car_white_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWhiteInfoServiceImpl.java` | `app/manager/service/car_white_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/IGantryCarService.java` | `app/manager/service/gantry_car_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/GantryCarServiceImpl.java` | `app/manager/service/gantry_car_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/IGantryTradeInfoService.java` | `app/manager/service/gantry_trade_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/GantryTradeInfoServiceImpl.java` | `app/manager/service/gantry_trade_info_service.py` |

### 3.5 framework（2 行）

| Java | Python |
|---|---|
| `ruoyi-framework/src/main/java/com/ruoyi/framework/manager/AsyncManager.java` | `app/framework/manager/async_manager.py` |
| `ruoyi-framework/src/main/java/com/ruoyi/framework/manager/factory/AsyncFactory.java` | `app/framework/manager/factory/async_factory.py` |

## 4. 控制器端点（170 个）

### 4.1 `BigScreenController`（12 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `getCarAudit` | `get_car_audit` | GET `/manager/bigScreen/carAudit` | `—` | — |
| `getCarLocation` | `get_car_location` | GET `/manager/bigScreen/carLocation` | `—` | — |
| `getCarStatistics` | `get_car_statistics` | GET `/manager/bigScreen/carStatistics` | `—` | — |
| `carVoList` | `car_vo_list` | GET `/manager/bigScreen/carVoList` | `—` | — |
| `getCarWarning` | `get_car_warning` | GET `/manager/bigScreen/carWarning` | `—` | — |
| `list` | `list` | GET `/manager/bigScreen/exceptRecordList` | `—` | — |
| `getExceptionCar` | `get_exception_car` | GET `/manager/bigScreen/exceptionCar` | `—` | — |
| `incomeStatistic` | `income_statistic` | GET `/manager/bigScreen/incomeStatistic` | `—` | — |
| `getOrgList` | `get_org_list` | GET `/manager/bigScreen/orgList` | `—` | — |
| `getSectionList` | `get_section_list` | GET `/manager/bigScreen/sectionList` | `—` | — |
| `getTollList` | `get_toll_list` | GET `/manager/bigScreen/tollGantryFwqList` | `—` | — |
| `topTen` | `top_ten` | GET `/manager/bigScreen/topTen` | `—` | — |

### 4.2 `BigScreenExportController`（10 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `approvals` | `approvals` | GET `/manager/bigScreen/export/approvals` | `manager:bigscreen:exportApprove` | — |
| `download` | `download` | GET `/manager/bigScreen/export/download/{taskId}` | `—` | — |
| `status` | `status` | GET `/manager/bigScreen/export/status/{taskId}` | `—` | — |
| `approve` | `approve` | POST `/manager/bigScreen/export/approvals/{requestId}/approve` | `manager:bigscreen:exportApprove` | — |
| `reject` | `reject` | POST `/manager/bigScreen/export/approvals/{requestId}/reject` | `manager:bigscreen:exportApprove` | — |
| `display` | `display` | POST `/manager/bigScreen/export/display` | `manager:bigscreen:export` | — |
| `full` | `full` | POST `/manager/bigScreen/export/full` | `manager:bigscreen:export` | — |
| `downloadUrl` | `download_url` | POST `/manager/bigScreen/export/{taskId}/download-url` | `—` | — |
| `resume` | `resume` | POST `/manager/bigScreen/export/{taskId}/resume` | `manager:bigscreen:export` | — |
| `retry` | `retry` | POST `/manager/bigScreen/export/{taskId}/retry` | `manager:bigscreen:export` | — |

### 4.3 `BussTestController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/busstest/{ids}` | `manager:busstest:remove` | 业务测试 / DELETE |
| `export` | `export` | GET `/manager/busstest/export` | `manager:busstest:export` | 业务测试 / EXPORT |
| `list` | `list_buss_tests` | GET `/manager/busstest/list` | `manager:busstest:list` | — |
| `getInfo` | `get_info` | GET `/manager/busstest/{id}` | `—` | — |
| `add` | `add` | POST `/manager/busstest` | `manager:busstest:add` | 业务测试 / INSERT |
| `syncCurrentTrack` | `sync_current_track` | POST `/manager/busstest/syncCurrentTrack` | `manager:busstest:syncTest` | — |
| `edit` | `edit` | PUT `/manager/busstest` | `manager:busstest:edit` | 业务测试 / UPDATE |

### 4.4 `CarAduitFreeController`（10 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/aduitfree/{ids}` | `—` | 补缴处理 / DELETE |
| `export` | `export` | GET `/manager/aduitfree/export` | `—` | 补缴处理 / EXPORT |
| `exportIncomeDetailList` | `export_income_detail_list` | GET `/manager/aduitfree/exportIncomeDetailList` | `—` | — |
| `exportIncomeStatics` | `export_income_statics` | GET `/manager/aduitfree/exportIncomeStatics` | `—` | — |
| `incomeDetailList` | `income_detail_list` | GET `/manager/aduitfree/incomeDetailList` | `—` | — |
| `incomeStatics` | `income_statics` | GET `/manager/aduitfree/incomeStatics` | `—` | — |
| `list` | `list_aduit_frees` | GET `/manager/aduitfree/list` | `—` | — |
| `getInfo` | `get_info` | GET `/manager/aduitfree/{id}` | `—` | — |
| `add` | `add` | POST `/manager/aduitfree` | `—` | 补缴处理 / INSERT |
| `edit` | `edit` | PUT `/manager/aduitfree` | `—` | 补缴处理 / UPDATE |

### 4.5 `CarConfimFreeController`（13 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/confimfree/{ids}` | `—` | 确认补缴 / DELETE |
| `getCarStatics` | `get_car_statics` | GET `/manager/confimfree/carStatics` | `—` | — |
| `concernedList` | `concerned_list` | GET `/manager/confimfree/concernedList` | `—` | — |
| `getExceptIds` | `get_except_ids` | GET `/manager/confimfree/except/{exceptIds}` | `—` | — |
| `export` | `export` | GET `/manager/confimfree/export` | `—` | 确认补缴 / EXPORT |
| `exportCarStatics` | `export_car_statics` | GET `/manager/confimfree/exportCarStatics` | `—` | — |
| `exportConcernedList` | `export_concerned_list` | GET `/manager/confimfree/exportConcernedList` | `—` | — |
| `list` | `list_confim_frees` | GET `/manager/confimfree/list` | `—` | — |
| `listCarNo` | `list_car_no` | GET `/manager/confimfree/listCarNo` | `—` | — |
| `listCount` | `list_count` | GET `/manager/confimfree/listCount` | `—` | — |
| `getInfo` | `get_info` | GET `/manager/confimfree/{id}` | `—` | — |
| `add` | `add` | POST `/manager/confimfree` | `—` | 确认补缴 / INSERT |
| `edit` | `edit` | PUT `/manager/confimfree` | `—` | 确认补缴 / UPDATE |

### 4.6 `CarExceptRecordController`（13 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/exceptrecord/{ids}` | `—` | 异常车辆流水 / DELETE |
| `exceptRecordCount` | `except_record_count` | GET `/manager/exceptrecord/exceptRecordCount` | `—` | — |
| `export` | `export` | GET `/manager/exceptrecord/export` | `—` | 异常车辆流水 / EXPORT |
| `exportOrgId` | `export_org_id` | GET `/manager/exceptrecord/exportOrgId` | `—` | 异常车辆流水 / EXPORT |
| `getConfirmId` | `get_confirm_id` | GET `/manager/exceptrecord/getConfirmId/{id}` | `—` | — |
| `list` | `list_car_except_records` | GET `/manager/exceptrecord/list` | `—` | — |
| `listCarNo` | `list_car_except_records_by_car_no` | GET `/manager/exceptrecord/listCarNo` | `—` | — |
| `listCarOrgId` | `list_car_org_id` | GET `/manager/exceptrecord/listCarOrgId` | `—` | — |
| `listExceptId` | `list_except_id` | GET `/manager/exceptrecord/listExceptId` | `—` | — |
| `getInfo` | `get_info` | GET `/manager/exceptrecord/{id}` | `—` | — |
| `add` | `add` | POST `/manager/exceptrecord` | `—` | 异常车辆流水 / INSERT |
| `doImport` | `do_import` | POST `/manager/exceptrecord/import` | `—` | 新增流水导入 / IMPORT |
| `edit` | `edit` | PUT `/manager/exceptrecord` | `—` | 异常车辆流水 / UPDATE |

### 4.7 `CarFeeRecordController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/feerecord/{ids}` | `manager:feerecord:remove` | 收费流水 / DELETE |
| `export` | `export` | GET `/manager/feerecord/export` | `manager:feerecord:export` | 收费流水 / EXPORT |
| `list` | `list_fee_records` | GET `/manager/feerecord/list` | `manager:feerecord:list` | — |
| `getInfo` | `get_info` | GET `/manager/feerecord/{id}` | `—` | — |
| `add` | `add` | POST `/manager/feerecord` | `manager:feerecord:add` | 收费流水 / INSERT |
| `edit` | `edit` | PUT `/manager/feerecord` | `manager:feerecord:edit` | 收费流水 / UPDATE |

### 4.8 `CarInfoController`（8 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/carinfo/{ids}` | `manager:carinfo:remove` | 车辆信息 / DELETE |
| `export` | `export` | GET `/manager/carinfo/export` | `manager:carinfo:export` | 车辆信息 / EXPORT |
| `list` | `list_car_infos` | GET `/manager/carinfo/list` | `manager:carinfo:list` | — |
| `listAll` | `list_all_car_infos` | GET `/manager/carinfo/listAll` | `—` | — |
| `getInfo` | `get_info` | GET `/manager/carinfo/{id}` | `—` | — |
| `add` | `add` | POST `/manager/carinfo` | `—` | 车辆信息 / INSERT |
| `doImport` | `do_import` | POST `/manager/carinfo/import` | `—` | 车辆信息 / IMPORT |
| `edit` | `edit` | PUT `/manager/carinfo` | `manager:carinfo:edit` | 车辆信息 / UPDATE |

### 4.9 `CarQueryLogController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/querylog/{ids}` | `manager:querylog:remove` | 查询日志 / DELETE |
| `export` | `export` | GET `/manager/querylog/export` | `manager:querylog:export` | 日志信息 / EXPORT |
| `list` | `list_query_logs` | GET `/manager/querylog/list` | `manager:querylog:list` | — |
| `getInfo` | `get_info` | GET `/manager/querylog/{id}` | `—` | — |
| `add` | `add` | POST `/manager/querylog` | `manager:querylog:add` | 查询日志 / INSERT |
| `edit` | `edit` | PUT `/manager/querylog` | `manager:querylog:edit` | 查询日志 / UPDATE |

### 4.10 `CarRouteDetailController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/routedetail/{ids}` | `manager:routedetail:remove` | 常用路线明细 / DELETE |
| `export` | `export` | GET `/manager/routedetail/export` | `manager:routedetail:export` | 常用路线明细 / EXPORT |
| `list` | `list_route_details` | GET `/manager/routedetail/list` | `manager:routedetail:list` | — |
| `getInfo` | `get_info` | GET `/manager/routedetail/{id}` | `—` | — |
| `add` | `add` | POST `/manager/routedetail` | `manager:routedetail:add` | 常用路线明细 / INSERT |
| `edit` | `edit` | PUT `/manager/routedetail` | `manager:routedetail:edit` | 常用路线明细 / UPDATE |

### 4.11 `CarRouteInfoController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/routeinfo/{ids}` | `manager:routeinfo:remove` | 常用路线 / DELETE |
| `export` | `export` | GET `/manager/routeinfo/export` | `manager:routeinfo:export` | 常用路线 / EXPORT |
| `list` | `list_route_infos` | GET `/manager/routeinfo/list` | `manager:routeinfo:list` | — |
| `getInfo` | `get_info` | GET `/manager/routeinfo/{id}` | `—` | — |
| `add` | `add` | POST `/manager/routeinfo` | `manager:routeinfo:add` | 常用路线 / INSERT |
| `edit` | `edit` | PUT `/manager/routeinfo` | `manager:routeinfo:edit` | 常用路线 / UPDATE |

### 4.12 `CarSplitRecordController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/splitrecord/{ids}` | `manager:splitrecord:remove` | 拆分流水 / DELETE |
| `export` | `export` | GET `/manager/splitrecord/export` | `manager:splitrecord:export` | 拆分流水 / EXPORT |
| `list` | `list_split_records` | GET `/manager/splitrecord/list` | `manager:splitrecord:list` | — |
| `getInfo` | `get_info` | GET `/manager/splitrecord/{id}` | `—` | — |
| `add` | `add` | POST `/manager/splitrecord` | `manager:splitrecord:add` | 拆分流水 / INSERT |
| `edit` | `edit` | PUT `/manager/splitrecord` | `manager:splitrecord:edit` | 拆分流水 / UPDATE |

### 4.13 `CarSuspiciousBackController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/carsuspiciousback/{ids}` | `manager:carsuspiciousback:remove` | 可疑车辆备份 / DELETE |
| `export` | `export` | GET `/manager/carsuspiciousback/export` | `manager:carsuspiciousback:export` | 可疑车辆备份 / EXPORT |
| `list` | `list_suspicious_backs` | GET `/manager/carsuspiciousback/list` | `manager:carsuspiciousback:list` | — |
| `getInfo` | `get_info` | GET `/manager/carsuspiciousback/{id}` | `—` | — |
| `add` | `add` | POST `/manager/carsuspiciousback` | `manager:carsuspiciousback:add` | 可疑车辆备份 / INSERT |
| `edit` | `edit` | PUT `/manager/carsuspiciousback` | `manager:carsuspiciousback:edit` | 可疑车辆备份 / UPDATE |

### 4.14 `CarSuspiciousCheckController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/suspiciouscheck/{ids}` | `manager:suspiciouscheck:remove` | 可疑车辆人工核实 / DELETE |
| `export` | `export` | GET `/manager/suspiciouscheck/export` | `manager:suspiciouscheck:export` | 可疑车辆人工核实 / EXPORT |
| `list` | `list_suspicious_checks` | GET `/manager/suspiciouscheck/list` | `manager:suspiciouscheck:list` | — |
| `getInfo` | `get_info` | GET `/manager/suspiciouscheck/{id}` | `—` | — |
| `add` | `add` | POST `/manager/suspiciouscheck` | `manager:suspiciouscheck:add` | 可疑车辆人工核实 / INSERT |
| `edit` | `edit` | PUT `/manager/suspiciouscheck` | `manager:suspiciouscheck:edit` | 可疑车辆人工核实 / UPDATE |

### 4.15 `CarSuspiciousController`（15 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/suspicious/{ids}` | `manager:suspicious:remove` | 可疑车辆 / DELETE |
| `export` | `export` | GET `/manager/suspicious/export` | `manager:suspicious:export` | 可疑车辆 / EXPORT |
| `exportAbnormalPassage` | `export_abnormal_passage` | GET `/manager/suspicious/exportAbnormalPassage` | `—` | — |
| `exportHistory` | `export_history` | GET `/manager/suspicious/exportHistory` | `manager:suspicious:export` | 可疑车辆 / EXPORT |
| `gethistoryInfo` | `get_history_info` | GET `/manager/suspicious/history/{id}` | `—` | — |
| `list` | `list_car_suspicious` | GET `/manager/suspicious/list` | `manager:suspicious:list` | — |
| `listAll` | `list_all_car_suspicious` | GET `/manager/suspicious/listAll` | `—` | — |
| `listCarNo` | `list_car_suspicious_by_car_no` | GET `/manager/suspicious/listCarNo` | `—` | — |
| `listFileCarNo` | `list_file_car_no` | GET `/manager/suspicious/listFileCarNo` | `—` | — |
| `listHistory` | `list_history` | GET `/manager/suspicious/listHistory` | `manager:suspicious:list` | — |
| `getInfo` | `get_info` | GET `/manager/suspicious/{id}` | `—` | — |
| `add` | `add` | POST `/manager/suspicious` | `manager:suspicious:add` | 可疑车辆 / INSERT |
| `syncSuspiciousCarTask` | `sync_suspicious_car_task` | POST `/manager/suspicious/syncSuspiciousCarTask` | `—` | — |
| `edit` | `edit` | PUT `/manager/suspicious` | `manager:suspicious:edit` | 可疑车辆 / UPDATE |
| `check` | `check` | PUT `/manager/suspicious/check` | `—` | 可疑车辆 / UPDATE |

### 4.16 `CarTrackInfoController`（10 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/cartrackinfo/{ids}` | `manager:cartrackinfo:remove` | 车辆行驶轨迹 / DELETE |
| `carSnapShot` | `car_snap_shot` | GET `/manager/cartrackinfo/carSnapShot` | `—` | — |
| `export` | `export` | GET `/manager/cartrackinfo/export` | `manager:cartrackinfo:export` | 车辆行驶轨迹 / EXPORT |
| `list` | `list_tracks` | GET `/manager/cartrackinfo/list` | `manager:cartrackinfo:list` | — |
| `listByCarByTime` | `list_by_car_by_time` | GET `/manager/cartrackinfo/listByCarByTime` | `—` | — |
| `listByCarId` | `list_by_car_id` | GET `/manager/cartrackinfo/listByCarId` | `—` | — |
| `getInfo` | `get_info` | GET `/manager/cartrackinfo/{id}` | `—` | — |
| `add` | `add` | POST `/manager/cartrackinfo` | `manager:cartrackinfo:add` | 车辆行驶轨迹 / INSERT |
| `edit` | `edit` | PUT `/manager/cartrackinfo` | `manager:cartrackinfo:edit` | 车辆行驶轨迹 / UPDATE |
| `changeTrailInfo` | `change_trail_info` | PUT `/manager/cartrackinfo/changeTrailInfo` | `—` | 车辆行驶轨迹 / UPDATE |

### 4.17 `CarWarningInfoController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/carwarning/{ids}` | `manager:carwarning:remove` | 预警车辆 / DELETE |
| `export` | `export` | GET `/manager/carwarning/export` | `manager:carwarning:export` | 预警车辆 / EXPORT |
| `list` | `list_warning_infos` | GET `/manager/carwarning/list` | `—` | — |
| `getInfo` | `get_info` | GET `/manager/carwarning/{id}` | `—` | — |
| `add` | `add` | POST `/manager/carwarning` | `manager:carwarning:add` | 预警车辆 / INSERT |
| `edit` | `edit` | PUT `/manager/carwarning` | `manager:carwarning:edit` | 预警车辆 / UPDATE |

### 4.18 `CarWarningRuleController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/warningrule/{ids}` | `manager:warningrule:remove` | 预警规则 / DELETE |
| `export` | `export` | GET `/manager/warningrule/export` | `manager:warningrule:export` | 预警规则 / EXPORT |
| `list` | `list_warning_rules` | GET `/manager/warningrule/list` | `manager:warningrule:list` | — |
| `getInfo` | `get_info` | GET `/manager/warningrule/{id}` | `—` | — |
| `add` | `add` | POST `/manager/warningrule` | `manager:warningrule:add` | 预警规则 / INSERT |
| `edit` | `edit` | PUT `/manager/warningrule` | `manager:warningrule:edit` | 预警规则 / UPDATE |

### 4.19 `CarWhiteInfoController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/whiteinfo/{ids}` | `manager:whiteinfo:remove` | 车俩白名单 / DELETE |
| `export` | `export` | GET `/manager/whiteinfo/export` | `manager:whiteinfo:export` | 车俩白名单 / EXPORT |
| `list` | `list_white_infos` | GET `/manager/whiteinfo/list` | `manager:whiteinfo:list` | — |
| `getInfo` | `get_info` | GET `/manager/whiteinfo/{id}` | `—` | — |
| `add` | `add` | POST `/manager/whiteinfo` | `manager:whiteinfo:add` | 车俩白名单 / INSERT |
| `edit` | `edit` | PUT `/manager/whiteinfo` | `manager:whiteinfo:edit` | 车俩白名单 / UPDATE |

### 4.20 `GantryCarController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/gantrycar/{ids}` | `manager:gantrycar:remove` | 门架拍识查询 / DELETE |
| `export` | `export` | GET `/manager/gantrycar/export` | `manager:gantrycar:export` | 门架拍识查询 / EXPORT |
| `list` | `list_gantry_cars` | GET `/manager/gantrycar/list` | `manager:gantrycar:list` | — |
| `getInfo` | `get_info` | GET `/manager/gantrycar/{id}` | `—` | — |
| `add` | `add` | POST `/manager/gantrycar` | `manager:gantrycar:add` | 门架拍识查询 / INSERT |
| `edit` | `edit` | PUT `/manager/gantrycar` | `manager:gantrycar:edit` | 门架拍识查询 / UPDATE |

### 4.21 `GantryTradeInfoController`（6 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `remove` | DELETE `/manager/gantrytrade/{ids}` | `manager:gantrytrade:remove` | 门架交易查询 / DELETE |
| `export` | `export` | GET `/manager/gantrytrade/export` | `manager:gantrytrade:export` | 门架交易查询 / EXPORT |
| `list` | `list_gantry_trade_infos` | GET `/manager/gantrytrade/list` | `manager:gantrytrade:list` | — |
| `getInfo` | `get_info` | GET `/manager/gantrytrade/{id}` | `—` | — |
| `add` | `add` | POST `/manager/gantrytrade` | `manager:gantrytrade:add` | 门架交易查询 / INSERT |
| `edit` | `edit` | PUT `/manager/gantrytrade` | `manager:gantrytrade:edit` | 门架交易查询 / UPDATE |

## 5. 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_manager_controllers.py` | **53** | 19 个业务控制器：路由、权限点、`@Log`、CRUD 的 `code/msg` 契约 |
| Controller | `tests/test_big_screen_controller.py` | **30** | 大屏接口：参数绑定、聚合结构、惰性 import 的回归护栏 |
| 合计 | — | **83** | — |

用例数取自 `pytest --collect-only`（含参数化展开）。全量套件当前 **3646** 条（3563 单测 + 83 条真实 MySQL/Redis 联调），见 `MIGRATION_PROGRESS.md` §6.10。
