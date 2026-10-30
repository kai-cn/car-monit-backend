# MAPPING_SYS_DICT.md — `sys_dict` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §32。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectDictDataByTypeMore` → `select_dict_data_by_type_more`。
- 接口与实现（`ISysDictTypeService` + `SysDictTypeServiceImpl`）在 Python 里合并成一个类，
  因为 Python 没有"接口"这个概念；`default` 方法也直接变成实例方法。
- 本切片**唯一新增的基础设施是字典缓存**（`DictUtils`）—— 后面的 `sys_config`、
  `manager` / `base` 包里的导出都会复用它。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysDictTypeController.java` | `app/api/system/sys_dict_type_controller.py` | **新建**；**8 个映射，迁 7 个**（`export` 未迁） |
| `ruoyi-admin/.../web/controller/system/SysDictDataController.java` | `app/api/system/sys_dict_data_controller.py` | **新建**；**8 个映射，迁 7 个**（`export` 未迁） |
| `ruoyi-system/.../service/ISysDictTypeService.java`<br>`ruoyi-system/.../service/impl/SysDictTypeServiceImpl.java` | `app/system/service/sys_dict_type_service.py` | **新建**；12 个方法合并成一个 `SysDictTypeService` |
| `ruoyi-system/.../service/ISysDictDataService.java`<br>`ruoyi-system/.../service/impl/SysDictDataServiceImpl.java` | `app/system/service/sys_dict_data_service.py` | **新建**；9 个方法（含两个 `default` Map 方法） |
| `ruoyi-system/.../mapper/SysDictTypeMapper.java`<br>`ruoyi-system/.../resources/mapper/system/SysDictTypeMapper.xml` | `app/system/mapper/sys_dict_type_mapper.py` | **新建**；10 个方法 ↔ 9 条 statement + 1 个 `<sql>` 片段 |
| `ruoyi-system/.../mapper/SysDictDataMapper.java`<br>`ruoyi-system/.../resources/mapper/SysDictDataMapper.xml`<br>（注意 XML 在 `resources/mapper/` 根下，**不在** `mapper/system/`） | `app/system/mapper/sys_dict_data_mapper.py` | **新建**；11 个方法 ↔ 11 条 statement + 1 个 `<sql>` 片段 |
| `ruoyi-common/.../core/domain/entity/SysDictType.java` | `app/common/core/domain/entity/sys_dict_type.py` | **新建**；`@NotBlank` / `@Size` 约束原样搬 |
| `ruoyi-common/.../core/domain/entity/SysDictData.java` | `app/common/core/domain/entity/sys_dict_data.py` | **新建**；多一个 `@computed_field` 复刻 `getDefault()` |
| `ruoyi-common/.../utils/DictUtils.java` | `app/common/utils/dict_utils.py` | **新建**；9 个静态方法 → 9 个模块函数 |
| `ruoyi-framework/.../config/SecurityConfig.java` | `app/framework/config/security_config.py` | **未改动**；字典的 7 条路径全部落在 `authenticated()` 里，没有匿名特例 |
| `ruoyi-admin/.../RuoYiApplication.java`（组件扫描） | `app/main.py` | **改了两处**：`include_router(sys_dict_type_router)` / `include_router(sys_dict_data_router)` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `BaseController#startPage()` | `base_controller.start_page()` | 两个 `list` 都调了；**只有** `selectDictTypeList` / `selectDictDataList` 消费它 |
| `BaseController#getDataTable(List)` | `base_controller.get_data_table(rows)` | `total` 取自 `PageHelper` |
| `BaseController#toAjax(int)` | `base_controller.to_ajax(rows)` | `rows > 0` → `success()`，否则 `error("操作失败")` |
| `SecurityUtils#getUsername()` | `security_utils.get_username()` | 控制器写 `createBy` / `updateBy` |
| `@PathVariable Long[] dictIds` | `base_controller.parse_id_array(raw)` | 逗号串 → `List[int]` |
| `@Migration` 无注解实体参数 `SysDictType dictType` | `Depends(_query_dict_type)` → `bind_query_params(...)` | 无 `@RequestBody` 即按 query string 绑定 |
| `@Validated @RequestBody SysDictType` | `Annotated[SysDictType, Depends(_validated_dict_type)]` | 做成 `Depends` 是为了让校验排在 `@PreAuthorize` **之前** |
| `@PreAuthorize("@ss.hasPermi(...)")` | `@pre_authorize_permi("system:dict:...")` | 类型 6 处、数据 5 处（见 §2.1） |
| `@Log(title = "字典类型" / "字典数据", ...)` | **未迁移** | 不写 `sys_oper_log`，见 §32.3 |
| `RedisCache`（`spring-data-redis`） | `app/common/core/redis/redis_cache.py` | `keys()` / `delete_object()` / `set_cache_object()` 逐条对应 |
| `CacheConstants.SYS_DICT_KEY` | `app/common/constant/cache_constants.py` | 前缀 `"sys_dict:"` |
| `AjaxResult.success(Object)` | `AjaxResult.success_data(data)` | `data is None` 时**整个键省略**；`success_data([])` 保留 `"data": []` |

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| 缓存工具 | `tests/test_dict_utils.py` | **45** | 键前缀 / `None` 与 `[]` 的区别 / 单值分支**不** `stripEnd` / 多值按**字典表顺序**而不是入参顺序 / `containsAny` 参数顺序被对调 / `getDictValue` 的 else 分支 NPE / `KEYS sys_dict:*` / `stripEnd` 是字符集剥离 |
| 类型 Mapper | `tests/test_sys_dict_type_mapper.py` | **32** | 5 个 `<if>` 的顺序与判据 / `_text` 与 `is_not_empty` 的差别 / `selectDictTypeAll` 不消费分页 / 7 列投影 / 不回写主键 / `<set>` 的判据不对称 / `where` 不以 `and` 开头 |
| 数据 Mapper | `tests/test_sys_dict_data_mapper.py` | **42** | `status = '0'` 写死 / `in (:t0,:t1)` 的拆串 / Java `split` 丢尾部空串 / `selectDictLabel` 无 `limit 1` / `countDictDataByType` 不过滤状态 / insert↔update 判据矩阵 / `updateDictDataType` |
| 类型 Service | `tests/test_sys_dict_type_service.py` | **41** | `init()` 不连库 / 缓存优先、`[]` 视为未命中 / `-dadadadas` 哨兵（含 `" "`）/ 尾逗号保留 / 删除的"全过才删" / 子表先改父表后改的**已知缺口** / 清缓存时机 |
| 数据 Service | `tests/test_sys_dict_data_service.py` | **24** | `row > 0` 才清缓存 / `selectDictLabel` 直连库 / 两个 Map 方法**不读缓存**、不过滤状态 / 重复键抛 `IllegalStateException` |
| 类型 Controller | `tests/test_sys_dict_type_controller.py` | **44** | 7 条路由与注册顺序 / `export` 落进 `/{dict_id}` 回 500 / 权限矩阵 / `clearCache` 不被当成 id 串 / 唯一性校验在插入之前 / 文案里用 `dictName` |
| 数据 Controller | `tests/test_sys_dict_data_controller.py` | **43** | 7 条路由 / `/type` 与 `/typemore` 无权限点 / 未命中 `[]` vs `{}` / 5 条校验文案 / `cssClass` 可省 |

