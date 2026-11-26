# C++ 侧未完成迁移工作清单（排期基线 v3，基于 car-monit-cpp-local 分支真实代码）

> 生成日期：2026-11-07（v2 建立；v3 依据 `01-tech-stack-review.md` 增补架构与技术债条目）
> 迁移方向：Java（RuoYi 3.8.7 / Spring Boot 2.5.15 / Java 8）→ C++20（CMake + 自研框架）
> 代码位置：**仓库 `car-monit-cpp-local` 分支下的 `car-monit-cpp/` 子目录**（不在 master 工作区）
> 依据文档：`java-to-cpp-migration-prompt.md`；分支内 `FINAL_DIFFERENCES.md`（2026-11-04）、`COMPATIBILITY.md`、`PORTING_REPORT.md`、`ENDPOINTS_INVENTORY.md`（脚本自动生成）；**v3 新增：[`01-tech-stack-review.md`](./01-tech-stack-review.md)（2026-11-07 技术审阅，风险编号 R-1…R-22、待确认推断 U-1…U-8）**
> 用途：剩余工作的排期基线。所有状态判断均来自对分支代码与文档的实测，标注了证据来源。

> **v3 修订说明**：功能对齐清单（§4.1-4.9）基本沿用 v2 的真实代码判断，只对少数条目补充了评审发现的实现边界；
> 新增 **§1.4 架构与技术债快照**、**§4.10 架构与技术债工作项（TD-01…TD-17）**、**§5.2 架构与运维风险**、
> **§6 决策 D-05…D-07**、**§7 技术债轨（R0/R6）**。技术债轨与 Java 对齐轨**可并行**，互不阻塞。

---

## 0. 上一版结论的推翻与修正声明

v1（2026-11-07 上午）基于 master 工作区磁盘扫描得出"C++ 侧完全空白"，**该结论错误**，修正如下：

| # | v1 结论 | 实际情况 | 错误原因 |
|---|---|---|---|
| 1 | C++ 侧完全空白，仅 1 个提示词文件 | **代码在 `car-monit-cpp-local` 分支**，`car-monit-cpp/` 目录 351 个文件，实现覆盖 491/497 端点 | 只扫了 master 工作区，未查 git 分支 |
| 2 | 技术栈选型未定（8 项待拍板） | 全部已定且已落地：自研 Server/Router、自研 MySqlClient + CrudEngine、nlohmann ordered_json + fastjson2 兼容层、自研最小 OOXML、CMake + vendored 依赖 | 基于错误前提推断 |
| 3 | 全部 86 个工作项"未开始" | 大部分已完成并对拍验证；真实剩余工作集中在中间件运行时（Kafka/ES/Quartz/分表）、6 条端点、Excel 版式与若干横切件 | 同上 |
| 4 | 端点基线 501（我方 grep 口径） | 分支自动化脚本（`endpoint_coverage.py`）口径为 **497**；Go 侧自称 515。三个口径并存，需统一 | 统计方法不同，见 §3 |
| 5 | "701 个 Java 文件 / 75 Mapper XML" 等体量数据 | 仍然有效（master 工作区即 Java 源）；分支口径 Java 497 端点、234 条 `@Log`、59 个 CRUD 实体 | — |
| 6 | 交付物 D1-D7 全部缺失 | D1-D7 在分支上**全部已有雏形**（含 MIGRATION_GUIDE/README_CPP/COMPATIBILITY/QUICK_REFERENCE/tests/Dockerfile/compose/start 脚本） | 同上 |

---

## 1. 代码现状概览

### 1.1 分支与规模

| 项 | 值 |
|---|---|
| 分支 | `car-monit-cpp-local`（本地与 `origin` 同名分支均在） |
| 最新提交 | `b4e8c47` 2026-11-07 14:03 "feat(manager): 两条轨迹远程端点落地（listByCarId / carSnapShot），覆盖 489→491" |
| 报告基线 | `FINAL_DIFFERENCES.md` 生成于 2026-11-04（对应提交 `1bfe671`），其后有 3 个提交（+80 文件 / +11,661 行） |
| C++ 文件总数 | 351：`.hpp` 142 + `.cpp` 127 + `.py`(脚本) 37 + `.h` 7 + `.c` 4 + 文档 10 + 配置/构建/脚本若干 |
| 目录结构 | `include/cm` + `src/cm`（镜像 Java 包名）：`common` / `framework` / `web` / `system` / `base` / `flow`；另有 `tests`(11)、`scripts`(39)、`config`(2)、`third_party`(bcrypt + nlohmann) |

### 1.2 技术栈（选型已定，全部自研/vendored）

| 层 | 方案 | 证据 |
|---|---|---|
| Web 框架 | **自研** `Server/Router/HttpRequest/FileUpload/ExceptionMapper`（C++20，固定 32 工作线程，不依赖 Drogon/Paozhu） | `src/cm/framework/web/*`、CMakeLists 注释 |
| JSON/ID 契约 | nlohmann `ordered_json` + 自研 `JavaCollections::javaMapOrder`（复刻 HashMap 桶序）+ `FastJson2Compat`（POJO 字母序 / Map 容器序、`@type`、Long `L` 后缀归一） | 契约 1-4、23、35；单测 `testAjaxResultOrder/testR/testOperLogAspect` |
| DB 访问 | 自研 `MySqlClient`（socket）+ **spec 驱动 CrudEngine**（59 个实体声明式 CRUD spec，含 `<if>`/OGNL/`@TableLogic`/PageHelper 语义），特殊 SQL 手写 | `src/cm/framework/web/crud/CrudEngine.cpp`、`scripts/gen_crud_spec.py`、契约 9-12、20-25 |
| Excel/Word | 自研最小 OOXML：xlsx 读写（inline string，**无样式/合并单元格**）+ INFLATE/DEFLATE 自实现；**docx 未做** | `utils/Xlsx.hpp`、`ImportExcel.cpp`、⚠️3、契约 26 |
| 依赖管理 | **无 Conan/vcpkg**；bcrypt + nlohmann vendored 到 `third_party/`，SHA/HMAC/RSA-OAEP/INFLATE 全部自实现，"clone 即可构建"；系统可选 zlib | CMakeLists.txt 头注 |
| 构建/部署 | CMake ≥3.16、Debug/Release、ASAN 开关、单测 target；Dockerfile + docker-compose（TZ=Asia/Shanghai）+ start.sh/bat | CMakeLists、`config/` |

