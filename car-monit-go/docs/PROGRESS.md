# 迁移工作进度（接口返回逐一对比阶段）

> **2026-11-08 真实中间件联调批次**：按用户下发的本机环境（MySQL 8/3307、Redis 8、
> ES 7.15.2、Kafka 4.0.0），在 3307 实例上 `CREATE DATABASE carmonit_ingest_test` 做端到端验证
> （用后 DROP）。实测 Kafka→Redis 幂等→月度分表→ES→DLQ 全链路：4 条消息中 1 条入库、
> 1 条重复被跳过、2 条进 DLQ（信封字段与 Java `sendToDLQ` 一致），consumer group offset 4/4。
> **联调中发现真实缺陷**：kafka-go v0.4.47 对 Kafka 4.0 的 `JoinGroup` 返回 EOF，消费端
> 无法加入组；升级到 v0.4.51 后正常。另新增 `-tags=integration` 集成测试验证
> `SyncSingleMonth`（2 行入库、缺 snapshottime 跳过、重复同步幂等）与 `PreCreateTables`。
> 详见 MAPPING §4.1 与 MIGRATION_GUIDE §1.9。
>
> **2026-11-08 构建/迁移验证批次**：`cmd/migrate` 在本机 MySQL 8.0.30 上实跑 `-dry-run`
> 与落库（`schema_migrations=0001`）。本机无 Docker，无法执行 `docker build`；已用
> Dockerfile 内完全相同的构建命令交叉编译 linux/amd64 的 server 与 migrate（产物
> 21.5MB / 8.2MB），并确认 Dockerfile 会 COPY 的 `configs/{vm,vmplus,templates}` 与
> `configs/generator.yml` 均存在。**验证缺口**：distroless 运行期未实跑（无 Docker），
> 镜像内非 root 用户写 `ruoyi.profile` 需保证挂载目录可写。
>
> **2026-11-08 基建收敛批次**：新增 `internal/platform/conv`，把散落在 base/manager/
> systemaux/flow/system/generator/ops 的 `strPtr/isNull/strOf/isNotBlank/isBlank/splitCSV`
> 收敛为唯一实现，各模块只保留同签名薄包装（调用点与 NULL/trim 语义不变）。
> `placeholders/inPlaceholders` 统一委托 `internal/platform/sqlx`，并为 MyBatis 空集合
> 语义补 `PlaceholdersOrNull`。**收敛过程中测试发现 `sqlx.SpacePlaceholders` 生成
> `"?, ?, ?,"`（尾部多逗号）的既有缺陷，已修复并补单测**；ops 的 IN 拼接因此从手写
> 循环改为统一实现。新增 `conv`/`sqlx` 单测覆盖 null、trim、CSV 尾空串与空集合。
>
> **2026-11-08 golangci-lint 实跑批次**：本机安装 v2.1.6 并真实执行（非仅留配置）。
> 首轮 89 个问题全部收敛到 0：修复 3 处 errcheck、2 处 goimports、1 处 ineffassign、
> 2 处可简化表达式；删除 27 个迁移遗留的死函数/常量；对 Java 语义必须保留的
> `saveFlowApply/doFlowApply` 与公告死代码用 `//nolint:unused` 注明原因。
> 配置层关闭 ST1000/ST1003/ST1005/ST1020-ST1022，理由均为“与迁移规范冲突”：
> 每个文件顶部的中文对照注释、Java 方法名/字段名（如 `synchDb`、`CpuNum`）、
> Java 原文错误消息必须逐字保留。`misspell` 对 `strat`/`curent` 两个 Java 原名加白名单。
> 复跑命令（缓存目录需可写）：
> `$env:GOLANGCI_LINT_CACHE="$env:TEMP\golangci-cache"; golangci-lint run` → `0 issues`。
>
> **2026-11-08 运行时回归批次**：本机无 Docker，改用 MySQL 8.0.30（临时 datadir，3307）+
> 临时 miniredis（6379）实跑 `cmd/migrate`（dry-run + 落库）与 `cmd/server`；
> `/healthz` 返回 database/redis 均 UP；admin 与无权限账号登录成功；
> 无权限账号访问 4 个受保护只读端点全部 `code=403`，admin 同端点不被拒；
> 非 admin 触发带 OperLog 的失败操作后，`sys_oper_log` 落到 `operName=noperm status=1`，
> `sys_logininfor` 记录登录成功。上述矩阵固化为
> `scripts/parity/check_permissions_runtime.py` + `make parity-perms-runtime`，
> 并新增 CI 作业 `runtime-perms-audit`（MySQL/Redis service containers + 基线 schema）。
> 细节与账号种子见 MIGRATION_GUIDE §1.8。
>
> **2026-11-08 数据面批次（分支 `car-monit-go-V2`）**：把此前"未接线"的 `internal/stream/*` 真正接到
> 运行时。新增 `internal/modules/base/datasync{,_source,_sync,_baseinfo}.go`：
> Kafka 消费 → Redis SETNX 幂等 → 按 `snapshottime` 路由 MySQL 月度分表 → ES `_bulk` 索引，
> 失败消息重试 3 次后按 Java 信封进死信队列；`main` 在 `kafka.enabled=true` 时启动消费者并参与优雅停机。
> 同时实现 `vehicleMonitoringTask`（7 个基础表全量刷新，含 `section_list` 覆盖写）、
> `snapshotFlowSyncTask`（全量/增量/单月/GaussDB HTTP 适配层）、`shardingTableTask`（分表预创建），
> 三者注册为 quartz 任务 Bean；`unmigratedTargets` 只剩 `trackTask.syncHistoryTrack`。
> **关键 DIFF**：分表路由不再依赖 ShardingSphere；INSERT 改为 `ON DUPLICATE KEY UPDATE` 保证重试幂等；
> 写入前按需建表；分表写失败不再静默 ack。**未验证**：真实 Kafka/ES/GaussDB 联调、
> ES 毫秒时间戳 mapping、vehicleMonitor 的 `earliest-time` 响应结构（见 MAPPING §4.1）。
> 新增离线测试 `datasync_test.go`（sqlmock + httptest）与 Redis 集成测试（默认跳过，
> `CARMONIT_TEST_REDIS=1` 启用）。
>
> **2026-11-08 加固批次（分支 `car-monit-go-V2`）**：按代码审阅结论做生产化整改，
> 不改动 API 契约。已完成：manager 手写控制器的权限点与操作日志逐条对齐 Java（含被注释注解不加）、
> 可疑车辆核实/批量同步、异常流水+车辆金额回写、代码生成 4 个多写流程补事务并把吞错改为返回 error、
> OperLog 改固定 worker 池（跳过文件流与 multipart、2000 字节上限）、雪花 ID 统一到 `internal/idgen`
> 并支持多副本（`CARMONIT_WORKER_ID`/`CARMONIT_DATACENTER_ID`）、数据接入归属决策
> （Kafka/ES/GaussDB 仍由 Java 承担，未迁移任务保存时直接拒绝）、`/healthz` DOWN 返回 503、
> 服务器超时与优雅停机（限时收敛定时任务 + 排空操作日志）。
> **注意**：这些改动会改变非 admin 用户的 403 行为与 `sys_oper_log` 行数，双端对拍需用无权限账号补测权限/审计维度。
>
> **2026-11-06→07 第四批：按"每条注册路由是否真被比过"重查一遍** —— 新增 `check_coverage.py`，
> 口径直接复用各对拍脚本自己的定义。第一轮盘出 515 条路由里 **102 条从没被跑过**；补齐口径后
> 现在是 437/450 = **97.1%** 覆盖，未覆盖只剩 13 条动作型端点（5 条可补 `actions`、8 条按约定该豁免，
> 逐条列在 §11.5）。这一轮挖出 **4 个真差异并全部修掉**：
> ① `/getRouters` 少 `meta.link`（Java 的 MetaVo 实例字段恒输出 null，Go 用了 omitempty）；
> ② `/downTemplate/{type}` 的模板根只认"配置文件同级"，配置一搬走 7 个合法 type 全退成空 200
> （现按两个候选根找；type 只当 map 键用，路径全是本包常量，无穿越面）；
> ③ base 模块写接口在"请求体没有主键这个键"时多输出 `"data":""`（Java 是 `success(msg, null)`
> 不写 data 键；新增 `bodyStringValue` 区分缺键与空串）；
> ④ `PUT /manager/suspicious/check`：Java 在 `isExcept != "1"` 时不判空就遍历 null 的 `checkList`
> ⇒ NPE ⇒ `{"msg":null,"code":500}`，且 `@Transactional` 把前面两个 delete 回滚掉，
> Go 原先直接"操作成功"，现在返回同样的空消息错误（`[]` 空数组仍照常走完）。
> 读侧口径扩了 5 条顶层路由（`/getInfo`、`/getRouters`、`/downTemplate`、`/test/**`），
> 第 3 档 95 → 100 条、差异仍是 11 条已知；写侧从 32 个资源族扩到 **45 个**并加了 `actions` 钩子，
> 新增资源里 6 个四步全一致，其余 4 条新差异全部定性为 Java 侧（§11.4）。
> `/downTemplate/{type}` 的 7 个合法 type 首次逐格比对：Java 是 easypoi 重写后的字节、
> Go 是模板原始字节，长度不同但 **单元格差异 0**。
> 另外记两个会造成"假绿"的坑：Git Bash 会把位置参数转成 Windows 路径，
> `compare_write.py /manager/xxx` 必须先 `export MSYS2_ARG_CONV_EXCL='*'`，否则匹配不到任何资源
> 却安静地报"差异 0"；19 位雪花 id 不能当 JSON 数字传（Go 解成 float64 会丢精度，Java 的
> String 字段拿原始 token），脚本只在 15 位以内才转数字。
> 详见 `docs/PARITY-API-TIER-2026-11-04.md` §11。
>
> **2026-11-04 批次（api 联动 + 分层校验）见 `docs/PARITY-API-TIER-2026-11-04.md`**：
> 按「backend→api 的接口 → 其它业务接口 → 框架接口」三档跑双端对比，api 双端（9902/9903）与
> backend 双端共用 MySQL、Redis 各占不同 db；用**钉版接线**（两端同指一个 api）把残余差异归因到
> api 双端自身：第 1 档 14 条 URL 在 A/B 两种钉版接线下**0 差异**，交付接线只剩 1 条（api Java
> `/base/feerecords/*` 恒 500）。第 2 档 185 条 2 差异（均为已记录的 Java 侧缺陷），第 3 档 95 条
> 11 差异（运行态 / Java 缺陷 / 同为 500 的错误文本）。
> 本轮最大收获是补上**xlsx 附件流盲区**：新增 `compare_xlsx.py` 做单元格级对比、`dump_templates.py`
> 打印 EasyPOI 模板真值，21 个导出端点修复前 18 个有差异（合计 19633 格）、修复后全部 0 格；
> 顺带修掉 `/manager/carwarning/list` 的 8 个字段差异（列表被误做了字典翻译 + 缺 `car_info` 联表列）。
> 另修 `/oss/object/*/*/*` 预签名（改用离线 SigV4，此前 MinIO 不可达时整条 500）、
> `/common/download` 的 `anonymous()` 语义（有效 token 应 403、无效 token 应 200）。
>
> **第二批：把导出层彻底做成可比口径** —— 新增 `compare_export_all.py`，覆盖全部 58 条 `/export` 路由
> （22 条 EasyPOI 附件流 + 33 条 **ExcelUtil 落盘型**：文件写到 `profile/download`、响应 msg 只带文件名，
> 之前完全没被比过 + 3 条 non-xlsx 两端逐字节相同），修完 **单元格差异 253487 → 2941 → 0**。
> 三条新落格规则由双端对拍反推 + `ExcelUtil` 源码印证：① XML 1.0 非法字符 Java 落 `?`（POI 序列化）
> 而 Go 落 U+FFFD；② STRING 单元格的值以 `= - + @` 开头时 Java 前补一个 TAB（CSV 注入防护，
> `tenant_id=-1` 落成 `"\t-1"`）；③ `readConverterExp` / `dictType` **未命中给空串**（工程里大量注解是
> 代码生成切坏 Javadoc 的残骸，如 `readConverterExp="内=部"` ⇒ Java 整列空），且 separator 默认是 `,` 不是 `=`。
> 规则集中在 `internal/excelx`（`cell_test.go` 钉住），并按 `dump_excels.py` 打印的 @Excel 真值重建了
> 6 个 manager 端点的列集（busstest 17 / aduitfree 14 / routedetail 25（含 Kangxi 部首 ⾏⽅，不是"行方"）/
> cartrackinfo 20 / feerecord 17 / carsuspiciousback 补两个残缺 `Exp`）；顺手对齐了 `exportAbnormalPassage`
> 的 Word 正文标签与金额格式。并更正第一轮口径：`/monitor/operlog/export` 的 496 格差异**不是**自生成审计行
> （自记录只多 1 行、贡献 0 格），而是规则①。
> 静态门禁：`build/vet/test` 通过、`check_startpage_map.py` 六类全 0、默认分页 91 条 0 差异、
> 参数矩阵 1617 组合 0 差异、Redis 隔离 24 项全通过（清理 `failures=0`）。
>
> **第三批（2026-11-05）：Excel 导入层收口** —— 导出归零后剩下的最后一块是**上传**。
> 新增 `compare_import.py`（同一份 inlineStr xlsx 传两端，比响应 + 按本端标记值精确查落库）、
> `compare_upload_errors.py`（10 类畸形请求 × 3 端点 = 30 条错误形态）、`dump_local_xlsx.py`
> （本地 xlsx 逐行打印，用来核对真实导入模板的表头）。把 `ImportUtil.importExcel` 的通用逐列校验
> （规则 `1 必填 / 2 小数 / 3 整数 / 4 年月日 / 5 身份证 / 6 年月 / 7 数值 / 8 年月日时分秒`）
> 抄成 `internal/modules/manager/import_validate.go`，错误对象统一成 `ImportErrorEntity` 的
> `{rowNo,colName,message}`，行号按 `getErrorBO(index+1)` 的双重 +1 落成「数据行序号 + 2」，
> 单测 `import_validate_test.go` 钉住（含"每个 token 独立一轮 ⇒ 一个值可报两条"、
> "空值只查必填"、Java `Pattern.matches` 的全匹配语义）。三个端点按 Java 的**两段式**重排：
> 格式校验先跑完所有行，全通过才轮到字典/业务校验。落库侧补齐 Java 的 MP 语义
> （`mpNonNullCols` 剔掉 nil 指针，null 属性不进 SET；`insertFill` 不填 update_*、
> `updateFill` 会把值写回实体所以响应里也有；`tenant_id` 只在 `epsId` 原本为 null 时才填 ⇒
> `car_except_record` 拿到 `-1`、`car_info` 拿不到），并把 `isExitsTime` 区间查重
> 抽成 `exceptTimeOverlap`（命中就"这一行不写库、响应照样带着它"）。
> 途中修掉三个真 bug：① `/manager/carinfo/import` 更新分支漏 stamp `updateBy/updateTime`；
> ② 导入的时间列用 `time.Parse` 拿到 UTC，配合 DSN `loc=Local` 把入库钟点整体 +8 小时；
> ③ `/system/user/importData` 的 `readXlsxRows` 用 `GetRows` 会裁掉"有单元格但全是空串"的行，
> 行号与 POI `getRow(i)` 对不上 ⇒ 换成 `Rows` 迭代器、缺行补 nil，据此区分
> 「没有数据行」与「标题全不匹配」（后者 Java 是 `list.add(entity)` 无条件加 null 再被
> `importUser` 的 catch 二次 NPE ⇒ `{"msg":null,"code":500}`，已复刻）。
> 另外把预签名 URL 的 `X-Amz-Expires` 还原成 Java 的两次取时反算（86400/86399 由 SDK 耗时决定，
> 对拍里按 `<EXPIRES>` 归一）。
> 结果：导入回归**问题 0**（10 组用例，其中 5 组是多行：跨行业务错误顺序、`isExitsTime` 区间重叠时
> "这一行不写库但响应照样带着它"、首格 `结束` 终止读行、一行报错后合法行也不入库的级联、
> `errorList > 100` 提前 break）、30 条错误形态 28 条一致（2 条已知，
> 均为 Java 内部异常文本），第 1/2/3 档复跑 14/12/**0**/2、185/162/2/21、95/82/11/2，
> 导出层 59 条路由复扫单元格差异 0（口径从 58/33 校正为 59/34，多出的那条是 `/system/user/importTemplate`）、
> 路由清单 Java 511 全匹配、
> 参数矩阵 1617 组合 0 差异、默认分页 91 条 0 差异、`check_startpage_map.py` 六类全 0、
> 写生命周期 15 条差异仍只落在 8 个 Java 侧缺陷资源上、Redis 隔离清理 `failures=0`，
> PARITY 行已全部清干净（`--clean` 现在也扫 `car_except_record`）。
> 详见 `docs/PARITY-API-TIER-2026-11-04.md` §6.6。
> **收尾时踩到一件环境上的事**：共享库里 `admin` 的口令散列被换掉了（`update_time` 仍是 2025-09-27，
> 像是直接改的列），现在 Java 参照端与 Go 端**都**返回「用户不存在/密码错误」，
> 在线双端对拍因此打不进去；本轮结束前所有用例都还是通的，代码与文档状态不受影响。
>
> **2026-11-03 批次收口见 `docs/PARITY-SUMMARY-2026-11-03.md`，分页专题见 `docs/PAGINATION-PARITY-2026-11-03.md`**：
> 分页语义与 PageHelper 5.3.3 源码逐条对齐（`SkipQuery` 照抄 `afterCount` 的 `pageNum>0 && count>startRow`、
> `Clamp` 的 reasonable 两界、`startRow`、`OrderBy` 原样拼接、`reasonable` 的 `Convert.toBool` 词表）、
> 补齐漏掉客户端排序的端点（car_free/car_track 手拼 SQL、ops 两个日志 List、systemaux queryPage/indexmenu）、
> 校验矩阵从 11 种组合扩到 22 种并修掉脚本自身的 rows 盲区；1617 组合 0 差异（豁免白名单已删）；新增 `check_startpage_map.py` 静态核对（四类检查；以 Java 的 94 条分页路由为基准，100% 匹配到 Go 注册）补回 28 处空表掩盖的分页缺失；`StartPageError` 复刻 `escapeOrderBySql` 的两条拒绝，
> 单测 `internal/web/pagination_test.go` 钉住语义（`pagination.go` 语句覆盖 100%）。
>
> **第三轮（2026-11-02）另见 `docs/PARITY-2026-11-02.md`**：共用 MySQL、**两端使用不同 Redis DB
> （Java=db0 / Go=db2）**重做全量校验，校验脚本进仓库（`scripts/parity/`）。
> 该轮结果：路由 Java 有/Go 没有 **0** 条；GET 288 条中 **250** 条逐字段一致、14 条差异全部定性为
> 环境设定或 Java 侧缺陷；写接口 32 资源中 24 个四步全一致；Redis 双 DB 隔离 24 项断言全通过；
> 查询参数矩阵（起步 696 组合，后扩到 1463 组合）**0** 差异。
> 新发现并修复 9 类问题：登录审计 `status` 写错导致整行丢失、`GET /system/user/` 缺失、
> 根路径只注册 GET、`/oss/**` 九个端点未迁移、MinIO 建连超时、
> **45 个列表端点在请求不带分页参数时未按 Java 默认 `pageSize=10` 分页**、
> 分页参数取值与 `reasonable` 越界回末页、客户端 `orderByColumn` 被忽略、
> 以及 PageHelper「count=0 就不再执行分页查询」的短路（`web.PageDomain.SkipQuery`）。
> 后四类在「固定带 `pageSize=3` 的对比」里都是隐形的，只有 `check_default_page.py` /
> `check_query_matrix.py` 两个专项才暴露（42 → 0、183 → 0）。
> 下文保留第一、二轮的记录。

