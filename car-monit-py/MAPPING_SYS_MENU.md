# MAPPING_SYS_MENU.md — `sys_menu` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §29。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectMenuList` → `select_menu_list`，`checkMenuNameUnique` → `check_menu_name_unique`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysMenuService` + `SysMenuServiceImpl`）
  在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。
- **本切片没有新增文件**：菜单的实体、mapper、service 在 Phase 2 / 3.1 就已存在
  （`GET /getRouters` 用得着），这次是把"管理页"那半边补齐。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysMenuController.java` | `app/api/system/sys_menu_controller.py` | **7 个映射，全部迁移**（菜单本来就没有 `export`） |
| `ruoyi-system/.../service/ISysMenuService.java`<br>`ruoyi-system/.../service/impl/SysMenuServiceImpl.java` | `app/system/service/sys_menu_service.py` | 接口 + 实现合并为 `SysMenuService`；接口 15 个 + 实现类额外的 7 个 public 方法 |
| `ruoyi-system/.../mapper/SysMenuMapper.java`<br>`.../resources/mapper/system/SysMenuMapper.xml` | `app/system/mapper/sys_menu_mapper.py` | 接口 + XML 合并：**14** 条 statement 各变成一个模块级 SQL 常量（或方法内联 SQL） |
| `ruoyi-common/.../core/domain/entity/SysMenu.java` | `app/common/core/domain/entity/sys_menu.py` | 15 个字段 + `BaseEntity`；含 `MENU_CONSTRAINTS`（7 条 / 6 个字段） |
| `ruoyi-common/.../core/domain/TreeSelect.java` | `app/common/core/domain/tree_select.py` | 已存在；`treeselect` / `roleMenuTreeselect` 的返回元素 |
| `ruoyi-system/.../domain/vo/RouterVo.java`<br>`ruoyi-system/.../domain/vo/MetaVo.java` | `app/system/domain/vo/router_vo.py`<br>`app/system/domain/vo/meta_vo.py` | 已存在；只被 `buildMenus`（`GET /getRouters`）用 |
| `ruoyi-system/.../mapper/SysRoleMapper.java`（`selectRoleById`） | `app/system/mapper/sys_role_mapper.py` | `selectMenuListByRoleId` 先查角色拿 `menuCheckStrictly` |
| `ruoyi-system/.../mapper/SysRoleMenuMapper.java`（`checkMenuExistRole`） | `app/system/mapper/sys_role_menu_mapper.py` | `checkMenuExistRole` 走**关联表**，不是菜单表 |
| `ruoyi-common/.../core/domain/BaseEntity.java` | `app/common/core/domain/base_entity.py` | `createBy` / `updateBy` / `params` ... |
| `ruoyi-common/.../constant/UserConstants.java` | `app/common/constant/user_constants.py` | 只用 `UNIQUE_OLD` / `NOT_UNIQUE_OLD` / `YES_FRAME` / `NO_FRAME` / `TYPE_DIR` / `TYPE_MENU` / `LAYOUT` / `PARENT_VIEW` |
| `ruoyi-common/.../constant/Constants.java` | `app/common/constant/constants.py` | `HTTP` / `HTTPS`（外链前缀校验）；`RESOURCE_PREFIX` 本轮用不到 |
| `ruoyi-common/.../core/controller/BaseController.java` | `app/common/core/controller/base_controller.py` | `to_ajax` / `bind_query_params`（**不用** `start_page`） |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-framework/.../web/service/PermissionService.java`（`@ss.hasPermi`） | `app/framework/web/service/permission_service.py` | `@pre_authorize_permi("...")`，**4 个标识 5 处使用** |
| `ruoyi-framework/.../web/service/TokenService.java` | `app/framework/web/service/token_service.py` | `tokenService.getLoginUser(request)` → 当前用户 id |
| `ruoyi-common/.../utils/SecurityUtils.java` | `app/common/utils/security_utils.py` | `get_username()`（写 `create_by` / `update_by`） |
| `ruoyi-common/.../utils/StringUtils.java`（`startsWithAny` / `capitalize` / `isEmpty`） | `app/common/utils/string_utils.py` | 外链校验、路由名首字母大写、路由零件 |
| `ruoyi-framework/.../aspectj/LogAspect.java` | **未迁移** | 因此不写 `sys_oper_log`，见 §29.2 |
| `ruoyi-framework/.../aspectj/DataScopeAspect.java` | 无需对应 | `sys_menu` 的 XML 里**没有** `${params.dataScope}`，`@DataScope` 对这个表不生效 |
| `Hibernate Validator`（`MethodArgumentNotValidException`） | `bean_validation.validate()` + `RuntimeError` 处理器 | 见 §5 |

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_menu_mapper.py` | 33 | 14 条 statement 的拼装 / 三个 `<if>` 顺序与不 trim 语义 / `limit 1` / 动态列与 `<set>` 的不对称 / 无主键回写 |
| Service | `tests/test_sys_menu_service.py` | 61 | 超管与非超管两分支 / `params["userId"]` 副作用 / 树构建与 `TreeSelect` / 路由零件 6 个 / `-1` 哨兵 |
| Controller | `tests/test_sys_menu_controller.py` | 55 | 路由表（7 条）/ 5 个权限点 / 校验先于权限 / `add` 两道闸与 `edit` 三道闸 / `remove` 两道闸 / 三个端点取当前用户 |

合计 **149** 条；全量套件 **1200 passed**。

Java 侧 **没有任何 `src/test`**，所以上表没有"Java 对应用例"列 ——
这些用例是照着 Java 源码逐行推导出来的，不是移植过来的。

---

## 2. 控制器：7 个映射逐条对照

前缀都是 `/system/menu`。`权限` 列是 `@PreAuthorize("@ss.hasPermi(...)")` 的值；
写 `登录` 表示**没有注解**。

| # | Java 方法 | Python 函数 | HTTP + 路径 | 权限 |
|---|---|---|---|---|
| 1 | `list(SysMenu menu)` | `list_menus(menu: MenuParam, request)` | `GET /system/menu/list` | `system:menu:list` |
| 2 | `treeselect(SysMenu menu)` | `treeselect(menu: MenuParam, request)` | `GET /system/menu/treeselect` | **登录** |
| 3 | `roleMenuTreeselect(Long roleId)` | `role_menu_treeselect(role_id, request)` | `GET /system/menu/roleMenuTreeselect/{roleId}` | **登录** |
| 4 | `getInfo(Long menuId)` | `get_info(menu_id: int)` | `GET /system/menu/{menuId}` | `system:menu:query` |
| 5 | `add(SysMenu menu)` | `add(menu: ValidMenu)` | `POST /system/menu` | `system:menu:add` |
| 6 | `edit(SysMenu menu)` | `edit(menu: ValidMenu)` | `PUT /system/menu` | `system:menu:edit` |
| 7 | `remove(Long menuId)` | `remove(menu_id: int)` | `DELETE /system/menu/{menuId}` | `system:menu:remove` |

> 早期版本的 `MIGRATION_PROGRESS.md` 把这里写成"13 个映射"，是错的。
> `SysMenuController` 全文只有 7 个 `@GetMapping` / `@PostMapping` / `@PutMapping` /
> `@DeleteMapping`，**也没有** `export`（角色、岗位、用户、部门都有，菜单没有）。

### 2.1 两个树端点**没有**权限点（安全相关）

```java
@GetMapping("/treeselect")
public AjaxResult treeselect(SysMenu menu) { ... }