合计 **271** 条（45 + 32 + 42 + 41 + 24 + 44 + 43）。
另外 `tests/test_sys_notice_mapper.py` 因 §32.12 的缺陷修复补了 1 条，
全量套件从 1351 → **1623 passed**。

---

## 2. 控制器：两个 8 映射

### 2.1 端点逐条对照

`SysDictTypeController` —— `/system/dict/type`：

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list(SysDictType dictType)` | `list_dict_types(dict_type)` | GET `/list` | `system:dict:list` |
| `export(HttpServletResponse response, SysDictType dictType)` | **未迁移** | GET `/export` | — |
| `getInfo(@PathVariable Long dictId)` | `get_info(dict_id)` | GET `/{dict_id}` | `system:dict:query` |
| `optionselect()` | `optionselect()` | GET `/optionselect` | **无**（登录即可） |
| `add(@Validated @RequestBody SysDictType dictType)` | `add(dict_type)` | POST `` | `system:dict:add` |
| `edit(@Validated @RequestBody SysDictType dictType)` | `edit(dict_type)` | PUT `` | `system:dict:edit` |
| `clearCache()` | `clear_cache()` | DELETE `/clearCache` | `system:dict:remove` |
| `remove(@PathVariable Long[] dictIds)` | `remove(dict_ids)` | DELETE `/{dict_ids}` | `system:dict:remove` |

`SysDictDataController` —— `/system/dict/data`：

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list(SysDictData dictData)` | `list_dict_data(dict_data)` | GET `/list` | `system:dict:list` |
| `export(HttpServletResponse response, SysDictData dictData)` | **未迁移** | GET `/export` | — |
| `getInfo(@PathVariable Long dictCode)` | `get_info(dict_code)` | GET `/{dict_code}` | `system:dict:query` |
| `dictType(@PathVariable String dictType)` | `dict_type(dict_type)` | GET `/type/{dict_type}` | **无** |
| `dictTypeMore(@PathVariable String dictType)` | `dict_type_more(dict_type)` | GET `/typemore/{dict_type}` | **无** |
| `add(@Validated @RequestBody SysDictData dictData)` | `add(dict_data)` | POST `` | `system:dict:add` |
| `edit(@Validated @RequestBody SysDictData dictData)` | `edit(dict_data)` | PUT `` | `system:dict:edit` |
| `remove(@PathVariable Long[] dictCodes)` | `remove(dict_codes)` | DELETE `/{dict_codes}` | `system:dict:remove` |

