# car-monit-backend-new Java↔Python 双端一致性校验（2026-11-05）

范围与顺序按用户要求：**① backend 调 api 服务的接口 → ② backend 其它业务接口 → ③ 框架接口**，
另加导出层（xlsx/zip 单元格级）与 Redis 分库/共库断言。

## 1. 结论摘要

| 档 | 比对单元 | 一致 | 有差异 | 差异归类 |
|---|---|---|---|---|
| 1 api（经 `vehicleMonitor.baseUrl` 转发） | 20 | 14 | 6（全部复验可重现） | 上游 5xx 不传播 ×3、Java 侧日期反序列化 500 ×1、hutool null 成员 ×2 |
| 2 business | 134 | 127 | 7 | Redis 分库所致 ×2、Java 侧缺陷 ×2、同为 500 的错误文本 ×2、数值/浮点打印 ×1 |
| 3 framework | 82 | 66（含 3 条只可比状态码、3 条只可比形状） | 16 | `params.@type` ×4、`configKey` 落位 ×1、`columns` 子集合 ×3、代码生成 ×3、缺表文本 ×4、Java `/monitor/server` 500 ×1 |
| 导出层（附件流 + ExcelUtil 落盘） | 58 | 35 | 23 | 数值/时间格式 ×15、`Date.toString()` ×2、超长单元格 ×1、堆栈换行 ×1、增长表写入序 ×2、分库 ×1、缺表文本 ×1 |
| api 双端直连（归因用） | 16 | 14 | 2 | 车颜色翻译、空响应体 vs `null` |
| Redis 分库 / MySQL 共库断言 | 17 | 17 | 0 | — |

GET 面合计 236 条 + 导出面 58 条 = **294 个比对单元，一致 242 条（82.3%）**；
差异中 **Python 侧待修 12 条（4 类根因）**，其余为 Java 侧既有缺陷、Redis 分库的必然代价、运行态文本差异。
本轮只校验、未改任何业务代码。
**§12 是随后按 §10 前四项改完 Python 端的复验：294 单元一致数 242 → 258（87.8%）。**

## 2. 接线

| 进程 | 端口 | Redis | 数据源 | 说明 |
|---|---|---|---|---|
| car-monit-api Java（`pro-business-api-1.0.jar`） | 9902 | db0 | openGauss `192.168.56.10:5432/RuoYi` | **已存在进程，按要求未重启**（它是 `-Xmx2048m`，非本轮起的） |
| car-monit-api Python（`car-monit-api-python/run.py`） | 9901 | 无真实连接（进程内 `RedisCache` shim） | 读同一份 `pro-business-api/src/main/resources/application.yml` | 24 controller / 85 路由注册成功 |
| backend Java（`ruoyi-admin.jar`） | 9788 | db0 | MySQL `127.0.0.1:3307/carmonitdb` | `-Xmx500m`，`--vehicleMonitor.baseUrl=http://127.0.0.1:9902` |
| backend Python（`car-monit-py/run.py`） | 9789 | **db7** | 同一 MySQL | `SERVER__PORT=9789 SPRING__REDIS__DATABASE=7 VEHICLE_MONITOR__BASE_URL=http://127.0.0.1:9901` |
| backend Python 对照（钉 api） | 9790 | db8 | 同一 MySQL | `VEHICLE_MONITOR__BASE_URL=http://127.0.0.1:9902`，用于归因 |
| backend Python 对照（钉 db） | 9791 | db0 | 同一 MySQL | 与 Java 端共用缓存键空间，用于证明"分库导致的差异" |

要点：

- **9984–9989 全部被其它会话占用**（9988 是别的会话起的 `ruoyi-admin.jar -Xmx2g`、9989 是 Go backend、
  9985/9987 是上一轮 Java 参照、9984/9986 是 Go 参照）。本轮一律另起 9788/9789，**没有动任何他人进程**。
- 配置文件的 `vehicleMonitor.baseUrl` 本来就是对的（Java 端 `ruoyi-admin/src/main/resources/application.yml:200`
  已是 9902；Python 端 `car-monit-py/config/application.yml:281` 已是 9901），
  所以只加命令行/环境变量覆盖，未改仓库内配置。
- api 双端"共用配置文件中的数据库"由构造保证：`car-monit-api-python` 读的正是 Java 那份
  `application.yml`（两份文件 `diff` 完全一致），Redis 侧 api-Python 根本不连真实 Redis。
  **代价**见 §4:api-Java 写进 db0 的 `gantry_list` / `section_list` 快照，Python 端永远读不到。
