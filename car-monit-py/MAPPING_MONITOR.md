# MAPPING_MONITOR.md — `monitor` 包切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §39。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectOperLogList` → `select_oper_log_list`。
- 接口与实现（`ISysOperLogService` + `SysOperLogServiceImpl`）在 Python 里合并成一个类，
  因为 Python 没有"接口"这个概念。
- **本切片是全项目唯一直接把 Redis 与宿主机指标暴露成 JSON 的地方**，
  所以第 3、4、5、6 节都比别的切片长。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/monitor/SysOperlogController.java` | `app/api/monitor/sys_operlog_controller.py` | **新建**；**4/4 映射** |
| `ruoyi-admin/.../web/controller/monitor/SysLogininforController.java` | `app/api/monitor/sys_logininfor_controller.py` | **新建**；**4/4 映射** |
| `ruoyi-admin/.../web/controller/monitor/SysUserOnlineController.java` | `app/api/monitor/sys_user_online_controller.py` | **新建**；**2/2 映射** |
| `ruoyi-admin/.../web/controller/monitor/CacheController.java` | `app/api/monitor/cache_controller.py` | **新建**；**1/1 映射** |
| `ruoyi-admin/.../web/controller/monitor/ServerController.java` | `app/api/monitor/server_controller.py` | **新建**；**1/1 映射** |
| `ruoyi-system/.../service/ISysOperLogService.java`<br>`.../service/impl/SysOperLogServiceImpl.java` | `app/system/service/sys_oper_log_service.py` | **新建**；5 个方法，**全是"转发一行"** |
| `ruoyi-system/.../service/ISysLogininforService.java`<br>`.../service/impl/SysLogininforServiceImpl.java` | `app/system/service/sys_logininfor_service.py` | 登录链路早就有 `insertLogininfor`；本切片**补 3 个方法**（list / delete / clean） |
| `ruoyi-system/.../service/ISysUserOnlineService.java`<br>`.../service/impl/SysUserOnlineServiceImpl.java` | `app/system/service/sys_user_online_service.py` | **新建**；数据源是 **Redis**，没有 mapper |
| `ruoyi-system/.../mapper/SysOperLogMapper.java`<br>`.../resources/mapper/system/SysOperLogMapper.xml` | `app/system/mapper/sys_oper_log_mapper.py` | **新建**；XML **5 条 statement** ↔ 5 个方法 |
| `ruoyi-system/.../mapper/SysLogininforMapper.java`<br>`.../resources/mapper/system/SysLogininforMapper.xml` | `app/system/mapper/sys_logininfor_mapper.py` | **新建**；XML **4 条 statement** ↔ 4 个方法 |
| `ruoyi-system/.../domain/SysOperLog.java` | `app/system/domain/sys_oper_log.py` | **新建**；`extends BaseEntity`，16 列 `@Excel` |
| `ruoyi-system/.../domain/SysLogininfor.java` | `app/system/domain/sys_logininfor.py` | **新建**；`extends BaseEntity`，9 列 `@Excel` |
| `ruoyi-system/.../domain/SysUserOnline.java` | `app/system/domain/sys_user_online.py` | **新建**；**不继承** `BaseEntity`，`loginTime` 是 epoch **毫秒** |
| `ruoyi-framework/.../web/domain/Server.java`<br>`.../web/domain/server/{Cpu,Jvm,Mem,Sys,SysFileInfo}.java` | `app/framework/web/domain/server.py` | **新建**；**6 个类合进 1 个文件**（原因见 §6.1） |
| `ruoyi-common/.../utils/Arith.java` | `app/common/utils/arith.py` | **新建**；`Server` / `Cpu` / `Mem` / `Jvm` 全靠它 |
| `com.github.oshi:oshi-core`（Maven 依赖） | **`psutil==6.1.1`** | 依赖**早已在** `pyproject.toml` 里（标注 `<- oshi-core`），本切片只是开始用它 |
| `com.ruoyi.system.service.ISysLogininforService`（登录链路注入点） | 未改动 | 登录 / 登出 / 注册三条异步链路早在其它切片就用了 |

### 1.2 被改动的已有文件（只有三处）

| 文件 | 改动 | 原因 |
|---|---|---|
| `app/system/service/sys_logininfor_service.py` | 新增 `select_logininfor_list` / `delete_logininfor_by_ids` / `clean_logininfor` 三个方法 + `List` 导入 | 登录链路只需要 `insertLogininfor`；`/monitor/logininfor` 的另外三个端点此前没有对应物 |
| `app/main.py` | 5 行 `include_router`（operlog / logininfor / online / cache / server） | 挂路由 |
| `tests/test_security_filter.py` | `PROTECTED_UNMAPPED_PATH` 从 `/monitor/online/list` 改为 **`/migration/probe/never-mapped`** | `monitor` 包的 `list` 一旦注册，探针路径就不再是 404，那三条"未映射路径"用例会去连真实 MySQL / Redis |

`app/api/monitor/__init__.py` 与 `app/framework/web/domain/__init__.py` 是**新建的空包标记**（只有一行 docstring）。

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| `Arith` | `tests/test_arith.py` | **23** | `div` 的默认 scale=10 / HALF_UP / 零被除数 / 除数为零 / 负 scale；`round_half_up` 的 2.5→3、3.5→4；四个调用点的算式 |
| Server DTO | `tests/test_server_domain.py` | **45** | `Cpu.getTotal()` 的乘 100 不除 / `Mem`、`Jvm` 的 GB·MB 换算 / `Sys` 的 `os.name` 取法 / `SysFileInfo.typeName` 的卷标 / `convertFileSize` 的四档与取整 / 真实采集冒烟 |
| operlog Mapper | `tests/test_sys_oper_log_mapper.py` | **27** | `businessType = 0` 被 OGNL 吃掉 / `order by oper_id desc` / `<if>` 判据与顺序 / insert 用 `sysdate()` / `truncate` |
| logininfor Mapper | `tests/test_sys_logininfor_mapper.py` | **21** | `status` 是字符串 / 列序与 resultMap 的错位 / `sysdate()` / `truncate` |
| 三个 Service | `tests/test_monitor_services.py` | **29** | 参数与返回值原样穿透 / 不吞异常 / 单例与 `reset_*` / Redis 惰性解析 |
| operlog Controller | `tests/test_sys_operlog_controller.py` | **26** | 4 条路由与顺序 / `businessTypes` 的重复参数与逗号串 / 导出 `msg` 是文件名 / `toAjax(0)` → code 500 |
| logininfor Controller | `tests/test_sys_logininfor_controller.py` | **17** | 4 条路由 / `clean` 必须排在 `{infoIds}` 之前 / `status="0"` 不被丢 / 时间范围进 `params` |
| online Controller + Service | `tests/test_sys_user_online_controller.py` | **23** | 四个分支 / `reverse` 之后的顺序 / 脏会话被丢弃 / `total` 是列表长度 / `userName` 别名 / 强退恒 200 |
| cache Controller | `tests/test_monitor_cache_controller.py` | **39** | `INFO` 文本解析（含 `# ` 段、`:` 二次出现、空白） / `substringBetween` 的四种失败态 / `cmdstat_` 前缀剥离 / 三条命令的次序 / 权限精确匹配 |
| server Controller | `tests/test_monitor_server_controller.py` | **14** | 1 条路由 / `copyTo()` 先于序列化 / 每请求新建 `Server` / 异常不吞（HTTP 200 + code 500） |

