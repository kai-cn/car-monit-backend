# MAPPING_SYS_CONFIG.md — `sys_config` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §33。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `checkConfigKeyUnique` → `check_config_key_unique`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysConfigService` +
  `SysConfigServiceImpl`）在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。
- 本切片**只为 `Convert` 加了 `to_str` / `to_str_with_default`**（Java
  `Convert.toStr`），其余全部是新建文件；`main.py` 多了一行 `include_router`。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysConfigController.java` | `app/api/system/sys_config_controller.py` | **新建**；**8 个映射，迁移 7 个**（`export` 缺 `ExcelUtil`） |
| `ruoyi-system/.../service/ISysConfigService.java`<br>`ruoyi-system/.../service/impl/SysConfigServiceImpl.java` | `app/system/service/sys_config_service.py` | **新建**；9 个方法合并成一个 `SysConfigService` 类 |
| `ruoyi-system/.../mapper/SysConfigMapper.java`<br>`ruoyi-system/.../resources/mapper/system/SysConfigMapper.xml` | `app/system/mapper/sys_config_mapper.py` | **新建**；7 个方法 ↔ 7 条 statement，**严格 1:1** |
| `ruoyi-system/.../domain/SysConfig.java` | `app/system/domain/sys_config.py` | **新建**；5 个自有字段 + `BaseEntity` 6 个 + `CONFIG_CONSTRAINTS` |
| `ruoyi-common/.../utils/Convert.java`（`toStr`） | `app/common/core/text/convert.py`（`to_str` / `to_str_with_default`） | **改了这一处**：本切片是它唯一的调用方（`selectConfigByKey` 读缓存后转换） |
| `ruoyi-admin/.../RuoYiApplication.java`（`@SpringBootApplication` 扫描） | `app/main.py` | **改了一处**：`include_router(sys_config_router)` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `BaseController#startPage()` | `base_controller.start_page()` | 写 `PageDomain` 到 `ContextVar`，**不**发 SQL |
| `BaseController#getDataTable(List)` | `base_controller.get_data_table(rows)` | 有 `.total` 就用它，否则 `len(rows)` |
| `BaseController#toAjax(int)` | `base_controller.to_ajax(row)` | `row > 0` → `success()`，否则 `error()`（`"操作失败"`） |
| `BaseController#getUsername()` | `security_utils.get_username()` | `add` 写 `createBy` / `edit` 写 `updateBy`（是**字符串**，与 `sys_index_menu` 的 `Long` 相反） |
| `@PathVariable Long[] configIds` | `base_controller.parse_id_array(raw)` | 逗号串 → `List[int]` |
| 无注解实体参数 `SysConfig config` | `bind_query_params(SysConfig, request.query_params)` | 无 `@RequestBody` 即按 query string 绑定 |
| `@Validated @RequestBody SysConfig` | `ValidConfig = Annotated[SysConfig, Depends(_validated_config)]` | 做成依赖，让校验排在 `@PreAuthorize` **之前** |
| `@PreAuthorize("@ss.hasPermi(...)")` | `@pre_authorize_permi("system:config:...")` | 6 处；`getConfigKey` **没有** |
| `@RepeatSubmit` | **未迁移** | 全工程都没有重复提交拦截 |
| `@Log(title = "参数管理", ...)` | **未迁移** | 不写 `sys_oper_log`，见 §33.3 |
| `Constants.SYS_CONFIG_KEY` | `cache_constants.SYS_CONFIG_KEY` | 值是 `"sys_config:"` |
| `Convert.toStr(Object)` | `convert.to_str(value)` | `null` → `""`；`"null"` 字符串**不会**被吃掉 |
| `AjaxResult.success(Object)` | `AjaxResult.success_data(data)` | `data is None` 时**整个键省略** |

### 1.3 测试