- Java 端 500M 限制：全程 `-Xmx500m` 无 OOM、无 GC 超时、236 条 GET 零连接失败；
  进程 RSS ≈900MB（堆 500M + 元空间/线程栈/JNA/Netty 原生），这是 JVM 进程 RSS 与堆上限的正常差值。

## 3. 工装（本轮新增，均在 `car-monit-py/evidence/`）

| 文件 | 作用 |
|---|---|
| `_par_common.py` | 双端登录（验证码从各端自己的 db 取）、HTTP、db 感知 Redis 读取、归一化、差异分类 |
| `_par_tier.py` | 三档分档对比；URL 清单取 **Java 静态映射**（`scripts/audit_endpoints.py`），非一致自动复验一次 |
| `_par_api_pair.py` | 绕开 backend 直连 api 两端（9902 vs 9901），用于把第 1 档差异归因 |
| `_par_xlsx.py` | 导出层：附件流 + `ExcelUtil` 落盘两类都覆盖，单元格级对比 + 格式/排序分类 |
| `_par_redis.py` | 会话/验证码/缓存的分库隔离断言 + 同库行数一致性断言 |

两处自纠（都影响结论可信度，先记下）：

1. `_par_xlsx.py` 起初用 `iter_rows(values_only=False)`，比的是 `<Cell 'S'.A1>` 这种**坐标 repr**
   而不是值 ⇒ 首轮"55 条 SAME"全部无效；改为 `values_only=True` 后真实差异才露出来（23 条）。
2. `_par_tier.py` 复验时 `enumerate(first, 1)` 配 `urls[i]` 差一位，会把**下一条 URL** 的结果当复验结论
   （曾把 14 条真差异误判成"抖动"）。改为 `zip(urls, first)`。
3. 另修两处：httpx 被环境里的 `HTTP_PROXY`（DevSidecar）劫持本机端口 → `trust_env=False`；
   token 缓存未按端地址分键 → 换实例后复用旧会话导致钉版整批 401。

## 4. 第 1 档：backend 调 api 的接口（20 条，一致 14）

档位定义沿用 `car-monit-go/scripts/parity/compare_get.py`：`/base/{feeGantry,feerecords,feestationexit,snapshotflow}`
+ `/manager/cartrackinfo/{listByCarId,listByCarByTime,carSnapShot}`。
`/base/feerecords`、`/base/snapshotflow` 补时间窗参数（`inApplyTime1/2`、`applyTime1/2`），
否则两端都是 `total=0`，值比对失明。

| # | 端点 | java | py | 根因 | 定性 |
|---|---|---|---|---|---|
| 1 | `/base/feerecords/list?inApplyTime1/2` | code 500 + `msg="HTTP 500 ErrorContent={…}"` | code 200 + `rows=[]` | api 两端都 500（§5 已证），Java 的 Forest 抛错→全局异常处理器转 500；Python 的 `forest_get` **不看状态码**，把错误体当数据返回 | **Python 缺陷** |
| 2 | `/base/feerecords/{bigId}` | code 500 | code 200 + `data={"timestamp":…,"status":500,"error":"Internal Server Error"}` | 同上，且 Python 把上游错误信封整块塞进 `data` | **Python 缺陷** |
| 3 | `/base/feerecords/{bigId}`（带时间窗） | code 500 | 同上 | 同上 | **Python 缺陷** |
| 4 | `/base/feeGantry/{bigId}` | code 500，`ForestConvertException … Text '2024-10-26 08:53:57' could not be parsed` | code 200 + 正常数据 | api 两端此路径**逐字节相同**（2343B 全等）⇒ 与 api 无关；Java 侧 Forest/Fastjson2 无法把该日期文本转成实体字段 | **Java 侧既有缺陷**（Python 更宽松） |
| 5 | `/base/feestationexit/list` | `rows[0]` 无 `cid`/`cidList`/`enaxlecount` 等 null 键 | 同名键存在、值为 null | Java 用 hutool `JSONObject` 透传，默认丢弃 null 成员；Python 原样保留 | **Python 缺陷**（信封形状） |
| 6 | `/base/feestationexit/{bigId}` | 同上（`data.data.*`） | 同上 | 同上 | **Python 缺陷** |

