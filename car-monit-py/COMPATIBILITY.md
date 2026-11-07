# COMPATIBILITY.md — 已知行为差异与规避方式

> 本文件持续更新。每条差异都回答三个问题：
> 1. **Java 原行为是什么**
> 2. **Python 侧怎么做**
> 3. **客户端/运维要不要改**
>
> 标记说明：
> - `[无影响]` 客户端感知不到，纯内部实现差异
> - `[可配置]` 通过配置项可切回 Java 行为
> - `[需注意]` 客户端或运维需要知道

---

## 0. 结论速览

| # | 差异 | 等级 | 处置 |
|---|---|---|---|
| 1 | 新增 `GET /health` 端点 | `[可配置]` | `app.health-endpoint-enabled=false` 可关闭 |
| 2 | 所有已处理异常返回 **HTTP 200** | `[无影响]` | 与 Java 完全一致，**不是**差异，仅作说明 |
| 3 | 未匹配路由返回真实 404 + Spring 错误体 | `[无影响]` | 与 Java 一致 |
| 4 | `BaseException` 改名为 `RuoYiBaseException` | `[无影响]` | 避免遮蔽 Python 内建异常 |
| 5 | `AjaxResult.put(...)` 改名为 `put_chain(...)` | `[无影响]` | 覆写 `dict.put` 会破坏 dict 协议 |
| 6 | Tomcat 800 线程 → anyio 线程池 800 | `[无影响]` | 已对齐，不是削弱 |
| 7 | 日志按时间+大小滚动 → 仅按大小滚动 | `[需注意]` | 运维看日志留存策略 |
| 8 | p6spy → SQLAlchemy 事件监听器 | `[无影响]` | SQL 日志格式不同，内容等价 |
| 9 | Druid 监控台 `/druid/**` 不迁移 | `[需注意]` | Java 里本来就被 `denyAll()` 拒绝 |
| 10 | `server.tomcat.*` / `spring.devtools.*` 接受但不生效 | `[无影响]` | 保留配置项仅为了可 diff |
| 11 | 9 个 `@Scheduled` 方法默认不执行 | `[可配置]` | 镜像 Java 现实（无 `@EnableScheduling`） |
| 12 | Quartz → **自研内存调度器**（不是 APScheduler） | `[无影响]` | 启动时重载 `sys_job`，行为一致，见 §42.1 |
| 13 | Kafka / MinIO 默认关闭 | `[可配置]` | 当前环境不可达，启动打印告警 |
| 14 | Alembic 只做结构查看，不接管 schema | `[无影响]` | Java 侧本来就没有 Flyway/Liquibase |
| 15 | 标准输出编码用 `errors="replace"` | `[无影响]` | 等价 Java `PrintStream` 行为 |
| 16 | 配置优先级：环境变量 > YAML | `[无影响]` | 与 Spring 一致（见 §16） |
| 17 | 动态数据源 `@DataSource` 不迁移 | `[无影响]` | 从库 `enabled: false`，永远走主库 |
| 18 | Spring Security 过滤器链 → ASGI 中间件 | `[无影响]` | 规则表/状态码/响应体逐条对齐，见 §18 |
| 19 | `/logout` 不校验 HTTP 方法 | `[需注意]` | 从源码推导，待实机核对，见 §19 |
| 20 | 静态资源规则遮蔽 swagger/druid 的 `denyAll` | `[无影响]` | 镜像 Java 缺陷，见 §20 |
| 21 | UA 解析库不同（`useragentutils` → `user_agents`） | `[需注意]` | 只影响审计列，见 §21 |
| 22 | 验证码图片由 `java.awt` 改由 Pillow 渲染 | `[无影响]` | 尺寸/颜色/答案一致，像素必然不同，见 §22 |
| 23 | 验证码比对 `equalsIgnoreCase` → 小写比较 | `[无影响]` | 对验证码字符集完全等价，见 §23 |
| 24 | `/login` 对缺失 `Content-Type` 的请求体更宽容 | `[需注意]` | Java 走 415 错误体，Python 正常登录，见 §24 |
| 25 | `/system/user` 的 `export` / `importTemplate` / `importData` **已实现** | `[需注意]` | Phase 3.18 补齐 `ExcelUtil`；`export` 只回文件名（在 `msg`），见 §37.1 / §37.2 |
| 26 | `@Log` 未迁移 → 用户管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §25.2 |
| 27 | 曾缺失 `RuntimeException` 处理器 + 装饰器破坏参数绑定 | `[需注意]` | 端到端用例发现的两个真实缺陷，**均已修复**，见 §25.3 / §25.4 |
| 28 | varchar 排序列接受 JSON 数字（`JavaString`） | `[无影响]` | `el-input-number` 发的数字按 Jackson 规则强转，见 §25.5 |
| 29 | `/system/post/export` **已实现** | `[需注意]` | Phase 3.18；不再是“被 `/{post_id}` 兜住回 500”，见 §37.1 |
| 30 | `@Log` 未迁移 → 岗位管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §26.2 |
| 31 | 新增 `bean_validation` 桥接 `@NotBlank` / `@Size` | `[无影响]` | 文案与 Java 注解一致，且顺序排在 `@PreAuthorize` 之前，见 §26.3 |
| 32 | `@DataScope` 对 `sys_dept` 完全无效 | `[需注意]` | `${params.dataScope}` 在 XML 里被注释掉了，**镜像 Java 现状**，见 §27.1 |
| 33 | `@Log` 未迁移 → 部门管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §27.2 |
| 34 | `bean_validation` 新增 `@Email`（Hibernate 放宽版） | `[需注意]` | 只可能比 Java **多放过**，不会多拒绝，见 §27.3 |
| 35 | `updateDept` 写空 `phone`/`email`，`insertDept` 丢弃 | `[需注意]` | 两段 SQL 判据不同，是 Java 原样，见 §27.4 |
| 36 | `del_flag` 过滤与 `select *` 的三处不对称 | `[无影响]` | 照抄 XML，改“正常”会换结果集，见 §27.5 |
| 37 | `/system/role/export` **已实现** | `[需注意]` | Phase 3.18；文件名在 `msg`，见 §37.1 |
| 38 | `@Log` 未迁移 → 角色管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §28.2 |
| 39 | `@Transactional` 未复刻：多语句方法**不再原子** | `[需注意]` | 写失败可能留半成品，见 §28.3 |
| 40 | 基本类型布尔 → 两个 `*_check_strictly` 列**总是**写库 | `[需注意]` | OGNL 装箱后永不为 null，见 §28.4 |
| 41 | `updateRole` 的 `remark` 传空串会**清列** | `[需注意]` | 唯一一个只有 `!= null` 的字段，见 §28.5 |
| 42 | `roleKey.trim().split(",")` 不逐段 trim | `[无影响]` | `trim` 只作用于整串，见 §28.6 |
| 43 | `deleteRoleById` 没有超管/已分配拦截 | `[无影响]` | Java 原样，且**当前无调用方**，见 §28.7 |
| 44 | 菜单**没有** `export`（Java 也没有） | `[无影响]` | `GET /system/menu/export` 被 `/{menuId}` 兜住回 **500**，见 §29.1 |
| 45 | `@Log` 未迁移 → 菜单管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §29.2 |
| 46 | `insertMenu` **不回写** `menuId` | `[无影响]` | 全项目唯一一个没有 `useGeneratedKeys` 的 `insertXxx`，见 §29.3 |
| 47 | `updateMenu` 的 4 个字段传空串会**清列** | `[需注意]` | `component`/`visible`/`status`/`perms` 只判 `!= null`，见 §29.4 |
| 48 | `deleteMenuById` 是**物理删除**（无 `del_flag`） | `[需注意]` | 过了两道闸就不可恢复，见 §29.5 |
| 49 | `menuCheckStrictly` 是 primitive → `<if>` 是**活条件** | `[无影响]` | 与 §28.4 恰好相反，见 §29.6 |
| 50 | `treeselect` / `roleMenuTreeselect` **没有**权限点 | `[无影响]` | Java 原样，别“顺手”补 `@PreAuthorize`，见 §29.7 |
| 51 | 两条孤儿 statement（`selectMenuPerms` / `selectMenuPermsByRoleId`） | `[无影响]` | XML 有、Java 接口无，照留，见 §29.8 |
| 52 | `component` 的 `@Size` 上限 200、文案写 255 | `[无影响]` | Java 原文，改了就是行为改变，见 §29.9 |
| 53 | `@Log` 未迁移 → 个人信息/头像不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §30.1 |
| 54 | `/system/user/profile` 四个端点**都没有**权限点 | `[无影响]` | Java 原样，靠 `anyRequest().authenticated()` 兜，见 §30.2 |
| 55 | `profile` 路由必须在 `sys_user` **之前**注册 | `[无影响]` | 否则被 `/{userId}` 吃掉，已按序注册，见 §30.3 |
| 56 | 库里与缓存里的 `password` **不是同一个哈希** | `[无影响]` | 两次独立 BCrypt，Java 原样，见 §30.4 |
| 57 | 头像存的是 `/profile/avatar/...` **相对 url** | `[需注意]` | 不是完整 http 地址，靠 `/profile/**` 静态映射提供，见 §30.5 |
| 58 | `UploadFile.size` 为 `None` 时回退到底层文件长度 | `[无影响]` | `size_of()` 复刻 `getSize()`，见 §30.6 |
| 59 | 缺 `oldPassword` → `rawPassword cannot be null` | `[无影响]` | 与 Java 的 `IllegalArgumentException` 同名同义，见 §30.7 |
| 60 | 缺 multipart 部件：Java 400，Python **200 + code 500** | `[需注意]` | 全局校验处理器统一转 200，见 §30.8 |
| 61 | `getPathFileName` 对 `profile` 之外的目录“截错位置” | `[无影响]` | Java 没有校验，这里也不加，见 §30.9 |
| 62 | 0 字节文件在控制器短路，工具类本身接受空文件 | `[无影响]` | `isEmpty()` 是控制器的闸，见 §30.10 |
| 63 | `GET /system/role/list` 曾漏了分页（**已修复**） | `[需注意]` | Phase 3.9 遗留，见 §28.8 |
| 64 | `@Log` 未迁移 → 公告管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §31.2 |
| 65 | `GET /system/notice/list` **没有**权限点 | `[无影响]` | Java 注解被注释掉，别“顺手”补，见 §31.3 |
| 66 | `/system/notice/view/**` **只允许匿名**：已登录反而 403 | `[需注意]` | `anonymous()` 的语义，见 §31.4 |
| 67 | `insertNotice` 把 `createBy` 改写成 `userId`（不是 userName） | `[需注意]` | Java 原样，与其它模块不一致，见 §31.5 |
| 68 | `noticeType` 被服务层**强制**成 `"1"` | `[需注意]` | 传 `"2"` 也会变通知，见 §31.6 |
| 69 | `@Validated` 是空壳：公告实体零约束注解 | `[无影响]` | 空标题/超长标题都能入库，见 §31.7 |
| 70 | `buss_id`/`buss_name` 在 insert 与 update 里判据**不对称** | `[无影响]` | 照抄 XML，见 §31.8 |
| 71 | `addDeliveryTimeAbnormal` 是**死代码** | `[无影响]` | 无调用方，按原则第 4 条照搬，见 §31.9 |
| 72 | 两个字典 `export` **已实现** | `[需注意]` | Phase 3.18；不再是“被 `/{id}` 兜住回 500”，见 §37.1 |
| 73 | `@Log` 未迁移 → 字典管理不写 `sys_oper_log` | `[需注意]` | 含 `clearCache`，见 §32.3 |
| 74 | 字典预热 `init()` **不在启动时调用** | `[需注意]` | 首个请求回源填充，结果一致，见 §32.4 |
| 75 | `updateDictType` 无事务 → 子表先改 | `[需注意]` | 与 §28.3 同一缺口，见 §32.5 |
| 76 | `substring(0, len)` 是空操作：缓存键带尾逗号 | `[无影响]` | 照抄 XML 对应的 Java 原文，见 §32.6 |
| 77 | `selectDictLabel` **没有** `limit 1` | `[无影响]` | 重复数据 → `TooManyResultsException` → 500，见 §32.7 |
| 78 | 两个 `insertDictXxx` **不回写**主键 | `[无影响]` | 没有 `useGeneratedKeys`，见 §32.8 |
| 79 | `SysDictData` 的 JSON 多一个 `default` 键 | `[无影响]` | Jackson 只读属性，前端在用，见 §32.9 |
| 80 | 两个 `selectDictData*Map` 不走缓存、不过滤 `status` | `[无影响]` | 重复键 → `IllegalStateException`，见 §32.10 |
| 81 | `clearDictCache` 用 `KEYS` 扫全部键 | `[无影响]` | O(N) 阻塞命令，照抄，见 §32.11 |
| 82 | 曾拼出 `where AND ...`（**已修复**） | `[需注意]` | 公告 + 两个字典列表查询共三处，见 §32.12 |
| 83 | `/typemore` 未命中返回 `{}` 而不是 `[]` | `[无影响]` | 空数组被 `groupingBy` 吞掉，见 §32.13 |
| 84 | `/system/config/export` **已实现** | `[需注意]` | Phase 3.18；文件名在 `msg`，见 §37.1 |
| 85 | `@Log` 未迁移 → 参数管理不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §33.3 |
| 86 | 参数预热 `init()` **不在启动时调用** | `[需注意]` | 首个按键读取回源填充，结果一致，见 §33.4 |
| 87 | 参数缓存"增改写单键、删除全清" | `[无影响]` | 与字典切片的"写完全清"**不同**，见 §33.5 |
| 88 | `selectConfigByKey` 命中 `config_value = NULL` 时回 `null` | `[需注意]` | 不是 `""`，见 §33.6 |
| 89 | `GET /configKey/{key}` **没有**权限点 | `[无影响]` | Java 原样，别"顺手"补，见 §33.7 |
| 90 | `updateConfig` 的 `remark` 传空串会**清列** | `[需注意]` | 唯一一列只有 `!= null`，见 §33.8 |
| 91 | `insertConfig` **不回写**主键 | `[无影响]` | 没有 `useGeneratedKeys`，见 §33.9 |
| 92 | `deleteConfigById` 是**孤儿 statement** | `[无影响]` | XML 有、无调用方，照留，见 §33.10 |
| 93 | `/system/indexmenu/export` **已实现** | `[需注意]` | Phase 3.18；文件名在 `msg`，见 §37.1 |
| 94 | `@Log` 未迁移 → 常用菜单不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §34.3 |
| 95 | `list` / `add` / `remove` **没有**权限点 | `[无影响]` | Java 注解被注释，补上会让首页白屏，见 §34.4 |
| 96 | `insertSysIndexMenu` 是"先物理删、后插"且**无事务** | `[需注意]` | 中途失败留下空洞，见 §34.5 |
| 97 | `menuIds` 只剥**一个**尾逗号；中间空段回 500 | `[需注意]` | `"1,2,,"` 是 2 行，`"1,,2"` 直接 500，见 §34.6 |
| 98 | 软删除与物理删除**混用**；`count == 0` 仍 200 | `[无影响]` | 用 `AjaxResult.success` 而非 `toAjax`，见 §34.7 |
| 99 | `SysIndexMenu` 的 JSON 里 `params` 是 `null` | `[需注意]` | `BaseUuidEntity` 没有 `NON_EMPTY`，与 `BaseEntity` 相反，见 §34.8 |
| 100 | `<if test="userId != 1">` 对 `null` **也成立** | `[无影响]` | OGNL 的 `!=`，只有 `1` 走"看全部"分支，见 §34.9 |
| 101 | `getList` 自带 `order by create_time desc` + `limit 9` | `[无影响]` | 固定 9 条，不受分页参数影响，见 §34.10 |
| 102 | `selectSysIndexMenuList` 自带 `order by` → 客户端排序**不生效** | `[需注意]` | 与 `sys_config` 列表相反，见 §34.11 |
| 103 | 整个 `SysUpgradeInfoController` **零权限点** | `[无影响]` | Java 本来就没写 `@PreAuthorize`，见 §35.1 |
| 104 | `/system/upgradeInfo/export` **已实现**，但导出**零列空表** | `[需注意]` | 实体上没有任何 `@Excel`，见 §37.1 / §37.8 |
| 105 | `@Log` 未迁移 → 系统升级信息不写 `sys_oper_log` | `[需注意]` | 业务结果不变，审计查不到，见 §35.3 |
| 106 | `list` 在**控制器**里盖 `tenantId` | `[无影响]` | 客户端传的值被无视，与 indexmenu 的位置相反，见 §35.4 |
| 107 | 新增时**多盖** `tenantId`（indexmenu 不盖） | `[需注意]` | 漏了会让公告对同租户他人不可见，见 §35.5 |
| 108 | `selectSysUpgradeInfoById` **没有** `del_flag` 过滤 | `[需注意]` | 软删除的记录仍能按 id 查到，见 §35.6 |
| 109 | `newest` 的 SQL **无视入参** | `[无影响]` | 传什么版本号结果都一样，见 §35.7 |
| 110 | `back_col1`（`varchar`）与数字 `1` 比较 | `[无影响]` | 只有值为 `"1"` 的行算"最新日志"，见 §35.7 |
| 111 | `remove` 用 `String[]` 而不是 `Long[]` | `[无影响]` | 非数字 id **不会** 500，见 §35.8 |
| 112 | 列表 SQL 自带 `order by` → 客户端排序**不生效** | `[需注意]` | 与 `sys_config` / `sys_index_menu` 同类，见 §35.9 |
| 113 | 两条 `delete` 都是**软删除**；`deleteSysUpgradeInfoById` 无调用方 | `[无影响]` | 按原则第 4 条照留，见 §35.10 |
| 114 | `add` / `edit` **零校验注解**，空 body 也接受 | `[无影响]` | `PUT` 不带 id 会变成**新增**，见 §35.11 |
| 115 | 曾把非法 base64 上传成 0 字节对象（**已修复**） | `[无影响]` | `BytesIO(None)` 不报错，已补判空，见 §36.1 |
| 116 | `@Log` 未迁移 → 文件管理不写 `sys_oper_log` | `[需注意]` | 10 个写操作，审计查不到，见 §36.2 |
| 117 | `SysFileController` 只有 **2 个**权限点，且都“抄错” | `[无影响]` | `base:sysflie:list`（音近拼错）+ `base:supplier:remove`，见 §36.3 |
| 118 | 文件下载失败是 **HTTP 200 + 空 body**，不是 404 | `[需注意]` | `getFile` 吞掉所有异常，见 §36.4 |
| 119 | `getInfo` 用 `-111111` 兜住空 ids | `[无影响]` | 避免拼出 `in ()`，见 §36.5 |
| 120 | `uploadFileId` 的 `AjaxResult.error` 被**丢弃** | `[无影响]` | id 为空时照样往下走，见 §36.6 |
| 121 | 微信上传：扩展名**区分大小写** + **子串**匹配 | `[需注意]` | `.JPG` 被拒、`.mjpg` 能过，见 §36.7 |
| 122 | `selectSysFileById` **没有** `del_flag` 过滤 | `[需注意]` | 软删除的文件按 id 仍能查到，见 §36.8 |
| 123 | 列表自带 `order by` → 客户端排序**不生效** | `[需注意]` | 与 `sys_config` 相反，见 §36.9 |
| 124 | 两条软删 + 一条**物理**删；`updateCAFile` 把主键写死成 3001 | `[需注意]` | CA 驱动固定占 3001，见 §36.10 |
| 125 | `uploadFilesUser` 不写 `del_flag` → 列表里**查不到** | `[无影响]` | 无控制器调用，照留，见 §36.11 |
| 126 | `uploadBase64Picture` 把文件 id 放在 **`msg`** 里 | `[需注意]` | `success(String)` 重载陷阱，**没有 `data` 键**，见 §36.12 |
| 127 | `uploadPdf` 对非 pdf **只写本地临时文件** | `[需注意]` | 结果里没有 `id`，Word→PDF 转换被注释，见 §36.13 |
| 128 | `uploadFileEnc` / `getFileUrl` 是**空实现** | `[无影响]` | 永远 `success([])` / `null`，照留，见 §36.14 |
| 129 | 删除失败的 `msg` 文案与 Java 不同 | `[需注意]` | Java NPE → `null`，Python → 英文异常文本，见 §36.15 |
| 130 | `SysFile.id` 在 JSON 里是**字符串** | `[无影响]` | `@JsonSerialize(ToStringSerializer)` 防 19 位精度丢失，见 §36.16 |
| 131 | 八个 `export` 端点上线：**500 → 200** | `[需注意]` | 补齐历史欠账，不是行为改变，见 §37.1 |
| 132 | 导出返回的是**文件名**（在 `msg`），不是文件 | `[需注意]` | `success(String)` 重载陷阱，**无 `data` 键**，见 §37.2 |
| 133 | 导出的 xlsx 落在 `{profile}/download/` 且**永不清理** | `[需注意]` | 文件名是 UUID，只能顺着 `msg` 走，运维需自加 cron，见 §37.3 |
| 134 | `.xls` **不能**导入（只认 `.xlsx`） | `[需注意]` | openpyxl 不支持 HSSF，回 `code 500`，见 §37.4 |
| 135 | 公式单元格依赖上次保存的**缓存值** | `[需注意]` | `data_only=True`，程序生成的文件公式列为 `None`，见 §37.5 |
| 136 | `SXSSFWorkbook(500)` → 内存 `Workbook` | `[无影响]` | 输出字节等价，只差内存占用，见 §37.6 |
| 137 | `ColumnType.IMAGE` 未迁移，且**显式报错** | `[无影响]` | 零使用；抛 `NotImplementedError` 被吞，日志可见，见 §37.7 |
| 138 | `SysUpgradeInfo` 导出的是**零列空表** | `[无影响]` | 实体没有 `@Excel`，Java 一样，见 §37.8 |
| 139 | `showDropDown` 在 openpyxl 里语义**相反** | `[无影响]` | 写 `False` 才是“显示箭头”，见 §37.9 |
| 140 | `setDefaultColumnStyle` 无对应物 | `[无影响]` | 子列表场景本身休眠，见 §37.10 |
| 141 | 导入的 `Integer` / `Long` 统一按 `to_long` | `[无影响]` | 本项目整型字段全是 `Long`，见 §37.11 |
| 142 | `export` 排序依赖**稳定排序** | `[无影响]` | `sort` 默认 `Integer.MAX_VALUE`，见 §37.12 |
| 143 | `GET /common/download` **已登录反而 403** | `[需注意]` | `anonymous()` 是“只允许匿名”，见 §38.1 |
| 144 | `/common/download/resource` **没有**被 `/common/download**` 遮蔽 | `[需注意]` | `AntPathMatcher` 切段后路径有剩余 → `doMatch` 返 `false`，见 §38.2 |
| 145 | 缺 `fileName` / `delete` **不是 400** | `[需注意]` | 无注解简单类型 `required=false`；缺 `delete` 时“下载成功但不删文件”，见 §38.3 |
| 146 | 下载文件不存在 = **200 + 完整头 + 空 body** | `[需注意]` | `writeBytes` 的 `finally` 关流 = 提交响应，见 §38.4 |
| 147 | 真实文件名**吃掉**第一个 `_` 之前的部分 | `[无影响]` | 去掉的正好是 uuid，见 §38.5 |
| 148 | `delete` 传非法值 → `code 500`，且必须用 `ServiceException` | `[需注意]` | 抛 `ValueError` 会落到 `ServerErrorMiddleware` 被**重抛**，见 §38.6 |
| 149 | 下载白名单**不区分大小写**，上传那边**区分** | `[需注意]` | 22 项；两套规则不能互相参照，见 §38.7 |
| 150 | `/downTemplate/{type}` 未知 `type` = **200 空 body + 零响应头** | `[需注意]` | `url` 停在目录，`setContentType` 在异常点之后，见 §38.8 |
| 151 | `Content-Disposition: attachment` **没有 filename** | `[需注意]` | 下回来叫 `carinfo`（无后缀），见 §38.9 |
| 152 | 模板**原始字节直出**，不经 openpyxl | `[无影响]` | 7 个模板无 `${...}`；重写会丢数据校验，见 §38.10 |
| 153 | `resourceDownload` 方法体**整块注释** → 永远空 body | `[无影响]` | 无调用方，照留，见 §38.11 |
| 154 | `URLEncoder` 安全集（`.-*_`）≠ `quote`（`_.-~`） | `[无影响]` | 手写 `url_encode`，见 §38.12 |
| 155 | `uploadFiles` 的四个值是**逗号串**而非数组 | `[无影响]` | `FILE_DELIMETER` 保留 Java 错拼；批量上传**无回滚**，见 §38.13 |
| 156 | `@Log` 未迁移 → `/monitor` 的 **6 处** `@Log` 全部不生效 | `[需注意]` | 操作日志页只剩历史数据，登录日志不受影响，见 §39.1 |
| 157 | `Cpu.total` 是“tick 总和 × 100”，**不是**百分比 | `[需注意]` | Java 的 `getTotal()` 漏了除以 `total`，上游 bug 照抄，见 §39.2 |
| 158 | CPU 用 psutil 的**秒** × 100 冒充 OSHI tick | `[无影响]` | 只影响 `Cpu.total` 的量级，百分比字段与单位无关，见 §39.3 |
| 159 | `Jvm` 面板映射成**宿主机内存** | `[需注意]` | Python 没有 JVM；换来的是自洽的 `used` / `usage`，见 §39.4 |
| 160 | 磁盘分区采集失败时**跳过**该分区 | `[无影响]` | Java 会让整个 `copyTo()` 失败，见 §39.5 |
| 161 | `cache.info` / `commandStats` 的键顺序**稳定** | `[无影响]` | Java 的 `Properties` 无序，键集合相同，见 §39.6 |
| 162 | `businessTypes` 额外接受**逗号串** | `[无影响]` | RuoYi 前端发的是重复键；多接受一种写法，见 §39.7 |
| 163 | `parseInfo` 的空白处理逐字对齐 `Properties.load` | `[无影响]` | 真实 `INFO` 输出两侧没有空白，见 §39.8 |
| 164 | `DELETE .../clean` 在 Python 侧**注册在 `{ids}` 之前** | `[无影响]` | Spring 靠 `AntPathMatcher` 偏爱字面量，净结果一致，见 §39.9 |
| 165 | `SysUserOnline.loginTime` 是 epoch **毫秒数字** | `[无影响]` | 该实体不继承 `BaseEntity`，不走日期格式化，见 §39.10 |
| 166 | `selectOperLogById` / `selectUserOnlineList` **无调用方** | `[无影响]` | 死代码，按原则第 4 条照留，见 §39.11 |
| 167 | `businessType = 0`（其它）的筛选**被丢掉** | `[需注意]` | OGNL 把 `""` 当 `0.0`，选“其它”会查出全部记录，见 §39.12 |
| 168 | 两个 `export` 的文件名在 **`msg`**，没有 `data` | `[需注意]` | `success(String)` 重载陷阱，见 §39.13 |
| 169 | `/monitor/online/list` **没有分页**，`total` 是列表长度 | `[需注意]` | `pageSize=10` 也会拿到全部在线用户，见 §39.14 |
| 170 | `forceLogout` 对不存在的 token 也回 **200** | `[无影响]` | `deleteObject` 的返回值被丢弃，见 §39.15 |
| 171 | 在线用户扫描用 **`KEYS`**（O(N) 阻塞） | `[需注意]` | Spring Data Redis 同样如此；会话多了会卡住 Redis，见 §39.16 |
| 172 | `psutil==6.1.1` 早已是声明依赖 | `[无影响]` | `pyproject.toml` 里标注 `<- oshi-core`，无需新装，见 §39.17 |
| 173 | 安全探针路径搬到 `/migration/probe/never-mapped` | `[无影响]` | 仅测试侧；`/monitor/online/list` 已注册，不再是 404，见 §39.18 |
| 174 | **金额类 `BigDecimal` 在 JSON 里是字符串** | `[需注意]` | 全局 `ORJSONResponse` 所致；Java 输出数字，`"12.5"` vs `12.5`，见 §40.1 |
| 175 | `/manager/bigScreen` **12 个端点一个权限点都没有** | `[需注意]` | Java 类上确实没有 `@PreAuthorize`，登录即可访问，见 §40.2 |
| 176 | 路径里的 `bigScreen` 是**驼峰** | `[无影响]` | 同包其它控制器全小写；改小写就是 404，见 §40.3 |
| 177 | `code` 为空时塞的是三个**魔法值** | `[需注意]` | `StationCapture` / `GantryCapture` / `ServiceAreaCapture`，按它们查库命中 0 行，见 §40.4 |
| 178 | `"all"` 是**子串**判断，`deleteEnd` 只削**一个**逗号 | `[需注意]` | `"SD01,all"` 会退化成全量；`"SD01,,"` 切完仍是 `["SD01"]`，见 §40.5 |
| 179 | `exceptRecordList` 的 **N+1** 查询原样保留 | `[需注意]` | 每行 2 次额外查询；`pageSize` 大时线性增长，见 §40.6 |
| 180 | `carAudit` 的空值是**零初值**，不是 `null` | `[无影响]` | 四个字段都有非 null 初值，见 §40.7 |
| 181 | `type` 缺失时手抄 Spring 的**英文原文** | `[无影响]` | `MissingServletRequestParameterException` 的固定句式，见 §40.8 |
| 182 | `bigscreen/center` 的 **7 个 VO 未迁移**（死代码） | `[无影响]` | 全仓无引用，属未实现的“城市配送大屏”，见 §40.9 |
| 183 | 三个 base 实体**补回** `sectionCodeList` | `[无影响]` | Java 有 `@TableField(exist = false)`，Python 侧此前漏建，见 §40.10 |
| 184 | 控制器方法名就叫 `list`，**遮蔽内置函数** | `[无影响]` | 与 Java 同名，便于 `# Java:` 检索；调用方用 `module.list`，见 §40.11 |
| 185 | `GET /base/fitting/list` 在 Java 侧**恒定 500** | `[需注意]` | XML 的 `<if test="id">` 指向实体不存在的属性，Python 侧不复制崩溃，见 §41.1 |
| 186 | `...BO` 这类大写缩写**必须**写 `alias` | `[无影响]` | `to_camel` 只拼得出 `Bo`；全仓共 6 个字段，见 §41.2 |
| 187 | PageHelper 在 count 前**删掉最外层 `ORDER BY`** | `[无影响]` | `CountSqlParser#removeOrderBy`；`order by` 引用不存在的列时 Java 反而不报错，见 §41.3 |
| 188 | `BigDecimal` 出的是**数字且保留 scale** | `[无影响]` | `BigDecimal.ZERO` → `0`；`decimal_to_java_number()`，见 §41.4 |
| 189 | `GET /system/user`（无尾斜杠）= 405 → `code 500` | `[无影响]` | `@GetMapping({"/"})` 只匹配带尾斜杠的形式，见 §41.5 |
| 190 | 外部服务 `:9901` 不可达时的 `msg` **不对齐** | `[需注意]` | 两边都 200 + `code 500`，文案来自 Apache HttpClient，刻意不伪造，见 §41.6 |
| 191 | 6 个 `export*` 只比内容、不比字节 | `[无影响]` | EasyExcel 与 openpyxl 的 zip 打包参数不同，见 §41.7 |
| 192 | `searchValue` 在 `BaseEntity` 被忽略、在 `BaseUuidEntity` **不**被忽略 | `[需注意]` | 两个同名基类**只有一个**带 `@JsonIgnore`，见 §41.8 |
| 193 | `/system/user/list` 每行的 `deptName` 都是 `null` | `[无影响]` | `<association>` 让 MyBatis 整体关掉自动映射，见 §41.9 |
| 194 | `quartz` 切片完成：**13 个端点** + 6 个任务 Bean | `[无影响]` | 逐字段对齐，见 §42 / `MAPPING_QUARTZ.md` |
| 195 | Quartz 由**自研内存调度器**承接，不是 APScheduler | `[无影响]` | 换库会让 `Key.toString()`、`SchedulerException` 文案、cron 方言漂移，见 §12 / §42.1 |
| 196 | `AbstractQuartzJob#execute` 曾缺 `TASK_PROPERTIES` 导入 | `[需注意]` | 每次执行都 `NameError` 且不落作业日志，**已修复**，见 §42.2 |
| 197 | `insertBatchToTable` 里 25 个属性在实体上**不存在** | `[需注意]` | Java 侧抛 `ReflectionException`，语句从未执行过，见 §42.3 |
| 198 | `SnapshotFlowSyncTask` 在 Java 里就是**空转** | `[无影响]` | `convertToEntityList` 的 `instanceof` 永远为假，照抄，见 §42.4 |
| 199 | `invoke_target` 存的是 **Java 方法名** | `[无影响]` | 已加 `toUnderScoreCase` 桥，`sys_job` 数据一个字不动，见 §42.5 |
| 200 | `RyTask` 的布尔参数拼成小写 `true`/`null` | `[无影响]` | Java `String.valueOf` 语义，会进 `sys_job_log.job_message`，见 §42.6 |
| 201 | `sys_job` 装载失败：Java 启动失败，Python 只记日志 | `[需注意]` | 无库环境也能起服务；那一行警告是唯一信号，见 §42.7 |
| 202 | **`@Log` 现已全量生效**，13 条历史"未迁移"结论作废 | `[需注意]` | 233 处：admin 217 + quartz 9 + generator 7，见 §42.9 / §44.4 |
| 203 | `@PreAuthorize` 与参数解析的先后顺序**相反** | `[需注意]` | 仅 `/monitor/jobLog/{configId}`（恒定 500），见 §43.1 |
| 204 | 单值 `Long` 路径变量传非数字时 `msg` 是 pydantic 的 | `[无影响]` | `Long[]` / `Boolean` 两种形态已是 Java 原文案，见 §43.2 |
| 205 | 启动脚本用 `psutil` 找进程，不用 `jps -l` | `[无影响]` | 四个操作与 `ry.sh` / `ry.bat` 一致，见 `README_PY.md` §5 |

> **2026-10 修订（Phase 3.23）**：上表第 **26 / 30 / 33 / 38 / 45 / 53 / 64 / 73 / 85 /
> 94 / 105 / 116 / 156** 条写的是"`@Log` 未迁移 → 不写 `sys_oper_log`"，
> 该结论**已被推翻**（`LogAspect` 已迁移，全仓 **233** 处 `@Log` 全部生效）。
> 这 13 行保留原样只为不打断编号与交叉引用，请以 §42.9 为准。

---

## 1. 新增端点 `GET /health` `[可配置]`

**Java 原行为**
项目没有 Actuator、没有 `/health`、没有任何健康检查端点。
唯一的存活信号是 `GET /`（`SysIndexController`），它只返回一句欢迎语，**不探测任何依赖**。

**Python 实现**
新增 `GET /health`，复用 `AjaxResult` 结构：

```json
{"code": 200, "msg": "操作成功",
 "data": {"status": "UP", "application": "系统", "version": "3.8.7",
          "components": {"db": "UP", "redis": "UP"}}}
```

- HTTP 状态码**永远 200**（遵循 RuoYi 约定），真实状态看 `data.status`
- `data.status == "UP"` 当且仅当 MySQL 与 Redis 都可达
- 依赖不可达时 `code` 仍是 200，`msg` 变为 `"部分依赖不可用"`
- 该路径已加入过滤器链的 `permitAll` 白名单（见 §18），否则健康检查自己就会先被判 401

**影响与规避**
纯增量，不修改任何既有路径/响应/状态码。
关闭方式：`app.health-endpoint-enabled: false` 或 `APP__HEALTH_ENDPOINT_ENABLED=false`，
关闭后 `/health` 返回真实的 404（与 Java 一致）。

**为什么必须加**
Phase 5 验收要求「健康检查通过」，而 Java 版没有任何可探测依赖的端点。

---

## 2 & 3. HTTP 状态码约定 `[无影响]`

> 这两条**不是**差异，写在这里是因为迁移时最容易被误改。

**Java 原行为**