三个"无权限点"端点（`optionselect` / `type` / `typemore`）都是前端每个下拉框都会调的
数据源，补 `@PreAuthorize` 会直接白屏 —— 与 §31.3 的 `notice/list` 同类，**别顺手补**。

### 2.2 注册顺序（不是装饰性的）

FastAPI 按**注册顺序**匹配，Spring 的 `AntPathMatcher` 优先字面量。两个模块的声明顺序是：

```
类型 : /list → /optionselect → /{dict_id} → POST "" → PUT "" → DELETE /clearCache → DELETE /{dict_ids}
数据 : /list → /type/{t} → /typemore/{t} → /{dict_code} → POST "" → PUT "" → DELETE /{dict_codes}
```

`/clearCache` **必须**排在 `/{dict_ids}` 之前：否则 `DELETE /system/dict/type/clearCache`
会被当成 `dict_ids = "clearCache"`，在 `parse_id_array` 处失败。
`/optionselect` 同理，必须排在 `/{dict_id}` 之前（`"optionselect"` 转不成 `int`）。

### 2.3 查询参数绑定

`GET /list` 的形参在 Java 里是**没有注解的实体**，Spring 用 `WebDataBinder` 按名字绑定。
Python 用 `bind_query_params(SysDictType, request.query_params)`：

| Java 字段 | query 参数名 | Python 属性 | 出现在哪个 `list` |
|---|---|---|---|
| `dictName` | `dictName` | `dict_name` | 类型 |
| `dictType` | `dictType` | `dict_type` | 两者都有 |
| `status` | `status` | `status` | 两者都有 |
| `dictLabel` | `dictLabel` | `dict_label` | 数据 |
| `params[beginTime]` / `params[endTime]` | 同名 | `params` | **只有类型**有这一对条件 |

`pageNum` / `pageSize` / `orderByColumn` / `isAsc` 走 `start_page()` 那条通道，**不**在实体上。

---

## 3. Service

### 3.1 `SysDictTypeService`：12 个方法

| Java（`ISysDictTypeService`） | Python | 说明 |
|---|---|---|
| `@PostConstruct init()` | `init()` | 遍历类型表逐个预热；**不挂到 FastAPI 生命周期**（§32.4） |
| `selectDictTypeList(SysDictType)` | `select_dict_type_list(dict_type)` | 分页点在 mapper |
| `selectDictTypeAll()` | `select_dict_type_all()` | 给 `optionselect` 用，**不**分页 |
| `selectDictDataByType(String)` | `select_dict_data_by_type(dict_type)` | 缓存优先；库里也没有返回 `None` |
| `selectDictDataByTypeMore(String)` | `select_dict_data_by_type_more(dict_type)` | `"a,b"` 多类型；两处原文缺陷照抄（§32.6） |
| `selectDictTypeById(Long)` | `select_dict_type_by_id(dict_id)` | 一行转发 |
| `selectDictTypeByType(String)` | `select_dict_type_by_type(dict_type)` | 一行转发 |
| `deleteDictTypeByIds(Long[])` | `delete_dict_type_by_ids(dict_ids)` | 全过才删，否则 `CustomException` |
| `clearCache()` | `clear_cache()` | 只清 Redis，不动库 |
| `insertDictType(SysDictType)` | `insert_dict_type(dict_type)` | `row > 0` 才清缓存 |
| `@Transactional updateDictType(SysDictType)` | `update_dict_type(dict_type)` | 子表先改名（**无事务**，§32.5） |
| `checkDictTypeUnique(SysDictType)` | `check_dict_type_unique(dict_type)` | 返回 `"1"` / `"0"` / `-1` 三态字符串 |

