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
| 已迁移并路径匹配 | **491**（98.8%） |
| 未迁移 | **6**（逐条见 §4） |
| C++ 已注册路由（含 Java 没有的扩展） | **564** |
| CRUD Spec 覆盖实体 | 59，`verify_generated_sql` 在真实库 0 异常 |
| 实体字段 ↔ JSON 键缺口 | `audit_spec_keys` 报告 **0** |
| 单元测试 | 10 文件 / 514 处断言调用点（含 INFLATE 三种块类型、真实 deflate 的 xlsx 对拍、GpsUtil 对 Python 独立实现的对拍） |
| 端到端断言（实机，需 MySQL+Redis） | 18 个脚本；本轮复跑 14 个共 **380** 项全通过（suspicious_check 33、sync_suspicious 27、trail 几何 54、import 61、bigscreen 22、suspicious/history 41、track_by_time 34、template_export 22、operlog 18、cn_export 16、user_excel 14、gen 31、tb_flow 20、**list_by_car_id 47**）；`verify_generated_sql` 另有 59 个实体逐条建 SQL 跑真实库，0 异常。其余脚本需 fake S3 / 桩服务，随各自批次验过。⚠️ 本轮末次改动（`compactJson` 的 POJO/Map 排序开关、`FormatMessageW`、错误信封 `dumpLenient`）复跑时 MySQL/Redis 已经下线，只有单测 + 手工 curl 验到，**下一次拉起依赖服务后要把上面 14 个脚本整套重跑一遍** |
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
| 23 | **Redis 缓存值的字节形态 = fastjson2 `WriteClassName`**：`RedisConfig` 给 valueSerializer 开了 WriteClassName，于是 `car_list` 里是 `[{"@type":"com.ruoyi.manager.domain.CarInfo","carNo":…,"createBy":1L,…}]` —— 字段**按名排序**、null 整个键省略、Long 带 `L`、BigDecimal 保 DB 标度。C++ 若 dump 严格 JSON，Java 反序列化拿到的是 JSONObject，用到就 ClassCastException，等于缓存互操作失效 | `cm::web::crud::fastJson2CachedArray`，`verify_import.py` 的 3 条缓存断言 |
| 24 | **恒定 WHERE 只看本层**：`selectCarInfoList` 除了 `del_flag='0'` 还挂着一个**无条件**的 `not exists (… group by car_no … except_num = 0)` —— 异常流水已全部补缴的车牌在列表/导出/缓存/导入回查里都查不到。早先生成器把子查询里的 `case when t1.status='0'` 误成本层恒定过滤，凭空加了 `and t.status='0'`（少返回一批行，且让导入把已缴清的车当新车重插） | `scripts/gen_crud_spec.py:strip_subqueries`、`verify_import.py` |
| 25 | **派生列不属于任何 Field**：Java 普遍写成 `<include refid="selectXxxVo"/>,concat(sd.dept_name,' ',su.nick_name) createInfo` + 两个 left join。它既不在 Vo 里也不是表列，所以要用 `Spec::selectTail`/`fromSql` 表达；任何自己拼 `FROM 表 别名` 的地方都会因为拿不到 join 而生成非法 SQL | `selectSqlOf`/`fromClauseOf` |
| 26 | **导入的三段语义**：表头逐格 `String.equals`（carinfo 比第 1 行，exceptrecord 比第 2 行**或**第 3 行且两次用同一份列名）；数据读取靠 `getRow()` 的 NPE-catch 做 break ⇒ "整行缺失"停读、"行在但没格"不停；`errorList` 跨行共享 + `> 100` 才 break ⇒ 第一个错误之后的行全不入库、最多 101 条错误；`rowNo = index + 2`（exceptrecord 数据在 Excel 第 4 行起，报的却是 2 起） | `ImportExcel.hpp/cpp`、`verify_import.py` 61 项 |
| 27 | **`@Transactional` 的提交点**：`saveCarInfo` / `saveCarExceptRecord` 都是"return error 而不是 throw" ⇒ 事务照常提交，只是少写一行；而外层 `CarInfoServiceImpl.doImport` 与非事务的控制器循环意味着批量导入**没有**整体原子性，插到第 N 行失败就留前 N-1 行。C++ 的 `Transaction` 析构默认回滚，必须在每个"正常返回"路径显式 commit | `ManagerImportControllers.cpp`，`verify_import.py` |
| 28 | **轨迹几何是三级回退，不是二选一**：`ByPlanNew`（本地 roadPath）→ `ByPlan`（腾讯）→ `getCarGeometry`（纯本地 geometry 表按桩号区间拼接）。两条出站分支把所有异常都 `catch(Exception){return null;}` 吞掉，调用方据此**继续降级**而不是返回空/500；失败值也不写缓存。所以外部服务全挂时响应依然是 200 且 `raodTrailList` 有内容 | `TrailGeometry.hpp` 顶部链路图，`verify_trail_geo.py` |
| 29 | **`sys_config:api_map` 只读 Redis 裸键**，绕开 `SysConfigService`：不走 `sys_config` 表回源、不回填缓存，键缺失时默认 `"1"`，只有 trim 后等于 `"0"` 才切到腾讯分支。也就是说库里配了 `api_map` 而 Redis 没同步时，Java 这里看不见 —— C++ 若"顺手"改成走配置服务就会不一致 | `Constants::API_MAP`，`verify_trail_geo.py` 的两条开关断言 |
| 30 | **`car_lxgh:` 缓存键是无分隔符拼接**（前缀 + 车牌 + 入口站 + 出口站 + 点数），且 `ByPlan` 那条键里 BigDecimal 用 `toString()` 而请求用 `toPlainString()` —— 需要科学计数法的值两边文本不同。这是 Java 的不一致，照抄 | `TrailGeometry::carGeometryByPlan*` |
| 31 | **`getCarGeometry` 对入参列表有可见副作用**：`trailBo.setPilenoDec(...)` 写的是控制器同一个 list 实例，所以响应里 `trailList` 与 `trailDevCountBO.trailList` 都带出 `pilenoDec`；而且路线顺序是 `LinkedHashMap` 的首次出现序（不是排序），`reserver` 又取的是**排序前**的首/末位置 | `verify_trail_geo.py`（pilenoDec 断言） |
| 34 | **`syncSuspiciousCar` 里那段 Redis 扫描是"跑了但结果被丢掉"**：`addFlag` 是 `"task"` 时，代码仍然先执行 `keys(car_uspicious + yyyyMMdd + "*")`，`redis` 分支收集到的 `trailInfoList` 随后被 `trailInfoList = paraTrailInfoList;` 无条件覆盖。所以那次 KEYS + 若干 GET 对输出没有任何影响 —— 但它是 Java 每次请求都会付出的开销，不算死代码，去掉就是行为不一致。另外 `userId` 写死 `1L`（不是登录人），`create_time/update_time` 用的是 `getTimestampNew2()` —— 名字像"取当前时间"，实际是**当前时间减 2 天**。 | `verify_sync_suspicious.py` |
| 33 | **MyBatis-Plus 的审计列填充取决于父类，不是一刀切**：17 张表的实体 extends `BasePlusEntity` / `BasePlusEntityInput`，这两个父类声明了 `fill = FieldFill.INSERT/UPDATE` ⇒ insert 补 create_by/create_time/eps_id（tenantId 只在 epsId 恰好为空时才补，Java 的复制粘贴错误），update 补 update_by/update_time。其余父类（`BasePlusEntityNew` / `…InputNew` / `…Long` / `BaseEntity` / `BaseUuidEntity`）**一个都没有** —— 例如 `car_info`（InputNew）与 `car_suspicious`（Long）的 updateById 就不动审计列。因为 `update_time` 就在 `selectXxxVo` 里，少写了列表接口立刻能看出来 | `Spec::auditFillInsert/Update`（由生成器读父类源码得出），`verify_suspicious_check.py` |
| 32 | **同一份实体在不同层的形态不同**：Jackson 响应 = 声明序 + null 全输出（`ZdataTrailTracks` 51 键、`TrailBo` 32 键）；fastjson2 缓存/query_condition = 按名排序 + null 省略；`TrailInfo.enterTime` 没有 `@JsonFormat` ⇒ 输出 epoch 毫秒数字，而 `tracks.enterTime` 有 ⇒ 输出 `"yyyy-MM-dd HH:mm:ss"`。三者混用就是不一致 | `projectViaSpec`/`projectTrailInfo`，`verify_trail_geo.py` |
| 35 | **fastjson2 的对象写出器按字段名排序，Map 不排**：`JSON.toJSONString(TrailInfo/TrailBo)` 是字母序，而 `AjaxResult`(HashMap) 是桶序 —— 同一条链路上并存两种形态。C++ 的 `ordered_json` 只保留插入序，所以 `fastJsonCompact` 加了 `pojoFieldOrder` 让调用方声明是哪一种 | 实机对拍 fastjson2 2.0.43（声明序 `zzUuid/lon/middle/…` 打出来是 `countNum,directionIn,emptyStr,lon,nested,zzUuid`）；Map 那一侧由单测 `testOperLogAspect` 钉住 |
| 36 | **Forest `@Query(POJO)` 的拍平规则**：按声明序、null 整个省略、BigDecimal 保标度（`116.500` 就是 `116.500`）、布尔小写、嵌套对象转 JSON 文本、空串渲染成裸键名；`CarParaVO` 因此只出 `carNo&pageNum&pageSize` 三项 | 实机抓 Forest 1.5.9 发出的请求行；`verify_list_by_car_id.py` 断言上游收到的 query（与 C++ 的等号差异见 ⚠️17） |
| 37 | **Spring 的参数绑定发生在进方法之前**：`carSnapShot?lon=abc` 走不到 `isNoneBlank` 判断，直接 `BindException` ⇒ `code:500`；空串对数字/布尔属性落成 null（属性保持缺省、拍平时省略），对 String 属性则是 `""`（照样拍平出去） | `verify_list_by_car_id.py` 的 `lon=abc` / `directionIn=maybe` 两条用例（文案见 ⚠️18） |
| 38 | **`carSnapShot` 两个字段的空白判断不对称**：`stateType` 过了 `CommonUtil.isNull`（顺带 trim），`pointUuid` 没过。任一空白就直接 `AjaxResult.success()` ⇒ 响应**没有 `data` 键** | `verify_list_by_car_id.py` 的三条缺参用例 |