| 场景 | HTTP 状态 | 响应体 |
|---|---|---|
| 业务异常 `ServiceException` | **200** | `{"code":500,"msg":"..."}` |
| 权限不足 `AccessDeniedException` | **200** | `{"code":403,"msg":"没有权限，请联系管理员授权"}` |
| 参数校验失败 | **200** | `{"code":500,"msg":"..."}` |
| 请求方法不支持 | **200** | `{"code":500,"msg":"Request method 'POST' not supported"}` |
| 认证失败（未登录/Token 过期） | **200** | `{"code":401,"msg":"请求访问：/x，认证失败，无法访问系统资源"}` |
| **路由未匹配** | **404** | `{"timestamp","status","error","path"}`（Spring `BasicErrorController`） |

根因：`ServletUtils.renderString` 硬编码 `response.setStatus(200)`，而 `@ExceptionHandler`
返回 `AjaxResult` 时 Spring 也用 200 序列化。

**Python 实现**
`app/config/exception_handlers.py` 完整复刻上表。特别是 404 分支回退到真实的 HTTP 404
并手写 Spring 的错误体，保证「客户端按 HTTP 状态码分支」的老代码不会失效。

**回归用例**
`tests/test_http_contract.py::TestGlobalExceptionHandler`

---

## 4. `BaseException` → `RuoYiBaseException` `[无影响]`

Java 的 `com.ruoyi.common.exception.BaseException` 与 Python 内建的 `BaseException`
**同名**。若在 Python 中叫 `BaseException`，会遮蔽内建类型，导致
`except BaseException:`（捕获 `KeyboardInterrupt` / `SystemExit`）静默变成捕获业务异常 —— 极危险。

因此重命名为 `RuoYiBaseException`，继承链保持 `RuoYiBaseException(RuntimeError)`，
`ServiceException(RuntimeError)`，`BusinessException(ServiceException)`。
业务侧真正被 catch 的是 `ServiceException`，与 Java 的 `@ExceptionHandler(ServiceException.class)` 对应。

**`args` 字段为什么叫 `arguments`**
Java 的 `BaseException` 有一个 `private Object[] args`，配合 `MessageUtils` 做 i18n 占位符填充。
Python 的 `BaseException` **自带** `args`，而且它是 CPython 的 getset 描述符，只接受 `tuple`：

```python
self.args = None   # TypeError: 'NoneType' object is not iterable
```

所以字段改名为 `self.arguments`，并保留 `get_args()` 访问器维持与 Java getter 的对应。
`resolve_message()` 读的是 `arguments`，`super().__init__(message)` 传入的是解析后的字符串 ——
**不要**改成 `super().__init__(*arguments)`，那会让 `str(exc)` 退化成 arg 元组的 repr。
这个坑只有真正抛出 `RuoYiBaseException("账号已停用")` 时才会炸，Phase 3.3 的用例才把它暴露出来。

---

## 5. `AjaxResult.put(...)` → `AjaxResult.put_chain(...)` `[无影响]`

Java 的 `AjaxResult extends HashMap` 并覆写 `put` 使其返回 `this`（链式调用）：

```java
return success().put("key", value);
```

Python 的 `AjaxResult(dict)` 若覆写 `put`，会破坏 `dict` 协议的语义（`dict.put` 不是标准方法，
但 `update`/`setdefault` 等存在同名冲突风险），且 `mypy`/`dict` 子类化约定不鼓励。
因此保留同名语义、改名为 `put_chain`，行为完全一致：

```python
result.put_chain("key", value)   # 返回 self，可链式
```

**逐条重载对照表**见 `app/common/core/domain/ajax_result.py` 模块 docstring。

### 5.1 JSON 键序是 **HashMap 桶序**，不是 `put` 先后 `[需注意]`

`AjaxResult extends HashMap<String, Object>`，Jackson 走的是 `HashMap` 的迭代器，
而 `HashMap` 的迭代序是**桶号升序**（`(h = hashCode) ^ (h >>> 16)` 的低 4 位，默认容量 16），
不是插入序。所以 `success()` 的真实字节是：

```text
{"msg":"操作成功","code":200}
```

`msg`(桶 0) 在 `code`(桶 3) **前面** —— 这是 RuoYi 全站响应的样子，不是笔误。

Python 的 `dict` 是插入序，所以：

* `AjaxResult._create` / `put_chain` **必须** 走
  `app.common.core.domain.java_hash_map.put_in_order`；
* 控制器里 **禁止** 写 `ajax["key"] = value`（那会排到末尾）。验证码与
  `getConfirmId` 曾各踩一次，已在 Phase 6 改正。

完整的桶号对照表与实际响应的最终键序见 `java_hash_map.py` 模块 docstring。
回归阀：`tests/test_core_types.py::TestAjaxResult::test_put_chain_places_keys_by_bucket_not_by_call_order`。

**对照**：`TableDataInfo` 与 `R` 都是普通 POJO，Jackson 按**字段声明序**输出
（`total, rows, code, msg` / `code, msg, data`），**不要**也套上桶序。

---

## 6. Tomcat 线程池 → anyio 线程池 `[无影响]`

**Java 原行为**
`server.tomcat.threads.max: 800` → 最多 800 个请求工作线程并发执行阻塞 JDBC 调用。

**Python 的坑**
所有端点都写成 sync `def`（为了与 JDBC / ThreadLocal 语义 1:1），
Starlette 会把每个请求丢到 **anyio 默认线程池**，而该池**默认上限只有 40**。
若不处理，并发能力会静默下降 20 倍 —— 这属于「迁移后变慢但看不出原因」的典型事故。

**Python 实现**
`app/main.py::_apply_tomcat_thread_parity` 在 lifespan 启动时把
`anyio.to_thread.current_default_thread_limiter().total_tokens` 设为 `server.tomcat.threads.max`（800）。
启动日志会打印：`[启动参数] anyio 线程池上限 = 800 (对应 server.tomcat.threads.max)`。

---

## 7. 日志滚动策略 `[需注意]`

**Java（logback.xml）**
按「时间 + 大小」双条件滚动，单文件 100 MB，保留 60 天。

**Python（logging.handlers.RotatingFileHandler）**
只支持按大小滚动：`maxBytes=100MB`，`backupCount=30`（30 个历史文件）。
没有「按天」维度。

**运维影响**
如果日志量小（每天远不到 100 MB），Java 会每天生成一个新文件、保留 60 天；
Python 会一直是同一个文件直到滚到 100 MB。**日志内容与级别完全一致，只是切分粒度不同。**

**规避**
如需按天切分，把 `app/logging_config.py::_rotating_handler` 换成
`TimedRotatingFileHandler(when="midnight", backupCount=60)` —— 但会失去单文件大小上限。
本项目选择保大小（避免单文件无限增长），因为 Java 的 60 天策略在低流量下更浪费磁盘。

---

## 8. p6spy → SQLAlchemy 事件监听器 `[无影响]`

**Java 原行为**
`spy.properties`：`appender=StdoutLogger`，p6spy 把**每条** SQL 打到 stdout
（格式 `Consume Time: xx ms` + `Execute SQL: ...`）；
`filter.stat.slow-sql-millis: 1000` 另外统计慢 SQL；
`SqlLogInterceptor` 对慢 SQL 额外告警。

**Python 实现**
`app/config/database.py::_register_slow_sql_listener`：

| 级别 | 内容 | 对应 Java |
|---|---|---|
| DEBUG | `[SQL] 耗时=0ms \| SELECT 1 \| params={}` | p6spy `StdoutLogger` |
| WARNING | `[慢SQL告警] 耗时=1200ms, 阈值=1000ms, SQL=...` | Druid stat filter |

因为 `logging.level.com.ruoyi: debug`，DEBUG 默认可见 —— 与「p6spy 无条件打印」等价。

**额外处理**
SQLAlchemy 自带的 `sqlalchemy.engine` echo 会打印方言探测语句
（`SELECT DATABASE()` / `SELECT @@sql_mode` / `SELECT @@lower_case_table_names`），
**JDBC 驱动不做这些输出**，所以被压到 `WARNING` 级，避免出现 Java 没有的噪音。

---

## 9. Druid 监控台不迁移 `[需注意]`

**Java 原行为**
`application-druid.yml` 配置了 `statViewServlet`，`url-pattern: /druid/*`，
账号 `druidUser / Sys#2024Test`。但 `SecurityConfig` 里 `/druid/**` 是 `denyAll()` ——
**普通用户与管理员都访问不到**，实际上是个死配置。

**Python 实现**
不迁移。`/druid/**` 直接 404。

**影响**
如果确实有人绕过鉴权在用 Druid 监控台，会失效。目前判断为「看似无用但可能有意为之」的配置，
按迁移原则第 4 条（不删除看似无用的代码，标注并询问）在此登记，**未做任何删除动作**。
若确认需要，可另起一个受保护的路由提供连接池指标。

---

## 10. 接受但不生效的配置项 `[无影响]`

| 配置 | 原因 |
|---|---|
| `server.tomcat.*`（`uri-encoding`、`accept-count`、`threads.*`） | uvicorn 不暴露 Tomcat 参数；`threads.max` 例外，被用来设 anyio 上限（§6） |
| `spring.devtools.restart.enabled` | 等价物是 `uvicorn --reload`，见 `run.py --reload` |
| `mybatis-plus.*` | Python 侧用 SQLAlchemy Core 执行手写 SQL，无 MyBatis 运行时 |
| `pagehelper.*` | 分页改为显式 `count` 查询，见 Phase 3 的 `page_helper` |
| `generator-code.*` | 代码生成器（`ruoyi-generator`）迁移时另行处理 |
| `xss.*` | XSS 过滤在 Phase 3 随 `XssFilter` 一起迁移 |

这些字段保留在 `config/application.yml` 里，**目的是让 Java 开发者可以逐行 diff 原配置**，
而不是「配置被悄悄丢掉」。

---

## 11. `@Scheduled` 默认不执行 `[可配置]`

**重要发现（Finding A）**
Java 工程里存在 **9 个** `@Scheduled` 方法：

- `SnapshotFlowSyncTask`
- `ViewMaintenanceTask`
- `PartitionMaintenanceTask`
- `ShardingTableTask`

但全工程 **没有任何 `@EnableScheduling`**，`ScheduleConfig.java` 整个文件被注释掉。
结论：**这些定时任务在 Java 线上从未执行过。**

**Python 实现**
`app.scheduled-annotations-enabled: false`（默认）。
`app/main.py` 启动时打印：

```
[启动警告] @Scheduled 已禁用, 与 Java 运行时一致 (Java 缺少 @EnableScheduling)
```

**这是一次「镜像运行时现实」而非「修复 bug」的决策**（见 §决策记录）。
若确认这些任务**本应**运行（即 Java 侧漏加注解），把开关改为 `true` 即恢复，
但请注意：这会让 Python 版产生 Java 版从未产生的数据变更。

---

## 12. Quartz → **自研内存调度器**（不是 APScheduler） `[无影响]`

**重要发现（Finding B）**
- `ruoyi-quartz/pom.xml` 只依赖 `org.quartz-scheduler:quartz`，**没有** Spring Boot Quartz starter
- `ScheduleConfig.java` 整个文件被注释掉
- 因此 `SysJobServiceImpl` 里 `@Autowired Scheduler scheduler` 只能来自 Spring Boot 的
  `QuartzAutoConfiguration`，使用**默认内存 JobStore**（`RAMJobStore`）
- `SysJobServiceImpl` 的 `@PostConstruct init()` 在每次启动时把 `sys_job` 重新装载进调度器

**Python 实现**
`app/quartz/util/scheduler.py`（内存 JobStore + per-job 锁）与
`app/quartz/util/cron_expression.py`（Quartz 2.3.2 `CronExpression` 的逐行转写），
启动时由 `app/main.py::_init_quartz` 从 `sys_job` 表重载任务。
因为 Java 用的是内存 JobStore，**重启后任务丢失、靠 `init()` 重载**，Python 行为完全一致。

关闭方式：`app.scheduler-enabled: false`（Java 没有这个开关，属本工程新增，见 §42.7）。

> 本节标题此前写的是 "Quartz → APScheduler"，那是 Phase 4 之前的设计草案。
> **实际落地是自研实现**：换第三方库会让 `Key.toString()`（`group.name`）、
> `SchedulerException` 的原文案、"删不存在的任务不报错"、cron 方言这四类
> **可观察行为**全部漂移。逐条对照见 §42.1。

---

## 13. Kafka / MinIO 默认关闭 `[可配置]`

**运行环境实测（2026-10-22）**

| 服务 | 端口 | 状态 |
|---|---|---|
| MySQL | 3307 | OPEN |
| Redis | 6379 | OPEN |
| Elasticsearch | 9200 | OPEN |
| Kafka | 9092 | **CLOSED** |
| MinIO | 172.30.100.102:9002 | **CLOSED** |
| `vehicleMonitor` 外部服务 | 9901 | **CLOSED** |
| 原 Java 应用 | 9989 | **CLOSED** |

Kafka 有 4 个 `@KafkaListener` consumer，MinIO 负责文件上传下载。
若默认启用，服务会因为连不上 broker 而反复重试 / 启动变慢。

**Python 实现**
`app.kafka-enabled: false`、`app.oss-enabled: false`（默认），启动时打印告警：

```
[启动警告] Kafka 已禁用 (app.kafka_enabled=false); 4 个 consumer 不会启动
[启动警告] MinIO/OSS 已禁用 (app.oss_enabled=false); 文件上传/下载将不可用
```

**注意**：这不改变任何**接口行为**，只是不启动后台 consumer / 不让上传接口工作。
一旦 broker 就绪，把开关打开即可（配置项已按 Java 原样映射，见 `.env.example`）。

---

## 14. Alembic 只做结构查看 `[无影响]`

**Java 原行为**
没有 Flyway、没有 Liquibase。表结构由 `ruoyi-system/src/main/resources/sql/*.sql` 人工执行，
schema 就是「库里的现状」。

**Python 实现**
初始化了 Alembic，但：
- `alembic.ini` 里 `sqlalchemy.url` 留空，连接串统一从 `app.settings` 读取（避免两份数据库配置）
- `target_metadata = None` —— 没有声明式模型，因为 97 个 MyBatis XML mapper 才是 SQL 的唯一权威
- 因此 `--autogenerate` 只会输出「删除所有表」，**禁止**用于生成迁移

**铁律**
不执行 `alembic upgrade head` 改生产库。表结构变更仍然走 Java 侧的 `sql/*.sql`。
`alembic current` / `alembic history` 可以安全使用。

**验收记录**
```
> .venv\Scripts\alembic.exe current
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
```

> `alembic.ini` 必须保持**纯 ASCII**：Alembic 用 `configparser` 以 `encoding="locale"` 读取，
> 中文 Windows 的 locale 是 GBK，文件里出现 UTF-8 中文/emoji 会让 `alembic` 直接崩溃。

---

## 15. 标准输出编码 `[无影响]`

**Java 原行为**
`System.out` / `System.err` 用**平台默认字符集**，无法映射的字符替换成 `?`，**永不抛异常**。

**Python 的坑（已修复的真实缺陷）**
stdout 被重定向（管道、文件、IDE 捕获、systemd）时使用的是 locale 编码，
中文 Windows 上是 GBK。启动横幅里的 `♥` / `ლ` 会抛 `UnicodeEncodeError`：

```
UnicodeEncodeError: 'gbk' codec can't encode character '\u2665' in position 1
```

后果不是「少打一行日志」，而是**进程启动失败**。

**Python 实现**
`app/main.py::_relax_stdio_encoding()` 在模块导入时执行
`sys.stdout.reconfigure(errors="replace")` / `sys.stderr.reconfigure(errors="replace")`。

**为什么只改 errors、不改 encoding**
改成 UTF-8 会让 GBK 控制台显示乱码，而 Java 在同样的控制台上是可读的。
保留平台编码 + 替换策略，才与 `PrintStream` 完全一致（`♥` → `?`）。

**回归用例**
`tests/test_logging.py::TestStdioEncoding`

---

## 16. 配置优先级 `[无影响]`

**Java / Spring**
`命令行参数 > OS 环境变量 > application.yml > 字段默认值`

**Python 的坑（已修复的真实缺陷）**
最初实现是 `AppSettings(**yaml_values)`。pydantic-settings 中**构造参数优先级最高**，
高于环境变量 —— 于是 `SERVER__PORT=9990` 被 `application.yml` 的 `9989` 静默覆盖，
与 Spring 恰好相反，且不会报错。

**Python 实现**
`AppSettings.settings_customise_sources` 显式声明来源顺序：

```
构造参数 > OS 环境变量 > .env > config/application.yml > secrets > 字段默认值
```

`get_settings()` 不再传任何构造参数。**回归用例**：
`tests/test_settings.py::TestSourcePrecedence`

---

## 17. 动态数据源不迁移 `[无影响]`

**Java 原行为**
`DynamicDataSource` + `@DataSource(DataSourceType.SLAVE)` 通过 AOP 切换主从库。

**Python 实现**
单一 engine。因为 `application-druid.yml` 里从库是 `slave.enabled: false`，
`DynamicDataSource.determineCurrentLookupKey` 永远返回 master。
**没有任何一条 SQL 会走从库**，所以单 engine 与 Java 完全等价。

`@DataSource` 注解的迁移见 Phase 3（`DataSourceType` 常量保留，装饰器为空实现，便于日后启用从库）。

---

## 18. 过滤器链：Spring Security → ASGI 中间件 `[无影响]`

**Java 原行为**
`SecurityConfig` 注册了一条固定顺序的过滤器链，顺序决定了「谁能看到什么」：

```
CorsFilter → LogoutFilter → JwtAuthenticationTokenFilter
           → AnonymousAuthenticationFilter → ExceptionTranslationFilter
           → FilterSecurityInterceptor（真正的鉴权）
           → DispatcherServlet（路由）
```

由此得出的、客户端可感知的结论（已逐条复刻）：

| 场景 | 结果 |
|---|---|
| 未带 Token 访问受保护路径 | **HTTP 200** + `{"code":401,"msg":"请求访问：/x，认证失败，无法访问系统资源"}` |
| 未带 Token 访问**不存在的**路径 | 同上 —— 鉴权跑在路由之前，所以是 401 而不是 404 |
| 已登录访问 `anonymous()` 规则（如 `/system/file/view/**`） | **真实 403** + Spring `BasicErrorController` 错误体 `{timestamp,status,error,path}` |
| 已登录访问 `denyAll()` 规则 | 同上，403 |
| 未登录访问 `denyAll()` 规则 | `ExceptionTranslationFilter` 判定「匿名 → 走 EntryPoint」，返回 401 体（HTTP 200） |
| Token 签名或格式错误 | **真实 500** —— 过滤器抛出的异常到不了 `@ControllerAdvice` |
| 预检 `OPTIONS` | `CorsFilter` 自己应答，**不进鉴权**，也不需要 Token |

**Python 实现**

| Java | Python |
|---|---|
| `SecurityConfig#configure(HttpSecurity)` | `app/framework/config/security_config.py::AUTHORIZATION_RULES` |
| `JwtAuthenticationTokenFilter` | `app/framework/security/filter/jwt_authentication_token_filter.py` |
| `AuthenticationEntryPointImpl` | `app/framework/security/handle/authentication_entry_point_impl.py` |
| `LogoutSuccessHandlerImpl` | `app/framework/security/handle/logout_success_handler_impl.py` |
| `FilterSecurityInterceptor` + `ExceptionTranslationFilter` | `app/middleware/security.py` |
| `CorsFilter`（最外层） | `app/main.py` 中注册在安全中间件**之外**的 `CORSMiddleware` |

两个实现细节值得知道：

1. **`SecurityMiddleware` 必须注册在最内层。** `main.py` 的注册顺序是
   `Security → RequestContext → CORS → TraceId`，Starlette 会反转，最终执行顺序正好是
   `TraceId → CORS → RequestContext → Security → 路由`。安全层要「内」于 `RequestContextMiddleware`，
   `AsyncFactory.recordLogininfor` 才能从上下文里读到 `Request`；CORS 必须在「外」面，
   否则预检会被当成未授权请求。
2. **只捕获过滤器阶段的异常。** 端点内部抛出的异常**不允许**被这一层吞掉，否则
   `ServiceException` 得不到约定中的「HTTP 200 + code 500」，会退化成 500。
   实现方式是先 `await to_thread.run_sync(过滤器链)`、再 `await call_next(request)`，只给前者套 `try`。

**回归用例**
`tests/test_security_filter.py`（27 例）+ `tests/test_http_contract.py::test_root_only_get_is_permitted`、
`::test_unmapped_path_without_token_is_unauthorized`

---

## 19. `/logout` 接受任意 HTTP 方法 `[需注意]`

**Java 原行为**
`LogoutConfigurer#createLogoutRequestMatcher` 只有在 CSRF 开启时才会把匹配器固化成 `POST /logout`；
本项目 `SecurityConfig` 里 `csrf().disable()`，走的是「不限定方法」的分支 —— 因此 `GET /logout` 同样会注销。
另外 `/logout` **不在**规则表里（`LogoutFilter` 先于鉴权），所以它既不需要 Token 也不会 403。

**Python 实现**
`security_config.is_logout_request()` 只比对路径、不比对方法；`/logout` 也没有写进 `AUTHORIZATION_RULES`。

**待办**
这一条是从源码推导的，尚未对着运行中的 Java 实例验证。若实机确认是 `POST only`，
只需改 `is_logout_request` 一行。

**回归用例**
`tests/test_security_filter.py::TestLogout`

---

## 20. 静态资源规则遮蔽 swagger/druid 的 `denyAll` `[无影响]`

**Java 原行为**
`denyAll()` 组写在静态资源 `permitAll()` 组**之后**，而 Spring 的匹配器列表是**首次匹配即返回**：

```java
.antMatchers(HttpMethod.GET, "/*.html", "/**/*.html", "/**/*.js", "/**/*.css").permitAll()
.antMatchers("/swagger-ui.html", "/swagger-resources/**", "/webjars/**", "/*/api-docs", "/druid/**").denyAll()
```

所以 `GET /swagger-ui.html` 命中的是 `/*.html` 的 `permitAll`，`denyAll` 对这类 GET 路径**是死代码**。

**实际生效情况（已逐条核对）**

| 路径 | 结果 |
|---|---|
| `GET /swagger-ui.html`、`GET /druid/index.html`、`GET /webjars/springfox.js` | `permitAll`（被遮蔽） |
| `GET /druid/api/list`、`GET /swagger-resources/configuration/ui`、`GET /v3/api-docs` | `denyAll` |
| `GET /webjars/lib/data.json`（非 js/css/html） | `denyAll` |
| `POST /swagger-ui.html`（静态规则只放行 GET） | `denyAll` |

**Python 实现**
`AUTHORIZATION_RULES` **保持 Java 的声明顺序**，不做「顺手修正」——迁移原则第 4 条：不擅自修 Java 的缺陷。
要修也应该先改 Java，再同步过来。

**回归用例**
`tests/test_security_filter.py::TestAuthorizationRuleTable::test_static_resource_rules_shadow_the_deny_all_rules`
与 `::test_management_endpoints_are_deny_all`

---

## 21. User-Agent 解析：`useragentutils` → `user_agents` `[需注意]`

**Java 原行为**
`AsyncFactory.recordLogininfor` 用 `UserAgentUtils.parseOsAndBrowser(userAgent)` 解析出
`browser` / `os` 两列写入 `sys_logininfor`。

**Python 实现**
`app/common/utils/user_agent_utils.py` 用 `user_agents`（ua-parser）做同样的事，输出固定枚举：
浏览器 `Chrome` / `Firefox` / `Safari` / `Edge` / `Opera` / `Mobile` / `Unknown`，
系统 `Windows 10` / `Windows` / `Mac OS X` / `Android` / `iOS` / `Linux` / `Unix` / `Unknown`。

**差异面**
两个库的识别表天然不同，**冷门或非浏览器 UA**（爬虫、脚本客户端、自定义 UA）可能落在不同的枚举值上。
常见组合（Chrome/Windows、Safari/macOS 等）已用回归用例钉住。

**影响**
只影响 `sys_logininfor.browser` / `sys_logininfor.os` 两个**审计列**，不影响任何鉴权判断 —— 鉴权只用
`Authorization` 头。

**回归用例**
`tests/test_security_filter.py::TestLogout::test_logout_deletes_the_session_and_writes_the_audit_row`

---

## 22. 验证码图片：`java.awt` → Pillow `[无影响]`

**Java 原行为**
`CaptchaConfig` 注册两个 kaptcha `DefaultKaptcha` bean，`CaptchaController.getCode()` 按
`ruoyi.captchaType` 二选一；`DefaultKaptcha#createImage` 用 `java.awt` 的 `Graphics2D` /
`GradientPaint` / `ShadowGimpy` 画图，`ImageIO.write(image, "jpg", os)` 编码 JPEG，
最后 `Base64.encode()` 塞进 `AjaxResult.img`。

**Python 实现**
`app/framework/config/captcha_config.py` 用 Pillow 重画，两个 bean 的配置逐项对应：

| 配置项 | `captchaProducer`（char） | `captchaProducerMath`（math） | 是否保留 |
|---|---|---|---|
| 图片尺寸 | 160 × 60 | 160 × 60 | 是 |
| 边框 | 有，1px，黑色 | 有，1px，`rgb(105,179,90)` | 是 |
| 文字颜色 | 黑色 | 蓝色 | 是 |
| 字号 | 38 | 35 | 是 |
| 字间距 | 2 | 3 | 是 |
| 字体 | `Arial,Courier`，**每个字符随机取一个** | 同左 | 是 |
| 噪点 | `DefaultNoise` | `NoNoise` | 近似 |
| 背景 | `WHITE` → `LIGHT_GRAY` 竖向渐变 | 同左 | 是 |
| 阴影 | `ShadowGimpy` | 同左 | 近似 |
| 输出 | JPEG，JDK 默认质量 0.75 | 同左 | 是（Pillow 默认 75） |

**不能等价的部分**
kaptcha 的光栅器、字形 hinting、抗锯齿与 Pillow 完全不同，同一串字符渲染出的字节**必然不同**。
这点无法也不应追求对齐 —— 验证码的契约是「人能读出算式」，不是「像素一致」。
具体近似项：

- `ShadowGimpy`：Java 是「按偏移量逐像素复制一层再变暗」，Python 改为「偏移的文字层做高斯模糊 +
  半透明着色」。视觉上都是右下方一层淡影。
- `DefaultNoise`：Java 随机画短线，Python 随机打单像素点，密度按面积取
  `width × height / 250` 的近似值（math 生产者本来就 `NoNoise`，不受影响）。
- 字体回退：`Arial` / `Courier New` 在 Windows 上直接命中；Linux 容器回退到
  `DejaVuSans` / `DejaVuSansMono`；都没有则 `ImageFont.load_default(size=...)`。
  **容器镜像建议装 `fonts-dejavu-core`**，否则图片能生成但字形明显更粗糙。
- JPEG 字节数不同，`img` 的 base64 长度自然也不同。

**客户端影响**
无。客户端只做两件事：把 `img` 拼成 `data:image/jpeg;base64,{img}` 的 URL 交给图片标签展示，
以及把用户输入的答案放进 `POST /login` 的 `code` 字段。二者都与渲染器无关。

**回归用例**
`tests/test_login_service.py::TestCaptchaController`（含端到端 `GET /captchaImage`）

---

## 23. 验证码比对：`equalsIgnoreCase` → 小写比较 `[无影响]`

**Java 原行为**

```java
if (CommonUtil.isNotBlank(code)) {
    String verifyKey = Constants.CAPTCHA_CODE_KEY + uuid;   // 无保护拼接
    String captcha = redisCache.getCacheObject(verifyKey);
    redisCache.deleteObject(verifyKey);                     // 先删，后比
    if (captcha == null) { ... throw new CaptchaExpireException(); }
    if (!code.equalsIgnoreCase(captcha)) { ... throw new CaptchaException(); }
}
```

`String#equalsIgnoreCase` 是**逐字符** `toUpperCase` / `toLowerCase` 后比较。

**Python 实现**
`SysLoginService.validate_captcha()` 中：

```python
if code.lower() != str(captcha).lower():
```

在验证码字符集上二者完全等价：math 生产者只产生 `0-9` 与 `* / + -`，char 生产者只产生
`abcde2345678gfynmnpwx` 中的 ASCII 字母与数字。这些字符的 `.lower()` 都是单字符映射。

**推广前要注意**
`str.lower()` 是完整 Unicode 映射，极少数码位会**改变长度**（如 `'İ'.lower()` 变成 2 个字符）。
若将来把验证码字符集换成含此类字符的语言包，应改用 `str.casefold()` 或对字符集做白名单校验。

**另外三条一起对齐了的行为**

- `code` 为 `null` / 空串 / **纯空白** → 整段校验直接返回，既不查 Redis 也不删 key
  （`CommonUtil.isNotBlank`）。也就是说**关掉验证码的方式是不传 `code`**，而不是传某个特殊值。
- `uuid` 为 `null` 时 Redis key 是字面量 `captcha_codes:null`（Java 字符串拼接语义），
  Python 同样如此 —— 这个 key 永远不存在，所以表现为「验证码已失效」。
- key **在比对之前就删**，一次失败即作废，重试必须重新取图。

**回归用例**
`tests/test_login_service.py::TestLoginCaptcha`（8 例）

---

## 24. `/login` / `/getInfo` / `/getRouters` 的响应差异 `[需注意]`

本节只记录**与 Java 有差异**的部分。三个端点的业务逻辑是逐行对应的，
包括容易误读的一点：**密码强度不合格时不消耗验证码、也不写 `sys_logininfor`** ——
这是 Java 的既有行为（`checkPassword` 在 `SysLoginController` 里、先于 `SysLoginService`），
不是迁移缺陷。

### 24.1 `roles` / `permissions` 由无序变成有序 `[无影响]`

**Java 原行为**
`SysPermissionService` 返回 `HashSet<String>`，Jackson 按迭代顺序输出 —— **顺序不确定**，
同一个用户两次请求的数组顺序可能不同。

**Python 实现**
`sorted(...)` 后输出。JSON 仍是字符串数组，长度与内容完全一致，只是顺序稳定。
不存在能依赖 Java 顺序的客户端（无顺序可依赖）。

**回归用例**
`tests/test_login_controller.py::TestGetInfo::test_a_regular_user_gets_sorted_lists`

### 24.2 请求体缺失 / 不是合法 JSON 时的提示文案不同 `[无影响]`

两侧**都是 HTTP 200 + `{"code":500,...}`**，只是 `msg` 内容不同：

| 场景 | Java | Python |
|---|---|---|
| 完全不带请求体 | `Required request body is missing: public com.ruoyi.common.core.domain.AjaxResult ...` | `body Field required` |
| 请求体不是 JSON | `JSON parse error: ...` | `JSON decode error` |
| 请求体是数组/字符串 | `Cannot deserialize value of type ... from Array value` | `Input should be a valid dictionary or object ...` |

没有任何客户端解析这段文案（前端只看 `code`），因此不去仿写 Spring 的措辞。

### 24.3 不带 `Content-Type` 的请求体：Java 拒绝，Python 接受 `[需注意]`

**Java 原行为**
`@RequestBody` 经 `MappingJackson2HttpMessageConverter` 处理，只认 `application/json` 与
`application/*+json`。请求头里**没有** `Content-Type` 时 Spring 按 `application/octet-stream`
处理 → `HttpMediaTypeNotSupportedException`（415）→ `GlobalExceptionHandler` 里没有对应
handler，落到 `@ExceptionHandler(Exception.class)` → **HTTP 200 + `{"code":500,
"msg":"Content type 'application/octet-stream' not supported"}`**。

**Python 实现**
FastAPI 在没有 `Content-Type` 时仍按 JSON 解析请求体，因此这种请求会**正常登录成功**。

**影响面**
这是「接受的请求集合变大」而不是「原有请求行为改变」：只要客户端带 `Content-Type: application/json`
（所有浏览器与 axios 默认如此），两侧完全一致。没有添加 Content-Type 白名单校验 ——
那会变成比 Java 更严格的拒绝逻辑，而真实前端无法从任何文档推断出这一约束。

**建议**
若将来需要严格等价，在 `login()` 入口检查 `request.headers["content-type"]`，
不匹配时返回 `AjaxResult.error_message("Content type '...' not supported")`。

---

## 25. `/system/user` 切片（Phase 3.5 / 3.6）`[需注意]`

> 本节覆盖 `SysUserController` + `SysUserServiceImpl` + `SysUserMapper` 这一条竖切面。
> 两条**真实缺陷**（§25.3 / §25.4）在 595 条非 E2E 用例里一条都没暴露 —— 它们只在
> `tests/test_e2e_sys_user.py` 的 28 条端到端用例跑起来后才现形。原因很直接：那些单元用例
> 用假实现替掉了 `session_scope` 与 `get_redis_cache`，而这两个缺陷都长在**假实现的边界之外**
> （一个是 Starlette 的异常路由，一个是 FastAPI 的参数反射）。

§0 表里的第 25–28 条分别对应本节 25.1、25.2、25.3–25.4、25.5。

### 25.1 三个 Excel 端点未迁移 `[需注意]`

**Java 原行为**
`SysUserController` 共 19 个映射，其中三个返回 xlsx 二进制流：

| 端点 | 权限 | Java 返回 |
|---|---|---|
| `GET /system/user/export` | `system:user:export` | `util.exportExcel(list, "用户数据")` 写出的 xlsx |
| `GET /system/user/importTemplate` | 仅登录 | 空模板 xlsx |
| `POST /system/user/importData` | `system:user:import` | `{"code":200,"msg":"<importUser 的汇总文案>"}` |

**Python 实现**
三条路由**都没有注册**。这不是"少写几行"：

- `export` / `importTemplate` 需要 `ExcelUtil`（Apache POI 的 `SXSSFWorkbook`、`@Excel` 注解、
  字典翻译、列宽与合并单元格）；
- `importData` 还要 `SysUserService#importUser`，而它读
  `ISysConfigService.selectConfigByKey("sys.user.initPassword")` —— `sys_config` 模块尚未迁移。

**影响与规避**
差异只在**已认证**的请求上显现：

| 调用方 | Java | Python |
|---|---|---|
| 未登录 / token 失效 | HTTP 200 + `code 401` | HTTP 200 + `code 401`（一样） |
| 已登录、权限足够 | HTTP 200 + xlsx 二进制流 | **HTTP 200 + `code 500`** |

因为安全过滤器在路由之前执行（见 §2&3 与 §18），未登录时两侧都先返回 401；
已登录时请求会落到 `GET /system/user/{user_id}` 那条路由上，`"export"` 转 `Long` 失败，
于是是 200+`code 500` 而不是 404（更正：Phase 3.9 实测，详见 §28.1）。
前端“导出用户”按钮（已登录）会拿到 500。
其余 16 个端点不受影响。补的顺序应为：`ExcelUtil` → `sys_config` → `importUser` → 挂路由。

**回归用例**
`tests/test_sys_user_controller.py::TestRoutesOverHttp::test_the_three_excel_endpoints_are_deliberately_absent`
—— 断言路由表里**没有**这三条。这既是缺口备忘，也是防回退阀：在 `ExcelUtil` 真的迁过来之前
不要挂占位路由，否则"导出"会从 404 变成 500。

### 25.2 `@Log` 已全量生效（本条已关闭）`[无影响]`

**Java 原行为**
`add` / `edit` / `remove` / `resetPwd` / `changeStatus` / `export` / `importData` 都带
`@Log(title = "用户管理", businessType = ...)`，由 `LogAspect` 在方法返回后**异步**写一条
`sys_oper_log`（`AsyncManager`）。

**Python 实现**
`app/framework/aspectj/log_aspect.py`（528 行）是 `LogAspect` 的逐方法转写：同样的
"记起始时间 / 返回后 / 抛异常后"三段，同样的
`AsyncManager.me().execute(record_oper(oper_log))` 异步落库，同样的 2000 字截断。
用户管理的 7 个写操作（`export` / `importData` / `add` / `edit` / `remove` /
`resetPwd` / `changeStatus`）全部带 `@log(...)`。

