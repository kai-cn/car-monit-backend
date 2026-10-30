# MAPPING_SYS_ROLE.md — `sys_role` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §28。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectRoleList` → `select_role_list`，`checkRoleKeyUnique` → `check_role_key_unique`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysRoleService` + `SysRoleServiceImpl`）
  在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。
- 本切片**新增了三个文件**（`sys_role_menu_mapper.py` / `sys_role_dept_mapper.py` /
  `sys_role_menu.py` + `sys_role_dept.py`），它们此前只在 `sys_user_role` 里出现过同类物。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysRoleController.java` | `app/api/system/sys_role_controller.py` | **10 个映射，迁 9 个**（`export` 见 §28.1） |
| `ruoyi-system/.../service/ISysRoleService.java`<br>`ruoyi-system/.../service/impl/SysRoleServiceImpl.java` | `app/system/service/sys_role_service.py` | 接口 + 实现合并为 `SysRoleService`；18 个方法（含 2 个本项目新增的计数方法） |
| `ruoyi-system/.../mapper/SysRoleMapper.java`<br>`.../resources/mapper/system/SysRoleMapper.xml` | `app/system/mapper/sys_role_mapper.py` | 接口 + XML 合并：**12** 条 statement 各变成一个模块级 SQL 常量 |
| `ruoyi-system/.../mapper/SysRoleMenuMapper.java`<br>`.../mapper/system/SysRoleMenuMapper.xml` | `app/system/mapper/sys_role_menu_mapper.py` | **新增文件**；4 条 statement |
| `ruoyi-system/.../mapper/SysRoleDeptMapper.java`<br>`.../mapper/system/SysRoleDeptMapper.xml` | `app/system/mapper/sys_role_dept_mapper.py` | **新增文件**；4 条 statement |
| `ruoyi-system/.../domain/SysRoleMenu.java` | `app/system/domain/sys_role_menu.py` | **新增文件**；纯 POJO（`@dataclass`） |
| `ruoyi-system/.../domain/SysRoleDept.java` | `app/system/domain/sys_role_dept.py` | **新增文件**；纯 POJO（`@dataclass`） |
| `ruoyi-common/.../core/domain/entity/SysRole.java` | `app/common/core/domain/entity/sys_role.py` | 14 个字段 + `BaseEntity`；含 `ROLE_CONSTRAINTS`（5 条） |
| `ruoyi-system/.../mapper/SysUserRoleMapper.java`（`countUserRoleByRoleId` / `countUserRoleByRoleIdUserId`） | `app/system/mapper/sys_user_role_mapper.py` | 本切片**新增** `count_user_role_by_role_id_user_id` |
| `ruoyi-common/.../core/domain/BaseEntity.java` | `app/common/core/domain/base_entity.py` | `createBy` / `updateBy` / `params` ... |
| `ruoyi-common/.../constant/UserConstants.java` | `app/common/constant/user_constants.py` | 只用 `UNIQUE_OLD = "0"` / `NOT_UNIQUE_OLD = "1"` |
| `ruoyi-common/.../core/controller/BaseController.java` | `app/common/core/controller/base_controller.py` | `start_page` / `get_data_table` / `to_ajax` / `parse_id_array` / `bind_query_params` |
| `ruoyi-common/.../core/domain/TreeSelect.java` | 未使用 | 角色没有树形返回 |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-framework/.../web/service/PermissionService.java`（`@ss.hasPermi`） | `app/framework/web/service/permission_service.py` | `@pre_authorize_permi("...")`，**4 个标识 7 处使用** |
| `ruoyi-framework/.../web/service/SysPermissionService.java` | `app/framework/web/service/sys_permission_service.py` | `edit` 里刷新缓存时调 `get_menu_permission` |
| `ruoyi-framework/.../web/service/TokenService.java` | `app/framework/web/service/token_service.py` | `edit` 里 `get_login_user` / `set_login_user` |
| `ruoyi-framework/.../aspectj/DataScopeAspect.java` | `app/framework/aspectj/data_scope_aspect.py` | **本切片真的生效**（与 `sys_dept` 相反），见 §3.2 |
| `ruoyi-framework/.../aspectj/LogAspect.java` | **未迁移** | 因此不写 `sys_oper_log`，见 §28.2 |
| `ruoyi-common/.../utils/SecurityUtils.java` | `app/common/utils/security_utils.py` | `get_username()` |
| `ruoyi-common/.../utils/spring/SpringUtils.java`（`getAopProxy`） | 无需对应 | Python 直接调自身方法，见 §3.2 |
| `Hibernate Validator`（`MethodArgumentNotValidException`） | `bean_validation.validate()` + `RuntimeError` 处理器 | 见 §5 |

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_role_mapper.py` | 41 | 12 + 4 + 4 条 SQL 的拼装 / 5 个 `<if>` 顺序 / `${dataScope}` 拼接 / 两个 `<foreach>` / `lastrowid` 回写 |
| Service | `tests/test_sys_role_service.py` | 35 | 数据权限传递 / 名称与权限字符判重 / `@Transactional` 语义 / 两道删除拦截 / roleKey 分段 |
| Controller | `tests/test_sys_role_controller.py` | 70 | 路由表（9 条）/ 5 个权限点 / 校验先于权限 / 三道闸 / `edit` 的缓存刷新三条分支 |

合计 **146** 条；全量套件 **1051 passed**。

Java 侧 **没有任何 `src/test`**，所以上表没有"Java 对应用例"列 ——
这些用例是照着 Java 源码逐行推导出来的，不是移植过来的。

---

## 2. 控制器：10 个映射逐条对照

前缀都是 `/system/role`。`权限` 列是 `@PreAuthorize("@ss.hasPermi(...)")` 的值；
写 `登录` 表示**没有注解**。

| # | Java 方法 | Python 函数 | HTTP + 路径 | 权限 |
|---|---|---|---|---|
| 1 | `list(SysRole role)` | `list_roles(role: RoleParam)` | `GET /system/role/list` | **登录**（注解被注释掉） |
| 2 | `export(SysRole role)` | — | `GET /system/role/export` | **未迁移**（§28.1） |
| 3 | `getInfo(Long roleId)` | `get_info(role_id: int)` | `GET /system/role/{roleId}` | `system:role:query` |
| 4 | `add(SysRole role)` | `add(role: ValidRole)` | `POST /system/role` | `system:role:add` |
| 5 | `edit(SysRole role)` | `edit(role: ValidRole, request)` | `PUT /system/role` | `system:role:edit` |
| 6 | `dataScope(SysRole role)` | `data_scope(role: SysRole)` | `PUT /system/role/dataScope` | `system:role:edit` |
| 7 | `changeStatus(SysRole role)` | `change_status(role: SysRole)` | `PUT /system/role/changeStatus` | `system:role:edit` |
| 8 | `remove(Long[] roleIds)` | `remove(role_ids: str)` | `DELETE /system/role/{roleIds}` | `system:role:remove` |
| 9 | `optionselect()` | `optionselect()` | `GET /system/role/optionselect` | `system:role:query` |
| 10 | `selectlist(SysRole role)` | `selectlist(role: RoleParam)` | `GET /system/role/selectlist` | **登录** |

### 2.1 `list` 的 `@PreAuthorize` 在 Java 里是**注释掉**的

`SysRoleController.java` 第 47 行：

```java
// @PreAuthorize("@ss.hasPermi('system:role:list')")
@GetMapping("/list")
public TableDataInfo list(SysRole role)
```

所以"角色管理"列表页**任何登录用户**都能访问 —— 与本项目其它模块（`sys_post` /
`sys_dept` 都真的校验了 `:list`）不同。Python 侧照抄：`list_roles` 上**没有**
`@pre_authorize_permi`。`selectlist` 同理（它是本项目加的"下拉角色"接口，Java 里也没有注解）。

这一条是**安全相关**的：看到 `system:role:query` 出现在 `get_info` / `optionselect` 上就
"顺手"给 `list` 也加一个，会让普通用户的角色下拉框突然 403。

回归用例：`tests/test_sys_role_controller.py::TestPermissions::test_list_only_need_a_login`。

### 2.2 形参绑定的三种写法

| Java 形参 | 绑定来源 | Python |
|---|---|---|
| `SysRole role`（**无**注解） | query string | `RoleParam = Annotated[SysRole, Depends(_query_role)]` |
| `@Validated @RequestBody SysRole role` | JSON body + 校验 | `ValidRole = Annotated[SysRole, Depends(_validated_role)]` |
| `@RequestBody SysRole role`（裸） | JSON body，**不校验** | `role: SysRole`（`dataScope` / `changeStatus`） |
| `@PathVariable Long[] roleIds` | 路径，逗号分隔 | `role_ids: str` + `parse_id_array()` |
| `@PathVariable Long roleId` | 路径 | `role_id: int` |
| 无参数 | — | `optionselect()` |

`dataScope` / `changeStatus` 是裸 `@RequestBody`，所以只传
`{"roleId": 2, "status": "1"}` 改状态是**合法**的（不需要 `roleName` / `roleKey` / `roleSort`）。
给它们套 `ValidRole` 会凭空造出 500，是真实的回归。

### 2.3 声明顺序：三个字面量路径必须写在 `/{role_id}` 之前

FastAPI **按注册顺序**匹配。`/system/role/optionselect` 若排在 `/system/role/{role_id}`
之后，会被当成 `role_id = "optionselect"`，随后在 `int` 转换处炸掉（HTTP 500）。

顺序（文件里的实际顺序）：

```
/list   /optionselect   /selectlist   /{role_id}   POST ""   PUT ""
PUT /dataScope   PUT /changeStatus   DELETE /{role_ids}
```

注意 `POST` / `PUT` 用的是空串 `""`（拼出 `/system/role`，与 Java 的
`@PostMapping` / `@PutMapping` 一致），**不是** `"/"`：后者会多出一条
`/system/role/` 的尾斜杠路由，Java 没有。

防回退阀：`TestRouteTable::test_literal_paths_come_before_the_path_variable`。

### 2.4 三道闸的顺序（`add` 与 `edit` 不同）

`add`（两道闸）：

```python
if _is_not_unique(check_role_name_unique(role)):   # ① 角色名称
    return AjaxResult.error_message(ADD_ROLE_NAME_EXISTS.format(role.role_name))