@GetMapping("/roleMenuTreeselect/{roleId}")
public AjaxResult roleMenuTreeselect(@PathVariable("roleId") Long roleId) { ... }
```

两个方法上都没有 `@PreAuthorize`。这不是遗漏：**角色编辑页**要画菜单树，任何能进
"角色管理"的人都得拿到它，而 `sys_role.list` 的权限点本身也是关掉的。
Python 侧照抄：`treeselect` / `role_menu_treeselect` 上**没有** `@pre_authorize_permi`。

`list` 相反，**有** `system:menu:list`（与 `sys_role.list` 正好相反）——
看到角色那边没注解就"顺手"把菜单这边的也删掉，会让任何登录用户都能翻整个菜单表。

回归用例：`tests/test_sys_menu_controller.py::TestPermissions::test_an_anonymous_caller_is_refused`
（5 个参数化分支，含 `list`）与 `TestPermissions::test_list_only_need_a_login_when_the_permission_is_present`；
`TestPermissions::test_treeselect_has_no_permission_point` 则断言**空权限集**也能调通。

### 2.2 `list` 不分页

```java
@GetMapping("/list")
public AjaxResult list(SysMenu menu)      // 不是 TableDataInfo
{
    List<SysMenu> menus = menuService.selectMenuList(menu, getUserId());
    return AjaxResult.success(menus);
}
```

菜单是树形数据，分页没有意义。所以 Python 侧**没有** `start_page` / `get_data_table`，
直接 `AjaxResult.success_data(menus)`。`tests/test_sys_menu_controller.py::TestList::test_it_is_not_paged`
是这一点的回归阀（`isinstance(result, AjaxResult)` + 键序 `msg/code/data`）。

### 2.3 形参绑定：三个端点用 query string，两个用请求体

| Java 形参 | 绑定来源 | Python |
|---|---|---|
| `SysMenu menu`（**无**注解，`list` / `treeselect`） | query string | `MenuParam = Annotated[SysMenu, Depends(_query_menu)]` |
| `@PathVariable Long roleId` | 路径 | `role_id: int` |
| `@PathVariable Long menuId` | 路径 | `menu_id: int` |
| `@Validated @RequestBody SysMenu menu`（`add` / `edit`） | 请求体 + 校验 | `ValidMenu = Annotated[SysMenu, Depends(_validated_menu)]` |
| `Long menuId`（`remove`） | 路径 | `menu_id: int` |

`list` / `treeselect` 的 `SysMenu` 形参**没有** `@RequestBody`，所以是从查询串绑的：
`?menuName=用户&visible=0&status=0`。`bind_query_params` 逐字段调用
`SysMenu.field(alias)`，因此 `menuName`（驼峰）能落进 `menu_name`（蛇形）。

> 中文查询串在 Starlette 里必须 `urlencode` 后再编码，否则按 latin-1 解码成乱码。
> 这是**测试夹具**的注意点（`tests/test_sys_menu_controller.py::_fake_request`），
> 不是生产代码问题 —— 真实请求走 `urllib.parse.parse_qsl`，本来就是 UTF-8。

### 2.4 声明顺序：三个字面量路径必须写在 `/{menu_id}` 之前

FastAPI 按**注册顺序**匹配；Spring 的 `AntPathMatcher` 优先字面量，两者结果一致，但
前提是 Python 侧把字面量写在前面：

```
/system/menu/list                        <- 必须先注册
/system/menu/treeselect
/system/menu/roleMenuTreeselect/{role_id}
/system/menu/{menu_id}                   <- 兜底的变量路径
```

写反了的话 `GET /system/menu/list` 会命中 `/{menu_id}`，`"list"` 转 `int` 失败 →
HTTP 200 + `{"code":500}`。

另外 `POST` / `PUT` 用的是空串 `""`（拼出 `/system/menu`，与 Java 的 `@PostMapping` /
`@PutMapping` 一致），**不是** `"/"`：写成 `"/"` 会额外接受 `/system/menu/` 这个 Java 不认的路径。

回归用例：`TestRouteTable`（4 条，含"没有尾斜杠变体"）。

### 2.5 `add` 两道闸 / `edit` 三道闸

```java
public AjaxResult add(@Validated @RequestBody SysMenu menu) {
    if (UserConstants.NOT_UNIQUE_OLD.equals(menuService.checkMenuNameUnique(menu))) {
        return error("新增菜单'" + menu.getMenuName() + "'失败，菜单名称已存在");
    } else if (YES_FRAME.equals(menu.getIsFrame()) && !StringUtils.startsWithAny(menu.getPath(), HTTP, HTTPS)) {
        return error("新增菜单'" + menu.getMenuName() + "'失败，地址必须以http(s)://开头");
    }
    menu.setCreateBy(getUsername());
    return toAjax(menuService.insertMenu(menu));
}