---

## 3. ⚠️ 有意偏离（全部标注 + 影响面 + 规避）

| # | 偏离 | 影响 | 规避 / 现状 | 章节 |
|---|---|---|---|---|
| ⚠️1 | 验证码图片 **JPEG → PNG**；无 zlib 时 PNG 不压缩（约 10KB） | 仅体积，解码结果一致 | 系统装 zlib 则自动启用 | §2.1/§2.2 |
| ⚠️2 | Redis value 的写出形态：`car_list`/`car_list_jc` 已改为 fastjson2 `WriteClassName` 形态（✅ 可与 Java 互读，见契约 23）；其余键（登录会话等）C++ 仍写普通 JSON 文本 | **只影响 C++ 自己写的非缓存键**；读 Java 会话/缓存都正常 | 与 Java 混跑时别让 Java 读那些普通 JSON 键；新增缓存键一律走 `fastJson2CachedArray` | §2.2、§6.2、契约 23 |
| ⚠️3 | Excel 导出：响应形态/文件名/列集合/单元格类型/`readConverterExp` 都对，但模板导出**不复刻标题行、两级表头、合并单元格与样式**（自研最小 OOXML，单 sheet inline string） | 导出文件可正常打开，数据一致，版式不同 | 需要版式时改接真实模板渲染 | §2.3 |
| ⚠️4 | 无 Quartz 调度器：`sys_job` CRUD 与 `changeStatus`/`jobLog` 语义一致，但 `PUT /monitor/job/run` **明确返回未实现**，调度需外部触发 | 定时任务不会自转 | 外部 cron/systemd/K8s 调 HTTP；或 Java 继续承担调度 | §2.4、`PORTING_REPORT` §6.6 |
| ⚠️5 | 固定 32 工作线程（`CM_WORKERS`），无 GC；长耗时外部调用会占满 worker | 并发模型不同，慢上游会整站排队 | 部署时按核数放大；外部调用必须设超时 | §2.5、§5.1 |
| ⚠️6 | 日期固定按 `+08:00`（Java 跟随 JVM 时区） | 部署到别的时区会不一致 | 容器内 `TZ=Asia/Shanghai`（compose 已设） | §2.6 |
| ⚠️7 | `BigDecimal` 按 double 最短形式输出（`1.10 → 1.1`）。本轮又多一处实证：`listByCarId` 回退分支把远程轨迹写成 `track_josn` 时，Java 的 fastjson2 会把 `"116.500"` 转成 BigDecimal 再原样写回 `116.500`，C++ 的 JSON 数值只有 double ⇒ 写成 `116.5`，**这串文本会落库** | 前端若按字符串比较会不同；导出另有 `*Str` 文本列 | 金额透传原始文本；`verify_list_by_car_id.py` 用一条 ⚠️ 断言把这个丢失钉住，别让它悄悄扩散 | §2.7 |
| ⚠️8 | ~~**不支持 chunked 请求体**（返回 411）~~ **已于 2026-11-07 补齐**：支持 `Transfer-Encoding: chunked`（chunk-ext + trailer），上限 200MB 与 Java 一致 | 无（已对齐） | — | §2.8 |
| ⚠️9 | 日志：非 Logback 逐字节格式，无 MDC/traceId 自动注入 | 日志采集格式需适配 | 显式传 traceId | §2.10 |
| ⚠️10 | **SQL 执行失败被降级成空结果**（Java 是 `BadSqlGrammar` → code 500）——模板导出路径已改成失败即抛，其余路径未统一 | "接口返回空"可能是真失败 | 查 `logs/carmonit.log` 的 `[WARN] Db - 查询失败` | §2.12 |
| ⚠️11 | Windows 本地开发机 `std::filesystem` 按 GBK 解释 UTF-8 路径（Java/JDK 无此问题） | 中文名文件读写会失败 | `cm::compat::fsPath/fsUtf8` 已在全部落盘点接入；Linux/Docker 不涉及 | §2.11 |
| ⚠️12 | 操作日志异步队列**有界**（5 万），Java 的 timer 队列无界 | 溢出丢日志并打本地错误，不改 | 刻意偏离，保内存 | §6.6 |
| ⚠️13 | `multipart` 上传类接口的 `oper_param` 记空串；JSON 请求体记"请求体本身"而非绑定后的实体（键序/未知键取舍可能不同） | 仅日志可读性 | §6.6 三条偏离已逐条说明 | §6.6 |
| ⚠️14 | 静态资源/前端：`config/static` 代替 classpath，无 swagger-ui / druid 控制台（Java 侧本来就 `denyAll`） | 运维入口缺失 | 用 `ENDPOINTS_INVENTORY.md`；`GET /health` 是 C++ 扩展 | §2.9、§5 |
| ⚠️15 | 无 Apache POI / Kafka / Elasticsearch / ShardingSphere / MinIO SDK / OSS SDK | 见 §4 未实现清单 | 逐条替代方案在 §5 表 | §5 |
| ⚠️16 | fastjson2 的**对象**写出器按字段名排序、**Map** 按容器序 —— C++ 的 `Json` 是 `ordered_json`，只会保留插入序，所以 `fastJsonCompact` 必须显式声明是哪一种（`pojoFieldOrder`）。`@Log` 的 `oper_param`/`json_result` 拿的是 `joinPoint.getArgs()`，到底是 POJO 还是 Map 取决于方法签名，本轮没逐条核，仍按插入序输出 | 日志里的键序可能与 Java 不同（POJO 入参那几处） | 已确认的三处 POJO 序列化（`queryLog` 的 `TrailInfo`、`track_josn` 的 `TrailBo` 列表、Forest 拍平里的嵌套 BO）显式传 `true`；其余维持现状，改动时按签名逐条判定 | §2.16、契约 35 |
| ⚠️17 | Forest 把空串查询参数渲染成**没有等号**的裸键名（`…&isQuery`），C++ 的 `buildQuery` 一律带等号（`…&isQuery=`）。`buildQuery` 同时服务 `postForm`，那里 `a=` 才是正确形态，所以没有改传输层 | Servlet 侧 `getParameter` 两种都返回 `""`，实测上游行为一致 | 只在出站 URL 的字面文本上不同；`verify_list_by_car_id.py` 断言的是"键照样带上" | §5.1、契约 36 |
| ⚠️18 | Spring 绑定失败（如 `carSnapShot?lon=abc`）的 `BindException` 文案模板照抄了 `Failed to convert property value of type 'java.lang.String' to required type 'java.math.BigDecimal' for property 'lon'`，但**子串没跟真实 Spring 5.3 逐字对拍**（本机跑不起 Java 侧） | 只有失败响应的 `msg` 文本；`code:500` 与 HTTP 200 的形态是对的 | 有 Java 环境时用 `lon=abc` 打一次原始应用对拍文案 | 契约 37 |