### 1.3 各层覆盖度矩阵（基于 ENDPOINTS_INVENTORY 491/497 + FINAL_DIFFERENCES 验证矩阵）

| 层 | 覆盖度 | 摘要 |
|---|---|---|
| 请求处理与路由 | **≈99%** | 491/497 端点已注册并路径匹配；C++ 另注册 564 路由（含 `/health` 等扩展）；CORS/RepeatSubmit/RateLimiter 未实现（Java 各仅 1 处使用，影响极小） |
| 序列化与契约 | **≈95%** | 信封/键序/日期三态/字段初值/继承/fastjson2 兼容均已对拍；缺口：Excel 模板版式、docx、`@Sensitive` 脱敏 |
| 数据访问与事务 | **≈90%** | 59 实体 SQL 真库 0 异常；事务 RAII 语义对齐；缺口：分表路由、跨月/视图维护/一致性增强服务、慢 SQL 拦截器 |
| 鉴权与安全 | **≈95%** | JWT(jjwt 0.9.1 兼容)/Redis 会话互通/anonymous 陷阱/权限语义/操作日志 234 条规则均已复刻；`@Sensitive`、限流、防重缺失 |
| 异步与定时 | **≈30%** | 异步操作日志队列有；**Kafka 消费、Quartz 调度运行时、6 个 `@Scheduled` 任务全缺**；CDC 控制器层已实现 |
| 外部中间件 | **≈60%** | Redis ✅、出站 HTTP ✅、S3 SigV4 ✅（仅对 fake S3 验证）；**Kafka/ES 客户端缺**；真实 MinIO/GeoServer/腾讯/roadPath 未验证 |
| 配置与启动 | **≈85%** | application.yaml 与 Java 逐块对应、启动脚本/compose//health 齐；日志非逐字节 Logback、无 MDC |
| 测试与文档 | **≈80%** | 单测 11 文件 / 514 断言；18 个 e2e 脚本（末次全跑 380 项通过，**末次提交后需整套复跑**）；D2-D4/D7 文档齐 |
| 监控与可观测 | **≈20%** | monitor 配置已解析但 **TraceId/MetricCollector/AlertEngine 无实现**；缓存/服务器监控端点已实现 |

> 注：以上是**对 Java 的行为覆盖度**，不含架构健康度；后者见 §1.4 与 §4.10。

### 1.4 架构与技术债快照（来自 `01-tech-stack-review.md`）

| 维度 | 评审结论 | 对应工作项 |
|---|---|---|
| HTTP 内核 | 阻塞线程池 32 worker；无 TLS/HTTP2、无限流（需 nginx）；**队列/慢速滴灌/整文件读内存已自修**（`5cf8294`/`5c5c7dc`/`d619d49`），chunked 已支持（`05fe02c`） | TD-01、TD-11、TD-17 |
| JSON 层 | **保留**：HashMap 桶序/fastjson2 兼容/lenient dump 是契约必需；BigDecimal 经 double 是已知偏离（决策保留）；空/非法输入崩溃已修（`7baba72`） | SC-09、TD-10、TD-18 |
| DB 访问 | CrudEngine/Spec **保留**；`MySqlClient` 手写文本协议无预处理语句，注入防护靠 `Db::lit` 纪律，建议换 libmysqlclient | TD-05、TD-15 |
| Redis | 功能对齐，但**单连接 + 全局 mutex** 是 32-worker 之后的第二并发瓶颈 | TD-06 |
| 日志 | **已改异步**（单后台线程 + 有界队列，`4a0f2a8`）；仍建议 spdlog + 薄适配层（LOG_* 宏不变） | TD-07 |
| 出站 HTTP | **TLS 已补**（`2e86447`）；Forest BackOffRetryer 已复刻（`c478d9d`，非 GET 默认不重试） | TD-08、TD-09 |
| Excel/Word | xlsx 数据面可用、版式缺失；docx 无成熟 C++ 库，需自研 | SC-04、SC-05、D-03 |
| 保留资产（不建议动） | 信封/异常映射、JWT 密钥 quirk、crypto/Inflate（有 OpenSSL 对拍）、S3 SigV4（有 fake S3 对拍） | — |
| 无数据支撑的推断 | 吞吐量级、慢上游雪崩形态、Redis 排队量级、MySQL auth 组合（YAML 边界已关：`67dd8f7`） | TD-11、TD-13 |

---

## 2. 已选型结论（原 v1 "待拍板" 项的重新判定）