装饰器顺序等价于 Spring 的 advisor 顺序：`@PreAuthorize` 在外、`@log` 在最内，
所以**被 403 拒绝的请求不留审计记录** —— Java 的 `@Before` 通知同样要等授权通过才执行。

**影响与规避**
无。本条此前写的是"`LogAspect` 随 `sys_oper_log` 模块一起待迁移，因此这些操作不会留下
审计记录"——**该结论已作废**（见 §42.9；§26.2 起的 12 处"同 §25.2"一并失效）。
仍然成立的相关限制只有一个：审计写在业务之后，**业务回滚时审计照样留下**
（§28.3 的请求级事务未复刻）。

### 25.3 曾缺失 `@ExceptionHandler(RuntimeException.class)`（已修复）`[需注意]`

**Java 原行为**
`GlobalExceptionHandler` 最后一个是：

```java
@ExceptionHandler(RuntimeException.class)
public AjaxResult handleRuntimeException(RuntimeException e, HttpServletRequest request) {
    String requestURI = request.getRequestURI();
    log.error("请求地址'{}',发生未知异常.", requestURI, e);
    return AjaxResult.error(e.getMessage());
}
```

它捕的是 `RuoYiBaseException`（`UserException` / `CaptchaException` ...）、`CustomException`
以及任何其他未受控错误 —— 全部翻成 **HTTP 200 + `code 500`**。

**Python 早先的实现（缺陷）**
`exception_handlers.py` 当时只注册了 `ServiceException` / `AccessDeniedException` /
`DemoModeException` / `RequestValidationError` / `StarletteHTTPException` / `Exception`。
漏掉 `RuntimeException` 的后果比“少一个 handler”严重：Starlette 把 `Exception` 的处理器挂在
`ServerErrorMiddleware` 上，而它在**发完响应之后还会再把异常抛回去**。于是：

- `POST /login` 密码错误 → `UserPasswordNotMatchException` 直接冒到客户端（生产上是连接被重置）；
- `PUT /system/user/resetPwd` 操作超管 → `CustomException("不允许操作超级管理员用户")` 同样冒出去；
- 两种场景客户端都**拿不到** `{"code":500,"msg":...}`。

**修复**
新增一个注册在 `ExceptionMiddleware` 上的 `RuntimeError` 处理器。选择 `RuntimeError` 而不是
`Exception` 是关键：`ExceptionMiddleware._lookup_exception_handler` 沿 `type(exc).__mro__` 找
**第一个**命中的注册项，所以 `ServiceException` 等子类仍走各自的专用 handler，只有真正的
"未知异常"落到底部 —— 与 Spring 的 `@ExceptionHandler` 选择规则一致。

**为什么单元用例没发现**
`tests/test_login_service.py` 直调 Service，`pytest.raises(UserPasswordNotMatchException)`
正是它预期的行为。缺陷在"异常怎么变成 HTTP 响应"这一层，只有真的过一遍 ASGI 中间件才看得见。

**回归用例**
`tests/test_e2e_sys_user.py::TestLogin::test_a_wrong_password_is_a_500_envelope_with_http_200`

### 25.4 `@PreAuthorize` 装饰器曾把 4 个写接口的 JSON body 变成 query 参数（已修复）`[需注意]`

**症状**
`POST /system/user`、`PUT /system/user`、`PUT /system/user/resetPwd`、
`PUT /system/user/changeStatus` 收到合法 JSON 后一律回
`{"code":500,"msg":"user Field required"}`，日志里是
`[参数校验失败] 请求地址'/system/user', user Field required`。

**根因（PEP 563 + 装饰器 + FastAPI 反射）**
1. 这些模块都写了 `from __future__ import annotations`，所以 `__annotations__` 里存的是**字符串**
   （`"SysUser"`）；
2. `functools.wraps` 把 `__annotations__` 与 `__wrapped__` 都复制到包装函数上；
3. FastAPI 的 `get_typed_signature(call)` 用 `inspect.signature(call)` 拿到**原函数**的（字符串）
   注解，却用 `call.__globals__` —— 即**包装函数所在模块**（`framework/web/service/`）—— 去求值；
4. 那里没有 `SysUser`，求值失败后注解留成 `ForwardRef`，FastAPI 就把它**静默降级成 query 参数**。

于是函数体里的 `user` 永远是 `SysUser()`（全 `None`），JSON body 被完全忽略。
最危险的地方是它**不报错**：不挂装饰器的 `PUT /system/user/bindUky` 一切正常，而
`@pre_authorize_permi("system:user:query")` 的 `get_info` 因为本来就不带参数也看不出异常。

**修复**
`permission_service._keep_target_signature(wrapper, func)`：用
`typing.get_type_hints(func, include_extras=True)` 把字符串注解**真正求值**，再用
`inspect.signature(func).replace(...)` 写回 `wrapper.__signature__`。FastAPI 优先读
`__signature__`，因此看到的是已解析的类型。这相当于恢复 Spring AOP 代理对参数注解的透明性。

**将来的约束**
任何新的 FastAPI 依赖/装饰器（限流、幂等、`@Log` ...）都必须调这个 helper，否则会重现同一个
“参数静默变 query”的缺陷。对应的防护是：§25.4 提到的四个端点，在端到端用例里**各至少有一条**
携带真实 JSON body 的写用例。

**回归用例**
`tests/test_e2e_sys_user.py::TestWrite`（9 条，全部通过 JSON body 驱动）

### 25.5 varchar 排序列接受 JSON 数字（`JavaString`）`[无影响]`

**Java 原行为**
`sys_dept.order_num`、`sys_role.role_sort`、`sys_post.post_sort`、`sys_menu.order_num`
在库里是 `varchar`，在实体上是 `String`。Jackson 的 `StringDeserializer` 默认
`CoercionAction.TryConvert`，所以 `{"postSort": 1}` 会解成 `"1"`，布尔解成 `"true"`/`"false"`。

**为什么重要**
RuoYi 前端的排序列用 `el-input-number` 绑定，提交的确实是 **JSON 数字**。pydantic v2 默认
**拒绝** `int -> str`，不处理的话同一份请求会从 Java 的 200 变成 Python 的 `code 500`
（“Input should be a valid string"）—— 而这两列恰好又都在必填表单里。

**Python 实现**
`app/common/core/domain/domain_model.py` 新增
`JavaString = Annotated[Optional[str], BeforeValidator(_coerce_to_java_string)]`，应用到上述四个字段。
只做 Jackson 会做的事：`int`/`float` → `str()`，`bool` → `"true"`/`"false"`，`None` 与字符串原样通过。
`dict` / `list` 仍然被拒（Jackson 对它们也会抛 `MismatchedInputException`）。

**回归用例**
`tests/test_domain_serialization.py::TestJacksonScalarCoercion`（4 条，含 `postSort` 的 camelCase 入口）

### 25.6 PageHelper `orderBy` 与语句自带 `ORDER BY` `[需注意]`

**Java 原行为**
`BaseController.startPage()` 把 `orderByColumn` + `isAsc` 拼成 `orderBy` 交给
`PageHelper.startPage(pageNum, pageSize, orderBy)`。本项目的 Mapper XML 里有一部分语句
**自己**带 `order by`（如 `selectRoleList` 的 `order by r.role_sort`）。

**Python 实现**
`page_helper.select_page()` 追加 `ORDER BY` 之前先看语句里是否已有 —— 有就**忽略请求排序**并打一条
DEBUG 日志，避免拼出两个 `ORDER BY`（MySQL 直接语法错误）。

**这意味着什么**
只有当调用方同时传 `orderByColumn` **且**语句自带 `ORDER BY` 时才会有差异：
若 PageHelper 是"替换"掉的，则 Java 按客户端列排序、Python 按语句列排序；
若 PageHelper 是"追加"，则 Java 那边本来就是一个语法错误。两者都是客户端点了表头才可能触发，
不影响默认请求。**未实机核对**，见待确认清单第 7 条。

### 25.7 已逐条核对为等价、不要“顺手修好”`[无影响]`

下面四处看起来像 bug，实际两侧一模一样，改掉任何一处都会造成真实差异：

| 位置 | 写法 | 为什么等价 |
|---|---|---|
| `insertUserRole` / `insertUserPost` | `if (StringUtils.isNotEmpty(roleIds))` ↔ `if rows:` | `isNotEmpty(Object[])` 就是“非 null 且长度 > 0” |
| 密码文案 | `add`/`resetPwd` 的提示**无**感叹号，`SysLoginController` 那句**有** | 两处 Java 源码确实不同 |
| `getInfo` 的角色过滤 | 用**被查看人**的 `userId` 判超管 | 看普通人时隐藏 admin 角色，防止提权 |
| `bindUky` 的“已绑定” | 只看 `selectUserList(...)[0]` | 同一实体标识绑到自己头上是允许的 |

### 25.8 `GET /system/user` 与 `/system/user/` `[无影响]`

Java 的 `@GetMapping(value = {"/", "/{userId}"})` 在 Spring 5.3 的
`useTrailingSlashMatch` 下同时接受两种写法。FastAPI 默认会把不带斜杠的形式 307 重定向，
为让“不跟随重定向”的客户端也直接拿到 200，同一个处理函数挂了**两条路由**。
副作用：OpenAPI 文档里会看到两个路径，而 Spring 那边也导出两个 mapping，一致。

---

## 26. `/system/post` 切片（Phase 3.7）`[需注意]`

> 本节覆盖 `SysPostController` + `SysPostServiceImpl` + `SysPostMapper` 这一条竖切面。
> 对照表见 [MAPPING_SYS_POST.md](MAPPING_SYS_POST.md)。
>
> §0 表里的第 29–31 条分别对应本节 26.1、26.2、26.3。

### 26.1 `export` 端点未迁移 `[需注意]`

**Java 原行为**
`SysPostController` 共 7 个映射，其中 `GET /system/post/export`（权限 `system:post:export`）
调 `util.exportExcel(postService.selectPostList(post), "岗位数据")`，输出 xlsx 二进制流。

**Python 实现**
路由**没有注册**。原因与 §25.1 同源：`ExcelUtil`（Apache POI 的 `SXSSFWorkbook`、
`@Excel` 注解、字典翻译、列宽与合并单元格）尚未迁移。

**影响与规避**

| 调用方 | Java | Python |
|---|---|---|
| 未登录 / token 失效 | HTTP 200 + `code 401` | HTTP 200 + `code 401`（一样） |
| 已登录、权限足够 | HTTP 200 + xlsx 二进制流 | **HTTP 200 + `code 500`** |

安全过滤器在路由之前执行（见 §2&3 与 §18），未登录时两侧都先返回 401；
已登录时请求会落到 `GET /system/post/{post_id}` 上，`"export"` 转 `Long` 失败，
因此是 200+`code 500`（更正：Phase 3.9 实测，详见 §28.1）。
其余 6 个端点不受影响。

**回归用例**
`tests/test_sys_post_controller.py::TestRouteTable::test_export_is_not_registered`
—— 断言路由表里**没有**这条。在 `ExcelUtil` 真的迁过来之前不要挂占位路由，
否则“导出”会从 404 变成 500。

### 26.2 `@Log` 未迁移 → 岗位管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，岗位管理的 4 处 `@Log` 全部生效。
> 下面"不会留下审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

**Java 原行为**
`add` / `edit` / `remove` / `export` 带 `@Log(title = "岗位管理", businessType = ...)`，
由 `LogAspect` 在方法返回后**异步**写一条 `sys_oper_log`。

**Python 实现**
`LogAspect` 随 `sys_oper_log` 模块一起待迁移（同 §25.2），因此这些操作**不会**留下审计记录。

**影响与规避**
接口返回、数据库业务表全部一致，客户端感知不到（多语句方法的事务边界见 §28.3）；唯一可见后果是
`/monitor/operlog` 页面查不到岗位管理的操作记录。

### 26.3 新增 `bean_validation` 桥接 `@NotBlank` / `@Size` `[无影响]`

**Java 原行为**
`SysPost` 的 getter 上有**生效的**校验注解（`SysUser` 的那组在源码里被注释掉了，两者不同）：

| 字段 | 注解 | 失败文案 |
|---|---|---|
| `postCode` | `@NotBlank` + `@Size(max = 64)` | `岗位编码不能为空` / `岗位编码长度不能超过64个字符` |
| `postName` | `@NotBlank` + `@Size(max = 50)` | `岗位名称不能为空` / `岗位名称长度不能超过50个字符` |
| `postSort` | `@NotBlank`（**无** `@Size`） | `显示顺序不能为空` |

`add` / `edit` 上的 `@Validated @RequestBody` 触发 Hibernate Validator，失败后
`GlobalExceptionHandler#handleMethodArgumentNotValidException` 回
`AjaxResult.error(fieldError.getDefaultMessage())` —— 即 **HTTP 200 + `code 500` + 注解里的中文**。

**Python 实现**
新增 `app/common/utils/bean_validation.py`（`NotBlank` / `Size` / `validate`）+
实体旁的 `POST_CONSTRAINTS`（同文件、同顺序）。

不用 pydantic `Field(...)` 的原因只有一个：pydantic 的校验消息是英文的
（`String should have at most 50 characters`），而 Java 回的是注解里的中文，
逐字对齐只能自己带文案。也不能用 `RequestValidationError` 的默认处理 ——
它同样看不到注解文案。

**顺序：校验必须先于 `@PreAuthorize`**
Spring MVC 先解析参数（`resolveArgument` → `validateIfApplicable`），
再在 CGLIB 代理的 `doInvoke` 里触发 `@PreAuthorize`：

```
安全过滤器链(401) -> 路由 -> 反序列化+校验(500) -> @PreAuthorize(403) -> 方法体
```

Python 侧 `pre_authorize_permi` 是装饰器，检查天然在函数体之前，所以校验**不能**
写成函数体的第一条语句，否则会变成“没权限的人先撞 403”。实现上把校验做成 FastAPI 的
`Depends`（`ValidPost`），依赖在端点函数体之前解析，正好补回 Spring 的位置。

| 场景 | Spring | 函数体第一行（错） | `Depends`（对） |
|---|---|---|---|
| 未登录 + 缺 `postName` | `500 岗位名称不能为空` | `403` | **`500 岗位名称不能为空`** |
| 未登录 + 合法 body | `403` | `403` | `403` |

代价：`pre_authorize_permi` 必须保留原函数签名（`_keep_target_signature`），
否则 `Annotated[SysPost, Depends(...)]` 会在反射时退化成 query 参数（§25.4 的同一个坑）。

**将来的约束**
`SysDept` / `SysMenu` / `SysRole` 的校验注解同样是**生效的**，迁这三个模块时应直接复用
`bean_validation`，不要在端点里写 `if/return AjaxResult.error(...)` —— 那样异常会变成
“正常返回”，与 Java 的异常分支不等价（日志、后续拦截都不同）。

**回归用例**
`tests/test_sys_post_controller.py::TestValidationRunsBeforePermission`（10 条：
8 条是“未登录 + 非法 body”，断言 `code == 500` 而不是 `403`；另 2 条是对照组 ——
边界值合法时落到 `403`、查询端点不做校验）。

### 26.4 `selectPostVo` 不投影 `updateBy` / `updateTime` `[无影响]`

**Java 原行为**
`<sql id="selectPostVo">` 只 select 8 列，`resultMap="SysPostResult"` 里的
`update_by` / `update_time` 没有对应列源，因此**每一条岗位响应里这两个字段都是 `null`**。
`BaseEntity` 上没有 `@JsonInclude`，所以 Jackson 会输出 `"updateBy": null` 而不是省略。

**Python 实现**
`_POST_COLUMNS`（8 列）+ `_map_post` 原样照抄：未投影的字段保持 dataclass 默认值 `None`。

**为什么单独立一节**
它看起来像“Mapper 少写了两列”，很容易在“顺手补全”时被改掉。补全后前端会开始用
`updateBy` 展示“最后修改人”，而 Java 那边这一列永远是空 —— 这是真实的响应差异。

**回归用例**
`tests/test_sys_post_mapper.py::TestSingleRowQueries::test_update_by_and_update_time_are_never_selected`

---

## 27. `/system/dept` 切片（Phase 3.8）`[需注意]`

> 本节覆盖 `SysDeptController` + `SysDeptServiceImpl` + `SysDeptMapper` 这一条竖切面，
> 外加它第一次用到的 `TreeSelect` / `CommonUtil.isNull` / `@Email`。
> 对照表见 [MAPPING_SYS_DEPT.md](MAPPING_SYS_DEPT.md)。
>
> §0 表里的第 32–36 条分别对应本节 27.1–27.5。

### 27.1 `@DataScope` 对部门列表完全无效 `[需注意]`

**Java 原行为**
`SysDeptServiceImpl#selectDeptList` 挂着 `@DataScope(deptAlias = "d")`，切面会把拼好的
`AND (d.dept_id IN (...))` 写进 `dept.params["dataScope"]`，供 XML 里的
`${params.dataScope}` 引用。但 `SysDeptMapper.xml#selectDeptList` 那一行是**注释**：

```xml
<!-- 数据范围过滤 ${params.dataScope}-->
		order by d.parent_id, d.order_num
```

注释在 XML 解析前就被丢掉了，`${}` 根本不会被替换。**结论：部门列表从来不做数据权限过滤**，
任何登录用户（连 `getList` 这种没有 `@PreAuthorize` 的端点）都能拿到全量部门树。

**Python 实现**
`select_dept_list` 仍然调 `apply_data_scope(dept, "d")`（保持调用链一致），但 mapper 不读
`params["dataScope"]`，SQL 里也没有对应片段。

**为什么单独立一节**
这是最容易被“顺手修好”的地方：补上 `${params.dataScope}` 看起来是修正遗漏，实际是**新增
一个 Java 没有的过滤**，前端下拉框会突然少一批部门。要开这个特性必须先改需求。

**回归用例**
`tests/test_sys_dept_mapper.py::TestSelectDeptList::test_without_filters_only_the_soft_delete_guard`
（断言 WHERE 只有 `d.del_flag = '0'`），以及
`tests/test_sys_dept_controller.py::TestPermissions::test_five_endpoints_only_need_a_login`。

### 27.2 `@Log` 未迁移 → 部门管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，本控制器的 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

**Java 原行为**
`add` / `edit` / `remove` 带 `@Log(title = "部门管理", businessType = ...)`，由 `LogAspect`
异步写 `sys_oper_log`。

**Python 实现**
`LogAspect` 仍未迁移（同 §25.2 / §26.2），因此这三次操作不留审计记录。

**影响与规避**
接口返回、数据库业务表、`sub_code` / `tenant_id` 的联动结果全部一致；唯一可见后果是
`/monitor/operlog` 查不到部门变更。

### 27.3 `@Email` 是 Hibernate 正则的放宽版 `[需注意]`

**Java 原行为**
`SysDept#getEmail` 上有 `@Email(message = "邮箱格式不正确")`。Hibernate 的实现是
`Pattern.compile(".{0,64}@" + DOMAIN_PART_REGEX, CASE_INSENSITIVE)` 配 `matches()`：

* **本地部分完全不校验字符集**，`"a b@c.d"` 是通过的；
* `null` 与 `""` 都返回 `true`（`@Email` 不管空值，`@NotBlank` 才管）。

**Python 实现**
`app/common/utils/bean_validation.py` 的 `Email` + `_EMAIL_PATTERN`：

```python
r"^.{0,64}@[a-z0-9\-\u0080-\uffff]+(?:\.[a-z0-9\-\u0080-\uffff]+)*$"
```

本地部分逐字照抄；域名部分用“一个或多个字符类”代替 Hibernate 的
`[首字符][中间]{0,62}[尾字符]?`，因此有**两处放宽**：

| 输入 | Java | Python | 方向 |
|---|---|---|---|
| `a@-b.com`（域名标签以 `-` 开头） | 不通过 | **通过** | Python 更宽 |
| 单个标签超过 63 字符 | 不通过 | **通过** | Python 更宽 |
| `a b@c.d`（本地部分带空格） | 通过 | 通过 | 一致 |
| `null` / `""` | 通过 | 通过 | 一致 |

放宽方向是刻意的、也是可接受的：**Python 只可能多放过、不会多拒绝**，即不存在“Java 接受但
Python 报 500”的输入。反过来（Java 拒绝、Python 接受）只会让脏数据多一条，而
`varchar(50)` 列和前端表单都不会产生这种值。要收紧到逐字一致，把域名部分换成
Hibernate 的三段式正则即可，但收益是 0。

**回归用例**
`tests/test_sys_dept_controller.py::TestValidationRunsBeforePermission` 的
`test_the_lax_email_rule_matches_hibernate`（`"a b@c.d"` -> 403 而非 500）、
`test_a_blank_email_is_accepted`、`test_an_overlong_email_is_reported`。

### 27.4 `updateDept` 会把空 `phone` / `email` 写进库 `[需注意]`

**Java 原行为**
同一对字段，两条语句的 `<if>` 判据不同：

| 语句 | `phone` / `email` 的判据 | 传 `""` 时 |
|---|---|---|
| `insertDept` | `!= null and != ''` | **列不出现在 `insert` 里**，落库默认值 `NULL` |
| `updateDept` | 只有 `!= null` | 列出现在 `set` 里，**把已有值改成 `""`** |

后果：前端把联系电话清空后点保存，库里是空串而不是 `NULL`；再点新增同样的数据，库里却是
`NULL`。同一个字段因此有两种“空值”，查询里写 `phone is null` 会漏掉一批。

**Python 实现**
`_INSERT_DEPT_COLUMNS` 里这两项 `require_text=True`，`_UPDATE_DEPT_COLUMNS` 里是 `False`，
由同一张表驱动建 SQL —— 差异只在这一个布尔位上，不要“统一”。

**回归用例**
`tests/test_sys_dept_mapper.py`：`TestInsertDept::test_empty_strings_follow_each_column_rule`、
`TestUpdateDept::test_empty_phone_and_email_are_written_over`。

### 27.5 `del_flag` 过滤与 `select *` 的三处不对称 `[无影响]`

**Java 原行为**

| 语句 | 不对称之处 |
|---|---|
| `selectDeptById` | **不过滤** `del_flag` —— 已逻辑删除的部门也查得到 |
| `checkDeptNameUnique` | 同上：删除掉的部门仍会占用名字，新增同名报表“已存在” |
| `selectChildrenDeptById` | 写的是 `select *`，MyBatis 的 `autoMappingBehavior=PARTIAL` 把 `remark` / `update_by` / `update_time` 也陪进来了 |

**Python 实现**
`_SELECT_DEPT_BY_ID` / `_CHECK_DEPT_NAME_UNIQUE` 的 WHERE 里没有 `del_flag`；
`select_children_dept_by_id` 映射时用 `_DEPT_SELECT_ALL_COLUMNS`（比 `_DEPT_COLUMNS` 多三列）。

**为什么不能“修”**
`insertDept` 要靠 `selectDeptById` 读到**已被删除的父节点**才能算出 `tree_leavel`；
加上 `del_flag = '0'` 会让“在已删除的部门下建子部门”从“正常插入”变成 NPE。

**回归用例**
`tests/test_sys_dept_mapper.py::TestSelectDeptById::test_no_del_flag_filter`、
`TestSelectChildrenDeptById::test_select_star_maps_three_extra_columns`。

---

## 28. `/system/role` 切片（Phase 3.9）`[需注意]`

> 本节覆盖 `SysRoleController` + `SysRoleServiceImpl` + `SysRoleMapper` /
> `SysRoleMenuMapper` / `SysRoleDeptMapper` 这一条竖切面。
> 对照表见 [MAPPING_SYS_ROLE.md](MAPPING_SYS_ROLE.md)。
>
> §0 表里的第 37–43 条分别对应本节 28.1–28.7。

### 28.1 `export` 未迁移，且**不是** 404 `[需注意]`

**Java 原行为**
`SysRoleController#export` 用 `ExcelUtil<SysRole>` 把列表写成 xlsx 流，Content-Type 是
`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。

**Python 实现**
和 `/system/user/export`（§25.1）、`/system/post/export`（§26.1）、`/system/dept/export`
同属 `ExcelUtil` 缺口，**路由没有注册**。

**与另外三处的差别**
角色控制器注册了 `GET /system/role/{role_id}`，所以 `GET /system/role/export`
**不会**落到 404，而是被那条路由兜住：`"export"` 转 `Long` 失败 ->
`MethodArgumentTypeMismatchException` -> **HTTP 200 + `{"code":500,...}`**。

同样的情形也适用于另外三个模块（它们都注册了 `GET /{id}` 详情路由），
§25.1 / §26.1 原先写的“真实 404”已在本次修正为 500。

**客户端感知**
前端“导出角色”按钮当前拿到的是 500 而不是文件流。

**回归用例**
`tests/test_sys_role_controller.py::TestRouteTable::test_export_is_not_registered`（路由表阀）
与 `test_export_falls_into_the_path_variable`（500 行为阀）。

### 28.2 `@Log` 未迁移 → 角色管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，角色管理的 6 处 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

**Java 原行为**
`export` / `add` / `edit` / `dataScope` / `changeStatus` / `remove` 带
`@Log(title = "角色管理", businessType = ...)`，由 `LogAspect` 异步写 `sys_oper_log`。

**Python 实现**
`LogAspect` 仍未迁移（同 §25.2 / §26.2 / §27.2），因此这六次操作不留审计记录。

**影响与规避**
接口返回与业务表一致；唯一可见后果是 `/monitor/operlog` 查不到角色变更。
注意：`edit` 成功后**会**重写当前登录用户的 Redis 令牌（见 MAPPING_SYS_ROLE.md §2.5），
这是业务逻辑，与审计无关，不要因为“没日志”而怀疑它没生效。

### 28.3 `@Transactional` 未复刻：多语句方法不再原子 `[需注意]`

这是**整个迁移**层面上最值得知道的一条，不止角色模块。

**Java 原行为**
`SysRoleServiceImpl` 上四个方法带 `@Transactional`：

| 方法 | 语句序列 |
|---|---|
| `insertRole` | `insert sys_role` -> `delete/insert sys_role_menu` -> `delete/insert sys_role_dept` |
| `updateRole` | `update sys_role` -> `delete sys_role_menu` -> `insert sys_role_menu` |
| `authDataScope` | `update sys_role`（只改 data_scope）-> `delete sys_role_dept` -> `insert sys_role_dept` |
| `deleteRoleByIds` | `delete sys_role_menu` -> `delete sys_role_dept` -> `update sys_role set del_flag` |

任何一条抛异常，整批回滚。

**Python 实现**
每个 Mapper 方法自己 `with session_scope()`（开连接 -> 执行 -> 提交 -> 关闭），
所以上面四组语句是**逐条提交**的，没有跨方法的回滚点。

**具体后果**

| 失败点 | Java | Python |
|---|---|---|
| `insertRole` 里 `insertRoleMenu` 抛错（`menuIds` 为 `null` 的 NPE） | 角色行不存在 | **角色已入库、菜单关联为空** |
| `updateRole` 里 `insertRoleMenu` 抛错 | 菜单关联不变 | **菜单已被删空**（角色没权限了） |
| `deleteRoleByIds` 中途数据库报错 | 一行都不删 | 可能只删了部分关联 |

**为什么没现在修**
要真正复刻必须把 `session` 从 Mapper 签名里透传上去（或引入 `ContextVar` 级的
“当前事务”），这会改动所有已迁移模块的 97 条 XML 对应物 —— 属于结构性改动，
不在“行为等价 1:1”的范围内。当前选取的是“与 Java 语义最接近但不具备原子性”的折中。

**规避方式**
1. 前端保存角色后若拿到 500，**重新查询一次角色详情**再重试，不要直接以为“什么也没发生”；
2. 运维修复这类半成品数据时，重点查 `sys_role_menu` 是否有孤儿 `role_id`；
3. 生产上若要彻底解决，建议先迁 `LogAspect` 时一并引入“请求级事务`，理由相同（都是切面层）。

### 28.4 基本类型布尔让两个 `*_check_strictly` 列**总是**写库 `[需注意]`

**Java 原行为**
`SysRole` 的 `menuCheckStrictly` / `deptCheckStrictly` 是 **primitive `boolean`**，
XML 里却写着：

```xml
<if test="menuCheckStrictly != null">menu_check_strictly,</if>
```

OGNL 把 `boolean` 装箱成 `Boolean.TRUE/FALSE`，**永远不为 null** —— 这个 `<if>` 是死条件。
所以：

* `insertRole` 一定会写这两列（客户端不传就是 `0`）；
* `updateRole` 一定会更新这两列 —— **只改状态（`changeStatus`）也会把它们重置成 `0`**。

**Python 实现**
`insert_role` / `update_role` 无条件带上这两列，值取 `1 if role.menu_check_strictly else 0`。

**为什么不能“优化”成“传了才写”**
那会让“菜单未严格校验”的旧角色在下次改状态时**保留** `1`，而 Java 会把它重置成 `0`。
两边的授权树勾选行为不一样（`1` = 父子联动，`0` = 独立勾选），是真实的业务差异。

**回归用例**
`tests/test_sys_role_mapper.py`：`TestInsertRole::test_minimal_role_still_writes_the_two_boolean_columns`、
`TestUpdateRole::test_the_two_boolean_columns_are_always_updated`；
`tests/test_sys_role_service.py::TestUpdateRole::test_update_role_status_does_not_touch_the_menu_table`
（只改状态也只会走 `updateRole`，两列照样被重置）。

### 28.5 `updateRole` 的 `remark` 传空串会**清列** `[需注意]`

**Java 原行为**
`updateRole` 的 `<set>` 里，只有 `remark` 的判据是 `!= null`：

| 字段 | 判据 | 传 `""` 时 |
|---|---|---|
| `role_name` / `role_key` / `role_sort` / `data_scope` / `status` / `update_by` | `!= null and != ''` | 不覆盖旧值 |
| `remark` | 只有 `!= null` | **把旧备注改成空串** |

另外 `insertRole` 的 `remark` 是 `!= null and != ''`（空串丢列），于是同一个字段在
新增和修改里对空串的处理**不一致** —— 与 §27.4 的 `phone`/`email` 同源，照抄。

**Python 实现**
`update_role` 里 `remark` 单独用 `if role.remark is not None`，其余走 `_text()`；
`insert_role` 里 `remark` 走 `_text()`。**不要统一**。

### 28.6 `roleKey` 的分割不逐段 trim `[无影响]`

**Java 原行为**
`SysRoleServiceImpl#selectRoleList` 里：

```java
for (String roleKey : role.getRoleKey().trim().split(",")) { role.setRoleKey(roleKey); ... }
```

`trim()` 作用在**整串**上，`split` 不丢段内空格。于是 `" a , b "` 得到 `{"a ", " b"}` ——
不是 `{"a", "b"}`。

**Python 实现**
`role.role_key.strip().split(",")`，逐段**不**做 `strip()`。
表面看像少了一行 “防御式编程”，实际是唯一正确的写法：补上逐段 trim 会多匹配到角色
（`role_key = " b"` 的脏数据），返回的列表就与 Java 不同。

**客户端感知**
前端从不发送带空格的 `role_key`，所以正常链路无差异。

**回归用例**
`tests/test_sys_role_service.py::TestRolePermissionKeys::test_role_keys_are_split_on_commas`
与 `TestRolePermissionKeys::test_a_fully_trimmed_key_is_split_cleanly`。

### 28.7 `deleteRoleById` 没有超管/已分配拦截 `[无影响]`

**Java 原行为**
`ISysRoleService#deleteRoleById(Long)` 的实现是“删两个关联表 + 删角色行”，但**不**调
`checkRoleAllowed`，也不查 `countUserRoleByRoleId`。两道拦截只在 `deleteRoleByIds` 里。

**Python 实现**
`delete_role_by_id` 同样先删 `sys_role_menu` / `sys_role_dept` 再软删角色行，
并**同样没有**两道闸（与 Java 的前置条件一致）。

**当前是否可达**
不可达 —— 控制器只有 `DELETE /system/role/{roleIds}`（走 `deleteRoleByIds`）。
但它在接口上存在，属于“看上去没用、改了可能出事”的一类，按迁移原则第 4 条保留。
如果有人“顺手补全”拦截，`delete_role_by_id` 就与 Java 的前置条件不一致了 —— 单测会变红。

**回归用例**
`tests/test_sys_role_service.py::TestDeleteRoleByIds::test_delete_role_by_id_has_no_guards`。

### 28.8 `GET /system/role/list` 曾漏了分页（**已修复**）`[需注意]`

**Java 原行为**
`SysRoleController#list` 第一行就是 `startPage()`，紧随其后的 `selectRoleList` 是 PageHelper
的拦截对象 —— 先 count、再把 `LIMIT` 拼到语句末尾。

**曾有缺陷（Phase 3.9 遗留）**
`sys_role_mapper.select_role_list` 直接 `session.execute(...).all()`，**没有** `take_page()`：

1. `GET /system/role/list` 返回**全表**，`total` 由 `len(rows)` 算出 —— 前端分页器显示
   “共 N 条”，实际一次全给了；
2. 更隐蔽的是 `start_page()` 写进 `ContextVar` 的分页参数没人消费，会在同一请求内
   泄漏给**下一条** select。

对比：`sys_user_mapper.select_user_list` 与 `sys_post_mapper.select_post_list` 一直都分页，
只有角色漏了。

**现在**
与那两处一致：`take_page()` + `select_page(count_sql, data_sql, params, page)`，
count 同样包成 `select count(0) from (...) table_count`。
投影列走写死的 `_ROLE_COLUMNS`（`select_page` 只回 row，取不到 `result.keys()`）。

**顺带核对过、确认无缺口的**
`SysDeptController#list` 返回的是 `AjaxResult`（**不是** `TableDataInfo`），Java 侧根本
没有 `startPage()` —— 所以部门列表不分页是正确的，不要去“补”。

**顺带修好的测试隔离缺陷**
`tests/test_page_helper.py` 的 `use_query()` 直接改写模块属性 `page_helper.get_request`
且**不还原**，而 `ContextVar` 在整个 session 内共享 —— 于是它之后的每个 `start_page()`
都会读到那个假请求（`pageNum=2`）。现在 autouse fixture 用 `monkeypatch` 还原，
用例不再互相污染。

**回归用例**
`tests/test_sys_role_mapper.py::TestSelectRoleList::test_after_start_page_the_count_wraps_the_statement`、
`::test_the_paging_applies_even_though_the_statement_has_its_own_order_by`。

---

## 29. `/system/menu` 切片（Phase 3.10）`[需注意]`

> 本节覆盖 `SysMenuController` + `SysMenuServiceImpl` + `SysMenuMapper` 这一条竖切面。
> 对照表见 [MAPPING_SYS_MENU.md](MAPPING_SYS_MENU.md)。
>
> §0 表里的第 44–52 条分别对应本节 29.1–29.9。

### 29.1 菜单**没有** `export`，而且 Java 也没有 `[无影响]`

**Java 原行为**
`SysMenuController` 只有 7 个映射，**没有** `export` 方法 —— 用户/岗位/部门/角色都有，
菜单没有（菜单是树形数据，导出没有意义）。

**Python 实现**
路由表里也没有 `/system/menu/export`。请求 `GET /system/menu/export` 会被
`GET /system/menu/{menu_id}` 兜住，`"export"` 转 `int` 失败 → **HTTP 200 + `{"code":500,...}`**。

**与其它四个模块的区别**
那四个的 `export` 是“**未迁移**”（`ExcelUtil` 缺口，见 §25.1 / §26.1 / §28.1）；
菜单这个是“**本来就不存在**”。两者客户端看到的都是 500，但原因不同 ——
即使将来把 `ExcelUtil` 补上，**也不应该**给菜单加导出端点。

**回归用例**
`tests/test_sys_menu_controller.py::TestRouteTable::test_the_seven_paths_are_registered`
与 `TestServerErrors::test_the_export_style_404_does_not_exist_here`。

