# MAPPING_SYS_USER.md — `sys_user` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §25。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectUserList` → `select_user_list`，`userName` → `user_name`。
  唯一的例外是 Java 里本来就是小写连写的字段（`phonenumber` / `bussid` 等）**保持原样**。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`IXxxService` + `XxxServiceImpl`）
  在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysUserController.java` | `app/api/system/sys_user_controller.py` | 19 个映射，已迁 16 个 |
| `ruoyi-system/.../service/ISysUserService.java`<br>`ruoyi-system/.../service/impl/SysUserServiceImpl.java` | `app/system/service/sys_user_service.py` | 接口 + 实现合并为 `SysUserService` |
| `ruoyi-system/.../mapper/SysUserMapper.java`<br>`ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml` | `app/system/mapper/sys_user_mapper.py` | 接口 + XML 合并：XML 的每条 statement 变成一个模块级 SQL 常量 |
| `ruoyi-system/.../mapper/SysUserRoleMapper.java` + XML | `app/system/mapper/sys_user_role_mapper.py` | 用到 4 条，见 §4.2 |
| `ruoyi-system/.../mapper/SysUserPostMapper.java` + XML | `app/system/mapper/sys_user_post_mapper.py` | 4 条全部迁完 |
| `ruoyi-common/.../core/domain/entity/SysUser.java` | `app/common/core/domain/entity/sys_user.py` | 40 个字段 |
| `ruoyi-common/.../core/domain/entity/SysDept.java` | `app/common/core/domain/entity/sys_dept.py` | `SysUser.dept` 的类型 |
| `ruoyi-common/.../core/domain/entity/SysRole.java` | `app/common/core/domain/entity/sys_role.py` | `SysUser.roles` 的元素类型 |
| `ruoyi-system/.../domain/SysPost.java` | `app/system/domain/sys_post.py` | 岗位下拉框 |
| `ruoyi-common/.../core/domain/BaseEntity.java` | `app/common/core/domain/base_entity.py` | `searchValue`/`createTime`/`params` ... |
| `ruoyi-common/.../constant/UserConstants.java` | `app/common/constant/user_constants.py` | `NOT_UNIQUE_OLD = "1"` 等 |
| `ruoyi-common/.../core/controller/BaseController.java` | `app/common/core/controller/base_controller.py` | `startPage` / `getDataTable` / `toAjax` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-framework/.../web/service/SysPermissionService.java`（`@ss.hasPermi`） | `app/framework/web/service/permission_service.py` | `@pre_authorize_permi("...")` |
| `ruoyi-framework/.../aspectj/DataScopeAspect.java` | `app/framework/aspectj/data_scope_aspect.py` | `apply_data_scope(user, "d", "u")` |
| `ruoyi-framework/.../aspectj/LogAspect.java` | **未迁移** | 因此不写 `sys_oper_log`，见 COMPATIBILITY §25.2 |
| `pagehelper-spring-boot-starter`（`PageHelper.startPage`） | `app/common/core/page/page_helper.py` | `start_page()` / `take_page()` / `select_page()` |
| `ruoyi-common/.../utils/SecurityUtils.java` | `app/common/utils/security_utils.py` | `get_username` / `get_user_id` / `get_tenant_id` / `get_eps_id` |
| `ruoyi-common/.../utils/ExcelUtil.java` | **未迁移** | 三个 Excel 端点因此不注册，见 COMPATIBILITY §25.1 |

### 1.3 测试

| 层 | Python 测试文件 | 用例数 |
|---|---|---|
| Mapper | `tests/test_sys_user_mapper.py` | SQL 文本 / 动态 `<if>` / 结果映射 |
| Service | `tests/test_sys_user_service.py` | 业务分支 / 异常 / 关联表写入顺序 |
| Controller | `tests/test_sys_user_controller.py` | 强制字段 / 文案 / 权限 / 路由表 |
| 端到端 | `tests/test_e2e_sys_user.py` | 28 条：登录 + JWT + CRUD |
| 序列化 | `tests/test_domain_serialization.py` | 字段名 / `@JsonIgnore` / `NumericDate` |

