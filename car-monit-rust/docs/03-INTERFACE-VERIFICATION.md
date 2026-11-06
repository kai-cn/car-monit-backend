# 03 - Java ↔ Rust 接口逐个校验（GET 全量）

> 校验时间：2026-10-31 首版，2026-11-02 复核并补齐 §4
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

## 2. 结果总览（2026-11-02 复核）

> 本表是 2026-11-02 那一轮的快照。2026-11-04 又改了 TIMESTAMP 会话时区、请求体非列字段过滤、
> 远端透传实体成型与车辆新增语义（§7.7–§9），最新总数见 §11：**285 OK / 6 WARN / 0 FAIL**（真实 api 上游那一轮）。

| 结论 | 数量 | 说明 |
|---|---:|---|
| OK | 282 | 结构、值、类型、**键顺序**均一致（含代码生成 4 个端点） |
| WARN | 6 | 4 处 `sys_upgrade_info` 表缺失的异常文案、`/base/fitting/list` 的 MyBatis 反射异常文案、`/monitor/cache` 的 Properties 桶序，见 §5.1 |
| FAIL | 0 | 首版 13 处 + 共因 2 处均已消除，见 §4 |
| KNOWN | 6 | 依赖不可用上游或 Java 自身故障，见 §5 |
| SKIP | 3 | `geometry/syncAllGeometry(1)`、`tool/gen/synchDb`（有远端写入副作用，避免污染） |

> 进度：首版（2026-10-31）OK 160 / WARN 109 / FAIL 13 → 补 §4 的 13 项后 182 / 98 / FAIL 2
> → 补 Redis 共存与字典/统计口径 186 / 98 / **0** → 代码生成模板引擎（§5）190 / 98 / 0
> → **键顺序全面对齐（§3.3）282 / 6 / 0** → 真实 api 上游 + 框架层四类差异（§10）**285 / 6 / 0**。

> WARN 从 98 降到 6 的原因是原先 87 个 `ORDER-DIFF` 全部消除，只剩 6 个文案/桶序类；
> 剩余的 6 个都不是值差异。

### 3.3 键顺序对齐（本轮）
Java 的响应键序有三套互相独立的规则，Rust 侧分别用三个工具复刻：

| Java 侧 | 顺序来源 | Rust 实现 |
|---|---|---|
| 实体（SysUser/SysRole/CarInfo/…） | Jackson：`BaseEntity` 字段在前（createBy,createTime,updateBy,updateTime,remark,params）→ 类内声明顺序 → 派生 getter（flag/admin/children/nextValidTime/…） | 每个模块一份 `*_KEYS` 常量 + `support::reorder_keys`/`reorder_rows`（纯重排，不增删键）；`manager_crud!` 宏新增可选 `keys: [...]` 参数，生成的 list/get_info 自动重排 |
| `AjaxResult`（`extends HashMap`） | HashMap 桶序：容量从 16 起（`new HashMap<>(n)` 时取 ≥n 的 2 次幂），下标 `(h ^ (h>>>16)) & (cap-1)`，`h` 为 String.hashCode（UTF-16 码元 31 进制），同桶按插入序 | `response::java_hashmap_ordered`，在 `Serialize`/`to_value` 里统一套用；实测校准 `/captchaImage`、`/getInfo`、`/system/user/{id}` 三种键序 |
| `Properties`（`/monitor/cache` 的 info） | Hashtable 桶序：容量 11 起按 `2n+1` 扩容，下标 `(h & 0x7FFFFFFF) % cap`，从最后一个桶往前遍历 | `response::java_hashtable_ordered`（同桶链表的头/尾插与 JDK 版本有关，仍保留 ORDER-DIFF，值一致） |

- 键序基准不是手抄 Java 源码，而是**实测采集**：`tools/endpoint_parity/entity_order.py`
  把 Java 响应的每个容器键序列进 `build/java_orders.json`（83 端点 / 96 容器），
  再据此生成 Rust 的常量表；重采一次即可复核。
- `TableDataInfo` 是 POJO（total,rows,code,msg 声明序），不走 HashMap 规则，保持原样。
- 两处导出文件名（`补缴处理数据`/`常用路线明细数据`/`可疑车辆备份数据`）与
  两处 `{"msg":null,"code":500}`（Java 异常 message 为 null）也一并按实测修正。

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

## 4. 首版 13 处实质差异的处理结果

| 端点 | 首版差异 | 结果 |
|---|---|---|
| `/tool/gen/list`、`/tool/gen/all/list`、`/tool/gen/db/list` | 缺 `columns`/`pkColumn`/树字段等 GenTable 派生键 | 已按 GenTable 实体输出（含 `crud/sub/tree`、MyBatis 嵌套 `<collection>` 的「空子对象」语义）→ OK |
| `/tool/gen/{talbleId}` | `tables/rows/info` 顺序与字段不全 | `selectGenTableAll` 的 join + 按 `table_id` 归并、`setTableFromOptions` 回填、`rows` 与 `info.columns` 审计字段差异 → OK |
| `/manager/confimfree/{id}` | 缺 `carAduitFreeList/carExceptRecordList/difAmount` | 复刻 `selectCarConfimFreeById` 的两次子查询与 `deleteEnd`/BigDecimal 汇总口径 → OK |
| `/manager/confimfree/concernedList` | 缺实体空字段与 `<if>` 过滤 | 按 `CarConfimFree`(43 键) 输出并补齐 Java 的全部过滤分支 → OK |
| `/manager/confimfree/carStatics` | 未透视、未分页 | 复刻 `getPCCarStatistics`：先分页分组行，再按固定逃费类型 10~60 透视，`total` 取单位数 → OK |
| `/manager/confimfree/except/{exceptIds}` | 缺状态校验 | 复刻五级校验（空 ids／流水不存在／多车／多单位／已追缴）与成功体字段（`backCol1="0.3"`、`amount` 用未取整的和计算）→ OK |
| `/manager/aduitfree/incomeStatics` | 行数不同 | 补 PageHelper 默认分页（`pageNum=1,pageSize=10`）+ `PCIncomeStaticsVO` 键序 → OK |
| `/manager/aduitfree/incomeDetailList` | 行数不同 | Java 控制器把空 `orgId` 换成哨兵 `-1`（恒空结果）；Rust 此前不过滤 → OK |
| `/manager/suspicious/{id}` | `trackJosn/checkList/trailList` 缺失 | 复刻 `selectCarSuspiciousById`：真实 `track_josn`、`checkList` 排序与 24 键实体、`TrailInfo`/`ZdataTrailTracks(51)`/`TrailBo(32)`、`pilenoDec` 还原、`getCarGeometry` 桩号区间拼路径、`getTrailDevBO` 设备异常统计 → OK |
| `/manager/suspicious/listHistory`、`/manager/cartrackinfo/list*`、`/manager/aduitfree/*`、`/manager/exceptrecord/*` | 键顺序 | 统一按 Java 实体声明顺序输出 → WARN 消除 |
| `/manager/cartrackinfo/listByCarByTime` | `lon/lat` 末位差 1 ULP | `serde_json` 打开 `float_roundtrip`；路径点字符串按字面量拼接（hutool 用 BigDecimal 保留原文）→ OK |
| `/system/dict/data/type|typemore/{dictType}` | `params`/审计字段被剥掉 | 缓存命中时保留 FastJson2 写进 `params` 的 `@type` 条目（Java 自身也会输出）→ OK |

剩余 2 处曾报 FAIL 的端点共用同一根因，且**不是 Rust 侧缺陷**：本机的 `car-monit-py` / `car-monit-go`
端口与两端共用同一个 Redis，它们写入的值没有 FastJson2 的 `@type`，Java 读取后强转失败返回
`code:500`，而 Rust 容错解析后正常返回数据。

| 端点 | Java（被污染时） | Rust | 被污染的键 |
|---|---|---|---|
| `/monitor/online/list` | `JSONObject cannot be cast to LoginUser` | 200 + 在线列表 | `login_tokens:*` |
| `/manager/bigScreen/carLocation` | `JSONObject cannot be cast to CarInfo` | 200 + 车辆定位 | `car_list` |