| v1 编号 | 决策项 | 结论 | 备注 |
|---|---|---|---|
| B-01 | Web 框架 | **已定：自研 Server/Router**（无第三方框架，32 固定线程） | 已运行；⚠️5 长耗时外调会占满 worker，需外调超时纪律 |
| B-02 | DB 访问 | **已定：自研 MySqlClient + CrudEngine spec**（声明式 spec 生成 SQL + 手写特殊 SQL） | `verify_generated_sql` 59 实体真库 0 异常 |
| B-03 | JSON/ID | **已定：nlohmann ordered_json + javaMapOrder + FastJson2Compat** | 桶序/POJO 字母序/Map 序三态显式区分；BigDecimal 按 double 最短形式（⚠️7，遗留精度风险） |
| B-04 | Excel/Word | **部分定：xlsx 自研最小 OOXML（数据一致、版式不复刻）；docx 未做** | ⚠️3；`exportAbnormalPassage`（docx+图片+S3）整条阻塞 |
| B-05 | Quartz | **已定：不实现调度器**，`sys_job` CRUD/changeStatus 对齐，`PUT /monitor/job/run` 显式返回未实现 | 调度需外部 cron/systemd/K8s 或 Java 承担 |
| B-06 | Velocity | **未定→事实上未做**：4 条 gen 端点阻塞（preview/download/genCode/batchGenCode，需 13 个 vmplus 模板 + zip） | zip/deflate 能力已具备，属纯增量工作 |
| B-07 | Kafka/ES/分表启用范围 | **代码给出答案：三者均未实现**（Kafka/ES 无客户端，分表仅配置解析无路由） | 是否补齐待业务确认（见 §6 决策） |
| B-08 | Java "保持无效"行为 | **已系统性处理**：FINAL_DIFFERENCES §5 列出约 25 条"照抄的 Java 缺陷"防顺手修正 | 如 anonymous 403、find_in_set 参数方向、恒达 MD5 自拼接等 |

---

## 3. 端点口径说明（需统一）

| 口径 | 数值 | 来源 |
|---|---|---|
| 分支自动化脚本 | Java **497** / C++ 匹配 **491** / C++ 注册路由 564 | `scripts/endpoint_coverage.py` + `ENDPOINTS_INVENTORY.md`（随代码更新，推荐作为活基线） |
| v1 文档 grep 口径 | 501（admin 473 + quartz 13 + generator 15） | v1 附录 A 的正则统计（不含方法级 `@RequestMapping` 差异） |
| Go 侧文档 | 515 | `car-monit-go/docs/PROGRESS.md`（可能含重复注册/api 层） |

**建议**：以分支的 `gen_inventory.py` 产物为唯一活基线；差异 4 条逐一定位后关闭。

**当前 6 条未迁移端点**（ENDPOINTS_INVENTORY 尾部 ❌）：

| 端点 | 阻塞能力 |
|---|---|
| `GET /tool/gen/preview/{*}` | Velocity 模板渲染（13 个 vmplus 模板 + HashSet 导入序） |
| `GET /tool/gen/download/{*}` | 同上 + zip 打包（zip 已具备，属增量） |
| `GET /tool/gen/genCode/{*}` | 同上 |
| `GET /tool/gen/batchGenCode` | 同上 |
| `GET /manager/suspicious/exportAbnormalPassage` | docx 模板填充 + ImageEntity 图片嵌入 + S3 取图 |
| `POST /manager/busstest/syncCurrentTrack` | 无能力缺口（纯 DB+Redis），但会把 `car_info` 整表刷平，开发库不能拿真实数据跑 |

---

## 4. 未完成工作清单（按层，v3）

状态图例：`✅ 已对齐`（代码在且有对拍证据）/ `🟡 部分完成` / `❌ 缺失` / `❓ 待验证`。
优先级：P0 阻塞验收或一致性风险；P1 主链路补齐；P2 低影响。

### 4.1 语言与运行时层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| LW-01 | 工程骨架（CMake/src/include/tests/configs） | ✅ 已对齐 | CMakeLists.txt、cm 包结构镜像 Java | — |
| LW-02 | 心智模型/迁移手册（D2） | ✅ 已对齐 | `MIGRATION_GUIDE.md`、`PORTING_GUIDE.md`（内容完整度建议抽查） | P2 |
| LW-03 | 线程与上下文模型 | 🟡 部分完成 | 32 固定 worker（⚠️5）；无 TraceId 上下文（⚠️9） | P2 |
| LW-04 | 异常与错误码体系 | ✅ 已对齐 | `ExceptionMapper/Errors`、契约 17、非法 JWT→真 500 | — |
| LW-05 | 通用工具层 | 🟡 部分完成 | utils 20+ 组件已对拍；`SnowflakeIdUtil`（Java 分表 big_id 用）未见对应物 | P1（随分表决策） |

### 4.2 请求处理与路由层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| RT-01 | 501/497 端点对齐 | 🟡 491/497 | `ENDPOINTS_INVENTORY.md`；剩 6 条见 §3 | P0 |
| RT-02 | Spring 参数绑定语义 | ✅ 已对齐 | 契约 37；BindException 文案未逐字对拍（⚠️18） | P2 |
| RT-03 | PageHelper 分页语义 | ✅ 已对齐 | 契约 12 | — |
| RT-04 | 文件上传/下载/静态资源 | ✅ 已对齐 | 契约 19；SysFile 7 条经 fake S3 验证；静态文件整读内存（TD-12）、入站无 TLS（TD-01） | — |
| RT-05 | CORS 过滤器 | ❓ 待验证 | 未见实现；Java 有 CorsFilter（放行配置需对齐） | P2 |
| RT-06 | `@RepeatSubmit` 防重 | ✅ 已对齐 | `cm::web::checkRepeatSubmit`；key/value/TTL/响应形态逐条对齐；单测 `testRepeatSubmit`（提交 `514d719`） | — |
| RT-07 | `@RateLimiter` 限流 | ✅ 不适用 | **Java 0 处使用**（仅 `annotation/RateLimiter.java` + `RateLimiterAspect` 定义，全仓无 `@RateLimiter` 命中）⇒ C++ 不实现即一致（COMPATIBILITY §4-14） | — |
| RT-08 | XSS 过滤 | ❓ 待验证 | `cm.xss.*` 配置已解析，拦截实现未见 | P2 |