### 29.2 `@Log` 未迁移 → 菜单管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，菜单管理的 3 处 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

**Java 原行为**
`add` / `edit` / `remove` 带 `@Log(title = "菜单管理", businessType = ...)`，由 `LogAspect`
异步写 `sys_oper_log`。

**Python 实现**
`LogAspect` 仍未迁移（同 §25.2 / §26.2 / §27.2 / §28.2），因此这三次操作不留审计记录。

**影响与规避**
接口返回与业务表一致；唯一可见后果是 `/monitor/operlog` 查不到菜单变更。
菜单改动是**权限层**的变更，比角色改动还敏感，生产上建议暂时靠数据库审计记录
（`update_time` / `update_by` 能看出“谁在什么时候改的”）。

### 29.3 `insertMenu` **不回写** `menuId` `[无影响]`

**Java 原行为**
`SysMenuMapper.xml` 的 `<insert id="insertMenu">` 是全项目**唯一一个没有**
`useGeneratedKeys="true" keyProperty="menuId"` 的插入语句。所以：

```java
menuService.insertMenu(menu);      // 返回 1
menu.getMenuId();                  // 仍然是入参里的值（新增时是 null）
```

**Python 实现**
`insert_menu` 只 `return session.execute(...).rowcount or 0`，**不** `result.lastrowid`
回写 `menu.menu_id`。

**为什么不能“补全”**
补上之后，`add` 返回的 `AjaxResult` 看不出差别（它只带 `code`/`msg`），
但任何“插入后拿 id 继续写子表”的代码会因为 `None` → 真实 id 而改变行为。
当前 Java 没有这种代码，所以是**等价**的；补上就不再等价了。

**回归用例**
`tests/test_sys_menu_mapper.py::TestInsertMenu::test_no_generated_key_is_written_back`。

### 29.4 `updateMenu` 的 4 个字段传空串会**清列** `[需注意]`

**Java 原行为**
`<set>` 里的判据分两类：

| 字段 | 判据 | 传 `""` 时 |
|---|---|---|
| `menu_name` / `order_num` / `path` / `is_frame` / `is_cache` / `menu_type` / `icon` / `remark` / `update_by` | `!= null and != ''` | 整列**跳过**，保留旧值 |
| `parent_id` | 只有 `!= null` | 写 `0` 是合法的 |
| `component` / `visible` / `status` / `perms` | **只有 `!= null`** | **把旧值改成空串** |
| `update_time` | 不在 `<if>` 里 | 恒为 `sysdate()` |

**客户端感知**
前端“菜单编辑”页把「组件路径」输入框清空 → 发 `component: ""` → 组件路径真的被清掉；
把「路由地址」清空 → 发 `path: ""` → **什么也没发生**（旧值还在）。
这是 Java 原样，不是 bug。

**Python 实现**
`_UPDATE_MENU_COLUMNS` 的第三列 `require_text` 区分两类，`update_menu` 里
`if require_text and value == "": continue`。**不要统一**。

**与 `insertMenu` 的不对称**
`insert_menu` 里 `component` 判的是 `!= null and != ''`（空串丢列，由 DDL 兜底），
`update_menu` 里只判 `!= null`。同一个字段在新增/修改里对空串的处理**不一致**，
与 §27.4 / §28.5 同源。

**回归用例**
`TestUpdateMenu::test_empty_string_clears_the_null_only_columns`
与 `test_empty_string_skips_the_other_columns`；
`TestInsertMenu::test_empty_strings_are_dropped_except_the_null_only_columns`。

### 29.5 `deleteMenuById` 是**物理删除** `[需注意]`

**Java 原行为**
`sys_menu` 表**没有** `del_flag` 列（`sys_role` / `sys_dept` 都有）。
`remove` 过了两道闸就直接：

```sql
delete from sys_menu where menu_id = #{menuId}
```

**Python 实现**
同一个 `delete`，**不是**软删。过了 `hasChildByMenuId` / `checkMenuExistRole`
两道闸之后数据不可恢复。

**两道闸的局限**
`hasChildByMenuId` 只查 `parent_id = ?` 的行数，**不区分菜单类型** ——
一个目录下只有按钮子节点也算“有子菜单”，禁止删除。这与前端“先删按钮再删菜单”的
操作顺序一致，不要“优化”成只看 `menu_type in ('M','C')`。

**运维注意**
误删只能从备份恢复；`sys_role_menu` 里的对应行**不会**被级联清理（MySQL 侧没有外键），
会留下孤儿关联。删菜单前先 `select count(1) from sys_role_menu where menu_id = ?`。

### 29.6 `menuCheckStrictly` 是 primitive → `<if>` 是**活条件** `[无影响]`

**Java 原行为**

```java
public List<Integer> selectMenuListByRoleId(@Param("roleId") Long roleId,
                                            @Param("menuCheckStrictly") boolean menuCheckStrictly);
```

```xml
<if test="menuCheckStrictly">
  and m.menu_id not in (select m.parent_id from sys_menu m ...)
</if>
```

形参是 **primitive `boolean`**，OGNL 拿到的是真值，所以这个 `<if>` **真的**在决定
SQL 拼不拼 —— 与 §28.4 里那两个 `Boolean` 包类型（死条件）**恰好相反**。

**Python 实现**
`select_menu_list_by_role_id(role_id, menu_check_strictly)`，第二个形参**没有默认值**；
`if menu_check_strictly:` 才追加那段 `not in`。

**为什么值得单独写一条**
两个同名字段（`SysRole.menuCheckStrictly` 与 mapper 的 `menuCheckStrictly` 形参）
语义完全不同。看到 §28.4 就以为“这里的 `<if>` 也是死的”，会把
`menu_check_strictly = 0` 的角色也剔掉子节点 —— 授权树会少勾一批菜单。

**回归用例**
`tests/test_sys_menu_mapper.py::TestSelectMenuListByRoleId`（严格 / 非严格两支）。

### 29.7 `treeselect` / `roleMenuTreeselect` **没有**权限点 `[无影响]`

**Java 原行为**
这两个方法上没有 `@PreAuthorize`，**只要求登录**。而 `list` 上有 `system:menu:list`。

**Python 实现**
照抄：`treeselect` / `role_menu_treeselect` 不加 `@pre_authorize_permi`。

**为什么不能“补齐”**
角色编辑页要画菜单树，`sys_role.list` 的权限点本来就是关掉的 ——
给树端点加 `system:menu:list` 会让所有能进角色管理、但没被授菜单列表权限的用户
看到空树，角色授权功能直接不可用。

**回归用例**
`tests/test_sys_menu_controller.py::TestPermissions::test_treeselect_has_no_permission_point`
与 `test_role_menu_treeselect_has_no_permission_point`（空权限集下应当调通）。

### 29.8 两条孤儿 statement 照留不删 `[无影响]`

**Java 原行为**
`SysMenuMapper.xml` 里有两条 statement 在 Java 侧永远走不到：

| statement | 为何走不到 |
|---|---|
| `selectMenuPerms` | 连 `where` 都没有（拉全表 `perms`）；`SysMenuMapper` 接口声明了，但**全项目无人调用** |
| `selectMenuPermsByRoleId` | `SysMenuMapper` 接口**没有**这个方法，`ISysMenuService` 也没有 |

**Python 实现**
两条都迁移了（`select_menu_perms` / `select_menu_perms_by_role_id`），并在注释里标明
“无 Java 对应” / “没有任何调用者”。服务层也多了一个对称包装
`select_menu_perms_by_role_id` —— 它**没有 Java 对应**，纯属多迁一层，不参与任何端点。

**为什么保留**
迁移原则第 4 条：不删除“看似无用”的 Java 代码。真实原因更实际 —— 上游 RuoYi
经常在下一个版本里把这类语句“接上”，提前删掉会让后续升级的 diff 变成“新增 + 冲突”。

**回归用例**
`tests/test_sys_menu_mapper.py::TestSelectMenuPerms`（断言两条语句照旧拼得出来）。

### 29.9 `component` 的 `@Size` 上限 200、文案写 255 `[无影响]`

**Java 原行为**

```java
@Size(min = 0, max = 200, message = "组件路径不能超过255个字符")
public String getComponent() { return component; }
```

上限是 **200**，提示文案写的是 **255**。

**Python 实现**
`MENU_CONSTRAINTS` 里 `Size("component", max=200, message="组件路径不能超过255个字符")`，
与 Java 逐字一致。

**为什么不能“顺手改成 255”**
文案只是描述，限制才是行为。改成 255 之后，201–255 字符的组件路径会从“被拒绝（500 +
提示文案）”变成“保存成功”，是一条真实的功能变更。

**回归用例**
`tests/test_sys_menu_service.py` / `test_sys_menu_controller.py` 里覆盖了 50 / 100 / 200
三处上限的边界；`component` 超长时回的是 `组件路径不能超过255个字符`。

---

## 30. `/system/user/profile` 切片（Phase 3.11）`[需注意]`

> 本节覆盖 `SysProfileController` + 它带进来的文件上传基础设施（`FileUploadUtils` /
> `MimeTypeUtils` / `Seq` / 文件异常族）。
> 对照表见 [MAPPING_SYS_PROFILE.md](MAPPING_SYS_PROFILE.md)。
>
> §0 表里的第 53–62 条分别对应本节 30.1–30.10。

### 30.1 `@Log` 未迁移 → 个人信息/头像不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，`updateProfile` / `updatePwd` /
> `avatar` 的 `@Log` 全部生效。下面"不留审计记录"的结论**已失效**，
> 原文保留只为留下变更轨迹，请以 §42.9 为准。

**Java 原行为**
`updateProfile` / `updatePwd` 带 `@Log(title = "个人信息", businessType = UPDATE)`，
`avatar` 带 `@Log(title = "用户头像", ...)`，由 `LogAspect` 异步写 `sys_oper_log`。

**Python 实现**
`LogAspect` 仍未迁移（同 §25.2 / §26.2 / §27.2 / §28.2 / §29.2），因此这三次操作不留审计记录。
`profile` 是读操作，Java 也没有 `@Log`。

**影响与规避**
接口返回与业务表一致；唯一可见后果是 `/monitor/operlog` 查不到“用户改了自己的昵称/密码/头像”。
密码变更属于安全敏感事件，生产上建议与 §28.3 的请求级事务一起补
`LogAspect`（两者都在切面层，改动面重合）。

### 30.2 四个端点**都没有**权限点 `[无影响]`

**Java 原行为**
`SysProfileController` 全文**一个 `@PreAuthorize` 都没有**。它们能被调用是因为
`SecurityConfig` 的 `anyRequest().authenticated()`；未登录仍然是安全过滤器给的 401。

**Python 实现**
四个函数上都没有 `@pre_authorize_permi`。这是**有意**的：改自己的资料不应该要求
“用户管理”权限。

**为什么不能“顺手补上”**
补一个 `system:user:edit` 会让**普通用户**（没有用户管理权限）连自己的昵称都改不了。
注意与 `sys_menu` 的 `treeselect` 不是一回事：那里是“角色编辑页要用”（§29.7），
这里是“本来就不该有”。

**回归用例**
`tests/test_sys_profile_controller.py::TestRouteTable::test_no_endpoint_carries_a_permission_point`
（逐个检查 `route.dependant.dependencies` 里没有 `pre_authorize_permi`）。

### 30.3 `profile` 路由必须在 `sys_user` **之前**注册 `[无影响]`

**Java 原行为**
Spring 的 `PathPattern` 会优先匹配字面量段，所以 `GET /system/user/profile`
与 `GET /system/user/{userId}` 同时存在也没问题。

**Python 实现**
FastAPI **严格按注册顺序**匹配。`app/main.py` 里 `sys_profile_router` 必须排在
`sys_user_router` 之前，否则 `/system/user/profile` 先命中 `/{user_id}`，在 `int` 转换处
回 **HTTP 422 + 校验错误体**（Java 是 200）。

当前已按序注册，客户端感知不到任何差异。这是一条“改 `main.py` 时容易踩”的约束，
不是对外行为差异。

**回归用例**
`TestRouteTable::test_the_profile_router_is_registered_before_the_user_router`
（对 `create_app().routes` 做下标比较）。

### 30.4 库里与缓存里的 `password` **不是同一个哈希** `[无影响]`

**Java 原行为**

```java
if (userService.resetUserPwd(userName, SecurityUtils.encryptPassword(newPassword)) > 0)
{
    loginUser.getUser().setPassword(SecurityUtils.encryptPassword(newPassword));
```

`encryptPassword` 调了**两次**。BCrypt 每次生成随机 salt，所以：

- `sys_user.password`（数据库）= 哈希 A
- `login_tokens:<uuid>` 里的 `user.password`（缓存）= 哈希 B
- `A != B`，但两者都能用同一个明文校验通过

**Python 实现**
逐字照抄，也是两次独立调用。

**为什么不能“优化”成一次**
省一次 BCrypt（约 100ms）看起来划算，但那样会**改变**一个可观测事实：拿到库里的哈希与
缓存里的哈希做等值比较（数据修复脚本、排查“密码改了为什么还能登录”之类）会从
“永远不等”变成“永远相等”。行为等价优先于性能。

**运维注意**
不要用 `select password from sys_user` 与 Redis 里的 `password` 比对是否相等 —— 它们本来就不等。

**回归用例**
`tests/test_sys_profile_controller.py::TestUpdatePwd::test_it_stores_an_encrypted_password_and_refreshes_the_cache`
（断言 `reset_user_pwd` 与缓存写入各发生一次，且**不**断言两者哈希相同）。

### 30.5 头像存的是 `/profile/avatar/...` **相对 url** `[需注意]`

**Java 原行为**
`FileUploadUtils.getPathFileName` 切掉 `RuoYiConfig.getProfile()` 前缀，返回
`Constants.RESOURCE_PREFIX + "/" + currentDir + "/" + fileName`，即：

```text
/profile/avatar/2026/10/26/avatar_20261026103851A001.png
```

这个字符串原样写进 `sys_user.avatar`，前端 `<img :src="avatar">` 直接用它，
由 `ResourcesConfig` 的 `/profile/**` → `file:{ruoyi.profile}` 映射提供静态访问。

**Python 实现**
同样返回相对 url，同样写入 `sys_user.avatar`。`app/main.py` 里已挂同一条静态映射。

**客户端/运维注意**
- 数据库里**没有**域名，也没有 `http://`；换域名/换端口时**不需要**刷数据。
- 头像的物理文件在 `ruoyi.profile` 指向的目录下；`profile` 换了而旧文件没搬，旧头像会 404。
- 头像是**每次上传都不覆盖**：文件名带 14 位时间 + 3 位序列号，旧文件留在盘上，
  不自动清理（Java 也没有清理逻辑）。

**回归用例**
`tests/test_file_upload_utils.py::TestUpload::test_it_writes_the_bytes_and_creates_the_date_directories`
与 `tests/test_sys_profile_controller.py::TestAvatar::test_a_successful_upload_returns_the_url_and_refreshes_the_cache`
（断言 url 匹配 `r"/profile/avatar/\d{4}/\d{2}/\d{2}/avatar_\d{14}A\d{3}\.png"`）。

### 30.6 `UploadFile.size` 为 `None` 时回退到底层文件长度 `[无影响]`

**Java 原行为**
`MultipartFile#getSize()` 永远返回真实字节数（Spring 解析 multipart 时就记下来了）。
`isEmpty()` = `getSize() == 0`。

**Python 实现**
Starlette 的 `UploadFile` 有 `size` 属性，但它是**实例属性**且可以为 `None`
（手工构造、或某些解析路径没填）。`file_upload_utils.size_of()` 的顺序是：

1. `getattr(file, "size", None)` 是 `int` → 直接返回；
2. 否则 `seek(0, SEEK_END)` 量长度，量完**复位到原位置**。

**为什么需要这层兜底**
`avatar` 用 `size_of(file) == 0` 复刻 `file.isEmpty()`。若 `size` 是 `None` 而不兜底，
`None == 0` 为 `False`，一个 0 字节文件会被当成“非空”送进 `upload` ——
与 Java 的短路行为分道扬镛。

**回归用例**
`tests/test_file_upload_utils.py::TestUpload::test_a_zero_byte_file_is_accepted_here`
（工具类接受 0 字节）与 `tests/test_sys_profile_controller.py::TestAvatar::test_a_zero_byte_file_falls_through_to_the_failure_message`
（控制器短路）。

### 30.7 缺 `oldPassword` → `rawPassword cannot be null` `[无影响]`

**Java 原行为**
`updatePwd(String oldPassword, String newPassword)` 没有 `@RequestParam(required = ...)`，
**请求里不传就是 `null`**，然后：

```java
SecurityUtils.matchesPassword(null, password)
// -> BCryptPasswordEncoder#matches -> IllegalArgumentException("rawPassword cannot be null")
```

Spring 的 `matches` **不会**把 `null` 当成“不匹配”返回 `false`，而是抛异常。
所以客户端看到的不是 `修改密码失败，旧密码错误`，而是
**HTTP 200 + `{"code":500,"msg":"rawPassword cannot be null"}`**。

**Python 实现**
`security_utils.BCryptPasswordEncoder.matches` 对 `None` 抛
`ValueError("rawPassword cannot be null")`（**同一个 message**），落到 `Exception` 兜底处理器。

**客户端注意**
前端“修改密码”页两个输入框都必填，正常不会遇到；但脚本调错（拼错字段名）时看到的
是英文 message。这是 Java 原样，**不要**改成中文业务文案。

**回归用例**
`TestUpdatePwd::test_a_missing_old_password_raises_the_spring_message`
与 `test_a_wrong_old_password_still_answers_the_business_message`
（后者把边界钉住：**传了值**但不对 → 中文业务文案）。

### 30.8 缺 multipart 部件：Java 400，Python **200 + code 500** `[需注意]`

**Java 原行为**
`avatar(@RequestParam("avatarfile") MultipartFile file)` —— 没有送这个部件时，
Spring 在参数解析阶段就抛 `MissingServletRequestPartException`，由容器的默认错误页
处理：**HTTP 400** + Spring 错误体（不是 `AjaxResult`）。

**Python 实现**
FastAPI 把它归为请求校验错误（`avatarfile: Field required`），而本项目的
`RequestValidationError` 处理器统一转成 **HTTP 200 + `{"code":500,"msg":...}`**
（见 §2 的总约定）。

**客户端注意**
- 两者都“不会上传成功”，但状态码不同：`400` vs `200`。
- 依赖 `response.ok` 判断成败的脚本在 Python 侧会误以为成功 —— 必须看 `body.code`。
这条偏差**不是本切片引入的**，而是全局校验处理器（`§2`）的必然结果；
要彻底对齐，需要给校验处理器加一个“缺少 body 参数时回 400”的分支，
影响面覆盖所有端点，因此单独评估。

**回归用例**
`TestAvatar::test_a_missing_part_is_a_validation_error`
（断言 `code == 500` 且 message 里含 `avatarfile`）。

### 30.9 `getPathFileName` 对 `profile` 之外的目录“截错位置” `[无影响]`

**Java 原行为**

```java
int dirLastIndex = RuoYiConfig.getProfile().length() + 1;
String currentDir = StringUtils.substring(uploadDir, dirLastIndex);
```

`uploadDir` 不在 `profile` 之下时，这个下标是“意位置”，`substring` 不会抛异常
（`StringUtils.substring` 会自己 clamp），于是得到一个莫名其妙的 url。

**Python 实现**
`string_utils.substring` 已经实现了 Java 的 clamp 语义（见 §25 的字符串工具），
`get_path_file_name` 逐字照拄，**不加**“目录必须在 profile 之下”的校验。

**为什么保留**
当前唯一调用方传的是 `RuoYiConfig.getAvatarPath()`（一定在 `profile` 之下），
所以这条分支在线上不可达。加上校验会让“本该失败”的调用变成异常，
新增了一个 Java 没有的失败点。

**回归用例**
`tests/test_file_upload_utils.py::TestFilenameHelpers::test_get_path_file_name_truncates_a_directory_outside_the_profile`。

### 30.10 0 字节文件在控制器短路，工具类本身接受空文件 `[无影响]`

**Java 原行为**

```java
if (!file.isEmpty()) { ...upload... }
return AjaxResult.error("上传图片异常，请联系管理员");
```

`isEmpty()` 的判断在**控制器**，`FileUploadUtils` 不管内容长度。所以：

| 调用方式 | 0 字节文件的结果 |
|---|---|
| `POST /system/user/profile/avatar` | `上传图片异常，请联系管理员`，**磁盘/数据库都不动** |
| 直接调 `FileUploadUtils.upload(...)` | 正常落盘（得到一个 0 字节文件） |

**Python 实现**
同一个分工：`avatar` 里 `if not _is_empty_file(avatarfile)`，
`file_upload_utils` 不做长度判断。

**为什么不能“把校验下沉到工具类”**
下沉之后，将来其它调用方（如 `CommonController` 的文件上传）也会被拒绝 0 字节文件 ——
而 Java 那边不会。行为差异会隐到现在看不到的地方。

**回归用例**
`TestUpload::test_a_zero_byte_file_is_accepted_here` 与
`TestAvatar::test_a_zero_byte_file_falls_through_to_the_failure_message`
（一对：工具类接受、控制器拒绝）。

---

## 31. `/system/notice` 切片（Phase 3.12）`[需注意]`

> 本节覆盖 `SysNoticeController` + `SysNoticeServiceImpl` + `SysNoticeMapper` 这一条竖切面。
> 对照表见 [MAPPING_SYS_NOTICE.md](MAPPING_SYS_NOTICE.md)。
>
> §0 表里的第 64–71 条分别对应本节 31.2–31.9。

### 31.1 端点与权限点总览 `[无影响]`

7 个映射**全部迁移**（本模块 Java 侧就没有 `export`，与 user / post / role 不同）：

| Java | Method | Path | 权限点 |
|---|---|---|---|
| `list(SysNotice)` | GET | `/system/notice/list` | **无**（注解被注释） |
| `listquery(SysNotice)` | GET | `/system/notice/listquery` | **无** |
| `getInfo(Long)` | GET | `/system/notice/{noticeId}` | **无** |
| `getViewInfo(Long)` | GET | `/system/notice/view/{noticeId}` | **匿名**（不能登录） |
| `add(SysNotice)` | POST | `/system/notice` | `system:notice:add` |
| `edit(SysNotice)` | PUT | `/system/notice` | `system:notice:edit` |
| `remove(Long[])` | DELETE | `/system/notice/{noticeIds}` | `system:notice:remove` |

只有 **3 个**权限点。注册顺序上 `/list` / `/listquery` / `/view/{id}` 必须排在
`/{id}` 之前（FastAPI 按注册顺序匹配）。

### 31.2 `@Log` 未迁移 → 公告管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，本控制器的 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

**Java 原行为**
`add` / `edit` / `remove` 带 `@Log(title = "通知公告", businessType = INSERT/UPDATE/DELETE)`，
由 `LogAspect` 异步写入 `sys_oper_log`（操作人、IP、耗时、请求参数）。

**Python 实现**
`LogAspect` 尚未迁移，因此这三次操作**不留审计记录**，业务结果完全不变。
与 §25.2 / §26.2 / §27.2 / §28.2 / §29.2 / §30.1 同源，是全局缺口，不是本切片的缺陷。

**运维注意**
公告变更（尤其是“删除”）在审计里查不到。若合规要求必须留痕，需要先迁 `LogAspect`。

### 31.3 `GET /system/notice/list` **没有**权限点 `[无影响]`

**Java 原行为**

```java
// @PreAuthorize("@ss.hasPermi('system:notice:list')")
@GetMapping("/list")
public TableDataInfo list(SysNotice notice)
```

注解是**被注释掉的**。`listquery` / `getInfo` 本来也没写。三者都只能靠
`anyRequest().authenticated()` 兜底 —— **登录即可，不看权限**。

**Python 实现**
`list_notices` / `listquery` / `get_info` 都没有 `@pre_authorize_permi`。

**为什么不能“补上”**
RuoYi 给普通角色默认只勾了业务菜单，公告页靠“登录即可”才能打开；
补上 `system:notice:list` 后，`role_key = common` 的用户会直接收到 403。
这是行为改变，不是修 bug。

**另一个容易误读的点：`listquery`**
它不是一个“另一个列表接口”，而是**强制只看正常状态**的列表：

```java
startPage();
notice.setStatus("0");   // 覆盖客户端传的 status
```

首页/门禁大屏用它，避免展示已关闭的公告。两行顺序与 Java 一致
（先分页、后覆盖），结果上等价于“先覆盖再分页”，但保持同序便于 diff。

**回归用例**
`tests/test_sys_notice_controller.py::TestPermissions::test_list_needs_no_permission`、
`TestListQuery::test_status_is_forced_to_zero`。

### 31.4 `/system/notice/view/**` **只允许匿名**：已登录反而 403 `[需注意]`

**Java 原行为**

```java
// SecurityConfig
.antMatchers("/system/notice/view/**").anonymous()
```

`anonymous()` 不是 `permitAll()`：它要求**当前请求没有认证**。
已登录的浏览器带着 token 访问 `/system/notice/view/1`，会被 `AccessDeniedHandler`
直接挡回 **403**。

**Python 实现**
`security_config.AUTHORIZATION_RULES` 里对应 `AccessMode.ANONYMOUS`：

| 请求 | 结果 |
|---|---|
| 无 token | 200，正常返回公告详情 |
| 带有效 token | **403** `{"code":403,"msg":"..."}` |

**客户端注意**
这个端点只用于“未登录看公告详情”（例如登录页公告弹窗、扫码页）。
**已登录时请走 `/system/notice/{noticeId}`** —— 两者查的是同一个 service 方法，
响应体完全相同，只是安全规则不同。

**回归用例**
`tests/test_security_filter.py` 的规则表断言；
`tests/test_sys_notice_controller.py::TestDetailEndpoints::test_view_and_get_info_hit_the_same_method`
（两个端点返回体一致）。

### 31.5 `insertNotice` 把 `createBy` 改写成 `userId` `[需注意]`

**Java 原行为**
控制器先写 `userName`，服务层立刻覆盖：

```java
// SysNoticeController#add
notice.setCreateBy(getUsername());            // "admin"

// SysNoticeServiceImpl#insertNotice
notice.setCreateBy(SecurityUtils.getUserId() + "");   // "1"，覆盖上面那句
notice.setTenantId(SecurityUtils.getTenantId());
```

于是 `sys_notice.create_by` 里存的是 **数字字符串**，而 `sys_user.create_by`、
`sys_post.create_by` 存的是 `userName`。`updateNotice` 对 `updateBy` 做同样的事。

**Python 实现**
`insert_notice` / `update_notice` 里 `f"{SecurityUtils.get_user_id()}"`，
控制器里那两句 `get_username()` **保留**（它们在 Java 里也确实执行了，只是被覆盖）。

**影响**
- 前端“创建者”列如果在公告页做姓名反查，会查不到（存的是 id）；
- 数据迁移/报表若统一按 `create_by` = userName 取数，公告表要特殊处理。

**为什么保留**
一旦改成 userName，就与线上历史数据（全部是 id）不一致，且属于行为改变。

**回归用例**
`tests/test_sys_notice_service.py::TestInsertNotice::test_create_by_is_overwritten_with_the_user_id`。

### 31.6 `noticeType` 被服务层强制成 `"1"` `[需注意]`

**Java 原行为**
`insertNotice` 第一行就是 `notice.setNoticeType("1")`。`1` = 通知，`2` = 公告。
**前端选“公告”也存成“通知”。** 字典 `sys_notice_type` 里的 `2` 在新增链路永远用不上。

**Python 实现**
同位置 `notice.notice_type = "1"`。

**注意 `updateNotice` 不强制** —— 修改时传 `"2"` 会真的写进库（`<set>` 里
`notice_type` 判 `!= null and != ''`）。所以“新增是通知、改一次能变公告”是现状。

**回归用例**
`TestInsertNotice::test_notice_type_is_forced_to_one`。

### 31.7 `@Validated` 是空壳：公告实体零约束注解 `[无影响]`

**Java 原行为**
`add` / `edit` 上有 `@Validated @RequestBody`，但 `SysNotice` 上**一个约束注解都没有**
（没有 `@NotBlank` / `@Size` / `@NotNull`）。Hibernate Validator 拿到空约束集，直接放行：
空标题、200 字标题、空内容都能入库，最终由数据库列宽/`nullable` 决定成败。

**Python 实现**
没有 `NOTICE_CONSTRAINTS`，`add` / `edit` 的请求体直接绑定为 `SysNotice`，**不**做
`validate()`。这是“忠实迁移”，不是遗漏。

**为什么不能“补上”**
凭空加 `@NotBlank` 会让空标题从“能入库”变成 `code 500` —— 线上任何依赖空标题的
导入脚本会立刻失效。若确实需要校验，应该先在 Java 侧加，再同步。

**回归用例**
`tests/test_sys_notice_controller.py::TestNoValidation`（4 条：空 body 仍走到 403、
空标题通过、超长标题通过、坏类型在权限之前失败）。

### 31.8 `buss_id`/`buss_name` 的 insert/update 判据**不对称** `[无影响]`

**Java 原行为**

```xml
<!-- insert -->
<if test="bussId != null">buss_id,</if>
<if test="bussName != null">buss_name,</if>
<if test="tenantId != null">tenant_id,</if>

<!-- update -->
<if test="bussId != null and bussId != ''">buss_id = #{bussId},</if>
<if test="bussName != null and bussName != ''">buss_name = #{bussName},</if>
<!-- 没有 tenant_id -->
```

同一个字段：**新增时空串会写库，修改时空串被跳过**。另外 `updateNotice` 里
**没有** `tenant_id` —— 改公告不会改租户。

**Python 实现**
`_INSERT_NOTICE_NULL_ONLY = ("buss_id", "buss_name", "tenant_id")`；
`_UPDATE_NOTICE_COLUMNS` 里这两列 `require_text=True`，且不含 `tenant_id`。

**另一处容易看错**
`notice_content` 恰好**相反**：insert 判 `!= null and != ''`，update 只判 `!= null`
（空串能把正文清空）。这两个“方向相反”的不对称都必须保留。

**列名大小写**
条件里写的是 `t.TENANT_ID`，投影里是 `t.tenant_id` —— MySQL 列名不区分大小写所以能跑，
换严格大小写的库会炸。照抄，不要统一。

**回归用例**
`tests/test_sys_notice_mapper.py::TestInsertNotice::test_buss_and_tenant_columns_keep_the_empty_string`、
`TestUpdateNotice::test_buss_columns_drop_the_empty_string`、
`TestUpdateNotice::test_tenant_id_is_not_updatable`、
`TestUpdateNotice::test_notice_content_survives_an_empty_string_but_titles_do_not`。

### 31.9 `addDeliveryTimeAbnormal` 是**死代码** `[无影响]`

**Java 原行为**
`SysNoticeServiceImpl#addDeliveryTimeAbnormal` 注释写着“新增到货时间异常提的通知公告”，
逻辑是“内容相同的不重复新增”：先按入参当条件查一遍，查不到才插，查到就返回已有 id。

但它在整个工程里**没有任何调用方** —— 没有控制器映射，没有定时任务引用，
没有内部调用。

**Python 实现**
`SysNoticeService.add_delivery_time_abnormal` 逐行照搬，含两个易错点：

1. 它直接调 mapper 的 `insert_notice`，**不经过** `insert_notice` 服务方法
   （因此不会自动带 `noticeType`）—— 所以它手工补了 `createBy` / `tenantId` /
   `noticeType` / `status` 四行；
2. 命中已有记录时 `notice = sysNoticeList.get(0)` 是**改局部变量**，入参上的改动
   全部丢弃（不写库）。

**为什么要迁**
迁移原则第 4 条：不删“看似无用”的 Java 代码。将来如果启用，实现已经就位。

**回归用例**
`tests/test_sys_notice_service.py::TestAddDeliveryTimeAbnormal`（4 条）。

### 31.10 本模块**没有** `export`（Java 也没有）`[无影响]`

`SysNoticeController` 源码里只有上表那 7 个映射，没有导出按钮对应的端点。
所以 `GET /system/notice/export` 在两侧都是 **404**（不像 user / post / role 那样
被 `/{id}` 兜住回 500）。

**回归用例**
`tests/test_sys_notice_controller.py::TestRouteTable::test_export_is_not_registered_either`。

---

## 32. `/system/dict` 切片（Phase 3.13）`[需注意]`

> 本节覆盖 `SysDictTypeController` / `SysDictDataController` + 两个 `ServiceImpl` +
> 两个 `Mapper` + `DictUtils` 这一整条竖切面。
> 对照表见 [MAPPING_SYS_DICT.md](MAPPING_SYS_DICT.md)。
>
> §0 表里的第 72–83 条分别对应本节 32.2–32.13。

字典是这个系统里被调用最多的读接口（每个下拉框、每次导出）。它的特点是：**读走
Redis 缓存**、**写完全清缓存**、**改类型名要同步子表**。

### 32.1 端点与权限点总览 `[无影响]`

`SysDictTypeController` —— `/system/dict/type`，**8** 个映射（迁移 7 个）：

| Java | Method | Path | 权限点 |
|---|---|---|---|
| `list` | GET | `/list` | `system:dict:list` |
| `export` | GET | `/export` | `system:dict:export`（**未迁移**） |
| `getInfo` | GET | `/{dictId}` | `system:dict:query` |
| `optionselect` | GET | `/optionselect` | **无**（登录即可） |
| `add` | POST | `` | `system:dict:add` |
| `edit` | PUT | `` | `system:dict:edit` |
| `clearCache` | DELETE | `/clearCache` | `system:dict:remove` |
| `remove` | DELETE | `/{dictIds}` | `system:dict:remove` |

`SysDictDataController` —— `/system/dict/data`，**8** 个映射（迁移 7 个）：

| Java | Method | Path | 权限点 |
|---|---|---|---|
| `list` | GET | `/list` | `system:dict:list` |
| `export` | GET | `/export` | `system:dict:export`（**未迁移**） |
| `getInfo` | GET | `/{dictCode}` | `system:dict:query` |
| `dictType` | GET | `/type/{dictType}` | **无**（登录即可） |
| `dictTypeMore` | GET | `/typemore/{dictType}` | **无**（登录即可） |
| `add` | POST | `` | `system:dict:add` |
| `edit` | PUT | `` | `system:dict:edit` |
| `remove` | DELETE | `/{dictCodes}` | `system:dict:remove` |

三个"无权限点"的端点都是**前端每页都调**的数据源，补上 `@PreAuthorize` 会白屏；
这一点与 §31.3 的 `notice/list` 同类。

**注册顺序**（两处都是"字面量在变量之前"）：
`/list` → `/optionselect` → `/{dictId}` → `/clearCache` → `/{dictIds}`；
`/list` → `/type/{t}` → `/typemore/{t}` → `/{dictCode}`。
`/clearCache` **必须**写在 `/{dictIds}` 之前，否则会被当成 `dictIds = "clearCache"`
而在 `parse_id_array` 处抛错。

**回归用例**
`tests/test_sys_dict_type_controller.py::TestRouteTable`、
`tests/test_sys_dict_data_controller.py::TestRouteTable`。

### 32.2 两个 `export` 未迁移 `[需注意]`

与 §25.1 / §26.1 / §28.1 同一个缺口：`ExcelUtil`（Apache POI）不存在。

* `GET /system/dict/type/export` 会被 `/{dictId}` 兜住，`"export"` 转 `int` 失败 →
  **HTTP 200 + code 500**；
* `GET /system/dict/data/export` 同上（被 `/{dictCode}` 兜住）。

**回归用例**
`tests/test_sys_dict_type_controller.py::TestRouteTable::test_export_falls_into_the_path_variable`、
`tests/test_sys_dict_data_controller.py::TestRouteTable::test_export_falls_into_the_path_variable`。

### 32.3 `@Log` 未迁移 → 字典管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，含 `clearCache` 在内的 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