---

## 4. ❌ 未迁移的端点（当前 6 条；历史上按前置能力分组，分组标题里的条数是各自批次的快照）

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
| ~~`PUT /manager/suspicious/check`~~ ✅ | 已实现：校验 status≠"1" → **物理**删 check/`car_except_record` → 无车则插 `car_info` → 批量落库 → `check_status='1'` → 刷 Redis 车辆列表；返回 `AjaxResult.success("操作成功！",id)`；**`@PreAuthorize` 在 Java 里被注释掉**，没有补 |
| ~~`GET /manager/suspicious/listFileCarNo`~~ ✅ | 已实现：每行 `selectCarSuspiciousById` → 解析 `track_josn` → 三级回退几何；`total` 是行数、`escapedTypeName` 尾逗号都照抄 |
| ~~`GET /manager/suspicious/history/{id}`~~ ✅ | 已实现（同一套几何后处理，读的是 `car_suspicious_back`） |
| `GET /manager/suspicious/exportAbnormalPassage` | **docx** 模板：`WordExportUtil.exportWord07` + `ImageEntity` 图片嵌入 + S3 GetObject 取图 ⇒ 需 docx 填充能力 |
| ~~`POST /manager/suspicious/syncSuspiciousCarTask`~~ ✅ | 已实现：SHA1 签名校验 + Redis 白名单/车辆缓存 + `envehicletype→carVehicle` 硬编码映射 + 收费站/门架首末点提取 + `track_names` 拼接（设备段不判重、路线/路段段判重）+ 批量落库。签名脚本用 Python `hashlib` 独立算，不拿 C++ 输出自证 |