| 层 | Python 测试文件 | 函数数 → 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_config_mapper.py` | 25 → **26** | `sqlwhereSearch` 的 2 个条件与 `!= null` / `!= null and != ''` 的区别 / `selectConfigList` 的 5 个 `<if>` 与顺序 / 无 `order by` / `insertConfig` 无 `useGeneratedKeys` / `deleteConfigByIds` 的 `in ()` |
| Service | `tests/test_sys_config_service.py` | 36 → **40** | 逐键写缓存 vs 全清 / `init()` 不自动调用 / `selectConfigByKey` 返回 `None` 的情形 / 内置参数拦截（含尾空格文案）/ `getCacheKey(null)` → `"sys_config:null"` |
| Controller | `tests/test_sys_config_controller.py` | 46 → **56** | 7 条路由与注册顺序 / 6 个权限点 + `getConfigKey` 免权限 / 唯一性校验在写库之前 / 两条文案插 `configName` / 六条校验的文案与顺序 / `configType` 无约束 |

合计 **122** 条（26 + 40 + 56）。Phase 3.14 之前全量 **1623 passed**，本切片 **+122**。

---

## 2. 控制器：8 个映射

### 2.1 端点逐条对照

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list(SysConfig config)` | `list_configs(config)` | GET `/system/config/list` | `system:config:list` |
| `export(HttpServletResponse)` | **未迁移** | GET `/system/config/export` | — |
| `getInfo(@PathVariable Long configId)` | `get_info(config_id)` | GET `/system/config/{config_id}` | `system:config:query` |
| `getConfigKey(@PathVariable String configKey)` | `get_config_key(config_key)` | GET `/system/config/configKey/{config_key}` | **无**（登录即可） |
| `add(@Validated @RequestBody SysConfig)` | `add(config)` | POST `/system/config` | `system:config:add` |
| `edit(@Validated @RequestBody SysConfig)` | `edit(config)` | PUT `/system/config` | `system:config:edit` |
| `remove(@PathVariable Long[] configIds)` | `remove(config_ids)` | DELETE `/system/config/{config_ids}` | `system:config:remove` |
| `clearCache()` | `clear_cache()` | DELETE `/system/config/clearCache` | `system:config:remove` |

### 2.2 注册顺序（不是装饰性的）

FastAPI 按**注册顺序**匹配，Spring 的 `AntPathMatcher` 优先字面量。为了两边同结果，
模块里的声明顺序是：

```
/list -> /configKey/{config_key} -> /{config_id}
      -> POST "" -> PUT ""
      -> DELETE /clearCache -> DELETE /{config_ids}
```

- `/clearCache` **必须**在 `/{config_ids}` 之前，否则 `DELETE /system/config/clearCache`
  会被当成 `configIds = "clearCache"`，在 `parse_id_array` 处 `int("clearCache")` 失败；
- `/list` 与 `/configKey/...` 同理必须在 `/{config_id}` 之前 —— 后者只收数字，
  `"list"` / `"configKey"` 都会转 `int` 失败。

**回归用例** `tests/test_sys_config_controller.py::TestRouteTable`。

### 2.3 查询参数绑定

`list(SysConfig config)` 没有 `@RequestBody`，Spring 用 `ServletModelAttributeMethodProcessor`
把 query string 逐个 setter 进去。Python 用 `bind_query_params`：

| query 参数 | 落到 |
|---|---|
| `configName` / `configKey` / `configType` | 同名字段 |
| `params[beginTime]` / `params[endTime]` | `config.params["beginTime"]` / `["endTime"]` |
| 未声明的键 | **静默丢弃**（`WebDataBinder.ignoreUnknownFields=true`） |

注意 `configName=""` 会**原样保留**空串（`str_strip_whitespace=False`），
mapper 里再按 `!= null and != ''` 判断，所以空串等于"不过滤"。

### 2.4 校验位置：`@Validated` 在 `@PreAuthorize` 之前

Spring MVC 先解析/校验方法参数，再进入 `@PreAuthorize` 的方法代理 —— 所以**没有权限**
的用户提交一个非法 body，看到的是**校验错误**而不是 403。Python 侧把校验做成
`Depends(_validated_config)`（依赖先于函数体执行）复刻这个顺序。

`add` / `edit` 都是 `ValidConfig`，`remove` / `clear_cache` / `get_info` 直接是
`@pre_authorize_permi` 装饰器，两者不可混写。

---

## 3. Service：9 个方法

### 3.1 方法对照

