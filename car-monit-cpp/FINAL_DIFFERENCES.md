# 最终差异报告 —— Java(RuoYi/carmonit) ↔ C++(car-monit-cpp)

生成时间：2026-11-04；分支 `car-monit-cpp-local`，本报告之前的末次提交 `1bfe671`。
口径：分母 497 = Java 侧按 `@*Mapping` 注解逐条统计（`ruoyi-admin` + `ruoyi-quartz` + `ruoyi-generator`），
由 `scripts/endpoint_coverage.py` 生成，`scripts/gen_inventory.py` 渲染成 `ENDPOINTS_INVENTORY.md`。

本报告是**汇总索引**；逐条细节仍以 `COMPATIBILITY.md`（行为差异契约）、`PORTING_REPORT.md`（工程过程）为准，
本文每条都给出它们的章节号，避免两处描述漂移。

---

## 1. 结论摘要

| 指标 | 数值 |
|---|---|
| Java 端点总数 | **497** |
| 已迁移并路径匹配 | **466**（93.8%） |
| 未迁移 | **31**（逐条见 §4） |
| C++ 已注册路由（含 Java 没有的扩展） | **537** |
| CRUD Spec 覆盖实体 | 59，`verify_generated_sql` 在真实库 0 异常 |
| 实体字段 ↔ JSON 键缺口 | `audit_spec_keys` 报告 **0** |
| 单元测试 | 3 文件 / 32 组用例 / 286 处断言调用点 |
| 端到端断言（实机，需 MySQL+Redis） | 11 个脚本共 **265** 项（16+14+18+22+31+22+41+34+20 + 审批 27），本轮全部通过 |
| `@Log` 操作日志规则 | 234 条，C++ 已能写 `sys_oper_log` |

一句话结论：**接口契约（路径、方法、状态码、错误码、JSON 结构与键序、分页与鉴权语义）已对齐到"拿真实数据回归"的程度；剩余差异集中在外部依赖（对象存储、外部 HTTP、模板引擎）与 Excel 读取，且全部是显式标注的缺口，没有静默假数据。**

---

## 2. 契约层：已 1:1 复刻（✅）