### C. GenController —— 7 条

| 端点 | 阻塞点 |
|---|---|
| `POST /tool/gen/importTable`、`PUT /tool/gen`、`GET /tool/gen/synchDb/{tableName}` | 需 `GenUtils.initTable/initColumnField`（类型→javaType/htmlType 映射表、`information_schema.columns` 读列）与 `validateEdit` 的树/子表校验分支 |
| `GET /tool/gen/preview/{id}`、`/download/{t}`、`/genCode/{t}`、`/batchGenCode` | 28 份 Velocity 模板渲染 + zip（zip 写出器本轮已为 xlsx 落地） |

### D. CarTrackInfoController —— 0 条（全部落地）

| 端点 | 状态 |
|---|---|
| `GET /manager/cartrackinfo/listByCarId` | ✅ 已实现：本地查询与 `listByCarByTime` 共用同一份 `carTrackQueryLocal`；本地**一行都没有**才回退 `carTrackQueryByCarNo`，回退命中时照抄那个"GET 却写库"的副作用（`removeRealData(请求车牌)` + `saveBatch(远程 tracks)`，无事务 ⇒ 删先提交）。验证走脚本自带的假上游（`CM_VEHICLEMONITOR_BASEURL` 指过去），47 项断言 |
| ~~`PUT /manager/cartrackinfo/changeTrailInfo`~~ ✅ | 已实现：`carQueryLogService.queryLog` 落日志 + 三级回退几何 + `trailDevCountBO`；`query_condition` 写的是 fastjson2 丢 null 的形态 |
| `GET /manager/cartrackinfo/carSnapShot` | ✅ 已实现：`stateType`/`pointUuid` 不齐就直接 `success()`（没有 `data` 键）；齐了把整个 `TrailBo` 拍平成 query string 打 `getByTrailBo`。拍平规则（声明序、null 省略、BigDecimal 保标度、空串也带上）是**实机抓 Forest 1.5.x 的请求行**钉下来的，见 §3 |