Java 侧 **没有任何 `src/test`**（`find` 结果为空），所以上表没有"Java 对应用例"列 ——
这些用例是照着 Java 源码逐行推导出来的，不是移植过来的。

---

## 2. 控制器：19 个映射逐条对照

前缀都是 `/system/user`。`权限` 列是 `@PreAuthorize("@ss.hasPermi(...)")` 的值；
写 `登录` 表示没有注解，只要求通过认证。

| # | Java 方法 | Python 函数 | HTTP + 路径 | 权限 |
|---|---|---|---|---|
| 1 | `list(SysUser)` | `list_users` | `GET /list` | 登录 |
| 2 | `listAll(SysUser)` | `list_all` | `GET /listAll` | 登录 |
| 3 | `listTenantIdAll(SysUser)` | `list_tenant_id_all` | `GET /listTenantIdAll` | 登录 |
| 4 | `listutil(SysUser)` | `list_util` | `GET /listutil` | 登录 |
| 5 | `listSameUtil(SysUser)` | `list_same_util` | `GET /listSameUtil` | 登录 |
| 6 | `listMy(SysUser)` | `list_my` | `GET /listMy` | 登录 |
| 7 | `export(SysUser)` | **未迁移** | `GET /export` | `system:user:export` |
| 8 | `importData(MultipartFile, boolean)` | **未迁移** | `POST /importData` | `system:user:import` |
| 9 | `importTemplate()` | **未迁移** | `GET /importTemplate` | 登录 |
| 10 | `getInfo(Long userId)` | `get_info` + `get_info_by_id` | `GET /` 与 `GET /{userId}` | `system:user:query` |
| 11 | `add(SysUser)` | `add` | `POST /` | `system:user:add` |
| 12 | `edit(SysUser)` | `edit` | `PUT /` | `system:user:edit` |
| 13 | `remove(Long[] userIds)` | `remove` | `DELETE /{userIds}` | `system:user:remove` |
| 14 | `resetPwd(SysUser)` | `reset_pwd` | `PUT /resetPwd` | `system:user:resetPwd` |
| 15 | `changeStatus(SysUser)` | `change_status` | `PUT /changeStatus` | `system:user:edit` |
| 16 | `bindUky(SysUser)` | `bind_uky` | `PUT /bindUky` | 登录 |
| 17 | `getroleUser(String roleCode)` | `getrole_user` | `GET /getroleUser/{roleCode}` | 登录 |
| 18 | `listByDept(SysUser)` | `list_by_dept` | `GET /list/dept` | 登录 |
| 19 | `selectCurrentUser()` | `select_current_user` | `GET /currentUser` | 登录 |

Java 用 `@GetMapping(value = {"/", "/{userId}"})` 一个方法吃两种 URL，
Python 的 FastAPI 做不到"可选路径参数"，所以拆成 `get_info` / `get_info_by_id` 两个函数
共用一个 `_get_info(user_id)`。**业务逻辑只写了一份。**

### 2.1 形参绑定的两套写法

| Java 形参 | Python | 说明 |
|---|---|---|
| `SysUser user`（无注解，如 `list`） | `user: UserParam` = `Annotated[SysUser, Depends(_query_user)]` | 从 query string 绑定，规则见 `base_controller.bind_query_params` |
| `@RequestBody SysUser user`（如 `add`） | `user: SysUser` | FastAPI 从 JSON body 解析 |
| `@PathVariable Long[] userIds` | `user_ids: str` + `_parse_id_array` | 按逗号切分再转 `int` |
| `@PathVariable String roleCode` | `role_code: str` | 同名同义 |
| `MultipartFile file` | **未迁移** | 无 PoI 等价物 |