> 记录时间：2026-11-02（第三轮更新）。前两轮修掉 GET 响应的字段级差异；本轮补齐
> **Redis 共存**（Go 写的缓存 Java 读得回来）与 **写接口（POST/详情/PUT/DELETE）全生命周期回归**。

## 1. 对比方法

| 项 | 值 |
|---|---|
| Java 参考服务 | `ruoyi-admin/target/ruoyi-admin.jar`，端口 **9988**（`--server.port=9988`） |
| Go 服务 | `bin/carmonit-server.exe`，端口 **9989**，配置 `configs/config.yaml` |
| 账号 | admin / __SET_CARMONIT_ADMIN_PASSWORD__（Java 登录需验证码，答案从 Redis `captcha_codes:<uuid>` 读取） |
| 对比脚本 | 第三轮起统一在仓库内：`scripts/parity/compare_get.py --prefix /<模块> --out <报告.json>`（前两轮使用的 `cmp_api.py`/`cmp_one.py` 已作废） |
| 写接口生命周期对比 | `scripts/parity/compare_write.py`：取真实行做模板 → 两端各插一条 `PARITY_*` 标记行 → 比 POST/详情/PUT/DELETE → 按标记硬清理 |
| 落库逐列对比 | `scripts/parity/pp.py` 里的 `sql()`/`read_key()` 封装（MySQL CLI + db 感知的 redis-cli） |
| Redis 共存验收 | `scripts/parity/check_redis_isolation.py`（双 DB 隔离 24 项断言）；早期的 `verify_*.py`/`smoke_redis.py` 为共享 DB 时期脚本 |
| 路由清单来源 | Go 启动日志 `C:/Users/abelz/AppData/Local/Temp/carmonit.log` 里的 `[GIN-debug]` 行 |
| 归一化规则 | `yyyy-MM-dd HH:mm:ss` → `<DT>`、带横杠/无横杠 UUID → `<UUID>`/`<HEX32>`、15–20 位主键 → `<ID>`、`PARITY_*` 测试值 → `<PARITY>`、浮点保留 6 位，深度逐字段比较 |