elif _is_not_unique(check_role_key_unique(role)):  # ② 权限字符
    return AjaxResult.error_message(ADD_ROLE_KEY_EXISTS.format(role.role_name))
role.create_by = SecurityUtils.get_username()
return to_ajax(insert_role(role))
```

`edit`（**三道**闸，第一道是超管拦截）：

```python
role_service.check_role_allowed(role)              # ⓪ roleId == 1 -> 抛 CustomException
if _is_not_unique(check_role_name_unique(role)):   # ①
    ...
elif _is_not_unique(check_role_key_unique(role)):  # ②
    ...
```

两个细节：

- 超管拦截**抛异常**（`CustomException` → HTTP 200 + `code 500`），不是返回
  `AjaxResult.error(...)`。所以它出现在 `TestEditEndpoint::test_the_admin_role_cannot_be_edited`
  的 `{"code": 500, "msg": "不允许操作超级管理员角色"}` 里，而不是某条"修改角色失败"文案。
- 提示文案里插的是 **`role.getRoleName()`**，不是重复的那个字段值。`roleKey` 重复时
  文案仍是"新增角色'运营'失败，角色权限已存在"（用名称填充）。

### 2.5 `edit` 成功后刷新"当前登录用户"的缓存

```python
if role_service.update_role(role) > 0:
    login_user = _token_service().get_login_user(request)
    if login_user.user is not None and not login_user.user.admin:
        login_user.permissions = _permission_service().get_menu_permission(login_user.user)
        login_user.user = _user_service().select_user_by_user_name(login_user.user.user_name)
        _token_service().set_login_user(login_user)
    return AjaxResult.success()