| # | 契约 | 证据 / 章节 |
|---|---|---|
| 1 | `AjaxResult` 继承 `HashMap`，输出顺序是**桶序**而非插入顺序（`msg,code,data`） | COMPATIBILITY §3、`JavaCollections::javaMapOrder`、单测 `testAjaxResultOrder` |
| 2 | `AjaxResult.success(String)` 命中 **msg 重载** ⇒ 导出响应没有 `data` 键 | §2.3、`verify_cn_export.py` |
| 3 | `TableDataInfo` = `total,rows,code,msg`，走 `getDataTable` 才填 `200/查询成功`；`new TableDataInfo()` 是 `code:0,msg:null` | §6.3、`verify_gen.py`（`/tool/gen/column/{id}`） |
| 4 | `R<T>` = `code,msg,data`（`data=null` 也输出） | §3、单测 `testR` |
| 5 | 日期三态：`@JsonFormat` → 模式串；无注解 `java.util.Date` → **ISO-8601 带 `+08:00`**（用真实 jackson 2.11.4 + spring 5.3.6 + boot 2.4.5 customizer 实跑确认，不是 epoch 毫秒）；`@JsonInclude(NON_EMPTY)` 的 VO 空值不输出 | §3、§4.6 |
| 6 | 实体**字段初始值**照输出：`flag=false`、`number=0`、`supplementaryStatus="0"`、`children=[]`；只有无初值才是 `null` | §3、`audit_spec_keys.py` |
| 7 | 父类字段先输出、数组类型字段照输出、`@JsonIgnore` 字段（如 `password`、`searchValue`）不输出 | §4.13、`audit_spec_keys.py` |
| 8 | 只有 getter 的派生属性排在字段之后（`sub/tree/crud`、`capJavaField/pk/…/usableColumn`），故 `isPk`(String) 与 `pk`(bool) 并存 | §4.5 与 `verify_gen.py` |
| 9 | `MyBatis <if test="x != null and x != ''">` 语义：空串不进条件；OGNL 把 `''` 转成 0 ⇒ 数值字段的 `!= null and != ''` 对 `0` 不成立 | §3.8、`verify_gen.py` |
| 10 | XML 里 `<if>` 的全部条件都被移植，含**继承列**（epsId/tenantId/createBy/createTime 区间）与 `find_in_set` 的**参数方向**两种写法 | `PORTING_REPORT` §4.6 |
| 11 | `@TableLogic` 使 MyBatis-Plus 的 `count()` 自动带 `del_flag='0'`；`insert/update` 的 NOT_NULL 策略、`ASSIGN_UUID` 客户端生成 32 位主键 | §3 |
| 12 | PageHelper：`count(1)` 包同一条 dataSql、`total==0` 时不发数据查询、`pageNum<=0` → offset 0、`reasonable` 夹页、`order by` 前端优先回落 XML | §3.8、`verify_generated_sql.py` |
| 13 | 鉴权语义：未登录 **HTTP 200** + body `{"msg":"请求访问：…，认证失败，无法访问系统资源","code":401}`（RuoYi 的 `ServletUtils.renderString` 写死 `setStatus(200)`，业务码在 body 里）+ `Content-Type: application/json;charset=utf-8`（小写）、方法级权限不足 HTTP 200 + `AjaxResult(403,"没有权限，请联系管理员授权")`、URL 级 `anonymous()` == `isAnonymous()` ⇒ **带 token 反而容器级 HTTP 403**、URL 规则按注册顺序先命中先生效、非法 JWT → 真 500 | §4.1/§4.4/§4.5 |
| 14 | JWT：jjwt 0.9.1 secret 走 Base64 宽松解码（26 字符 → **19 字节**，尾组补零）、HS512、claim `login_user_key`；能直接复用 Java 写在 Redis db0 的会话 | §6.1 |
| 15 | 能读 Java 写的 Redis 缓存：fastjson2 非严格 JSON（`Set[...]`、`25367L`、`@type`）由 `normalizeFastJson2` 归一 | §6.2 |
| 16 | `@Log` 操作日志切面：枚举 ordinal、`getRequestURI` 不含 query、`IpUtils` 取 IP、`内网IP/XX XX`、参数三分支、fastjson2 丢 null、按**字符**截断、未登录/权限不足不写 | §6.6 |
| 17 | 异常→响应映射逐条对齐（`ServiceException`/`CustomException`/`BaseException`/NPE/`MethodArgumentTypeMismatch`/404/405） | §3、§4.8 |
| 18 | 结果集列名匹配不区分大小写（`information_schema` 的 `TABLE_NAME` 能落到 `table_name`） | §3 |
| 19 | 上传/下载：`FileUploadUtils` 命名规则、`/common/download` 的毫秒名与 `filename*=utf-8''`、静态 `/profile/**` | §2.3、`verify_cn_export.py` |
| 20 | **SELECT 投影 = `<sql id="selectXxxVo">` 的列清单**：MyBatis 只填结果集里出现的列，Vo 没写的属性在 Java 里保持字段声明初值（多为 null），但**照样能当 WHERE 条件的左值**。`car_suspicious` 的 `trackJosn/trackNames/epsId/sort/tenantId/createBy/updateBy/updateTime/delFlag` 9 个键即为此类（`scripts/audit_projection.py` 可逐实体复现） | `Field::inVo`、`verify_suspicious_history.py` |
| 21 | **WHERE 左值列与运算符以 XML 为准**：`sectionCode`/`sectionName` 在 Java 里过滤的是 `t.track_names`（不是 `section_code`）、`carNoQuery`→`t.car_no like`、`applyTime1/2`→`t.in_time >= / <=`、`and t.id != #{id}` 是不等于；派生属性也能带条件（`condColumn`）。`scripts/audit_cond_columns.py` 逐条对拍 | `Field::condColumn`、`Cond::Gte/Lte/Ne/NotLike` |
| 22 | 导出类接口一律先 `startPage()`：`exportHistory` 导的是**当前页**，不是全表；且 Java 导出前把 7 个字典全查一遍（`Collectors.toMap` 遇重复 `dict_value` 抛异常 → 整个导出 500），少查一个就变成"Java 500、C++ 成功" | §2.3、`verify_suspicious_history.py` |