处理方式：新增 `tools/endpoint_parity/redis_compat.py`（`--apply` 可删除这些无 `@type`
的键；缓存会由任一端的下次读取回源重建，登录会话则被踢掉），把它作为每次对拍前的
体检步骤。体检通过（或手动 `--apply` 清理）后复跑，两个端点均为 **OK**：
Java 200 + 与 Rust 一致的在线列表 / 车辆定位数据。真正的修法仍是让另外两个端口
也写 `@type`，或给各端口隔离 Redis DB。
Rust 自身写入的登录态、`section_list`、`sys_dict:*`、`car_warning*`、`lxbh_jdwd:` 均已带
`@type`（见 §3.1）。

## 5. 环境受限 / KNOWN（6）

- 远端代理（`vehicleMonitor.baseUrl` 的 mock 返回的结构 Java 反不出来，Java 侧 500/非法值）：
  `/base/feeGantry/{bigId}`、`/base/snapshotflow/{bigId}`、`/base/snapshotflow/earliest-time`、
  `/base/geometry/getHenDa`。同族的 `list` 类端点（`/base/feeGantry/list`、
  `/base/feerecords/{bigId}`、`/base/feestationexit/list|{bigId}`）本轮已可比对，不再列 KNOWN。
- Java 自身故障：`/monitor/server`（`jna Memory.close` NoSuchMethodError，Java 直接 500，
  Rust 用 sysinfo 正常返回）、`/base/cdc/config`（Java 返回非法 JSON，无法解析比对）。
- 表缺失（两端均 500，仅文案不同）：`/system/upgradeInfo/*`。
- 代码生成（Rust 自研 Velocity 子集，已完成）：`/tool/gen/preview`、`/tool/gen/download`、
  `/tool/gen/genCode`、`/tool/gen/batchGenCode` 均由 KNOWN 转 OK。
  - `src/service/velocity.rs`：指令/表达式/引用字面量回显/`#foreach` 作用域变量，
    空格吞噬按 Java 逐条对齐——独占行的指令吞本行缩进与行尾换行；行首 `#if/#elseif` 头部
    额外吞掉**同行**紧随其后的空格；只有 `#foreach` 的收尾 `#end` 吞换行（`#if` 的 `#end`
    不吞，mapper.xml 的列清单靠它分行）；模板 CRLF **原样保留**在产物里（Java 侧模板文件
    本身就是 CRLF，之前归一成 LF 会让每个文件少若干个字节）。
  - `src/api/generator/gen_render.rs`：prepareContext / getTemplateList / getImportList
    的 HashSet 桶序 / dictionaryKeyToCamelCase / setPkColumn / initFilterColumnInfo /
    initUploadInfo / initRichTextInfo / columnDialogInfo / parentMenuId / getFileName / getGenPath。
    `readConverterExp` 按 Java 语义在备注为 null 时返回 null（Velocity 原样打印引用文本）。
  - `src/api/generator/gen_zip.rs`：无依赖 ZIP 写入器（STORE + CRC32）。Java 走
    `java.util.zip`（DEFLATE + data descriptor），**压缩包字节必然不同**（Java 14KB /
    Rust 72KB），可比的是解压后的条目名、顺序与内容。
  - 对拍结果：`gen_table` 全 **53 张表 × 10 个模板 = 530 个文件**与 Java **逐字节一致**
    （`gen_zip_diff --all-tables`，不一致 0）；表 231 的 preview 10 个模板与 Java 基准
    逐字节一致（`gen_preview_diff`）；`genCode` 落盘的 7 个文件与 Java 写到
    `<user.dir>/src/` 的同名文件逐字节一致。
  - 仍留的一处刻意留白：`field_map_string` + `link_table_id` 的关联表回查
    （LinkTableField / linkTable / tableFileInfo）未迁移，遇到配置了关联列的表
    preview/download 会显式报错而不是静默生成错误代码；本库 `gen_table` 无此类配置。
  - `genCode` 在 `gen_path=/` 时按 Java 规则写到「进程工作目录/src/」，从本 crate 启动
    会落到 `car-monit-rust/src/main/`、`src/vue/`（已在 `.gitignore` 排除，验证后已清理）。
- 可疑车辆详情的 `raodTrailList` 依赖外部路网/腾讯地图 API：两端在 API 不可用时都会
  落到本地桩号拼接的兜底分支（`getCarGeometry`），本次比对即该分支，结果一致；
  若外部 API 可用，返回值取决于上游。

## 5.1 剩余 11 个 WARN（均非值差异）

| 端点 | 类别 | 说明 |
|---|---|---|
| `/system/upgradeInfo/list`、`/newest`、`/export`、`/{id}` | MSG-DIFF | 库里缺 `sys_upgrade_info` 表，两端都 500、`code` 一致，只是 MyBatis 拼装的异常文本 vs sqlx 文本不同（要再压缩差距只能硬编码对方文案） |
| `/base/fitting/list` | MSG-DIFF | Java 的 Mapper 里 `<where>` 引用 `#{id}` 而 `ZdataTrailFitting` 没有该 getter → MyBatis `ReflectionException`；Rust 直接把 SQL 交给 MySQL，报 `Unknown column 'id'`。同为 500 |
| `/monitor/cache` | ORDER-DIFF | `data.info` 是 Jackson 直接序列化 `Properties`（Hashtable）：桶容量与下标规则已复刻（`java_hashtable_ordered`），同桶内链表的头/尾插随 JDK 版本而变，仍有局部错位；键集合与值完全一致 |
| `/tool/gen/list`、`/all/list`、`/db/list`、`/{talbleId}` | ORDER-DIFF | GenTable/GenTableColumn 尾部派生 getter（`sub`/`crud`/`tree`、`insert`/`edit`/`capJavaField`/`superColumn`/`increment`/`usableColumn`）没有 `@JsonPropertyOrder`，顺序取决于反射给出的方法序：**同一 JVM 实例内稳定、跨重启会变**（实测本轮 `sub,crud,tree` → `tree,crud,sub`），Rust 只能对齐其中一次。详见 §11 |
| `/monitor/online/list` | LEN-WARN + TOTAL-WARN | 两端各连自己的 Redis db（db0/db15），在线会话条数天然不同；`userName`/`ipaddr`/`deptName` 等业务值仍逐字段实比（§10.7） |

## 6. 校验脚本（已入仓库）

脚本从本机临时目录迁到 `car-monit-rust/tools/endpoint_parity/`，两端地址、账号、
输出路径全部参数化，可直接复跑或被 CI 调用（详见该目录 `README.md`）：

| 文件 | 作用 |
|---|---|
| `endpoints.py` | 从 `docs/01-baseline/02-endpoints.md` 生成 `endpoints.json`（GET 297 条） |
| `client.py` | Redis 验证码读取 + 两端登录 + HTTP；账号只取环境变量 `PARITY_USER`/`PARITY_PASSWORD`，仓库内不落口令 |
| `compare.py` | 逐端点对比并输出 `report.json`；`--only/--skip/--workers/--strict/--quiet` |
| `redis_compat.py` | 共存体检：列出（`--apply` 时删除）缺 FastJson2 `@type` 的共享缓存值 |
| `entity_order.py` | 采集 Java 每个响应容器的键顺序到 `build/java_orders.json`（Rust 侧 `*_KEYS` 常量的唯一依据） |
| `gen_preview_diff.py` | `/tool/gen/preview` 逐模板与 Java 基准比对（`--save-oracle` 采集基准，按 `newline=''` 读回，CRLF 不参与归一） |
| `gen_zip_diff.py` | `/tool/gen/download`、`/tool/gen/batchGenCode`：解压后比条目名/顺序/字节；`--all-tables` 跑全表 |
| `job_invoke_matrix.py` | 写入路径：建任务→立即执行→读 `sys_job_log`，比 `status`/`jobMessage`/`exceptionInfo` 首行（`JobInvokeUtil` 的真实结果），25 个 target |
| `cron_matrix.py` | 写入路径：59 条表达式的 Quartz 接受度 + `nextValidTime` + 落库 status/misfire，建成功的行用完即删 |
| `job_write_matrix.py` | 写入路径：`add/edit/changeStatus/run/remove` 的 18 条 Java 语义分支（含事务回滚与不回滚两类） |
| `post_smoke_matrix.py` | 14 个新增端点 × 两种请求体（干净 / 掺 `params` 等非列字段）的对拍，`last_insert_id` 解码与列过滤两类回归的守门用例 |
| `xlsx_fixture.py` | 造导入夹具：往自带模板追加数据行（只改 `sheet1.xml` 与 `<dimension>`），`FX_TEMPLATE` 换模板 |
| `import_probe.py` | 把 xlsx 上传到两端两个导入端点，比原始响应（§8） |
| `write_crud_matrix.py` | 写入路径：从 `manager_crud!` 宏块自动推导 11 张表的 route/table/列，逐表 POST→按 id 回读→DELETE→再回读；两端标记不同后缀（同一张表），比 `msg`/`code`/`data` 有无、落库内容（忽略 id/审计列/标记列）、删除后行为 |
| `mock_vehicle_monitor.py` | `vehicleMonitor.baseUrl`（127.0.0.1:9901）的桩上游，返回**故意不全**的样本字段，让 `/base/*` 透传端点的「Forest→实体→Jackson」成型行为可比对（§9） |