`checkDictTypeUnique` 的三态（照抄 RuoYi 约定）：

| 场景 | 返回值 | 控制器处理 |
|---|---|---|
| 查到记录且 `dictId` 相同 | `"0"` | 不改（校验通过） |
| 查到记录且 `dictId` 不同 | `"1"` | 回 `新增/修改字典失败，字典类型已存在` |
| 查不到记录 | `-1` | 校验通过 |

### 3.2 `SysDictDataService`：9 个方法

| Java（`ISysDictDataService`） | Python | 说明 |
|---|---|---|
| `selectDictDataList(SysDictData)` | `select_dict_data_list(dict_data)` | 分页点在 mapper |
| `selectDictLabel(String, String)` | `select_dict_label(dict_type, dict_value)` | 直连库，**不过缓存** |
| `selectDictDataById(Long)` | `select_dict_data_by_id(dict_code)` | 一行转发 |
| `deleteDictDataByIds(Long[])` | `delete_dict_data_by_ids(dict_codes)` | 物理删除 |
| `insertDictData(SysDictData)` | `insert_dict_data(dict_data)` | `row > 0` 才清缓存 |
| `updateDictData(SysDictData)` | `update_dict_data(dict_data)` | 同上 |
| `default selectDictDataMap(String dictValue)` | `select_dict_data_map(dict_value)` | `{dictValue: dictLabel}`；无端点、无缓存、不过滤状态 |
| `default selectDictDataLaleMap(String dictValue)` | `select_dict_data_lale_map(dict_value)` | `{dictLabel: dictValue}`；`Lale` 是 `Label` 的笔误，照抄 |

两个 Map 方法的形参名叫 `dictValue`，**实际传的是字典类型** —— 命名照抄，不要改。
它们和 `DictUtils.getDictLabel` 是两条不同的路（一个直连库、含停用项；一个走缓存、只有
`status='0'`），不要合并。

### 3.3 缓存契约（谁清、谁不清）

| 方法 | 清缓存？ | 触发条件 |
|---|---|---|
| `insert_dict_type` / `insert_dict_data` | 是 | `row > 0` |
| `update_dict_type` / `update_dict_data` | 是 | `row > 0` |
| `delete_dict_type_by_ids` / `delete_dict_data_by_ids` | 是 | `count > 0` |
| `clear_cache` | 是 | 无条件 |
| 所有 `select_*` | 否 | — 未命中时**写回**（`select_dict_data_by_type*` 两条） |

写操作清的是**整个** `sys_dict:*`，不是当前类型：因为 `updateDictData` 可能连 `dictType`
一起改，只清一个键会留下脏数据（§32.11）。

---

## 4. Mapper

### 4.1 语句对照

`sys_dict_type_mapper.py`：

| XML | Python |
|---|---|
| `<sql id="selectDictTypeVo">` | `SELECT_DICT_TYPE_VO`（逐字照抄，含那行用 Tab 缩进的 `from`） |
| `<select id="selectDictTypeList">` | `select_dict_type_list()` ← **分页点** |
| `<select id="selectDictTypeAll">` | `select_dict_type_all()` ← **不**分页 |
| `<select id="selectDictTypeById">` | `select_dict_type_by_id()` |
| `<select id="selectDictTypeByType">` | `select_dict_type_by_type()` |
| `<select id="checkDictTypeUnique">` | `check_dict_type_unique()` |
| `<delete id="deleteDictTypeById">` | `delete_dict_type_by_id()` |
| `<delete id="deleteDictTypeByIds">` | `delete_dict_type_by_ids()` |
| `<insert id="insertDictType">` | `insert_dict_type()` |
| `<update id="updateDictType">` | `update_dict_type()` |

`sys_dict_data_mapper.py`：