---

## 3. ⚠️ 有意偏离（全部标注 + 影响面 + 规避）

| # | 偏离 | 影响 | 规避 / 现状 | 章节 |
|---|---|---|---|---|
| ⚠️1 | 验证码图片 **JPEG → PNG**；无 zlib 时 PNG 不压缩（约 10KB） | 仅体积，解码结果一致 | 系统装 zlib 则自动启用 | §2.1/§2.2 |
| ⚠️2 | Redis value 序列化不是 Java 的 fastjson2 二进制格式，而是 JSON 文本 | **只影响 C++ 自己写的键**；读 Java 会话正常 | 与 Java 混跑时避免让 Java 读 C++ 写的键 | §2.2、§6.2 |
| ⚠️3 | Excel 导出：响应形态/文件名/列集合/单元格类型/`readConverterExp` 都对，但模板导出**不复刻标题行、两级表头、合并单元格与样式**（自研最小 OOXML，单 sheet inline string） | 导出文件可正常打开，数据一致，版式不同 | 需要版式时改接真实模板渲染 | §2.3 |
| ⚠️4 | 无 Quartz 调度器：`sys_job` CRUD 与 `changeStatus`/`jobLog` 语义一致，但 `PUT /monitor/job/run` **明确返回未实现**，调度需外部触发 | 定时任务不会自转 | 外部 cron/systemd/K8s 调 HTTP；或 Java 继续承担调度 | §2.4、`PORTING_REPORT` §6.6 |
| ⚠️5 | 固定 32 工作线程（`CM_WORKERS`），无 GC；长耗时外部调用会占满 worker | 并发模型不同，慢上游会整站排队 | 部署时按核数放大；外部调用必须设超时 | §2.5、§5.1 |
| ⚠️6 | 日期固定按 `+08:00`（Java 跟随 JVM 时区） | 部署到别的时区会不一致 | 容器内 `TZ=Asia/Shanghai`（compose 已设） | §2.6 |
| ⚠️7 | `BigDecimal` 按 double 最短形式输出（`1.10 → 1.1`） | 前端若按字符串比较会不同；导出另有 `*Str` 文本列 | 金额透传原始文本 | §2.7 |
| ⚠️8 | **不支持 chunked 请求体**（返回 411），需 `Content-Length`；上限 200MB 与 Java 一致 | 极少数流式上传客户端受影响 | 网关缓冲后转发 | §2.8 |
| ⚠️9 | 日志：非 Logback 逐字节格式，无 MDC/traceId 自动注入 | 日志采集格式需适配 | 显式传 traceId | §2.10 |
| ⚠️10 | **SQL 执行失败被降级成空结果**（Java 是 `BadSqlGrammar` → code 500）——模板导出路径已改成失败即抛，其余路径未统一 | "接口返回空"可能是真失败 | 查 `logs/carmonit.log` 的 `[WARN] Db - 查询失败` | §2.12 |
| ⚠️11 | Windows 本地开发机 `std::filesystem` 按 GBK 解释 UTF-8 路径（Java/JDK 无此问题） | 中文名文件读写会失败 | `cm::compat::fsPath/fsUtf8` 已在全部落盘点接入；Linux/Docker 不涉及 | §2.11 |
| ⚠️12 | 操作日志异步队列**有界**（5 万），Java 的 timer 队列无界 | 溢出丢日志并打本地错误，不改 | 刻意偏离，保内存 | §6.6 |
| ⚠️13 | `multipart` 上传类接口的 `oper_param` 记空串；JSON 请求体记"请求体本身"而非绑定后的实体（键序/未知键取舍可能不同） | 仅日志可读性 | §6.6 三条偏离已逐条说明 | §6.6 |
| ⚠️14 | 静态资源/前端：`config/static` 代替 classpath，无 swagger-ui / druid 控制台（Java 侧本来就 `denyAll`） | 运维入口缺失 | 用 `ENDPOINTS_INVENTORY.md`；`GET /health` 是 C++ 扩展 | §2.9、§5 |
| ⚠️15 | 无 Apache POI / Kafka / Elasticsearch / ShardingSphere / MinIO SDK / OSS SDK | 见 §4 未实现清单 | 逐条替代方案在 §5 表 | §5 |