合计 **264** 条；本切片结束时全量实测 **2942 passed**（Phase 3.19 结束时 **2678**），
Phase 3.21 叠加后 **2972**。

---

## 2. 控制器：12 个映射，全部迁移

| Java | Python | Method / Path | 权限点 |
|---|---|---|---|
| `SysOperlogController#list(SysOperLog)` | `list_oper_logs(oper_log)` | GET `/monitor/operlog/list` | `monitor:operlog:list` |
| `SysOperlogController#export(SysOperLog)` | `export(oper_log)` | GET `/monitor/operlog/export` | `monitor:operlog:export` |
| `SysOperlogController#clean()` | `clean()` | DELETE `/monitor/operlog/clean` | `monitor:operlog:remove` |
| `SysOperlogController#remove(Long[])` | `remove(oper_ids)` | DELETE `/monitor/operlog/{operIds}` | `monitor:operlog:remove` |
| `SysLogininforController#list(SysLogininfor)` | `list_logininfor(logininfor)` | GET `/monitor/logininfor/list` | `monitor:logininfor:list` |
| `SysLogininforController#export(SysLogininfor)` | `export(logininfor)` | GET `/monitor/logininfor/export` | `monitor:logininfor:export` |
| `SysLogininforController#remove(Long[])` | `remove(info_ids)` | DELETE `/monitor/logininfor/{infoIds}` | `monitor:logininfor:remove` |
| `SysLogininforController#clean()` | `clean()` | DELETE `/monitor/logininfor/clean` | `monitor:logininfor:remove` |
| `SysUserOnlineController#list(String, String)` | `list_online(ipaddr, user_name)` | GET `/monitor/online/list` | `monitor:online:list` |
| `SysUserOnlineController#forceLogout(String)` | `force_logout(token_id)` | DELETE `/monitor/online/{tokenId}` | `monitor:online:forceLogout` |
| `CacheController#getInfo()` | `get_info()` | GET `/monitor/cache` | `monitor:cache:list` |
| `ServerController#getInfo()` | `get_info()` | GET `/monitor/server` | `monitor:server:list` |