### 4.3 序列化与契约层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| SC-01 | 响应信封/键序/空值 | ✅ 已对齐 | 契约 1-4、35；单测钉住 | — |
| SC-02 | 日期三态/时区 | ✅ 已对齐 | 契约 5、⚠️6（固定 +08:00，容器已设 TZ） | — |
| SC-03 | Excel 导出（数据面） | ✅ 已对齐 | 契约 19、`verify_template_export` 22 项 | — |
| SC-04 | **Excel 模板版式**（标题行/两级表头/合并单元格/样式） | ❌ 缺失 | ⚠️3；自研 OOXML 无样式能力 | P1 |
| SC-05 | **docx 模板填充** | ❌ 缺失 | `exportAbnormalPassage` 阻塞（§3） | P1 |
| SC-06 | easypoi `@Excel` 注解导入（`/system/user/importData`） | 🟡 部分完成 | 已注册但返回显式错误（§4 注）；机制与 ImportSysUtil 不同 | P2 |
| SC-07 | `@Sensitive` 脱敏序列化 | ✅ 不适用 | **Java 0 个字段使用**（仅注解 + `SensitiveJsonSerializer` 定义）⇒ 不实现即一致（COMPATIBILITY §4-14） | — |
| SC-08 | Redis 缓存互操作（fastjson2 WriteClassName） | ✅ 已对齐 | 契约 23、⚠️2（C++ 自写非缓存键仍普通 JSON）；`login_tokens:` 已双向互读（`e17b056`） | — |
| SC-09 | BigDecimal 精度保真 | 🟡 已知偏离（**决策：保留**） | ⚠️7：`116.500→116.5` 文本会落库；结论与影响面写入 `MIGRATION_GUIDE §9-⑪`（`8d10607`） | P1（金额链路） |

### 4.4 数据访问与事务层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| DA-01 | 59 实体 CRUD spec + 特殊 SQL | ✅ 已对齐 | `verify_generated_sql` 真库 0 异常；契约 9-12、20-25；注入防护依赖 `Db::lit` 纪律（TD-05） | — |
| DA-02 | 事务语义 | ✅ 已对齐 | 契约 27、`Transaction` RAII + 显式 commit；`verify_flow_approval` 27 项 | — |
| DA-03 | **ShardingSphere 分表等价**（卡口流水按月 / 费用记录按日） | ❌ 缺失 | `AppConfig.cpp:222-224` 仅解析配置；spec 中无 `ods_rt_szdn_snapshot_flow` 主表路由 | P1（待决策，见 §6） |
| DA-04 | 跨月查询/并行查询/视图维护/一致性服务 | ❌ 缺失 | Java `base/service/{enhanced,query,consistency}` 无 C++ 对应 | P1（依赖 DA-03 与调度） |
| DA-05 | `SqlLogInterceptor` 慢 SQL | ❌ 缺失 | monitor 配置已解析，拦截器无实现 | P2 |
| DA-06 | SQL 失败降级语义统一 | 🟡 部分完成 | ⚠️10：仅模板导出与导入链路改抛异常，其余"失败变空结果" | P0（一致性风险） |
| DA-07 | 分库初始化（分区 SQL/种子数据） | ❓ 待验证 | 分支无 sql/ 目录；`verify_generated_sql` 需真库 | P1 |

### 4.5 异步与定时层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| AS-01 | 异步操作日志队列 | ✅ 已对齐 | 契约 16、⚠️12/13（有界 5 万、multipart 记空串） | — |
| AS-02 | **Kafka 消费链路**（V2 批量消费 / MANUAL_IMMEDIATE / DLQ 生产） | ❌ 缺失 | grep 全仓无 Kafka 客户端；仅 `AppConfig` 解析 bootstrap-servers | P0（快照流主链路） |
| AS-03 | **Quartz 调度运行时** + 6 个 `@Scheduled`（分区维护/快照同步/分表/视图维护） | ❌ 缺失 | ⚠️4；`job/run` 显式未实现 | P0（依赖外部调度决策） |
| AS-04 | CDC 后端（CdcSyncService/RetryTask/DeadLetterQueue） | 🟡 部分完成 | `CdcController` 8 端点 ✅；Kafka 驱动源缺失 | P1（依赖 AS-02） |
| AS-05 | 幂等键（`snapshot:flow:idempotent_`） | ❓ 待验证 | Java yml 有；C++ AppConfig/实现未确认 | P1（依赖 AS-02） |