return AjaxResult.error_message(EDIT_ROLE_FAILED.format(role.role_name))
```

三点必须保留：

1. 刷新的是**当前请求者**的令牌，不是被修改角色的成员。改别人的角色，自己的
   `login_tokens:<uuid>` 会被重写（顺带续期 120 分钟）。
2. `loginUser` 为 `null` 时 Java 直接 NPE（`loginUser.getUser()`）—— 路由要求认证，
   理论上走不到，但这里**不**加 `if login_user is not None` 兜底。
3. 分支条件是 `!user.isAdmin()`（即 `userId != 1`）。超管改角色不刷新缓存。

`set_login_user` 只在 `login_user.token` 非空时才真正写 Redis（
`TokenService#setLoginUser` 的实现），所以测试里注入的假 `LoginUser` 没有 `token`
时看不到"写缓存"的副作用 —— 这是 `TokenService` 的行为，不是控制器的。

---

## 3. 服务层：`ISysRoleService` / `SysRoleServiceImpl`

18 个方法全部迁移（16 个 Java 接口方法 + 2 个项目自建的计数方法）。

| # | Java | Python | 备注 |
|---|---|---|---|
| 1 | `selectRolePermissionByUserId(Long)` | `select_role_permission_by_user_id` | 返回**权限字符集合**，见 §3.1 |
| 2 | `selectRoleList(SysRole)` | `select_role_list` | `@DataScope`，见 §3.2 |
| 3 | `selectRoleAll()` | `select_role_all` | 内部转调 `select_role_list`，见 §3.2 |
| 4 | `selectRoleListByUserId(Long)` | `select_role_list_by_user_id` | 返回**角色 id 列表**（`Integer`） |
| 5 | `selectRoleById(Long)` | `select_role_by_id` | 无行返回 `None` |
| 6 | `selectRolesByUserName(String)` | `select_roles_by_user_name` | 登录时装配 `LoginUser` 用 |
| 7 | `checkRoleNameUnique(SysRole)` | `check_role_name_unique` | 返回 `"0"`/`"1"` **字符串** |
| 8 | `checkRoleKeyUnique(SysRole)` | `check_role_key_unique` | 同上 |
| 9 | `checkRoleAllowed(SysRole)` | `check_role_allowed` | 抛 `CustomException` |
| 10 | `countUserRoleByRoleId(Long)` | `count_user_role_by_role_id` | 项目新增 |
| 11 | `countUserRoleByRoleIdUserId(Long, Long)` | `count_user_role_by_role_id_user_id` | 项目新增 |
| 12 | `insertRole(SysRole)` | `insert_role` | 返回 **insertRoleMenu 的行数** |
| 13 | `updateRole(SysRole)` | `update_role` | 先全删再插菜单 |
| 14 | `updateRoleStatus(SysRole)` | `update_role_status` | 走整行 `update_role` |
| 15 | `authDataScope(SysRole)` | `auth_data_scope` | 先全删再插部门 |
| 16 | `insertRoleMenu(SysRole)` | `insert_role_menu` | `public`，空集合返回 1 |
| 17 | `insertRoleDept(SysRole)` | `insert_role_dept` | `public`，空集合返回 1 |
| 18 | `deleteRoleById(Long)` | `delete_role_by_id` | **无**两道拦截，见 §28.7 |
| 19 | `deleteRoleByIds(Long[])` | `delete_role_by_ids` | 先逐个校验，再删 |