GET 逐字段比较用 `scripts/parity/compare_get.py`；写接口不再用畸形请求体探测，改为
`scripts/parity/compare_write.py` 走完整生命周期。
两端**共用一个库**，所以每条记录的唯一列用不同随机盐，比对时把标记值与主键一并屏蔽；
`/base/section`、`/flow/*` 一类空表没有样本行可克隆，改用手工请求体（`RESOURCES[].body`）。

## 2. 对比结果（第二轮；第三轮的 288 条 URL 与专项数字见 `docs/PARITY-2026-11-02.md`）

注册路由合计 **498** 条（移除 Go 多注册的 `GET /system/user` 后，与 Java 路由表一致）。

### 2.1 GET 响应

| 模块 | GET 路由 | 完全一致 | 仍有差异 | 非 JSON/二进制 | 说明 |
|---|---|---|---|---|---|
| `/manager/**` | 99 | 79 | 0 | 20 | 原 `carLocation`/`online/list` 差异随 Redis 共存修复消失；其余为 Excel 附件流 |
| `/base/**` | 70 | 57 | 8 | 5 | 差异=外部服务/Java 自身缺陷（见 §4.1） |
| `/flow/**` | 30 | 30 | 0 | 0 | 全量一致 |
| `/system/**` | 65 | 60 | 4 | 1 | 差异=upgradeInfo 的 500 错误文本 |
| `/monitor/**` | 13 | 10 | 3 | 0 | 差异=Redis 运行态统计 + 2 个 Java 自身异常 |
| `/tool/**` | 10 | 10 | 0 | 0 | 全量一致 |
| **合计** | **287** | **246** | **15** | **26** | 第二轮为 242 一致 / 20 差异 |