`clean` 与 `remove` **共用同一个权限点**（`*:remove`）—— Java 原文如此，能删一条就能清空整表。

### 2.1 `clean` 必须注册在 `{ids}` **之前**

Java 里 `SysLogininforController` 把 `clean()` 写在 `remove()` **后面**，靠的是
`AntPathMatcher` 偏爱字面量；FastAPI 按**注册顺序**匹配，所以 Python 侧必须把
`clean` 放在 `{ids}` 前面，否则 `clean` 会被当成 `infoIds="clean"` → `int("clean")` 失败
→ code 500。两边**净行为一致**，只是顺序不同。两个模块的用例都钉住了这一条。

### 2.2 `SysOperLog` 的 `businessTypes` 不能走通用绑定器

Java 的形参是 `SysOperLog operLog`（**无** `@RequestBody`），query string 里
`businessTypes` 是 `Integer[]`；RuoYi 前端用 `tansParams` 把它发成**重复键**
（`businessTypes=0&businessTypes=1`），Spring 的 `ArrayToArrayConverter` 逐元素转
`Integer`。

`bind_query_params` 只处理 `str` / `bool` / `int` / `datetime` 标量，`List[int]` 会直接
塞给 pydantic 然后失败，所以 `sys_operlog_controller` 里有一个专用绑定器
`_query_oper_log`：标量字段仍交给通用绑定器，`businessTypes` 由
`_parse_business_types` 单独解析（**同时**支持重复键与逗号串）。

`businessTypes=`（空值）在 Java 里会抛 `NumberFormatException` → code 500，
Python 侧抛 `ValueError`，走同一条兜底路径。

### 2.3 `SysLogininfor` 没有这个问题

`SysLogininfor.status` 是 **`String`**（`"0"` / `"1"`），查询条件走普通的
`!= null and != ''`，没有 `businessType` 那个"`0` 被当空串吃掉"的 OGNL 陷阱；
也没有数组字段，所以可以直接 `bind_query_params(SysLogininfor, request.query_params)`。

### 2.4 两个 `export` 的返回体是**文件名**

`AjaxResult.success(String)` 重载挑中的是 `success(String msg)` —— 文件名落在 **`msg`**，
**没有 `data` 键**，文件本身在 `{profile}/download/` 下（§37.2）。工作表名分别是
`操作日志` / `登录日志`（常量 `EXPORT_SHEET_NAME`）。

`export` **不调** `startPage()`，导出的是全量命中行。

### 2.5 `/monitor/online/list` 没有分页

Java 直接 `getDataTable(userOnlineService.selectOnlineByInfo(...))`，没有 `startPage()`：

- `total` 是**列表长度**（`new PageInfo(list).getTotal()`），不是总数；
- 前端传的 `pageNum` / `pageSize` **完全不看**，`pageSize=10` 也会拿到全部在线用户。