同一缺口（§25.2）：`export` / `add` / `edit` / `remove` / `clearCache` 的 `@Log`
都不会写审计表。业务结果不受影响。

两个原文细节照抄：

* `clearCache` 的 `businessType` 是 `BusinessType.CLEAN`（全项目唯一一处）；
* `SysDictDataController#remove` 的注解写的是 `@Log(title = "字典类型", ...)` ——
  而本类叫"字典数据"，是 Java 的复制粘贴笔误。将来迁 `LogAspect` 时**不要"修正"**，
  否则操作日志的标题会与历史数据不一致。

### 32.4 字典预热 `init()` **不在启动时调用** `[需注意]`

Java：`SysDictTypeServiceImpl#init()` 带 `@PostConstruct`，容器启动后遍历
`sys_dict_type` 全表，把每个类型下的 `status='0'` 子项写进 Redis。

Python：**保留方法，不挂到 FastAPI 生命周期**。理由是本工程的数据源惰性创建
（`app.main`），启动期连库会让"没有 MySQL 也能起来做健康检查"这条能力失效。

**语义无损**：`selectDictDataByType` 在缓存未命中时会回源查库并写回，用的是与
`init()` **完全同一条 SQL**（`SysDictDataMapper.selectDictDataByType`），所以
"启动预热"只是把第一次请求的延迟提前，不是行为差异。

需要手工预热时：

```python
from app.system.service.sys_dict_type_service import get_dict_type_service
get_dict_type_service().init()
```

**回归用例** `tests/test_sys_dict_type_service.py::TestInit`（含"构造服务不连库"一条）。

### 32.5 `updateDictType` **没有**事务 → 子表先改 `[需注意]`

Java 的 `updateDictType` 是全切片唯一带 `@Transactional` 的方法，顺序是：

1. `selectDictTypeById(dictId)` 拿**旧**类型名；
2. `updateDictDataType(oldDictType, newDictType)` —— 子表全部改名；
3. `updateDictType(dict)` —— 主表改名；
4. `row > 0` 时清缓存。

Python 侧第 2、3 步**不在同一事务里**（§28.3 的缺口）。第 3 步失败时，子表
已经改成新名字，库里会留下"子项指向一个不存在的类型"的孤儿行。

顺序本身是照抄的，不能调换：先改主表会让第 2 步拿不到旧名字（`oldDict` 是**改之前**
查出来的，所以下标顺序只影响失败时的残留形态，不影响成功路径）。

**回归用例**
`tests/test_sys_dict_type_service.py::TestUpdateDictType::test_the_children_are_still_renamed_when_the_parent_fails`
（该用例**主动钉住**这个缺口，补事务后应改写成期望回滚）。

### 32.6 `selectDictDataByTypeMore` 的两处原文缺陷 `[无影响]`

```java
if (StringUtils.isEmpty(dictType)) {
    dictType = "-dadadadas";
} else {
    if (dictType.endsWith(",")) {
        dictType = dictType.substring(0, dictType.length());   // 空操作！
    }
}
if (StringUtils.isEmpty(dictType)) {          // 死代码
    dictType = "-dadadadas";
}
```

1. `substring(0, length)` **等于原样返回**，尾逗号没被去掉。于是 `"car_type,"` 与
   `"car_type"` 是**两个不同的缓存键**（内容一样）。Python 侧照样保留这个差异。
2. 第二个 `isEmpty` 判断是死代码（中间那段不可能把它变空）。

两处都照抄：真要清理，得先确认线上 Redis 里有没有带尾逗号的键，否则会把不同键的
缓存内容混在一起。`"-dadadadas"` 这个哨兵值也一样照抄（它是一个永远查不到的类型名）。

**回归用例** `tests/test_sys_dict_type_service.py::TestSelectDictDataByTypeMore`。

### 32.7 `selectDictLabel` **没有** `limit 1` `[无影响]`

```xml
<select id="selectDictLabel" resultType="String">
  select dict_label from sys_dict_data where dict_type = #{dictType} and dict_value = #{dictValue}
</select>
```

同一 `(dictType, dictValue)` 有两条数据时，MyBatis 的 `selectOne()` 抛
`TooManyResultsException` → **500**。Python 侧显式检测行数并在 >1 时抛
`AttributeError("org.apache.ibatis.exceptions.TooManyResultsException: ...")` ——
不能"取第一行"，那会让数据质量错误静默变成"显示得还行"。

配合 `add` **没有**唯一性校验（Java 也没有），库里存在重复键是完全可能的。

**回归用例** `tests/test_sys_dict_data_mapper.py::TestSelectDictLabel`。

### 32.8 两个 `insertDictXxx` **不回写**主键 `[无影响]`

`insertDictType` / `insertDictData` 的 XML **没有** `useGeneratedKeys`（对比
`insertPost` / `insertNotice` 都有），所以插入后 `dictId` / `dictCode` 仍是 `null`。
Python 侧同理**不**回写 `lastrowid` —— 与 §29.3 的 `insertMenu` 是同一类。

风险点：如果哪天"顺手"补上回写，`add` 之后再调 `checkDictTypeUnique(dict)` 的判定
会从"新增"变成"改自己"，边界行为随之改变。

**回归用例**
`tests/test_sys_dict_type_mapper.py::TestInsertDictType::test_the_generated_key_is_not_written_back`、
`tests/test_sys_dict_data_mapper.py::TestInsertDictData::test_the_generated_key_is_not_written_back`。

### 32.9 `SysDictData` 的 JSON 多一个 `default` 键 `[无影响]`

Java 除 `getIsDefault()`（→ `"isDefault"`）之外还有一个**只读计算属性**：

```java
public boolean getDefault() {
    return UserConstants.YES.equals(this.isDefault) ? true : false;
}
```

Jackson 把它当属性序列化，于是每条字典数据的 JSON 里都多出 `"default": true/false`
（严格等于 `"Y"` 才为 `true`；`null` / `""` / `"N"` / 小写 `"y"` 都是 `false`）。
前端用它做下拉框默认项，**不能删**。

Python 用 pydantic 的 `@computed_field` 复刻：只出现在输出、不接受入参、排在普通字段
之后（与 Jackson"先字段、后 getter-only 属性"一致）。

**回归用例**
`tests/test_sys_dict_data_controller.py::TestValidationRunsBeforePermission::test_the_computed_default_key_is_emitted`。

### 32.10 两个 `selectDictData*Map` 不走缓存、不过滤 `status` `[无影响]`

```java
default Map<String, String> selectDictDataMap(String dictValue)      // {dictValue: dictLabel}
default Map<String, String> selectDictDataLaleMap(String dictValue)  // {dictLabel: dictValue}
```

* 没有控制器端点，是 `manager` / `base` 包里导出、详情接口的辅助方法（把编码翻成中文）；
* 形参名叫 `dictValue`，实际传的是**字典类型**（命名照抄）；
* **不走缓存**，直接 `selectDictDataList` 查库；
* **不过滤** `status` —— 停用项也在映射表里（与 `DictUtils.getDictLabel` 是两条路，别合并）；
* `Collectors.toMap` 遇重复键抛 `IllegalStateException`（500），Python 侧显式检测并抛
  `AttributeError`，与 §32.7 的处理方式一致；`null` 值允许、`null` 键同样会撞键；
* `Lale` 是 `Label` 的笔误，方法名照抄。

**回归用例** `tests/test_sys_dict_data_service.py::TestSelectDictDataMap` /
`::TestSelectDictDataLaleMap`。

### 32.11 `clearDictCache` 用 `KEYS` 扫全部键 `[无影响]`

```java
Collection<String> keys = redisCache.keys(CacheConstants.SYS_DICT_KEY + "*");
redisCache.deleteObject(keys);
```

`KEYS` 是 **O(N) 阻塞**命令，键多了会卡住 Redis（`RedisCache.keys` 的注释里已说明
同一取舍）。照抄，不改成 `SCAN` —— 改成 `SCAN` 会让"删干净"变成"删大部分"，
而字典缓存的正确性依赖"清空"。

任何写操作（`insert` / `update` / `delete` / 改类型名）都会清**整个** `sys_dict:*`，
不只是当前类型：因为 `updateDictData` 可能连 `dictType` 一起改。

**回归用例** `tests/test_dict_utils.py::TestRemoveAndClear`。

### 32.12 曾拼出 `where AND ...`（**已修复**）`[需注意]`

三个列表查询（`selectNoticeList`、`selectDictTypeList`、`selectDictDataList`）最初的
SQL 拼接是"每个条件自带前导 `AND`，再用空格 join，最后前面加 `where`"，于是命中任一
条件时拼出：

```sql
... where AND t.notice_title like ...    -- MySQL 直接报语法错
```

MyBatis 的 `<where>` 元素会自动削掉首个 `AND` / `OR`，手写拼接必须做同样的事。
修法是"条件片段不带前导 `AND`，用 ` and ` 拼接"（与 `sys_post_mapper` / `sys_role_mapper`
原本的写法一致）。

为什么之前没被发现：mapper 的单元测试只断言**片段**与**顺序**，不跑真库；而公告的
列表接口在此之前没有端到端用例。现在三个 mapper 各加了一条
`test_the_where_clause_does_not_start_with_and`，断言 `"where and"` 不出现。

**回归用例**
`tests/test_sys_notice_mapper.py`、`tests/test_sys_dict_type_mapper.py`、
`tests/test_sys_dict_data_mapper.py` 中的同名用例。

### 32.13 `/typemore` 未命中返回 `{}` 而不是 `[]` `[无影响]`

Java 的写法是"先把 `null` 换成空 List，**再** `groupingBy`"：

```java
List<SysDictData> data = dictTypeService.selectDictDataByTypeMore(dictType);
if (StringUtils.isNull(data)) { data = new ArrayList<>(); }
return AjaxResult.success(data.stream().collect(Collectors.groupingBy(SysDictData::getDictType)));
```

空数组分组后是空 `HashMap`，所以 `"data": {}`；`/type/{dictType}` 没有分组这一步，
所以才是 `"data": []`。两个端点在"查不到"时的 JSON **形状不同**，这是 Java 原样。

另外 Java 的 `groupingBy` 默认用 `HashMap`（键顺序不确定）；Python 的 `dict` 保留
首次出现顺序，而 SQL 自带 `order by dict_type,dict_sort asc`，所以 Python 侧是确定的
字典序 —— 属于"更可预期"，不是行为差异。

**回归用例** `tests/test_sys_dict_data_controller.py::TestDictTypeMoreEndpoint`。

---

## 33. `/system/config` 切片（Phase 3.14）`[需注意]`

> 本节覆盖 `SysConfigController` + `SysConfigServiceImpl` + `SysConfigMapper` + `Convert.toStr`
> 这一整条竖切面。对照表见 [MAPPING_SYS_CONFIG.md](MAPPING_SYS_CONFIG.md)。
>
> §0 表里的第 84–92 条分别对应本节 33.2–33.10。

参数配置的特点：**读走缓存且逐键维护**、**增改写单键**、**删除才全清**、**内置参数禁删**。
这个策略与字典切片（§32）**完全不同**，两者不可互相参照。

### 33.1 端点与权限点总览 `[无影响]`

`SysConfigController` —— `/system/config`，**8** 个映射（迁移 7 个）：

| Java | Method | Path | 权限点 |
|---|---|---|---|
| `list` | GET | `/list` | `system:config:list` |
| `export` | GET | `/export` | `system:config:export`（**未迁移**） |
| `getInfo` | GET | `/{configId}` | `system:config:query` |
| `getConfigKey` | GET | `/configKey/{configKey}` | **无**（登录即可） |
| `add` | POST | `` | `system:config:add` |
| `edit` | PUT | `` | `system:config:edit` |
| `remove` | DELETE | `/{configIds}` | `system:config:remove` |
| `clearCache` | DELETE | `/clearCache` | `system:config:remove` |

**注册顺序**：`/list` → `/configKey/{key}` → `/{configId}` → `POST` → `PUT` →
`/clearCache` → `/{configIds}`。`/clearCache` 必须写在 `/{configIds}` 之前，否则会被
当成 id 列表而 `int("clearCache")` 失败。

**回归用例** `tests/test_sys_config_controller.py::TestRouteTable`。

### 33.2 `export` 未迁移 `[需注意]`

与 §25.1 / §26.1 / §28.1 / §32.2 同一个缺口：`ExcelUtil`（Apache POI）不存在。
于是 `GET /system/config/export` 会被 `/{configId}` 兜住，`"export"` 转 `int` 失败 →
**HTTP 200 + code 500**（不是 404，也不是空 xlsx）。

**回归用例** `tests/test_sys_config_controller.py::TestRouteTable::test_export_falls_into_the_path_variable`。

### 33.3 `@Log` 未迁移 → 参数管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，含 `clearCache` 在内的 5 处 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

同一缺口（§25.2）：`export` / `add` / `edit` / `remove` / `clearCache` 的 `@Log`
都不会写审计表。`clearCache` 的 `businessType` 是 `BusinessType.CLEAN`（与字典的
`clearCache` 一样，是全项目仅有的两处）。

### 33.4 参数预热 `init()` **不在启动时调用** `[需注意]`

Java：`SysConfigServiceImpl#init()` 带 `@PostConstruct`，启动后遍历 `sys_config` 全表
写进 Redis（键 = `sys_config:<config_key>`）。

Python：**保留方法，不挂到 FastAPI 生命周期**，理由与 §32.4 相同（数据源惰性创建）。
语义无损：`selectConfigByKey` 未命中时会回源查库并**写回这一个键**。

手工预热：

```python
from app.system.service.sys_config_service import get_config_service
get_config_service().init()
```

**回归用例** `tests/test_sys_config_service.py::TestInit`。

### 33.5 缓存策略：增改写单键、删除全清 `[无影响]`

| 操作 | 字典（§32） | **参数配置** |
|---|---|---|
| 新增 / 修改 | 清空 `sys_dict:*` | 只写 `sys_config:<key>` |
| 删除 | 清空 `sys_dict:*` | 清空 `sys_config:*` |
| 读未命中 | 回源并写回该类型 | 回源并写回该键 |
| 清缓存端点 | `/clearCache`（`system:dict:remove`） | `/clearCache`（`system:config:remove`） |

增改不清理整个前缀，是因为一个键的变更不影响其它键；删除只能全清，因为 Java 在删除
**前**没收集键名，删完就查不到 `config_key` 了。照抄。

副作用（Java 原样）：`updateConfig` 写缓存用的是**入参**的 `configKey`。如果这次更新
刚好把键名改了，缓存里会多出一个新键，而旧键仍保留旧值，直到 TTL 或 `clearCache`。
**不要"顺手"再加一次 `keys + delete`** —— 那会把其它键一起清掉。

**回归用例** `tests/test_sys_config_service.py::TestCache`。

### 33.6 `selectConfigByKey` 命中 `NULL` 时回 `null` `[需注意]`

```java
String configValue = Convert.toStr(redisCache.getCacheObject(getCacheKey(configKey)));
if (StringUtils.isNotEmpty(configValue)) { return configValue; }
SysConfig retConfig = configMapper.selectConfig(new SysConfig(configKey));
if (StringUtils.isNotNull(retConfig)) {
    redisCache.setCacheObject(getCacheKey(configKey), retConfig.getConfigValue());
    return retConfig.getConfigValue();      // <-- 可能是 null
}
return StringUtils.EMPTY;                    // <-- 只有查不到才是 ""
```

两种"没有值"的返回**不同**：

| 情形 | 返回 |
|---|---|
| 库里没有这个键 | `""` |
| 库里有这个键，但 `config_value` 是 `NULL` | `null`（`data` 键被省略） |

前端的 `if (configValue)` 两种都能过，但 `configValue === ""` 只在第一种成立。
`Convert.toStr(null)` 回 `""` 只作用在**缓存读**上，不影响这里的返回值。

另外 `isNotEmpty` 会 trim，所以缓存里存了 `"  "` 也当未命中，会回源。

**回归用例** `tests/test_sys_config_service.py::TestSelectConfigByKey`。

### 33.7 `GET /configKey/{key}` **没有**权限点 `[无影响]`

Java 源码上**没有** `@PreAuthorize`（其余 6 个都有）。它是前端"按参数键名取值"的
数据源（登录页开关、皮肤名、验证码开关），补上权限会让没有参数管理权限的用户白屏。
与 §31.3 的 `notice/list`、§29.7 的 `treeselect`、`dict/type/optionselect` 同类。

**回归用例** `tests/test_sys_config_controller.py::TestPermissions::test_get_config_key_needs_no_permission`。

### 33.8 `updateConfig` 的 `remark` 传空串会**清列** `[需注意]`

`<set>` 里其它 5 列都是 `!= null and != ''`，只有 `remark` 是 `!= null`：

```xml
<if test="remark != null">remark = #{remark},</if>
```

于是 `remark: ""` 会把列清成空串，其它字段传空串则跳过。而 `insertConfig` 里
`remark` **与其它列一样**是 `!= null and != ''` —— 两条语句判据**不对称**（与 §31.8
的公告同类，方向相反）。

**回归用例** `tests/test_sys_config_mapper.py::TestUpdateConfig`。

### 33.9 `insertConfig` **不回写**主键 `[无影响]`

`<insert id="insertConfig">` **没有** `useGeneratedKeys`（对比 `insertPost` /
`insertNotice` 都有），插入后 `config.config_id` 仍是 `null`。Python 侧同理
**不**回写 `lastrowid`，与 §29.3 的 `insertMenu`、§32.8 的两个 `insertDictXxx` 同类。

**回归用例** `tests/test_sys_config_mapper.py::TestInsertConfig::test_the_generated_key_is_not_written_back`。

### 33.10 `deleteConfigById` 是孤儿 statement `[无影响]`

XML 里有 `<delete id="deleteConfigById">`，Java 接口里也声明了 `int deleteConfigById(Long`
`configId)`，但**全项目没有任何调用方**（控制器只调 `deleteConfigByIds`）。
按迁移原则第 4 条照留并标注，不删。

与 §29.8 的两条孤儿 statement（`selectMenuPerms` / `selectMenuPermsByRoleId`）同类。

---

## 34. `/system/indexmenu` 切片（Phase 3.15）`[需注意]`

> 本节覆盖 `SysIndexMenuController` + `SysIndexMenuServiceImpl` + `SysIndexMenuMapper`
> + 新增的 `BaseUuidEntity` 这一整条竖切面。
> 对照表见 [MAPPING_SYS_INDEX_MENU.md](MAPPING_SYS_INDEX_MENU.md)。
>
> §0 表里的第 93–102 条分别对应本节 34.2–34.11。

"用户常用菜单"是首页九宫格：`mylist` 取 9 条，`list` 是"可添加的候选菜单"，
`add` 把多选结果一次性写进去（先删后插）。它是**唯一**一个主键为 UUID、
审计列为 `Long` 的业务模块。

### 34.1 端点与权限点总览 `[无影响]`

`SysIndexMenuController` —— `/system/indexmenu`，**7** 个映射（迁移 6 个）：

| Java | Method | Path | 权限点 |
|---|---|---|---|
| `list` | GET | `/list` | **无**（注解被注释） |
| `getSysIndexMenulist` | GET | `/mylist` | **无**（本来就没有） |
| `export` | GET | `/export` | `system:indexmenu:export`（**未迁移**） |
| `getInfo` | GET | `/{id}` | `system:indexmenu:query` |
| `add` | POST | `` | **无**（注解被注释） |
| `edit` | PUT | `` | `system:indexmenu:edit` |
| `remove` | DELETE | `/{ids}` | **无**（注解被注释） |

**注册顺序**：`/list` → `/mylist` → `/{id}` → `POST` → `PUT` → `/{ids}`。
永远**两个**字面量路径都在 `/{id}` 之前。

**回归用例** `tests/test_sys_index_menu_controller.py::TestRouteTable`。

### 34.2 `export` 未迁移 `[需注意]`

同 §33.2：`GET /system/indexmenu/export` 被 `/{id}` 兜住，`"export"` 转 `int` 失败 →
**HTTP 200 + code 500**。

**回归用例** `tests/test_sys_index_menu_controller.py::TestRouteTable::test_export_falls_into_the_path_variable`。

### 34.3 `@Log` 未迁移 → 常用菜单不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，本控制器的 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

同一缺口（§25.2）。`add` / `edit` / `remove` 的 `@Log(title = "菜单管理")` 都没有落表。
业务结果不受影响。

### 34.4 `list` / `add` / `remove` **没有**权限点 `[无影响]`

Java 源码里的三行 `@PreAuthorize` **是被注释掉的**（不是漏抄）：

```java
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:list')")
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:add')")
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:remove')")
```

这 4 个端点（含 `mylist`）是首页九宫格的数据源，**普通用户**也在用；补上权限会让
他们白屏。唯一鉴权来自 `anyRequest().authenticated()`。

**回归用例** `tests/test_sys_index_menu_controller.py::TestPermissions`（含一条
`test_an_anonymous_delete_is_not_403`）。

### 34.5 `insertSysIndexMenu` 是"先物理删、后插"且**无事务** `[需注意]`

```java
for (String s : menuIdStr) {
    m.setMenuId(Long.parseLong(s));
    mapper.deleteByMenuUserId(m);   // delete from（物理）
    ... 四个审计列 ...
    mapper.insertSysIndexMenu(m);
}
```

两个风险，都是 Java 原样：

1. **无事务**（§28.3）。第 N 条插入失败时，前 N-1 条已生效，第 N 条的"删"也已生效 →
   库里会少一条收藏。
2. `deleteByMenuUserId` 是**物理**删除（全模块唯一一处），只比 `menu_id` + `user_id`。
   同一个人把同一个菜单选两次不会报错，但库里只要一行 —— 这是设计意图。

另外 `curDate` 在循环**外**取得，所以同一批的记录 `CREATE_TIME` 完全相同。`getList`
的 `order by t.CREATE_TIME desc` 在"一次选了很多个"时无法再细分先后。

**回归用例** `tests/test_sys_index_menu_service.py::TestInsertMenuIds`。

### 34.6 `menuIds` 只剥**一个**尾逗号；中间空段回 500 `[需注意]`

| 入参 | 结果 |
|---|---|
| `None` / `""` / `"   "` | **一行不写**，直接 `success` |
| `"100"` | 1 行 |
| `"100,"` | 1 行（剥一个尾逗号） |
| `"100,101,,"` | 2 行（只剥一个 → `split` 丢尾部空串） |
| `"100,,101"` | **500**（`Long.parseLong("")`） |
| `"abc"` | **500**（`Long.parseLong("abc")`） |

Java 的 `String.split` 只丢弃**尾部**空串，中间的空段会变成 `""` 进入 `parseLong`。
Python 侧用 `split_regex(value, ",", 0)` + `int(part)` 完全复刻（`ValueError`
落到与 `NumberFormatException` 同一个通用处理器）。

**回归用例** `tests/test_sys_index_menu_service.py::TestInsertMenuIds`。

### 34.7 软删除与物理删除**混用**；`count == 0` 仍 200 `[无影响]`

| 方法 | SQL | Java 侧调用方 |
|---|---|---|
| `deleteSysIndexMenuById` | `update ... set del_flag='1'` | **无**（照留） |
| `deleteSysIndexMenuByIds` | `update ... set del_flag='1'` | `remove` 端点 |
| `deleteByMenuUserId` | `delete from ...` | `insertSysIndexMenu` 内部 |

4 个 Service 方法直接返回 `AjaxResult`，用的是 `AjaxResult.success`
而**不是** `BaseController#toAjax`：

* `saveSysIndexMenu` → `success("操作成功！", id)`（**全角叹号**）
* `insertSysIndexMenu` → `success()`（不带 `data`）
* 两个删除 → `success(count)`，**`count == 0` 也是 200**

改成 `to_ajax` 会让"删一个不存在的 id"从 200 变 500 —— 这是本项目唯一刻意
**不**用 `toAjax` 的删除接口。

**回归用例** `tests/test_sys_index_menu_service.py::TestDelete`。

### 34.8 `SysIndexMenu` 的 JSON 里 `params` 是 `null` `[需注意]`

`SysIndexMenu extends BaseUuidEntity`，而 `BaseUuidEntity.params` **没有**
`@JsonInclude(NON_EMPTY)`（`BaseEntity.params` 有）。于是同样"没填 params"：

| 实体 | JSON |
|---|---|
| `SysConfig`（`BaseEntity`） | **没有** `params` 键 |
| `SysIndexMenu`（`BaseUuidEntity`） | `"params": null` |

前端的 `if (res.params)` 两种写法都能过，但逐字节比对或 `Object.keys()` 会不一样。

同时这个基类还带来 6 个客户端能看到的字段：`epsId` / `delFlag` / `deptSubCode` /
`tenantId` / `sort` / `flag`；`createBy` / `updateBy` 是 **数字**（用户 id）而不是用户名。

**回归用例** `tests/test_sys_index_menu_controller.py::TestGetInfo::test_params_is_serialized_as_null`。

### 34.9 `<if test="userId != 1">` 对 `null` **也成立** `[无影响]`

```xml
<if test="userId != 1 ">
  exists (select 1 from sys_role_menu rm, sys_user_role ur ... and ur.user_id = #{userId})
</if>
```

判据是 OGNL 的 `!=`（不是 `!= null`）：

| `userId` | 分支 |
|---|---|
| `1`（超管） | **不生效** → 所有人的候选菜单 |
| `null` | **生效** → `user_id = NULL` → `exists` 恒假 → 结果为空 |
| 其它 | 生效 → 只看自己有角色的菜单 |

Service 总会先 `setUserId(getUserId())`，正常路径不会是 `null`。写成
`if user_id is not None and user_id != 1` 是**错的** —— 与 §28.4 的"primitive 永不为
null"是同一类 OGNL 陷阱，方向相反。

**回归用例** `tests/test_sys_index_menu_mapper.py::TestSelectSysIndexMenuList`。

### 34.10 `getList` 自带 `order by create_time desc` + `limit 9` `[无影响]`

```sql
select t.id, t1.menu_name, concat(t2.path,'/',t1.path) as menuUrl
from SYS_INDEX_MENU t
left join sys_menu t1 on t.MENU_ID = t1.menu_id
left join sys_menu t2 on t1.parent_id = t2.menu_id
where t.del_flag='0' and t.USER_ID = :user_id
order by t.CREATE_TIME desc
limit 9
```

* 固定 9 条（前端九宫格），**不受**分页参数影响 —— 控制器也不调 `startPage()`；
* `menuUrl` 是 `父路径/子路径`（如 `system/user`），**没有**前导 `/`；父菜单为空时
  `concat` 返回 `NULL` → `menuUrl` 为 `null`（Java `CONCAT` 遇到 `NULL` 就是 `NULL`）；
* `del_flag='0'` 过滤的是**收藏记录**，不是菜单；菜单被删后靠 `left join` 留下空名字而不是消失。

**回归用例** `tests/test_sys_index_menu_mapper.py::TestGetList`。

### 34.11 `selectSysIndexMenuList` 自带 `order by` → 客户端排序**不生效** `[需注意]`

这条语句自带 `order by t2.parent_id,t2.order_num,t1.order_num,t1.menu_id`，所以
PageHelper **不会**追加客户端排序列（见 `page_helper._has_order_by`）。

对比：`sys_config` 的 `selectConfigList` **没有** `order by`，前端点表头排序是生效的。
两个模块在这一点上相反，不要当成 bug 去"修"。

另：这条语句的 `where` 与 `and` 都是**硬编码**的（没有 `<where>` 标签），所以 Python
拼接用的是 `"\nand ".join(conditions)` —— 与 `<where>` 模块的结果形态相同，但原因不同。

**回归用例** `tests/test_sys_index_menu_mapper.py::TestSelectSysIndexMenuList`。

---

## 35. `/system/upgradeInfo` 切片（Phase 3.16）`[需注意]`

> 本节覆盖 `SysUpgradeInfoController` + `SysUpgradeInfoServiceImpl` + `SysUpgradeInfoMapper`
> + 新增的 `parse_str_array` 这一整条竖切面。
> 对照表见 [MAPPING_SYS_UPGRADE_INFO.md](MAPPING_SYS_UPGRADE_INFO.md)。

### 35.1 整个控制器**零权限点** `[无影响]`

Java 源码里 `SysUpgradeInfoController` **一个 `@PreAuthorize` 都没有** —— 不是被注释掉，
是本来就没写（对比 `sys_index_menu` 的"部分被注释"）。

所以本模块的鉴权强度只有 `SecurityConfig` 的 `anyRequest().authenticated()`：**登录即可**，
不查任何权限字符串。

**不要"顺手补上"**。这组端点是首页/登录后的升级公告弹窗的数据源，补权限会让没有
"系统升级信息"菜单的普通用户看不到公告。

**回归用例** `tests/test_sys_upgrade_info_controller.py::TestPermissions`
（含 `inspect.getsource` 断言：源码里不出现 `pre_authorize_permi`）。

### 35.2 `export` 未迁移，但在这个模块**不会**回 500 `[需注意]`

这是全项目唯一的例外，值得单独记住。

| 模块 | `getInfo` 的路径变量类型 | `GET .../export` 的结果 |
|---|---|---|
| `sys_config` | `Long` | `int("export")` 失败 → **HTTP 200 + code 500** |
| `sys_dict/*` | `Long` | 同上 |
| `sys_indexmenu` | `Long` | 同上 |
| **`sys_upgrade_info`** | **`String`**（主键是 UUID） | 走进 `get_info("export")` → 查不到 → **HTTP 200 + code 200，`data` 键消失** |

Java 下这里返回的是 `ExcelUtil.exportExcel` 的信封（`{"code":200,"msg":"操作成功",
"data":{"fileName":...}}`，文件本身走 response 下载）。**状态码相同，信封不同** ——
前端如果读 `data.fileName` 会拿到 `undefined`，不会崩，但也不会下载。

等 `ExcelUtil` 迁移完成（见 MIGRATION_PROGRESS §4）时，这条路由会覆盖掉 `/{id}` 的兜底，
行为自然对齐。

**回归用例** `tests/test_sys_upgrade_info_controller.py::TestRouteTable::test_export_falls_into_the_string_path_variable`。

### 35.3 `@Log` 未迁移 → 不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，本控制器的 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

Java 的 `add` / `edit` / `remove` 都带 `@Log(title = "系统升级信息", businessType = ...)`。
Python 侧操作日志切面未迁移，这三类操作**不落审计表**。业务结果不受影响。

与 §33.3 / §34.3 同一个缺口，审计需求上线前统一补。

### 35.4 `list` 在**控制器**里盖 `tenantId` `[无影响]`

```java
// SysUpgradeInfoController
startPage();
sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
```

客户端传 `?tenantId=999` 会被登录上下文覆盖。三个后果：

* 用户只能看到自己租户的公告（这是本意）；
* SQL 的 `<if test="tenantId != null">` 因此**总是**生效；
* 登录用户的 `tenantId` 为 `null` 时覆盖成 `null`，条件**不生效** → 能看到所有租户的公告。

与 `sys_index_menu` 把"覆盖"放在 **Service** 里不同：本模块 Service 是纯转发。位置差异
是照抄 Java 的结果。

**回归用例** `tests/test_sys_upgrade_info_controller.py::TestList`。

### 35.5 新增时**多盖**一个 `tenantId` `[需注意]`

两个模块同样是 `extends BaseUuidEntity`、同样"有 id 就改、没 id 就新增"，但
`SysUpgradeInfoServiceImpl.saveSysUpgradeInfo` 在新增分支里**多一行**：

```java
sysUpgradeInfo.setEpsId(SecurityUtils.getEpsId());
sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId());   // <- SysIndexMenu 没有这行
```

漏掉不会报错，后果是：新插入的公告 `tenant_id` 为 `NULL`，而列表查询按 `tenant_id` 等值
过滤 —— 同租户的其他人**看不到**这条公告，只有该用户自己的查询（同样 `tenant_id = NULL`）
…… 也看不到（`<if>` 只在非空时生效，`NULL` 等于不过滤，所以实际上是"所有人可见"）。

无论哪种，都是错的。测试把这一行钉在
`tests/test_sys_upgrade_info_service.py::TestSave::test_the_insert_branch_stamps_the_tenant`。

### 35.6 `selectSysUpgradeInfoById` **没有** `del_flag` 过滤 `[需注意]`

```sql
select <include refid="selectSysUpgradeInfoVo"/> from sys_upgrade_info t where t.id = #{id}
```

与列表（始终带 `del_flag = '0'`）**不对称**：被软删除的记录仍能按 id 查到。

影响：`GET /system/upgradeInfo/{已删除的id}` 返回**整条记录**而不是空信封。前端如果用它
做详情页，能看到"已删除"的公告。照抄 Java，不修。

**回归用例** `tests/test_sys_upgrade_info_mapper.py::TestSelectById::test_there_is_no_del_flag_filter`。

### 35.7 `newest` 的两个"照抄"陷阱 `[无影响]`

```sql
select <include refid="selectSysUpgradeInfoVo"/>
from sys_upgrade_info t
where t.del_flag = '0' and t.back_col1 = 1
ORDER BY t.UPDATE_TIME desc LIMIT 1
```

1. **SQL 完全无视入参**：Java 声明了 `SysUpgradeInfo sysUpgradeInfo`，但语句里没有一个
   `#{...}`。传 `?ver=9.9.9` 与不传结果完全相同。前端如果以为能"按版本查"就是误解。
2. **`varchar` 与数字比较**：`back_col1` 是字符串列，却写 `= 1`（MySQL 隐式转换）。
   效果是只有值恰好为 `"1"`（或 `" 1"` / `"1 "` 这类能转成 1 的）的行参选；`"0"` / `""` /
   `NULL` 全部被排除。

另外它用的是 `resultType` 而不是 `resultMap` —— 靠 `mapUnderscoreToCamelCase` 自动映射，
11 个属性名与列名一一对得上，结果与 `resultMap` 相同。

**回归用例** `tests/test_sys_upgrade_info_mapper.py::TestSelectNewest`。

### 35.8 `remove` 是 `String[]`，不是 `Long[]` `[无影响]`

```java
@DeleteMapping("/{ids}")
public AjaxResult remove(@PathVariable String[] ids)
```

其它模块都是 `Long[]`，本模块是 `String[]`（主键 UUID 字符串）。Python 为此新增了
`base_controller.parse_str_array`：逗号切分、**不做** `int` 转换。

| 输入 | 结果 | 若误用 `parse_id_array` |
|---|---|---|
| `1d3f0b9c…`（UUID） | `["1d3f0b9c…"]` | 500 |
| `u-1,u-2` | `["u-1", "u-2"]` | 500 |
| `u-1,,u-2` | `["u-1", "", "u-2"]` | 500 |

即：**用错助手，所有删除请求都会 500**。这是本切片最容易犯的错。

**回归用例** `tests/test_sys_upgrade_info_controller.py::TestRemove`。

### 35.9 列表 SQL 自带 `order by` → 客户端排序**不生效** `[需注意]`

`selectSysUpgradeInfoList` 以 `order by t.create_time desc,t.id` 结尾，所以
PageHelper 不会追加 `orderByColumn`。前端点表头排序对这张表无效。

三个模块在这点上一致（`sys_index_menu` / 本模块）或相反（`sys_config` 有、`sys_notice`
无），**不要统一**。

另外这条语句的 `where` 与 7 个 `and` 都是**硬编码**的（没有 `<where>` 标签），所以 Python
拼接统一用 `"and "` 连接 —— 与 `<where>` 模块的结果形态相同，但原因不同。

**回归用例** `tests/test_sys_upgrade_info_mapper.py::TestSelectList`。

### 35.10 两条 `delete` 都是软删除；`deleteSysUpgradeInfoById` 无调用方 `[无影响]`

```sql
update sys_upgrade_info set del_flag = '1' where id = ?
update sys_upgrade_info set del_flag = '1' where id in (?, ?)
```

整个 XML 里**没有** `delete from`。