（表里 19 行，第 10/11 是项目新增的两条计数，Java 接口里没有 —— 见 §3.6。）

### 3.1 `selectRolePermissionByUserId` 返回的是"权限字符"，会按逗号拆

```java
for (SysRole perm : perms) {
    if (StringUtils.isNotNull(perm)) {
        permsSet.addAll(Arrays.asList(perm.getRoleKey().trim().split(",")));
    }
}
```

- 返回 `Set<String>`，元素是 `role_key`（如 `"admin"`、`"common"`），**不是** `role_id`；
- `"admin,common"` 这种一个角色带多个权限字符的写法会被拆成两个；
- `trim()` 只作用于**整串**，不逐段去空格 —— `" a , b "` → `{"a ", " b"}`（见 §28.6）。

### 3.2 `selectRoleAll` 必须绕一圈走 `selectRoleList`

```java
public List<SysRole> selectRoleAll() {
    return SpringUtils.getAopProxy(this).selectRoleList(new SysRole());
}
```

Java 故意通过 AOP 代理调自己，就是为了让 `@DataScope` 生效。所以：

- Python 侧 `select_role_all()` 里写的是 `return self.select_role_list(SysRole())`，
  **不能**改成 `self._mapper.select_role_all()`；
- `SysRoleMapper.xml#selectRoleAll` 因此在 Java 里**没有任何调用者**（
  `selectRoleAll()` 走的是 `selectRoleList`）。按迁移原则第 4 条，XML 里那条照留、
  Python 里 `SysRoleMapper.select_role_all` 也照留，只是没人调。

为什么这件事在角色这里比部门更要紧：`sys_dept` 的 `${params.dataScope}` 是 XML 注释，
"漏掉"没有后果；而 `SysRoleMapper.xml#selectRoleList` 里的 `${params.dataScope}`
是**活的**，漏掉 `apply_data_scope` 会让 `/optionselect` 多返回一批越权角色。

### 3.3 `insertRole` 的返回值不是插入行数

```python
def insert_role(self, role: SysRole) -> int:
    self._mapper.insert_role(role)          # 恒为 1 行，但**不**作为返回值
    return self.insert_role_menu(role)      # 返回值来自这里
```

于是：

| 场景 | 返回值 | 接口响应 |
|---|---|---|
| 勾了 3 个菜单 | `batchRoleMenu` 的行数（3） | `操作成功` |
| 一个菜单都没勾（`menuIds: []`） | `1`（`insert_role_menu` 的初值） | `操作成功` |
| `menuIds` 缺失（`null`） | 抛 `TypeError`（Java NPE） | HTTP 200 + `code 500`，但**角色已入库**（§28.3） |