`ipaddr` / `userName` 两个形参都**没有** `@RequestParam`，走 Spring 的默认
`required = false`；第二个参数的 query 名是驼峰的 `userName`，所以 Python 侧写成
`Query(default=None, alias="userName")`。

### 2.6 强退不看返回值

`redisCache.deleteObject(...)` 的返回值被丢弃，`return AjaxResult.success()` 是无条件的
—— 对一个已经过期的 `tokenId` 强退，同样是 `code 200`。`tokenId` 是
`LoginUser.token`（UUID），**不是** JWT。

### 2.7 `/monitor/cache` 是三条裸 Redis 命令

Java 用三条 `RedisCallback` 取 `INFO` / `INFO commandstats` / `DBSIZE`。
`RedisTemplate#execute` 在 `redis-py` 里没有对应物（后者本身就是"裸连接"风格），
所以直接 `RedisCache.client.execute_command(...)`（§4.3）。

### 2.8 `/monitor/server` 必然阻塞 1 秒

`Server.setCpuInfo()` 为了算占用率先取 ticks、`Thread.sleep(1000)`、再取一次
（`OSHI_WAIT_SECOND = 1000`）。**不要为了"性能"去掉睡眠**，否则 `total` / `used` 会算成 0。

---

## 3. 服务层

| Java | Python | 备注 |
|---|---|---|
| `SysOperLogServiceImpl#insertOperlog` | `insert_operlog(oper_log) -> int` | Java 签名是 `void`；**返回 int 只为用例断言**，控制器侧没有调用点 |
| `#selectOperLogList` | `select_oper_log_list(oper_log)` | 分页点在 mapper 内部（`take_page()`） |
| `#deleteOperLogByIds` | `delete_oper_log_by_ids(oper_ids)` | 返回值**没有**抛给 `toAjax` 之外的地方 |
| `#selectOperLogById` | `select_oper_log_by_id(oper_id)` | **无调用方**（Java 控制器没有 `/{operId}` 详情接口），死代码照搬 |
| `#cleanOperLog` | `clean_oper_log()` | `truncate`，DDL，隐式提交，不可回滚 |
| `SysLogininforServiceImpl#selectLogininforList` | `select_logininfor_list(logininfor)` | 本切片新增 |
| `#deleteLogininforByIds` | `delete_logininfor_by_ids(info_ids)` | 本切片新增 |
| `#cleanLogininfor` | `clean_logininfor()` | 本切片新增 |
| `SysUserOnlineServiceImpl#selectOnlineByInfo` | `select_online_by_info(ipaddr, user_name)` | 四个分支与 Java 逐字对应 |
| `#selectUserOnlineList` | `select_user_online_list()` | **无调用方**，死代码照搬 |
| `#loginUserToUserOnline` | `login_user_to_user_online(user)` | `user` 或 `user.user` 为 `None` 时返回 `None` |
| `@Autowired XxxService` | `get_xxx_service()` / `reset_xxx_service()` | Spring 默认单例；`reset_*` 是测试用后门 |

三个 service 都**没有** `@Transactional`（Java 侧也没有），异常原样冒到全局处理器。

### 3.1 `selectOnlineByInfo` 的三个必抄细节

1. **`Collections.reverse` 之后才丢 `null`** —— 结果是"键顺序的倒序、丢掉 null"。
2. **过滤用的是 RuoYi 覆写的 `isNotEmpty`**，它内部 `trim()`，所以**全空格串 `" "` 算空**
   —— 等同于不传该过滤条件，会返回全部在线用户。
3. **分支 3 比分支 1、2 多一个 `isNotNull(user.getUser())`**：只有"按用户名过滤"这条
   路径会先判空；"按 ip 过滤"时 Java 直接 `user.getIpaddr()`，脏值 → NPE → code 500。
   Python 侧**不加兜底**，保持同样的失败面。

### 3.2 谁在写 `sys_oper_log` / `sys_logininfor`

| 表 | 写入方 | 当前状态 |
|---|---|---|
| `sys_oper_log` | `LogAspect`（`@Log` 切面）异步调 `insertOperlog` | **`LogAspect` 未迁移** → 没有任何代码路径会写这张表（§25.2） |
| `sys_logininfor` | `AsyncFactory`（登录 / 登出 / 注册三条异步链路） | **已迁移**，登录链路正常落库 |