报告：`recheck_manager.json`、`recheck2_base.json`、`recheck_flow.json`、`recheck2_system.json`、`recheck2_monitor.json`、`recheck_tool.json`。

### 2.2 写接口生命周期（32 个资源 × POST→详情→PUT→DELETE）

| 结果 | 数量 | 明细 |
|---|---|---|
| 四步全一致 | 24 | dict/type、dict/data、config、notice、post、dept、menu、role、base/config、geometry、carinfo、whiteinfo、warningrule、querylog、suspiciouscheck、cartrackinfo、busstest、routeinfo、routedetail、feerecord、splitrecord、carwarning、flowname、flowlist、flowtemplate |
| 仅 Java 侧缺陷 | 8 | 见 §4.2：`/system/user` 与 5 个 `IdType.INPUT` 主键未由服务层生成、`/base/configServiceArea` 引用不存在的 `id` 列、`/base/geometry` 删除引用不存在的 `del_flag` |
| 收尾清理 | failures=0 | 按 `PARITY` 标记逐表扫描字符列后硬删，测试数据无残留 |

## 3. 修复清单（累计三轮；§3.1–§3.6 为前两轮，§3.7–§3.8 为本轮）

### 3.1 响应信封 / 公共设施
- `AjaxResult`：`data` 仅在非 null 时输出；`rows` 恒为数组（`internal/web/response.go`）
- 新增 `web.ErrorNilMsg()` + `ServiceError.NilMsg`：复刻 Java 未捕获 NPE 的「code 500、msg = null」
- 新增 `web.ISODateTime`：对应 Java 里**没有 @JsonFormat 的 `java.util.Date`**（Jackson 默认 ISO-8601 带毫秒与 +08:00 偏移）