```bash
cd car-monit-rust
python -m tools.endpoint_parity.endpoints                       # 生成清单
python -m tools.endpoint_parity.redis_compat                     # 共存体检
python -m tools.endpoint_parity.compare --report build/parity-report.json --strict
python -m tools.endpoint_parity.compare --only /tool/gen --only /manager/confimfree   # 局部复跑
python -m tools.endpoint_parity.gen_preview_diff --table-id 231  # 代码生成逐模板
python -m tools.endpoint_parity.gen_zip_diff --all-tables        # 代码生成 zip 全表对拍
python -m tools.endpoint_parity.entity_order --report tools/endpoint_parity/report.json  # 重采 Java 键序
```

分类口径：`ORDER-DIFF`/`MSG-DIFF`/`TOTAL-WARN` 记 WARN，其余硬差异记 FAIL；
上游透传且主键随机的端点在 `SHAPE_ONLY` 里只比结构；
`msg` 里的 UUID 与时间戳归一后再比。
CI 入口是仓库根 `.github/workflows/car-monit-rust.yml`：`push/PR` 跑
`cargo fmt --check`、`cargo clippy -D warnings`、`cargo test`；
两端对比依赖本机 MySQL/Redis + 运行中的 Java，公共 runner 起不来，
因此只在 `workflow_dispatch` 显式填入 `java_base`/`rust_base` 与 secrets 时执行，
并以 `--strict` 的退出码作为门控。

`endpoints.json`、`report.json`、`build/` 属生成物，已在
`tools/endpoint_parity/.gitignore` 里排除。

## 7. 写入路径（POST/PUT）对拍

§1–§5 的 297 条只覆盖 GET。任务 #26（复刻 `JobInvokeUtil`）打开了 `/monitor/job`
的写入路径，下面先记录实测到的 Java 事实，再给逐条对齐后的结果（§7.4）。
`cron_matrix.py` 首轮（2026-11-03 上午）是 **42/59 不一致**，差异集中在两处——
Rust 侧 `last_insert_id()` 解码失败（见 §7.1）与 Quartz 专有语法（`L/W/#`、7 段）未被接受。

### 7.1 顺手修掉的真实缺陷

`select last_insert_id()` 的列元信息是 **BIGINT UNSIGNED**，sqlx 按 `i64` 解码直接报
`mismatched types; Rust type i64 (as SQL type BIGINT) is not compatible with SQL type BIGINT UNSIGNED`。
5 处新增端点全部命中：`sys_user`/`sys_role`/`sys_dept`/`sys_job`/`gen_table` 的 `POST`
（事务内取回自增 id，解码失败即回滚 → 接口恒 500，GET 对拍看不出来）。已统一改为 `u64` 再转 `i64`，
并由 `post_smoke_matrix.py`（§7.4）验证 5 个新增端点两端一致。

### 7.2 Quartz 接受度（Java 实测，59 条表达式）

| 表达式 | Java | 要点 |
|---|---|---|
| `0 0 2 ? * L` / `6L` / `1LW` | 接受 | DOW 的 `L` = 该周几的最后一个；裸 `L` 先按 `add_to_set(7,7,0)` 落成 SAT |
| `0 0 2 L * ?` / `LW` / `L-3` / `15W` / `1W,3` | 接受 | `L-31`、`LW,1` 拒绝；带 `W` 时只用 `daysOfMonth.first()`，列表里其余值被忽略 |
| `0 0 2 ? * 2#1` / `5#2,6` / `5,6#2` | 接受 | `#` 全表达式只许一个；`nthDayOfWeek` 也只用 `daysOfWeek.first()` |
| `0 0 2 ? * 2-6L` | 接受 | 区间吃掉 `L`：`checkNext` 在 `-` 分支直接 return，尾部的 `L` 从未被解析 → 等价 `2-6` |
| `0 0 2 ? * 7W` / `3#0` / `3#6` / `0`（DOW） | 拒绝 | DOW 取值 1–7，`#` 后 1–5，`W` 只许出现在 DOM |
| `0 0 2 1 1 ? 2099` / `0 0 2 1 1 ? *` | 接受 | 第 7 段（年）参与校验与计算 |
| `0 0 2 1 1 ? 1969` / `2400` | **校验通过** | 年字段不做 1970–2299 范围校验；建 trigger 时才失败（见 §7.3） |
| `0 0 2 * * ? 2099 2100` | 接受 | 第 8 段起被 `if (exprOn > YEAR) break` 丢弃 |
| `0 0 2 * * ?x` | 接受 | `?` 分支的越界判断写成 `(i + 1) < len`，`?x` 逃过检查（Java 自身的 bug） |
| `*/0 * * * * ?` | 接受 | `increment <= 0` 时补 1 并塞 `ALL_SPEC` 哨兵（99） |
| `0 0 2 * 1 ?` / `? * *` | 接受 | DOM/DOW **必须恰好一个为 `?`**；`?`/`?`、`*`/`*`、`*`/`5` 一律拒绝 |
| `? 0 2 * * ?` / `0 0 2 * ? 1` | 拒绝 | `?` 只许 DOM/DOW |
| `0 0 2 ? jan ?` | 拒绝 | 双 `?`；小写名本身没问题（构造器先 `toUpperCase(Locale.US)`） |

哨兵值：`ALL_SPEC_INT = 99`、`NO_SPEC_INT = 98`；`MAX_YEAR = 进程启动年 + 100`（静态初始化）。
`CronUtils.getNextExecution()` 对非法表达式**抛** `IllegalArgumentException(pe.getMessage())`，
所以 `nextValidTime` 落在非法 cron 上是整接口 500，不是 `null`。

### 7.3 `/monitor/job` 写入语义（Java 实测）

- `POST` 缺 `cronExpression`（null）→ `CronExpression` 构造器抛 **非** ParseException 的
  `IllegalArgumentException` → `{"msg":"cronExpression cannot be null","code":500}`；
  空串与非法串才走 `CronUtils.isValid` → `{"msg":"cron表达式不正确","code":500}`。**两条路径必须分开。**
- Java 侧**没有** target 白名单：`Constants.JOB_WHITELIST_STR`/`JOB_ERROR_STR` 在本仓库无调用方，
  `SysJobController.add/edit` 只校验 cron。Rust 现在多一条 `目标字符串不在白名单内` 的拒绝，属超集。
- `insertJob` 先 `job.setStatus(PAUSE)`：**新增行恒为 `status='1'`**，与请求体里的 `status` 无关。
- `misfirePolicy` 非 `0/1/2/3` → `TaskException`（`extends RuntimeException`）→
  `{"msg":"The task misfire policy '9' cannot be used in cron schedule tasks","code":500}`，
  `@Transactional` **回滚**，行不残留。实体默认值 `MISFIRE_DEFAULT = "0"`（请求体不传也是 `"0"`）。
- 年份越界等「永不触发」→ `CronTriggerImpl` 阶段 `SchedulerException`（checked，默认**不回滚**）→
  `{"msg":"Based on configured schedule, the given trigger 'DEFAULT.TASK_CLASS_NAME172' will never fire.","code":500}`，
  **行留在库里**（实测残留 172/173 两行，已清理）。
- `run`：`triggerJob(getJobKey(body.jobId, body.jobGroup))`，key 不在调度器里 →
  `{"msg":"The job (DEFAULT.TASK_CLASS_NAME999999) referenced by the trigger does not exist.","code":500}`；
  `group` 取请求体，缺省 `DEFAULT`（`KeyImpl` 的字段初值），且 Java 启动时 `init()` 装入**全部**行（暂停的也在），
  所以暂停任务照样能「立即执行」。