### 4.6 外部中间件层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| MW-01 | Redis 客户端与会话互通 | ✅ 已对齐 | 契约 14-15、23；`verify_import` 缓存断言；单连接全局互斥为并发瓶颈（TD-06） | — |
| MW-02 | **Elasticsearch 客户端**（snapshot-flow 索引） | ❌ 缺失 | 仅 AppConfig 解析 host/port/index | P1（待决策） |
| MW-03 | S3/MinIO 客户端 | 🟡 部分完成 | SigV4 实现 + fake S3 40 项通过；**真实 MinIO 未验证** | P0 |
| MW-04 | 出站 HTTP（Forest 等价） | ✅ 已对齐 | 契约 36-38；`verify_list_by_car_id` 47 项（含假上游）；出站 TLS 已补（`2e86447` vendored mbedTLS + cacert），BackOffRetryer 已复刻（`c478d9d`，非 GET 默认不重试为有意收紧，COMPATIBILITY §5.1） | — |
| MW-05 | 恒达 GeoServer / roadPath / 腾讯地图真实验证 | ❓ 待验证 | 签名单测钉住；仅 stub/降级路径实测 | P1 |
| MW-06 | 阿里云短信（AliyunSMSUtil/SMSService） | ❌ 缺失 | grep 无落点（Java 侧配置项均为空值，可能未启用） | P2（待裁剪决策） |
| MW-07 | vehicleMonitor 联动（9902） | ✅ 已对齐 | listByCarId/carSnapShot 远程分支已实测（假上游） | — |

### 4.7 配置与启动层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| CF-01 | application.yaml 1:1 | ✅ 已对齐 | 与 Java yml 逐块对应 + cm 扩展段 | — |
| CF-02 | 环境变量覆盖（CM_*） | 🟡 部分完成 | `CM_SERVER_PORT`/`CM_VEHICLEMONITOR_BASEURL` 已用；覆盖面未系统化 | P2 |
| CF-03 | 日志格式/MDC | 🟡 已知偏离 | ⚠️9：非逐字节 Logback、无 traceId 注入；同步锁写盘在请求路径（TD-07） | P2 |
| CF-04 | 启动闭环（脚本/compose//health/Dockerfile） | ✅ 已对齐 | start.sh/bat、Dockerfile、docker-compose.yml | — |
| CF-05 | D3 上手文档（README_CPP）/D7 速查表 | ✅ 已对齐 | 两文件均在（内容随剩余工作更新） | P2 |
| CF-06 | 构建可复现（第三方机器从零构建） | 🟡 部分完成 | MSVC `/utf-8 /DNOMINMAX` 已内置 `CMakeLists.txt`（`d3e85a9`），换全新 build 目录可构建；Linux/CI 未验证 | P1 |

### 4.8 测试与文档层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| TS-01 | 单元测试 | ✅ 已对齐 | 11 文件 / 514 断言调用点 | — |
| TS-02 | 端到端实机断言 | 🟡 需复跑 | 18 脚本；末次 14 脚本 380 项通过；**末次 3 提交（compactJson 排序开关/FormatMessageW/dumpLenient）后 MySQL/Redis 下线未复跑** | **P0** |
| TS-03 | 6 条未迁移端点的测试 | ❌ 缺失 | 随端点补齐 | P1 |
| TS-04 | 真实 MinIO/GeoServer/上游验证 | ❌ 缺失 | 仅 fake/stub | P1 |
| TS-05 | 文档 D2/D4 与代码同步 | 🟡 部分完成 | FINAL_DIFFERENCES 停在 11-04（462/497 快照），HEAD 已 491 | P1 |

### 4.9 横切关注点层

| 编号 | 工作项 | 状态 | 证据 | 优先级 |
|---|---|---|---|---|
| XC-01 | JWT/Token/会话/anonymous 陷阱 | ✅ 已对齐 | 契约 13-14、§5 缺陷清单 | — |
| XC-02 | `@PreAuthorize` 权限点 | ✅ 已对齐 | INVENTORY 含权限列；登录/权限失败形态对齐 | — |
| XC-03 | `@Log` 操作日志（234 条规则） | ✅ 已对齐 | 契约 16；`verify_operlog` 18 项 | — |
| XC-04 | `@DataScope` 数据权限 | ❓ 待验证 | SysRole/SysUser/CrudSpec 有 dataScope 落点，覆盖面未核对 Java 159 处事务/数据权限全量 | P2 |
| XC-05 | **TraceId/MetricCollector/AlertEngine 监控埋点** | ❌ 缺失 | 仅 AppConfig 解析阈值；无埋点实现 | P1（Java 端 monitor.enabled=true） |
| XC-06 | 登录日志/在线用户 | ✅ 已对齐 | monitor 5 控制器齐 | — |
| XC-07 | i18n 文案（messages.properties） | ✅ 等价 | 真实调用 8 处、仅 1 份 `i18n/messages.properties`（无其它 locale），C++ 硬编码文案与默认 bundle 逐字相同 ⇒ `?lang` 无行为差异（COMPATIBILITY §4-15，`8d10607`） | — |
| XC-08 | 静态资源/swagger/druid | ✅ 有意缺失 | ⚠️14（Java 本来 denyAll）；`GET /health` 为 C++ 扩展 | — |

### 4.10 架构与技术债层（v3 新增，来自 `01-tech-stack-review.md`）

> 说明：本节条目**不属于 Java 行为对齐缺口**，而是自研栈的健壮性/并发/可维护性债。
> 评审给出的"保留 / 替换 / 混合"建议已折算为工作项；`R-*` 为评审报告的风险编号，`U-*` 为无法从代码确认的推断编号。