public AjaxResult edit(@Validated @RequestBody SysMenu menu) {
    // 1. 名称判重  2. 外链前缀  3. 上级不能是自己
    ...
    else if (menu.getMenuId().equals(menu.getParentId())) {
        return error("修改菜单'" + menu.getMenuName() + "'失败，上级菜单不能选择自己");
    }
    menu.setUpdateBy(getUsername());
    return toAjax(menuService.updateMenu(menu));
}
```

| 闸 | `add` | `edit` | 判据 |
|---|---|---|---|
| 1 | 名称判重 | 名称判重 | `checkMenuNameUnique` 返回 `"1"` → 拒绝（**同一父节点**下） |
| 2 | 外链前缀 | 外链前缀 | `is_frame == "0"` 且 `path` 不以 `http://` / `https://` 开头 |
| 3 | — | 上级不能是自己 | `menu.menu_id.equals(menu.parent_id)` |

两个细节：

* **`is_frame` 的语义是反的**：`YES_FRAME = "0"` 表示"是外链"。所以校验写成
  `YES_FRAME == menu.is_frame`，看着像"是框架"其实是"是外链"。
* **`startsWithAny(null, ...)` 返回 `false`**，于是 `path` 为空的外链菜单会被拒绝
  （而不是抛 NPE）。`tests/.../TestAdd::test_a_missing_path_counts_as_a_bad_url` 锁这一条。

`_same_id` 是 `edit` 第三道闸的实现，**故意不复用 `==`**：

```python
def _same_id(left: Optional[int], right: Optional[int]) -> bool:
    if left is None:
        # Java: menu.getMenuId().equals(...) -> NPE
        raise AttributeError("'NoneType' object has no attribute 'equals'")
    return left == right
```

写成 `left == right` 会让 `None == None` 变成 `True`，于是"两个都没传"被当成
"上级是自己"并回一条业务错误；Java 这里是 **500**（NPE → 通用处理器）。
`tests/.../TestEdit::test_a_missing_menu_id_raises_like_the_java_npe` 锁这一条。

### 2.6 `remove` 的两道闸，顺序不能换

```java
if (menuService.hasChildByMenuId(menuId)) {
    return error("存在子菜单,不允许删除");
}
if (menuService.checkMenuExistRole(menuId)) {
    return error("菜单已分配,不允许删除");
}
return toAjax(menuService.deleteMenuById(menuId));
```

* 第一道用 `sys_menu`（`parent_id = ?` 的行数），**含按钮**：一个目录下只有按钮子节点
  也算"有子菜单"。
* 第二道查的是 **`sys_role_menu`**（`count(1) where menu_id = ?`），不是菜单表。
* 两道闸都是 `return`（不是抛异常），所以第一道命中时第二道的 SQL **不会**执行 ——
  `tests/.../TestRemove::test_the_child_gate_runs_first` 断言的是"`check_menu_exist_role`
  一次都没被调用"，而不是调用顺序。