其余 14 条（含 `feeGantry/list`、`snapshotflow/list(+时间窗)`、`snapshotflow/{id}`、`earliest-time`、
`cartrackinfo` 三条的两种参数形态）逐字段一致。

### 钉版归因（两端都打 api-Java 9902）

把 Python backend 起在 9790 指向 9902 复跑同一批 20 条：`SAME=11 / CODE=8 / MISSING=1`。
比交付接线（14/6）多出 3 条，全部是 **api-Java 的响应体形态触发 Python 侧严格解析**：

| 端点 | api-Java | api-Python | Python backend 钉到 9902 时 |
|---|---|---|---|
| `/base/snapshotflow/earliest-time` | 200 + **0 字节空体** | 200 + `null` | 500 `响应不是合法 JSON` |
| `/base/snapshotflow/{id}`（用非法 bigId） | 空体/非 JSON | 合法 JSON | 500 同上 |

⇒ 交付接线下的第 1 档差异**不会被 api 双端差异掩盖**：Python backend 在自己那侧（api-Python）
拿到的都是合法 JSON，剩下的 6 条差异确凿属于 backend 层（含 Java 自身的日期解析缺陷）。

### Redis 分库在这一档的连带影响

`gantry_list` / `section_list` 是 api-Java 用 `RedisCache` 写进 **db0** 的快照
（`pro-business-api/.../OdsSzdnGantryServiceImpl.java:63`），api-Python 的 Redis 是进程内 shim，
**不会落真实 Redis**（`car-monit-api-python/requirements.txt:17` 明确注明）。
因此凡读这些键的 backend 接口，在 Python 端只能走回源分支 —— 第 2 档、导出层各有一组差异由此而来。

## 5. api 双端自身（9902 vs 9901 直连，16 条，一致 14）

| 路径 | 结果 |
|---|---|
| `/base/snapshotflow/listToExport` | Java `$[6].carcolor="红色"、carcolorcode=4` vs Python `"未知"、0` —— **api-Python 车颜色翻译缺陷** |
| `/base/snapshotflow/earliest-time` | Java 空体 vs Python `null` —— **api-Python 响应体形态差异** |
| `/base/feerecords/list`、`/base/feerecords/{id}` | **两端都 500**（上一轮 Go 校验时 api-Java 500 而别的实现 200；这次 Python 端也 500，等价） |
| 其余 11 条列表 + 3 条详情 | 一致（`gantry/listAll` 1526、`org/listAll` 481、`section/listAll` 85、`toll/listAll` 321 等逐字节/逐字段等长） |

抖动记录：首轮 `/base/sfsjcxx/listAll` Java 20 条 vs Python 24 条；随后 3 轮复测两端都是 24 条且**逐字节相同**。
定性为 api-Java 侧冷缓存抖动（与 `car-monit-go/docs/PARITY-API-TIER-2026-11-04.md` §7 记录的现象同类），不作为结论。

## 6. 第 2 档：其它业务接口（134 条，一致 127）

| # | 端点 | 差异 | 根因 | 定性 |
|---|---|---|---|---|
| 1,2 | `/base/gantry/list`、`/base/toll/list` | `roadName`/`sectionName` Java 有值、Python 空串 | Python 端 db7 无 `section_list` 快照 ⇒ `read_section_list()` 拿到空表 ⇒ 名称映射空。**对照实验**：把 Python 起在 db0（9791）后与 Java 逐值相同（`福银高速/乐温`、`广吉`） | **分库必然代价**，非代码缺陷 |
| 3 | `/base/fitting/list` | Java 500（`ReflectionException`：Mapper 引用实体不存在的 `id` 属性）、Python 200 | Java 侧缺陷，上一轮 Go 校验已记录（`PARITY-2026-11-02` §8.2） | **Java 侧既有缺陷** |
| 4 | `/base/vehicleweight/{dataSource}` | Java 500（`TooManyResultsException: selectOne() found 200`）、Python 200 + data | Java 用 `selectOne` 命中多行直接抛错；Python 取首行返回 | **Java 侧既有缺陷**（Python 更宽松） |
| 5,6 | `/base/gantryIp/{id}`、`/base/tollStationIp/{id}` | 两端都 500，只有错误文本不同（Java「请求参数类型不匹配，参数[id]要求类型为 'java.lang.Long'」vs Python「id Input should be a valid integer」） | 这两张表的 `/list` 首行 `id` 是 32 位十六进制串，而 Java 控制器声明 `Long` ⇒ 主键类型本身不自洽 | **错误文本形态差异**（两端行为等价） |
| 7 | `/manager/suspicious/{id}` | 153 处，全在数值打印：`enweight 49440` vs `49440.0`、`pilenoDec 3146.37` vs `"3146.370"`、轨迹 `paths` 串中 `114.68317500000001` vs `114.683175`（长度 144418 vs 143041） | Java 侧 `BigDecimal`/`double` 全精度文本 vs Python 最短 repr + 字符串重序列化 | **Python 侧格式差异**（可修，属序列化层） |