### 3.2 manager
- `/manager/carsuspiciousback/**` 独立实体/列/排序（`order by t.create_time desc,t.id`、`@JsonFormat(yyyy-MM-dd)`），历史列表改回 `CarSuspicious` + `order by t.id`
- `EntityBase.ID` 改为 `*string`（列表 SQL 少选 `id` 时 Java 返回 null）
- `TrailBo` / `ZdataTrailTracks` 按 Java 字段全集建模；移植 `getTrailDevBO`、桩号换算 `pilenoDec`
- `carExceptRecord.supplementaryStatus` 的 Java 字段默认值 `"0"`（`tableSpec.afterScan` 钩子）
- `createInfo` 联表、`orgId` 查不到保持 null、`cartrackinfo` 去掉 Java 不存在的 `firtStation*` 赋值
- 导出文件名用 `UUID.randomUUID()`（带横杠）+ `@Excel(readConverterExp)` 支持

### 3.3 base
- **系统化指针化**：`models_*.go` 里 374 个 `string` 字段改为 `*string`（`null` / `""` 与 Java 对齐）；`isNull/isNotBlank/isBlank/deleteEnd` 扩展为 `any`
- 日期三态：`@JsonFormat(yyyy-MM-dd)` → `dateOnly`；`@JsonFormat(yyyy-MM-dd HH:mm:ss)` → `web.DateTime`；无注解 → `isoDateTime`（修好 `provcapture.loadtime` 等）
- `gantry.listAll` / `toll.listAll` / `fwqjcxx` 增补 `@TableField(exist=false)` 的 `sectionCodeList`
- `ods_yhgl_v_base_org` 的 `parentId` 相关子查询列映射（此前恒为 null）
- `/base/cdc/status` 不再读 `kafka.*`（Java 的 CdcConfig 全取默认值）
- `/base/geometry/getHenDa`、`/base/geometry/syncAllGeometry1` 改回 code 200（Java 为异步/兜底成功）；`syncAllGeometry` 真正执行 `geometry_copy1` 查询让 SQL 失败（与 Java 同因）
- `fitting/list` 保持可用（Java 的 Mapper 引用了不存在的 `id` 属性，恒 500 —— 记为 Java 侧缺陷）

### 3.4 flow
- `/flow/messageinfo/exportShrz` 的 NPE 分支改为 msg=null：**30/30 全量一致**

### 3.5 system / systemaux
- `model` 包系统实体（SysUser/SysRole/SysDept/SysMenu/SysPost/SysDict*/SysConfig/SysNotice/SysOperLog/SysLogininfor/SysFile）字符串字段指针化；`BaseEntity.CreateBy/UpdateBy/Remark` 指针化
- Jackson 派生属性：`SysUser.admin`、`SysRole.admin`、`SysDictData.default`、`SysDept/SysMenu.children`（恒数组）、`roles/menuIds/deptIds` 不省略
- `loginDate` 改 `ISODateTime`；`password` 改 `json:"-"`（Java `@JsonIgnore`）
- 查询列对齐 Java VO：`selectUserVo`（`dept` 只映射 dept_id/dept_name、`sub_code`、`ifnull(tenant_id,-1)`）、`RoleResult` 6 列、dict type/data 的 7/12 列、job/jobLog 的 12/8 列
- `/system/user/list/dept` 回填扁平 `deptName`；`/system/config/configKey/{k}` 的配置值放在 **msg**（Java 命中的是 `success(String msg)` 重载）
- `/system/user/profile` 复刻 fastjson2 缓存回读的 `params: {"@type":"java.util.HashMap"}`（user/dept/roles）
- 移除 Go 多注册的 `GET /system/user`；`/system/{file,notice}/view/**` 增加 `.anonymous()` 语义（带 token 访问 → 403 + Spring 错误体）