* 文案里是**半角逗号**：`存在子菜单,不允许删除` / `菜单已分配,不允许删除`。

---

## 3. 服务层：`ISysMenuService` / `SysMenuServiceImpl`

接口 15 个方法，实现类另有 7 个不在接口里的 public 方法（供 `buildMenus` 使用，
也从 `SysMenuController` 之外被别的模块调用）。

| # | Java | Python | 备注 |
|---|---|---|---|
| 1 | `selectMenuList(Long userId)` | `select_menu_list_for_user(user_id)` | **重载改名**，见 §3.1 |
| 2 | `selectMenuList(SysMenu, Long userId)` | `select_menu_list(menu, user_id)` | 见 §3.2 |
| 3 | `selectMenuPermsByUserId(Long)` | `select_menu_perms_by_user_id(user_id)` | 装 `LoginUser` 用 |
| 4 | `selectMenuTreeByUserId(Long)` | `select_menu_tree_by_user_id(user_id)` | `GET /getRouters` |
| 5 | `selectMenuListByRoleId(Long)` | `select_menu_list_by_role_id(role_id)` | 见 §3.3 |
| 6 | `buildMenus(List<SysMenu>)` | `build_menus(menus)` | 树 → `RouterVo` |
| 7 | `buildMenuTree(List<SysMenu>)` | `build_menu_tree(menus)` | 平铺 → 树 |
| 8 | `buildMenuTreeSelect(List<SysMenu>)` | `build_menu_tree_select(menus)` | 树 → `TreeSelect` |
| 9 | `selectMenuById(Long)` | `select_menu_by_id(menu_id)` | 无行返回 `None` |
| 10 | `hasChildByMenuId(Long)` | `has_child_by_menu_id(menu_id)` | `count(1) > 0` |
| 11 | `checkMenuExistRole(Long)` | `check_menu_exist_role(menu_id)` | 见 §3.4 |
| 12 | `insertMenu(SysMenu)` | `insert_menu(menu)` | 见 §4.4 |
| 13 | `updateMenu(SysMenu)` | `update_menu(menu)` | 见 §4.5 |
| 14 | `deleteMenuById(Long)` | `delete_menu_by_id(menu_id)` | **物理删除**，见 §29.5 |
| 15 | `checkMenuNameUnique(SysMenu)` | `check_menu_name_unique(menu)` | 见 §3.5 |
| — | `selectMenuPermsByRoleId(Long)`（**不存在**） | `select_menu_perms_by_role_id(role_id)` | 多迁的一层，见 §4.1 |
| — | `getRouteName(SysMenu)` | `get_route_name(menu)` | 路由零件 |
| — | `getRouterPath(SysMenu)` | `get_router_path(menu)` | 路由零件 |
| — | `getComponent(SysMenu)` | `get_component(menu)` | 路由零件 |
| — | `isMenuFrame(SysMenu)` | `is_menu_frame(menu)` | 路由零件 |
| — | `isParentView(SysMenu)` | `is_parent_view(menu)` | 路由零件 |
| — | `getChildPerms(List, Long)` | `get_child_perms(menus, parent_id)` | 平铺 → 树 |
| — | `recursionFn` / `getChildList` / `hasChild`（private） | `_recursion_fn` / `_get_child_list` / `_has_child` | 递归辅助 |

### 3.1 两个 `selectMenuList` 重载在 Python 里必须改名

Java 允许同名重载，Python 不允许。取"单参的是给某个人看的"这层意思命名：

| Java | Python |
|---|---|
| `selectMenuList(Long userId)` | `select_menu_list_for_user(user_id)` |
| `selectMenuList(SysMenu menu, Long userId)` | `select_menu_list(menu, user_id)` |

单参版本在 Java 里就是 `selectMenuList(new SysMenu(), userId)`，Python 照抄：

```python
def select_menu_list_for_user(self, user_id: int) -> List[SysMenu]:
    return self.select_menu_list(SysMenu(), user_id)
```

`roleMenuTreeselect` 用的是**单参**版本（`checkedKeys` 与 `menus` 各查一次，共两条 SQL），
`list` / `treeselect` 用双参版本。控制器测试里有一条专门盯这个：
`TestRoleMenuTreeselect::test_it_uses_the_single_argument_overload`。

### 3.2 非超管分支会**写回** `menu.params`

```java
if (SysUser.isAdmin(userId)) {
    menuList = menuMapper.selectMenuList(menu);
} else {
    menu.getParams().put("userId", userId);
    menuList = menuMapper.selectMenuListByUserId(menu);
}
```

`params` 是 `BaseEntity` 上的 `Map<String, Object>`，Java 用它给 XML 传
`#{params.userId}`。Python 侧直接 `menu.params["userId"] = user_id`。

这是**副作用**：调用方传进来的 `menu` 对象被改了。照抄，不要"改干净"——
`select_menu_list_by_user_id` 后面就从 `menu.params` 里读这个值。