- `changeStatus`：控制器先 `selectJobById` 再 `newJob.setStatus(...)` → 行不存在时 NPE →
  `{"msg":null,"code":500}`；`status` 非 `0/1` 时 `rows` 恒 0 → `操作失败`，**库不改**。
- `remove`：`deleteJobByIds` 对每个 id `selectJobById` 后解引用 → 行不存在同样 `{"msg":null,"code":500}`；
  `DELETE /abc` → `请求参数类型不匹配，参数[jobIds]要求类型为：'[Ljava.lang.Long;'，但输入值为：'abc'`。
- `sys_job_log`：`jobMessage = jobName + " 总共耗时：" + runMs + "毫秒"`（没有「任务执行成功」前缀）；
  `jobGroup` 取**库里的行**；`exceptionInfo = StringUtils.substring(ExceptionUtil.getExceptionMessage(e), 0, 2000)`，
  即完整 Java 栈（Rust 只能对齐**首行** `类全名: message`，后续帧无法复刻）。

### 7.4 本轮结果（2026-11-03，四张矩阵全绿）

| 矩阵 | 覆盖 | 结果 |
|---|---|---|
| `cron_matrix.py` | 59 条表达式的接受度 + `nextValidTime` + 落库 `status`/`misfire_policy` | **0 / 59 不一致** |
| `job_invoke_matrix.py` | 25 个 `invokeTarget` 的 `sys_job_log` 结果 | **0 / 25 不一致** |
| `job_write_matrix.py` | `add/edit/changeStatus/run/remove` 的 18 条 Java 分支 | **0 / 18 不一致** |
| `post_smoke_matrix.py` | 5 个新增端点 | 5 / 6 一致，剩 1 条见 §7.6 |

实现落点：

- `src/service/quartz_cron.rs`（新）——按 Java 逐分支移植 `buildExpression/storeExpressionVals/checkNext/addToSet`，
  三个怪癖照抄：`?x` 因 `(i + 1) < len` 的越界判断逃过检查、第 8 段起被 `if (exprOn > YEAR) break` 丢弃、
  年份字段不做范围校验（改由「永不触发」报错）；`MAX_YEAR = 进程启动年 + 100`；
  `next_after` 用逐字段前跳扫描，`L/#` 只取 `daysOfWeek.first()`、`nW` 只取 `daysOfMonth.first()`（与 Java 一致）。
  单测 `service::quartz_cron::tests` 把上面这张表钉住（含 31 条 `nextValidTime` 基准值）。
- `src/service/job_invoke.rs`（新）——`JobInvokeUtil` 的解析与执行：bean 表按 Java 类全名 + 方法签名登记，
  异常对齐首行（`NoSuchBeanDefinitionException: No bean named 'x' available`、
  `NoSuchMethodException: com.ruoyi.quartz.task.RyTask.ryParams(java.lang.String, java.lang.String)`、
  `NumberFormatException: For input string: "abc"`）。
  类全名形式的 target 走 `Class.forName(...).newInstance()`，新实例没有注入依赖，
  Java 实测抛的是 `java.lang.reflect.InvocationTargetException`（不是 NPE 本身），照此对齐。
- `src/api/quartz/job.rs` + `src/service/quartz_runtime.rs`——注册表按 Java 的 `JobKey(jobId, jobGroup)` 建模：
  启动时装**全部**行（暂停的也在，所以「立即执行」照样能跑）、`run` 未注册时回
  `The job (…) referenced by the trigger does not exist.`、misfire 非法与「永不触发」都**不回滚**、
  只有 NPE（请求体显式给 `misfirePolicy: null`）才回滚——与 §7.3 的实测逐条对应。
- Java 侧**没有** target 白名单（`Constants.JOB_WHITELIST_STR`/`JOB_ERROR_STR` 无调用方），
  Rust 原先多出的 `目标字符串不在白名单内` 拒绝已删除。

### 7.5 顺手修掉的另外两处真实缺陷

1. `POST /tool/gen/importTable`：`information_schema` 结果集的列名在元信息里是**大写**
   （`TABLE_NAME`），Rust 原样按 `table_name` 取值 → 取不到 → 回落成空串，
   于是登记出 `table_name=''` 的 `gen_table` 脏行、且 `gen_table_column` 一条都不写，接口却回「操作成功」。
   已按 Java mapper 的写法给两处查询起驼峰别名（`column_name as columnName` 等）。
   同类写法在 `createNew`（按表名同步列）里也有一份，一并修了。脏行已清理。
2. `POST/PUT /system/dept` 与 `/system/user`：Java 靠解引用取父部门/所属部门
   （`parentBO.getTreeLeavel() + 1`、`sysDept.getDeptName()`），父节点不存在或 `tree_leavel` 为 NULL 时
   **直接 NPE**（响应 `{"msg":null,"code":500}`，什么都不写）。Rust 原先用 `unwrap_or` 兜底，
   会往库里插出挂在不存在父节点下的部门/用户。已改成逐条对齐：不存在即回空 msg。

### 7.6 未复刻的 Java 侧缺陷（记录）

`POST /system/user` 在 Java 里**任何**入参都失败：MyBatis 在设置参数阶段抛
`IndexOutOfBoundsException: No group 2`（`SysUserMapper.insertUser`，异常文本里带 jar 路径），
所以 Java 侧新增用户功能整体不可用。Rust 侧能正常写入（并正确带上 `buss_name`/`tenant_id`）。
这条不复刻——要对齐的只是「部门不存在时的 NPE」（§7.5），其余按正确行为实现。
`jobMessage` 里的耗时毫秒、`exceptionInfo` 的完整栈、报错文案里嵌的自增 id 都已在脚本里归一化后再比。

### 7.7 `manager_crud!` 11 张表的写入对拍（2026-11-04）

`write_crud_matrix.py` 从 `src/api/**/*.rs` 里的 `manager_crud!` 宏块自动推导 route/table/列，
逐表 POST→按返回 id 回读→DELETE→再回读。**10 OK / 1 WARN / 0 FAIL**
（唯一的 WARN 是 §7.8 的报错文案包装，行为两端一致）。

两端标记必须不同后缀：两端写的是**同一个库**，标记相同就会各自认领对方的行——
第一版正是这样，`/manager/querylog` 报出一个根本不存在的「删除失败」。

这一轮挖出三个真实缺陷，全都只出现在写入路径或空表上，GET 全量 297 条一个都看不见：

1. **`TIMESTAMP` 列读写差 8 小时**（`car_*`/`gantry_*` 全部表的 `create_time`/`update_time` 是
   `timestamp(3)`，`sys_*`/`flow_*` 是 `datetime`，所以只有 manager 切片受影响）。
   - 读：SQLx 里 `NaiveDateTime` 与 `ColumnType::Timestamp` **类型不匹配**，`try_get` 失败后
     一路落到兜底的 `try_get::<String>` 也失败 → `createTime` 恒为 `null`，Java 侧是有值的字符串。
     11 个 list 端点 + 全部 `{id}` 详情都受影响；GET 全量把它们归到「动态数据只比结构」，因此没报。
   - 写：SQLx 建连接时默认 `SET time_zone='+00:00'`，而 Java 的 JDBC URL 是
     `serverTimezone=GMT%2B8`。Rust 把本地墙上时钟 `'2026-11-03 19:02:27'` 当 UTC 存 →
     Java 读到的是 `2026-11-04 03:02:27`，列表按 `create_time desc` 排序时新行会被顶到前面，
     等于两端排序基准不同。
   - 修：`Settings::mysql_session_timezone()` 解析 Java 那条 URL 的 `serverTimezone`
     （`GMT+8`/`GMT+8:30`/`+08:00`/`UTC` → `+08:00` 之类），`AppState::connect` 用它覆盖 SQLx 默认；
     `db/rows.rs` 给 `TIMESTAMP` 补 `DateTime<Utc>` 解码并取字面量。
     实测两端 `createTime` 逐字节相同，且新写入的行在库里的墙上时钟也相同。
     `timestamp(3)` 的毫秒位 Java 是 `.910` 这类，Rust 走字符串写入恒 `.000`——
     出参都是秒精度（`@JsonFormat yyyy-MM-dd HH:mm:ss`），不影响响应。
