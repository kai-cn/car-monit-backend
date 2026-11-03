# 迁移工作进度（接口返回逐一对比阶段）

> **2026-11-03 批次收口见 `docs/PARITY-SUMMARY-2026-11-03.md`**：分页语义与 PageHelper 5.3.3 源码
> 逐条对齐（`SkipQuery`/`Clamp`/`startRow`/`OrderBy`）、手拼 SQL 与 ops/systemaux 的客户端排序覆盖补齐、
> 校验矩阵从 11 种组合扩到 16 种并修掉脚本自身的 rows 盲区；1155 组合 0 差异，单测 `internal/web/pagination_test.go` 钉住语义。
>
> **第三轮（2026-11-02）另见 `docs/PARITY-2026-11-02.md`**：共用 MySQL、**两端使用不同 Redis DB
> （Java=db0 / Go=db2）**重做全量校验，校验脚本进仓库（`scripts/parity/`）。
> 该轮结果：路由 Java 有/Go 没有 **0** 条；GET 288 条中 **250** 条逐字段一致、14 条差异全部定性为
> 环境设定或 Java 侧缺陷；写接口 32 资源中 24 个四步全一致；Redis 双 DB 隔离 24 项断言全通过；
> 查询参数矩阵 696 组合 **0** 差异。
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
| 账号 | admin / Admin@2025-（Java 登录需验证码，答案从 Redis `captcha_codes:<uuid>` 读取） |
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
  15 处分页执行器（11 个文件）先问这一句（1155 组合 → 0 差异）
- **`isAsc` 原样拼接**：`getOrderBy()` 不校验方向值，`isAsc=bogus` 就是让 MySQL 报错；
  别名 `ascending/descending` 在 `setIsAsc` 里转 ⇒ `web.OrderBy` 去掉「非 desc 即 asc」兜底
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
