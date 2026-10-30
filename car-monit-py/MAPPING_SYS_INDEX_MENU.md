# MAPPING_SYS_INDEX_MENU.md — `sys_index_menu` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §34。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectSysIndexMenuById` → `select_sys_index_menu_by_id`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysIndexMenuService` +
  `SysIndexMenuServiceImpl`）在 Python 里合并成一个类。
- **本切片新增了第二个实体基类** `BaseUuidEntity`（Java `BaseUuidEntity`），
  这是本次迁移第一次遇到"主键是 UUID、审计人是 `Long`"的实体，见 §5。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysIndexMenuController.java` | `app/api/system/sys_index_menu_controller.py` | **新建**；**7 个映射，迁移 6 个**（`export` 缺 `ExcelUtil`） |
| `ruoyi-system/.../service/ISysIndexMenuService.java`<br>`ruoyi-system/.../service/impl/SysIndexMenuServiceImpl.java` | `app/system/service/sys_index_menu_service.py` | **新建**；6 个方法，其中 **4 个直接返回 `AjaxResult`** |
| `ruoyi-system/.../mapper/SysIndexMenuMapper.java`<br>`ruoyi-system/.../resources/mapper/system/SysIndexMenuMapper.xml` | `app/system/mapper/sys_index_menu_mapper.py` | **新建**；8 个方法 ↔ 8 条 statement，**严格 1:1** |
| `ruoyi-system/.../domain/SysIndexMenu.java` | `app/system/domain/sys_index_menu.py` | **新建**；8 个自有字段 + `BaseUuidEntity` 13 个，**零校验注解** |
| `ruoyi-common/.../core/domain/BaseUuidEntity.java` | `app/common/core/domain/base_uuid_entity.py` | **新建**（本切片的基础设施改动） |
| `ruoyi-admin/.../RuoYiApplication.java`（`@SpringBootApplication` 扫描） | `app/main.py` | **改了一处**：`include_router(sys_index_menu_router)` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `BaseController#startPage()` | `base_controller.start_page()` | `list` 调用；`mylist` **不**调用 |
| `BaseController#getDataTable(List)` | `base_controller.get_data_table(rows)` | 有 `.total` 就用它，否则 `len(rows)` |
| `@PathVariable Long[] ids` | `base_controller.parse_id_array(raw)` | 逗号串 → `List[int]` |
| 无注解实体参数 `SysIndexMenu` | `bind_query_params(SysIndexMenu, request.query_params)` | 无 `@RequestBody` 即按 query string 绑定 |
| `@PreAuthorize("@ss.hasPermi(...)")` | `@pre_authorize_permi("system:indexmenu:...")` | **只有 2 处**（`getInfo` / `edit`） |
| `@Log(title = "菜单管理", ...)` | **未迁移** | 不写 `sys_oper_log`，见 §34.3 |
| `SecurityUtils#getUserId()` | `security_utils.get_user_id()` | service **每次都覆盖** `userId` |
| `SecurityUtils#getEpsId()` | `security_utils.get_eps_id()` | 新增时写 `eps_id`（= `sysUser.deptId`） |
| `StringUtils.getUUID()` | `string_utils.get_uuid()` | 32 位、无连字符 |
| `DateUtils.getTimestamp()` | `date_utils.get_timestamp()` | 毫秒截断；同批插入共用一个值 |
| `StringUtils.isNotEmpty(String)` | `string_utils.is_not_empty(value)` | `saveSysIndexMenu` 判"有没有 id" |
| `StringUtils.isNotBlank(String)` | `string_utils.is_not_blank(value)` | `insertSysIndexMenu` 判空 |
| `String.split(",")` | `string_utils.split_regex(value, ",", 0)` | `limit=0` 丢弃尾部空串 |
| `AjaxResult.success(msg, data)` | `AjaxResult.success_message_data(msg, data)` | `"操作成功！"` 是全角叹号 |

### 1.3 测试