2. **请求体里任何非表列字段都会让新增/修改整体失败**：RuoYi 前端每个 `add`/`edit` 请求体都带
   `params`（`BaseEntity.params`），MP 标注 `exist=false` 的 `applyTime1` 等同理；
   Java 的 Jackson 忽略未知属性，Rust 原样拼进 `INSERT` → `1054 Unknown column 'params'`，
   即**两端所有 manager 新增接口在真实前端请求下只有 Rust 是 500**。
   修：`support::table_columns()`（按 `information_schema` 缓存）+ `filter_entity_columns()`，
   `insert_entity`/`update_entity_by_id` 先按表真实列过滤再拼 SQL——与 Java「不是列的字段不参与 SQL」一致。
3. **四张空表把整类出参缺陷藏住了**：`car_fee_record`/`car_route_detail`/`car_route_info`/
   `car_split_record` 库里 0 行，list 与 `{id}` 都没有行可比。造出探针行后立刻暴露三处：
   实体里 `@TableField(exist=false)` 的 `applyTime1`/`applyTime2`/`createTimeStr` 在 Java 出参里
   是显式 `null` 键（Rust 缺键）、`inTime`/`outTime`/`lastPassTime`/`nextPassTime` 的
   `@JsonFormat(pattern="yyyy-MM-dd")` 没做（Rust 出的是 `yyyy-MM-dd HH:mm:ss`）、键序未按实体声明排。
   已给这四个宏块补 `select` 里的 `null as …`、`dates:` 与 `keys:`——`keys` 直接抄 Java 实测的键序。

顺带确认：软删后 Java 的 `selectXxxById` **不带** `del_flag='0'`，按 id 仍能查到行，Rust 一致。

### 7.8 复刻与不复刻的边界（本轮新增）

- **复刻**：`POST /manager/carsuspiciousback` 不带 `id` 时 Java **必失败**。
  `CarSuspiciousBack extends BasePlusEntityInput`（`@TableId(type = IdType.INPUT)`），
  而 `saveCarSuspiciousBack` 只在 id 非空时走 `updateById`、else 直接 `insert`，全程没有 `setUUID`，
  MP 又把 `id` 恒放进 INSERT 列清单 → `Column 'id' cannot be null`。
  Rust 原先自己生成 uuid 写成功。现在 `support::ID_INPUT_TABLES = ["car_suspicious_back"]`
  关掉主键生成并显式写 `id = NULL`，两端同一 MySQL 报错、同样一行都不写。
  （`CarInfo` 虽然也继承 `BasePlusEntityInput`，但 `saveCarInfo` 里有
  `carInfo.setId(StringUtils.getUUID())`，所以不在这一列——这类区别只能逐个 service 读，不能按基类推。）
- **不复刻**：数据库报错的**包装文案**。Java 是 MyBatis 的一整段
  `### Error updating database. Cause: …### SQL: INSERT INTO …### Cause: …`，
  Rust 是 `error returned from database: 1364 (HY000): …`。
  两端的 **HTTP 码、SQL 是否执行、写没写行、`data` 有无**完全一致，只差在文本模板；
  复刻它需要在 Rust 里重算 MP 的动态列清单（随请求体变化），换来的只是错误字符串逐字相同，
  因此记为已知不一致，`write_crud_matrix.py` 把这类情况判 WARN 而不是 FAIL。

### 7.9 `/system/*` 与自定义新增端点（2026-11-04，14 个端点 × 两种请求体）

`post_smoke_matrix.py` 从 5 个用例扩到 14 个（`/system/user|role|dept|post|config|dict/type|dict/data|notice|menu`、
`/monitor/job`、`/manager/carinfo`、`/manager/carsuspiciousback`、`/tool/gen/importTable`），
每个用例跑两遍请求体：干净体，以及掺上前端真实会带的非列字段
（`params`、`pageDomain`、`applyTime1/2` 和一个彻底不存在的键），
既比两端一致，也比「同一端掺字段前后是否同构」。
结果：**54 组比较 0 不一致**，2 组记 KNOWN（§7.6 的 `POST /system/user`）。

探针名必须**按用例区分**：RuoYi 的判重（角色名、权限字符、车牌、字典键）都不看 `del_flag`，
上一遍留下的软删行会让下一遍直接报「已存在」——第一版报出的两条 FAIL 其实是探针自己在撞自己。

这一轮修掉两处：

1. `POST/PUT /system/role`（以及 `changeStatus`）自己拼 SQL（同一事务里还要写 `sys_role_menu`），
   没经过 `insert_entity`，所以 §7.7 的列过滤对它无效：掺 `params` 就
   `1054 Unknown column 'params' in 'field list'`，Java 照样建成功。
   现在这些路径统一先过 `support::entity_for_table(pool, table, entity)`；
   `sys_dept` 同样处理。`sys_user`/`sys_profile` 是按字段白名单取值的，本来就不会带非列字段。
   注意 `menuIds` 之类不是列、但要在过滤**前**取出来，否则角色与菜单的关联会静默丢掉。
2. `POST/PUT /manager/carinfo` 缺了 Java `saveCarInfo` 的三段语义：
   - **车牌判重**：`isExitsCar` = `del_flag='0' and car_no=?`（编辑时再 `and id<>?`），
     命中就**整条不写**并回 `车牌号存在重复，请确定！`。Rust 原先无条件写 → 重复车牌能进库。
     （`updateRedisCarList` 之前也没有，见 §7.9.1。）
   - 新增分支：`escapedAmount` 为 null 时补 `BigDecimal.ZERO`、显式写 `updateBy/updateTime`
     （MP 的自动填充在 INSERT 时同样写这两个），Rust 原先留 NULL。
   - `carNo` 先 `CommonUtil.isNull`（null→""、trim）再判重与落库，两端存的是 trim 后的值。

#### 7.9.1 `car_list` 缓存共存实测

Java 每次 save/import 都整体重写两个**无 TTL 的字符串键**：`car_list`（`CarInfo` 全字段）与
`car_list_jc`（`CarVO`，只有 `carId`/`carNo`），消费方是 `getRedisCarList()`
（大屏 `/manager/bigScreen/carLocation`、`trackTask`、可疑车）——批量删除走的是
`deleteCarInfoByIds`，**不**刷缓存，这条不对称照抄。

实测两端各自写入的缓存：同一行的**键集合、键序、取值完全相同**
（`@type` 在最前、字段名**字典序**、null 不写 —— FastJson2 的写法，不是 Jackson 的实体序）。
Java 读 Rust 写的缓存走 `/manager/bigScreen/carLocation` 返回 200（它遍历 `List<CarInfo>`
并调 getter，形状不对就会像 `login_tokens` 那样抛 ClassCastException）。
唯一残留差异：FastJson2 给 Long 值加 `L` 后缀（`"tenantId":100L`），Rust 写 `100` ——
Java 侧字段类型已知，反序列化照常；Rust 侧 `sanitize_fastjson2` 读 Java 的 `100L` 也没问题。

## 8. Excel 导入两端对拍（`/manager/exceptrecord/import`、`/manager/carinfo/import`）

夹具：直接用 `config/templates/down/importCar*.xlsx` 追加数据行（`tools/endpoint_parity/xlsx_fixture.py`，
只改 `xl/worksheets/sheet1.xml` 与 `<dimension>`），两端各上传一次比原始响应
（`tools/endpoint_parity/import_probe.py`，纯标准库写 multipart，不需要 openpyxl）。

实现落点：`src/common/import_util.rs`（`ImportSysUtil` 的取值规则 + `ImportUtil.importExcel` 的规则码校验）
与两个控制器各自的导入函数。逐条实测到的 Java 事实：

- 报错行号是**数据行下标 + 2**（`dataRtnExcel*` 从表头后一行起，`getErrorBO` 再 +1），两个端点一致。
- 错误项 JSON 形状来自 `ImportErrorEntity`：`{"rowNo":…,"colName":…,"message":…}`；消息只有规则码
  那几种文案（`不能为空`/`不是小数`/`不是正整数`/`日期格式（年月日时分秒）不正确`…），列名取
  `ImportEntity.colName`，所以异常流水模板里「小计」这类空列名的 `colName` 就是空串。
- **业务字典翻译只在整份导入一条规则错误都没有时才执行**（Java 的 `if (errorList.size() == 0)`），
  所以规则错误会完全遮蔽「XX 不存在,请在字典菜单维护！」；`errorList` 超过 100 即 break。
- `ImportSysUtil` 取值：`DecimalFormat("#.##")`（无分组、最多两位、`0.5` 写成 `.5`、HALF_EVEN）；
  日期单元格在 `getCellFormatValue08` 里是 `yyyy-MM-dd HH:mm:ss`（表头校验用的 07 是 `yyyy/MM/dd`）；
  所有值 `trim()`；整行为空或首列是 `break`/`结束` 立即停止读取。