### E/F/G/H. 其余 7 条

| 端点 | 阻塞点 |
|---|---|
| `GET /base/geometry/getHenDa`、`/syncAllGeometry`、`/syncAllGeometry1` | Forest → GeoServer `http://36.200.20.14:7890/...`；签名是 `EncryptUtils.createSignature` 的 MD5 字典序拼接，**含 `append(publicStr)` 自拼接 quirk，必须逐字复刻**；两个 sync 是"先 `return success()` 再后台线程池跑"，失败不可见（§5.1） |
| `GET /base/snapshotflow/earliest-time` | Forest → `127.0.0.1:9901`；无 try/catch ⇒ 上游失败直接 500；`data` 在"日期串"与 `"暂无数据"` 之间切换 |
| `POST /manager/busstest/syncCurrentTrack` | **纯 DB+Redis**；返回 `void` ⇒ 成功是 200 空体；`isLocalhost=="local"` 时直接不执行 |

> ~~`POST /manager/carinfo/import`、`POST /manager/exceptrecord/import`~~ —— 已迁移（xlsx 读取器可用后落地，见 §2 契约 23–26 与 `scripts/verify_import.py` 的 61 项实机断言）。
> 另注：`POST /system/user/importData` 已在路由表里（未计作"未覆盖"），但它走的是另一套机制（`@Excel` 注解反查 + `updateSupport` 的部门/角色校验），目前仍返回**显式错误**而不是假成功。