---

## 4. ❌ 未迁移的 31 条端点（按前置能力分组，分组计数与 31 对账）

依据：逐条读 Java 源码（controller → service impl → mapper XML → application.yml/SecurityConfig），
不靠猜。分组小计：9 + 7 + 7 + 4 + 3 + 1 + 2 + 2 = **35**。

### A. SysFileController —— 9 条（存储是 MinIO/S3，`oss.endpoint=http://172.30.100.102:9002`，非本地盘）

| 端点 | 阻塞点 |
|---|---|
| `POST /system/file/upload` | `AmazonS3Client.putObject`（AWS SDK v1，SigV4 + path-style + `disableChunkedEncoding`）+ 写 `sys_file` + 扩展名白名单 |
| `POST /system/file/uploadSupplier` | 同上，另多带 `bussNames[]` 数组参数与 `fileSupplierLog` |
| `POST /system/file/uploadPdf` | PDF 走 S3；**非 PDF 分支写本地盘**（`ruoyi.profile/upload`），Word→PDF 转换整段被注释 ⇒ 返回的 map 没有 `id` |
| `POST /system/file/uploadFile` | 小程序入口：`getFile("file")` + jpg/jpeg/png/gif + 15MB；之后同 upload（**无 @Log**） |
| `POST /system/file/uploadFileId` | `sun.misc.BASE64Decoder` 解 `data:<mime>;base64` 并伪造 originalFilename；先 S3 DeleteObject 再 insert+put |
| `GET /system/file/{bucket}/{obj}` | S3 GetObject，`void` + 裸字节流，Content-Type 恒 `application/octet-stream; charset=UTF-8`；异常被吞 ⇒ 200 空体 |
| `GET /system/file/view/{bucket}/{obj}` | 与上共用 `getFile`；SecurityConfig 是 `anonymous()` ⇒ **带 token 反而 403**，是唯一免鉴权读取口 |
| `POST /system/file/uploadByUrl` | S3 + **Forest 下载任意 URL**（`FileApi.downloadImageToByteArray`）⇒ 还要出站 HTTP 客户端；单条异常被吞 |
| `POST /system/file/uploadFileEnc` | **其实没有阻塞**：Java 里循环体与 `caService.encodeEnvelopedFile` 全是注释 ⇒ 恒返回 `AjaxResult.success([])`，不碰 S3、不加密。现在就能 1:1 复刻 |

### B. CarSuspiciousController —— 5 条

| 端点 | 阻塞点 |
|---|---|
| `PUT /manager/suspicious/check` | **纯本地事务，无外部 HTTP**：校验 status≠"1" → 删 check/`car_except_record` → 无车则插 `car_info` → 批量落库 → `check_status='1'` → 刷 Redis 车辆列表；返回 `AjaxResult.success("操作成功！",id)`；**`@PreAuthorize` 在 Java 里被注释掉**，不要顺手补 |
| `GET /manager/suspicious/listFileCarNo` | 本地 SQL，但每行调 `selectCarSuspiciousById` → 解析 `track_josn` → `getCarGeometryByPlanNew` → 受 Redis 开关 `sys_config:api_map` 分流（`"0"` 走本地几何，否则要外部路网） |
| `GET /manager/suspicious/history/{id}` | 同上（同一套几何后处理） |
| `GET /manager/suspicious/exportAbnormalPassage` | **docx** 模板：`WordExportUtil.exportWord07` + `ImageEntity` 图片嵌入 + S3 GetObject 取图 ⇒ 需 docx 填充能力 |
| `POST /manager/suspicious/syncSuspiciousCarTask` | `SecuritySHA1Utils.shaEncode(signatureKey+timeStamp)` 与传入 signature 直接比（三参数都由调用方给 ⇒ 可离线伪造、无时间窗）+ Redis 白名单/字典 + `envehicletype→carVehicle` 硬编码映射 + 批量落库。SHA1 原语已有，缺的是那套映射 |