超管判据是 `SysUser.isAdmin(userId)`，即 `userId == 1`（`security_utils.is_admin`），
**不是**看角色 key。

### 3.3 `selectMenuListByRoleId` 先查角色再查菜单

```java
SysRole role = roleMapper.selectRoleById(roleId);
return menuMapper.selectMenuListByRoleId(roleId, role.getIsMenuCheckStrictly());
```

`role` 为 `null` 时 Java NPE。Python 侧不兜底：`role.menu_check_strictly` 抛 `AttributeError`，
落到通用处理器后同样是 HTTP 200 + `code 500`。

`menuCheckStrictly = true` 时 SQL 多一段 `not in (子查询)`，把"父节点已勾选"的子节点剔除，
让前端树只勾叶子。见 §4.6。

### 3.4 `checkMenuExistRole` 走**关联表**的 mapper

```java
int result = roleMenuMapper.checkMenuExistRole(menuId);
```

注意注入的是 `SysRoleMenuMapper`（不是 `SysMenuMapper`）。Python 的 `SysMenuService`
因此需要三个协作者：`mapper` / `role_mapper` / `role_menu_mapper`，
构造函数都接受 `None` 并在缺省时自己 `new`。

### 3.5 `checkMenuNameUnique` 的 `-1` 哨兵

```java
Long menuId = StringUtils.isNull(menu.getMenuId()) ? -1L : menu.getMenuId();
SysMenu info = menuMapper.checkMenuNameUnique(menu.getMenuName(), menu.getParentId());
if (StringUtils.isNotNull(info) && info.getMenuId().longValue() != menuId.longValue()) {
    return UserConstants.NOT_UNIQUE_OLD;
}
return UserConstants.UNIQUE_OLD;
```

新增时 `menuId` 是 `null`，用 `-1` 占位（主键不可能是负数），于是"撞到的自己是自己"
这条永远不会在新增分支成立。Python 侧 `menu_id = -1 if menu.menu_id is None else menu.menu_id`。

返回的是 `"0"` / `"1"` **字符串**（`UserConstants.UNIQUE_OLD` / `NOT_UNIQUE_OLD`），
不是 `boolean` —— 与 `sys_role` 一致。

### 3.6 路由零件：`getChildPerms` 会**静默丢掉**整棵子树

```java
for (SysMenu menu : list) {
    if (menu.getParentId().longValue() == parentId.longValue()) { ... }
}
```

只留 `parent_id` **恰好等于** 根（`0`）的节点。所以父目录被停用时，子菜单虽然还在
`selectMenuTreeByUserId` 的结果里，却**挂不到根上**，从而整体消失 ——
这正是"停用一个目录就隐藏整个子树"的实现方式。不要"修"成把孤儿节点提升到根。

`parent_id` 为 `null` 时 Java NPE；Python 侧写成 `menu.parent_id is not None and ...`，
对 `null` 返回 `False` 而不是抛错 —— 这是唯一一处**故意宽松**的地方，
因为 `sys_menu.parent_id` 是 `NOT NULL DEFAULT 0`，脏数据不会出现。

---

## 4. Mapper：14 条 statement

XML 里 11 个 `<select>` + 1 `<insert>` + 1 `<update>` + 1 `<delete>`，另有 1 个
`<sql id="selectMenuVo">` 与 1 个 `<resultMap id="SysMenuResult">`。

### 4.1 三个权限查询，其中**两个是孤儿**

| XML id | Python | 调用方 |
|---|---|---|
| `selectMenuPermsByUserId` | `select_menu_perms_by_user_id` | `selectMenuPermsByUserId` → 装 `LoginUser` |
| `selectMenuPermsByRoleId` | `select_menu_perms_by_role_id` | **没有** —— `SysMenuMapper` 接口里都没有这个方法 |
| `selectMenuPerms` | `select_menu_perms` | **没有** —— 连 `where` 都没有，会拉全表 |

后两条按迁移原则第 4 条**照留**，并在注释里标了"无 Java 对应"。§29.8 记录了这件事。
如果有人"清理死代码"把它们删掉，`test_sys_menu_mapper.py::TestSelectMenuPerms` 会变红。

### 4.2 两个树查询

| XML id | Python | 过滤条件 |
|---|---|---|
| `selectMenuTreeAll` | `select_menu_tree_all` | `menu_type in ('M','C')` + `status = 0`，**无 join** |
| `selectMenuTreeByUserId` | `select_menu_tree_by_user_id` | 上面两条 + `ur.user_id` + `ro.status = 0`（角色被停用则整组菜单消失） |

两条都以 `order by m.parent_id, m.order_num` 收尾。**不要**在 Python 里再排序 ——
`getChildPerms` 的兄弟顺序完全依赖这个 ORDER BY。

`ifnull(m.perms,'')` 让 `perms` 永远不是 `null`，所以树里的菜单 `perms` 是 `""` 而不是 `None`。

### 4.3 九个管理语句与两份列清单