| 编号 | 工作项 | 状态 | 依据（代码/文档证据） | 优先级 | 依赖 |
|---|---|---|---|---|---|
| TD-01 | **nginx 前置**：TLS 终止、慢连接防护、限流、大文件/请求体上限、超时统一 | 🟡 部分完成（代码侧已加固） | 入站 TLS/限流/统一上限仍需 nginx；连接队列（`5cf8294`）与 slowloris（`5c5c7dc`）已在 Server 内修掉 | **P0** | 无（零代码改动） |
| TD-02 | Server 内部连接队列改有界 + 过载返回 503（对齐 Tomcat accept-count 语义） | ✅ 已实现 | 上限 `max(workers*2, 100)`，满则 close + `queue_overflow_` 计数（首次/每 1000 次 WARN）；`5cf8294` | P1 | — |
| TD-03 | 请求读超时分层：header / body / keep-alive 独立超时，防慢速滴灌 | ✅ 已实现 | 每请求 `steady_clock` 整体 60s 截止（`armDeadline` + `readLine/readExact(deadline)`）；头部读完恢复 body 空闲超时；`5c5c7dc` | P1 | — |
| TD-04 | chunked 请求体行为统一（按承诺返回 411，或修正 ⚠️8 文档） | ✅ 已实现 | chunked 解码 + chunk-ext + trailer，上限 200MB；`parseChunkSizeLine` 单测；⚠️8 与注释同步（`05fe02c`） | P2 | — |
| TD-05 | **MySqlClient 协议层替换**：libmysqlclient/MariaDB（COM_STMT + TLS），`MySqlConnection` 接口与池保留；CMake 可选依赖 + 自研回退 | ❌ 未开始 | `Db.hpp` 自述"文本协议 + 手工转义"；注入防护全靠 `Db::lit` 纪律（R-8）、协议长尾与无 TLS 到库（R-9） | P1 | DA-01（回归基线） |
| TD-06 | **Redis 客户端替换**：hiredis + 连接池（3-8 连接），保持 `RedisClient` API 形状 | ❌ 未开始 | `RedisClient` 单连接 + 全局 `std::mutex`，32 worker 全部串行（R-16） | P1 | SC-08（缓存互操作回归） |
| TD-07 | **Logger 替换**：spdlog + `LOG_*` 宏薄适配，异步 sink 出请求路径 | 🟡 异步已做 | 单后台线程 + 8192 有界队列 + 20% 丢弃水位 + dropped 计数 + shutdown 排空（`4a0f2a8`）；未换 spdlog、仍无 MDC/traceId（⚠️9） | P2 | CF-03 |
| TD-08 | **出站 HttpClient 支持 TLS**（https 上游），失败边界与 Forest 对齐 | ✅ 已实现 | vendored mbedTLS 3.6.2 + cacert.pem，强制证书链/主机名校验，真实站点握手通过（`2e86447`） | P1 | MW-05 |
| TD-09 | Forest `BackOffRetryer`（retry-count 2）语义核对与复刻 | ✅ 已实现 | `HttpOptions.maxRetryCount=2`、间隔封顶 1s、异常与非 2xx 都重试；非 GET 默认不重试（有意收紧）；`testRetry` 三条路径（`c478d9d`） | P1 | — |
| TD-10 | **BigDecimal 文本透传规范**：金额/标度字段禁止走 double，禁止 `116.500→116.5` 落库 | 🟡 已知偏离（**决策：保留**） | ⚠️7、SC-09；结论/影响面/验收基线写入 `MIGRATION_GUIDE §9-⑪`（`8d10607`），金额链路如需保真另立十进制类型 | P1 | 无 |
| TD-11 | **压测与容量基线**：RPS、P95/P99、慢上游雪崩形态、Redis 排队量级 | ❌ 无数据 | 评审 U-1/U-2/U-5：仓库无任何压测数据 | P1 | TD-01、TD-06 |
| TD-12 | 静态文件流式化（Range/ETag/sendfile），避免整文件读入内存 | ✅ 已实现 | `ApiResponse.file_path` + `file_size` 写 Content-Length，64KB 分块 `writeAll`；Range/ETag 仍无（`d619d49`） | P2 | — |
| TD-13 | MySQL auth 组合矩阵验证（native / caching_sha2 fast / full-RSA） | 🟡 部分完成 | 2026-11-08 用全新 8.0.30 临时实例复跑 27/27（24 矩阵 + 3 基准）PASS；仍只覆盖 native 一种 auth 组合 | P2 | TD-05 |
| TD-14 | 文档与注释一致性巡检（Jwt.hpp 18 vs 19 字节、chunked 411、reason phrase 表） | ✅ 已实现 | `Jwt.hpp` 改 19 字节（`fa5e1c9`）、chunked 文档与 ⚠️8 同步（`05fe02c`）、reason phrase 全表 100-505（`a6ec459`） | P3 | — |
| TD-15 | spec"生成 + 手改"双轨流程文档化：何时安全重生成、如何 diff、手工补丁清单 | ✅ 已实现 | `MIGRATION_GUIDE §5.7` 写入同步流程 + `scripts/audit_projection.py` 修三处漏判（`9ad648b`） | P1 | — |
| TD-16 | Yaml 解析能力边界记录（锚点/多行/嵌套列表不支持），配置复杂化前先换 yaml-cpp | ✅ 已实现 | `parse(text, warnings)` 检测锚点/别名/块标量/多文档/Tab/重复键，`AppConfig` 汇总 `LOG_WARN`（`67dd8f7`）；边界写入 MIGRATION_GUIDE | P3 | — |
| TD-17 | HTTP 协议边界测试：keep-alive、头解析健壮性、状态码 reason phrase、请求体上限 | 🟡 部分完成 | 新增 chunk-size / chunked 请求体 / 请求整体截止 / 重试三条路径单测；keep-alive 与畸形头仍未系统覆盖 | P2 | — |
| TD-18 | **JSON 空/非法输入触发进程级崩溃**（nlohmann `__fastfail` 0xC0000409） | ✅ 已实现 | `parse_json` 改 `Json::accept` 预检后抛 `JsonParseException`（`7baba72`）；影响所有 Redis/JSON 读路径 | **P0** | — |