`insert_role_menu` **不**写 `role.menu_ids or []`：Java 的 `for-each` 在 `null` 上 NPE，
Python 的 `for` 在 `None` 上 `TypeError`，两边都是 500。

### 3.4 `authDataScope` 无条件清空 `sys_role_dept`

```python
self._mapper.update_role(role)                                   # 只改 data_scope 等
self._role_dept_mapper.delete_role_dept_by_role_id(role.role_id) # 先全删
return self.insert_role_dept(role)                               # 再按 deptIds 插
```

不管新范围是不是 `"2"`（自定义），都先清空。所以把范围从 `自定义` 改成 `全部数据`，
旧的部门授权会被一起清掉 —— 这是 Java 原样，不是 bug。

控制器侧 `data_scope` **不**设 `update_by`（Java 原文没有 `setUpdateBy`）。

### 3.5 `updateRoleStatus` 走的是整行更新

```python
def update_role_status(self, role: SysRole) -> int:
    return self._mapper.update_role(role)
```

虽然是 `changeStatus` 端点，落到 SQL 的是 `updateRole` 那条动态 `<set>`，因此：

- **不会**动 `sys_role_menu`；
- **会**把 `menu_check_strictly` / `dept_check_strictly` 重置成 `0`（primitive boolean，§28.4）；
- 控制器会设 `update_by`（`change_status` 里有 `role.update_by = get_username()`，
  而 `dataScope` 没有）。

### 3.6 两个计数方法

`countUserRoleByRoleId` 在 Java 接口里，本项目又加了
`countUserRoleByRoleIdUserId(roleId, userId)`（`SysUserRoleMapper.xml` 里对应
`countUserRoleByRoleIdUserId`）。它目前只被 `sys_user` 的角色分配页调用，
本切片一并补齐，避免"另一个切片要用时再回头找 XML"。

### 3.7 依赖注入

Java 是 `@Autowired` 四个 Mapper 字段（`roleMapper` / `roleMenuMapper` /
`userRoleMapper` / `roleDeptMapper`）。Python 是构造函数四个可选参数 + 模块级单例
（`get_role_service()` / `reset_role_service()`）；四个字段都有只读 property，
名字与 Java 字段一一对应（`mapper` / `role_menu_mapper` / `user_role_mapper` /
`role_dept_mapper`）。

测试直接 `SysRoleService(fake_role, fake_menu, fake_user_role, fake_dept)`。

---

## 4. Mapper 层

### 4.1 `SysRoleMapper`（12 条 statement + 1 个 `<sql>` + 1 个 `<resultMap>`）

| XML 片段 | Python | 备注 |
|---|---|---|
| `<sql id="selectRoleVo">` | `_SELECT_ROLE_VO` | `select distinct` + 三张表 `left join`，逐字照抄 |
| `selectRoleList` | `select_role_list` | 5 个 `<if>` + `${params.dataScope}`，见 §4.2 |
| `selectRolePermissionByUserId` | `select_role_permission_by_user_id` | `r.del_flag = '0' and ur.user_id = ?` |
| `selectRoleAll` | `select_role_all` | **无 WHERE**（连 `del_flag` 都不过滤）；无调用者 |
| `selectRoleListByUserId` | `select_role_list_by_user_id` | `resultType="Integer"`，只取 `role_id` |
| `selectRoleById` | `select_role_by_id` | **不过滤** `del_flag` |
| `selectRolesByUserName` | `select_roles_by_user_name` | `u.user_name = ?`（`sys_user` 表） |
| `checkRoleNameUnique` | `check_role_name_unique` | `limit 1` 写在 XML 里；**不过滤** `del_flag` |
| `checkRoleKeyUnique` | `check_role_key_unique` | 同上 |
| `insertRole` | `insert_role` | 动态列 + `sysdate()` + `lastrowid` 回写，见 §4.3 |
| `updateRole` | `update_role` | 动态 `<set>`，见 §4.4 |
| `deleteRoleById` | `delete_role_by_id` | 名为 delete，SQL 是 `update ... del_flag = '2'` |
| `deleteRoleByIds` | `delete_role_by_ids` | `<foreach>` → `in (:p0, :p1, ...)` |
| `<resultMap id="SysRoleResult">` | `_map_role` | 14 个属性，但 `selectRoleVo` 只投影 11 列，见 §4.5 |

### 4.2 `selectRoleList` 的 5 个 `<if>`，顺序固定

```
roleName(like) → status → roleKey(等值) → params.beginTime → params.endTime
→ ${params.dataScope} → order by r.role_sort
```