`ISysUpgradeInfoService#deleteSysUpgradeInfoById` 在接口与实现里都有，但**控制器只调
`ByIds`** —— 按迁移原则第 4 条照留、照写测试、并在 docstring 里标注"孤儿方法"。

两个方法都返回 `AjaxResult.success(count)`（不是 `toAjax`），所以 `count == 0` 也是 `200`。

**回归用例** `tests/test_sys_upgrade_info_service.py::TestDelete`、
`tests/test_sys_upgrade_info_mapper.py::TestDelete`。

### 35.11 `add` / `edit` 零校验注解 `[无影响]`

两个端点只写了 `@RequestBody`，没有 `@Validated`，实体上也没有任何 constraint 注解。

后果：

* `POST {}` 会被接受 → Service 走新增分支，插一条只有审计列和 UUID 的空记录；
* `PUT {"ver": "1.2.4"}`（没有 `id`）**不会报错**，Service 会当成**新增**再插一条；
* 字段长度/非空全部由数据库决定，超长会抛 SQL 异常 → `code 500`。

本模块因此**不建** `*_CONSTRAINTS` 表（对比 `sys_config` / `sys_user`）。

**回归用例** `tests/test_sys_upgrade_info_controller.py::TestAddAndEdit`。

## 36. `/system/file` 切片（Phase 3.17）`[需注意]`

> 本节覆盖 `SysFileController` + `SysFileServiceImpl` + `SysFileMapper` + 新增的
> `ResponseSink` 这一整条竖切面（文件管理 / OSS）。
> 对照表见 [MAPPING_SYS_FILE.md](MAPPING_SYS_FILE.md)。
>
> 本切片是 Phase 3 里**依赖最重**的一个：24 个 service 方法、17 个端点、
> OSS 客户端、雪花 id、Forest 下载客户端全都用上了。

### 36.1 曾把非法 base64 上传成 0 字节对象（**已修复**）`[无影响]`

这是本切片发现的**唯一一个真实缺陷**，值得单独记住。

```java
// Java: SysFileServiceImpl#uploadBase64Picture
byte[] decode = new BASE64Decoder().decodeBuffer(base64Picture);
...
ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(decode);
```

`decodeBuffer` 遇到非法输入返回 `null`，`new ByteArrayInputStream(null)` 抛 NPE →
落到 `catch` → `AjaxResult.error()`（`{"code":500,"msg":"操作失败"}`）。

但 CPython 的 `BytesIO(None)` **等价于空缓冲区、不会报错**。直译的结果是：

| 入参 | Java | 直译后的 Python（错） | 修复后 |
|---|---|---|---|
| 合法 base64 | 上传成功 | 上传成功 | 上传成功 |
| `"not-base64"` | `code 500` | **`code 200`，OSS 里多一个 0 字节对象 + 一条库记录** | `code 500` |

修复方式是在 `try` 里显式判空：

```python
if decoded is None:
    raise ValueError("Base64 解码结果为空")
```

**回归用例** `tests/test_sys_file_service.py::TestBase64Picture::test_a_malformed_base64_falls_into_the_error_branch`。

### 36.2 `@Log` 未迁移 → 文件管理不写 `sys_oper_log` `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，本控制器的 10 处 `@Log` 全部生效。
> 下面"不留审计记录"的结论**已失效**，原文保留只为留下变更轨迹，请以 §42.9 为准。

Java 的 10 个写操作带 `@Log`：

| 端点 | `title` | `businessType` |
|---|---|---|
| `upload` / `uploadByUrl` / `uploadSupplier` / `uploadPdf` / `uploadFileId` / `uploadFileEnc` / `uploadFile` | `文件` | `INSERT` |
| `removeById` / `remove` | `文件` | `DELETE` |
| `updateCAFile` | `文件` | `UPDATE` |
| `edit` | **`文件管理`** | `UPDATE` |

Python 侧操作日志切面未迁移，上述操作**不落审计表**。业务结果不受影响。

注意 `edit` 的 `title` 是 `文件管理`，其余 9 个是 `文件` —— 补 `LogAspect` 时别统一。

与 §33.3 / §34.3 / §35.3 同一个缺口，审计需求上线前统一补。

### 36.3 只有 2 个权限点，且都“抄错”了 `[无影响]`

| 端点 | 权限串 | 问题 |
|---|---|---|
| `GET /system/file/list` | `base:sysflie:list` | **拼写错**（`sysflie`，不是 `sysfile`） |
| `DELETE /system/file/{ids}` | `base:supplier:remove` | 借用了**供应商**模块的权限点 |

其余 15 个端点**登录即可**（靠 `anyRequest().authenticated()`）。

**不要修正拼写**：`sys_menu` 表里那条菜单的 `perms` 也是 `base:sysflie:list`，
改成 `sysfile` 会让文件列表**直接 403**（用户却拥有权限）。

`remove` 借用供应商的权限点也是 Java 原样 —— 它本来就是为了删供应商附件而加的。

**回归用例** `tests/test_sys_file_controller.py::TestPermissions`
（含反向用例：只有 `sysflie` 能过，`sysfile` 反而 403）。

### 36.4 文件下载失败是 **HTTP 200 + 空 body**，不是 404 `[需注意]`

两条 `void` 路由（`/{bucket}/{fileName}` 与 `/view/{bucket}/{fileName}`）：

```java
public void file(String bucket, String fileName, HttpServletResponse response) {
    sysFileService.getFile(bucket, fileName, response);
}
```

`getFile` 内部 `catch (Exception e) { /* 连日志都被注释掉了 */ }`，所以：

| 场景 | HTTP | `Content-Type` | body |
|---|---|---|---|
| OSS 正常 | 200 | `application/octet-stream; charset=UTF-8` | 对象字节 |
| 对象不存在 / OSS 报错 / 未装 boto3 | **200** | **不发** | **空** |

客户端如果靠状态码判断“文件在不在”会永远得到“在”。这是 Java 原行为。

Python 用 `ResponseSink` 攒字节，再由 `_to_response()` 决定发不发 `Content-Type` ——
连“异常路径不带 `Content-Type`”都对齐了。

> 副作用：`test_security_filter.py` 里原本拿 `/system/file/view/a.jpg` 当
> “无控制器”探针，现在会回 **200 + 空 body**（`bucket = "view"`，与 Spring 的
> `AntPathMatcher` 同样的匹配）。那条断言已随之改成 200。

**回归用例** `tests/test_sys_file_controller.py::TestDownload`。

### 36.5 `getInfo` 用 `-111111` 兜住空 ids `[无影响]`

```java
ids = CommonUtil.deleteEnd(ids);
if (CommonUtil.isBlank(ids)) { ids = "-111111"; }
```

`deleteEnd` 只删**一个**结尾逗号；删完为空白就换成 `-111111`。它**不是合法主键**，
`in ('-111111')` 必然查空 —— 目的只是避开 `in ()` 的 SQL 语法错误。

| 入参 | 之后 | |
|---|---|---|
| `"1,"` | `""` → `-111111` | 回空数组 |
| `"1,2,,"` | `"1,2,"` | Service 切出 `["1","2",""]` |

Service 的 `ids.split(",")` **不 trim、不过滤空串**，所以尾部空段会变成 `in (...,'')`。

### 36.6 `uploadFileId` 的 `AjaxResult.error` 被**丢弃** `[无影响]`

```java
if (CommonUtil.isNull(sysFile.getId()).equals("")) {
    AjaxResult.error("主键不能为空");   // 没有 return，也没有 throw
}
```

返回值没人接。所以 `id` 为空时**照样往下走**：解 base64 → `fileLogId` →
`deleteSysFileByIdNew(null)`（异常被吞）→ 插一条 `id = NULL` 的记录 →
结果里 `"id": "null"`。

**不要补 `return`**，补了就变成“回 500 且不落库”，是行为改变。

### 36.7 微信上传：扩展名**区分大小写** + **子串**匹配 `[需注意]`

```java
if (ext.indexOf("jpg") > -1 || ext.indexOf("jpeg") > -1
        || ext.indexOf("png") > -1 || ext.indexOf("gif") > -1) { } else { return error(...); }
if (file.getSize() > 1024 * 1024 * 15) { return error(...); }
```

| 细节 | 后果 |
|---|---|
| **没有** `toLowerCase()` | `.JPG` / `.Png` 一律被拒 |
| `indexOf` 是**子串**匹配 | `.mjpg` / `.pngx` 也能过 |
| 上限 `1024 * 1024 * 15` | 15M，超过回 `上传失败,你上传的附件大于15M！` |
| 两条文案不同 | `上传失败,请上传照片格式的附件！` / `上传失败,你上传的附件大于15M！` |

两个文案的逗号都是**半角**（前端按键文案分支，别看错）。

**回归用例** `tests/test_sys_file_controller.py::TestWechatUpload`。

### 36.8 `selectSysFileById` **没有** `del_flag` 过滤 `[需注意]`

```sql
select <include refid="selectSysFileVo"/> from sys_file t where t.id = #{id}
```

列表始终带 `del_flag = '0'`，按 id 查不带 —— 被软删除的文件按 id **仍能查到**。
影响 `GET /system/file/getInfoById/{已删除的id}`：回整条记录而不是空信封。

### 36.9 列表自带 `order by` → 客户端排序**不生效** `[需注意]`

`selectSysFileList` 以 `order by t.create_time desc,t.id` 结尾，PageHelper 不会追加
客户端的 `orderByColumn`。前端点表头排序对这张表无效。

与 §32（`sys_dict` 无自带排序）相反，与 §35.9 同类。**不要统一**。

另外 `where t.del_flag = '0'` 与 11 个 `and` 都是**硬编码**的（没有 `<where>` 标签）。
Python 侧的条件片段**不带前导 `AND`**，且**顺序与 XML 逐字一致**，所以拼出的 SQL 与
MyBatis 的输出可以直接 diff。

### 36.10 两条软删 + 一条**物理**删；`updateCAFile` 把主键写死成 3001 `[需注意]`

```sql
update sys_file set del_flag = '1' where id = :id          -- deleteSysFileById
update sys_file set del_flag = '1' where id in (:p0, :p1)  -- deleteSysFileByIds
delete from  sys_file  where id = :id                      -- deleteSysFileByIdNew
```

`deleteSysFileByIdNew` 是本模块**唯一**的硬删除，两个调用点：

1. `fileLogId`（`uploadFileId` 的“先删后插”）；
2. `updateCAFile` —— 先把 `id = 3001` 的旧记录物理删掉（连同 OSS 对象），再把本条
   的主键**改成 3001**（CA 驱动程序固定占这个主键）。

`updateCAFile` 返回的 `data` 是**改之前**的那个 `id`，不是 `3001`。

另：`deleteSysFileByIdNew` 是**实现类私有方法**（不在 `ISysFileService` 接口里），
异常全部吞掉、不回任何东西。

### 36.11 `uploadFilesUser` 不写 `del_flag` → 列表里**查不到** `[无影响]`

`fileLogUser` 直接调 `insertSysFile`，绕过了 `saveSysFile`，所以插入的行 `del_flag` 是
**NULL**。`selectSysFileList` 过滤 `del_flag = '0'` → 这些记录**在列表里查不到**
（按 id 仍能查到）。

`uploadFilesUser` 目前**没有控制器调用**，但按原则第 4 条照留、照写测试。

### 36.12 `uploadBase64Picture` 把文件 id 放在 **`msg`** 里 `[需注意]`

```java
String fileId = String.valueOf(ajaxResult.get(DATA_TAG));
return AjaxResult.success(fileId);      // 挑中了 success(String msg)
```

`fileId` 是 `String`，Java 重载解析挑的是 `success(String msg)` 而**不是**
`success(Object data)`。所以返回体是：

```json
{"code": 200, "msg": "<文件id>"}
```

**没有 `data` 键**。前端如果读 `data` 会拿到 `undefined`。

本端点当前**没有映射**（无控制器调用），但 service 方法公开可用，别的模块可能在用。
别“修正”成 `success_data` —— 富文本那半边读的就是 `MSG_TAG`。

### 36.13 `uploadPdf` 对非 pdf **只写本地临时文件** `[需注意]`

```java
if (ext != null && ext.equals("pdf")) { /* 登记 + putObject */ }
else { /* Word->PDF 转换整块被注释；只往本地临时目录写一个文件 */ }
```

后果：

* 判据是 `equals("pdf")` —— **区分大小写**，`.PDF` 走 else；
* else 分支**不写库、不上传**，只把字节落到
  `{ruoyi.uploadPath}/{uuid}/{fileName}`，结果里**没有 `id` 键**；
* 那些临时文件**永远不会被清理** —— 磁盘会持续长。运维需要定期清 `uploadPath`。

Java 的 `HttpServletResponse response` 参数从没被写过（`out` 被下一行覆盖），
所以 Python 侧直接传 `None`。

### 36.14 `uploadFileEnc` / `getFileUrl` 是**空实现** `[无影响]`

| 方法 | Java 原样 | 返回 |
|---|---|---|
| `uploadFilesEnc` | 方法体**整块被注释**，只剩空循环 | 永远 `{"code":200,"data":[]}` |
| `getFileUrl` | 方法体被注释 | 永远 `null` |
| `uploadBase64Picture(String)` | 方法体被注释 | 空白原样返回，其余 `""` |
| `uploadFile(InputStream, SysFile)` | 方法体被注释 | 只返回**新生成的**雪花 id（不写库、不上传！） |

`uploadFileEnc` 看起来像“加密上传”，实际什么都不做 —— 前端拿到空数组也当成功。
`uploadFileFromStream` 更危险：它“看起来成功”但什么都没发生。

四个方法都按原则第 4 条照留，并在 docstring 里标注“死代码”。

### 36.15 删除失败的 `msg` 文案与 Java 不同 `[需注意]`

```java
catch (Exception ex) { return AjaxResult.error(ex.getMessage()); }
```

删一个不存在的 id 时，`file.getFileName()` 抛 NPE，Java 的 `getMessage()` 返回 `null`，
响应是 `{"code":500,"msg":null}`。

Python 抛 `AttributeError`，`_message_of` 取到的是
`"'NoneType' object has no attribute 'file_name'"` —— **同一位置、不同文案**。

客户端如果只判 `code` 不受影响；如果把 `msg` 直接展示给用户，会说“英文”。

两个删除方法（单个 / 批量）都是这个形态。

### 36.16 `SysFile.id` 在 JSON 里是**字符串** `[无影响]`

```java
@JsonSerialize(using = ToStringSerializer.class)
private Long id;
```

19 位雪花 id 超过 JS 的 `Number.MAX_SAFE_INTEGER`（16 位），发数字前端会丢精度。
**这是线上契约**：`"id": "1234567890123456789"`。

Python 内部仍是 `int`（要参与 SQL 的 id 比较），只在 `field_serializer` 里转 `str`。

注意 `SysFile` **不继承** `BaseEntity`（裸 POJO），所以：没有 `searchValue` / `remark` /
`params` 三件套；审计列是 `String`（`createUser` / `updateUser`），不是 `Long`。

**回归用例** `tests/test_sys_file_controller.py::TestGetInfo`（断言 `data[0]["id"] == "9"`）。

---

## 37. `ExcelUtil` 切片（Phase 3.18）`[需注意]`

> 本节覆盖 `ExcelUtil`（1797 行 POI 工具类）+ `@Excel` / `@Excels` 注解 +
> **8 个 `export` 端点** + `SysUser` 的导入两连。
> 对照表见 [MAPPING_EXCEL_UTIL.md](MAPPING_EXCEL_UTIL.md)。
>
> 这是**补齐历史欠账**的一节：§25.1 / §26.1 / §28.1 / §32.2 / §33.2 / §34.2 / §35.2
> 里八处“`export` 未迁移”的缺口在本阶段全部关闭。

### 37.1 八个 `export` 端点上线：**从 500 变成 200** `[需注意]`

这是客户端能直接看到的**行为变化**，不是对齐 Java —— 而是**补回 Java 本来就有的东西**。

| 端点 | 补之前 | 补之后 |
|---|---|---|
| `GET /system/user/export` | 被 `GET /system/user/{user_id}` 兜住 → **500** | `200` + `{"code":200,"msg":"<uuid>_用户数据.xlsx"}` |
| `GET /system/post/export` | 同上 → **500** | 同上（`_岗位数据.xlsx`） |
| `GET /system/role/export` | 同上 → **500** | 同上（`_角色数据.xlsx`） |
| `GET /system/dict/type/export` | 同上 → **500** | 同上（`_字典类型.xlsx`） |
| `GET /system/dict/data/export` | 同上 → **500** | 同上（`_字典数据.xlsx`） |
| `GET /system/config/export` | 同上 → **500** | 同上（`_参数数据.xlsx`） |
| `GET /system/indexmenu/export` | 同上 → **500** | 同上（`_常用菜单.xlsx`） |
| `GET /system/upgradeInfo/export` | 被 `String` 的 `/{id}` 兜住 → **200 但无 `data`** | `200` + `msg` 里是文件名（`_升级信息.xlsx`） |

如果监控/压测脚本把“`export` 回 500”当成已知现状，需要同步更新。

### 37.2 导出返回的是**文件名**，不是文件 `[需注意]`

```java
return AjaxResult.success(filename);   // filename 是 String
```

Java 的重载决议挑 `success(String msg)` 而**不是** `success(Object data)`。所以：

```json
{"code": 200, "msg": "3f2b...-..._用户数据.xlsx"}
```

**没有 `data` 键**。前端必须拿 `msg` 去请求 `GET /common/download?fileName=<msg>` 才能
下载到内容（两个端点的配合见 §38）。

Python 侧用的是 `AjaxResult.success_message(...)`。
**回归用例** `tests/test_excel_util.py::TestExportToFile::test_returns_the_filename_in_msg_not_data`
+ `tests/test_sys_config_controller.py::TestRouteTable::test_export_returns_the_filename_in_msg`。

### 37.3 文件落在 `{profile}/download/`，且**永不自动清理** `[需注意]`

```java
public static String getAbsoluteFile(String filename) {
    String downloadPath = RuoYiConfig.getDownloadPath() + filename;   // {profile}/download/ + 名字
    File desc = new File(downloadPath);
    if (!desc.getParentFile().exists()) { desc.getParentFile().mkdirs(); }
    return downloadPath;
}
```

后果：

* 每点一次“导出”就多一个 xlsx，磁盘会持续长；
* 文件名是 `UUID`，**不可预测**，所以没法“先导出再按名字找文件” —— 只能顺着 `msg` 走；
* 没有定时清理任务（Java 也没有）。运维需要自己加 cron 清 `{profile}/download/`。

### 37.4 `.xls` 不能导入（`.xlsx` 才能）`[需注意]`

| | Java | Python |
|---|---|---|
| 读 `WorkbookFactory.create(InputStream)` | `.xls`（HSSF）+ `.xlsx`（XSSF）都行 | `load_workbook` **只认** `.xlsx` / `.xlsm` |

`.xls` 会抛 `InvalidFileException`，被包成 `UtilException`，前端拿 `code 500`。
正常流程（模板从 `GET /system/user/importTemplate` 下载）不受影响；
**手工另存为 `.xls` 再上传就会失败**。

### 37.5 公式单元格依赖“缓存值” `[需注意]`

Python 用 `load_workbook(..., data_only=True)`：读到的是**上次 Excel 保存时算好的缓存值**。
如果文件是用程序生成的、从没在 Excel 里打开过，公式单元格读出来是 `None`。

Java 的 `cell.getCellType() == FORMULA` 分支拿的也是 POI 缓存的公式结果，行为一致。

### 37.6 `SXSSFWorkbook(500)` → 内存 `Workbook` `[无影响]`

POI 的流式工作簿把超过 500 行的部分刷到临时文件；openpyxl 全程在内存。
**输出字节语义等价**（都是 xlsx），差别只在内存占用与临时文件。
本项目最大导出量（用户表）远不到需要流式。

### 37.7 `ColumnType.IMAGE` 未迁移，且**会显式报错** `[无影响]`

POI 的 `addPicture` / 读图那套没有迁。本工程**没有任何**字段声明 `cellType = IMAGE`
（已全量搜过），所以是休眠代码。

导出分支留的是 `raise NotImplementedError("ColumnType.IMAGE 未迁移（无调用点）")`，
由 `add_cell` 的 `except Exception` 吞掉 —— 效果是“单元格有样式、没值”。
**这是故意的**：将来有人给字段加上 `IMAGE` 时，日志里会立刻出现一条 `导出Excel失败`，
而不是静默出一张没图的表。

### 37.8 `SysUpgradeInfo` 导出的是**零列空表** `[无影响]`

`SysUpgradeInfo` 一个 `@Excel` 都没有，`getFields()` 返回空列表，于是导出的是
一个只有 sheet 名、一列都没有的空工作簿。Java 一样。

`GET /system/upgradeInfo/export` 现在真的能下到这样一个文件 —— 不要当 bug 修。
**回归用例** `tests/test_excel_util.py::TestColumnTables::test_sys_upgrade_info_has_no_annotation_at_all`。

### 37.9 `showDropDown` 在 openpyxl 里语义**相反** `[无影响]`

OOXML 的属性名叫 `showDropDown`，含义却是“**隐藏**下拉箭头”：

| | 想让箭头显示 |
|---|---|
| POI | `setSuppressDropDownArrow(false)`（取反） |
| openpyxl | `validation.showDropDown = False`（取反） |

`set_prompt_or_validation` 里写的是 `False`。**别“顺手”改成 `True`**，那会让所有下拉框
消失。

### 37.10 `setDefaultColumnStyle` 没有对应物 `[无影响]`

Java 在子列表场景下调 `sheet.setDefaultColumnStyle(column, dataStyle)`；openpyxl 没有
“列默认样式”这个概念，等价效果由 `fill_excel_data` 里的 `add_cell` 逐格设置补齐。
**子列表场景本身是休眠代码**（本工程 `_sub_fields` 永远是 `None`），所以只在纸面上有差异。

### 37.11 导入的 `Integer` / `Long` 统一按 `to_long` `[无影响]`

Java 用 `field.getType()` 分派，`Integer` 走 `toInt`、`Long` 走 `toLong`。
Python 的 `int` 不分这两者，统一用值域更大的 `to_long`。

本项目所有带 `@Excel` 的整型字段在 Java 里都是 `Long`，不存在“`int` 字段被放宽”的情形。

### 37.12 `sort` 默认值不是“未排序”，而是 `Integer.MAX_VALUE` `[无影响]`

`@Excel(sort = Integer.MAX_VALUE)` 的默认值 + `Stream.sorted` **稳定** → 没写 `sort`
的字段保持“父类字段在前、本类声明顺序在后”。

Python 里是 `UNSORTED = sys.maxsize`，`fields.sort(key=...)` 也是稳定排序。
**改排序实现时不能换成非稳定排序**，否则用户表的 21 列会乱序。

---

## 38. `/common` + `/downTemplate` 切片（Phase 3.19）`[需注意]`

> 本节覆盖 `CommonController`（4 个端点）+ `DownTemplateController`（1 个）+
> `FileUtils` + `FileTypeUtils` + `ServerConfig` + 7 个 xlsx 模板。
> 对照表见 [MAPPING_COMMON.md](MAPPING_COMMON.md)。
>
> 本切片是 §37 的**下游**：`export` 只返回文件名，真正的字节靠 `GET /common/download`。

### 38.1 `GET /common/download` 是 `anonymous()`：**已登录反而 403** `[需注意]`

```java
.antMatchers("/common/download**").anonymous()
```

`anonymous()` 是“**只**允许匿名”，不是“允许匿名”。已登录（带有效 token）的请求会拿到
**真实 403** + Spring 的 `BasicErrorController` 错误体。

前端如果统一给所有请求塞 token，下载就会失败。要么这一处不带 token，要么把规则改成
`permitAll()` —— **但那就是行为改变**，需要业务确认。

同类问题见 §31.4（`/system/notice/view/**`）。

### 38.2 `GET /common/download/resource` **没有**被上一条规则遮蔽 `[需注意]`

这一条值得单独写，因为**很容易误判**（本项目的实现曾按“被遮蔽”写过，后来推翻）。

```java
.antMatchers("/common/download**").anonymous()
.antMatchers("/common/download/resource**").authenticated()
```

`AntPathMatcher` 先按 `/` 切段：

| | 切出来 |
|---|---|
| `/common/download**` | `["common", "download**"]` |
| `/common/download/resource` | `["common", "download", "resource"]` |

第二段 `download**` 确实能匹配 `download`，但此时**路径还有剩余段、模式已经用完**，
`doMatch` 直接 `return false`。所以 `authenticated()` 那条**真的生效**。

> 这与 §20 的“静态资源规则遮蔽 `denyAll`”**不是同一类问题**：
> 那是规则**排序**（`/**` 写在了前面），这里是规则**形状**。

**回归用例** `tests/test_common_controller.py::TestSecurityRules::test_download_resource_is_not_shadowed_by_the_earlier_pattern`。

### 38.3 缺 `fileName` / `delete` **不是 400**，而是“异常被吞 → 200” `[需注意]`

Spring 对**没有注解**的简单类型参数用 `RequestParamNamedValueInfo()`，其 `required`
默认是 **`false`** —— 所以这两个参数都是可选的：

| 缺什么 | 客户端看到 | 副作用 |
|---|---|---|
| `fileName` | **200 + 空 body** + 无 `Content-Disposition` | 日志里一条 `下载文件失败` |
| `delete` | **200 + 完整内容**（文件照下） | 磁盘上的文件**不删**（`if (delete)` 拆箱 NPE） |

第二条尤其阴险：功能“看起来正常”，但每下一次就留一个文件，磁盘慢慢满。

### 38.4 文件不存在是 **200 + 完整响应头 + 空 body**，不是 404 `[需注意]`

`FileUtils.writeBytes` 抛 `FileNotFoundException`，但它在 `finally` 里**已经关掉了
输出流** —— servlet 世界里“关流 = 提交响应”。所以客户端拿到的是：

```
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Disposition: attachment; filename=...
download-filename: ...
Content-Length: 0
```

**判“下载是否成功”只能看 body 长度，不能看状态码。**

Python 侧用 `_CloseTolerantStream` 复刻这个语义（`close()` 只置位、不销毁 `BytesIO`），
否则 FastAPI 在函数返回后取不到 body，会变成真实 500。

### 38.5 真实文件名会**吃掉**第一个 `_` 之前的部分 `[无影响]`

```java
String realFileName = System.currentTimeMillis() + fileName.substring(fileName.indexOf("_") + 1);
```

| `fileName` | `download-filename` |
|---|---|
| `export_用户数据.xlsx` | `<毫秒>用户数据.xlsx`（**`_` 没了**） |
| `a.png`（没有 `_`） | `<毫秒>a.png`（`indexOf` 返回 `-1`，`substring(0)` 是整串，**不抛异常**） |

导出接口生成的文件名是 `<uuid>_<sheetName>.xlsx`，uuid 里**没有**下划线（`uuid4()` 带连字符），
所以去掉的正好是 uuid，用户看到的是干净的中文名。这是设计意图，不是 bug。

### 38.6 `delete` 传非法值是 `code 500`，且必须用 `ServiceException` `[需注意]`

Spring 的 `StringToBooleanConverter` 真值集是 `{true,on,yes,1}`、假值集是
`{false,off,no,0}`，其它值抛 `MethodArgumentTypeMismatchException` →
`GlobalExceptionHandler` 的中文文案：

```
请求参数类型不匹配，参数[delete]要求类型为：'java.lang.Boolean'，但输入值为：'maybe'
```

Python 的 `_spring_boolean` **必须**抛 `ServiceException`（`RuntimeError` 子类），
不能抛 `ValueError`：

> `@app.exception_handler(Exception)` 挂在 `ServerErrorMiddleware` 上，响应发完还会
> **重新抛**，在 `TestClient` 下表现为测试直接炸而不是回信封。
> 详见 §25.3。

### 38.7 下载白名单**不区分大小写**，上传那边**区分** `[需注意]`

| | 判据 | 大小写 |
|---|---|---|
| 下载 `checkAllowDownload` | `FileTypeUtils.getFileType` → **`toLowerCase()`** | **不区分**（`A.PNG` 能过） |
| 上传 `MimeTypeUtils.getExtension` | `contains(extension)` 即**子串**匹配 | **区分**（`a.JPG` 被拒） |

两套规则**是两套**，别互相参照。下载白名单共 **22** 项：
`bmp gif jpg jpeg png doc docx xls xlsx ppt pptx html htm txt rar zip gz bz2 mp4 avi rmvb pdf`。

另外 `checkAllowDownload` 第一道闸是 `contains(resource, "..")` —— `a..png` 这种
“文件名里带两个点”也会被拒。

### 38.8 `GET /downTemplate/{type}` 未知 `type` 是 **200 空 body + 零响应头** `[需注意]`

Java 的 `url` 停在初值 `"templates/down"` —— 那是个**目录**，`TemplateExportParams`
加载失败 → `catch` 里 `printStackTrace` → `return null`。

由于 `setContentType` / `setHeader` 都写在 `try` 里、在异常点**之后**，所以失败的响应
**一个头都没有**（连 `Content-Type` 都没有）。

| 场景 | 状态码 | body | 响应头 |
|---|---|---|---|
| 已知 `type` | 200 | 模板原始字节 | `Content-Type: application/octet-stream;charset=UTF-8`<br>`Content-Disposition: attachment` |
| 未知 `type` | 200 | **空** | **零个** |

### 38.9 `Content-Disposition: attachment` **没有 filename** `[需注意]`

```java
response.setHeader("Content-Disposition", "attachment");
```

写死的两个字。浏览器会用 url 最后一段（即 `type`）当文件名，所以下载下来叫
`carinfo`（**没有 `.xlsx` 后缀**）。这是 Java 原样，改了就与线上不一致。

### 38.10 模板是**原始字节直出**，不经 openpyxl `[无影响]`

Java 走 easypoi `TemplateExportParams(url, true)` + 空 `HashMap` 渲染。
**这 7 个模板里没有任何 `${...}` 占位符**（已逐格核对），所以“渲染”等于“原样输出”。

Python 因此直接读文件字节返回。若改成 openpyxl 重写，会**丢掉**：

* 数据校验（下拉框）；
* 表单控件 / 批注；
* `importCarExcept.xlsx` 里那张 `基础表请勿改动` 的参考 sheet（它就是给下拉框用的数据源）。

模板位置从 classpath `templates/down/` 换成 `config/templates/down/`（`config/` 是
classpath 的镜像）。

### 38.11 `resourceDownload` 的方法体**整块被注释** —— 永远空 body `[无影响]`

只剩 `checkAllowDownload` 那道闸是活的，后面“读本地文件 + 写响应”四行全是注释。
所以：

* 白名单**通过** → 什么都不做 → **200 空 body 无响应头**；
* 白名单**拒绝** → 抛异常被吞 → **同上**，只是多一条日志。

这个端点**没有任何调用方**，按迁移原则第 4 条照留。

### 38.12 `URLEncoder` 的安全字符集与 `urllib.parse.quote` **不同** `[无影响]`

`Content-Disposition` 里的百分号编码必须逐字节对齐 `java.net.URLEncoder`：

| 字符 | Java `URLEncoder` | `urllib.parse.quote` |
|---|---|---|
| 空格 | `+` | `%20` |
| `~` | `%7E` | `~`（不编码） |
| `*` | `*`（不编码） | `%2A` |

所以 `file_utils.url_encode` 是**手写**的，`percent_encode` = `url_encode` 之后把
`+` 换成 `%20`。换成 `quote` 会让带 `~` 或 `*` 的文件名在客户端解不出来。

### 38.13 `uploadFile` / `uploadFiles` 的返回键顺序与拼接 `[无影响]`

| Java | Python | 值 |
|---|---|---|
| `url` | `url` | `ServerConfig.getUrl() + fileName`（**完整 http 地址**） |
| `fileName` | `fileName` | 相对 url，如 `/profile/upload/2026/10/27/a_1.png` |
| `newFileName` | `newFileName` | 磁盘上的名字（带时间戳后缀） |
| `originalFilename` | `originalFilename` | 客户端传来的原始名 |

`uploadFiles` 的四个键是**复数**（`urls` / `fileNames` / `newFileNames` /
`originalFilenames`），值是**逗号串**而不是数组 —— 照抄 Java 的
`StringUtils.join(..., FILE_DELIMETER)`。

`FILE_DELIMETER` 是 Java 原文的**拼写错误**（正确是 `DELIMITER`），Python 侧常量名保留
这个错拼，便于 grep。

批量上传**没有回滚**：第 2 个文件失败时，第 1 个已经落盘且入库，报错只是中断循环。

---

## 39. `monitor` 包（Phase 3.20）

> 5 个控制器、**12 个映射全部迁移**。这一节的重点只有两个：
> **`Server` 是本迁移里最不像 Java 的一处**（OSHI → psutil），
> 以及**几处“看着像笔误、其实是 Java 现状”的地方**。
>
> 文件级对照见 [MAPPING_MONITOR.md](MAPPING_MONITOR.md)。

### 39.1 `@Log` 未迁移 → `sys_oper_log` 没有新行 `[需注意]`

> **本条已关闭（Phase 3.23）**：`LogAspect` 已迁移，下面 6 处 `@Log` 全部生效
> （`SysOperlogController` 的 `export` / `clean`、`SysLogininforController` 的
> `export` / `remove` / `clean`、`SysUserOnlineController` 的 `forceLogout`）。
> 原文"这 6 处都不写审计行"的结论**已失效**，保留只为留下变更轨迹，请以 §42.9 为准。

`monitor` 包里一共有 **6 处** `@Log`：

| 控制器 | 方法 | `businessType` |
|---|---|---|
| `SysOperlogController` | `export` | `EXPORT` |
| `SysOperlogController` | `clean` | `CLEAN` |
| `SysLogininforController` | `export` | `EXPORT` |
| `SysLogininforController` | `remove` | `DELETE` |
| `SysLogininforController` | `clean` | `CLEAN` |
| `SysUserOnlineController` | `forceLogout` | `FORCE` |

**注意 `SysOperlogController#remove` 没有 `@Log`**（同包里的 `SysLogininforController#remove`
有）—— 这是 Java 的不对称，不是漏抄。

`LogAspect` 尚未迁移，所以这 6 处都不写审计行。后果分两半：

* `/monitor/operlog` 是**唯一的受害者**：它自己的写操作也不落库，页面永远只有历史数据；
* `/monitor/logininfor` **不受影响** —— 登录日志由 `AsyncFactory` 写（已迁移），
  与 `@Log` 无关。

### 39.2 `Cpu.getTotal()` 是 Java 的既有 bug，照抄 `[需注意]`

```java
public double getTotal() {
    return Arith.round(Arith.mul(total, 100), 2);          // 漏了 / total
}
public double getSys() {
    return Arith.round(Arith.mul(sys / total, 100), 2);    // 其余四个都是这个形状
}
```

于是 `/monitor/server` 响应里的 `cpu.total` 是 **“tick 总和 × 100”**（正常机器上几万），
而不是百分比；`sys` / `used` / `wait` / `free` 才是真正的百分比。

前端若把它当“总使用率”画进度条会溢出。**这是上游 RuoYi 3.8.7 的行为**，
按迁移原则第 1 条与第 4 条（不擅自修）照抄。真要修，请连同前端一起改，并在本节留记录。

另外，`Cpu` 的**字段**存的是 tick 差值、**getter** 返回百分比，所以
`cpu.total != cpu.get_total()`。序列化只走 getter，字段值不出现在 JSON 里。

### 39.3 OSHI 的 tick → psutil 的秒 × 100 `[无影响]`

OSHI 的 `getSystemCpuLoadTicks()` 在 Linux 上返回 **tick**（`HZ = 100`），
psutil 的 `cpu_times()` 返回**秒**。为了保持 `Cpu.total` 与 Java 侧同一量级，
`_TICKS_PER_SECOND = 100.0` 把秒乘回 tick 口径。