`add` / `edit` / `resetPwd` / `changeStatus` 四个 `@RequestBody` 端点都挂了
`@pre_authorize_permi(...)`。这个装饰器必须保留被装饰函数的 `__signature__`，
否则 FastAPI 会把 `user` 误判成 query 参数 —— 事故经过见 COMPATIBILITY §25.4。

---

## 3. 服务层：`ISysUserService` / `SysUserServiceImpl`

Python 只有一个 `SysUserService` 类（接口与实现合并）。所有方法都带 `# Java:` 行注释。

| Java 方法 | Python 方法 | 备注 |
|---|---|---|
| `selectUserList(SysUser)` | `select_user_list` | 方法体第一行 `apply_data_scope(user, "d", "u")` 代替 `@DataScope` |
| `selectUserByUserName(String)` | `select_user_by_user_name` | 直通 mapper，不 trim、不判空 |
| `selectUserByCertEntityID(String)` | `select_user_by_cert_entity_id` | 同上 |
| `selectUserById(Long)` | `select_user_by_id` | 同上 |
| `selectUserRoleGroup(String)` | `select_user_role_group` | 逗号分隔的**角色名**，`null` 拼成 `"null"` |
| `selectUserPostGroup(String)` | `select_user_post_group` | 逗号分隔的**岗位名** |
| `checkUserNameUnique(String)` | `check_user_name_unique` | 返回 `"0"` / `"1"` 字符串，不是 bool |
| `checkPhoneUnique(SysUser)` | `check_phone_unique` | `userId` 为 null 时按 `-1` 比较 |
| `checkEmailUnique(SysUser)` | `check_email_unique` | 同上 |
| `checkUserAllowed(SysUser)` | `check_user_allowed` | 超管抛 `CustomException` |
| `insertUser(SysUser)` | `insert_user` | 先写主表再写两张关联表 |
| `updateUser(SysUser)` | `update_user` | 先删关联再重建（**不是**原子操作，Java 也不是） |
| `updateUserInfoByBussId(SysUser)` | `update_user_info_by_buss_id` | 直通 mapper |
| `updateUserStatus(SysUser)` | `update_user_status` | 实际调 `updateUser`，**不是** XML 里的 `updateUserStatus` |
| `updateUserProfile(SysUser)` | `update_user_profile` | 实际调 `updateUser` |
| `updateUserAvatar(String, String)` | `update_user_avatar` | 返回值 `> 0` 折成 bool |
| `resetPwd(SysUser)` | `reset_pwd` | 实际调 `updateUser` |
| `resetUserPwd(String, String)` | `reset_user_pwd` | 直通 `resetUserPwd` statement |
| `deleteUserById(Long)` | `delete_user_by_id` | 软删除：`del_flag = '1'` |
| `deleteUserByIds(Long[])` | `delete_user_by_ids` | 逐个 `checkUserAllowed` |
| `insertUserRole(SysUser)` | `insert_user_role` | 实现类上的 public 方法，接口里没有 |
| `insertUserPost(SysUser)` | `insert_user_post` | 同上 |
| `updateUserPwd(SysUser)` | `update_user_pwd` | 短信验证码找回 → 重置为**默认密码** |
| `forgotPassword(SysUser)` | `forgot_password` | 重置为**请求里的新密码**，且对验证码大小写不敏感 |
| `selectCurrentUser()` | `select_current_user` | 返回只有 4 个字段的瘦对象 |
| `selectPwdJudge(Long)` | `select_pwd_judge` | 只带 `pjFlag` |
| `updateUserInfoByBussIdAndUserType(SysUser)` | `update_user_info_by_buss_id_and_user_type` | Java 是 `void`，Python 返回 `None` |
| `importUser(List, Boolean, String)` | **未迁移** | 依赖 `sys_config` 的 `sys.user.initPassword` |

### 3.1 依赖注入