### 小结：按"缺什么能力"重排（未迁移 6 条）

| 缺的能力 | 条数 | 端点 |
|---|---|---|
| **无（纯移植工作量）** | **1** | `busstest/syncCurrentTrack` —— 实现本身不难，难在它会把 `car_info` 整表刷成 `status='0', track_josn=NULL` 并重写 Redis 缓存，开发库上不能拿真实数据跑 |
| docx 模板填充 | 1 | `suspicious/exportAbnormalPassage` |
| GenUtils / Velocity + zip | 4 | `gen/preview/{*}`、`gen/download/{*}`、`gen/genCode/{*}`、`gen/batchGenCode`（要渲染 13 个 `vmplus/` 模板 + `HashSet` 的导入顺序 + deflate 打包） |

> "已注册、但只有降级/失败分支被验到"的那批不在这 6 条里：`file/*` 7 条缺真实 MinIO（`verify_sys_file.py` 需要 `fake_s3.py` + `logs/cfg_fake`）、`geometry/getHenDa`/`syncAllGeometry`/`syncAllGeometry1` 与 `snapshotflow/earliest-time` 缺真实 GeoServer/上游服务（`verify_henda.py` 用 `logs/cfg_stub`）。
> `cartrackinfo/listByCarId` 与 `carSnapShot` 这两条本轮**把成功分支也验到了**：`verify_list_by_car_id.py` 自带一个假上游，C++ 侧用 `CM_VEHICLEMONITOR_BASEURL` 指过去，因此远程返回、`track_josn` 回写、以及那个"GET 写库"的副作用都是可观察的。

> ~~xlsx 读取（INFLATE + sharedStrings）~~ —— 0 条：读取器已可用，`carinfo/import` 与 `exceptrecord/import` 已迁移。
> ~~`suspicious/listFileCarNo`、`suspicious/history/{id}`、`cartrackinfo/changeTrailInfo`~~ —— 已迁移（几何三级回退链，见契约 28–31）。本机既无 roadPath 也无腾讯服务，实测跑的是**降级路径**（最终落到本地 geometry 表拼接），与 Java 在同环境下的行为一致；两条出站分支只做到"签名/请求体拼串"级别的单测钉死。