### 3.6 monitor / tool
- quartz `SysJob`/`SysJobLog` 查询列对齐 Java VO；`SysJobLog` 补 `BaseEntity`（createBy/updateBy/remark/updateTime 为 null）
- `SysOperLog.businessTypes` 恒输出 null
- 生成器：`information_schema` 列名大小写归一、`gen/list|all/list|db/list` 复刻 MyBatis `<collection>` 的空占位元素、`gen/{id}` 的列补 `tableId` —— **/tool 10/10 一致**

### 3.7 Redis 共存（本轮，新增 `internal/cache/fastjson.go`、`internal/cache/javatypes.go`）

Java 的 `redisTemplate` 值序列化器是 `FastJson2JsonRedisSerializer(Object.class)` + `WriteClassName`，
写出的值不是标准 JSON；Go 原来写标准 JSON，Java 的 `getCacheObject` 反序列化得到 `JSONObject`，
强转业务类型即 `ClassCastException`（这正是 `/monitor/online/list`、`/manager/bigScreen/carLocation` 500 的根因）。

- `cache.ToJava(v, JavaOptions)` 写出：根对象/根数组元素补 `@type`、包装类型 `Long` 补 `L`、
  `Set` 字段写成 `Set[...]`、`params` 写成 `{"@type":"java.util.HashMap"}`、null 成员不写（fastjson2 默认行为）
- `cache.FromJava(raw)` 读回：去 `Set[` 前缀、去 `L` 后缀；**保留 `@type` 成员** ——
  Java 会把它读进 `BaseEntity.params`（`Map<String,Object>`）并原样输出到响应，剥掉反而不一致
- `Cache` 新增 `SetJava / SetJavaString / GetStringJava / ListJava`，`Get` 一律走容错解码
- 类型表按 Java 进程真实原值核对（`grab_java_cache.py` 抓取）：`LoginUser`、`CarInfo`、`CarVO`、
  `CarWhiteInfo`、`CarWarningInfo`、`CarWarningConfig`、`Geometry`、`OdsSzdnGantry`、`SysDictData`
- `login_tokens:*` 补 Java 有而 Go 没有的 `username`、`user.password`（HTTP 响应里被 `@JsonIgnore`，缓存里有），
  `loginDate` 用 fastjson2 的 `yyyy-MM-dd HH:mm:ss`（`internal/auth/login_cache.go`）
- `sys_config:*` 改为 FastJson2 的带引号字符串值，Go 读回时脱引号（原来读到 `"123"` 会连引号一起返回）
- `sys_dict:*` 保持 Java 的 string + 整数组形态（本工程 `DictUtils` 用的是 `setCacheObject`，不是 `setCacheList`）；
  缓存值里的 `params` 由 `JavaOptions.Maps` 规则**强制补齐**成 `{"@type":"java.util.HashMap"}` ——
  少这个标记时，「谁先回填缓存」会改变另一端读到的字段集合（Java 的 `BaseEntity.params` 是
  `@JsonInclude(NON_EMPTY)`：只有 map 里真的留有 `@type` 键时才会输出 `params`）
- `section_list` 由 Java 定时任务写成 Redis List，Go 改用 `ListJava` 读取（原来是裸 `LRange` + `json.Unmarshal`）
- `web.DateTime` / `web.ISODateTime` 接受裸毫秒时间戳：Java 老会话里就是 `"loginDate":1715955352000`，
  否则整条 `login_tokens` 解析失败、在线列表少 25 条
- 新增 `internal/cache/fastjson_test.go`：用 Java 真实原值做样本，覆盖 `@type`/`L`/`Set`/`HashMap`/null 五种写法与回读

**验收**：两端 `/monitor/online/list` 返回 96/96 条且 tokenId 集合一致；Go 刷新 `car_list` 后 Java 端点正常读取；
Go 写的 `sys_config`/`sys_dict` Java 读得到，反之亦然。
稳定性冒烟 `smoke_redis.py`（4 轮，交替由 Go/Java 回填字典缓存，覆盖登录态形态、在线列表、大屏位置、
白名单/车辆/门架列表、缓存原值类型、参数与字典的双向读写与删除驱逐）：**140 项检查 0 失败**，测试数据与测试键无残留。

### 3.8 写接口回归发现并修复（本轮）

- **审计字段**：Java 的 `insertFill` 只填 `createTime/createBy/epsId/tenantId`，
  `updateBy/updateTime` 属于 `updateFill`（实体上标 `FieldFill.UPDATE`）⇒ insert 后这两列是 NULL。
  Go 的 `withInsertAudit`/`insertAudit` 原来也填 update_*，已去掉（manager/base 两处）
- **`tenantId` 的复制粘贴 bug**：Java `insertFill` 判断的是 `if (epsId == null)` 而非 `tenantId == null`，
  即调用方传了 `epsId` 时 Java **不填** `tenant_id`；Go 一并复刻
- **`car_info` 特例**：`CarInfoServiceImpl.saveCarInfo:143-149` 由服务层显式写
  `epsId/createBy/updateBy/updateTime` 且从不写 `tenant_id`（Go 原来落 -1）⇒ `carInfoSave` 显式补齐