### C. GenController —— 7 条

| 端点 | 阻塞点 |
|---|---|
| `POST /tool/gen/importTable`、`PUT /tool/gen`、`GET /tool/gen/synchDb/{tableName}` | 需 `GenUtils.initTable/initColumnField`（类型→javaType/htmlType 映射表、`information_schema.columns` 读列）与 `validateEdit` 的树/子表校验分支 |
| `GET /tool/gen/preview/{id}`、`/download/{t}`、`/genCode/{t}`、`/batchGenCode` | 28 份 Velocity 模板渲染 + zip（zip 写出器本轮已为 xlsx 落地） |

### D. CarTrackInfoController —— 3 条

| 端点 | 阻塞点 |
|---|---|
| `GET /manager/cartrackinfo/listByCarId` | 本地为空才回退 `httpSysUtilApiService.carTrackQueryByCarNo`（`127.0.0.1:9901`），且**回退时写 Redis + 落库**（读接口带写副作用，必须照抄） |
| `PUT /manager/cartrackinfo/changeTrailInfo` | 同上按 `sys_config:api_map` 分流 + `carQueryLogService.queryLog` 落日志 |
| `GET /manager/cartrackinfo/carSnapShot` | 纯外部：`/base/sysutil/getByTrailBo`，整个 `TrailBo` 被拍平成 query string |

### E/F/G/H. 其余 7 条

| 端点 | 阻塞点 |
|---|---|
| `GET /base/geometry/getHenDa`、`/syncAllGeometry`、`/syncAllGeometry1` | Forest → GeoServer `http://36.200.20.14:7890/...`；签名是 `EncryptUtils.createSignature` 的 MD5 字典序拼接，**含 `append(publicStr)` 自拼接 quirk，必须逐字复刻**；两个 sync 是"先 `return success()` 再后台线程池跑"，失败不可见（§5.1） |
| `GET /base/snapshotflow/earliest-time` | Forest → `127.0.0.1:9901`；无 try/catch ⇒ 上游失败直接 500；`data` 在"日期串"与 `"暂无数据"` 之间切换 |
| `POST /manager/carinfo/import`、`POST /manager/exceptrecord/import` | 需 xlsx 读取（`ImportSysUtil` 只支持 xlsx；`ImportEntity` 中文列名→属性硬编码表；错误优先 `AjaxResult.error("error", errorList)`，msg 不是 500） |
| `POST /manager/busstest/syncCurrentTrack` | **纯 DB+Redis**；返回 `void` ⇒ 成功是 200 空体；`isLocalhost=="local"` 时直接不执行 |

> 另注：`POST /system/user/importData` 已在路由表里（未计作"未覆盖"），但它同样缺 xlsx 读取器 —— 现在返回显式错误而不是假成功。

### 小结：按"缺什么能力"重排（4 + 7 + 1 + 9 + 1 + 2 + 7 = 31）