- 异常流水模板有两套表头位置：Java 先试**第 2 行**再试**第 3 行**，两次都用 `initListTwo()` 的列名比对
  （`initListThree()` 因为 `gzListThree = initListTwo()` 这句写法是死代码，照抄不纠正）。
- 落库后的响应是**内存实体**而不是回读的库行，因此：异常流水的 `delFlag` 为 `null`（填充不写它），
  金额标度取自表格字符串（`20` 而不是 `20.00`）；车辆导入的新增分支显式写
  `id/delFlag='0'/createBy/epsId/createTime`，自动填充连 `updateBy/updateTime` 一起写，`tenantId` 留 `null`。
  这四处都是我先按「回读库行」实现、再由两端比对纠正出来的差异。
- 异常流水「车牌在 `car_info` 查不到」不报错（Java 那行报错是注释掉的），改为按车牌+颜色+车型车种补建车辆；
  车辆/收费站/字典的取值集合与列表接口共用同一条 SQL（含 `selectCarInfoList` 的 `not exists` 排除条件）。

两端一致的用例：错误路径（缺必填、坏日期、坏小数、坏正整数、两套表头位置）与成功路径
（车型/车种/车牌颜色/多值逃费类型翻译、`difAmount` 差额、入口出口站编码回填、按车牌决定新增或修改）；
成功响应的键序与取值逐项相同（`id`/时间戳归一后比）。附带修正：`carinfo` 导入原先自己编错误消息
并用 `rowNum/errorMsg` 键名，现已与 Java 的 `ImportErrorEntity` 完全一致。

回归：GET 全量 297 条仍是 **OK 282 / WARN 6 / FAIL 0 / KNOWN 6 / SKIP 3**（本轮数字；2026-11-04 真实上游复跑见 §11）。
期间 `/monitor/online/list` 短暂变 FAIL——Redis 里有一条早期遗留、缺 FastJson2 `@type` 的
`login_tokens:*`，Java 反序列化成 `JSONObject` 后强转 `LoginUser` 抛 500（Rust 侧容错所以照出 40 行）；
`tools/endpoint_parity/redis_compat.py --apply` 删掉即恢复，两端写登录态的代码本身没问题。

## 9. 远端透传端点的实体成型（`/base/*`，2026-11-04）

`vehicleMonitor.baseUrl`（127.0.0.1:9901）的外部 Python 服务不在本仓库，此前对拍靠一个
**没入库的手搓桩**，环境不可复现（桩一停，`/base/*` 与 `/manager/cartrackinfo/listByCarId`
立刻从 OK 变成一堆 `Connection refused`）。现在桩进了仓库：
`tools/endpoint_parity/mock_vehicle_monitor.py`，并且**故意只回部分字段**——
真实上游同样不会把实体的每个字段都给全，而这正是两端最容易分叉的地方。

Java 侧 `Forest @Get → 反序列化成 domain 实体 → Jackson 输出`，因此：
实体字段**一定全部出现**（上游缺的是显式 `null`），上游多给的字段被 Jackson 丢掉。
Rust 原先把上游 JSON 原样透传，键集合随上游而异。

修的是三个 `{bigId}` 详情端点（`support::entity_shape`，键序取自 Java 实测出参）：

| 端点 | Java 键数 | Rust（修前） | 修后 |
|---|---|---|---|
| `/base/feerecords/{bigId}` | 146 | 5（透传） | 逐字节一致（3431 字节） |
| `/base/feeGantry/{bigId}` | 79 | 5（透传） | 逐字节一致（1676 字节） |
| `/base/snapshotflow/{bigId}` | 53 | 43（本地实体缺 10 个 `exist=false` 字段） | 逐字节一致（1069 字节） |
| `/base/feerecords/list` | 行按实体成型后再补字典 | 只补字典 | 逐字节一致（3445 字节，含时间区间参数的真实查询） |

`/base/feestationexit/{bigId}` 与 `/base/feestationexit/list` 两端都**不**成型：
Java 走 hutool `JSONObject` 原样透传，其键序是 `HashMap` 迭代序（对同一键集合稳定，但与上游顺序无关），
Rust 保留上游顺序 → 只记 `ORDER-DIFF`，归入「只比结构」。
`/base/feeGantry/{bigId}` 一族里 Java 反不出桩响应的旧 KNOWN 结论（§5）在有桩后已升级为可比对。

### 9.1 共享缓存的**写入形状**也算对拍的一部分（`sys_dict:*`、`car_list*`）

`/system/dict/data/type/{dictType}` 这类「读缓存直接出参」的端点，两端在两条路径上的行为是：

| 路径 | Java | Rust（修后） |
|---|---|---|
| 缓存缺失（查库并回写缓存） | 实体经 Jackson 出参，`BaseEntity.params` 是 `@JsonInclude(NON_EMPTY)` → **没有 `params` 键** | 同一形状（SQL 里本来就没有 params 列）→ 逐字段一致 |
| 缓存命中 | 把缓存元素**原样**出参，FastJson2 写的 `params:{"@type":"java.util.HashMap"}` 作为普通键**留着** | 原样 echo → 一致 |

这条是实测出来的，不是推出来的：同一条件下跑 6/6 稳定（缓存先由 Java 写、先由 Rust 写各三种），
一度按「NON_EMPTY 该把空 map 抹掉」的想当然去剥 `params` 里的 `@type`，反而把命中路径改坏了。

另一半是**写入**形状：Rust 原先按实体顺序写、且把 null 一起写，而 Java 的
FastJson2 输出是「`@type` 在最前 + 字段名字典序 + null 不写」。同一个键被不同端写过之后，
另一端的读法就不一样了。统一成 `support::fastjson_rows()`，`sys_dict:*` 与
`car_list`/`car_list_jc` 都走它；实测两种缓存来源下两端响应逐字节一致，
`/system/dict` 的 9 条 GET 全 OK。

清过 Redis 之后**必须先热缓存再对拍**：冷缓存下 `compare.py` 先请求的一端（Java）走 DB、
后请求的一端（Rust）走缓存，就会差一个 `params` 键报出假 FAIL —— 同一端从冷启动连跑两次即一致，
与两端代码无关（实测过：热缓存下 java/rust 各 4 次出参完全一致）。

**环境教训**：Java 的 jar 里 `vehicleMonitor.baseUrl` 是 `http://127.0.0.1:9902`（真实的
`car-monit-api`），而 Rust 的配置指向 9901 的桩。重启 Java 时若不带
`--vehicleMonitor.baseUrl=http://127.0.0.1:9901`，两端就会各自打不同上游，
`/base/feerecords/{bigId}` 之类的比分会变成假的 FAIL。

## 10. 真实上游链路下的三段复核（2026-11-04）

前面 §7–§9 是在 9901 桩上游上跑的。本轮把 `D:\work\IdeaProjects\car-monit-api` 的双端服务起起来，
按「先 backend→api、再业务、后框架」三段重跑。

**拓扑**（两端各自成一套，共用 MySQL/GaussDB，Redis 分库）：

| 端 | 端口 | Redis db | 上游 |
|---|---|---|---|
| backend Java | 9988 | 0 | `vehicleMonitor.baseUrl=http://127.0.0.1:9902`（api 的 Java 端） |
| backend Rust | 9990 | 15 | `http://127.0.0.1:9911`（`car-monit-api-rust`） |
| api Java（pro-business-api） | 9902 | 0 | GaussDB `192.168.56.10:5432/RuoYi` |
| api Rust | 9911 | 15 | 同上 |

api 侧另有 Go 实现（9903，db1），backend 侧另有 Go（9989，db2），都不参与本轮对拍。
分库是拓扑要求而不是随意选的序号：api 写的 `gantry_list`/`section_road_map` 等缓存要被同侧 backend 读到。

### 10.1 A 段：backend 调 api 的端点

`tools/endpoint_parity/api_chain_matrix.py`（24 条，带真实上游返回值）：**20 OK / 4 WARN / 0 FAIL**；
`compare.py` 在这套拓扑下跑 `/base` 透传：**71 OK / 1 WARN / 0 FAIL / 2 KNOWN**。
4 条 WARN 都是既有类别：`BigDecimal` scale（`771.44800` vs `771.448`）、上游随机主键、
以及只有包装文案差的其他值一致项。随机 uuid 与时间戳在脚本里掩码后再比。

