# 03 - Java ↔ Rust 接口逐个校验（GET 全量）

> 校验时间：2026-10-31
> 环境：Java 3.8.7（端口 9988，jar 同库同 Redis） / Rust（端口 9990，`APP_SERVER__PORT=9990`
> 且关闭调度器），MySQL `127.0.0.1:3307/carmonitdb`，Redis `127.0.0.1:6379`，账号 `admin`。
> 基线：`docs/01-baseline/02-endpoints.md`（501 条，其中 GET 297 条）。

## 1. 方法

1. 解析基线中的 297 个 GET 端点（路径/权限/参数）。
2. 两端分别用验证码登录（验证码答案从 Redis `captcha_codes:{uuid}` 读取）。
3. 路径变量按业务表取真实主键（`id`/`bigId`/`fwqbm`/`tableName` 等），分页统一
   `pageNum=1&pageSize=10`；导出/下载类超时放宽到 240s。
4. 归一化后逐端点对比：HTTP 状态、`code`、`msg`（UUID 文件名归一）、
   `total`、`rows` 长度、首行及嵌套对象键集合/值/类型；二进制只比较状态、Content-Type 类别与文件头。
5. 已知的**动态数据**（登录日志、操作日志、在线用户、查询日志、Redis INFO）只比较结构，
   不比较值。

## 2. 结果总览

| 结论 | 数量 | 说明 |
|---|---:|---|
| OK | 160 | 结构、值、类型均一致 |
| WARN | 109 | 仅字段顺序（Java Jackson 继承字段顺序）或错误文案（MyBatis vs sqlx）、导出文件名 UUID 不同 |
| FAIL | 13 | 聚合/详情/生成器类端点的实质差异，见 §4 |
| KNOWN | 12 | 依赖不可用上游或 Java 自身故障，见 §5 |
| SKIP | 3 | `geometry/syncAllGeometry(1)`、`tool/gen/synchDb`（有远端写入副作用，避免污染） |

> WARN 中的 `ORDER-DIFF` 均为键顺序差异（如 Java 先输出 `BaseEntity` 的
> `createBy/createTime/updateBy/updateTime/remark`，Rust 按查询列顺序输出），
> 前端按字段名取值不受影响；`MSG-DIFF` 为 SQL 异常文本（MyBatis 与 SQLx 文案不同），
> `code` 一致。

## 3. 本轮修复的关键问题

### 3.1 Redis 共存（Java 读取 Rust 写入的值）
- `login_tokens:*`、`section_list`、`sys_dict:*` 写回时补 FastJson2 `@type`；
  Rust 读取 Java 值支持 `Set[...]`/`List[...]` 容器字面量与 `123L` 长整型后缀。
- 清理了历史测试遗留的旧格式 token；修复后 Java 的 `/monitor/online/list`、
  `/base/gantry/list`、`/base/toll/list`、`/manager/bigScreen/carLocation`
  等依赖 Redis 的接口恢复正常。

### 3.2 响应契约
- `AjaxResult.success(Object)` 在 data 为 null 时**不输出 data 键**（与 Java 构造器一致）。
- 实体字段类型/格式按 Java 实体声明对齐：
  - `LocalDate` → `yyyy-MM-dd`；`java.util.Date`（Jackson 默认）→ ISO+08:00；
  - `orderNum/isFrame/isCache/postSort/roleSort` 为 String；
  - `Integer` 字段（桩号、里程、parentId、loadRate 等）按整数输出。
- SQL 补齐 Java 实体存在但 Mapper 未查询的字段（输出 null），并移除 Rust 多查的列；
  `BOOLEAN`（tinyint(1)）与无符号整数的解码修复。
- 导出行为区分 Java 两种实现：
  - `ExcelUtil.exportExcel`：写文件到 `profile/download`，响应 `{msg: 文件名, code:200}`；
  - 模板导出（EasyPOI）：直接写 HTTP 二进制流（manager 大部分导出、门架/收费流水导出）。