百分比字段（`sys` / `used` / `wait` / `free`）是**比值**，与单位无关，所以这条差异
except `total` 之外看不出来。Windows 上 psutil 不给 `nice` / `irq` / `softirq` /
`steal` / `iowait`，一律按 0 处理（OSHI 在 Windows 上同样恒为 0）。

### 39.4 `Jvm` 面板映射成宿主机内存 `[需注意]`

`Runtime.getRuntime()` 在 Python 里没有等价物。两种“老实”的填法都很难看：

| 填法 | `used` | `usage` |
|---|---|---|
| `total = 0` | `-free` | `-Infinity` 或 100% |
| `max = 0`, `free = 0` | `total` | 100% |

最终取值：`total = max = 物理内存`，`free = 可用内存`。于是 getter 现算出的
`used = total - free`、`usage = (total - free) / total * 100` 就是**整机内存使用率**，
与 `Mem` 面板同源但语义明确。

其余字段：`version` = Python 版本、`home` = `sys.prefix`、`name` = `"CPython 3.12.x"`、
`startTime` / `runTime` 复用 `date_utils` 的三个函数（与 Java 同一个格式串）、
`inputArgs` = `str(sys.argv)`。

**如果业务方坚持要“进程级”数字**，最接近的替代是 `psutil.Process()` 的 RSS +
`tracemalloc` 峰值，但两者都不是“堆上限”，`usage` 会失去分母。不建议。

### 39.5 磁盘分区采集失败 → **跳过**该分区 `[无影响]`

Java 的 OSHI 遇到无介质的光驱会抛 `IOException`，`copyTo()` 整个失败 →
`/monitor/server` 回 **code 500**（整页监控打不开）。

Python 侧对 `psutil.disk_usage(...)` 抛 `OSError` 的分区 `continue`，并把原因记到 DEBUG 日志。

这是一处**有意偏差**：少一块盘比整页报错更接近运维预期，且 OSHI 在同样场景下的行为
在本项目环境里无法实测（没有可用的空光驱）。若要严格对齐，把 `except OSError` 去掉即可。

### 39.6 `cache.info` / `commandStats` 的键顺序**稳定** `[无影响]`

Java 用 `java.util.Properties`（继承 `Hashtable`）装 `INFO` 的键值对，
`stringPropertyNames()` 的迭代顺序**不确定** —— 同一台 Redis 两次请求的顺序可能不同。

Python 的 `parse_info` 按 `INFO` 文本的**原始顺序**输出。键集合完全相同，只是顺序稳定。
前端按 key 取值，不受影响；只有“把整个 `info` 对象 dump 出来做 diff”的场景会看到顺序差异。

### 39.7 `businessTypes` 额外接受**逗号串** `[无影响]`

Java 的形参是 `Integer[]`，RuoYi 前端用 `tansParams` 发成**重复键**
（`businessTypes=0&businessTypes=1`），Spring 的 `ArrayToArrayConverter` 逐元素转。

Python 侧的 `_parse_business_types` **同时**接受重复键与 `businessTypes=0,1`
（多支持一种写法）。两者都空 → `None`；`businessTypes=`（空值）→ `ValueError`
→ code 500，与 Java 的 `NumberFormatException` 同一条兜底路径。

### 39.8 `parseInfo` 的空白处理逐字对齐 `Properties.load` `[无影响]`

`Properties.load` 的 `LineReader` 只跳**前导**空白（`skipWhiteSpace`）与值的前导空白
（`valueStart++` 循环），**行尾空白不裁**。`parse_info` 因此写成 `raw_line.lstrip()`
而不是 `strip()`。

真实的 `INFO` 输出两侧都没有空白，所以这一条**只影响构造出来的输入**（例如用例）。
写成 `strip()` 也能跑，但那是在“顺手收紧” Java 的解析规则。

### 39.9 `clean` 在 Python 侧必须注册在 `{ids}` **之前** `[无影响]`

`SysLogininforController` 的源码顺序是 `remove`（`/{infoIds}`）在前、`clean` 在后，
靠的是 Spring 的 `AntPathMatcher` **偏爱字面量**。FastAPI 按**注册顺序**匹配，
所以 Python 侧把 `clean` 写在前面，否则 `clean` 会被当成 `infoIds="clean"`
→ `int("clean")` 失败 → code 500。

两边**净行为一致**（`DELETE /monitor/x/clean` 永远命中 `clean`），只是声明顺序不同。
两个模块的用例都有 `test_clean_comes_before_the_path_variable` 钉住这一点。

### 39.10 `SysUserOnline.loginTime` 是 epoch **毫秒数字** `[无影响]`

`SysUserOnline` **不继承** `BaseEntity`（裸 POJO），`loginTime` 是 `long`，
Jackson 直接输出数字。`/monitor/online/list` 里看到的是 `1700000000000`，
不是 `"2023-11-15 06:13:20"` —— 与其它列表页的时间格式**不同**，前端自己格式化。

`BaseEntity` 的 `params` 也不会出现（该实体没有这个字段）。

### 39.11 两个无调用方的方法照留 `[无影响]`

| 方法 | 为何没有调用方 |
|---|---|
| `SysOperLogService#selectOperLogById` | `SysOperlogController` 只有 `list` / `export` / `clean` / `remove`，没有 `/{operId}` 详情接口 |
| `SysUserOnlineService#selectUserOnlineList` | 控制器只调 `selectOnlineByInfo`；前者比后者少了过滤 |

按迁移原则第 4 条（不删除“看似无用”的 Java 代码）照留，并各有用例覆盖。

### 39.12 `businessType = 0`（其它）的筛选**被丢掉** `[需注意]`

XML 写的是：

```xml
<if test="businessType != null and businessType != ''">
    and business_type = #{businessType}
</if>
```

`businessType` 是 `Integer`，OGNL 对“数字 vs 字符串”统一转 `double`，而
`OgnlOps.doubleValue("")` 的实现是 `(s.length() == 0) ? 0.0 : Double.parseDouble(s)`
—— **空串等于 `0.0`**。于是：

| `businessType` | 条件求值 | `business_type` 筛选 |
|---|---|---|
| `null` | `false` | 不生效（正确） |
| `0`（其它） | `0 != 0` → **`false`** | **不生效** ← 问题 |
| `1` / `2` / … | `true` | 生效 |

结果：**操作日志页选“其它”会查出全部记录**。这是 Java 现状，照抄。
`status` 用的是 `<if test="status != null">`，没有这个问题。

### 39.13 两个 `export` 的文件名在 **`msg`** `[需注意]`

`util.exportExcel(list, "操作日志")` 返回 `AjaxResult.success(String)`，挑中的是
`success(String msg)` 重载 —— 文件名落在 **`msg`**，**没有 `data` 键**，文件本身在
`{profile}/download/` 下，前端得再发一次 `GET /common/download`（§37.2 / §37.3）。

工作表名分别是 `操作日志` / `登录日志`。`export` **不调** `startPage()`，导出全量命中行。

### 39.14 `/monitor/online/list` **没有分页** `[需注意]`

Java 直接 `getDataTable(userOnlineService.selectOnlineByInfo(...))`，**没有** `startPage()`：

* `total` 是 **列表长度**（`new PageInfo(list).getTotal()`），不是总数；
* 前端传的 `pageNum` / `pageSize` **完全不看** —— `pageSize=10` 也会拿到全部在线用户。

会话数量 = Redis 里 `login_tokens:*` 的键数，生产上通常是几十到几百，所以没炸；
但这不是“分页接口”，前端把它挂进分页表格只是碰巧能用。

### 39.15 `forceLogout` 对不存在的 token 也回 **200** `[无影响]`

```java
redisCache.deleteObject(LOGIN_TOKEN_KEY + tokenId);
return AjaxResult.success();
```

`deleteObject` 的返回值被丢弃，`return` 是无条件的。

`tokenId` 是 **`LoginUser.token`（UUID）**，不是 JWT 本身 —— 换成 JWT 在这里删不到任何键，
但接口仍然回 200。下一次请求时该 token 查不到会话，会被判为未认证（401）。

### 39.16 在线用户扫描用 **`KEYS`** `[需注意]`

`RedisCache.keys(...)` 发的是 `KEYS`（不是 `SCAN`），与 Spring Data Redis 的
`RedisTemplate#keys` 一致。这是 **O(N) 阻塞**命令：会话量大时会把整个 Redis 卡住，
`/monitor/cache` 那条 `INFO` 也会排队。

Java 线上就是如此，Python 侧不改 —— 改成 `SCAN` 是**行为改变**（顺序与一次性快照语义都变），
而且会掩盖同一个运维问题。真要改，先把会话键改成 Hash 或维护索引集。

### 39.17 `psutil==6.1.1` 早已是声明依赖 `[无影响]`

`pyproject.toml` 里原本就有 `psutil==6.1.1`（标注 `<- oshi-core`），
因为 `rouyi-framework` 用 OSHI 做服务器监控，迁移计划里早就预留了这个位置。
**本切片没有改依赖文件**，只是开始真正用它。

### 39.18 安全探针路径搬家（测试侧） `[无影响]`

`tests/test_security_filter.py::PROTECTED_UNMAPPED_PATH` 原本是 `/monitor/online/list`，
依赖“该路径没有控制器”来构造 404。`monitor` 包迁完之后它会去连真实 Redis，
所以改成 `/migration/probe/never-mapped` —— 一个**任何语言里都永远不存在**的路径，
以后迁移任何模块都不需要再动这个常量。

Java 侧对该路径同样是 404（`BasicErrorController`），两边可观测行为一致。

---

## 40. `manager/bigScreen` 大屏切片（Phase 3.21）

> **Phase 3 的最后一个控制器切片**：12 个映射全部迁移；迁完之后 `ruoyi-admin` 下的
> **75** 个控制器全部有对应物。
>
> 这一节的重点只有三个：**一个权限点都没有**、**路径是驼峰**、**三个魔法值**。
>
> 文件级对照见 [MAPPING_BIGSCREEN.md](MAPPING_BIGSCREEN.md)。

### 40.1 金额类 `BigDecimal` 在 JSON 里是**字符串** `[需注意]`

这是**全局**问题，不是本切片引入的，只是大屏把金额字段摆到了最前面：

```text
Java   : {"totalAmount": 12.50, "finishedAmount": 3.25}
Python : {"totalAmount": "12.50", "finishedAmount": "3.25"}
```

原因在 `app/main.py` 的 `default_response_class=ORJSONResponse` —— orjson 把
`decimal.Decimal` 原生序列化成**字符串**（它不把十进制字面量折成二进制浮点，这是
有意的精度保护）。Java 的 Jackson 对 `BigDecimal` 输出 JSON **数字**，且**保留 scale**
（`12.50` 不会变成 `12.5`）。

受影响的范围是**所有**带 `BigDecimal` 字段的响应：
`carAudit` 的 `totalAmount` / `finishedAmount`、`carStatistics` 的 `escapedAmount`、
`PCIncomeStatics` 的 `amount`、`CarAduitFree.amount` 等。

对前端的影响：

* JS 里 `"12.5" > 0` 为真（字符串会被隐式转换），但 `"12.5" + 0` 是 `"12.50"`；
* `==` 比较、`toFixed()`、排序需要显式 `Number(...)`；
* JSON Schema / 类型校验会判不合法。

**为什么不就地修**：要同时满足“输出数字”与“保留 scale” 两件事，必须在响应层做
一次自定义序列化（orjson 的 `default` 钩子拿不到 `Decimal`，原生分支优先命中）。
那是一次**全局**改动，会同时影响 2972 条用例里所有断言金额的地方，与
“行为保持 + 不顺手改” 的迁移纪律冲突。**当前状态**：

* 已在大屏用例里**钉住**现状（`tests/test_big_screen_controller.py` 注释里指向本节），
  任何“无心之改”都会让用例红；
* 若业务方要求与 Java 字面一致，这是一处**统一的**改造点（换 `Response` 类 + 改断言），
  不是逐接口打补丁。

### 40.2 12 个端点**没有任何权限点** `[需注意]`

`BigScreenController` 的类上、方法上都没有 `@PreAuthorize`（同包其它控制器每个 CRUD
都有权限点）。所以这 12 个接口**只要登录就能访问**，`{permissions: []}` 也照样 200。

Python 侧保持原样，一条 `pre_authorize_permi` 都没加 —— 别按“CRUD 惯例”自动补上，
那会让大屏在没配菜单权限的账号上直接白屏。

### 40.3 路径里的 `bigScreen` 是驼峰 `[无影响]`

`@RequestMapping("/manager/bigScreen")`。同包的全是 `/manager/carinfo`、
`/manager/aduitfree` 这种全小写，**这里照抄**。前端写的就是
`/manager/bigScreen/carStatistics`，改成 `/manager/bigscreen` 就是 404。

### 40.4 `code` 为空时塞的是三个**魔法值** `[需注意]`

`type` 非空、`code` 为空时，Java 写到查询对象上的不是 `null`，而是常量：

| `type` | 字段 | 空 `code` 时写入 |
|---|---|---|
| `1` | `tollCode` | `StationCapture` |
| `2` | `gantryCode` | `GantryCapture` |
| `3` | `fwqbm` | `ServiceAreaCapture` |

语义是“**怎么查都不会命中**”（这三个串不可能是真实编码），而不是“不过滤”。
前端不给编码就选类型时，页面本来就应该空 —— 照抄。

### 40.5 `"all"` 是**子串**判断，`deleteEnd` 只削**一个**逗号 `[需注意]`

`/tollGantryFwqList` 里三件事叠在一起，每件都容易抄错：

1. `sectionCode` **空白**（`null` / `""` / 全空格）→ 直接回**空数组**，**不查库**；
2. `CommonUtil.deleteEnd(s)` 只去掉**一个**尾逗号：`"SD01,,"` → `"SD01,"`，
   再 `split(",")` 时 Java 丢掉尾部空串 → `["SD01"]`；
3. `sectionCode.indexOf("all") > -1` —— 作用在**整串**上，所以 `"SD01,all"`
   也会把列表清空（= 全量）。**不是** `equals`，**不是**对列表 `contains`。

`/carLocation` 与 `/carWarning` 里的 `sectionCode.contains("all")` 同理：`"all,SD01"`
整串被清空。

### 40.6 `exceptRecordList` 的 **N+1** 查询原样保留 `[需注意]`

分页结果逐行再查两次：

| 字段 | 来源 | 次数 |
|---|---|---|
| `orgId` | `carConfimFreeService.selectOrgId(carId, id)` | 每行 1 次 |
| `supplementaryStatus` | `carAduitFreeService` 按 `carId` **count > 0** → `"1"` | 每行 1 次 |

`pageSize=50` 就是 1 + 100 条 SQL。**不要“优化”成 join**：`car_aduit_free` 的 count
带 `del_flag = '0'` 逻辑删除条件，join 出来的语义不同（而且 Java 就是 N+1）。

### 40.7 `carAudit` 的空值是**零初值**，不是 `null` `[无影响]`

`CarAuditVO` 四个字段在 Java 里都有非 null 初值（`0` / `0` /
`BigDecimal.ZERO` / `BigDecimal.ZERO`）。两个来源任意一方回 `null` 时**保留初值**，
所以响应体里永远是 `0` 而不是 `null`。两个来源的调用顺序固定：
先 `getCarAudit`（异常流水），再 `getCarConfirm`（已追缴）。

### 40.8 `type` 缺失时手抄 Spring 的**英文原文** `[无影响]`

Java 的 `@RequestParam String type`（无 `required = false`）缺失时抛
`MissingServletRequestParameterException`，被 `GlobalExceptionHandler` 的
`Exception` 分支接住 → HTTP 200 + `code 500`，`msg` 是 Spring 的固定句式：

```text
Required request parameter 'type' for method parameter type String is not present
```

Python 侧用模块常量 `MISSING_TYPE_MESSAGE` 复刻同一句（并 `raise ServiceException`
而不是 `ValueError` —— 后者会被 `ServerErrorMiddleware` 重抛，见 §38.6）。

### 40.9 `bigscreen/center` 的 7 个 VO 未迁移（死代码） `[无影响]`

`BaseBigScreenVo` + `bigscreen/center/` 下 6 个 VO（`CenterStatisticsVo` /
`OrderAndEnterpriseVo` / `OrderAndEnterpriseInfoVo` / `OrderDetailVo` /
`TransitOrderDetailVo` / `TrackPoint`）在全仓范围内**没有任何控制器、服务或 Mapper 引用**，
只被彼此继承/引用。它们属于一套**未实现的“城市配送中心大屏”**，依赖的
`TWaybill` / `TWaybillRoute` 两个实体也没有业务调用方（Python 侧同样没迁）。

按“不迁无调用方的空壳”处理：**Java 源码一行未动**，理由记在这里与
`MAPPING_BIGSCREEN.md` §5。将来那套大屏上线时，这 7 个 VO 连同两个实体一起补。

### 40.10 三个 base 实体**补回** `sectionCodeList` `[无影响]`

`OdsSzdnToll` / `OdsSzdnGantry` / `DwdLcztFwqjcxx` 在 Java 里都有

```java
@TableField(exist = false)
private List<String> sectionCodeList;
```

Python 侧此前**漏建**了这个字段（`/tollGantryFwqList` 是唯一往它里面塞值的地方，
所以没暴露）。本次按 Java 的声明位置补进三个实体 —— 修的是 Python 侧的漏项，
不是行为改变。

### 40.11 控制器方法名叫 `list`，**遮蔽内置函数** `[无影响]`

Java 的方法名就是 `list`（`@GetMapping("/exceptRecordList")`）。Python 侧保留同名，
好处是全文搜 `list(` 能直接对上 Java；模块内部没有别处调用内置 `list`，所以无冲突。
若将来要在同一模块里用内置 `list`，记得写 `builtins.list`。

---

## 41. 全量只读接口对拍（146 个端点）`[需注意]`

用真实账号（`admin`）分别登录 Java `:8090` 与 Python `:9989`，对 **146 个只读 GET**
逐字段比对（脚本与结论文档见 `MIGRATION_PROGRESS.md` §6.6）。最终结论：

| 判定 | 数量 | 含义 |
| --- | --- | --- |
| SAME | 122 | 逐字段一致 |
| DIFF | 13 | 有字段不同 —— 全部落在本节 |
| CODE | 1 | `code` 不同（§41.1） |
| STATUS | 1 | 状态码不同（`/health`，Python 独有） |
| SHAPE-DIFF | 1 | 形状不同（`/monitor/server`，Java 自己坏了） |
| STATUS-ONLY | 6 | 有副作用 / 二进制，只记状态码 |
| SHAPE-OK | 2 | 实时值，只比形状且形状一致 |

下面只登记**无法（或不该）靠改代码消掉**的差异。

### 41.1 `GET /base/fitting/list`：Java 恒定 500，Python 正常返回 `[需注意]`

```text
Java   : {"code":500,"msg":"nested exception is org.apache.ibatis.reflection.ReflectionException:
                     There is no getter for property named 'id' in 'class com.ruoyi.base.domain.ZdataTrailFitting'"}
Python : {"code":200,"msg":"查询成功","total":400,"rows":[...]}
```

根因：`ZdataTrailFittingMapper.xml` 的列表语句里有一条
`<if test="id != null  and id != ''"> and t.id = #{id}</if>`，而实体
`ZdataTrailFitting`（`ruoyi-system/.../base/domain/ZdataTrailFitting.java`）**没有 `id`
属性** —— 主键叫 `cid`。OGNL 在求值 `<if>` 时就要读 getter，所以**不管传不传参**都会抛
`ReflectionException`，这条语句在 Java 侧从未成功执行过（`t.id` 这一列在表里同样不存在）。

**决策：不复制这个崩溃。** `<if>` 已按原文迁移成 `If("id", "id")`（见
`app/base/mapper/zdata_trail_fitting_mapper.py`），只是 Python 侧取不到属性时**静默跳过**
（`build_conditions` 用 `getattr(query, attr, None)`），于是同一条语句能正常跑出 400 行。
若业务方确认要“连报错一起 1:1”，改回抛错即可；但要同时接受这个接口在两边都不可用。

### 41.2 `...BO` 的大写缩写必须写 `alias` `[无影响]`

Java 的 `TrailBo.borderWeighingCaptureBO` / `TrailInfo.trailDevCountBO` 这类字段，
`to_camel("border_weighing_capture_bo")` 只能拼出 `borderWeighingCaptureBo`。
不写 `alias` 的后果是**每个对象同时少一个 Java 有的键、多一个 Java 没有的键**
（`/manager/cartrackinfo/listByCarByTime` 实测 5 + 1 个字段 × 每条轨迹点）。

已核查：`ruoyi-system` + `ruoyi-common` 里以大写缩写结尾的**序列化**字段只有这 6 个
（其余命中全是 `serialVersionUID`），全部补了 `alias`。

### 41.3 PageHelper 会先删掉 count 语句的 `ORDER BY` `[无影响]`

`CountSqlParser#removeOrderBy` 在发 count 之前把**最外层** `order by` 摘掉。所以
“`order by` 引用了投影里没有的列”这种语句在 Java 里 **count 能过、数据语句不执行**
（`total == 0` 直接回空页），Python 若原样执行就会 `Unknown column ... in 'order clause'`。

已按同样规则实现 `page_helper.strip_order_by()` / `normalise_count_sql()`：只在**括注深度为 0**
处识别 `order by`，跳过引号内文本，且后面若跟 `limit` / `offset` 则不动。

### 41.4 `BigDecimal` 出的是**数字且保留 scale** `[无影响]`

`BigDecimal.ZERO` 序列化成 `0`，`new BigDecimal("12.00")` 是 `12.00`。Python 的 `Decimal`
统一 `float()` 会得到 `0.0`。已改为 `domain_model.decimal_to_java_number()`：
`Decimal.as_tuple().exponent >= 0` 出 `int`，否则 `float`。

### 41.5 `GET /system/user`（无尾斜杠）Java 是 500 `[无影响]`

Java `@GetMapping(value = {"/", "/{userId}"})` 的 `"/"` **只**匹配 `/system/user/`；
不带尾斜杠时只有 `@PostMapping`（`add`）在库里，Spring 判 405，再由
`GlobalExceptionHandler` 翻成 `HTTP 200 + code 500`：

```text
GET /system/user    -> {"code":500,"msg":"Request method 'GET' not supported"}
GET /system/user/   -> {"code":200,...}
```

Python 侧原先同时注册了 `""` 与 `"/"` 两个路由（都 200），已删掉 `""`，
让 Starlette 走“只有 POST 部分匹配 → 405 → 同一条 handler”的路径。

### 41.6 外部服务 `:9901` 不可达时的 `msg` **不对齐** `[需注意]`

`/base/feeGantry/list`、`/base/feestationexit/list`、`/manager/cartrackinfo/listByCarId`
都靠 Forest 转发到 `127.0.0.1:9901`。该服务不在本仓库（`vehicleMonitor.baseUrl`），当前不可达：

```text
Java   : org.apache.http.conn.HttpHostConnectException: Connect to 127.0.0.1:9901 [/127.0.0.1] failed: Connection refused: connect
Python : 请求失败: http://127.0.0.1:9901/... -> [WinError 10061] 由于目标计算机积极拒绝，无法连接。
```

两边都是 `HTTP 200 + code 500`（无数据可比），只有文案不同。**刻意不伪造** Java 那段字：
它由 Apache HttpClient 拼装、且尾部的 `Connection refused: connect` 来自 JVM/平台，
硬编码进 Python 等于把平台细节焊死。待 §“待确认清单”第 3 条由业务方明确后再决定
是“统一成自家文案”还是“逐字对齐”。

### 41.7 Excel 导出只比“能打开”，不比字节 `[无影响]`

6 个 `export*` 端点的 xlsx 字节必然不同（Java EasyExcel/POI 用 deflate + data descriptor，
Python openpyxl 用 store）。单元格内容、sheet 名、列序一致；对拍脚本对这类响应记的是
`__raw__` / `__len__` 两条“差异”，人工判定为**不可消除**，因此这 6 个端点固定计入 DIFF。

**已实测**（`evidence/_cmp_xlsx.py`：下载两侧 xlsx，用 openpyxl 读成
`(sheet 名, [[单元格字符串]])` 再比，`data_only=True`）：

| 端点 | Java 字节 | Python 字节 | 单元格 |
| --- | --- | --- | --- |
| `/manager/aduitfree/exportIncomeStatics` | 8875 | 7605 | SAME |
| `/manager/aduitfree/exportIncomeDetailList` | 7226 | 5711 | SAME |
| `/manager/confimfree/exportCarStatics` | 7835 | 6163 | SAME |
| `/manager/confimfree/exportConcernedList` | 10253 | 8895 | SAME |
| `/manager/exceptrecord/exportOrgId` | 7698 | 6118 | SAME |
| `/manager/suspicious/exportHistory` | 9352 | 7695 | SAME |

字节差稳定在 ~1.24 倍（deflate vs store 的封包开销），内容零差异。
**不要**为了“字节一致”改用 Java 的压缩方式：openpyxl 不暴露 zip `compress_type` 的
per-entry 控制，强改只会引入脆弱的手工重打包。

### 41.8 两个“同名基类”里只有一个带 `@JsonIgnore` `[需注意]`

```java
// BaseEntity.java
@JsonIgnore
private String searchValue;      // 双向都不出现

// BaseUuidEntity.java
private String searchValue;      // 没有注解 -> 输出 "searchValue": null
```

`BaseUuidEntity` 那份**没有** `@JsonIgnore`（实测源码 + 实测响应：`GET
/system/indexmenu/{id}` 的 `data` 里确实有 `"searchValue": null`），所以 Python 侧
`base_uuid_entity.py` 也**不能**给它加 `Field(exclude=True)`。反过来，
`BaseEntity` 那份必须双向屏蔽 —— 它是 `${params.dataScope}` 的注入面（§38.6）。

同样的分歧还有 `params`：`BaseEntity` 上是 `@JsonInclude(NON_EMPTY)`（空 Map 整键消失），
`BaseUuidEntity` 上什么都没有（`"params": null`）。

### 41.9 `/system/user/list` 每行的 `deptName` 恒为 `null` `[无影响]`

```text
Java   : {..., "deptName": null, "dept": {"deptId": 25367, "deptName": "吉安东管理中心", ...}}
Python : {..., "deptName": null, "dept": {...同上...}}
```

`SysUserResult` 里有 `<association property="dept" resultMap="deptResult"/>`。MyBatis 的
`autoMappingBehavior=PARTIAL` 一旦遇到**嵌套**映射，就会把整条语句的自动映射**关掉**，
于是 `d.dept_name` 只进 `dept.deptName`，扁平的 `SysUser.deptName` 保持 `null`。
Python 侧的 `_map_user_list_row` 因此**故意**不填 `dept_name`（`app/system/mapper/
sys_user_mapper.py`），两边的原始响应已逐键核对（只差顺序）。

---

## 42. `quartz` 切片（Phase 3.23）`[需注意]`

`ruoyi-quartz` 的 **25 个源文件**全部有对应物（文件级对照见 `MAPPING_QUARTZ.md`）；
`sys_job` / `sys_job_log` 两个控制器的 **13 个端点**（8 + 5）与 Java 逐字段对齐；
六个任务 Bean 全部能被 `sys_job.invoke_target` 调用。

本节只记**行为差异**，以及迁移中用测试抓到的**三个真缺陷**（都已修复）。

### 42.1 Quartz 2.3.2 → 自研内存实现，而不是引入调度库 `[无影响]`

**Java 现实**（决定一切的前提）

| 事实 | 出处 | 后果 |
|---|---|---|
| 只依赖 `org.quartz-scheduler:quartz:2.3.2` | `ruoyi-quartz/pom.xml` | **没有** Spring Boot Quartz starter |
| `ScheduleConfig.java` **58 行全是 `//`** | 连 `package` 都被注释 | 编译产物里没有这个类，`SchedulerFactoryBean` 不注册 |
| Spring Boot 2.5.15 的 `QuartzAutoConfiguration` 接管 | — | `RAMJobStore` + `SimpleThreadPool(10)` + `misfireThreshold=60000` + `isClustered=false` |

**Python 实现**

| 文件 | 规模 | 职责 |
|---|---|---|
| `app/quartz/util/scheduler.py` | 约 640 行 | 本工程真正用到的 12 个 Quartz API：`JobKey` / `TriggerKey` / `checkExists` / `deleteJob` / `scheduleJob` / `pauseJob` / `resumeJob` / `triggerJob` / `clear` / `getJobDataMap` / `getMergedJobDataMap` |
| `app/quartz/util/cron_expression.py` | 约 1250 行 | Quartz 2.3.2 `CronExpression` 逐行转写，`is_valid` 与 `next_valid_time` 共用同一份 |
| `app/quartz/config/schedule_config.py` | 78 行 | **整文件被注释掉的** `ScheduleConfig` 存档（无运行期行为） |

不引入 APScheduler / croniter 的**唯一理由**是可观察行为：

1. `Key.toString()` 是 `group.name`；`jobGroup` 为 `null` 时 Quartz 换成 `DEFAULT`，
   于是 `PUT /monitor/job/run` 的报错
   `The job (DEFAULT.TASK_CLASS_NAME999999) referenced by the trigger does not exist.`
   逐字可复现。
2. `pauseJob` / `resumeJob` / `deleteJob` 对**不存在**的 key **不抛异常**（`RAMJobStore`
   内部遍历空集合），只有 `triggerJob` 抛 `SchedulerException`。
3. cron 是 **Quartz 方言**：`*/0` 合法（`addToSet` 把 `incr <= 0` 改写成 `1`）、
   `StringTokenizer` 分词（不产生空 token，`"0  0 2 * * ?"` 合法）、
   `getNumericValue` 把剩余整串当数字（`0/10abc` 抛 `NumberFormatException`）、
   `Calendar.set` lenient（`MINUTE=60` 进位到下一小时）、`?` / `L` / `W` / `#`。
4. `misfire` 指令是**整型常量**：SMART(0) / FIRE_ONCE_NOW(1) / DO_NOTHING(2) /
   IGNORE(-1)，且 `CronTriggerImpl#updateAfterMisfire` 把 SMART 折成 FIRE_ONCE_NOW ——
   所以 `sys_job.misfire_policy` 的三个"有值"分支实际只区分**补一次**与**跳过**。

> `ScheduleConfig.java` 这个一行都不生效的文件按迁移原则第 4 条**保留**：
> 它把被注释掉的集群配置（`QRTZ_` 前缀、`LocalDataSourceJobStore`、
> `clusterCheckinInterval=15000`、`threadCount=20`）原样存成字典，是"将来要上集群
> 该配什么"的唯一书面依据。真上集群时内存实现**不再等价**，必须整段重做并重新验证
> 上面 4 条可观察行为。

依赖表也跟着改了：`pyproject.toml` / `requirements.txt` 里的 **`APScheduler==3.11.0` 已删除**
（此前把它当成 `quartz` 的替身，是 Phase 4 之前的设计草案，没有任何代码 import 它）。
quartz 在本工程里**不含第三方依赖** —— 那 12 个 API 与 `CronExpression` 都在
`app/quartz/util/` 里。启动日志的措辞同步改成 `Quartz 调度器已禁用`，不再出现 APScheduler。

### 42.2 `AbstractQuartzJob#execute` 曾缺一个 `import` —— 每次执行都崩（已修复）`[需注意]`

**现象**
`app/quartz/util/abstract_quartz_job.py` 的 `execute()` 第 2 行是
`copy_bean_prop(sys_job, context.get_merged_job_data_map().get(TASK_PROPERTIES))`，
而 `TASK_PROPERTIES` 这个常量**从来没有被 import 过**。

**为什么之前的用例全都没抓住**
`NameError` 抛在 `try:` **之前**，所以连 `after(context, sys_job, e)` 的失败分支都走不到：
`sys_job_log` 一条记录都不会有，看起来就像"任务没触发"。而当时的用例只分别测
`before` / `do_execute` / `after` 三个方法，没有一条调用 `execute` 本身。

**修法**
补一行 `from app.common.constant.schedule_constants import TASK_PROPERTIES`。
回归护栏在 `tests/test_quartz_tasks.py::TestAbstractQuartzJob`：直接调 `execute()`，
把"成功 → `SUCCESS` + 一条作业日志"与"异常 → `FAIL` + 2000 字截断的堆栈"两条路径钉住。

### 42.3 `insertBatchToTable` / `insertToTable` 的 25 个"幻影属性" `[需注意]`

**Java 原行为**
`OdsRtSzdnSnapshotFlowAddcodeMapper.xml` 的两条 `INSERT` 一共写了 **62 个**
`#{item.xxx}`，而实体 `OdsRtSzdnSnapshotFlowAddcode` **只有 43 个字段**。多出来的 25 个是：

```text
smallpicturepath, plategnssstatus, gpsinfo, devicename, devicetype,
carclass, gantryid, smallsideimage, headimageheight, sidescenetypecode,
sidescenetype, tailimagewidth, envstate, headscenetypecode,
headscenetype, sidedrivingdirectioncode, sidedrivingdirection,
sideimageheight, speed, tailplateimage, headdrivingdirectioncode,
headdrivingdirection, laneidcode, carlength, imagelevel
```

MyBatis 解析 `#{item.smallpicturepath}` 时要反射取 getter，抛

```text
ReflectionException: There is no getter for property named 'smallpicturepath'
in 'class com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode'
```

也就是说这两条语句在 Java 侧**从未成功执行过**（与 §41.1 的 `ZdataTrailFitting`
是同一类缺陷：OGNL/反射引用了实体上不存在的属性）。

**Python 实现**
按实体真实拥有的 43 列（`RESULT_COLUMNS`）生成同样形状的多值 `INSERT` ——
只消掉"引用了不存在的属性"这个**崩溃**，不动任何业务规则：
列清单来自实体本身，`with session_scope()` 一次提交，行数由 `rowcount` 回。

**影响**
Java 侧这段代码是死路（永远抛异常），所以"少写 19 列"不会造成数据差异。
反过来：若将来给实体补齐字段，两侧必须**同时**改，否则 Python 会开始写 Java 写不了的列。

### 42.4 `SnapshotFlowSyncTask` 在 Java 里就是**空转**的 `[无影响]`

`syncSnapshotFlowByDateRange` 的第一步：

```java
List<OdsRtSzdnSnapshotFlowAddcode> dataList = convertToEntityList(tableDataInfo.getRows());
```

而 `convertToEntityList` 只保留 `row instanceof OdsRtSzdnSnapshotFlowAddcode` 的行；
`TableDataInfo.rows` 声明是 `List<?>`，Jackson 反序列化出来是
`ArrayList<LinkedHashMap>` —— **没有一行**是实体。于是 `dataList` 恒空、立即 `break`，
整趟同步搬 0 条，`syncFullData()` 返回 `"全量同步完成，共同步 0 条数据"`。

Python 侧 Forest 返回的是 `dict`，`convert_to_entity_list` 的 `isinstance` 判定同样全部
落空 —— 两边都是空转。

**不要"顺手修好"**：一旦真跑起来就会往 `ods_rt_szdn_snapshot_flow_addcode_yyyyMM` 分表
写数据，而这个任务从来没人验证过（连它依赖的 `INSERT` 都是 §42.3 的死代码）。
两个 `@Scheduled` 方法也不会触发（§11：无 `@EnableScheduling`）。

### 42.5 `invoke_target` 存的是 **Java 方法名**，需要一个桥 `[无影响]`

`sys_job.invoke_target` 形如 `ryTask.ryNoParams()`。Java 的 `JobInvokeUtil.invokeMethod`
用 `getDeclaredMethod(methodName)` 反射，名字**一字不差**；Python 的方法名是
`ry_no_params`，`getattr(bean, "ryNoParams")` 恒为 `None`。

**修法**
`job_invoke_util._declared_method` 取不到原名时，再按 `StringUtils.toUnderScoreCase`
（`app/common/utils/string_utils.py` 里同名的逐字转写）取一次 `snake_case` 形态；
报错文案仍用 **Java 原名**：`java.lang.NoSuchMethodException: RyTask.ryNoParams()`。