### 10.2 B 段：业务端点（`/manager`、`/flow`）

129 条 GET：**129 OK / 0 WARN / 0 FAIL**（`build/phase-b-manager.json`）。到这一段的路上修掉三处：

| 位置 | Java | Rust（修前） |
|---|---|---|
| `carLocation` 缓存未命中的回退查询 | 走带 `not exists` 排除的 `selectCarInfo` | 用了不含排除条件的裸 SQL → 大屏多出 13 个点 |
| `support::java_int` | `BigDecimal.intValue()` 向零截断 | DECIMAL 列读出的 `1119.0` 被 `as_i64()` 判成 None → 当 0，于是可疑车辆详情的 `raodTrailList` **永远是空数组** |
| 外部路径服务 | 见下 | 见下 |

**外部路径服务是真要调的**。`getCarGeometryByPlanNew` 命中不了 `car_lxgh:` 缓存时会打
`roadPathUrl` 的 `/api/routes/query`；再拿不到就落 `getCarGeometryByPlan`，那条会调
`tx-service-url`（腾讯 direction，签名 + polyline 增量解码 + GCJ-02→WGS84 + 六位 HALF_UP）。
Rust 原先只读缓存、读不到就直接落本地桩号绘制 —— 而这台机器**出得了公网**，
Java 因此对同一个 id 返回一条整段路径、Rust 返回 6 段。补了 `src/common/gps.rs`（GpsUtil 移植）
与 `src/service/road_path.rs`，并把分支顺序照 Java 摆正：ByPlanNew 缓存未命中 → 调路网规划 →
失败落 ByPlan → 再失败才落本地；两边拿到结果都要回写 `car_lxgh:` 缓存（Java 无 TTL）。

验证方式：清掉两端缓存后交替各跑两轮，**同一时间窗内两端逐字节一致**（203480 字符），
跨窗会因路网结果刷新差一两个点。这类值不属于两端代码差异，`compare.py` 用
`VALUE_FREE`（`/manager/suspicious/{id}` 的 `*.paths`）只比结构不比这个标量。

### 10.3 C 段：框架端点（`/system`、`/monitor`、`/tool`、`/common`、`/flow`）

121 条 GET 首跑 107 OK / 10 WARN / 2 FAIL。两条 FAIL（`/system/dict/data/type|typemore`）
是 §9.1 记录过的**冷缓存**形状差 —— 热缓存后复跑 0 FAIL。10 条 WARN 里有 4 条是
`/tool/gen` 的尾部键序：实测 Java 在同一进程内对三个端点给的顺序一致
（`… filterColumnList, sub, crud, tree`；列是 `… query, insert, edit, capJavaField, superColumn, increment, usableColumn`），
Rust 的常量表把 `crud`/`sub` 与尾部七个写反了，已按实测改回。

### 10.4 GET 扫不到的四类框架层差异（本轮新增，都做了对拍）

1. **方法不匹配**：Java 由 `GlobalExceptionHandler` 兜住 `HttpRequestMethodNotSupportedException`，
   回 HTTP **200** + `{"msg":"Request method 'POST' not supported","code":500}`；Rust 原先是裸 405 空响应体。
   现在 `src/lib.rs` 在最内层把 405 翻译成同样的响应体（鉴权仍然先跑，未登录仍是 401，与 Java 一致）。
2. **路径变量类型**：`@PathVariable Long jobId` 遇到 `1x`，Spring 在进控制器之前就失败，
   文案是 `请求参数类型不匹配，参数[jobId]要求类型为：'java.lang.Long'，但输入值为：'1x'`
   —— 数组的 `getName()` 是 `[Ljava.lang.Long;`，且第三个 `%s` 是**整段路径变量原文**（`1,1x` 就写 `1,1x`）。
   Rust 原先一律 `Path<String>` 再宽松转换，于是 `/monitor/job/1x` **返回了 jobId=1 的数据**。
   新增 `support::path_long / path_int / path_long_list / path_int_list`（空白按 Spring 的
   `trimAllWhitespace` 全删、`+5` 合法、溢出报错），改到 Java 侧 48 个数字路径变量端点。
   对拍脚本 `tools/endpoint_parity/pathvar_matrix.py` 直接从 Java 源码解析 `@PathVariable` 类型，
   GET 侧用 `1x`：**28 OK / 0 WARN / 1 FAIL**，
   唯一 FAIL 是当时还没迁移的 `/oss`（§10.6/§10.8，现已补齐并实测）。
   写侧（48 条里 19 条 DELETE/PUT/POST）**不能直接用 `1x`** —— 宽松实现会把它当 1，
   而 id=1 正是 admin 用户与超级角色。`--writes` 用 `30000000x`：Java 在类型转换阶段就失败，
   万一某端仍宽松，`WHERE id = 30000000` 也只命中 0 行；再用
   `tools/endpoint_parity/db_snapshot.py` 对 23 张表做前后快照验证：
   **19 OK / 0 WARN / 0 FAIL，业务表行数零变动**（只有 `sys_logininfor` +2，是探针自身登录写的审计行）。
3. **两种「没权限」不是一种**：RuoYi 只定制了 `authenticationEntryPoint`（401 才是 AjaxResult），
   授权失败仍走 Spring 默认的 `AccessDeniedHandlerImpl` → `sendError(403)` → `/error` 的
   `{"timestamp","status":403,"error":"Forbidden","path"}`（HTTP **403**）。
   命中 `anonymous()`（`/system/notice/view/**`、`/system/file/view/**`、`/common/download**`）
   与 `denyAll()` 的**已认证**请求就是这一种，Rust 原先回 200+code403。
   `@PreAuthorize` 的失败仍是 AjaxResult（Java 有对应 handler），两条路径别混。
4. **响应头与 Content-Type**（每条响应都影响，GET 对拍脚本不比头，所以之前没暴露）：
   Java 每条响应带 `X-Trace-Id`（`TraceIdFilter`：请求头非空就透传，否则 32 位小写十六进制 UUID）、
   `X-Content-Type-Options: nosniff`、`X-XSS-Protection: 1; mode=block`（`SecurityConfig` 只关了
   cacheControl 与 frameOptions）；CORS 侧只有 `Vary: Origin`（不是 tower-http 的三个候选头）、
   请求不带 `Origin` 时不回 `Access-Control-Allow-Credentials`、`Access-Control-Allow-Headers`
   用 `", "` 连接回显，且**从不发 `Allow`**。Content-Type 分三类实测：控制器与 MVC 异常 =
   `application/json`；安全入口的 401 = `application/json;charset=utf-8`；`/error` 错误页 =
   GET/DELETE 不带 charset、POST/PUT/PATCH 带 `;charset=UTF-8`。落在 `src/middleware/web_filter.rs`（最外层）。

### 10.5 探针留下的脏数据

`/monitor/online/list` 在分库后第一次跑成了 FAIL：Java 侧 500
（`com.alibaba.fastjson2.JSONObject cannot be cast to LoginUser`）。原因是 db0 里残留一条**共用 db 时期**
Rust 写的 `login_tokens:*`（没有 `@type`），Java 把它读成 JSONObject 就炸。删掉该键即恢复；
随后把两端各自的 40/35 条探针会话一起清掉，`rows` 长度也一致了。
教训：分库之前写入的缓存值是脏数据源，跨端对拍前要先确认 db 归属。

### 10.6 基线漏掉的一个控制器

`ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssEndpoint.java`（`@RequestMapping("/oss")`，9 条）
没进 501 条基线清单（生成清单的解析器只扫了 `web/controller/**` 与 quartz、generator 两个模块），
所以 Rust 整块缺失。`tools/endpoint_parity/controller_coverage.py` 现在会把全部 Java 控制器与基线对照，
结论是**只漏了这一个**。实现与验证见 §10.8。

### 10.7 对拍脚本自身的修正（不修就会吞掉差异）

`compare.py` 的 DYNAMIC 分支原先写成 `sub_dyn = dyn or DYN_KEYS.search(k)` —— 只要端点前缀在
`DYNAMIC` 里，**所有标量值都不比了**。改成只按键名判断后，立刻暴露出 `/system/user` 家族的真实差异：