所以 `/monitor/operlog` 的读接口目前只对**历史数据**有意义；`/monitor/logininfor` 是活的。

---

## 4. Mapper

### 4.1 `SysOperLogMapper`（5 条 statement）

| XML `id` | Python | 说明 |
|---|---|---|
| `selectOperLogVo`（`<sql>`） | `SELECT_OPER_LOG_VO` | 16 列，顺序与 XML 一致 |
| `selectOperLogList` | `select_oper_log_list` | **自带 `order by oper_id desc`** → 客户端排序被忽略 |
| `selectOperLogById` | `select_oper_log_by_id` | 无 `del_flag` 过滤（该表没有这一列） |
| `insertOperlog` | `insert_operlog` | `oper_time` 取 **`sysdate()`**（数据库时钟，不是应用时钟）；**无** `useGeneratedKeys` |
| `deleteOperLogByIds` | `delete_oper_log_by_ids` | `in` 子句按 id 数量展开 |
| `cleanOperLog` | `clean_oper_log` | `truncate table sys_oper_log` |

**`businessType` 的 OGNL 陷阱**：XML 写的是 `<if test="businessType != null and businessType != ''">`，
而 `businessType` 是 `Integer`；OGNL 对"数字 vs 字符串"统一转 `double`，而
`OgnlOps.doubleValue("")` 返回 **`0.0`**。于是 `businessType = 0`（"其它"）时条件为
`0 != 0` → **假**，筛选被丢掉 —— **选"其它"会查出全部记录**。
`status` 用的是 `<if test="status != null">`，没有这个问题。

### 4.2 `SysLogininforMapper`（4 条 statement）

| XML `id` | Python | 说明 |
|---|---|---|
| `selectLogininforList` | `select_logininfor_list` | 列序与 `resultMap` 的**声明顺序不一致**，按列名映射（不是按下标） |
| `insertLogininfor` | `insert_logininfor` | `login_time` 取 **`sysdate()`**；**无** `useGeneratedKeys` |
| `deleteLogininforByIds` | `delete_logininfor_by_ids` | `in` 子句按 id 数量展开 |
| `cleanLogininfor` | `clean_logininfor` | `truncate table sys_logininfor` |

两个 `clean` 在 XML 里都是 **`<update>`** 标签（不是 `<delete>`），照抄。

### 4.3 Redis 侧：没有 mapper

`/monitor/online` 与 `/monitor/cache` 完全不碰数据库：

| Java | Python |
|---|---|
| `redisCache.keys("login_tokens:*")` | `RedisCache.keys(...)` → **`KEYS`**（O(N) 阻塞），与 Spring Data Redis 一致 |
| `redisCache.getCacheObject(key)` | `RedisCache.get_cache_object(key)` → FastJson2 的 JSON 文本反序列化 |
| `connection.info()` | `client.execute_command("INFO")` → `parse_info()` 拍平 |
| `connection.info("commandstats")` | `client.execute_command("INFO", "commandstats")` |
| `connection.dbSize()` | `client.dbsize()` |

---

## 5. 实体

| Java | Python | 基类 | 关键差异 |
|---|---|---|---|
| `SysOperLog` | `app/system/domain/sys_oper_log.py` | `BaseEntity` | 16 列 `@Excel`；`operTime` 带 `@JsonFormat("yyyy-MM-dd HH:mm:ss")`；`businessTypes` 是**查询专用**数组字段（不是列） |
| `SysLogininfor` | `app/system/domain/sys_logininfor.py` | `BaseEntity` | 9 列 `@Excel`；`status` 是 **`String`** |
| `SysUserOnline` | `app/system/domain/sys_user_online.py` | **无基类** | 裸 POJO：没有 `searchValue` / `remark` / `params`；`loginTime` 是 epoch **毫秒数字**，**不**格式化 |