| XML id | Python | 列清单 / 备注 |
|---|---|---|
| `selectMenuList` | `select_menu_list` | `selectMenuVo`（14 列）+ `<where>` 三个 `<if>` + `order by` |
| `selectMenuListByUserId` | `select_menu_list_by_user_id` | 内联 14 列 + 3 张 `left join` + `where ur.user_id = #{params.userId}` |
| `selectMenuListByRoleId` | `select_menu_list_by_role_id` | 只 select `m.menu_id` |
| `selectMenuById` | `select_menu_by_id` | `selectMenuVo` + `where menu_id` |
| `hasChildByMenuId` | `has_child_by_menu_id` | `count(1) where parent_id = ?` |
| `checkMenuNameUnique` | `check_menu_name_unique` | `selectMenuVo` + `menu_name = ? and parent_id = ? limit 1` |
| `insertMenu` | `insert_menu` | 动态列，见 §4.4 |
| `updateMenu` | `update_menu` | 动态 `<set>`，见 §4.5 |
| `deleteMenuById` | `delete_menu_by_id` | 方法内联 SQL（没有常量），**物理删除** |

两份列清单的差别（很容易踩）：

| | `<sql id="selectMenuVo">` | 树查询内联的那份 |
|---|---|---|
| 列数 | 14 | 14 |
| 表别名 | 无 | `m.` |
| `distinct` | 无 | **有** |
| `ifnull(perms,'')` | 有 | 有 |
| `create_by` / `update_by` / `update_time` / `remark` / `parent_name` | **没有** | **没有** |

所以走这些语句查出来的实体，那 5 个字段**恒为 `None`**。`SysMenu` 没有 `@JsonInclude`，
于是 JSON 里出现 `"parentName":null, "createBy":null, ...` —— 这不是漏映射，是 Java 原样。

`_to_sys_menu` 只映射 14 列，与 `<resultMap>` 的 19 个 property 相比少 5 个，
剩下的保持 `None`，与 MyBatis `autoMappingBehavior=PARTIAL` + "结果集里没有的列不覆盖"一致。

### 4.4 `insertMenu`：动态列 + **没有** `useGeneratedKeys`

```xml
<insert id="insertMenu" parameterType="SysMenu">
    insert into sys_menu(
    <if test="menuId != null and menuId != 0">menu_id,</if>
    <if test="parentId != null and parentId != 0">parent_id,</if>
    ...
    create_time
    )values( ... sysdate() )
</insert>
```

两点必须照抄：

1. **`menu_id` 与 `parent_id` 多一个 `!= 0` 判断**（其它列没有）。`parent_id = 0`（根节点）
   时整列被跳过，由 DDL 的 `DEFAULT 0` 兜底。
2. **没有 `useGeneratedKeys` / `keyProperty`** —— 全项目唯一一个不回写主键的
   `insertXxx`。Java 新增菜单后 `menu.getMenuId()` 仍是客户端传的值（通常是 `null`）。
   Python 的 `insert_menu` 只 `return rowcount`，**不** `result.lastrowid` 回写（§29.3）。

列的 `!= ''` 判断与 `updateMenu` **不一致**：这里 `component` / `perms` / `icon` / `remark`
都判 `!= null and != ''`，而 `visible` / `status` 只判 `!= null`（见 `_INSERT_MENU_COLUMNS`）。

### 4.5 `updateMenu` 的 `<set>` 不对称

| 字段 | 判据 | 传 `""` 时 |
|---|---|---|
| `menu_name` / `order_num` / `path` / `is_frame` / `is_cache` / `menu_type` / `icon` / `remark` / `update_by` | `!= null and != ''` | 整列**跳过**（保留旧值） |
| `parent_id` | 只有 `!= null` | 写 `0` 是合法的，"不动父节点"只能靠不传 |
| `component` / `visible` / `status` / `perms` | 只有 `!= null` | **清成空串**（覆盖旧值） |
| `update_time` | 不在 `<if>` 里 | 恒为 `sysdate()`，永远最后一个赋值 |

"清空组件路径"是前端真实会做的事（把输入框删干净 → 发 `""`），所以 `component` 必须能清；
而"清空路由地址"不行，`path` 传 `""` 会被跳过。**不要统一**这两类判据（§29.4）。

`update_time = sysdate()` 无条件带上，所以"只改一个字段"也会刷新修改时间。

### 4.6 `menuCheckStrictly` 是 primitive，所以那个 `<if>` 是**活条件**

```xml
<if test="menuCheckStrictly">
  and m.menu_id not in (select m.parent_id from sys_menu m ...)
</if>
```

`selectMenuListByRoleId(@Param("menuCheckStrictly") boolean menuCheckStrictly)` 的形参是
**primitive `boolean`**，OGNL 取到的是真值，所以这个 `<if>` **真的**在决定 SQL 拼不拼。

这与 `sys_role` 那边的 `menuCheckStrictly != null`（`Boolean` 包类型，永远为真 → 死条件，
见 COMPATIBILITY §28.4）**恰好相反**。两处同名不同义，别把这里也写成"永远拼上"。