| 出参 | Java | Rust（修前） |
|---|---|---|
| 顶层 `deptName` | resultMap 不映射 → 恒 null；只有 `listByDept` 在查完后把 `dept.deptName` 回填 | 列表里恒填 |
| `subCode` | 列表 SQL 不选 `d.sub_code` → null；详情 `selectUserVo` 选 → 有值 | 列表也填 |
| `pjFlag` | `private int pjFlag`（原始类型，无人 set）→ 恒 `0` | `null` |
| `loginDate` | 裸 `Date` 且无 `@JsonFormat` → Jackson 的 ISO 带毫秒与本机偏移 | `yyyy-MM-dd HH:mm:ss` |
| `dept.parentId/orderNum/status` | 详情 VO 选了 `d.parent_id`/`d.order_num`/`d.status as dept_status` → 进 dept | 没选，恒 null |
| `dept.orderNum` | `SysDept.orderNum` 是 `String` → `"0"` | 数字 `0` |
| `tenantName` | 实体字段未被映射 → 键存在、值为 null | 整个键缺失 |

上表都已在 `shape_user_rows` / `USER_COLUMNS` / `USER_VO_COLUMNS` 里改齐（`/system/user` 的 14 条 GET
现在全 OK）。同一轮里接着修掉的另两条：

- `/system/user/currentUser`：Java 的 `selectCurrentUser()` 返回的是**新建** SysUser，只填
  `userId`、`deptId`（= `SecurityUtils.getEpsId()`，即登录用户的 deptId）、`headOffice`、
  `procurementManager`，其余 41 个键全是 null，且**没有 `params` 键**（`BaseEntity.getParams()` 的空 map
  被 `@JsonInclude(NON_EMPTY)` 抹掉）。`selectHeadOffice()` 有个容易看漏的细节：它返回的是
  `filterSet.addAll(deptSet)` —— treeLeavel 为 1/2 的部门**本身**就算总公司，所以 admin 的
  `headOffice=true`；Rust 原先回的是登录态里的完整用户，现在按 Java 重建（`treeLeavel` 为 null 时
  Java 是 `Integer.equals` 的 NPE，也照抄成 `{"msg":null,"code":500}`）。
- `/monitor/online/list`：Java 的 `createSysUserOnline` 在 `user.getDept()` 非空时把
  `dept.deptName` 写进 `deptName`；Rust 原先恒 null。

`/monitor/online/list` 的行数与 `/monitor/cache` 的 `dbSize`/`commandStats`/`INFO` 属于
「两端各连自己的 Redis db」带来的天然差异，脚本对它们只比结构：
`DYNAMIC` 端点的列表长度与 `total` 降级为 `LEN-WARN`/`TOTAL-WARN`，`/monitor/cache` 的 `data.*`
整片走 `VALUE_FREE`。**这些降级只针对运行时计数**，`deptName`/`userName`/`ipaddr` 这类业务值仍然实比。

另外，`SHAPE_ONLY` 是整端降级，粒度太粗；新增 `VALUE_FREE`（端点 → 标量路径正则）只放过真正随时间
变化的那几个字段（本轮用于 `/manager/suspicious/{id}` 的 `*.paths`）。

### 10.8 `/oss/**` 补齐与尾斜杠匹配

`tools/endpoint_parity/controller_coverage.py` 把 Java 全部 `@Controller`/`@RestController` 与基线清单
对照，结论是**只漏了 `OssEndpoint` 一个控制器**（9 个端点）。本轮补上并做了双端对拍：
真实 MinIO（`oss.endpoint=172.30.100.102:9002`）不在网内，于是用
`tools/endpoint_parity/fake_s3_full.py` 顶一个会回 `ListAllMyBuckets`/`ListBucket`/PUT/HEAD/DELETE 的
假 S3，两端同时指过去 —— 这样**成功路径也是测出来的而不是推的**：

| 项 | 实测 |
|---|---|
| `Bucket` 出参 | 键序 `name, owner, creationDate`；`owner` 取自 XML 根元素而不是每个 Bucket 里 |
| `S3ObjectSummary` 出参 | 键序 `bucketName, key, size, lastModified, storageClass, owner, etag`，`etag` 去掉引号 |
| `Date` | Jackson 写 `2021-05-06T08:36:40.000+08:00`（无全局 date-format） |
| `GET /oss/object/{b}/{o}/{expires}` | 出参键序 `bucket, expires, url, object`；`expires` 按**天**加，>7 天时 SDK 在发请求前抛固定文案 |
| `POST /oss/object/**` | 恒 `{"msg":null,"code":500}`（Jackson 序列化 `S3Object` 失败，与对象是否存在无关） |
| `DELETE /oss/bucket/{n}` | HTTP 202 空体 |
| 签名 | path-style、`us-east-1`、`SignedHeaders` 含 host/x-amz-content-sha256/x-amz-date，与 Java 打到假 S3 的请求一致 |

16 组探针里 13 组逐字节一致；尾斜杠的两组差异见下。

**尾斜杠**：Spring Boot 2.x 默认 `useTrailingSlashMatch`，`/x/` 也命中注册为 `/x` 的映射，Rust 原先 404。
axum 的 `.layer()` 只包住各路由的 handler，中间件里改 URI 影响不到路由决策，所以改成
「按原样路由不到 → 削掉一个尾斜杠再路由一次」（`retry_with_trimmed_trailing_slash`）。
Java 侧 `404` 错误页的 `path` 保留原始尾斜杠，因此削完仍路由不到时用**原路径**回错误页。
已知残余偏差：`DELETE /oss/object/{b}/{o}`（不带尾斜杠）Java 回「方法不支持」—— Java 的映射声明本身就带
尾斜杠，归一之后两种写法只能对齐其中一个。

## 11. 结论

- GET 全量 297 条（真实 api 上游 + 双端分库 + **修正后的 compare.py**，2026-11-05 凌晨）：
  **OK 280 / WARN 11 / FAIL 0 / KNOWN 3 / SKIP 3**。
  11 条 WARN 分成三类：
  1. 5 条 `MSG-DIFF`（`sys_upgrade_info` 缺表 ×4、`/base/fitting/list` 的 Java mapper 反射异常）——
     两端同为 500，只差包装文案；
  2. 5 条 `ORDER-DIFF`（`/tool/gen` 的 4 条 + `/monitor/cache` 的 Redis INFO）——
     **`/tool/gen` 那 4 条是 Java 自己不稳定**：GenTable/GenTableColumn 尾部那几个派生 getter
     （`sub`/`crud`/`tree` 与 `insert`/`edit`/`capJavaField`/`superColumn`/`increment`/`usableColumn`）
     没有 `@JsonPropertyOrder`，顺序取决于 Jackson 从反射拿到的方法数组顺序，而这个**按 JVM 实例**固定、
     跨重启会变（实测同一进程内 4 次完全一致，两次重启之间从 `sub, crud, tree` 变成 `tree, crud, sub`）；
     Rust 只能对齐其中一次，记 WARN。`data.info` 是 Redis INFO 的键序。
  3. 1 条 `/monitor/online/list` 的行数/total —— 两端各自的会话库（db0/db15）天然不同。
- A 段 backend→api：链路矩阵 **20 OK / 4 WARN / 0 FAIL**，`/base` 透传 **71 OK / 1 WARN / 0 FAIL**（§10.1）。
- B 段业务（`/manager`、`/flow` 129 条 GET）：**129 OK / 0 WARN / 0 FAIL**（§10.2）。
- C 段框架（`/system`、`/monitor`、`/tool`、`/common`、`/flow` 121 条 GET）：热缓存后 109 OK / 6 WARN / 0 FAIL；
  修掉四类框架层差异后，`/system/user` 家族与 `/monitor/online`、`/monitor/cache` 的值差异也一并收口（§10.4、§10.7）。
- 数字路径变量（`pathvar_matrix.py`，只用非法值探 GET）：**28 OK / 0 WARN / 1 FAIL**，
  唯一那条 `/oss` 已随 §10.8 补齐。
- `/oss/**` 9 条：16 组探针 13 组逐字节一致，剩余 3 组都是尾斜杠路由与错误页 `path` 字段的细节（§10.8）。
- `manager_crud!` 11 张表写入：**10 OK / 1 WARN / 0 FAIL**（§7.7，路径变量改造后复跑不变）。
- `/system/*` 等 14 个新增端点 × 两种请求体：**不一致 0**（§7.9，复跑不变）。
- `/monitor/job` 四张矩阵、两个 Excel 导入端点仍全绿（§7.4、§8）。