## 7. 第 3 档：框架接口（82 条，一致 66）

| # | 端点 | 差异 | 根因 / 位置 | 定性 |
|---|---|---|---|---|
| 1 | `/system/config/configKey/{configKey}` | Java `{"msg":"skin-blue","code":200}` vs Python `{"msg":"操作成功","data":"skin-blue"}` | Java 命中的是 `AjaxResult.success(String)` 重载（值落 `msg`）；Python 写成 `car-monit-py/app/api/system/sys_config_controller.py:185` 的 `success_data()`。Go 端已复刻成 `msg` | **Python 缺陷** |
| 2-5 | `/getInfo`、`/system/user/profile`、`/system/dict/data/type/{dictType}`、`/system/dict/data/typemore/{dictType}` | Java 每个对象带 `"params":{"@type":"java.util.HashMap"}`，Python 整个键缺失 | Fastjson2 的 `WriteClassName` 标记随 Redis 反序列化漏进 HTTP 响应；Go 端在 `/getInfo` 上已复刻该标记 | **Python 缺陷**（信封形状；是否要复刻需先定策略：这是 Java 的内部类型标记外泄） |
| 6-8 | `/tool/gen/list`、`/tool/gen/db/list`、`/tool/gen/all/list` | `columns`：Java 给一条"除 `tableId` 外几乎全 null"的子集合，Python 给 `null` | `car-monit-py/app/api/tool/gen_controller.py:227/245/235` 未装配 `GenTable.columns` | **Python 缺陷** |
| 9 | `/tool/gen/genCode/{tableName}` | Java 200、Python 500「渲染模板失败，表名：…」 | Python 生成器模板与 Java `config/vm`(+`vmplus`) 不齐 | **Python 缺陷** |
| 10 | `/tool/gen/preview/{tableId}` | `data.vmplus/java/controller.java.vm` 文本不同 | 同上 | **Python 缺陷** |
| 11 | `/tool/gen/download/{tableName}` | zip 10790B vs 10580B | 生成物字节集不同（同一根因） | **Python 缺陷** |
| 12-15 | `/system/upgradeInfo/list`、`/newest`、`/{id}`、`/export` | 两端都 500，错误文本形态不同 | 库中缺表 `carmonitdb.sys_upgrade_info` | **环境问题**（非迁移缺陷） |
| 16 | `/monitor/server` | Java 500、Python 200 完整结构 | Java 侧 JNA 版本冲突（`PARITY-API-TIER-2026-11-04` §9 已记） | **Java 侧既有缺陷** |
| — | `/monitor/online/list`、`/monitor/cache`、`/monitor/cache/getNames` | 只比形状（3 条 SHAPE-OK） | 会话/命令计数是各端自己 db 的运行态 | **按设计只可比形状** |
| — | `/common/download/resource`、`/system/file/{id}/{name}` | 两端都 200 空体、逐字节一致（记为 non-json） | — | 一致 |

## 8. 导出层（58 条，一致 35）

覆盖两类：EasyPOI 附件流（响应体即 xlsx）与 `ExcelUtil` 落盘型（响应 `msg` 是文件名，文件在
`D:/ruoyi/uploadPath/download`，读完即删）。两端 writer 不同（POI vs openpyxl），只比
「sheet 名 + 单元格值」，两端都为空的尾行/尾列先裁掉。