- `POST /system/dept` 父部门不存在时 Java 抛 NPE ⇒ `msg` 应为 **null** 而非字符串 `"null"`（改用 `web.NewNilMessageError()`）
- `car_warning_info` 实体补 Java 的两个 `@TableField(exist=false)` 集合字段
  `sectionCodeList` / `codeList`（Java 未赋值时 Jackson 仍输出 `null`，键必须存在）
- 对比脚本需要避开的坑（复现时注意）：唯一列要用不同随机盐；主键/盐值/手机号进屏蔽表；
  `parentId`/`menuIds`/`deptIds` 这类 Java 侧无空判断的字段必须按前端真实形态补全；
  定位新增行改用 SQL 按标记值查（列表接口有树形与数据权限过滤）；
  `/system/dept` 的 `subCode` 依赖「插入前同级数量」，同库并行必然差 1 ⇒ 忽略该列

### 3.9 分页与代理响应语义（第三轮，`internal/web/pagination.go` 等）

Java 的分页是 PageHelper 拦截器行为，前两轮「固定带 `?pageNum=1&pageSize=3`」的对比看不到它，
本轮用 `check_default_page.py`（不带参数）与 `check_query_matrix.py`（11 种参数组合）专攻：

- **缺省也分页**：`TableSupport.getPageDomain` 给 `pageNum=1、pageSize=10` ⇒ 新增 `web.PageAlways(c)`，
  所有 Java 侧调过 `startPage()` 的列表路径都改用它（45 个端点，42 → 0）
- **参数取值**：照抄 `Convert.toInt(参数, 默认)` —— 只有没传/解析不出数字才回落默认，
  显式 `pageSize=0/-1` 是合法入参；删掉 Go 自造的 `MaxPageSize=500`
- **`reasonable` 词表**：`TableSupport` 走 `Convert.toBool(值, null)` —— `true/yes/ok/1` 真、
  `false/no/0` 假、空值与乱值 null，再由 `PageDomain.getReasonable()` 回落 TRUE ⇒
  `web.Page` 原来「只认 `"true"`」会把 `reasonable=1` 误判成 false（越界页少返回一页数据）
- **`reasonable` 越界回末页**：`PageDomain.getReasonable()` null → TRUE ⇒ 新增 `Clamp(total)`/`LimitOffset(total)`，
  分页点全部接上 total
- **客户端排序优先**：`startPage` 的 orderBy **覆盖** mapper XML 的 order by ⇒ `manager.orderFor`、
  `base.orderByFor`、`generator.selectGenTableList` 统一这个优先级；
  后续补齐手拼 SQL 与漏网端点（`car_free` 4 处、`car_track` 1 处、`ops` 两个日志 List 新增 `orderFor`、
  `systemaux.queryPage` 去掉「语句里有 order by 就不追加」、`indexmenu` 把语句排序移进 defaultOrder）
- **`afterCount` 放行条件**：`SkipQuery` 不写成「count=0」而是照抄
  `pageNum > 0 && count > startRow`（`AbstractHelperDialect.afterCount` + `Page.calculateStartAndEndRow`），
  且 `Clamp` 的下界钳位只在 `reasonable` 为真时发生（`reasonable=false&pageNum=0` 时 Java 返回空页）
- **空结果短路**：PageHelper 在不放行时 `return afterPage(new ArrayList())`，数据查询一次都不执行，
  因此「空结果 + 非法排序列」在 Java 侧不报错 ⇒ `web.PageDomain.SkipQuery(total)`，
  15 处分页执行器（11 个文件）先问这一句（1463 组合 → 0 差异）
- **`isAsc` 原样拼接**：`getOrderBy()` 不校验方向值，`isAsc=bogus` 就是让 MySQL 报错；
  别名 `ascending/descending` 在 `setIsAsc` 里转 ⇒ `web.OrderBy` 去掉「非 desc 即 asc」兜底
- **`pageSizeZero=false`**：本工程 pagehelper 没配这项 ⇒ `afterCount` 对 `pageSize<=0` 一律不放行；
  `SkipQuery` 补上该分支（原来靠「负数归一成 LIMIT 0」近似，遇非法排序列会比 Java 多报一个 500）
- **startPage 覆盖面（静态核对补回 28 处）**：flow 9 个列表、system user×7 + role + post、
  manager carwarning/listFileCarNo/incomeDetailList/carStatics、`system/file/getNewCa`、
  `system/upgradeInfo/list`、`tool/gen/getColumnList` 改用 `web.PageAlways(c)`。
  这类差异数据比对看不见（表为空或行数 ≤10），只能靠 `check_startpage_map.py`；
  已用「sys_post 造到 11 行 → 修复前 Java 10 / Go 11 → 修复后两端一致 → 清理」坐实
- **`escapeOrderBySql` 的拒绝语义**：`PageDomain` 加 `startPage` 标记（`PageAlways` 置位）与
  `StartPageError()`，16 处在跑 SQL 前给出 `{code:500, msg:"参数不符合规范，不能进行查询"}`
  或 `"参数已超过最大限制，不能进行查询"`；导出/listAll 这些 Java 不校验的端点不拒绝
- **代理 JSON 形态**：hutool `JSONUtil.toBean(..., TableDataInfo.class)` 默认丢 null 成员，
  Forest+Jackson 保留 —— 按端点区分（`renderRemoteTable(c, table, dropNull)`），
  上游响应 `UseNumber` 解码以原样透传数字字面量（`0` 不会变成 `0.0`）
- 以上语义由 `internal/web/pagination_test.go` 钉住（12 组钳位/短路 + 8 组排序拼接），
  依据逐条来自 `pagehelper-5.3.3-sources.jar`，见 `docs/PARITY-SUMMARY-2026-11-03.md` §3

## 4. 剩余差异

### 4.1 GET（15 项，均为外部依赖或 Java 侧缺陷）