| 缺的能力 | 条数 | 端点 |
|---|---|---|
| **无（纯移植工作量）** | **4** | `file/uploadFileEnc`、`suspicious/check`、`suspicious/syncSuspiciousCarTask`、`busstest/syncCurrentTrack` |
| S3 / MinIO 客户端（SigV4） | 7 | `file/upload`、`uploadSupplier`、`uploadPdf`、`uploadFile`、`uploadFileId`、`GET /{bucket}/{obj}`、`GET /view/{bucket}/{obj}` |
| S3 + 出站 HTTP | 1 | `file/uploadByUrl` |
| 出站 HTTP（外部服务在场才能验） | 9 | `suspicious/listFileCarNo`、`suspicious/history/{id}`、`cartrackinfo/listByCarId`、`changeTrailInfo`、`carSnapShot`、`geometry/getHenDa`、`syncAllGeometry`、`syncAllGeometry1`、`snapshotflow/earliest-time`（其中 `listByCarByTime` 的远程分支在 Java 里整块被注释，故已作为纯本地端点落地） |
| docx 模板填充 | 1 | `suspicious/exportAbnormalPassage` |
| xlsx 读取（INFLATE + sharedStrings + `@Excel` 反查） | 2 | `carinfo/import`、`exceptrecord/import` |
| GenUtils / Velocity + zip | 7 | `gen/importTable`、`PUT /tool/gen`、`gen/synchDb`、`preview`、`download`、`genCode`、`batchGenCode` |

两点修正性说明：
* `listFileCarNo` / `history/{id}` / `changeTrailInfo` 取决于 Redis 开关 `sys_config:api_map`：值为 `"0"` 时走**本地几何**，那时这三条也归入"无需新能力"。
* `POST /system/user/importData` 已注册（因此不计入 35），但它同样缺 xlsx 读取器 —— 现在返回显式错误而不是假成功。

## 5. 照抄的 Java 缺陷清单（防"顺手修正"）

| 条目 | 表现 | 出处 |
|---|---|---|
| `GET /base/tollStationIp/list` | XML `order by t.big_id`（列不存在）→ Java 本来就 500，C++ 一致 | `verify_generated_sql.py::EXPECTED_SQL_ERRORS` |
| `POST /system/user {}` | 校验注解被注释掉 ⇒ NPE，`{"msg":null,"code":500}` | COMPATIBILITY §4.9 |
| `anonymous()` 三处路径 | 带合法 token 反而容器级 403（`/common/download**`、`/system/notice/view/**`、`/system/file/view/**`） | §4.4 |
| `/**/*.html` 在 `/druid/**` 之前 | `GET /druid/index.html` 实际 permitAll，`.json` 才 denyAll | §4.5、单测 |
| `find_in_set(except_ids, #{id})` | 参数顺序反直觉（列在值里），照抄 | §4.10、`verify_generated_sql` |
| `submitReturn` 用节点 id 删 `flow_apply_info` | Java 的既有 quirk，保留 | `FlowApprovalService` |
| 恒达签名 `createSignature` 的 `append(publicStr)` 自拼接 | MD5 结果依赖这个 bug，移植必须逐字复刻 | COMPATIBILITY §5.1 |
| `GET /tool/gen/column/{talbleId}` | 路径变量拼错（`talbleId` vs 参数 `tableId`），Spring 解析行为不确定；C++ 按路径变量实现并标注 ⚠️ | `PORTING_REPORT` §4.5 |
| `selectOrgId` 返回 String 但 SQL 可能多行 | 多行时 Java 抛 `TooManyResultsException`；C++ 取第一行（已标注 ⚠️） | `PORTING_REPORT` §4.2 |
| `SysFileController.uploadFileId` 里 `AjaxResult.error("主键不能为空")` 返回值被丢弃 | 未迁移；迁移时不要"修正" | §4.2 |
| `uploadFileEnc` 循环体是注释 | 恒返回空数组 | §4.2 |
| `syncSuspiciousCarTask` 签名三参数由调用方提供、无时间窗 | 可无限重放、可离线伪造 | §5.1、§4.5 |

---

## 6. 验证矩阵