| 层 | Python 测试文件 | 函数数 → 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_index_menu_mapper.py` | 26 → **26** | 列表 SQL 的 7 段条件与顺序 / `userId != 1` 的 OGNL 语义（`None` 也生效）/ 硬编码 `where` 后的 `and` 拼接 / 自带 `order by` / `limit 9` / 两条软删除 vs 一条物理删除 / insert 无 `useGeneratedKeys` |
| Service | `tests/test_sys_index_menu_service.py` | 24 → **26** | 四处 `userId` 覆盖 / `isNotEmpty("   ")` 走新增 / 审计列补齐 / 全角叹号 / "先删后插"顺序 / 只剥一个尾逗号 / 中间空段 `ValueError` / `count == 0` 仍 200 / 同批共用一个时间戳 |
| Controller | `tests/test_sys_index_menu_controller.py` | 46 → **50** | 6 条路由与注册顺序 / 只有 2 个权限点 + 4 个无权限 / `/mylist` 在控制器里也设 `userId` / `add` 只认 `menuIds` / `edit` 无校验 / `remove` 软删除 |

合计 **102** 条（26 + 26 + 50）。加上 Phase 3.14 的 122 条，全量从 **1623** 到 **1847**。

---

## 2. 控制器：7 个映射

### 2.1 端点逐条对照

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list(SysIndexMenu sysIndexMenu)` | `list_index_menus(query)` | GET `/system/indexmenu/list` | **无**（注解被注释） |
| `getSysIndexMenulist(SysIndexMenu)` | `get_my_list(query)` | GET `/system/indexmenu/mylist` | **无**（本来就没有） |
| `export(HttpServletResponse)` | **未迁移** | GET `/system/indexmenu/export` | — |
| `getInfo(@PathVariable("id") Long id)` | `get_info(id)` | GET `/system/indexmenu/{id}` | `system:indexmenu:query` |
| `add(@RequestBody SysIndexMenu)` | `add(entity)` | POST `/system/indexmenu` | **无**（注解被注释） |
| `edit(@RequestBody SysIndexMenu)` | `edit(entity)` | PUT `/system/indexmenu` | `system:indexmenu:edit` |
| `remove(@PathVariable Long[] ids)` | `remove(ids)` | DELETE `/system/indexmenu/{ids}` | **无**（注解被注释） |

### 2.2 三个 `@PreAuthorize` 是被**注释掉**的

Java 源码原文：

```java
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:list')")
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:add')")
//    @PreAuthorize("@ss.hasPermi('system:indexmenu:remove')")
```

这不是遗漏：`list` / `mylist` / `add` / `remove` 是首页九宫格的数据源，**普通用户**
也在用。补上权限会让没有菜单管理权限的用户直接白屏。与 §31.3 的 `notice/list`、
§29.7 的 `treeselect` 同类。

结果就是 4 个"登录即可"的端点 + 2 个带权限点的端点。**别"顺手"补齐**。

### 2.3 注册顺序（不是装饰性的）

```
/list -> /mylist -> /{id}   -> POST "" -> PUT "" -> DELETE /{ids}
```

`/list` 与 `/mylist` 都是单段，必须排在 `/{id}` 之前，否则 `"list"` / `"mylist"`
会被 `/{id}` 吃掉（后者声明成 `int`，转换失败 → 500）。

### 2.4 `/mylist` 在控制器里也设了一次 `userId`

Java：

```java
Long userId = SecurityUtils.getUserId();
sysIndexMenu.setUserId(userId);       // 控制器设一次
return AjaxResult.success(sysIndexMenuService.getList(sysIndexMenu));  // service 里又设一次
```

Python 照抄这个"设两遍"（`sys_index_menu_controller.get_my_list`）。看起来冗余，
但它保证了即使将来 service 的覆盖被改掉，控制器这一层仍然不越权。

对比：`list` **不**在控制器里设 `userId`（只有 service 设）。两个端点的写法不同，
是 Java 原样。

### 2.5 `getInfo` 的 `@PathVariable("id")`

Java 显式写了 `value = "id"`，所以形参名不影响 URL 模板。Python 侧同样用
`{id}`。注意这个 id 在 Java 里声明成 **`Long`**（虽然实体的 `id` 是 UUID 字符串），
所以真实调用方传的是数字串；Python 照抄声明成 `int`，非数字在路由层转失败 →
**HTTP 200 + code 500**（与 Java 的 `MethodArgumentTypeMismatchException` 同形）。

### 2.6 `add` / `edit` 都没有 `@Validated`

实体上一个约束注解也没有，所以 Python 侧**不建** `*_CONSTRAINTS`，也不注入
`validate`。空 body `{}` 也能进 Service（`menuIds = None` → 短路返回成功）。