| XML | Python |
|---|---|
| `<sql id="selectDictDataVo">` | `SELECT_DICT_DATA_VO` |
| `<select id="selectDictDataList">` | `select_dict_data_list()` ← **分页点** |
| `<select id="selectDictDataByType">` | `select_dict_data_by_type()` ← `status = '0'` 写死 |
| `<select id="selectDictDataByTypeMore">` | `select_dict_data_by_type_more()` ← `in (...)` |
| `<select id="selectDictLabel">` | `select_dict_label()` ← **没有** `limit 1` |
| `<select id="selectDictDataById">` | `select_dict_data_by_id()` |
| `<select id="countDictDataByType">` | `count_dict_data_by_type()` ← **不过滤** `status` |
| `<delete id="deleteDictDataById">` | `delete_dict_data_by_id()` |
| `<delete id="deleteDictDataByIds">` | `delete_dict_data_by_ids()` |
| `<insert id="insertDictData">` | `insert_dict_data()` |
| `<update id="updateDictData">` | `update_dict_data()` |
| `<update id="updateDictDataType">` | `update_dict_data_type()` |

两个模块都**没有**"XML 有、接口无"的孤儿语句（对比 `sys_menu` 的 §29.8）。

### 4.2 `selectDictTypeList` 的 5 个 `<if>`

| 顺序 | 字段 | 判据 | 传 `""` 时 | 片段 |
|---|---|---|---|---|
| 1 | `dictName` | `!= null and != ''` | 跳过 | `dict_name like concat('%', ?, '%')` |
| 2 | `status` | `!= null and != ''` | 跳过 | `status = ?` |
| 3 | `dictType` | `!= null and != ''` | 跳过 | `dict_type like concat('%', ?, '%')` |
| 4 | `params.beginTime` | `!= null and != ''` | 跳过 | `date_format(create_time,'%y%m%d') >= date_format(?, '%y%m%d')` |
| 5 | `params.endTime` | `!= null and != ''` | 跳过 | `date_format(create_time,'%y%m%d') <= date_format(?, '%y%m%d')` |

排序固定 `order by create_time desc`（XML 自带，客户端 `orderByColumn` 会被忽略）。

### 4.3 `selectDictDataList` 的 3 个 `<if>`

| 顺序 | 字段 | 判据 | 传 `""` 时 | 片段 |
|---|---|---|---|---|
| 1 | `dictType` | `!= null and != ''` | 跳过 | `dict_type = ?`（**等值**，不是 like） |
| 2 | `dictLabel` | `!= null and != ''` | 跳过 | `dict_label like concat('%', ?, '%')` |
| 3 | `status` | `!= null and != ''` | 跳过 | `status = ?` |

排序固定 `order by dict_sort asc`。

**这两张表的"判据"必须用 `value is not None and value != ""`，不能用
`string_utils.is_not_empty`** —— 后者镜像的是 RuoYi 会 `trim()` 的 `StringUtils.isEmpty`，
会把只有一个空格的过滤值也判成空，从而少一个条件。

### 4.4 insert / update 的判据矩阵

`insertDictType`（`create_time` 无条件 `sysdate()`）：

| 字段 | 判据 |
|---|---|
| `dict_name` / `dict_type` / `remark` / `create_by` | `!= null and != ''` |
| `status` | **只有** `!= null` |

`updateDictType`（`update_time` 无条件 `sysdate()`）：

| 字段 | 判据 | 传 `""` 的后果 |
|---|---|---|
| `dict_name` / `dict_type` / `update_by` | `!= null and != ''` | 该列**不动** |
| `status` / `remark` | **只有** `!= null` | **清列**（写成 `''`） |

`insertDictData`：

| 字段 | 判据 |
|---|---|
| `dict_label` / `dict_value` / `dict_type` / `css_class` / `list_class` / `is_default` / `remark` / `create_by` | `!= null and != ''` |
| `dict_sort` / `status` | **只有** `!= null` |

`updateDictData`：

| 字段 | 判据 | 传 `""` 的后果 |
|---|---|---|
| `dict_label` / `dict_value` / `dict_type` / `is_default` / `update_by` | `!= null and != ''` | 该列**不动** |
| `dict_sort` / `css_class` / `list_class` / `status` / `remark` | **只有** `!= null` | **清列** |

对应 Python 的两个常量（第三项 `require_text` 就是 `!= null and != ''`）：

```python
_INSERT_DICT_TYPE_COLUMNS = (("dict_name", "dict_name", True),
                             ("dict_type", "dict_type", True),
                             ("status", "status", False),
                             ("remark", "remark", True),
                             ("create_by", "create_by", True))

_UPDATE_DICT_TYPE_COLUMNS = (("dict_name", "dict_name", True),
                             ("dict_type", "dict_type", True),
                             ("status", "status", False),
                             ("remark", "remark", False),
                             ("update_by", "update_by", True))
```