---

## 5. 与 Java 侧相比最明显的缺口（按风险排序）

### 5.1 功能对齐缺口

1. **Kafka 快照流消费链路整段缺失**（AS-02/AS-04/AS-05）：topic `ods-rt-szdn-snapshot-flow` 的批量消费、手动 ack、DLQ、幂等键、CDC 驱动源——C++ 侧只有 CDC 的 REST 管理端点。这是 Java 侧每日 50 万增量的数据入口，缺失意味着 C++ 无法独立承接实时数据面。
2. **定时面整体缺失**（AS-03）：无 Quartz 运行时、无 `@Scheduled`（分区维护/快照同步/分表/视图维护 6 处）。当前靠外部 cron 的运维决策兜底，但 6 个任务本身一个都没写。
3. **分表（ShardingSphere 等价）缺失**（DA-03/04）：配置解析了但没有路由实现；卡口流水主表（按月 2025-2099）与费用记录（按日）的读写都未处理，跨月查询/并行查询等增强服务随之缺失。
4. **Elasticsearch 缺失**（MW-02）：`snapshot-flow` 索引的写入/查询无实现。
5. **代码生成器收尾**（§3 的 4 条 gen 端点）：Velocity 渲染能力未做，zip/deflate 已具备，属纯增量。
6. **docx 导出**（1 条端点）：模板填充 + 图片嵌入能力空白。
7. **Excel 版式复刻**（⚠️3）：数据正确但无标题行/合并单元格/样式，对外观敏感的报表会与 Java 产物不一致。
8. **监控埋点**（XC-05）：Java `monitor.enabled=true` 的慢请求/慢 SQL/告警链路在 C++ 是空配置。
9. **验证欠账**：末次 3 提交后 e2e 整套未复跑（TS-02，P0）；真实 MinIO/GeoServer/腾讯/roadPath 从未真实验证；SQL 失败降级语义未统一（DA-06）。

### 5.2 架构与运维风险（非 Java 差异，v3 新增）

1. **入站仍无 TLS**：`Server` 不支持 TLS/HTTP2，生产部署必须由 nginx 兜住（TD-01）。**出站 TLS 已补齐**（`2e86447`，vendored mbedTLS + 强制校验证书链/主机名），腾讯地图等 https 上游已可达。
2. **过载保护**：内部连接队列已改有界（`5cf8294`）、slowloris 由每请求整体 60s 截止挡住（`5c5c7dc`）；**仍无限流**，异常流量只能靠 nginx（TD-01/TD-11）。
3. **并发天花板由 Redis 决定**：单连接 + 全局 mutex，每请求至少 1 次串行往返（R-16）；换 hiredis + 小池是最便宜的一次性提速（TD-06）。
4. **注入面靠纪律**：文本协议无预处理语句，所有值必须走 `Db::lit`（R-8）；换 libmysqlclient 是结构性消除，而不是"再加强 review"（TD-05）。
5. **金额精度与落库文本**：BigDecimal→double 会改写 `116.500→116.5` 并落库（R-6）。**已决策保留**（理由/影响面/验收基线见 `MIGRATION_GUIDE §9-⑪`），金额链路若要求逐字节保真需另立十进制类型（TD-10）。
6. **能力无数据**：吞吐/延迟/雪崩形态/Redis 排队/协议 auth 组合全部缺实测（U-1/U-2/U-5/U-7），无法定量验收（TD-11/TD-13）。

---

## 6. 剩余待确认决策（7 项）

| 编号 | 问题 | 背景 | 建议 |
|---|---|---|---|
| D-01 | Kafka/ES/分表/CDC 是否要在 C++ 侧补齐 | 三者代码均缺；若 Java 侧长期保留数据面，C++ 可只做查询面 | 按"部署形态"拍板：C++ 独立承接 → P0 补齐；混跑 → 降级 P2 并在 COMPATIBILITY 记录 |
| D-02 | 调度归属 | Quartz 运行时未做；`job/run` 显式未实现 | 外部 cron 触发 HTTP（⚠️4 已建议）或补齐 6 个任务本体 |
| D-03 | Excel 版式/docx 是否要求复刻 | 数据一致已达成，版式/样式是显式偏离 | 对外报表要求高 → 补模板渲染（工程量较大）；否则维持 ⚠️3 记录 |
| D-04 | 短信/脱敏/限流/防重/i18n 等低频件 | 实测口径：脱敏 **0 处**、限流 **0 处**、防重 **1 处（已实现）**、i18n **8 处但只有 1 份中文 bundle**、短信配置为空 | 已按"照抄 Java 行为"处理：0 处的不实现、1 处的补齐、i18n 硬编码等价；结论写入 COMPATIBILITY §4-14/15/16，不再挂账 |
| D-05 | **协议基础设施是否换成熟库**（MySQL / Redis / 日志） | 评审结论：可换且收益为正；但"clone 即可构建"是 CMakeLists 的显式承诺 | 建议"可选依赖 + 自研回退"：`find_package` 命中则用 libmysqlclient/hiredis/spdlog，否则回退；先做 TD-05/TD-06 两项，TD-07 后置 |
| D-06 | **入站 TLS 与过载保护由谁承担**（nginx vs 自研 Server 增强） | Server 无 TLS/HTTP2、无限流；队列与分层超时已在 Server 内补齐（TD-02/03 已完成） | 建议 nginx 前置作为生产默认（TD-01，零代码） |
| D-07 | **性能验收口径**（目标 RPS / P95 / 并发 / 慢上游容忍） | 当前无任何压测数据，无法判断 32 worker + 单 Redis 连接是否够用 | 先给业务量级（日活/峰值 QPS），再按 TD-11 压测；未定量前不承诺容量 |