| 类别 | 条数 | 具体表现 | 定性 |
|---|---|---|---|
| FORMAT/NUM | 15 条全在此类 | Java 单元格 `1.0`/`16075.00`/`225.30`，Python `1`/`16075`/`225.3`（POI 写 `Double.toString`；模板金额列 Java 落"两位小数字符串"） | **Python 侧格式差异**：整数列只是存储表示不同（Excel 显示一致），**金额列显示会差**，对应 Go 版 `moneyText()` 规则（恒两位小数） |
| FORMAT/STAMP | 与上并存（`confimfree/export` 83 格、`querylog/export` 1406 格） | `2026-02-03 16:19:19.572` vs `…572000`、`2025-12-18 11:19:27.0` vs `…27` | **Python 侧格式差异**，对应 Go 版 `stampText()`（小数秒去尾零、至少 1 位） |
| DIFF/JDATE | `gantrycar/export` 1 格、`gantrytrade/export` 2 格 | Java `Thu Aug 21 00:00:00 CST 2025` vs Python `2025-08-21 00:00:00` | **Python 侧格式差异**，对应 Go 版 `javaDateText()`（`Date.toString()`） |
| DIFF | `/base/geometry/export` 1 格 | Java 空格 vs Python 写入 1 万+ 字符的 `[[lng,lat],…]` | **Python 侧缺陷**：POI 拒绝 >32767 字符的格子，Java 表现为"有样式无值"空格 |
| DIFF | `/monitor/jobLog/export` 85 格 | 异常堆栈 Java `\r\n` vs Python `\n` | 运行态文本 + 换行表示 |
| DIFF | `/monitor/operlog/export` 12.9 万格 | 行集合规范化后交集 20250/21135（95.8%），差异集中在最新若干行 | **增长表自写入**：两端调用本身会写审计日志；`params[beginTime]` 时间窗在两端都未生效（两端 total 完全相同），无法做确定性行比对 |
| KIND | `/base/gantry/export` | Java 200+xlsx(1527×14) vs Python 200+空体 | **分库必然代价**（同 §6 第 1 条）。对照实验：Python 起在 db0 后逐格 **0 差异**（1527×14 全等） |
| DIFF | `/system/upgradeInfo/export` | 两端都返回错误 JSON，文本形态不同 | **环境问题**（缺表） |

其余 35 条导出（`/manager/carwarning`、`/manager/splitrecord`、`/manager/whiteinfo`、`/manager/exceptrecord/exportOrgId`、
`/manager/aduitfree/exportIncomeDetailList`、`/base/feerecords/export`、`/base/snapshotflow/export` 等）单元格级一致。

## 9. Redis 分库 / MySQL 共库断言（`_par_redis.py`，17 项全过）

- Java 会话 `login_tokens:*` 只在 db0、Python 只在 db7；验证码 `captcha_codes:*` 同理（双向都不漏）。
- 同名缓存键在两个 db 各有一份，且 `sys_config:*` 共名键两端值一致（同一 MySQL 回源，不是各自脏缓存）。
- 两端同参数查询 `total` 与 MySQL 行数一致：`sys_user` 6、`sys_dict_type` 53、`sys_dict_data` 226、
  `sys_config` 12、`car_suspicious` 63。
- api 双端读同一 openGauss：`gantry/listAll` 1526、`org/listAll` 481、`section/listAll` 85 两端等长。

## 10. 待修清单（Python 侧，按影响排序）

| 优先级 | 根因 | 位置 | 影响面 | 状态（修复轮后） |
|---|---|---|---|---|
| 高 | Forest 不看上游状态码：5xx 被当正常数据返回 | `app/base/service/forest/forest_client.py:113-119`（GET）、`:164-170`（POST）；需复刻 Java 的 `HTTP <status> ErrorContent=<body>` 文案 | 第 1 档 3 条 | **已修** §12.1 |
| 高 | hutool `JSONObject` 透传路径未丢 null 成员 | `app/api/base/ods_lwzxsfsj_fee_station_exit01_controller.py`（及其 forest service 返回的 Mapping） | 第 1 档 2 条 + 同类透传 | **已修** §12.2 |
| 高 | `AjaxResult.success(String)` 重载语义（值应落 `msg`） | `app/api/system/sys_config_controller.py:185` | 框架 1 条（前端直接读 `msg`） | **已修** §12.3 |
| 中 | 导出格式：金额恒两位小数 / Timestamp 小数秒去尾零 / `Date.toString()` / 超长格子置空 | `app/common/utils/poi/excel_util.py`（ExcelUtil 型）与 `app/common/utils/poi/template_export.py`（EasyPOI 模板型）；对应 Go 版 `moneyText`/`stampText`/`javaDateText`/`normalizeRow` | 导出层 18 条 | **已修** §12.4（另把 `car_info` 五列 + `buss_test.amount` 从 `float` 改回 `Decimal`） |
| 中 | 代码生成模板与 Java `config/vm`+`vmplus` 不齐 | `app/api/tool/gen_controller.py:227/245/235`、模板目录 | 框架 6 条 | 未修（不在本轮四项内） |
| 低 | 数值序列化：`BigDecimal`/`double` 的全精度文本 vs Python 最短 repr | 轨迹/重量相关 DTO | 业务 1 条（153 处） | 未修（同上） |
| 待定 | `params` 是否要复刻 Fastjson2 的 `{"@type":"java.util.HashMap"}` | 实体基类序列化层 | 框架 4 条；Go 端复刻了 `/getInfo` 一处，策略需先定（这是 Java 内部类型标记外泄） | 待定 |