`_INSERT_DICT_DATA_COLUMNS` / `_UPDATE_DICT_DATA_COLUMNS` 同构，字段顺序与 XML 一致。
**`remark` 在类型表是"判空串"、在数据表的 update 里是"只判 null"** —— 两张表不一样，
照抄，别统一。

### 4.5 主键与自增

| 语句 | 主键处理 |
|---|---|
| `insertDictType` | **没有** `useGeneratedKeys` → `dict_id` 保持入参值（通常是 `None`） |
| `insertDictData` | **没有** `useGeneratedKeys` → `dict_code` 保持入参值 |
| `updateDictType` / `updateDictData` | `where dict_id/dict_code = ?`；为空时 SQL 里是 `null`，永远匹配不到 |
| `deleteDictTypeByIds` / `deleteDictDataByIds` | `<foreach open="(" separator="," close=")">` → `_in_clause(...)`；空数组拼出 `in ()`，MySQL 语法错（Java 一样） |

### 4.6 `selectDictDataByTypeMore` 的 `in` 子句

```java
dictType.split(",")
```

必须用 `split_regex(value, ",", limit=0)` 复刻 Java 语义：

| 入参 | Java `split(",")` 结果 | SQL |
|---|---|---|
| `"a,b"` | `["a","b"]` | `in (:t0,:t1)` |
| `"a"` | `["a"]` | `in (:t0)` |
| `","` | `[]`（尾部空串被丢弃） | **`in ()` → 语法错** |
| `None` | `null.split(",")` → NPE | `AttributeError` → 500 |

Python 的 `str.split` 会多出空串，从而把 `","` 变成 `in ("","")` —— 那是个**能跑但结果不同**的
SQL，比语法错更难发现。

---

## 5. 实体

### 5.1 `SysDictType`

| Java 字段 | 列 | Python | 类型 | 约束 |
|---|---|---|---|---|
| `dictId` | `dict_id` | `dict_id` | `Optional[int]` | 自增主键 |
| `dictName` | `dict_name` | `dict_name` | `Optional[str]` | `@NotBlank(message = "字典名称不能为空")` + `@Size(max = 100, message = "字典类型名称长度不能超过100个字符")` |
| `dictType` | `dict_type` | `dict_type` | `Optional[str]` | `@NotBlank(message = "字典类型不能为空")` + `@Size(max = 100, message = "字典类型类型长度不能超过100个字符")` |
| `status` | `status` | `status` | `Optional[str]` | `0` 正常 / `1` 停用 |
| `createBy` / `createTime` | 同名 | `create_by` / `create_time` | 继承 `BaseEntity` | |
| `updateBy` / `updateTime` | 同名 | `update_by` / `update_time` | 继承 `BaseEntity` | 不在投影列里 |
| `remark` | `remark` | `remark` | 继承 `BaseEntity` | |

注意 `"字典类型类型长度..."` 那个**叠字**是 Java 原文（`dictName` 的文案写的是"名称"）。
校验常量的变量名是 `DICT_TYPE_CONSTRAINTS`，校验入口是 `_validated_dict_type`
里的 `validate(dict_type, DICT_TYPE_CONSTRAINTS)`。

### 5.2 `SysDictData`

| Java 字段 | 列 | Python | 类型 | 约束 |
|---|---|---|---|---|
| `dictCode` | `dict_code` | `dict_code` | `Optional[int]` | 自增主键 |
| `dictSort` | `dict_sort` | `dict_sort` | `Optional[int]` | 无 |
| `dictLabel` | `dict_label` | `dict_label` | `Optional[str]` | `@NotBlank(message = "字典标签不能为空")` |
| `dictValue` | `dict_value` | `dict_value` | `Optional[str]` | `@NotBlank(message = "字典键值不能为空")` |
| `dictType` | `dict_type` | `dict_type` | `Optional[str]` | `@NotBlank(message = "字典类型不能为空")` |
| `cssClass` | `css_class` | `css_class` | `Optional[str]` | `@Size(max = 100, message = "样式属性长度不能超过100个字符")`；**可省** |
| `listClass` | `list_class` | `list_class` | `Optional[str]` | 无（**没有** `@Size`） |
| `isDefault` | `is_default` | `is_default` | `Optional[str]` | `Y` / `N` |
| `status` | `status` | `status` | `Optional[str]` | `0` 正常 / `1` 停用 |
| `default` | — | `default` | `bool`（`@computed_field`） | **只读**，`"Y"` 才 `True`（§32.9） |
| `createBy` / `createTime` / `updateBy` / `updateTime` / `remark` | 同名 | 继承 `BaseEntity` | | |