两点修正性说明：
* ~~`listFileCarNo` / `history/{id}` / `changeTrailInfo` 取决于 Redis 开关 `sys_config:api_map`~~ —— 三条都已落地；值为 `"0"` 时走腾讯分支（本机不可达 ⇒ 降级），非 `"0"` 时走本地 roadPath（同样不可达 ⇒ 降级），最终都落在纯本地的 geometry 表拼接上，所以**响应形态与 Java 在本机环境下一致**，但两条出站分支本身仍未被真实服务验证过。
* `POST /system/user/importData` 已注册（因此不计入未覆盖），但它用的是 easypoi/`@Excel` 注解那一套，与 `ImportSysUtil` 的硬编码表头不是同一件事 —— 现在返回显式错误而不是假成功。

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
| `exceptrecord/import` 里 `initListThree()` 从未被调用 | `gzListThree` 也是 `initListTwo()` ⇒ 表头的第 2 行与第 3 行比的是**同一份**列名，那个看起来专为第 3 行准备的表定义是死代码。移植时不要"顺手接上" | `ManagerImportControllers.cpp`、`verify_import.py` |
| `isExitsTime` 判的是"区间有交集"而非文案说的"重复" | `out_time >= #{inTime} AND in_time <= #{outTime}`；且 `saveCarExceptRecord` 的返回值被导入循环丢弃 ⇒ "录入区间时间重复！"永远不会出现，那一行只是静默不写 | `verify_import.py` |
| `MyBatisPlusHandlerConfig.insertFill` 里 tenantId 判的是 `epsId == null` | epsId 已有值时 tenantId 就不填 —— 复制粘贴错误，照抄 | `saveCarExceptRecord` |
| `carinfo/import` 的 `doImport` 无 `@Transactional`，且插入前又重设一次 `createTime` | 注释还写着"创建的时间一样"，实际每行各取当前时间；失败时前面已插入的行不回滚 | `CarInfoServiceImpl:215` |
| `lxbh` 首点 roadCode 为 null 就永久锁死成 null | `if("".equals(lxbh) && !"".equals(roadCode))`：`roadCode==null` 时后者也是 true，于是 `lxbh=null`，之后 `"".equals(null)` 恒 false ⇒ 后面的有效路线编号再也进不来，响应里 `"lxbh":null` | `TrailGeometry`，`verify_trail_geo.py` 的缓存命中用例 |
| `listFileCarNo` 的 `total` 是当前页行数 | `getDataTable(rtnList)` 里 `new PageInfo(list)` 拿到的是普通 ArrayList ⇒ `total=pageSize`；`pageSize=1` 就报 1，不是数据库总数 | `verify_trail_geo.py` |
| `escapedTypeName` 结尾逗号不删 | 逐个 `bussName += label + ","` 后直接 set，没有 `deleteEnd`（同一段代码在别处都会删） | `verify_trail_geo.py` |
| `TrailDevList` 字段名首字母大写 | 声明成 `private List<TrailDevBO> TrailDevList;`，但 Jackson 从 getter 推导 ⇒ JSON 键是 `trailDevList`。输出成 `TrailDevList` 就是错的 | `TrailGeometry::trailDevCountBo` |
| `updateRedisList()` 缓存过滤后的列表、返回未过滤的全集 | 冷启动第一次与之后每次的 `raodTrailList` 可能不同。实测这两个差别不可观察（paths 为空的行本来就被跳过、lxbh 为空的行 trim 成 "" 永远匹配不到真实路线编号），C++ 按缓存那份实现 | `TrailGeometry::roadGeometryGroups` |
| `changeTrailInfo` 里 `trailInfo.setTrailList(josnList)` 是自我赋值 | `josnList` 本来就是从 `trailInfo.getTrailList()` 取的；照抄不改 | `CarTrackInfoController:312` |
| `check` 里算出来的 `escapedType` 没人用 | `escapedType.indexOf(addCheckType) > -1` 是**子串**判重（码 "1" 会因为已积累的 "10," 含 '1' 而被当成重复跳过；值为空串时 `indexOf("")==0` 永远跳过），拼完 `deleteEnd` 之后却把请求上的 `escapedType` 写进 updatebo —— 计算结果是死值，照抄不"接通" | `ManagerSuspiciousWriteControllers.cpp` |
| `check` 的两张表是**物理** delete，且排在可能 NPE 的循环之前 | `isExcept!="1"` 且 `checkList` 为 null 时：先删空 → for-each NPE → 500 → 靠 `@Transactional` 回滚。C++ 的 `Transaction` 析构默认回滚，所以正常返回路径必须逐个显式 commit，否则"500 之后旧行应该还在"这条就守不住 | `verify_suspicious_check.py` 的回滚用例 |
| `GET /manager/cartrackinfo/listByCarId` 是**读接口却写库** | 本地查空才回退远程，远程一有数据就 `redisCache.setCacheObject(car_history_trail+车牌)` + `removeRealData(请求车牌)` + `saveBatch(远程 tracks)`；且这条链路上没有 `@Transactional` ⇒ 删先提交，插一半失败也回不来。⚠️ 删的是**请求**车牌、插的是**远程返回**的车牌，两个值可以不一样 | `verify_list_by_car_id.py`（两条断言分别钉住"删请求车牌"和"插远程车牌"） |
| `listByCarId` 的回退判据是 `carlist.size() > 0`，不是展开后的 `rtnList` | `track_josn` 全为 NULL 的行进不了 `rows`，但照样算"有数据"⇒ 远程回退不触发，响应是 `rows:[], total:N` | `verify_list_by_car_id.py` 的 `QODER挂B` 夹具 |
| `carSnapShot` 的 `TrailBo` 是**外部接口的返回类型**，不是本项目实体 | 上游若回 `AjaxResult` 信封（大概率），fastjson2/Jackson 解不出任何 TrailBo 字段 ⇒ 响应 `data` 是 32 个全 null 的键，而不是报错。C++ 一致照抄 | `verify_list_by_car_id.py` 的"上游返信封"用例 |
| 远程轨迹写回 `track_josn` 用的是 **fastjson2** 文本（排序 + 丢 null），响应里的 `trailList` 用的是 **Jackson**（声明序 + null 全输出） | 同一个对象在同一次响应里出现两种序列化形态 | `verify_list_by_car_id.py` 两条键序断言 |