| 接口 | 现象 | 结论 |
|---|---|---|
| `/manager/suspicious/{id}` 的 `raodTrailList` | 缺路网几何 | Java 依赖 `getCarGeometryByPlanNew`（路网最短路 + 腾讯路线规划），Go 不复现，固定空数组 |
| `/base/feeGantry/*`、`/base/feerecords/*`、`/base/feestationexit/list`、`/base/snapshotflow/{id,earliest-time}` | Java 500（`String cannot be cast to ...` / `SocketException`） | 这些端点在 Java 里是转发外部 9901 服务的 proxy，Java 侧解析失败；Go 代理正常返回 |
| `/base/vehicleweight/ZdTrails:BorderWeighing` | Java 500 `TooManyResultsException` | Java 用 selectOne 取到多行（数据触发），Go 返回首行 |
| `/base/geometry/syncAllGeometry`、`/system/upgradeInfo/*` | 两侧均 500，错误文本不同 | 同为「表不存在」：`geometry_copy1`、`sys_upgrade_info` 本地基线库没有 |
| `/base/fitting/list` | Java 500 `ReflectionException` | Java Mapper 引用了实体上不存在的 `id` 属性；Go 保持可用 |
| `/base/cdc/config` | Java 返回两段拼接的非法 JSON | Java 自身序列化缺陷（含 Spring 内部结构 + 错误体），Go 返回合法 JSON |
| `/base/geometry/getHenDa` | Java 连接被重置 | 外部 HenDa 服务不可达导致 Java 侧连接中断 |
| `/monitor/jobLog/{id}` | Java 500 `缺少必需的路径变量[jobLogId]` | Java 编译未保留参数名，接口在 Java 侧不可用；Go 正常返回 |
| `/monitor/server` | Java 500 `NoSuchMethodError: com.sun.jna.Memory.close()` | Java 依赖的 JNA 版本冲突；Go 正常返回 |
| `/monitor/cache` | 命令统计/键数量不同 | Redis 运行态数据（两服务共享同一实例），结构一致 |
| 26 项非 JSON | Excel/Word/图片等附件流 | POI/EasyPOI 与 excelize 生成的二进制无法逐字节一致，表头与列顺序已按 Java 注解还原 |

### 4.2 写接口（8 个资源，全部是 Java 侧写入路径本身不可用）

| 接口 | Java 现象 | 结论 |
|---|---|---|
| `POST /system/user` | `IndexOutOfBoundsException: No group 2`，任意请求体都失败 | `SqlLogInterceptor:265` 用 `sql.replaceFirst("\\?", paramValue)` 拼 SQL，BCrypt 串里的 `$2a$` 被当成正则分组引用 ⇒ Java 新增用户整体不可用；Go 正常 |
| `POST /base/{section,toll,gantry}`、`/base/org`、`/manager/carsuspiciousback` | `Column 'id'`/`'big_id' cannot be null` | 实体是 `IdType.INPUT` 且服务层不生成主键，前端不传 id 时 Java 必然插入失败；Go 生成主键后可用 |
| `POST /base/configServiceArea` | `Unknown column 'id' in 'field list'` | Java 实体声明了库里不存在的 `id` 列 |
| `DELETE /base/geometry/{ids}` | `Unknown column 'del_flag' in 'field list'` | Java 的 `GeometryMapper.xml` 逻辑删除引用了库里没有的 `del_flag`；Go 走可用路径 |

## 5. 下一步

1. 如需要「连错误文本都一致」，可按模板拼出 §4 里的 MyBatis 长错误文本（当前判断为无收益，未做）
2. ~~只跑 Go 单服务的复测（排除共享 Redis / 共享库干扰）~~ —— 第三轮已做：两端改用不同 Redis DB，
   结果与新发现的 5 项修复见 `docs/PARITY-2026-11-02.md`
3. Java 进程下线后，可清理为兼容而保留的 `@type` 注入路径（`profile` 接口的手工注入与 `cache.ToJava` 重叠）
4. `/oss/**` 九个端点的**成功**返回形态尚未核对（本环境 MinIO 不可达，只验证了 500 信封一致）

## 6. 复现命令

```bash
# 构建与静态检查
go build ./... && go vet ./... && go test ./...
gofmt -l internal/ cmd/

# 重启 Go 服务（日志供脚本解析路由）
PID=$(netstat -ano | grep -E "TCP +0.0.0.0:9989" | awk '{print $5}' | head -1)
taskkill //PID $PID //F
go build -o bin/carmonit-server.exe ./cmd/server
bin/carmonit-server.exe > C:/Users/abelz/AppData/Local/Temp/carmonit.log 2>&1 &

# 逐字段对比（MSYS 会把 /manager 当路径改写，必须屏蔽；PYTHONIOENCODING 防 GBK 控制台崩溃）
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 \
  python C:/Users/abelz/AppData/Local/Temp/cmp_api.py \
  /manager C:/Users/abelz/AppData/Local/Temp/recheck_manager.json

# 写接口生命周期回归（结束后自动按 PARITY 标记清理）
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 \
  python C:/Users/abelz/AppData/Local/Temp/cmp_crud2.py
MSYS2_ARG_CONV_EXCL='*' python C:/Users/abelz/AppData/Local/Temp/cmp_crud2.py --clean   # 只清理

# 落库逐列对比 / Redis 共存验收
MSYS2_ARG_CONV_EXCL='*' python C:/Users/abelz/AppData/Local/Temp/probe_db.py /manager/carinfo
python C:/Users/abelz/AppData/Local/Temp/grab_java_cache.py       # 抓 Java 写入的缓存原值
python C:/Users/abelz/AppData/Local/Temp/verify_redis.py          # 登录态共存
python C:/Users/abelz/AppData/Local/Temp/smoke_redis.py 4         # 共存端点多轮稳定性冒烟
```