Python 侧：

```python
sql = _SELECT_MENU_LIST_BY_ROLE_ID
if menu_check_strictly:
    sql += _SELECT_MENU_LIST_BY_ROLE_ID_STRICTLY
sql += "        order by m.parent_id, m.order_num\n"
```

`select_menu_list_by_role_id(role_id, menu_check_strictly)` 的第二个形参**没有默认值**，
与 Java 的 primitive 形参一致（调用方必须给）。

---

## 5. Bean Validation：7 条约束 / 6 个字段

```java
@NotBlank(message = "菜单名称不能为空")
@Size(min = 0, max = 50, message = "菜单名称长度不能超过50个字符")
public String getMenuName() { return menuName; }

@NotBlank(message = "显示顺序不能为空")                      // 没有 @Size
public String getOrderNum() { return orderNum; }

@Size(min = 0, max = 200, message = "路由地址不能超过200个字符")
public String getPath() { return path; }

@Size(min = 0, max = 200, message = "组件路径不能超过255个字符")   // 200 vs 255，原文如此
public String getComponent() { return component; }

@NotBlank(message = "菜单类型不能为空")                       // 没有 @Size
public String getMenuType() { return menuType; }

@Size(min = 0, max = 100, message = "权限标识长度不能超过100个字符")
public String getPerms() { return perms; }
```

`parentName` / `parentId` / `isFrame` / `isCache` / `visible` / `status` / `icon` 上
**没有任何注解** —— 不要看到 `@NotBlank` 就"补全"到所有字段。

`MENU_CONSTRAINTS` 按 getter 声明顺序排列（`menu_name` NotBlank → `menu_name` Size →
`order_num` NotBlank → `path` Size → `component` Size → `menu_type` NotBlank → `perms` Size），
因此"多字段同时违规"时报第一条：空 body → `菜单名称不能为空`。

### 5.1 `component` 的上限与文案对不上

`@Size(max = 200)` 但文案写"不能超过255个字符"。**照抄**，不要"顺手改成 255"：
改了以后 201–255 字符的组件路径会从"被拒绝"变成"通过"，是真实的行为改变。

### 5.2 校验写成 `Depends` 的原因

Spring 的真实顺序是：

```
安全过滤器链(401) -> 路由 -> 反序列化 + 校验(500) -> @PreAuthorize(403) -> 方法体
```

`ValidMenu` 是 `Annotated[SysMenu, Depends(_validated_menu)]`，依赖在端点函数体之前解析，
正好补回 Spring 的位置。写成函数体第一行的话，"未登录 + 缺 menuName"会变成 403 而不是 500。

回归用例：`tests/test_sys_menu_controller.py::TestValidationRunsBeforePermission`（4 条）。

---

## 6. 实体字段：只列容易被改错的

| Java | Python | 类型 | 说明 |
|---|---|---|---|
| `Long menuId` | `menu_id` | `Optional[int]` | 主键；**插入后不会被回写**（§29.3） |
| `String menuName` | `menu_name` | `Optional[str]` | `@NotBlank` + `@Size(max=50)` |
| `String parentName` | `parent_name` | `Optional[str]` | 查询从不 select，恒 `None`（JSON 里是 `null`） |
| `Long parentId` | `parent_id` | `Optional[int]` | `0` = 根 |
| `String orderNum` | `order_num` | `JavaString` | **varchar 列 + `String` 字段**，前端发数字要强转 |
| `String path` | `path` | `Optional[str]` | `@Size(max=200)` |
| `String component` | `component` | `Optional[str]` | `@Size(max=200)`，文案写 255 |
| `String isFrame` | `is_frame` | `Optional[str]` | `0` **是外链** / `1` 否 —— 语义是反的 |
| `String isCache` | `is_cache` | `Optional[str]` | `0` 缓存 / `1` 不缓存 |
| `String menuType` | `menu_type` | `Optional[str]` | `M` 目录 / `C` 菜单 / `F` 按钮 |
| `String visible` | `visible` | `Optional[str]` | `0` 显示 / `1` 隐藏 |
| `String status` | `status` | `Optional[str]` | `0` 正常 / `1` 停用 |
| `String perms` | `perms` | `Optional[str]` | `@Size(max=100)`；树查询里经 `ifnull` 后是 `""` |
| `String icon` | `icon` | `Optional[str]` | |
| `List<SysMenu> children` | `children` | `List[SysMenu] = []` | Java `new ArrayList<>()`，**永不为 `None`** |

`children` 必须是 `default_factory=list`：`SysMenuServiceImpl#buildMenus` 里有
`cMenus.isEmpty()`，`None` 会 NPE。

`SysMenu` **没有** `@JsonInclude`（`RouterVo` / `TreeSelect` 有），所以实体是"胖返回"：
`null` 字段和空的 `children` 都会出现在 `/system/menu/list` 的响应里。

`order_num` 用 `JavaString` 而不是 `Optional[str]`：DB 是 `varchar(4)`，但前端
`el-input-number` 发的是 JSON 数字，Jackson 会强转，pydantic 默认拒绝（§25.5）。