| Java | Python |
|---|---|
| `@Autowired private ISysUserMapper userMapper` 等字段 | `@property def mapper(self)` 惰性构造，见 `SysUserService.__init__` |
| Spring 单例 | `get_user_service()` 模块级缓存 + `reset_user_service()` 供测试替换 |
| `@Autowired private ISysUserService userService`（控制器侧） | `_user_service()` + `reset_user_controller()` |

这样测试里可以直接 `monkeypatch.setattr(service, "_mapper", fake)`，等价于
`@MockBean` / `ReflectionTestUtils`。

---

## 4. Mapper 层

### 4.1 `SysUserMapper`

XML 共 23 条 statement：已迁 21 条，剩下 2 条（`getSendUserInfosByEpsId` / `selectByRoleKey`）
属于招投标与消息模块，返回 `UserRoleModel`，不在本切片。
接口里声明了 19 个方法，而已迁的 statement 有 21 条 —— 差的 2 条（`updateUserStatus`、
`updateUserInfoByBussIdAndUserType`）在 XML 里有、接口里**没有声明**：
前者在 Java 里没有任何调用者（死语句），后者由实现类直接调用。Python 两条都保留了。

| Java 方法 | Python 方法 | XML statement id / SQL 常量 |
|---|---|---|
| `selectUserList(SysUser)` | `select_user_list` | `selectUserList` / `_SELECT_USER_LIST` + `_build_user_list_sql` |
| `selectUserByUserName(String)` | `select_user_by_user_name` | `selectUserByUserName` / `_SELECT_USER_BY_USER_NAME` |
| `selectUserByCertEntityID(String)` | `select_user_by_cert_entity_id` | `selectUserByCertEntityID` / `_SELECT_USER_BY_CERT_ENTITY_ID` |
| `selectUserById(Long)` | `select_user_by_id` | `selectUserById` / `_SELECT_USER_BY_ID` |
| `checkUserNameUnique(String)` | `check_user_name_unique` | `checkUserNameUnique` / `_CHECK_USER_NAME_UNIQUE` |
| `checkPhoneUnique(String)` | `check_phone_unique` | `checkPhoneUnique` / `_CHECK_PHONE_UNIQUE` |
| `checkEmailUnique(String)` | `check_email_unique` | `checkEmailUnique` / `_CHECK_EMAIL_UNIQUE` |
| `insertUser(SysUser)` | `insert_user` | `insertUser` / `_INSERT_USER_HEAD`（列与值动态拼，`useGeneratedKeys` → `user.user_id` 回填） |
| `updateUser(SysUser)` | `update_user` | `updateUser` / `_UPDATE_USER_HEAD` + `_build_update_sql` |
| `updateUserInfoByBussId(SysUser)` | `update_user_info_by_buss_id` | `updateUserInfoByBussId` / `_UPDATE_USER_INFO_BY_BUSS_ID_HEAD` |
| （无接口声明） | `update_user_info_by_buss_id_and_user_type` | `updateUserInfoByBussIdAndUserType` / `_UPDATE_USER_INFO_BY_BUSS_ID_AND_USER_TYPE_HEAD` |
| （无接口声明，死语句） | `update_user_status` | `updateUserStatus` / `_UPDATE_USER_STATUS` |
| `updateUserPwd(String, String, String)` | `update_user_pwd` | `updateUserPwd` / `_UPDATE_USER_PWD` |
| `updateUserAvatar(String, String)` | `update_user_avatar` | `updateUserAvatar` / `_UPDATE_USER_AVATAR` |
| `resetUserPwd(String, String)` | `reset_user_pwd` | `resetUserPwd` / `_RESET_USER_PWD` |
| `deleteUserById(Long)` | `delete_user_by_id` | `deleteUserById` / `_DELETE_USER_BY_ID` |
| `deleteUserByIds(Long[])` | `delete_user_by_ids` | `deleteUserByIds` / 动态 `in (...)`，见 `_in_clause` |
| `deleteUserByBussId(String)` | `delete_user_by_buss_id` | `deleteUserByBussId` / `_DELETE_USER_BY_BUSS_ID` |
| `deleteUserByBussIds(String[])` | `delete_user_by_buss_ids` | `deleteUserByBussIds` / 动态 `in (...)` |
| `existsByBussId(SysUser)` | `exists_by_buss_id` | `existsByBussId` / 动态拼接（判据是 `buss_id !=`，不是 `=`） |
| `selectPwdJudge(Long)` | `select_pwd_judge` | `selectPwdJudge` / `_SELECT_PWD_JUDGE` |