### C++ 侧自己埋的坑（移植时必须防复发）

| 条目 | 表现 | 处置 |
|---|---|---|
| `Db::lit("0")` 命中 `lit(bool)` 重载 | `const char*` → `bool` 是**标准转换**，优先级高于 → `const std::string&` 的用户定义转换，于是 `del_flag` 这类字面量被写成 `1`。实测 car_info 的 `del_flag` 就这么错了 | 加了 `lit(const char*)` 精确匹配重载；新代码传字符串字面量不会再掉进 bool |
| 生成器与库里 spec 不完全一致 | `car_info` 那段无条件的 `not exists (… group by …)` 与两处 `createInfo` 派生列是手工补进去的；生成器还表达不了（试过改成逐字照抄 WHERE，被 RuoYi 的 `<where>` 标签骗出 `" and >"` 这种垃圾，已回退） | 已在 `gen_crud_spec.py` 注释里写明；**不要盲目重新生成**，先 diff 再落地 |
| `syncSuspiciousCarTask` 签名三参数由调用方提供、无时间窗 | 可无限重放、可离线伪造 | §5.1、§4.5 |
| 出站 HTTP 失败时把**操作系统的错误文本**塞进异常 message | Windows 上 `FormatMessageA` 返回系统 ANSI 码页（中文机是 GBK），那串字节进到 `AjaxResult.msg` 后 `nlohmann::dump()` 按 strict 抛 `type_error.316` —— 而它正是在异常处理路径里抛的，没人再接 ⇒ `terminate` ⇒ **整个进程下线**（本轮实机扫尾时真把服务打死了，后面几个脚本连不上服务其实都是这个） | `Os.hpp::lastError()` 走 `FormatMessageW` + `WideCharToMultiByte(CP_UTF8)`；错误信封/401/404 三处序列化改成 `dumpLenient`（非法字节替换成 U+FFFD，照样应答）。新增的 `verify_list_by_car_id.py` 里"上游连不上"就是这条的回归位 |
| 以为 `JSON.toJSONString` 只有一种键序 | fastjson2 对 **POJO** 按字段名排序、对 **Map** 按容器序；`compactJson` 一开始无条件排序，把 `json_result` 的 `{msg,code}` 排成 `{code,msg}` | 改成调用方显式声明 `pojoFieldOrder`；是单测 `testOperLogAspect` 先抓到的（不是实机），说明错误信封这类"全局共用的序列化位"必须挂在单测上 |

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
| 轨迹远程分支 | `python scripts/verify_list_by_car_id.py 9991 "$TOKEN"` | 47 | pass=47 fail=0 | §4 D、契约 35–38、⚠️7/16/17/18（脚本自带假上游，需 `CM_VEHICLEMONITOR_BASEURL`） |
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
2. ~~**再补 INFLATE + xlsx 读取器**~~ ✅ 已完成：INFLATE 三种块类型对拍通过（根因是距离基值表抄成了长度表那一路，见 `Inflate.cpp` 顶部），xlsx 读取器已接进 `carinfo/import` 与 `exceptrecord/import`。剩下的是 `system/user/importData`（easypoi `@Excel` 注解那套，机制不同）与 easypoi 模板的版式复刻（⚠️3 仍在）。
3. ~~**S3 SigV4 客户端**~~ ✅ 已实现（7 条 SysFile 端点 + `verify_sys_file.py` 40 项对本地 fake S3 通过，fake_s3 用 Python 标准库独立重算签名）。⚠️ 仍未对**真实 MinIO** 验证过，只验到签名与协议层。
4. **统一 SQL 失败的降级语义**（⚠️10）：现在只有模板导出与新增的导入链路改成抛异常（`mustRun`），其余仍是"失败变空结果"，需要一轮全量改 + 回归。
5. `@Log` 已落地，但 `preview/genCode/download` 的 Velocity 渲染是纯增量工作（zip 已具备，deflate 也可用了）。
6. 混跑注意：`car_list`/`car_list_jc`/`car_warning_list` 两侧都不设 TTL，行为一致，但缓存新鲜度依赖对方的刷新任务；C++ 写的**非缓存**键仍是普通 JSON 文本（⚠️2），别让 Java 去读。