---

## 3. Service：6 个方法

### 3.1 方法对照

| Java | Python | 返回值 |
|---|---|---|
| `selectSysIndexMenuById(Long id)` | `select_sys_index_menu_by_id(id)` | `Optional[SysIndexMenu]` |
| `selectSysIndexMenuList(SysIndexMenu)` | `select_sys_index_menu_list(entity)` | `List`，覆盖 `userId` |
| `getList(SysIndexMenu)` | `get_list(entity)` | `List`，覆盖 `userId` |
| `saveSysIndexMenu(SysIndexMenu)` | `save_sys_index_menu(entity)` | `AjaxResult` |
| `insertSysIndexMenu(String menuIds)` | `insert_sys_index_menu(menu_ids)` | `AjaxResult` |
| `deleteSysIndexMenuByIds(Long[])` | `delete_sys_index_menu_by_ids(ids)` | `AjaxResult` |
| `deleteSysIndexMenuById(Long id)` | `delete_sys_index_menu_by_id(id)` | `AjaxResult` |

### 3.2 四个方法直接返回 `AjaxResult`，`count == 0` 也是成功

| 方法 | 返回 |
|---|---|
| `saveSysIndexMenu` | `{"code":200,"msg":"操作成功！","data":<id>}`（**全角叹号**） |
| `insertSysIndexMenu` | `{"code":200,"msg":"操作成功"}`（**没有** `data`） |
| `deleteSysIndexMenuByIds` | `{"code":200,"msg":"操作成功","data":<count>}` |
| `deleteSysIndexMenuById` | 同上 |

用的是 `AjaxResult.success`，**不是** `BaseController#toAjax`。改成 `to_ajax`
会让"删一个不存在的 id"从 200 变 500 —— 这是唯一一处刻意**不**用 `toAjax` 的
删除接口。

### 3.3 `saveSysIndexMenu`：有 `id` 就改，没有就新增

判据是 `StringUtils.isNotEmpty(id)`（**trim 后为空**才算空）：

| 分支 | 写哪些列 |
|---|---|
| 有 id（`update`） | 只补 `updateBy` / `updateTime`，其余照入参 |
| 无 id（`insert`） | `id = getUUID()`（32 位） / `delFlag = "0"` / `epsId = getEpsId()` / `createBy` / `createTime` / `updateBy` / `updateTime` |

四个审计列都是 **`Long`**（`SecurityUtils.getUserId()`），不是用户名 —— 与
`sys_config` 的 `createBy = getUsername()`（字符串）相反，别混用。

`isNotEmpty(" ")` 为假，所以 `id = " "` 会走**新增**分支并生成一个新 UUID。

### 3.4 `insertSysIndexMenu`：先删后插，只剥一个尾逗号

```java
if (StringUtils.isNotBlank(menuIds)) {
    if (menuIds.endsWith(",")) {
        menuIds = menuIds.substring(0, menuIds.length() - 1);   // 只剥一个
    }
    String[] menuIdStr = menuIds.split(",");                    // 丢弃尾部空串
    for (String s : menuIdStr) {
        SysIndexMenu m = new SysIndexMenu();
        m.setUserId(userId);
        m.setMenuId(Long.parseLong(s));
        mapper.deleteByMenuUserId(m);      // 物理删除
        m.setDelFlag("0"); ... 四个审计列 ...
        mapper.insertSysIndexMenu(m);
    }
}
return AjaxResult.success();
```

四个细节全部照抄：

1. `isNotBlank` 判空 —— `None` / `""` / `"   "` 全部短路，**一行都不写**；
2. 尾逗号只剥**一个**：`"100,101,,"` → `"100,101,"` → `split` 丢尾部空串 → **2 行**；
3. 中间空段**不**被丢：`"100,,101"` → `int("")` → `ValueError` → 500；
4. `deleteByMenuUserId` 是**物理**删除（`delete from`），与其它两个软删除不同；
   非数字 id 同样 500（Java `NumberFormatException`）。

`curDate` 在循环**外**取得 —— 同一批插入的所有行时间戳**完全相同**。改成循环内取
时间对一个"多选收藏"接口没有意义，但会让排序（`order by t.CREATE_TIME desc`）
在多选时变成不确定。