| Java | Python | 备注 |
|---|---|---|
| `@PostConstruct init()` | `init()` | **不挂到 FastAPI 生命周期**（§33.4） |
| `@DataSource(MASTER) selectConfigById(Long)` | `select_config_by_id(config_id)` | 新建只带 id 的实体走 `selectConfig`，**没有**独立 statement |
| `selectConfigByKey(String)` | `select_config_by_key(config_key)` | 先读缓存，空/未命中才回源 |
| `selectConfigList(SysConfig)` | `select_config_list(config)` | 纯转发 |
| `insertConfig(SysConfig)` | `insert_config(config)` | `row > 0` 时写**这一个**键 |
| `updateConfig(SysConfig)` | `update_config(config)` | 同上 |
| `deleteConfigByIds(Long[])` | `delete_config_by_ids(config_ids)` | 先逐个体检内置参数，再删 |
| `clearCache()` | `clear_cache()` | `keys("sys_config:*")` + 批量删 |
| `checkConfigKeyUnique(SysConfig)` | `check_config_key_unique(config)` | 回 `"1"` / `"0"` |
| `private getCacheKey(String)` | `get_cache_key(config_key)`（**public**，测试要用） | `None` → `"null"` |

### 3.2 缓存策略：增改写键、删除全清

与字典切片（§32）**完全不同**：

| 操作 | 字典 | 参数配置 |
|---|---|---|
| 新增 / 修改 | 清空 `sys_dict:*` | 只写 `sys_config:<key>` |
| 删除 | 清空 `sys_dict:*` | 清空 `sys_config:*` |
| 读未命中 | 回源并写回该类型 | 回源并写回该键 |

删除只能全清，因为 Java 在删除前没收集键名，删完就查不到 `config_key` 了。照抄。

`update_config` 写缓存的键是 `config.config_key`（**入参**的值）；如果这次更新刚好
把键名也改了，缓存里会多出一个新键、旧键仍是旧值 —— 这是 Java 原样（等 TTL 或
`clearCache` 才收敛）。**不要"顺手"再加一次 `keys + delete`**。

**回归用例** `tests/test_sys_config_service.py::TestCache`。

---

## 4. Mapper：7 条 statement

### 4.1 语句对照

| XML `id` | Python | 说明 |
|---|---|---|
| `<sql id="selectConfigVo">` | 常量 `SELECT_CONFIG_VO` | 10 列，**Tab 缩进照抄** |
| `<sql id="sqlwhereSearch">` | `_build_select_config_sql(config)` | 2 个条件，无 `order by` |
| `selectConfig` | `select_config(config)` | `selectOne`：无行 → `None` |
| `selectConfigList` | `select_config_list(config)` | **分页点**（`take_page()`） |
| `checkConfigKeyUnique` | `check_config_key_unique(config_key)` | 入参是**键名**，SQL 自带 `limit 1` |
| `insertConfig` | `insert_config(config)` | 动态列，**无** `useGeneratedKeys` |
| `updateConfig` | `update_config(config)` | `<set>`，`update_time = sysdate()` 无条件 |
| `deleteConfigById` | `delete_config_by_id(config_id)` | **Java 侧无调用方**，按第 4 条照留 |
| `deleteConfigByIds` | `delete_config_by_ids(config_ids)` | `<foreach>`，空数组拼 `in ()` |

> 8 行 ≠ 7 条 statement：`selectConfigVo` 与 `sqlwhereSearch` 是 `<sql>` 片段，
> 真正的 statement 是 7 条（2 select 单行 + 1 select 列表 + 1 unique + 1 insert +
> 1 update + 2 delete = 8）。其中 `deleteConfigById` 无调用方，**全部迁移**。

### 4.2 `selectConfig` 与 `selectConfigList` 是两条不同的语句

这是本切片最容易搞错的地方：

| | `selectConfig` | `selectConfigList` |
|---|---|---|
| 条件数 | **2** | **5** |
| `configId` | `!= null` | **没有** |
| `configName` | **没有** | `!= null and != ''`（`like`） |
| `configKey` | `!= null and != ''`（`=`） | `!= null and != ''`（`like`） |
| `configType` | **没有** | `!= null and != ''`（`=`） |
| 时间区间 | **没有** | `params.beginTime` / `params.endTime` |
| `order by` | 无 | 无 |
| 用途 | 按主键 / 按键名取单行 | 列表分页 |

两个 `configKey` 的语义不同：单行取是**等值**，列表是**模糊**。合并会改变结果集。

因为没有 `order by`：