**为什么做桥而不是改数据**
`sys_job` 的后台数据是 Java 建的，**线上库里存的就是 Java 方法名**。把它改成
`ry_no_params` 会让 Java 与 Python 不能共用同一个库 —— 迁移第一原则是两边数据对等，
所以在代码里做双向兼容，表里一个字都不动。

**已知边界**
`getDeclaredMethod` 还能按参数个数/类型挑同名重载，Python 只有一个名字。
本工程 6 个任务类**没有同名方法重载**（`tests/test_quartz_tasks.py` 逐类断言
`__bases__ == (object,)`，方法名唯一），所以不影响；将来若出现重载，必须显式登记。

### 42.6 `RyTask` 的参数按 Java `String.valueOf` 拼 `[无影响]`

`ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)` 是唯一同时用到 5 种参数类型的
调用目标，也是 `JobInvokeUtil` 类型判定顺序（`'` → Boolean → Long → Double → Integer）
的"活体用例"：`316.50D` 只有先被 `D` 命中才不会落进 `Integer`。

| 参数 | Java `toString()` | Python `str()` | 处置 |
|---|---|---|---|
| `true` | `true` | `True` | `_java_str` 显式小写化 |
| `null` | `null` | `None` | `_java_str` 返回 `"null"` |
| `2000L` | `2000` | `2000` | 一致 |
| `316.50D` | `316.5` | `316.5` | 一致 |
| `100` | `100` | `100` | 一致 |

线上日志是 `布尔类型true`；照抄 `str()` 会得到 `布尔类型True`。该串会进
`sys_job_log.job_message`，属**可观察输出**，所以必须逐字对齐。

### 42.7 `sys_job` 装载失败：Java 启动失败，Python 只记日志 `[需注意]`

**Java**
`SysJobServiceImpl.init()` 是 `@PostConstruct`：`scheduler.clear()` + 逐条
`createScheduleJob`。数据库连不上时它抛异常 → Spring 包成 `BeanCreationException` →
**整个应用起不来**。

**Python**
`app/main.py::_init_quartz` 用 `try/except Exception` 包住，只打一行

```text
[启动警告] Quartz 任务初始化失败, sys_job 中的任务不会调度
```

**为什么保留这个偏差**
本工程允许在**没有 MySQL** 的环境起服务（健康探针、静态检查、接口文档都要能用；
`app.scheduler-enabled=false` 是同一诉求的另一半，Java 没有这个开关）。
代价是：库里任务表坏了，Python 会"安静地"跑起来，而 Java 会拒绝启动 ——
运维要知道**日志里那一行**才是唯一信号。

**未注册的任务仍然报同样的错**
调度器空转时 `PUT /monitor/job/run` 得到
`The job (DEFAULT.TASK_CLASS_NAME7) referenced by the trigger does not exist.`，
与 Java"任务没注册"时逐字一致。

### 42.8 `@DisallowConcurrentExecution` 用 per-job 锁 `[无影响]`

`sys_job.concurrent != "0"` 时任务类带 `@DisallowConcurrentExecution`，Quartz 不让
**同一个 JobDetail** 并发执行。Python 用一把 per-job 锁：锁被占住就**推迟**本次触发
（保留 fire time，下个 tick 再试），推迟超过 `misfireThreshold`（60 s）后按 misfire 指令
处理 —— 与 `QuartzSchedulerThread` 先 `acquireNextTriggers` 后
`releaseIfScheduleChangedSignificantly` 的结果一致。

线程池：Java `SimpleThreadPool(threadCount=10)` → Python `ThreadPoolExecutor(max_workers=10)`。
`JobExecutionContext` 的构造参数是 `(scheduler, trigger, job_detail, merged_job_data_map)`，
与 `JobExecutionContextImpl` 一致（`getMergedJobDataMap()` 取的是 JobDetail 与 Trigger
两份 map 的合并结果）。

### 42.9 `@Log` 现已**全量生效**（13 处"未迁移"的历史结论作废）`[需注意]`

Phase 3.23 之前的本文件在 §25.2 / §26.2 / §27.2 / §28.2 / §29.2 / §30.1 / §31.2 /
§32.3 / §33.3 / §34.3 / §35.3 / §36.2 / §39.1 十三处都写着
"`@Log` 未迁移 → 不写 `sys_oper_log`"。**这条结论已经失效**：

* `app/framework/aspectj/log_aspect.py`（528 行）是 `LogAspect` 的等价物，
  `AsyncManager.me().execute(record_oper(oper_log))` 与原实现同一路径；
* 全仓 **233 处** `@Log`（`tests/test_log_aspect.py::TestMigrationInventory` 逐文件统计；
  Java 源同样是 233 处，其中 `ruoyi-quartz` 贡献 9 处：`SysJobController` 6、
  `SysJobLogController` 3，另有 `ruoyi-generator` 的 `GenController` 7 处。
  另有 5 处 `@Log(title` 整段被块注释掉，两边都不计，见 §44.4）；
* 装饰器顺序：`@PreAuthorize` 在外、`@log` 在最内，与 Spring 的 advisor 顺序一致 ——
  **被 403 拒绝的请求不留审计记录**（Java 的 `@Before` 通知同理）。

上述 13 个小节保留编号（有交叉引用），结论一并改为指向本条。唯一仍然成立的限制是
§28.3 的"请求级事务未复刻"—— 审计写在业务之后，**业务回滚时审计照样留下**。

---

## 43. `@PreAuthorize` 与参数解析的先后顺序 `[需注意]`

### 43.1 唯一的偏差：`GET /monitor/jobLog/{configId}`

**Java**
`@PreAuthorize` 是 AOP 切在**方法调用**上的；而路径变量的解析在
`InvocableHandlerMethod#getMethodArgumentValues` 里、**调用之前**就做完了。所以判定顺序是：

```text
路径变量缺失(500)  ->  权限(403)
```

`SysJobLogController#getInfo` 恰好踩中这个顺序：`@GetMapping("/{configId}")` 配的是
`@PathVariable Long jobLogId`（**没写名字**），Spring 从参数名推出 `jobLogId`，
而 URI 模板里只有 `configId` → `MissingPathVariableException`。线上实测：

```text
GET /monitor/jobLog/1    -> {"msg":"请求路径中缺少必需的路径变量[jobLogId]","code":500}
GET /monitor/jobLog/abc  -> {"msg":"请求路径中缺少必需的路径变量[jobLogId]","code":500}
```

`abc` 也是同一句 —— **参数缺失发生在类型转换之前**，根本轮不到 `Long` 转换失败。
因为没有 `monitor:job:query` 的账号也拿不到 403，**Java 侧这个端点对所有人都是 500**。

**Python**
`@pre_authorize_permi` 是函数装饰器，先于函数体执行，于是变成
"有权限 → 500、没权限 → 403"。

**影响**
线上唯一的真实调用方是持有 `monitor:job:query` 的管理员，两者一致。
把装饰器挪到 `Depends` 里能复刻 Java 的顺序，但那要改全仓 **242 处** `@pre_authorize_permi` 的写法，
代价远大于收益 —— **不做**。前端本来就不该调这个端点（它恒定 500）。

### 43.2 单值 `Long` 路径变量的报错文案不同（全仓既有）

**Java**
`MethodArgumentTypeMismatchException` → `GlobalExceptionHandler` 翻成

```text
请求参数类型不匹配，参数[jobId]要求类型为：'java.lang.Long'，但输入值为：'abc'
```

**Python**
单值路径变量声明成 `job_id: int` / `role_id: int`，`abc` 会在 pydantic 层失败，
落进 `RequestValidationError` 处理器，文案是

```text
{"msg":"job_id Input should be a valid integer, unable to parse string as an integer","code":500}
```

`code` 一致（500），HTTP 状态码一致（200），只有 `msg` 的措辞不同。

**已经是 Java 原文案的两种形态**
* `Long[]`（`DELETE /{jobIds}`）—— `parse_long_array` 显式抛
  `请求参数类型不匹配，参数[jobIds]要求类型为：'[Ljava.lang.Long;'，但输入值为：'abc'`；
* `Boolean`（`/common/download?delete=maybe`）—— `_spring_boolean` 抛
  `...要求类型为：'java.lang.Boolean'...`。

这两处有明确调用方（前端会传、会传错），所以逐字还原；单值 `Long` 路径变量传错是
**前端 bug**（`GET /system/role/abc` 这种不该出现），按"不为假想调用方加班"处理。

|---|---|---|---|
| 目标目录 | `car-monit-py/`（工作区内） | 与 Java 工程并排，便于 diff 与共享 `config/`、`sql/` | 独立仓库 |
| 并发模型 | sync `def` + sync SQLAlchemy | JDBC、`ThreadLocal`、PageHelper 全是有状态阻塞语义，sync 才能 1:1 | async/await + asyncmy（会把「线程本地分页」变成「请求上下文分页」，语义漂移） |
| ORM | SQLAlchemy **Core**（`text()`） | 97 个 MyBatis XML 就是 SQL 规范；过 ORM 重新生成 SQL 必然漂移 | SQLAlchemy ORM / Tortoise |
| 定时任务 | 镜像现实：`@Scheduled` 关闭、Quartz 用内存 JobStore | Java 线上确实没跑这些任务，擅自「修好」会凭空产生数据变更 | 直接启用（会改变生产行为） |
| Kafka / MinIO | 默认关闭 + 启动告警 | 当前环境不可达，默认启用只会制造噪音 | 默认启用 |
| `@Scheduled` 发现 | 登记而非修复 | 迁移原则第 4 条：不删除/不擅改「看似无用」的代码 | 直接补 `@EnableScheduling` |

---

## 44. 一致性复核（Phase 6：Java ↔ Python 逐端点、逐字段比对）`[无影响]`

这一节记录「从头重做一遍全量比对」的**方法、结果与改动**，以后再做同类复核照这个流程走。

### 44.1 六层校验与当前结果

| 层 | 手段 | 结果 |
|---|---|---|
| 路由 | `scripts/audit_endpoints.py`（解析 `@XxxMapping` 与 `@router.xxx`） | Java **501** / Python **502** / 两边都有 **501** / 缺失 **0** / 多出 `GET /health`（§1） |
| 域字段 | `scripts/audit_domains.py`（解析 Java 字段 + getter 与 pydantic 别名） | Java 150 / Python 117 / 可比 **115** / 仅 Java 35 / 仅 Python 2；属性、Excel、导出列 **零缺口** |
| 响应信封 | `scripts/audit_envelopes.py`（按控制器方法的返回类型与签名分类）+ 本文 §5.1 | 可比 **501** 全部有归类，见 §44.6.1 矩阵；`AjaxResult` 桶序、`TableDataInfo` / `R` 字段序由 `tests/test_core_types.py` 固定 |
| 文案 | `scripts/audit_messages.py`（双向：Java 字面量 ↔ Python 字面量） | Java **148** 种 / Python **155** 种；Java 有 Python 无 **0**、Python 有 Java 无 **0**；例外 10 + 死代码 3 文件 + 替代层 9 文件逐条登记（§44.6.2） |
| 端到端 | `pytest` 全量 + `scripts/smoke_test.py` | **3646 passed / 0 failed / 0 skipped**（3563 单测 + 83 条真实 MySQL/Redis 联调）；smoke **5/5**（真实 socket + 真 MySQL + 真 Redis） |
| 文档对照 | `scripts/gen_mapping_docs.py` 生成 `MAPPING_*.md` + `tests/test_mapping_docs.py` | 5 份切片表（base / manager / flow / tool / generator）覆盖 **54** 个控制器 / **341** 个端点，声明数 = 表格行数 = Java 真实映射数 |

> 前四层是**机器判定**的：脚本只解析源码，不读 `app/` 运行期状态，所以「两边一致」是可比出来的，
> 不是人工眼过的。任何一层出现非零差异，脚本都以非 0 退出码结束，可直接串进 CI。

### 44.2 本轮挖出并修正的四个真实缺陷

1. **`String.split` 全分隔符返回空数组，不是 `[""]`**（`app/common/core/text/convert.py`）
   Java 的 `resultSize` 可以一路减到 0：`",".split(",")` → `[]`。原实现带了「至少留一个」
   的保底，于是 `to_long_array(",")` 返回 `[None]` 而不是 `[]`，把 Java 的
   `in ()` 语法错误（500）悄无声息地变成了「删 0 行」。已在 `_java_split` 改正。
   回归阀：`tests/test_convert_arrays.py`（33 个用例）。

2. **`importGenTable` 的失败文案少了 `null` 形态**（`app/generator/service/gen_table_service.py`）
   `"导入失败：" + e.getMessage()`，而 NPE 的 `getMessage()` 是 `null`，
   `String.valueOf((Object) null)` 拼出来是 `"导入失败：null"`。原实现会把
   `java.lang.NullPointerException: ...` 整段塞进去。新增 `_java_exception_message` 还原。

3. **验证码响应的键序是插入序**（`app/api/common/captcha_controller.py`）
   `ajax["uuid"] = ...` / `ajax["img"] = ...` 绕过了 `put_in_order`。真实字节应为
   `{"msg":…,"img":…,"code":200,"uuid":…}`，原实现给的是 `msg, code, uuid, img`。已改走 `put_chain`。

4. **`getConfirmId` 同样直接赋值 `data`**（`app/api/manager/car_except_record_controller.py`）
   输出恰好相同（`data` 桶 4 > `code` 桶 3），但违反了「不得直写 AjaxResult」的不变量，一并改掉。

### 44.3 顺带改正的三处**注释/文档**错误（代码本来就对）

* `gen_table_mapper.py` 模块 docstring 说列表行是 `"columns": []`；实际 MyBatis 的
  `applyNestedResultMappings` 在 ResultSet 里一列都对不上时**根本不构造**嵌套对象，
  `columns` 停在 `null`。
* `java_hash_map.py` 曾写 `R<T> extends HashMap`；实际 `R.java:11` 是
  `implements Serializable`，是 POJO（字段序 `code, msg, data`）。
* `tests/test_login_controller.py` 曾断言「`HashMap` 保留插入序」—— 恰好说反了。

### 44.4 全站 `@Log` 调用点：233

Java 源里活的 `@Log(title` 共 **233** 处（另有 5 处整段被块注释掉，不计）：
`ruoyi-admin` 217 + `ruoyi-quartz` 9（`SysJobController` 6 + `SysJobLogController` 3）
+ `ruoyi-generator` 7（`GenController`）。Python 侧 `@log(` 同为 233，逐控制器零差异。
回归阀：`tests/test_log_aspect.py::TestMigrationInventory::test_call_site_count`。

### 44.5 明确**不**修的差异

* 单值 `Long` / `Boolean` 路径变量传错时的 `msg` 措辞（§43.2）；
* 权限校验与参数校验的先后（§43.1）；
* Java 自己就没实现的东西（`captchaEnabled` 标志、`@Log` 在部分控制器上缺失等）。

都不影响真实调用方，改它们反而会偏离 Java。

### 44.6 后来补上的两层机检

§44.2–44.5 是一次「人看一遍」的复核。要让它可重复，又补了两个只读源码的脚本；
它们和路由 / 域字段两个脚本一起，构成四项可串进 CI 的门禁（命令见 `MIGRATION_GUIDE.md` §6）。

#### 44.6.1 信封层：`scripts/audit_envelopes.py`

对每个 Java 控制器方法取**声明返回类型**，对每个 Python 处理函数取**返回注解**，按路由配对：

| Java | Python | 条数 | 判定依据 |
|---|---|---|---|
| `AjaxResult` | `AjaxResult` | 359 | 直接返回 |
| `TableDataInfo` | `TableDataInfo` | 100 | 分页列表 |
| `AjaxResult` | `Response` | 24 | **方法签名里有 `HttpServletResponse`**：Java 把响应体写进 `OutputStream`，尾部 `return AjaxResult.success(...)` 永远到不了客户端，所以 Python 返回裸 `Response` 才是等价的 |
| `void` | `Response` | 8 | 同上，Java 无返回值 |
| `R` | `R` | 5 | 大屏专用信封（字段序 `code, msg, data`） |
| `String` | `str` | 5 | 纯文本 |
| **合计** | | **501** | 与路由层可比数一致，无未归类项 |

第 3、4 行是这一层唯一有争议的地方，所以它**不是白名单**：脚本自己去方法签名里找
`HttpServletResponse`，找到才认 `Response`；找不到而不匹配就直接报错。

#### 44.6.2 文案层：`scripts/audit_messages.py`

用户可见的 `msg` 是前端写 `if (msg === '新增成功')` 的依据，最容易在重构里悄悄改掉。
脚本做**双向**比对：

1. **正向**：Java 里每个 `AjaxResult.error(...)` / `throw new XxxException(...)` 的字面量，
   必须在 Python 全量源码里作为子串出现（`msg` 常常是拼接出来的，字符串相等太严）。
2. **反向**：Python 里每个响应字面量，必须在 Java 里找得到。

两个方向都做了**脱敏后再比**：把占位符（`{}` / `{0}` / `%s` / `%d$s` / `'...'` / `[...]`）抹平，
再把 `"A" + x + "B"` 这种拼接折叠成 `AB`，最后还允许比一次「去掉所有单引号」的宽松形式。
为什么需要这些：

* Python 把文案提到了模块级常量（`USER_NOT_FOUND_MESSAGE = "用户不存在"`），只扫调用点会漏掉一大半
  （本轮把采样从 39 种提到 **155** 种，就是这么发现的）；
* Java 大量用拼接写文案（`"新增用户'" + user.getUserName() + "'失败…"`），字面量本身不成句；
* `退出成功` 等文案在 `ruoyi-admin/src/main/resources/i18n/messages.properties` 里，不在 `.java` 文件中；
* 异常处理器用 `String.format("请求路径中缺少必需的路径变量[%s]", ...)`，方括号也是占位区。

最终两侧各 0 条缺口。三类**已登记**的例外（不是「忽略」，每类都有名字和理由）：

| 类别 | 常量 | 数量 | 含义 |
|---|---|---|---|
| Java 有、Python 不该有 | `ALLOWLIST` | 10 种 | 每条写着原因：未被任何控制器接线的 Service、整段被块注释掉的分支、Python 没有的 MyBatis 启动期异常等 |
| 整份 Java 文件的文案不用搬 | `JAVA_ONLY_FILES` | 3 个 | `@Scheduled` 入口（Java 无 `@EnableScheduling`，从不触发）及其下游 |
| 整份 Python 文件豁免反向检查 | `PYTHON_ONLY_FILES` | 9 个 | 替代第三方库时自写的内部诊断（自研 Velocity 解释器、boto3 适配层、JDK NPE 文案复现等），Java 源码里本来就没这些字面量 |

护栏：`tests/test_audit_scripts.py`（**31** 条）钉住了折叠、i18n 资源读取、模块级常量收集、
方括号占位符这几条规则本身；规则被改坏会先挂这里，而不是等到审计报假阳性。

#### 44.6.3 本轮用例总数的对账

历史文档里的「3597」和 `pytest --collect-only` 数出来的「3538」差 59，原因查清了：
`tests/integration/test_real_backend.py` 在 MySQL / Redis 不可达时**整模块 skip**
（模块级 `pytest.skip(..., allow_module_level=True)`），而 `--collect-only` 默认不展开被跳过的模块，
于是 83 条联调用例凭空消失。`3597 = 3514 + 83` 是对的。

本轮结束后：

| 组成 | 条数 |
|---|---|
| 单元用例（88 个文件） | 3538 |
| 新增：`tests/test_audit_scripts.py` 从 24 → 31 | +7 |
| 新增：`tests/test_mapping_docs.py` | +16 |
| 真实 MySQL / Redis 联调 | 83 |
| **合计** | **3644** |

验证方式：`pytest --junitxml=_res.xml` 后数 `testcase` 节点，按 `classname` 含 `integration`
切分，得 **3561 单测 + 83 联调 = 3644**，与上表一致。

> 上表是 §44.6 那轮的快照。§44.7 那轮又加了 2 条用例（跨实现验签锚点、`/logout`
> 坏 token），当前全量为 **3646**（3563 单测 + 83 联调）。

### 44.7 双前端实例实测：8080→Java / 8081→Python

**怎么搭的**：同一个前端工程跑两个 dev server（8080 / 8081），用 `VUE_APP_PROXY_TARGET`
决定 `/dev-api` 代理到谁（`static/config.js` 加了一行 dev-only 覆盖，生产分支未动）。
Java 侧 `application.yml` 也写着 `server.port: 9989`，与 Python 撞车，所以 Java 用
`--server.port=8090` 起。

**结论**：两端都能用 `admin/Admin@2025-` 正常登录，15 个接口里 13 个逐字节一致，2 个差异
都不是缺陷：

| 接口 | 差异 | 结论 |
|---|---|---|
| `/getInfo` | Java 的 `user` / `user.dept` / `user.roles[]` 多出 `"params":{"@type":"java.util.HashMap"}` | 会话对象在 Redis 里过了一遍 FastJSON2 `WriteClassName`，空 `params` 里落进了 `@type` 条目，读回来不再“空”，`@JsonInclude(NON_EMPTY)` 就把它序列化了。前端从不读 `params`（§34.8 / §41.8） |
| `/monitor/cache` | `commandStats` 的顺序与计数不同 | Redis `INFO commandstats` 是实时累计值，且 redis-py 自身会发 `client|setinfo` / `info`；非确定性数据，不构成不一致 |

#### 44.7.1 真差异一：HMAC 密钥派生方式不同 → 跨后端 token 互不认

`token.secret` 两端都是 `abcdefghijklmnopqrstuvwxyz`（26 字符），但派生出两个不同的密钥：

| 实现 | 规则 | 26 字符得到 |
|---|---|---|
| Java（jjwt 0.9.1 `TextCodec.BASE64`） | 只解**整 4 字符块**，尾部 1–3 字符**直接丢弃** | 18 字节 `69b71d79…dbafc31` |
| 原 Python（`_decode_secret`） | 补 `=` 到 4 的倍数再解 | 19 字节 `69b71d79…dbafc31cb` |

多出来的 `cb` 就是“`yz` 两个字符按补齐规则解出来”的那一个字节。两端各自自洽、
但互不认：Java 签的 token 到 Python 报 `InvalidSignatureError`，Python 签的到 Java 被 401。

从 fat jar（`BOOT-INF/lib/jjwt-0.9.1.jar`）里取出实际打包的库跑 `TextCodec.BASE64.decode`，
规则确认是“丢弃尾块”：

| 输入字符数 | 26 | 27 | 19 | 3 | 2 |
|---|---|---|---|---|---|
| 解出字节数 | 18 | 18 | 12 | 0 | 0 |

`_decode_secret` 已按此改为先截断到 4 的整数倍；`tests/test_token_service.py` 同时钉住了
密钥 hex 和一枚**真实 Java 签发**的 token。

#### 44.7.2 真差异二：坏 token 的响应，Python 给 500，Java 给 200 + code 401

Java 里 `JwtException` 逃出过滤器后，容器做 **ERROR 派发到 `/error`**；`/error` 不在
`SecurityConfig` 的放行名单里，于是又走一遍链子（`OncePerRequestFilter` 会跳过 error 派发，
不会二次抛异常），这次是匿名 → `AuthenticationEntryPointImpl` 拦下 → `HTTP 200` +
`code 401`，**msg 里的路径是 `/error`** 而不是原始路径。实测：

| 请求 | Java | 改前 Python |
|---|---|---|
| `GET /getInfo` 无 token | 200 `{"code":401,"msg":"请求访问：/getInfo，…"}` | 一致 |
| `GET /getInfo` 坏 token | 200 `{"code":401,"msg":"请求访问：/error，…"}` | **500**（Spring 错误体） |
| `POST /logout` 坏 token | 200 `{"code":401,"msg":"请求访问：/error，…"}` | **500** |

`SecurityMiddleware` 的 `except` 分支原来直接渲染 500 错误页，现在改用
`AuthenticationEntryPointImpl.commence_for_uri("/error")` 渲染 401 信封。改完后 6 种组合
（有/无/坏 token × `/getInfo` / `/logout`）两端逐字节一致，跨后端 token 双向可用：

| 组合 | 改前 | 改后 |
|---|---|---|
| Java token → Python | 500 | 200 `code:200` |
| Python token → Java | 401 | 200 `code:200` |
| 垃圾 token → 两端 | 500 / 200+401 | 200 + `code:401`，路径 `/error` |

用例 3644 → **3646**（跨实现验签锚点 + `/logout` 坏 token；同时把“19 字节”“真 500”
两条写错的断言改成实测值）。

---

## 待确认清单

以下问题需要业务方确认后才能继续，**当前按「镜像 Java 现状」处理**：

> 原本的第 8 / 9 / 10 条（`ExcelUtil` 要不要补、八个 `export` 什么时候上线）
> 已在 Phase 3.18 **全部关闭**，见 §37。下面重新编号。

1. **§11 的 9 个 `@Scheduled` 任务**：是否本应运行？若本应运行，需要确认 `SnapshotFlowSyncTask` 等
   对数据的影响面。
2. **§9 的 Druid 监控台**：是否真有人在使用？（Java 侧被 `denyAll()`）
3. **`vehicleMonitor.baseUrl` = `http://127.0.0.1:9901`** 当前不可达，
   相关接口在 Phase 3 迁移时需要确认「外部服务不可用」时的预期行为（抛错 / 返回空 / 降级）。
4. **§19 `/logout` 是否真的接受任意 HTTP 方法**：需要对着运行中的 Java 实例验证
   （`curl -X GET http://<host>/logout`）。当前按「任意方法」实现。
5. **§21 非浏览器 UA 的落值**：是否需要与 `useragentutils` 的枚举逐一对齐。
   目前只对齐常见浏览器/系统组合（鉴权不受影响，仅审计列）。
6. **§22 char 验证码的默认字符集**：本项目用的是 `pro.fessional:kaptcha:2.3.3`（重新打包的 kaptcha），
   该 jar 不在本地 Maven 仓库，无法解包核对 `DEFAULT_TEXTPRODUCER_CHAR_STRING`。
   当前按上游 kaptcha 2.3 的 `abcde2345678gfynmnpwx` 实现。
   生产配置是 `ruoyi.captchaType: math`，**该分支不可达**，优先级最低。
7. **§25.6 PageHelper `orderBy` 到底是替换还是追加自带 `ORDER BY`**：本地 `.m2` 里没有
   `pagehelper-5.x` 的源码，无法确认 `OrderByParser` 的行为。当前实现是“语句自带
   `ORDER BY` 时忽略客户端排序”。若确认 Java 是**替换**，应把
   `page_helper._has_order_by` 分支改成“剥掉原有 `ORDER BY` 后改用客户端列”。
   只在客户端点表头排序且该语句自带排序时才有差异。
8. **§38.1 `/common/download` 的 `anonymous()` 要不要改成 `permitAll()`**：当前镜像 Java
   （已登录反而 403）。前端的下载请求必须**不带 token**。如果前端普遍插 token，要么改
   前端，要么改规则 —— 后者是行为改变。
9. **§37.3 `{profile}/download/` 的清理策略**：Java 也没有清理任务，每点一次导出就多一个
   xlsx。需要运维确认：加 cron（保留 N 天）/ 改成流式直出（不落盘，但与 Java 不同）。
10. **§37.4 `.xls` 导入**：现在只有 `.xlsx` 能导入。如果业务方确实需要 `.xls`，
    需要额外引入 `xlrd`（只读）并改写 `import_excel_sheet`。
11. **§28.3 请求级事务**：是否要把“一次请求一个事务”补回来？当前每个 Mapper 方法自己提交，
    `insertRole` / `updateRole` / `authDataScope` / `deleteRoleByIds` 都不具备原子性。
    补的话建议与 `LogAspect` 迁移一起做（两者都在切面层，改动面重合）。

## 45. 双端一致性校验轮的四处修复（2026-11-05）`[需注意]`

接线与逐档数据见 `evidence/_par_report.md`；工装是 `evidence/_par_*.py`。
复验口径：交付接线 Java(:9788/db0)↔apiJava(:9902) / Python(:9789/db7)↔apiPy(:9901)，
钉版把 Python 的 `vehicleMonitor.baseUrl` 也指到 9902 用来归因。

### 45.1 Forest 不看上游状态码（已修）

- **现象**：`/base/feerecords/{bigId}` 上游 500 时，Java 给 `{"code":500,"msg":"HTTP 500 ErrorContent={…}"}`，
  Python 给 `{"code":200,"msg":"操作成功","data":{…错误体…}}`。
- **Java 依据**：Forest 非 2xx 抛 `HttpProtocolException`，文案就是 `HTTP <status> ErrorContent=<响应体>`；
  `GlobalExceptionHandler` 再 `AjaxResult.error(e.getMessage())`。原先模块注释里"本项目调用点都不检查状态码，
  所以这里也只在 JSON 解析失败时抛错"的前提是错的 —— 只有 `feestationexit` 检查的是**响应体内的** `code`。
- **改动**：`app/base/service/forest/forest_client.py` 新增 `_parse_response()`，GET/POST 共用；
  同时把**空响应体**返回 `None`（Java 侧反序列化成 `null`，`/base/snapshotflow/earliest-time` 的 Java 形态
  就是 200 + 0 字节，Python 原来会抛"响应不是合法 JSON"）。
- **复验**：第 1 档 14 一致 → **19 一致**（20 条里只剩 Java 自身的日期反序列化缺陷）；
  钉版从 11 一致 → **19 一致**。

### 45.2 hutool `JSONObject` 透传不丢 null（已修）

- **现象**：`/base/feestationexit/list` 的 `rows[0]`，Java 没有 `cid`/`enaxlecount` 等 null 键，Python 有。
- **判据**（不是全局 null 策略）：`/manager/carinfo/list` 两端都照发 111 个 null 键，
  而 `/base/feestationexit/list` Java 一个都没有 —— 差别只在返回 `JSONObject` 的那个客户端。
- **改动**：`app/base/service/forest/http_ods_lwzxsfsj_fee_station_exit01_service.py` 增加
  `_drop_null_members()`，递归删掉 null 成员后再交给控制器（列表与详情两个方法都走）。
- **复验**：该档两条 MISSING 消失。

### 45.3 `AjaxResult.success(String)` 重载落错键（已修）

- **现象**：`/system/config/configKey/{configKey}` Java 是 `{"msg":"skin-blue","code":200}`（没有 `data`），
  Python 是 `{"msg":"操作成功","code":200,"data":"skin-blue"}`。Go 端早已复刻成 `msg`。
- **Java 依据**：`selectConfigByKey` 返回 `String`，静态分派命中 `success(String msg)`；
  三参构造里 `data` 为 null 时**不放** `data` 键。
- **改动**：`app/api/system/sys_config_controller.py` 改用 `AjaxResult.success_message(...)`，
  同步修正 4 条断言了错误形态的用例（`tests/test_sys_config_controller.py`）。

### 45.4 导出层的四个渲染规则（已修）+ 金额列的字段类型（已修）

模板导出（EasyPOI 型）Java 侧等价于 `String.valueOf(getter())`，Python 原来把原生
`datetime` / `Decimal` / `float` 直接交给 openpyxl，于是：

| 规则 | Java 形态 | 改动 |
|---|---|---|
| `java.util.Date`（Python 侧 `date`） | `Thu Aug 21 00:00:00 CST 2025` | `template_export._cell_value` 用 `java_date_to_string` |
| `java.sql.Timestamp`（Python 侧 `datetime`） | `2026-02-03 16:19:19.572`；无小数是 `.0` | `_timestamp_fraction`：9 位定长后去尾零、至少 1 位 |
| `BigDecimal` | `225.30` / `16075.00`（标度可见） | `format(value, "f")` 保标度 |
| 文本超 32767 字符 | POI 抛错被 `addCell` 吞 → "有样式无值"空格 | `_cell_value` / `_set_string` 置空（`MAX_CELL_TEXT_LENGTH`） |
| 模板引用了实体上没有的属性 | 空格子 | `_resolve` 返回 `None` 时不写值（原已正确） |

金额列的标度**在模型层就丢了**：`car_info` 的五列金额与 `buss_test.amount` 在 Java 是
`BigDecimal`、库里是 `decimal(19,2)`，Python 却标成 `Optional[float]` ⇒ `16075.00` 塌成
`16075.0`。已改成 `Optional[Decimal]`（`app/manager/domain/car_info.py`、`buss_test.py`）。

**复验**：导出 58 条 35 一致 → **46 一致**。`/manager/{carinfo,busstest,confimfree,exceptrecord,aduitfree,
gantrycar,gantrytrade}/export`、`/base/{geometry,snapshotflow,feerecords}/export`、`/manager/querylog/export`
全部逐格 0 差异。

### 45.5 三处"写入器表示差"：不是逻辑差，改不动也不该硬改

| 差异 | 证据 | 结论 |
|---|---|---|
| ExcelUtil 数值格：Java `<v>1.0</v>`，Python 文件里是 `<v>1</v>` | POI 只有 `setCellValue(double)`，整数被加宽；openpyxl 落盘按最短形式，实测 `ws['A1']=1.0` 存进去读回是 `int 1` | 数值两端相等、Excel 显示也相同（General）。要复刻 `1.0` 只能把格子写成文本，那会把**单元格类型**弄错（Java 是 `n`），是更假的"一致"。留在 FORMAT 桶里 |
| 审计堆栈：Java `\r\n`，Python `\n\n` | 实测 openpyxl 写入 `'line1\r\nline2'` 读回 `'line1\n\nline2'`（CR 被规范化）；库里的文本两端同源 | 同上，`/monitor/jobLog/export` 的 85 格全在这一类 |
| JSON 金额标度：Java `225.30`，Python `225.3` | pydantic `model_dump(mode="json")` 把 `Decimal` 转成 `float`（`to_jsonable` 注释也这么写），orjson 拿到的已是 float | 数值相等，字面不同。真要复刻需在 ORJSON 层用 `orjson.Fragment(str(Decimal))` 注入裸数字 —— 那是响应层的设计变更，影响**所有** decimal 列，需单独一轮 |

### 45.6 本轮顺带修掉的两个既有用例抖动（缺陷非本轮引入）

1. `tests/integration/test_real_backend.py::…test_total_equals_the_row_count[/system/user/list]`：
   基准 SQL 是 `SELECT COUNT(*) FROM sys_user WHERE del_flag='0'`，而
   `SysUserController#list` 无条件 `user.setUserType("1")`（注释就是"查询本单位的机构用户"），
   SQL 里体现为 `AND u.user_type = '1'`。库里只要存在非机构用户的未删除行，两边就对不上 ——
   本轮期间别的写面对拍会话留下了 `PARITY_J`（`user_type` 为空串，工号还在 `990160`→`990172` 之间变动），
   该用例就报 7 vs 8；而**两端 HTTP 实测始终同为 7、互相一致** —— 所以是用例基准条件不全，不是双端差异。
   已把基准补成 `… WHERE del_flag='0' AND user_type='1'`；其余 `EXACT_TOTALS` 条目逐个核对过
   控制器（`post/role/config/dict/data/notice/file`、`base/{section,toll,gantry,org}` 的 list
   都没有这类无条件 `set…()`，那几行 `setTenantId` 在 Java 里本来就是注释掉的），只有这一条需要改。
   （`PARITY_J` / `PARITY_G` 是别的会话留下的行，本轮未删。）
2. `tests/test_common_utils.py::TestDateUtils::test_get_timestamp_new2_is_two_days_earlier`：
   依赖 `get_timestamp()` 与 `get_timestamp_new2()` 两次 `datetime.now()` 落在**同一毫秒**：
   各自截到毫秒后，一旦跨毫秒边界，差值就是 `1天23:59:59.999xxx`，`delta.days` 掉到 1。
   整套并发跑时偶发失败，单跑必过。已改成按秒比较
   `1.99 < delta.total_seconds() / 86400 <= 2`。

稳定性复验：这两条所在的两组用例连跑 5 轮，每轮 27 项 0 失败；整套 `pytest`
（3646 项，`--junit-xml` 计数）`failures=0 errors=0 skipped=0`，约 41s。