| 层 | 命令 | 断言 | 最近结果 | 覆盖的差异条目 |
|---|---|---|---|---|
| 单元 | `./build/carmonit_tests` | 32 组 / 286 处 | ALL PASSED | §2 的 1–8、11–14、17–19；`Field::dflt`；`ASSIGN_UUID`；URL 规则顺序 |
| 生成 SQL | `python scripts/verify_generated_sql.py` | 59 实体逐条打到真库 | 0 异常 | §2.10–11 |
| 键缺口 | `python scripts/audit_spec_keys.py` | 实体字段 ↔ spec 键 | 0 缺失 | §2.6–8 |
| 导出/下载 | `python scripts/verify_cn_export.py "$TOKEN"` | 16 | pass=16 fail=0 | §2.2–3、§4.4、⚠️11 |
| `@Excel` 列 | `python scripts/verify_user_excel.py "$TOKEN"` | 14 | pass=14 fail=0 | §2.3、§4.13 |
| 操作日志 | `python scripts/verify_operlog.py 9991 "$TOKEN"` | 18 | pass=18 fail=0 | §2.16 |
| 大屏 | `python scripts/verify_bigscreen.py 9991 "$TOKEN"` | 22 | pass=22 fail=0 | §2.15、缓存与规则链路 |
| 代码生成 | `python scripts/verify_gen.py 9991 "$TOKEN"` | 31 | pass=31 fail=0 | §2.7–8、§4.5、columnList 的 `code:0` |
| 模板导出 | `python scripts/verify_template_export.py 9991 "$TOKEN"` | 22 | pass=22 fail=0 | ⚠️3、§4.10 条件修复 |
| 审批流 | `python scripts/verify_flow_approval.py --port 9991` | 27 | ALL PASSED | 多表事务 + 回滚（`Transaction`） |
| 覆盖率 | `python scripts/gen_inventory.py` | — | 462/497 | §4 |

Token 不需要登录：`scripts/make_token.py` 复用 Redis db0 里 Java 现存会话，按 jjwt 等价方式签发（§6.1）。

---

## 7. 环境依赖与复验步骤

```bash
# 1) 依赖：MySQL(3307, carmonitdb) + Redis(6379, db0)。Windows 上 mysqld/redis-server 目前以手工进程方式提供，
#    服务 mysql8 本身是 Stopped（net start 报 InnoDB 'ibdata1' must be writable，需要改服务账号或目录 ACL）。
# 2) 构建 + 单测
cmake --build build -- -j2 && ./build/carmonit_tests
# 3) 起服务（默认 9990，可用环境变量换端口）
CM_SERVER_PORT=9991 ./build/car-monit-cpp.exe
curl -s http://127.0.0.1:9991/health        # {"status":"UP","db":"UP","redis":"UP"}（C++ 扩展端点）
# 4) 端到端全套
TOKEN=$(python scripts/make_token.py | tail -1)
for s in verify_cn_export verify_user_excel verify_operlog verify_bigscreen verify_gen verify_template_export; do
  python scripts/$s.py 9991 "$TOKEN" || echo "FAILED $s"
done
python scripts/verify_flow_approval.py --port 9991
```

---

## 8. 剩余风险与建议顺序

1. **先补出站 HTTP 客户端**（一次性解锁 8 条外部依赖接口，且能对本地 stub 验证超时/失败边界）；同时把 `hengda` 的 MD5 自拼接 quirk 与"失败塌缩成 null"照抄，不做参数化修复。
2. **再补 INFLATE + xlsx 读取器**（解锁 3 条 import；顺带能读 easypoi 模板做真正的版式复刻，消掉 ⚠️3）。
3. **S3 SigV4 客户端**（解锁 8 条 SysFile；MinIO 不在网内 ⇒ 只能对 AWS 官方测试向量做签名级单测 + 本地 fake S3 验证 PUT/GET/DELETE 行为，要如实标注"未对真实 MinIO 验证"）。
4. **统一 SQL 失败的降级语义**（⚠️10）：现在只有模板导出路径改成抛异常，其余仍是"失败变空结果"，需要一轮全量改 + 回归。
5. `@Log` 已落地，但 `preview/genCode/download` 的 Velocity 渲染是纯增量工作（zip 已具备）。
6. 混跑注意：C++ 写进 Redis 的键用 JSON 文本（⚠️2），别让 Java 侧去读；两侧都不给 `car_list`/`car_warning_list` 设 TTL，行为一致但缓存新鲜度依赖 Java 的刷新任务。