### 4.2 `SysUserRoleMapper` / `SysUserPostMapper`

| Java 方法 | Python 方法 | 备注 |
|---|---|---|
| `deleteUserRoleByUserId(Long)` | `delete_user_role_by_user_id` | |
| `deleteUserRole(Long[])` | `delete_user_role` | 注意参数是 **userIds**，与 `deleteUserRoleInfos` 不同 |
| `batchUserRole(List)` | `batch_user_role` | 单条 `insert ... values (...),(...),...` |
| `countUserRoleByRoleId(Long)` | `count_user_role_by_role_id` | 角色模块用 |
| `deleteUserRoleInfo(SysUserRole)` | **未迁移** | 随角色模块 |
| `deleteUserRoleInfos(Long, Long[])` | **未迁移** | 随角色模块 |
| `countUserRoleByRoleIdUserId(Long, Long)` | **未迁移** | 随角色模块 |
| `deleteUserPostByUserId(Long)` | `delete_user_post_by_user_id` | |
| `deleteUserPost(Long[])` | `delete_user_post` | |
| `batchUserPost(List)` | `batch_user_post` | |
| `countUserPostById(Long)` | `count_user_post_by_id` | 岗位模块用（删除岗位前校验） |

### 4.3 结果映射：`resultMap` ↔ 手写合并

Java 靠 MyBatis 的 `resultMap` 自动做两件事，Python 里必须手写，这是最容易出错的地方。

| Java (`SysUserMapper.xml`) | Python | 触发它的 statement |
|---|---|---|
| `<sql id="selectUserVo">` | `SELECT_USER_VO` / `_SELECT_USER_VO` | `selectUserByUserName` / `selectUserByCertEntityID` / `selectUserById` |
| `<resultMap id="SysUserResult">` 的 `<id property="userId">` | 无需处理（SQL 已去重） | — |
| `<association property="dept" resultMap="deptResult">` | `_map_user` 里构造 6 字段的 `SysDept` | 同上 |
| `<collection property="roles" resultMap="RoleResult">` | `_map_user` 里按 `role_id` 去重（等价于 `<id>` 合并 3 行） | 同上 |
| `selectUserList` 的结果映射（`d.dept_name` / `d.leader`） | `_map_user_list_row` | `selectUserList` |

为什么 `selectUserList` 要用另一个 mapper 函数：它**根本 select 角色列**，
所以 `roles` 恒为 `[]`；混用 `_map_user` 会在 `values["role_id"]` 上 `KeyError`。

### 4.4 分页

| Java | Python |
|---|---|
| `BaseController.startPage()` → `PageUtils.startPage()` → `PageHelper.startPage(...)` | `start_page()` |
| PageHelper 拦截器（在 SQL 执行时生效） | `SysUserMapper.select_user_list` 内部 `take_page()` + `select_page(...)` |
| `select count(0) from ( 原SQL ) table_count` | `select_page` 的第一个参数 `count_sql` |
| `Page<E>` 的 `total` / `pageNum` / `pageSize` | `PageList` 的同名属性 |
| `TableDataInfo` 的 `code`/`msg`/`rows`/`total` | `get_data_table(rows)` |

---

## 5. 实体字段：只列容易被改错的

完整字段表在 `app/common/core/domain/entity/sys_user.py` 里逐字段注释。
下面这些是"看起来该改、实际不能改"的：