- 分页的 `LIMIT` 结果顺序由 MySQL 决定（Java 一样）；
- 语句不带 `ORDER BY` 时 PageHelper 会把客户端的 `orderByColumn` / `isAsc` 追加进来，
  所以前端点表头排序**是生效的**；换成带 `order by` 的语句反而会关掉这个能力。

### 4.3 `updateConfig` 里 `remark` 只判 `!= null`

`<set>` 里其它 5 列都是 `!= null and != ''`，只有 `remark` 是 `<if test="remark != null">`：

```xml
<if test="remark != null">remark = #{remark},</if>
```

于是 `remark: ""` 会把列**清成空串**（而不是跳过），其它 5 列传空串则跳过。
这是本模块唯一一列"空串有语义"的字段，`_UPDATE_CONFIG_COLUMNS` 的第三项
`require_text` 就是为它准备的。

`insertConfig` 里**没有**这个特例：`remark` 与其它列一样是 `!= null and != ''`，
所以新增时传空串等于不写这一列（用库默认值）。**两条语句的判据不对称**，与
§31.8 的公告是同一类现象，方向相反。

---

## 5. 实体与校验

### 5.1 字段

| Java | Python | 类型 |
|---|---|---|
| `configId` | `config_id` | `Long` → `Optional[int]` |
| `configName` | `config_name` | `String` |
| `configKey` | `config_key` | `String`（唯一，缓存键就是它） |
| `configValue` | `config_value` | `String`（库里可能是 `NULL`） |
| `configType` | `config_type` | `String`（`Y` 内置 / `N` 非内置） |
| `BaseEntity` 的 6 个 | 继承 | `createBy` / `createTime` / `updateBy` / `updateTime` / `remark` / `params` |

`params` 在 `BaseEntity` 上带 `@JsonInclude(NON_EMPTY)`，所以详情接口的 JSON 里
**没有** `params` 键（前端拿到的 `SysConfig` 只有 10 个字段）。

### 5.2 六条约束与文案（顺序决定 `msg`）

Java 把 `@NotBlank` / `@Size` 挂在 **getter** 上，顺序即 getter 声明顺序：

| # | 字段 | 约束 | 文案 |
|---|---|---|---|
| 1 | `configName` | `@NotBlank` | 参数名称不能为空 |
| 2 | `configName` | `@Size(max=100)` | 参数名称不能超过100个字符 |
| 3 | `configKey` | `@NotBlank` | 参数键名**长度**不能为空 |
| 4 | `configKey` | `@Size(max=100)` | 参数键名长度不能超过100个字符 |
| 5 | `configValue` | `@NotBlank` | 参数键值不能为空 |
| 6 | `configValue` | `@Size(max=500)` | 参数键值长度不能超过500个字符 |

两个坑：

1. 第 3 条的 `@NotBlank` 文案里多了"**长度**"两个字（对比第 1 条）—— 照抄；
2. `configType` **一个约束都没有**，传 `"X"` 也能入库，只是不会被删除保护。

多个字段同时违规时，只有**第一条**进入 `msg`（与 `bean_validation` 的
"首个错误即返回"一致）。

---

## 6. 未迁移项

| Java | 原因 | 客户端表现 |
|---|---|---|
| `export(HttpServletResponse)` + `ExcelUtil<SysConfig>` | `ExcelUtil`（Apache POI）未迁移 | `GET /system/config/export` 被 `/{config_id}` 兜住 → **HTTP 200 + code 500** |
| `@Log(title = "参数管理", businessType = ...)` | `LogAspect` 未迁移 | 不写 `sys_oper_log`，业务结果不变 |
| `@RepeatSubmit(interval = 1000)` | 拦截器未迁移 | 一秒内重复提交同样会写两行（键名不同时） |
| `@PostConstruct` 触发 `init()` | 数据源惰性创建 | 首个 `selectConfigByKey` 回源填充，结果一致 |

`export` 一旦落地，`SysConfigController#export` 的写法与已迁的
`sys_user` / `sys_post` / `sys_role` / `sys_dict_*` 相同：`list` 的同一份查询、
`ExcelUtil.exportExcel(response, list, "参数数据")`。见
[COMPATIBILITY.md](COMPATIBILITY.md) 待确认清单第 8-10 条。