---

## 7. 建议执行顺序（v3，双轨并行）

| 批次 | 轨道 | 内容 | 退出标准 |
|---|---|---|---|
| **R0（立即）** | 技术债 | TD-01 nginx 前置 + TD-11 压测基线（先拿业务量级，见 D-07）；TD-14 文档巡检可随手做 | nginx 承接 TLS/慢连接/限流；拿到一组 RPS/P95 基线数字 |
| R1（立即） | 对齐 | 依赖服务拉起后**整套复跑 14+ e2e 脚本**（TS-02）；统一端点口径 497/501/515 | 全绿 + 口径基线唯一化 |
| R2 | 对齐 | DA-06 SQL 失败语义统一 + 真实 MinIO/外部服务验证（MW-03/05） | 失败路径行为与 Java 一致；真实依赖 1 轮实测 |
| R3 | 对齐 | 按 D-01/D-02 决策补齐 Kafka/CDC 驱动 + 调度任务（或书面裁剪） | 快照流一条消息端到端落库可复现 |
| R4 | 对齐 | gen 4 端点（Velocity+zip）+ docx 1 端点（按 D-03） | 497/497；INVENTORY 更新 |
| R5 | 对齐 | 监控埋点（XC-05）+ 其余 P2 项 + 文档同步（TS-05） | COMPATIBILITY/FINAL_DIFFERENCES 与 HEAD 一致；D-04 裁剪项落账 |
| **R6（与 R2-R5 并行）** | 技术债 | TD-05 libmysqlclient、TD-06 hiredis+池、TD-08 出站 TLS、TD-10 金额规范、TD-15 spec 流程；随后 TD-02/03/12/17、TD-07、TD-13、TD-16 | 每替换一项即跑全量 e2e + `verify_generated_sql` 回归；TD-05/TD-06 须在上线前完成或书面接受风险 |

> 轨道关系：R0/R6 是**独立技术债轨**，与 R1-R5 的 Java 对齐轨无代码冲突（R6 只动 `framework/*` 与适配层）。
> 唯一交汇点是 TD-08：它同时是 MW-05（腾讯 https）验证的前置，建议排在 R2 之前。

---

## 附录 A：核实方式（全部只读）

```
git branch -a / status            # 分支确认：car-monit-cpp-local；工作区保持 master 未动
git log -3 car-monit-cpp-local    # 最新提交 b4e8c47 2026-11-07
git ls-tree -r car-monit-cpp-local -- car-monit-cpp   # 351 文件清单与结构
git show car-monit-cpp-local:car-monit-cpp/{CMakeLists.txt,ENDPOINTS_INVENTORY.md,FINAL_DIFFERENCES.md,COMPATIBILITY.md 章节,config/application.yaml}
git grep -i -E "kafka|elasticsearch|sharding|RateLimiter|TraceId|MessageUtils" car-monit-cpp-local -- car-monit-cpp/src car-monit-cpp/include
# v3 技术审阅追加（见 01-tech-stack-review.md 附录）
git show car-monit-cpp-local:car-monit-cpp/src/cm/{main.cpp,framework/web/Server.cpp,framework/web/Router.cpp,framework/db/MySqlClient.cpp,framework/web/crud/CrudEngine.cpp,framework/aspect/OperLogAspect.cpp,framework/net/HttpClient.cpp}
git show car-monit-cpp-local:car-monit-cpp/include/cm/framework/{web/Server.hpp,web/Router.hpp,web/crud/CrudSpec.hpp,db/Db.hpp,redis/RedisClient.hpp,security/Jwt.hpp}
git show car-monit-cpp-local:car-monit-cpp/include/cm/common/utils/{JsonUtils.hpp,FastJson2Compat.hpp,JavaCollections.hpp,Logger.hpp}
```

未 checkout、未建 worktree、未改动 master 工作区任何文件；本文档只做文档编辑。

## 附录 B：版本变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1 | 2026-11-07 上午 | 基于 master 工作区磁盘扫描，误判"完全空白"（已推翻） |
| v2 | 2026-11-07 | 基于 `car-monit-cpp-local` 分支真实代码重做：九层清单、491/497 基线、缺口与决策 |
| **v3** | 2026-11-07 | 依据 `01-tech-stack-review.md`：新增 §1.4 技术债快照、§4.10 TD-01…TD-17、§5.2 架构运维风险、D-05…D-07、R0/R6 技术债轨；在 RT-04/DA-01/MW-01/MW-04/CF-03 补充实现边界 |
| **v4** | 2026-11-08 | 按真实提交更新状态：出站 TLS（`2e86447`）、Forest 重试（`c478d9d`）、chunked（`05fe02c`）、队列有界（`5cf8294`）、整体截止（`5c5c7dc`）、静态流式（`d619d49`）、异步日志（`4a0f2a8`）、YAML 告警（`67dd8f7`）、`@RepeatSubmit`（`514d719`）、JSON `__fastfail`（`7baba72`）、MSVC `/utf-8`（`d3e85a9`）；`@Sensitive`/`@RateLimiter`/i18n 实测为 0/0/等价；BigDecimal 决策保留（`8d10607`）；新增 TD-18；worktree 已改名为 `car-monit-cpp-V2` |