### 3.5 `userId` 一律来自登录上下文

`selectSysIndexMenuList` / `getList` / `saveSysIndexMenu` / `insertSysIndexMenu`
四个方法开头都 `entity.userId = SecurityUtils.getUserId()`。客户端传
`?userId=999` / `{"userId":999}` 一律被覆盖。

这是**权限边界**，不是冗余代码：`selectSysIndexMenuList` 的 SQL 要靠 `userId`
判断"超管（1）看全部 / 其它人只看自己有角色的菜单"。

---

## 4. Mapper：8 条 statement

### 4.1 语句对照

| XML `id` | Python | 类型 |
|---|---|---|
| `<sql id="selectSysIndexMenuVo">` | 常量 `SELECT_SYS_INDEX_MENU_VO` | 11 列，`t.` 前缀 |
| `selectSysIndexMenuById` | `select_sys_index_menu_by_id(id)` | select 单行 |
| `selectSysIndexMenuList` | `select_sys_index_menu_list(entity)` | select 列表，**分页点** |
| `getList` | `get_list(entity)` | select 列表，自带 `limit 9` |
| `insertSysIndexMenu` | `insert_sys_index_menu(entity)` | `<trim>` 动态列 |
| `updateSysIndexMenu` | `update_sys_index_menu(entity)` | `<trim prefix="SET">` |
| `deleteSysIndexMenuById` | `delete_sys_index_menu_by_id(id)` | **软删除**，Java 侧无调用方 |
| `deleteSysIndexMenuByIds` | `delete_sys_index_menu_by_ids(ids)` | **软删除**，`<foreach>` |
| `deleteByMenuUserId` | `delete_by_menu_user_id(entity)` | **物理删除** |

### 4.2 `selectSysIndexMenuList`：不是单表查询，也不是 `<where>`

```sql
select t2.menu_name as menuName2, t1.menu_id, t1.menu_name
from sys_menu t1, sys_menu t2
where t1.menu_type='C'
and t1.visible = '0'
and t2.menu_id = t1.parent_id
and exists (...)          -- 仅 userId != 1
and not exists (...)      -- 总是
and not exists (...)      -- 总是
and t1.menu_name like ... -- 仅 menuName 非空
and t2.menu_name like ... -- 仅 menuName2 非空
order by  t2.parent_id,t2.order_num,t1.order_num,t1.menu_id
```

三个要点：

1. **`where` 与 `and` 都是硬编码的**（XML 里没有 `<where>` 标签），所以拼接方式是
   "条件片段不带前导 `AND`，用 `"\nand "` 连起来"。这与其它用到 `<where>` 的模块
   恰好写出同一种形态，但原因不同 —— `<where>` 会吃掉首个 `AND`，这里是**手写**
   的 `where`，本就不该让第一个片段带 `AND`。
2. **投影只有 3 列**，`menuName2` 靠 SQL 别名映射（`resultMap` 里的 property 名就是
   `menuName2`），`menuId` / `menuName` 是原名。没有行的字段一律是 `None`。
3. **自带 `order by`**，所以 PageHelper 不会追加客户端排序列 —— 前端在"常用菜单"
   页点表头排序**不生效**（与 `sys_config` 列表相反，那边没有 `order by`）。

### 4.3 `userId != 1` 的 OGNL 语义

```xml
<if test="userId != 1 ">
```

判据是 **OGNL 的 `!=`**，不是 `!= null`：

| `userId` | 条件是否生效 |
|---|---|
| `1`（超管） | **不生效** → 返回所有人的候选菜单 |
| `2` / `null` / 其它 | 生效 → `exists` 只保留"该用户有角色授权"的菜单 |

也就是说 **`None != 1` 为真**，条件照样生效（此时 `:user_id` 绑成 SQL `NULL`，
`exists` 恒假 → 结果为空）。Service 总会先覆盖 `userId`，所以正常路径不会走到这里。
写成 `if entity.user_id is not None and entity.user_id != 1` 是**错的**。

### 4.4 `getList`：`limit 9` 与 `concat`

```sql
select t.id, t1.menu_name, concat(t2.path,'/',t1.path) as menuUrl
from SYS_INDEX_MENU t
left join sys_menu t1 on t.MENU_ID = t1.menu_id
left join sys_menu t2 on t1.parent_id = t2.menu_id
where t.del_flag='0'
and t.USER_ID = :user_id
order by t.CREATE_TIME desc
limit 9
```