| Java 字段 | JSON key | Python 属性 | 注意 |
|---|---|---|---|
| `private String userName` | `userName` | `user_name` | 大写 `N` |
| `private String phonenumber` | **`phonenumber`** | `phonenumber` | 不是 `phoneNumber`；RuoYi 的历史拼写 |
| `private String password` | （不输出） | `password` | getter 上 `@JsonIgnore` + `@JsonProperty` = 只写 |
| （无字段）`public boolean isAdmin()` | `admin` | `admin`（`computed_field`） | 虚拟属性，必须出现在每个响应里 |
| `private Date loginDate` | `loginDate` | `login_date` | **没有** `@JsonFormat` → 序列化为毫秒数字 |
| `private Date createTime` | `createTime` | `create_time` | 有 `@JsonFormat` → 字符串 `yyyy-MM-dd HH:mm:ss`（UTC） |
| `private int pjFlag` | `pjFlag` | `pj_flag: int = 0` | 基本类型：永远不为 null |
| `private String bussId` | `bussId` | `buss_id` | SQL 里是 `ifnull(u.buss_id, u.user_name)` |
| `private SysDept dept` | `dept` | `dept: Optional[SysDept]` | 只有关联查询才填 |
| `private List<SysRole> roles` | `roles` | `roles: Optional[List[SysRole]]` | `selectUserList` 里恒为 `[]` |
| `private Long[] roleIds` / `postIds` | `roleIds` / `postIds` | `role_ids` / `post_ids` | 表单提交的 id 数组 |
| `BaseEntity.params` | `params` | `params` | `@JsonInclude(NON_EMPTY)`：空 dict 不输出 |

`SysDept` / `SysRole` / `SysPost` 的排序列（`orderNum` / `roleSort` / `postSort`）
在库里是 `varchar`、在 Java 里是 `String`，前端却用数字控件提交。
Python 用 `JavaString` 类型接受数字并转成字符串，规则见 COMPATIBILITY §25.5。

---

## 6. 注解 ↔ 装饰器 / 显式调用

| Java 注解 | Python | 说明 |
|---|---|---|
| `@RestController` / `@RequestMapping("/system/user")` | `APIRouter(prefix="/system/user")` | 在 `app/main.py` 里 `include_router` |
| `@GetMapping` / `@PostMapping` / ... | `@router.get` / `@router.post` / ... | 必须带 `response_model=None`（返回的是 `AjaxResult` dict 子类） |
| `@PreAuthorize("@ss.hasPermi('x')")` | `@pre_authorize_permi("x")` | 装饰器顺序：**路由装饰器在上，权限装饰器在下** |
| `@DataScope(deptAlias="d", userAlias="u")` | `apply_data_scope(user, "d", "u")` | 方法体第一行，不是装饰器 |
| `@Log(title=..., businessType=...)` | **无** | `LogAspect` 未迁移 |
| `@Validated` | **无** | `SysUser` 上的 `@NotBlank`/`@Size`/`@Email` 在 Java 里全被注释掉了，校验只剩手写分支 |
| `@RequestBody` | 类型注解即隐式 body | FastAPI 的默认行为 |
| `@PathVariable` | 路径模板 `{user_id}` | — |
| `@Autowired` | `@property` + 模块级 `get_xxx()` 缓存 | 见 §3.1 |

---

## 7. 一句话总结

- **找代码**：Java 的 `XxxController` → `app/api/**/xxx_controller.py`；
  `XxxServiceImpl` → `app/system/service/xxx_service.py`；
  `XxxMapper.xml` → `app/system/mapper/xxx_mapper.py` 里的 `_UPPER_SNAKE` 常量。
- **找差异**：COMPATIBILITY.md §25（本切片）、§2&3（HTTP 状态码约定，最容易踩）。
- **找测试**：`tests/test_{mapper,service,controller,e2e}_*.py`，Java 侧没有对应物。