`SysOperLog.businessTypes` 在 Java 里是 `private Integer[] businessTypes`，**不在**
`resultMap` 里、也不在 `insertOperlog` 的列里 —— 它只用来拼 `in` 条件。Jackson 默认
序列化所有 getter，所以查询结果里它永远是 `"businessTypes": null`（Python 侧的
`Optional[List[int]]` 输出同一个键同一个值）。

---

## 6. `Server` DTO：本项目"最不像 Java"的一处

### 6.1 为什么 6 个类挤在 1 个文件

Java 的布局是 `web/domain/Server.java` + `web/domain/server/{Cpu,Jvm,Mem,Sys,SysFileInfo}.java`。
Python **不允许**同目录下 `server.py` 与 `server/` 并存（模块与包同名会互相遮蔽），
所以 `Server` 的五个内部 DTO 一并放进 `app/framework/web/domain/server.py`。
类名、字段名、getter 的算式逐字对应，只是少了那层目录。

### 6.2 三个"getter 不等于字段"

| 类 | 字段里存的 | getter 返回的 |
|---|---|---|
| `Cpu.total` / `sys` / `used` / `wait` / `free` | **tick 差值**（原始计数） | **百分比** |
| `Mem` / `Jvm` 的 `total` / `used` / `free` | **字节数** | **GB / MB**，2 位小数 |
| `Jvm.name` / `startTime` / `runTime` / `inputArgs` | **没有字段** | 每次现算 |

所以 `cpu.total != cpu.get_total()` —— 序列化时只走 getter。

### 6.3 `Cpu.getTotal()` 是 Java 的既有 bug（照抄）

```java
public double getTotal() {
    return Arith.round(Arith.mul(total, 100), 2);   // 只乘 100，没有除以 total
}
```

其余四个 getter 都是 `xxx / total * 100`。于是 JSON 里 `cpu.total` 是 "tick 总和 × 100"
这种量级（正常机器上几万），**不是百分比**。前端拿它当"总使用率"显示会溢出，
但改了就是行为改变 —— 见 `COMPATIBILITY.md` §39.2。

### 6.4 OSHI → psutil 的对应

| OSHI | psutil | 备注 |
|---|---|---|
| `CentralProcessor#getSystemCpuLoadTicks()` + `TickType` | `psutil.cpu_times()` | **单位不同**：OSHI 是 tick（Linux `HZ = 100`），psutil 是**秒**；`_TICKS_PER_SECOND = 100.0` 把两者对齐 |
| `CentralProcessor#getLogicalProcessorCount()` | `psutil.cpu_count(logical=True)` |  |
| `GlobalMemory` | `psutil.virtual_memory()` | `used = total - available`（与 OSHI 的 `total - available` 一致） |
| `OperatingSystem#getFileSystem().getFileStores()` | `psutil.disk_partitions(all=False)` |  |
| `OSFileStore#getTotalSpace()` / `getUsableSpace()` | `psutil.disk_usage(...)` |  |
| `OSFileStore#getName()` | `_file_store_name(...)` | **卷标**，不是挂载点也不是设备路径；Windows 走 `GetVolumeInformationW`，POSIX 用 `Partition.device` |
| `System.getProperty("os.name")` | `_java_os_name()` | **不是** `platform.system()`：Windows → `"Windows 11"`，macOS → `"Mac OS X"`，Linux → `"Linux"`（不带内核版本） |
| `System.getProperty("os.arch")` | `platform.machine()` | `"amd64"` / `"aarch64"` |
| `System.getProperty("user.dir")` | `os.getcwd()` |  |

Windows 上 psutil **不给** `nice` / `irq` / `softirq` / `steal` / `iowait`，
`_read_cpu_ticks()` 一律按 0 处理（OSHI 在 Windows 上同样恒为 0）。

### 6.5 `Jvm` 面板没有 Python 对应物 —— 换成宿主机内存

`Runtime.getRuntime()` 在 Python 里没有等价物。若把 `total` 填 0，`usage` 会是 100%
（假黑条）；若填 `max` 而 `free` 填 0，会是 0%。两种都难看。

最终取值：`total = max = 物理内存`，`free = 可用内存`。于是 getter 算出的
`used = total - free` / `usage = (total - free) / total * 100` 就是**整机内存使用率**，
与 `Mem` 面板同源但含义明确。`version` 是 Python 版本、`home` 是 `sys.prefix`、
`name` 是 `"CPython 3.12.x"`、`startTime` / `runTime` 复用 `date_utils` 的三个函数、
`inputArgs` 是 `str(sys.argv)`。见 §39.4。