- 其他：`/system/config/configKey/{key}` 走 `success(String msg)` 语义（值在 msg）；
  `/monitor/job/list` 计算 `nextValidTime`；`/monitor/jobLog/{id}` 复刻 Java
  路径变量绑定失败的 500；`/tool/gen/column` 使用 `TableDataInfo(code=0,msg=null)`。

## 4. 仍存在的 13 处实质差异（建议后续补齐）

| 端点 | 差异 | 原因/后续 |
|---|---|---|
| `/tool/gen/list`、`/tool/gen/all/list` | 缺 `columns`、`pkColumn`、`subTable`、`dictionaryInfo*`、树字段 | GenTable 聚合（表 + 列 + 字典）未建模，需按 `GenTableServiceImpl` 补 |
| `/tool/gen/{talbleId}` | `tables/rows/info` 顺序、tables 字段不全 | 同上，返回体 `{info, rows, tables}` 需完整 GenTable 实体 |
| `/tool/gen/db/list` | 缺 information_schema 生成字段（createTime/tableId/tableComment 等） | 需按 `GenTableMapper.selectDbTableList` 补别名 |
| `/manager/confimfree/{id}` | `carAduitFreeList`、`carExceptRecordList`、`difAmount` 等未回填 | Service 层聚合未迁移（按车号查补缴/异常流水并汇总） |
| `/manager/confimfree/concernedList` | 返回体缺少 CarConfimFree 实体空字段与聚合列 | `selectConcernedList` 的完整 VO 未对齐 |
| `/manager/confimfree/carStatics` | 2 行 vs 8 行，缺 `escapedTypeXXNum/Amount` | 统计 SQL 需按「单位 + 逃费类型」交叉汇总 |
| `/manager/confimfree/except/{exceptIds}` | Java 对已追缴单返回 500「车辆补缴单已追缴」 | 未实现补缴状态校验 |
| `/manager/aduitfree/incomeStatics` | 10 行 vs 21 行 | 收入统计需含零值单位/补缴合并口径 |
| `/manager/aduitfree/incomeDetailList` | 0 行 vs 167 行 | 明细 SQL 的默认时间范围/`union all` 口径不同 |
| `/manager/suspicious/{id}` | `trackJosn/checkList` 等由 Service 计算 | `selectCarSuspiciousById` 的轨迹/核查明细回填未迁移 |
| `/manager/suspicious/listHistory` | 首行数据源不同（UUID vs 数值 id） | `listHistory` 实际查询表/排序需与 Java 再核对 |
| `/manager/cartrackinfo/listByCarByTime` | `trailList[*]` 少数派生键缺失 | TrailBo 全字段（含 `borderWeighingCaptureBO`）补齐后再核对 |

## 5. 环境受限 / KNOWN（12）

- 远端代理（`vehicleMonitor.baseUrl` 未启动或返回不可预期）：`/base/feeGantry/list`、
  `/base/feeGantry/{bigId}`、`/base/feerecords/{bigId}`、`/base/snapshotflow/{bigId}`、
  `/base/snapshotflow/earliest-time`、`/base/feestationexit/list`、
  `/base/feestationexit/{bigId}`、`/base/geometry/getHenDa`。
- Java 自身故障：`/monitor/server`（`jna Memory.close` NoSuchMethodError）、
  `/base/cdc/config`（Java 返回非法 JSON）。
- 表缺失（两端均 500，仅文案不同）：`/system/upgradeInfo/*`。
- 模板引擎缺失（Rust 端明确返回 500）：`/tool/gen/preview`、`/tool/gen/download`、
  `/tool/gen/genCode`、`/tool/gen/batchGenCode`。

## 6. 校验脚本

对比脚本位于本机临时目录 `%TEMP%\jr-compare`（`parse.py` 生成端点清单，`client.py`
负责 Redis 验证码 + 登录 + HTTP，`compare.py` 执行全量比对并输出 `report.json`）。
如需纳入 CI，可将脚本迁到 `tools/endpoint-parity/` 并参数化两端 baseURL。