- `menuUrl` 是"父路径/子路径"拼出来的（如 `system/user`），**没有**前导 `/`；
- 表名 `SYS_INDEX_MENU`、列名 `MENU_ID` / `USER_ID` **大写**，而 `t.id` / `t.del_flag`
  小写 —— 混写照抄。MySQL 在 Linux 上列名不区分大小写，能跑；
- 自带 `limit 9`，控制器**不**调 `startPage()`，所以分页参数对它无影响。

### 4.5 两条软删除 + 一条物理删除

| 语句 | SQL | 用途 |
|---|---|---|
| `deleteSysIndexMenuById` | `update ... set del_flag = '1' where ID = :id` | Java 侧**无调用方**（照留） |
| `deleteSysIndexMenuByIds` | `update ... set del_flag = '1' where ID in (...)` | `remove` 端点 |
| `deleteByMenuUserId` | `delete from ... where menu_id = ? and user_id = ?` | `insertSysIndexMenu` 的"先删" |

`deleteByMenuUserId` 是**物理**删除，因为它要保证"同一菜单同一用户只有一行"，
软删除会留下多条 `del_flag='1'` 的历史行。这是全模块唯一一处物理删除。

`insertSysIndexMenu` **没有** `useGeneratedKeys`：主键是 UUID，由 service 侧
`StringUtils.getUUID()` 先生成好再插，不是数据库生成 —— 所以"不回写主键"不是缺陷。

---

## 5. `BaseUuidEntity`（新增的第二个实体基类）

### 5.1 与 `BaseEntity` 的四处不同

| | `BaseEntity` | `BaseUuidEntity` |
|---|---|---|
| 主键 | **没有**（各实体自己声明 `Long xxxId`） | `String id`（UUID） |
| `createBy` / `updateBy` | `String`（用户名） | **`Long`**（用户 id） |
| 时间类型 | `Date`（`java.util.Date`） | `Timestamp` |
| 额外字段 | `searchValue` / `params` | `searchValue` / `params` + `epsId` / `delFlag` / `deptSubCode` / `tenantId` / `sort` / `remark` / `flag` |
| `params` 的 JSON | `@JsonInclude(NON_EMPTY)` → 为空时**整个键消失** | **没有**注解 → 输出 `"params": null` |

最后一行是最容易漏的差异：同样是"没填 params"，`SysConfig` 的 JSON 里**没有**
`params` 键，`SysIndexMenu` 的 JSON 里**有** `"params": null`。前端的 `if (res.params)`
两种写法都能过，但逐字节比对会不一样。

### 5.2 `SysIndexMenu` 的 8 个自有字段

| Java | Python | 备注 |
|---|---|---|
| `userId` | `user_id` | `Long` |
| `menuId` | `menu_id` | `Long` |
| `menuName` | `menu_name` | `selectSysIndexMenuList` 投影 `t1.menu_name` |
| `menuName1` | `menu_name1` | **无人写入**，也不在 `resultMap` 里（照留） |
| `menuName2` | `menu_name2` | 投影 `t2.menu_name as menuName2` |
| `menuName3` | `menu_name3` | **无人写入**（照留） |
| `menuIds` | `menu_ids` | **仅入参**，库里没有这一列 |
| `menuUrl` | `menu_url` | `getList` 里 `concat` 出来的 |

`menuName1` / `menuName3` 是死字段（无 SQL 写入、不在 `resultMap`），按迁移原则
第 4 条**保留**并标注。

---

## 6. 未迁移项

| Java | 原因 | 客户端表现 |
|---|---|---|
| `export(HttpServletResponse)` + `ExcelUtil<SysIndexMenu>` | `ExcelUtil`（Apache POI）未迁移 | `GET /system/indexmenu/export` 被 `/{id}` 兜住 → **HTTP 200 + code 500** |
| `@Log(title = "菜单管理", businessType = ...)` | `LogAspect` 未迁移 | 不写 `sys_oper_log`，业务结果不变 |
| `@Transactional`（`insertSysIndexMenu` 的"先删后插"） | 全工程未复刻（§28.3） | 中途失败会留下"删了没插"的空洞 |