### 6.6 `convertFileSize` 的取整

| 档位 | 格式 | 说明 |
|---|---|---|
| `>= GB` | `%.1f GB` | 恒 1 位小数 |
| `>= MB` | 值 `> 100` → `%.0f MB`，否则 `%.1f MB` |  |
| `>= KB` | 值 `> 100` → `%.0f KB`，否则 `%.1f KB` |  |
| 其它 | `%d B` | `int(size)` 截断 |

Java 的 `%f` 用 **HALF_UP**，Python 的 `format` 用**银行家舍入**，所以 `_java_format`
先经 `arith.round_half_up` 定量再格式化。

---

## 7. `Arith`

| Java | Python | 说明 |
|---|---|---|
| `add` / `sub` / `mul` | `add` / `sub` / `mul` | `new BigDecimal(Double.toString(v))` ⇔ `Decimal(str(v))` |
| `div(v1, v2)` | `div(v1, v2, scale=10)` | 默认保留 **10** 位；被除数为 0 直接回 `0` |
| `div(v1, v2, scale)` | `div(v1, v2, scale)` | `scale < 0` 抛 `ValueError`（消息与 Java 一致） |
| `round(v, scale)` | **`round_half_up(v, scale)`** | **改了名**：Python 内建 `round` 是银行家舍入，直接同名会静默出错 |

`div` 必须 `quantize` 到 `scale` 位 —— 第一版漏了，返回 28 位有效数字，`convertFileSize`
的字符串会变成 `"2.7 GB"` 之外的东西。用例 `tests/test_arith.py::TestDiv` 钉住了这一点。

---

## 8. 路由注册与安全规则

`app/main.py` 追加 5 行（顺序即注册顺序，`{ids}` 之前已由模块内部保证）：

```python
application.include_router(monitor_operlog_router)
application.include_router(monitor_logininfor_router)
application.include_router(monitor_online_router)
application.include_router(monitor_cache_router)
application.include_router(monitor_server_router)
```

**安全规则没有改动**：`/monitor/**` 在 `security_config.py` 的规则表里不存在逐条匹配项，
所以 12 个端点全部落到 `anyRequest().authenticated()` —— 与 Java 的
`SecurityConfig` 一致（Java 也没有为 `monitor` 写 `antMatchers`）。

权限点由 `@pre_authorize_permi(...)` 逐个校验，**精确匹配**（不是通配）：一个只有
`monitor:cache:*` 的账号访问 `/monitor/cache` 会被拒（code 403）。

---

## 9. 与 Java 的已知差异（一览）

细节与理由见 [COMPATIBILITY.md](COMPATIBILITY.md) §39。

| # | 差异 | 影响 |
|---|---|---|
| 39.1 | `LogAspect` 未迁移 → `sys_oper_log` 没有新行 | 操作日志页只看得到历史数据 |
| 39.2 | `Cpu.total` 沿用 Java 的"乘 100 不除" bug | 前端该字段会溢出（Java 同样溢出） |
| 39.3 | `Cpu` 用 psutil 的秒 × 100 冒充 OSHI tick | 只影响 `Cpu.total` 的量级，百分比字段与单位无关 |
| 39.4 | `Jvm` 面板映射成宿主机内存 | 语义变化，但数值自洽 |
| 39.5 | 磁盘采集失败的分区**跳过**而不是整页 500 | 少一块盘 vs 整页报错 |
| 39.6 | `info` / `commandStats` 的键顺序稳定（Java 的 `Properties` 无序） | 内容相同，仅顺序不同 |
| 39.7 | `businessTypes` 额外接受逗号串 | 比 Java 宽松（RuoYi 前端不会发逗号串） |
| 39.8 | `parse_info` 的空白处理按 `Properties.load` 对齐 | 真实 `INFO` 无差异 |
| 39.9 | `/monitor/server` 依赖 psutil 6.1.1 | 已在 `pyproject.toml`，无需新装 |