Java 侧既有缺陷（Python 更宽松，不建议在 Python 复刻失败）：`/base/feeGantry/{id}` 日期反序列化 500、
`/base/fitting/list` Mapper 属性错、`/base/vehicleweight/{dataSource}` `selectOne` 多行抛错、`/monitor/server` JNA。

## 11. 复现

```bash
cd D:/work/IdeaProjects/car-monit-backend-new/car-monit-py
export PAR_JAVA=http://127.0.0.1:9788 PAR_PY=http://127.0.0.1:9789 PAR_JAVA_DB=0 PAR_PY_DB=7
export PAR_API_JAVA=http://127.0.0.1:9902 PAR_API_PY=http://127.0.0.1:9901
export MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8

.venv/Scripts/python.exe evidence/_par_tier.py     --tier api       --out D:/tmp/g-t1.json
.venv/Scripts/python.exe evidence/_par_tier.py     --tier business  --out D:/tmp/g-t2.json
.venv/Scripts/python.exe evidence/_par_tier.py     --tier framework --out D:/tmp/g-t3.json
.venv/Scripts/python.exe evidence/_par_xlsx.py     --tier all       --out D:/tmp/g-xlsx.json
.venv/Scripts/python.exe evidence/_par_api_pair.py --out D:/tmp/par-api2.json
.venv/Scripts/python.exe evidence/_par_redis.py    --out D:/tmp/par-redis.json
.venv/Scripts/python.exe scripts/audit_endpoints.py --json          # 路由面：Java 501 / Python 502 / 缺失 0
```

起服务（本轮实际用的命令行）：

```bash
# api Python（9901）
cd /d/work/IdeaProjects/car-monit-api/car-monit-api-python
CAR_MONIT_PORT=9901 .venv/Scripts/python.exe run.py

# backend Java（9788，堆 500M，Java→apiJava9902）
cd /d/work/IdeaProjects/car-monit-backend-new/ruoyi-admin/target
/d/jdk/jdk1.8.0_202/bin/java.exe -Xmx500m -jar ruoyi-admin.jar \
    --server.port=9788 --vehicleMonitor.baseUrl=http://127.0.0.1:9902

# backend Python（9789，db7，Python→apiPy9901）
cd /d/work/IdeaProjects/car-monit-backend-new/car-monit-py
SERVER__PORT=9789 SPRING__REDIS__DATABASE=7 \
    VEHICLE_MONITOR__BASE_URL=http://127.0.0.1:9901 .venv/Scripts/python.exe run.py
```

## 12. 修复轮（2026-11-05 下午，按 §10 前四项改 Python 端）

改动文件（7 个业务文件 + 1 个用例文件 + 文档）：

```
app/base/service/forest/forest_client.py                                  非 2xx 抛错 + 空体返回 None
app/base/service/forest/http_ods_lwzxsfsj_fee_station_exit01_service.py    hutool null 成员丢弃
app/api/system/sys_config_controller.py                                   configKey 值落 msg
app/common/utils/poi/template_export.py                                   Date/Timestamp/BigDecimal 文本、32767 置空
app/common/utils/poi/excel_util.py                                        MAX_CELL_TEXT_LENGTH、_set_string 超长置空
app/manager/domain/car_info.py                                            五列金额 float → Decimal
app/manager/domain/buss_test.py                                           amount float → Decimal
tests/test_sys_config_controller.py                                       4 条断言改回 Java 形态
COMPATIBILITY.md                                                          §45 记录本轮修复与三处表示差
```

### 12.1 复验数字（同一工装、同一接线，改前 vs 改后）