- **判据是 OGNL 的 `x != null and x != ''`，不是 `isBlank`。** 项目里的
  `string_utils.is_not_empty()` 照抄的是 `StringUtils.isEmpty`，它**先 `trim`**，
  于是 `is_not_empty(" ")` 是 `False` —— 用它就会漏掉"只填一个空格"的条件。
  `_text()` 因此写成 `value is not None and value != ""`。
- `roleKey` 是**等值**匹配（`= :role_key`），`roleName` 是 `like concat('%', ...)`。
- `beginTime` / `endTime` 走 `date_format(..., '%y%m%d')` 比较 —— 两位年份，
  跨世纪数据会错，照抄。
- `${params.dataScope}` 是**字符串拼接**（不是 `#{}`），值来自
  `apply_data_scope(role, "d")`，形如 `" AND (d.dept_id = 100 )"`。

### 4.3 `insertRole` 的动态列

| 列 | 判据 | 传 `""` / `0` 时 |
|---|---|---|
| `role_id` | `!= null and != 0` | 整列不出现（自增） |
| `role_name` / `role_key` / `role_sort` / `data_scope` | `!= null and != ''` | 整列不出现 |
| `menu_check_strictly` / `dept_check_strictly` | `!= null` | **永远出现**（primitive boolean，§28.4） |
| `status` / `remark` / `create_by` | `!= null and != ''` | 整列不出现 |
| `create_time` | — | 恒为 `sysdate()`，不走参数 |

`useGeneratedKeys="true" keyProperty="roleId"` → `result.lastrowid` 写回
`role.role_id`（MyBatis 的 `Jdbc3KeyGenerator` 同样是直接 set 到实体上）。
Service 后续 `insert_role_menu` 依赖这个回写值，所以在 `insert_role` 之前不能读 `role_id`。

### 4.4 `updateRole` 的 `<set>`：只有 `remark` 是 `!= null`

| 列 | 判据 |
|---|---|
| `role_name` / `role_key` / `role_sort` / `data_scope` / `status` / `update_by` | `!= null and != ''` |
| `menu_check_strictly` / `dept_check_strictly` | `!= null` → **永远出现** |
| `remark` | **只有** `!= null` → 空串会清列 |
| `update_time` | 恒为 `sysdate()`（不在 `<if>` 里） |

`update_time = sysdate()` 无条件带上，所以"只改状态"和"只改数据权限"也会刷新修改时间。

### 4.5 投影：`selectRoleVo` 只给 11 列

`<resultMap>` 声明了 14 个属性，但 `<sql id="selectRoleVo">` 只 select 11 列：
`create_by` / `update_by` / `update_time` 这 3 列**没有列源**，走这些语句时恒为 `None`
（`BaseEntity` 无 `@JsonInclude`，Jackson 会输出 `"createBy": null`）。

`tests/test_sys_role_mapper.py::TestSelectRoleById::test_all_columns_are_mapped`
锁的是"映射器不抛错、11 列都有值"，不是"14 列都有值"。

### 4.6 `sys_role_menu` / `sys_role_dept` 各 4 条

| XML 片段 | Python | 备注 |
|---|---|---|
| `checkMenuExistRole` | `check_menu_exist_role` | `count(1)`；`sys_menu` 删除前的校验 |
| `deleteRoleMenuByRoleId` | `delete_role_menu_by_role_id` | 单角色全删 |
| `deleteRoleMenu` | `delete_role_menu` | `<foreach>`；空数组 → `in ()` → MySQL 语法错 |
| `batchRoleMenu` | `batch_role_menu` | `executemany`；空列表返回 0 而**不**发语句 |
| `selectCountRoleDeptByDeptId` | `select_count_role_dept_by_dept_id` | `sys_dept` 删除前的校验 |
| `deleteRoleDeptByRoleId` | `delete_role_dept_by_role_id` | 单角色全删 |
| `deleteRoleDept` | `delete_role_dept` | `<foreach>` |
| `batchRoleDept` | `batch_role_dept` | `executemany` |

两处"空列表"的处理注意区别：

- `batch_role_menu` / `batch_role_dept`：**不发语句**返回 0（调用方已判 `size() > 0`，
  Java 里空列表是 SQL 语法错）；
- `delete_role_menu` / `delete_role_dept`：**照发** `in ()` 让 MySQL 报错 ——
  与 Java 一致，不额外保护（`deleteRoleByIds` 的调用方保证至少一个 id）。

---

## 5. Bean Validation：5 条约束

### 5.1 `SysRole` 的三个字段

