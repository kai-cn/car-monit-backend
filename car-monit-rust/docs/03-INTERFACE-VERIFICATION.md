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

| 结论 | 数量 | 说明 |
|---|---:|---|
| OK | 282 | 结构、值、类型、**键顺序**均一致（含代码生成 4 个端点） |
| WARN | 6 | 4 处 `sys_upgrade_info` 表缺失的异常文案、`/base/fitting/list` 的 MyBatis 反射异常文案、`/monitor/cache` 的 Properties 桶序，见 §5.1 |
| FAIL | 0 | 首版 13 处 + 共因 2 处均已消除，见 §4 |
| KNOWN | 6 | 依赖不可用上游或 Java 自身故障，见 §5 |
| SKIP | 3 | `geometry/syncAllGeometry(1)`、`tool/gen/synchDb`（有远端写入副作用，避免污染） |

> 进度：首版（2026-10-31）OK 160 / WARN 109 / FAIL 13 → 补 §4 的 13 项后 182 / 98 / FAIL 2
> → 补 Redis 共存与字典/统计口径 186 / 98 / **0** → 代码生成模板引擎（§5）190 / 98 / 0
> → **键顺序全面对齐（§3.3）282 / 6 / 0**。

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

## 5.1 剩余 6 个 WARN（均非值差异）

| 端点 | 类别 | 说明 |
|---|---|---|
| `/system/upgradeInfo/list`、`/newest`、`/export`、`/{id}` | MSG-DIFF | 库里缺 `sys_upgrade_info` 表，两端都 500、`code` 一致，只是 MyBatis 拼装的异常文本 vs sqlx 文本不同（要再压缩差距只能硬编码对方文案） |
| `/base/fitting/list` | MSG-DIFF | Java 的 Mapper 里 `<where>` 引用 `#{id}` 而 `ZdataTrailFitting` 没有该 getter → MyBatis `ReflectionException`；Rust 直接把 SQL 交给 MySQL，报 `Unknown column 'id'`。同为 500 |
| `/monitor/cache` | ORDER-DIFF | `data.info` 是 Jackson 直接序列化 `Properties`（Hashtable）：桶容量与下标规则已复刻（`java_hashtable_ordered`），同桶内链表的头/尾插随 JDK 版本而变，仍有局部错位；键集合与值完全一致 |

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