| 档 | 改前 | 改后 |
|---|---|---|
| 第 1 档 api（交付接线：Java→9902 / Python→9901） | 20 条：一致 14，CODE 4，MISSING 2 | 20 条：**一致 19**，CODE 1 |
| 第 1 档 api（钉版：两端都→9902） | 20 条：一致 11，CODE 8，MISSING 1 | 20 条：**一致 19**，CODE 1 |
| 第 2 档 business | 134 条：一致 127 | 134 条：一致 127（同一批 7 条，无新增、无回归） |
| 第 3 档 framework | 82 条：一致 59（+状态/形状 6） | 82 条：**一致 60**（+状态/形状 6），`configKey` 那条消失 |
| 导出层 | 58 条：一致 35，FORMAT 15，DIFF 7，KIND 1 | 58 条：**一致 46**，FORMAT 8，DIFF 3，KIND 1 |
| 合计 294 单元 | **一致 242（82.3%）** | **一致 258（87.8%）** |

钉版从 11 → 19 是因为空响应体的处理：api-Java 的 `/base/snapshotflow/earliest-time` 返回 0 字节，
Python 原来判"不是合法 JSON"直接 500，现在按 Java 一样得到 `null`。
**两种接线现在都只剩同一条差异** —— `/base/feeGantry/{bigId}`：api 两端字节相同，
Java backend 的 Forest/Fastjson2 解不了 `2024-10-26 08:53:57` 而恒 500（Java 侧缺陷，不在 Python 复刻）。

### 12.2 剩余差异的构成（改后再数一遍）

| 桶 | 条数 | 说明 |
|---|---|---|
| 分库必然代价 | 3（`/base/gantry/list`、`/base/toll/list`、`/base/gantry/export`） | `section_list`/`gantry_list` 快照只在 api-Java 那侧的 db0；Python 端起在 db0 对照实例后逐值/逐格相同 |
| Java 侧既有缺陷 | 4（`feeGantry/{id}`、`fitting/list`、`vehicleweight/{dataSource}`、`monitor/server`） | Python 更宽松，不建议复刻失败 |
| 同为错误时的文本形态 | 6（`upgradeInfo` ×4、`gantryIp/{id}`、`tollStationIp/{id}`） | 缺表 / 主键类型不自洽 |
| 运行态增长表 | 2（`/monitor/operlog/export`、`/monitor/jobLog/export`） | 两端调用自己会写审计行；堆栈换行受 openpyxl CR 归一影响 |
| 写入器表示差 | 8（`/system/*`、`/monitor/job|logininfor` 的导出 NUM 桶） | POI 写 `<v>1.0</v>`，openpyxl 归一成 `<v>1</v>`；数值与 Excel 显示都相同 |
| 未在这轮四项内 | 11（代码生成 6、`params.@type` 4、轨迹浮点打印 1） | 见 §10 状态列 |

另一条**不算差异但要知道**：`/base/feestationexit/*` 两端 JSON 的**键序**不同
（Java 的 hutool `JSONObject` 是 `HashMap` 顺序，Python 保留上游的插入顺序），
值集合在修复后已逐键相同。比对器按键集合比较，所以没有报出来；要做逐字节对拍时需要先归一化键序。

### 12.3 回归门

- `pytest -q`（3646 条）**全绿：0 失败、0 错误、0 跳过，约 41s**（`--junit-xml` 计数）。
- 修复过程中出现过、已定位并修稳的两条用例抖动（缺陷都不是本轮引入，机制见 `COMPATIBILITY.md` §45.6）：
  - `test_real_backend.py[…/system/user/list]`：基准 SQL 少了 `SysUserController#list` 那条无条件
    `user.setUserType("1")`。别的会话在共享库留下 `user_type` 为空串的 `PARITY_J` 行时就误报 7 vs 8，
    期间**两端 HTTP 实测始终同为 7、互相一致** —— 是用例基准条件不全，不是双端差异。
    已把基准补成 `… AND user_type='1'`，并逐个核对其余 `EXACT_TOTALS` 的控制器：只有这一条有隐藏过滤。
  - `test_common_utils.py::…get_timestamp_new2…`：断言依赖两次 `datetime.now()` 落在同一毫秒，
    跨毫秒边界时 `delta.days` 掉到 1。已改成按秒比较。
  - 两条所在用例组连跑 5 轮，每轮 27 项 0 失败。
- 4 条 `sys_config` 用例原本断言的是错误形态（`data`），按 Java 改成 `msg`。
- 交付接线的第 2 档 7 条差异与改前**逐条同号**，说明改动没有波及非目标端点。