```java
@NotBlank(message = "角色名称不能为空")
@Size(min = 0, max = 30, message = "角色名称长度不能超过30个字符")
public String getRoleName() { return roleName; }

@NotBlank(message = "权限字符不能为空")
@Size(min = 0, max = 100, message = "权限字符长度不能超过100个字符")
public String getRoleKey() { return roleKey; }

@NotBlank(message = "显示顺序不能为空")                       // 注意：没有 @Size
public String getRoleSort() { return roleSort; }
```

`dataScope` / `status` / `remark` / `menuIds` 上**没有任何注解**。

`ROLE_CONSTRAINTS` 按源码顺序排列（`role_name` NotBlank → `role_name` Size →
`role_key` NotBlank → `role_key` Size → `role_sort` NotBlank），因此"多字段同时违规"
时报的是第一条：空 body → `角色名称不能为空`；`{"roleName": <31 字>}` → 先报
`角色名称长度不能超过30个字符`（`role_name` 的 Size 排在 `role_key` 的 NotBlank 之前）。

### 5.2 校验写成 `Depends` 的原因

Spring 的真实顺序是：

```
安全过滤器链(401) -> 路由 -> 反序列化 + 校验(500) -> @PreAuthorize(403) -> 方法体
```

`ValidRole` 是 `Annotated[SysRole, Depends(_validated_role)]`，依赖在端点函数体之前解析，
正好补回 Spring 的位置。写成函数体第一行的话，"未登录 + 缺 roleName"会变成 403 而不是 500。

注意 `add` / `edit` 里 `edit` 多了个 `request: Request` 形参（要给 `token_service` 用），
FastAPI 会自动注入，不影响 `ValidRole` 的位置。

回归用例：`tests/test_sys_role_controller.py::TestValidationRunsBeforePermission`（11 条）。

---

## 6. 实体字段：只列容易被改错的

| Java | Python | 类型 | 说明 |
|---|---|---|---|
| `Long roleId` | `role_id` | `Optional[int]` | 主键，自增 |
| `String roleName` | `role_name` | `Optional[str]` | `@NotBlank` + `@Size(max=30)` |
| `String roleKey` | `role_key` | `Optional[str]` | `@NotBlank` + `@Size(max=100)`；可含逗号 |
| `String roleSort` | `role_sort` | `JavaString` | **varchar 列 + `String` 字段**，前端发数字要强转 |
| `String dataScope` | `data_scope` | `Optional[str]` | `1` 全部 / `2` 自定义 / `3` 本部门 / `4` 本部门及以下 |
| `boolean menuCheckStrictly` | `menu_check_strictly` | `bool = False` | **primitive**，永不为 `None` |
| `boolean deptCheckStrictly` | `dept_check_strictly` | `bool = False` | **primitive**，永不为 `None` |
| `String status` | `status` | `Optional[str]` | `0` 正常 / `1` 停用 |
| `String delFlag` | `del_flag` | `Optional[str]` | `0` 存在 / `2` 删除 |
| `boolean flag` | `flag` | `bool = False` | **primitive**，只用于查询，不落库 |
| `Long[] menuIds` | `menu_ids` | `Optional[List[int]]` | 不落库；`None` → 500，`[]` → 合法 |
| `Long[] deptIds` | `dept_ids` | `Optional[List[int]]` | 不落库，同上 |
| `boolean isAdmin()` | `admin`（计算属性） | `bool` | Jackson 输出 `"admin": false` |
| `static boolean isAdmin(Long)` | `SysRole.is_admin(role_id)` | `staticmethod` | 静态版 |

`menu_check_strictly` / `dept_check_strictly` / `flag` 声明为 `Optional[bool]` 是错的：
Java 是 primitive，Jackson **一定**输出 `false`（实测
`{"flag":false,"menuCheckStrictly":false}`），声明成 Optional 会多输出 `null`。

`admin` 与 `is_admin` 并存是因为 Python 里不能既定义同名实例属性又定义同名静态方法。

---

## 7. 逐行对照速查