---

## 7. 逐行对照速查

```text
SysMenuController#list                    -> sys_menu_controller.list_menus            (GET    /system/menu/list)
SysMenuController#treeselect              -> sys_menu_controller.treeselect            (GET    /system/menu/treeselect)
SysMenuController#roleMenuTreeselect      -> sys_menu_controller.role_menu_treeselect  (GET    /system/menu/roleMenuTreeselect/{roleId})
SysMenuController#getInfo                 -> sys_menu_controller.get_info              (GET    /system/menu/{menuId})
SysMenuController#add                     -> sys_menu_controller.add                   (POST   /system/menu)
SysMenuController#edit                    -> sys_menu_controller.edit                  (PUT    /system/menu)
SysMenuController#remove                  -> sys_menu_controller.remove                (DELETE /system/menu/{menuId})

SysMenuServiceImpl#selectMenuList(Long)          -> SysMenuService.select_menu_list_for_user
SysMenuServiceImpl#selectMenuList(SysMenu, Long) -> SysMenuService.select_menu_list
SysMenuServiceImpl#selectMenuPermsByUserId       -> SysMenuService.select_menu_perms_by_user_id
SysMenuServiceImpl#selectMenuTreeByUserId        -> SysMenuService.select_menu_tree_by_user_id
SysMenuServiceImpl#selectMenuListByRoleId        -> SysMenuService.select_menu_list_by_role_id
SysMenuServiceImpl#buildMenus                    -> SysMenuService.build_menus
SysMenuServiceImpl#buildMenuTree                 -> SysMenuService.build_menu_tree
SysMenuServiceImpl#buildMenuTreeSelect           -> SysMenuService.build_menu_tree_select
SysMenuServiceImpl#selectMenuById                -> SysMenuService.select_menu_by_id
SysMenuServiceImpl#hasChildByMenuId              -> SysMenuService.has_child_by_menu_id
SysMenuServiceImpl#checkMenuExistRole            -> SysMenuService.check_menu_exist_role
SysMenuServiceImpl#insertMenu                    -> SysMenuService.insert_menu
SysMenuServiceImpl#updateMenu                    -> SysMenuService.update_menu
SysMenuServiceImpl#deleteMenuById                -> SysMenuService.delete_menu_by_id
SysMenuServiceImpl#checkMenuNameUnique           -> SysMenuService.check_menu_name_unique
SysMenuServiceImpl#getRouteName                  -> SysMenuService.get_route_name
SysMenuServiceImpl#getRouterPath                 -> SysMenuService.get_router_path
SysMenuServiceImpl#getComponent                  -> SysMenuService.get_component
SysMenuServiceImpl#isMenuFrame                   -> SysMenuService.is_menu_frame
SysMenuServiceImpl#isParentView                  -> SysMenuService.is_parent_view
SysMenuServiceImpl#getChildPerms                 -> SysMenuService.get_child_perms
SysMenuServiceImpl#recursionFn (private)         -> SysMenuService._recursion_fn
SysMenuServiceImpl#getChildList (private)        -> SysMenuService._get_child_list
SysMenuServiceImpl#hasChild     (private)        -> SysMenuService._has_child

SysMenuMapper.xml#selectMenuList            -> SysMenuMapper.select_menu_list
SysMenuMapper.xml#selectMenuTreeAll         -> SysMenuMapper.select_menu_tree_all
SysMenuMapper.xml#selectMenuListByUserId    -> SysMenuMapper.select_menu_list_by_user_id
SysMenuMapper.xml#selectMenuTreeByUserId    -> SysMenuMapper.select_menu_tree_by_user_id
SysMenuMapper.xml#selectMenuListByRoleId    -> SysMenuMapper.select_menu_list_by_role_id
SysMenuMapper.xml#selectMenuPerms           -> SysMenuMapper.select_menu_perms            (孤儿)
SysMenuMapper.xml#selectMenuPermsByUserId   -> SysMenuMapper.select_menu_perms_by_user_id
SysMenuMapper.xml#selectMenuPermsByRoleId   -> SysMenuMapper.select_menu_perms_by_role_id  (孤儿)
SysMenuMapper.xml#selectMenuById            -> SysMenuMapper.select_menu_by_id
SysMenuMapper.xml#hasChildByMenuId          -> SysMenuMapper.has_child_by_menu_id
SysMenuMapper.xml#checkMenuNameUnique       -> SysMenuMapper.check_menu_name_unique
SysMenuMapper.xml#insertMenu                -> SysMenuMapper.insert_menu
SysMenuMapper.xml#updateMenu                -> SysMenuMapper.update_menu
SysMenuMapper.xml#deleteMenuById            -> SysMenuMapper.delete_menu_by_id

SysRoleMenuMapper.xml#checkMenuExistRole    -> SysRoleMenuMapper.check_menu_exist_role     (sys_menu 删除前校验)
SysRoleMapper.xml#selectRoleById            -> SysRoleMapper.select_role_by_id             (取 menuCheckStrictly)
```