校验常量的变量名是 `DICT_DATA_CONSTRAINTS`。

---

## 6. `DictUtils`（9 个方法）

| Java（`DictUtils`） | Python（`dict_utils`） | 说明 |
|---|---|---|
| `SEPARATOR` | `SEPARATOR = ","` | |
| `setDictCache(String, List)` | `set_dict_cache(key, datas)` | `None` 不特判（两侧都是"未命中"） |
| `getDictCache(String)` | `get_dict_cache(key)` | 未命中返回 `None`，**不是** `[]` |
| `getDictLabel(String, String)` | `get_dict_label(dict_type, dict_value)` | 单值走 `SEPARATOR` |
| `getDictValue(String, String)` | `get_dict_value(dict_type, dict_label)` | 同上 |
| `getDictLabel(String, String, String)` | `get_dict_label_with_separator(...)` | 多值分支按**字典表顺序**拼，末尾 `stripEnd` |
| `getDictValue(String, String, String)` | `get_dict_value_with_separator(...)` | 与上一条镜像，但多一处判空（见下） |
| `removeDictCache(String)` | `remove_dict_cache(key)` | 删单个键 |
| `clearDictCache()` | `clear_dict_cache()` | `KEYS sys_dict:*` + 批量删 |

三处必须记住的原文：

1. **`containsAny` 的参数是反的**：`StringUtils.containsAny(separator, dictValue)`
   意思是"`separator` 里有没有 `dictValue` 的某个字符"。正常写法应是
   `containsAny(dictValue, separator)`。Python 侧在 `_contains_any_char(chars, probe)`
   的注释里钉住了这一点，`tests/test_dict_utils.py::TestReversedContainsAny` 用自定义
   separator `"1"` 证明参数顺序确实是反的。
2. **`getDictLabel` 的单值分支不做 `stripEnd`**：所以 `dictLabel` 本身以逗号结尾时，
   返回值就带着那个逗号；多值分支才会 `stripEnd`。
3. **`getDictValue` 的 else 分支多判一次**：多值条件里多了 `&& isNotEmpty(datas)`，
   而 `else` 分支照样 for-each `datas` —— 于是"缓存为空 + 没有逗号"会 NPE（→ 500），
   而 `getDictLabel` 在同样输入下返回 `""`。这个不对称是 Java 原样。

---

## 7. 行号速查（改代码前先看这张表）

| 要改什么 | 去哪 |
|---|---|
| 端点路径 / 权限点 / 注册顺序 | 两个 `app/api/system/sys_dict_*_controller.py` 的顶部 docstring + `router` 声明 |
| 请求体校验 | 两个控制器的 `_validated_dict_*` 与 `DICT_TYPE_CONSTRAINTS` / `DICT_DATA_CONSTRAINTS` |
| 唯一性校验的三态 | `sys_dict_type_controller.py` 的 `NOT_UNIQUE_OLD` 与 `ADD_/EDIT_DICT_TYPE_EXISTS` |
| `/type` 与 `/typemore` 的形状差异 | `sys_dict_data_controller.py` 的 `dict_type` / `dict_type_more` |
| 缓存读写与写操作的清缓存时机 | `app/system/service/sys_dict_type_service.py` / `sys_dict_data_service.py` |
| `-dadadadas` 哨兵与尾逗号 | `sys_dict_type_service.py::select_dict_data_by_type_more` |
| `<if>` 判据 / SQL 文本 | 两个 mapper 的 `_build_*_list_sql` 与三个列元组常量 |
| 投影列 | 两个 mapper 的 `SELECT_DICT_TYPE_VO` / `SELECT_DICT_DATA_VO` 与 `_*_COLUMNS` |
| `default` 只读键 | `app/common/core/domain/entity/sys_dict_data.py` 的 `@computed_field` |
| 缓存键前缀 / 清缓存 | `app/common/utils/dict_utils.py` 的 `get_cache_key` / `clear_dict_cache` |
| 路由是否挂上 | `app/main.py` 的两个 `include_router(...)` |
| 行为差异说明 | [COMPATIBILITY.md](COMPATIBILITY.md) §32 |