```text
SysRoleController#list              -> sys_role_controller.list_roles          (GET    /system/role/list)
SysRoleController#export            -> (未迁移)                                 (GET    /system/role/export)
SysRoleController#getInfo           -> sys_role_controller.get_info            (GET    /system/role/{roleId})
SysRoleController#add               -> sys_role_controller.add                 (POST   /system/role)
SysRoleController#edit              -> sys_role_controller.edit                (PUT    /system/role)
SysRoleController#dataScope         -> sys_role_controller.data_scope          (PUT    /system/role/dataScope)
SysRoleController#changeStatus      -> sys_role_controller.change_status       (PUT    /system/role/changeStatus)
SysRoleController#remove            -> sys_role_controller.remove              (DELETE /system/role/{roleIds})
SysRoleController#optionselect      -> sys_role_controller.optionselect        (GET    /system/role/optionselect)
SysRoleController#selectlist        -> sys_role_controller.selectlist          (GET    /system/role/selectlist)

SysRoleServiceImpl#selectRolePermissionByUserId -> SysRoleService.select_role_permission_by_user_id
SysRoleServiceImpl#selectRoleList               -> SysRoleService.select_role_list
SysRoleServiceImpl#selectRoleAll                -> SysRoleService.select_role_all
SysRoleServiceImpl#selectRoleListByUserId       -> SysRoleService.select_role_list_by_user_id
SysRoleServiceImpl#selectRoleById               -> SysRoleService.select_role_by_id
SysRoleServiceImpl#selectRolesByUserName        -> SysRoleService.select_roles_by_user_name
SysRoleServiceImpl#checkRoleNameUnique          -> SysRoleService.check_role_name_unique
SysRoleServiceImpl#checkRoleKeyUnique           -> SysRoleService.check_role_key_unique
SysRoleServiceImpl#checkRoleAllowed             -> SysRoleService.check_role_allowed
SysRoleServiceImpl#countUserRoleByRoleId        -> SysRoleService.count_user_role_by_role_id
SysRoleServiceImpl#insertRole                   -> SysRoleService.insert_role
SysRoleServiceImpl#updateRole                   -> SysRoleService.update_role
SysRoleServiceImpl#updateRoleStatus             -> SysRoleService.update_role_status
SysRoleServiceImpl#authDataScope                -> SysRoleService.auth_data_scope
SysRoleServiceImpl#insertRoleMenu               -> SysRoleService.insert_role_menu
SysRoleServiceImpl#insertRoleDept               -> SysRoleService.insert_role_dept
SysRoleServiceImpl#deleteRoleById               -> SysRoleService.delete_role_by_id
SysRoleServiceImpl#deleteRoleByIds              -> SysRoleService.delete_role_by_ids

SysRoleMapper.xml#selectRoleList                  -> SysRoleMapper.select_role_list
SysRoleMapper.xml#selectRolePermissionByUserId    -> SysRoleMapper.select_role_permission_by_user_id
SysRoleMapper.xml#selectRoleAll                   -> SysRoleMapper.select_role_all
SysRoleMapper.xml#selectRoleListByUserId          -> SysRoleMapper.select_role_list_by_user_id
SysRoleMapper.xml#selectRoleById                  -> SysRoleMapper.select_role_by_id
SysRoleMapper.xml#selectRolesByUserName           -> SysRoleMapper.select_roles_by_user_name
SysRoleMapper.xml#checkRoleNameUnique             -> SysRoleMapper.check_role_name_unique
SysRoleMapper.xml#checkRoleKeyUnique              -> SysRoleMapper.check_role_key_unique
SysRoleMapper.xml#insertRole                      -> SysRoleMapper.insert_role
SysRoleMapper.xml#updateRole                      -> SysRoleMapper.update_role
SysRoleMapper.xml#deleteRoleById                  -> SysRoleMapper.delete_role_by_id
SysRoleMapper.xml#deleteRoleByIds                 -> SysRoleMapper.delete_role_by_ids

SysRoleMenuMapper.xml#checkMenuExistRole          -> SysRoleMenuMapper.check_menu_exist_role
SysRoleMenuMapper.xml#deleteRoleMenuByRoleId      -> SysRoleMenuMapper.delete_role_menu_by_role_id
SysRoleMenuMapper.xml#deleteRoleMenu              -> SysRoleMenuMapper.delete_role_menu
SysRoleMenuMapper.xml#batchRoleMenu               -> SysRoleMenuMapper.batch_role_menu

SysRoleDeptMapper.xml#selectCountRoleDeptByDeptId -> SysRoleDeptMapper.select_count_role_dept_by_dept_id
SysRoleDeptMapper.xml#deleteRoleDeptByRoleId      -> SysRoleDeptMapper.delete_role_dept_by_role_id
SysRoleDeptMapper.xml#deleteRoleDept              -> SysRoleDeptMapper.delete_role_dept
SysRoleDeptMapper.xml#batchRoleDept               -> SysRoleDeptMapper.batch_role_dept

SysUserRoleMapper.xml#countUserRoleByRoleIdUserId -> SysUserRoleMapper.count_user_role_by_role_id_user_id
```
