# MAPPING_SYS_PROFILE.md — `sys_profile` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §30。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `updateProfile` → `update_profile`，`getPathFileName` → `get_path_file_name`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysUserService` + `SysUserServiceImpl`）
  在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。
- **本切片是本阶段唯一一个"要用新基础设施"的切片**：文件上传（`FileUploadUtils` /
  `MimeTypeUtils` / `Seq` / 文件异常族）此前从未迁移过，这次一并落地（§1.2 的 4 个新文件）。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysProfileController.java` | `app/api/system/sys_profile_controller.py` | **新建**；**4 个映射，全部迁移** |
| `ruoyi-system/.../service/ISysUserService.java`<br>`ruoyi-system/.../service/impl/SysUserServiceImpl.java` | `app/system/service/sys_user_service.py` | Phase 3.5 已存在，本切片**未改动**；用到其中 7 个方法（§3） |
| `ruoyi-system/.../mapper/SysUserMapper.java`（`updateUser` / `updateUserAvatar` / `resetUserPwd`） | `app/system/mapper/sys_user_mapper.py` | 未改动；`updateUserProfile` 直接复用 `updateUser` 的 SQL |
| `ruoyi-system/.../mapper/SysRoleMapper.java`（`selectRolesByUserName`） | `app/system/mapper/sys_role_mapper.py` | `roleGroup` 的来源（角色**名称**串） |
| `ruoyi-system/.../mapper/SysPostMapper.java`（`selectPostsByUserName`） | `app/system/mapper/sys_post_mapper.py` | `postGroup` 的来源（岗位**名称**串） |
| `ruoyi-common/.../core/domain/entity/SysUser.java` | `app/common/core/domain/entity/sys_user.py` | 已存在；`password` 是 write-only（§6） |
| `ruoyi-common/.../core/domain/model/LoginUser.java` | `app/common/core/domain/model/login_user.py` | `getUsername()` / `getPassword()` → 同名 snake_case |
| `ruoyi-common/.../core/domain/AjaxResult.java` | `app/common/core/domain/ajax_result.py` | `success(user)` → `success_data(user)`；`put` → `put_chain` |
| `ruoyi-common/.../core/controller/BaseController.java` | `app/common/core/controller/base_controller.py` | Java 里 `extends BaseController`，但**一个 helper 都没用** —— 本切片不调用 `to_ajax` / `start_page` |
| `ruoyi-common/.../config/RuoYiConfig.java`（`getAvatarPath` 等 4 个） | `app/settings.py` 的 `RuoYiSection` | **改动**：补了 `import_path` / `avatar_path` / `download_path` / `upload_path` 四个 property |
| `ruoyi-common/.../constant/Constants.java`（`RESOURCE_PREFIX`） | `app/common/constant/constants.py` | 已存在；`"/profile"` |
| `ruoyi-common/.../constant/UserConstants.java` | `app/common/constant/user_constants.py` | 只用 `NOT_UNIQUE_OLD` |
| `ruoyi-admin/.../web/util/CommonUtil.java`（`checkPassword`） | `app/api/util/common_util.py` | 已存在；**返回 `True` 表示"不合法"** |

### 1.2 本切片新建的基础设施（4 个新文件 + 1 处改动）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-common/.../utils/file/FileUploadUtils.java` | `app/common/utils/file_upload_utils.py` | **新建**；3 个 `upload` 重载 → `upload_default` / `upload` / `upload_with_extensions`（§4） |
| `ruoyi-common/.../utils/file/MimeTypeUtils.java` | `app/common/utils/mime_type_utils.py` | **新建**；5 个图片前缀 + 5 个白名单常量（§5.2） |
| `ruoyi-common/.../utils/uuid/Seq.java` | `app/common/utils/seq.py` | **新建**；独立成模块，不与 `uuid_utils` 合并（§5.1） |
| `ruoyi-common/.../exception/file/FileException.java`<br>`.../exception/file/FileUploadException.java`<br>`.../exception/file/FileSizeLimitExceededException.java`<br>`.../exception/file/FileNameLengthLimitExceededException.java`<br>`.../exception/file/InvalidExtensionException.java` | `app/common/exception/file/__init__.py` | **新建**；5 个类 + 4 个 `static` 内部类，压平成一个模块（§4.3） |
| `ruoyi-common/.../config/RuoYiConfig.java` | `app/settings.py` | **改动**：`RuoYiSection` 补 4 个 property，对应 Java 的 4 个静态 getter |
| `org.apache.commons.io.FilenameUtils`（`getBaseName` / `getExtension`） | `file_upload_utils._get_base_name` / `_get_extension_of` 等私有函数 | **不引入 commons-io 依赖**，只搬被用到的那几个分支 |
| `ruoyi-common/.../utils/MessageUtils.java` + `i18n/messages.properties` | `app/common/utils/message_utils.py` + `config/i18n/messages.properties` | 已存在；两条 `upload.*` 文案原样留在 properties 里 |
| `org.springframework.web.multipart.MultipartFile` | `starlette.datastructures.UploadFile` | `getSize()` → `size_of()`（`UploadFile.size` 可能为 `None`，见 §30.6） |
| `ruoyi-common/.../utils/ServletUtils.java`（`getRequest`） | FastAPI 的 `Request` 依赖 | 无同名包装 |

### 1.3 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-framework/.../web/service/TokenService.java` | `app/framework/web/service/token_service.py` | `getLoginUser(request)` / `setLoginUser(...)`；**后者顺带刷新 TTL** |
| `ruoyi-common/.../utils/SecurityUtils.java` | `app/common/utils/security_utils.py` | `getUsername()` / `getPassword()` / `matchesPassword` / `encryptPassword` |
| `ruoyi-common/.../utils/StringUtils.java`（`isNotEmpty`） | `app/common/utils/string_utils.py` | `is_not_empty`（**不 trim**） |
| `ruoyi-framework/.../aspectj/LogAspect.java` | **未迁移** | 因此不写 `sys_oper_log`，见 §30.1 |
| `@RequestBody SysUser user` | 函数形参 `user: SysUser` | FastAPI 自动按 JSON body 解析 |
| `HttpServletRequest#getParameter` | `_request_parameters`（`async` 依赖） | query 优先 + form body，同名取第一个（§2.3） |
| `@RequestParam("avatarfile") MultipartFile` | `Annotated[UploadFile, File()]` | 部件名必须叫 `avatarfile` |
| `@RequestAttribute` / `SecurityContextHolder` | **本控制器完全不用** | 只走 `TokenService`（§2.4） |

### 1.4 测试

| 层 | Python 测试文件 | 函数数 → 用例数 | 覆盖点 |
|---|---|---|---|
| 工具 | `tests/test_file_upload_utils.py` | 31 → **39** | `Seq` 形状与循环边界 / `MimeTypeUtils` 5 前缀与白名单顺序 / Commons-IO 的 baseName 表 / 大小与后缀两道闸 / `is` 引用比较 / 落盘与异常包装 |
| Controller | `tests/test_sys_profile_controller.py` | 34 → **34** | 路由表（4 条 + 顺序 + 无权限点）/ `profile` 键序与缓存来源 / `updateProfile` 两道闸与 4 字段回写 / `updatePwd` 三分支**顺序** / `avatar` 空文件短路与落盘 url |

合计 **73** 条；全量套件 **1273 passed**（Phase 3.10 结束时是 1200）。

Java 侧 **没有任何 `src/test`**，所以上表没有"Java 对应用例"列 ——
这些用例是照着 Java 源码逐行推导出来的，不是移植过来的。

---

## 2. 控制器：4 个映射逐条对照

前缀是 `/system/user/profile`。`Access` 列写**登录**，因为**四个方法一个 `@PreAuthorize` 都没有**。

| # | Java 方法 | Python 函数 | HTTP + 路径 | Access |
|---|---|---|---|---|
| 1 | `profile()` | `profile(request)` | `GET /system/user/profile` | 登录 |
| 2 | `updateProfile(@RequestBody SysUser)` | `update_profile(request, user)` | `PUT /system/user/profile` | 登录 |
| 3 | `updatePwd(String oldPassword, String newPassword)` | `update_pwd(request, parameters)` | `PUT /system/user/profile/updatePwd` | 登录 |
| 4 | `avatar(@RequestParam("avatarfile") MultipartFile)` | `avatar(request, avatarfile)` | `POST /system/user/profile/avatar` | 登录 |

### 2.1 四个端点**都没有**权限点（安全相关）

```java
@GetMapping
public AjaxResult profile()                      // 无 @PreAuthorize
@PutMapping
public AjaxResult updateProfile(SysUser user)    // 无
@PutMapping("/updatePwd")
public AjaxResult updatePwd(...)                 // 无
@PostMapping("/avatar")
public AjaxResult avatar(MultipartFile file)     // 无
```

改自己的资料不应该要求"用户管理"权限。它们能被调用是因为
`SecurityConfig` 的 `anyRequest().authenticated()`；未登录仍然是安全过滤器给的 401。

Python 侧四个函数上**没有** `@pre_authorize_permi`。
`tests/test_sys_profile_controller.py::TestRouteTable::test_no_endpoint_carries_a_permission_point`
是这条的回归阀（逐个检查 `route.dependant.dependencies` 里没有 `pre_authorize_permi`）。

### 2.2 路由注册顺序（本切片唯一的坑）

`SysUserController` 有一条 `GET /system/user/{userId}`。FastAPI 与 Spring 一样按
**注册顺序**匹配（Spring 的 `PathPattern` 更聪明，会优先匹配字面量；FastAPI 不会），
所以 `sys_profile_router` 必须在 `sys_user_router` **之前** `include_router`：

```python
# app/main.py
application.include_router(sys_login_router)
application.include_router(sys_profile_router)   # 必须在 sys_user_router 之前
application.include_router(sys_user_router)      # GET /system/user/{user_id}
```

放在后面的话，`GET /system/user/profile` 会先命中 `/{user_id}`，在 `int` 转换处炸掉
（**HTTP 422 + 校验错误体**，而不是 Java 的 200）。

回归用例：`TestRouteTable::test_the_profile_router_is_registered_before_the_user_router`
（对 `create_app().routes` 做下标比较）。

### 2.3 形参绑定：`updatePwd` 用 `getParameter`，其余三个各走各的

| Java 形参 | 绑定来源 | Python |
|---|---|---|
| 无（`profile`） | —— | `request: Request`（只为拿令牌） |
| `@RequestBody SysUser user` | JSON body | `user: SysUser` |
| `String oldPassword, String newPassword`（**无注解**） | `HttpServletRequest#getParameter` | `parameters: RequestParameters` |
| `@RequestParam("avatarfile") MultipartFile file` | multipart 部件 | `avatarfile: Annotated[UploadFile, File()]` |

`getParameter` 的语义是三句话：**query string 与 form body 聚合成一个 Map**、
**query string 排在前面**、**同名只取第一个值**。FastAPI 的 `Query` 只读 query、
`Form` 只读 body，任何一个单独用都覆盖不了这两种来源，所以 `updatePwd` 用
`_request_parameters`（`async` 依赖 + `setdefault`）复刻它。

回归用例：`TestUpdatePwd::test_the_two_passwords_are_read_from_the_query_string`
（`params=`）与 `test_the_two_passwords_are_also_read_from_a_form_body`（`data=`）。

### 2.4 登录用户从哪儿拿

```java
LoginUser loginUser = tokenService.getLoginUser(ServletUtils.getRequest());
```

**不读** `SecurityContextHolder`。这是本控制器与 `SysUser` / `SysMenu` 等控制器最大的
结构差异：那几处用 `BaseController#getUserId()`（= 上下文），这里用令牌。

`getLoginUser` 在令牌过期时返回 `null`，随后 `loginUser.getUser()` NPE。Python 侧
`_current_login_user` **不兜底**，`None.user` 抛 `AttributeError`，落在同一个
`Exception` 兜底处理器上（HTTP 200 + `code 500`）。

回归用例：`TestProfile::test_the_login_user_comes_from_the_token_service`
（换掉 token 里的人 → 返回的 `data` 跟着变）与 `test_a_null_login_user_is_not_guarded`。

### 2.5 三个"短路"位置（顺序即行为）

| 端点 | 短路点 | 短路后**不做**什么 |
|---|---|---|
| `updateProfile` | 手机号重复 → return | 不查邮箱、不写库、不回写缓存 |
| `updateProfile` | 邮箱重复 → return | 不写库、不回写缓存 |
| `updatePwd` | 旧密码不匹配 → return | 不比对"新旧相同"、不校验复杂度、不写库 |
| `updatePwd` | 新旧相同 → return | 不校验复杂度、不写库 |
| `avatar` | 0 字节 → 落到末尾失败分支 | **不动磁盘**、不更新数据库、不回写缓存 |

`updatePwd` 的三段顺序在 Java 里是 旧密码 → 新旧相同 → 复杂度，
所以"旧密码错 + 新密码太弱"回的是 `修改密码失败，旧密码错误`。
Python 的三条 `if` 顺序与之逐字对齐，`TestUpdatePwd` 有 10 个用例专盯这个顺序。

---

## 3. 服务层：用到 `ISysUserService` 的 7 个方法

Phase 3.5 已经迁移过，本切片**一行没改**。列在这里只是为了把"控制器这一层看得到的行为"
和 SQL 对上。

| Java | Python | 返回 | 底层 SQL |
|---|---|---|---|
| `String selectUserRoleGroup(String userName)` | `select_user_role_group` | 逗号分隔的**角色名称** | `SysRoleMapper.selectRolesByUserName` |
| `String selectUserPostGroup(String userName)` | `select_user_post_group` | 逗号分隔的**岗位名称** | `SysPostMapper.selectPostsByUserName` |
| `String checkPhoneUnique(SysUser user)` | `check_phone_unique` | `"0"` 唯一 / `"1"` 已存在 | Service 自己比对 `user_id`（`null` → `-1`），SQL 只管查 |
| `String checkEmailUnique(SysUser user)` | `check_email_unique` | 同上 | 同上 |
| `int updateUserProfile(SysUser user)` | `update_user_profile` | 影响行数 | **就是 `updateUser`** —— 见下 |
| `boolean updateUserAvatar(String userName, String avatar)` | `update_user_avatar` | `> 0` 即成功 | `update sys_user set avatar = ? where user_name = ?` |
| `int resetUserPwd(String userName, String password)` | `reset_user_pwd` | 影响行数 | `update sys_user set password = ? where user_name = ?` |

### 3.1 `updateUserProfile` 就是 `updateUser`

```java
public int updateUserProfile(SysUser user) { return userMapper.updateUser(user); }
```

所以 `PUT /system/user/profile` 与 `PUT /system/user` 走**同一条** SQL。
控制器的"只改 4 个字段"不是靠 SQL 收窄的，而是靠 `<if test="xxx != null">`：
body 里没送的字段是 `null` → 整列跳过。**送空串会清列**（与 `updateUser` 完全同源，
见 COMPATIBILITY §25）。

控制器只把这 4 个字段回写到缓存（`nick_name` / `phonenumber` / `email` / `sex`），
因为 `updateUserProfile` 的语义就是"用户能自助改的只有这 4 个"——
body 里哪怕带了 `status`，缓存也不会跟着变（数据库却会变）。这是 Java 原样。

### 3.2 `checkPhoneUnique` / `checkEmailUnique` 会排除自己

```xml
<select id="checkPhoneUnique" ...>
    select user_id, phonenumber from sys_user
    where phonenumber = #{phonenumber} and del_flag = '0' limit 1
</select>
```

SQL 只管查，**排除自己是在 Service 里做的**：

```java
Long userId = StringUtils.isNull(user.getUserId()) ? -1L : user.getUserId();
if (StringUtils.isNotNull(info) && info.getUserId().longValue() != userId.longValue()) {
    return UserConstants.NOT_UNIQUE_OLD;
}
```

所以"不改手机号直接保存"不会被拦（查到的是自己，`user_id` 相等）。
`user.getUserId()` 为空时用 `-1L` 哨兵，永远不会等于真实 id ——
换句话说**body 里不送 `userId`、而手机号又已经被占用时，会回"已存在"**，
清除手机号/邮箱才是唯一不加 `userId` 也能过的情况（因为空值不查重）。
Python 侧逐字照抄（`user_id = -1 if user.user_id is None else user.user_id`）。

**副作用**：body 里 `userName` 为空时，`sys_user.user_name` 不参与这条 SQL，
但控制器用 `user.getUserName()` 拼**提示文案** —— 空 `userName` 会得到
`修改用户''失败，手机号码已存在`。Java 也是这个输出。

---

## 4. `FileUploadUtils` 逐方法

### 4.1 三个 `upload` 重载 → 三个函数名

Java 用重载，Python 用不同名字（同名函数在 Python 里只能有一个签名）：

| Java | Python | 说明 |
|---|---|---|
| `upload(MultipartFile file)` | `upload_default(file)` | 基目录回退到 `getDefaultBaseDir()` |
| `upload(String baseDir, MultipartFile file)` | `upload(base_dir, file)` | **接住一切异常并包成 `OSError`**（Java 的 `IOException`） |
| `upload(String baseDir, MultipartFile file, String[] allowedExtension)` | `upload_with_extensions(...)` | 原样抛出 `FileException` 族 |

`avatar` 用的是**2 参**版本，所以客户端看到的永远是"HTTP 200 + `code 500` + 原始文案"
（异常被包成 `OSError` 后由 `Exception` 兜底处理器接住），而不是某个专门的错误码。

### 4.2 校验链的四道闸（顺序不能换）

`upload_with_extensions` 的体就是 Java 的体：

| # | 判断 | 失败抛什么 | 客户端看到 |
|---|---|---|---|
| 1 | `len(file.filename) > 100` | `FileNameLengthLimitExceededException` | `上传的文件名最长100个字符`（i18n） |
| 2 | `getSize() > 50 * 1024 * 1024` | `FileSizeLimitExceededException` | `上传的文件大小超出限制的文件大小！<br/>允许的文件最大大小是：50MB！` |
| 3 | 后缀不在白名单 | `InvalidExtensionException`（或 4 个子类之一） | `文件[a.exe]后缀[exe]不正确，请上传[...]格式` |
| 4 | 落盘 | `OSError`（Java `IOException`） | 底层 message |

**1 在 2 之前**：文件名超长但大小也超限时，回的是"文件名太长"。这是 Java 的顺序，
`TestUpload::test_a_refused_extension_leaves_nothing_on_disk` 顺带证明了三道闸都在
`extract_filename`/`_transfer_to` **之前**（被拒时连日期目录都不会被创建）。

### 4.3 异常族的两个来源（不能合并）

Java 里这一族分两支，`catch` 的语义完全不同：

| Java | 父类 | Python 父类 | 走哪条路 |
|---|---|---|---|
| `FileException` | `BaseException`（RuoYi 的，`RuntimeException`） | `RuoYiBaseException(RuntimeError)` | `RuntimeError` 处理器 |
| `FileSizeLimitExceededException` / `FileNameLengthLimitExceededException` | `FileException` | 同上 | `RuntimeError` 处理器 |
| `FileUploadException` | `Exception`（**checked**） | `Exception` | 若逃出 2 参 `upload` 就是 `Exception` 兜底处理器 |
| `InvalidExtensionException` + 4 个 `static` 内部类 | `FileUploadException` | `InvalidExtensionException` + 4 个模块级类 | 同上 |

两条路的客户端结果**都是** HTTP 200 + `code 500` + 同一句文案，但类型不能混：
把 `FileException` 也做成 `Exception` 的子类会让"运行时异常"这一层语义消失
（`RuntimeError` 处理器里还有别的判断，见 §25.3）。

4 个 `static` 内部类在 Python 里先是**模块级类**，再挂回父类：

```python
InvalidExtensionException.InvalidImageExtensionException = InvalidImageExtensionException
```

原因是 Python 的类体里引不到"正在定义的类"。挂回去之后 `InvalidExtensionException.InvalidImageExtensionException`
这个 Java 访问路径仍然可用。

### 4.4 `getPathFileName`：数据库里存的是**相对 url**

```java
int dirLastIndex = RuoYiConfig.getProfile().length() + 1;
String currentDir = StringUtils.substring(uploadDir, dirLastIndex);
return Constants.RESOURCE_PREFIX + "/" + currentDir + "/" + fileName;
```

`uploadDir` 形如 `D:/ruoyi/uploadPath/avatar`，`profile` 是 `D:/ruoyi/uploadPath`，
切掉 `len(profile) + 1` 之后剩 `avatar`，拼成：

```text
/profile/avatar/2026/10/26/avatar_20261026103851A001.png
```

这个字符串就是写进 `sys_user.avatar` 的值，也是前端 `<img src>` 的前缀
（`ResourcesConfig` 把 `/profile/**` 映射到 `profile` 目录）。

**没有校验** `uploadDir` 是否真的在 `profile` 之下 —— 传一个别处的目录会"从头截错位置"，
得到一串无意义的 url 但**不会抛异常**（Java 一样）。`TestFilenameHelpers::test_get_path_file_name_truncates_a_directory_outside_the_profile`
把这条不校验的行为钉住了。

### 4.5 `assertAllowed` 里的 `==` 是**引用比较**

```java
if (allowedExtension == MimeTypeUtils.IMAGE_EXTENSION) { throw new InvalidImageExtensionException(...); }
else if (allowedExtension == MimeTypeUtils.FLASH_EXTENSION) { ... }
else if (allowedExtension == MimeTypeUtils.MEDIA_EXTENSION) { ... }
else if (allowedExtension == MimeTypeUtils.VIDEO_EXTENSION) { ... }
else { throw new InvalidExtensionException(allowedExtension, extension, filename); }
```

Java 的 `String[] == String[]` 比的是引用。所以只有**恰好传进那四个常量之一**才走专用子类；
`new String[]{"png"}` 这种内容相同、对象不同的数组走最后一个分支。

Python 用 `is`（元组的身份比较）复刻，**没有**改成 `==`：

```python
if allowed_extension is IMAGE_EXTENSION: ...
```

`TestAssertAllowed::test_the_image_constant_raises_the_image_subtype` 与
`test_an_equal_but_distinct_tuple_raises_the_generic_type` 是这一对回归阀。
改成 `==` 会让"内容相同的列表"也抛 `InvalidImageExtensionException` ——
对外文案不同（`请上传[bmp, gif, jpg, jpeg, png]格式` vs `请上传[全部 22 种]格式`）。

### 4.6 `FilenameUtils` 只搬了 4 个分支

| Commons-IO | Python 私有函数 | 说明 |
|---|---|---|
| `FilenameUtils.getBaseName(name)` | `_get_base_name` | `a/b.png` → `b`；`a.b.png` → `a.b`；`.bashrc` → `""` |
| `FilenameUtils.getExtension(name)` | `_get_extension_of` | `lastSeparator > extensionPos` 时返回 `""`（点在目录上） |
| `FilenameUtils.indexOfLastSeparator` | `_index_of_last_separator` | 同时认 `/` 与 `\` |
| `FilenameUtils.indexOfExtension` | `_index_of_extension` | 找不到点 → `-1` |

没有引入 `commons-io` 依赖：只有这 4 个方法被 `FileUploadUtils` 用到，
"依赖一个包换 4 个 if" 不划算，而且 `basename` 的边界（`.bashrc` → `""`）
超出一般的直觉，抄过来反而更可控。

### 4.7 `defaultBaseDir` 的三件套

```java
private static String defaultBaseDir = RuoYiConfig.getProfile();
```

Java 的静态字段在类初始化时求值。Python 里 `settings` 是"可重载的单例"
（`reset_settings_cache()`），所以用**惰性读取 + 可覆盖**：

| Java | Python |
|---|---|
| `getDefaultBaseDir()` | `get_default_base_dir()`（未覆盖时**每次**问 `get_settings()`） |
| `setDefaultBaseDir(String)` | `set_default_base_dir(...)` |
| —— | `reset_default_base_dir()`（**没有 Java 对应**，测试用） |

惰性读取很关键：测试把 `RUOYI__PROFILE` 指到临时目录之后，不需要重建模块。

---

## 5. `Seq` / `MimeTypeUtils`

### 5.1 `Seq`：`yyyyMMddHHmmss` + `"A"` + 3 位序号

```text
20261026103851A001
└─ 14 位 ──┘│└ 3 ┘
          机器标识
```

| Java | Python | 说明 |
|---|---|---|
| `COMM_SEQ_TYPE` / `UPLOAD_SEQ_TYPE` | 同名常量 | 两个独立计数器 |
| `MACHINE_CODE = "A"` | 同名常量 | 单机部署写死 |
| `getId()` / `getId(String)` / `getId(AtomicInteger, int)` | `get_id(seq_type="COMMON", length=3)` | 三个重载合成一个；`AtomicInteger` 形参在 Python 里没有对应物 |
| `getSeq(AtomicInteger, int)`（private） | `_get_seq` | `threading.Lock` 复刻 `synchronized` |
| —— | `reset_seq()` | **没有 Java 对应**，测试用 |

**注释与代码不一致**：Java 注释写"默认 16 位序列号 `yyMMddHHmmss`"，代码用的是
`DateUtils.dateTimeNow()` 的 14 位 `yyyyMMddHHmmss`，总长 **18**。按**代码**实现 ——
文件名长度会进 `sys_user.avatar`，长度变了就是行为变更。

**循环边界**：先取值、再 `+1`、**再**判断 `>= 10**length` 就重置。所以输出是 `1..999`，
永远不会是 `000`，也永远不会是 `1000`。写成"value >= max 就归零"会错一位。
`TestSeq::test_the_sequence_wraps_after_nine_for_length_one` 用 `length=1` 把这件事变可测。

### 5.2 `MimeTypeUtils`：只认 5 种图片

| Java 常量 | Python | 内容 |
|---|---|---|
| `IMAGE_PNG` / `IMAGE_JPG` / `IMAGE_JPEG` / `IMAGE_BMP` / `IMAGE_GIF` | 同名常量 | 5 个 `Content-Type` 字符串 |
| `IMAGE_EXTENSION` | `IMAGE_EXTENSION` | `("bmp","gif","jpg","jpeg","png")` —— 必须与 `assert_allowed` 的 `is` 比较同一个对象 |
| `FLASH_EXTENSION` | `FLASH_EXTENSION` | `("swf","flv")` |
| `MEDIA_EXTENSION` | `MEDIA_EXTENSION` | 12 项，含 `swf`/`flv`/`mp3`/... |
| `VIDEO_EXTENSION` | `VIDEO_EXTENSION` | `("mp4","avi","rmvb")` |
| `DEFAULT_ALLOWED_EXTENSION` | `DEFAULT_ALLOWED_EXTENSION` | 22 项，**顺序即文案顺序** |
| `getExtension(String prefix)` | `get_extension(prefix)` | `switch` → if 链；`default` 回 `""` |

`DEFAULT_ALLOWED_EXTENSION` 的顺序会原样出现在
`文件[a.exe]后缀[exe]不正确，请上传[bmp, gif, ...]格式` 这句里，
所以"排序"也是一条行为，不能为了好看重排。

`getExtension` 只认 5 种图片前缀 —— 换句话说 `image/webp` 返回 `""`，
随后被后缀白名单拦下（`""` 不在 22 项里）。这也是 Java 原样。

---

## 6. 实体字段：只列容易被改错的

| Java | Python | 类型 | 说明 |
|---|---|---|---|
| `Long userId` | `user_id` | `Optional[int]` | `updateUser` 的 where 条件，**body 里不送就更新不到任何行** |
| `String userName` | `user_name` | `Optional[str]` | 只用于拼提示文案（§3.2）；**不是** where 条件 |
| `String nickName` | `nick_name` | `Optional[str]` | 回写缓存的 4 个字段之一 |
| `String phonenumber` | `phonenumber` | `Optional[str]` | **一个词**，JSON key 不是 `phoneNumber` |
| `String email` | `email` | `Optional[str]` | |
| `String sex` | `sex` | `Optional[str]` | `0` 男 / `1` 女 / `2` 未知（字符串） |
| `String avatar` | `avatar` | `Optional[str]` | 存的是 `/profile/avatar/...` 相对 url |
| `String password` | `password` | `Optional[str]`，`exclude=True` | **write-only**：`/system/user/profile` 的 `data` 里**看不到**它 |
| `String confirmPassword` | `confirm_password` | `Optional[str]` | 只被"用户管理"的密码端点用，本切片不读 |

`password` 用 `Field(exclude=True)` 而不是"返回前 pop 掉"：`profile` 直接
`AjaxResult.success_data(user)`，没有中间层可以 pop；靠 pydantic 的
`field_serializer`/`exclude` 才能在**所有**序列化路径上都保持一致。

`/system/user/profile` 的 `data` 是**缓存里的**那个对象（`login_tokens:<uuid>` 里那份），
不是重新查库。所以它带着 `user_name` / `admin` 之类的全字段，只少了 `password`。

---

## 7. 逐行对照速查

```text
SysProfileController#profile        -> sys_profile_controller.profile        (GET  /system/user/profile)
SysProfileController#updateProfile  -> sys_profile_controller.update_profile (PUT  /system/user/profile)
SysProfileController#updatePwd      -> sys_profile_controller.update_pwd     (PUT  /system/user/profile/updatePwd)
SysProfileController#avatar         -> sys_profile_controller.avatar        (POST /system/user/profile/avatar)

SysUserServiceImpl#selectUserRoleGroup  -> SysUserService.select_user_role_group
SysUserServiceImpl#selectUserPostGroup  -> SysUserService.select_user_post_group
SysUserServiceImpl#checkPhoneUnique     -> SysUserService.check_phone_unique
SysUserServiceImpl#checkEmailUnique     -> SysUserService.check_email_unique
SysUserServiceImpl#updateUserProfile    -> SysUserService.update_user_profile   (= update_user)
SysUserServiceImpl#updateUserAvatar     -> SysUserService.update_user_avatar
SysUserServiceImpl#resetUserPwd         -> SysUserService.reset_user_pwd

SysUserMapper.xml#updateUser        -> SysUserMapper.update_user
SysUserMapper.xml#updateUserAvatar  -> SysUserMapper.update_user_avatar
SysUserMapper.xml#resetUserPwd      -> SysUserMapper.reset_user_pwd

FileUploadUtils#upload(MultipartFile)                    -> file_upload_utils.upload_default
FileUploadUtils#upload(String, MultipartFile)            -> file_upload_utils.upload
FileUploadUtils#upload(String, MultipartFile, String[])  -> file_upload_utils.upload_with_extensions
FileUploadUtils#extractFilename       -> file_upload_utils.extract_filename
FileUploadUtils#getAbsoluteFile       -> file_upload_utils.get_absolute_file
FileUploadUtils#getPathFileName       -> file_upload_utils.get_path_file_name
FileUploadUtils#assertAllowed         -> file_upload_utils.assert_allowed
FileUploadUtils#isAllowedExtension    -> file_upload_utils.is_allowed_extension
FileUploadUtils#getExtension          -> file_upload_utils.get_extension
FileUploadUtils#getDefaultBaseDir     -> file_upload_utils.get_default_base_dir
FileUploadUtils#setDefaultBaseDir     -> file_upload_utils.set_default_base_dir
MultipartFile#getSize                 -> file_upload_utils.size_of
MultipartFile#isEmpty                 -> sys_profile_controller._is_empty_file  (size_of(file) == 0)

FilenameUtils#getBaseName             -> file_upload_utils._get_base_name
FilenameUtils#getExtension            -> file_upload_utils._get_extension_of
FilenameUtils#indexOfExtension        -> file_upload_utils._index_of_extension
FilenameUtils#indexOfLastSeparator    -> file_upload_utils._index_of_last_separator

MimeTypeUtils#getExtension            -> mime_type_utils.get_extension

Seq#getId()                           -> seq.get_id()
Seq#getId(String type)                -> seq.get_id(seq_type)
Seq#getId(AtomicInteger, int)         -> seq.get_id(seq_type, length)
Seq#getSeq(AtomicInteger, int)        -> seq._get_seq

FileException                         -> file.FileException
FileSizeLimitExceededException        -> file.FileSizeLimitExceededException
FileNameLengthLimitExceededException  -> file.FileNameLengthLimitExceededException
FileUploadException                   -> file.FileUploadException
InvalidExtensionException             -> file.InvalidExtensionException
  .InvalidImageExtensionException     -> file.InvalidImageExtensionException
  .InvalidFlashExtensionException     -> file.InvalidFlashExtensionException
  .InvalidMediaExtensionException     -> file.InvalidMediaExtensionException
  .InvalidVideoExtensionException     -> file.InvalidVideoExtensionException

RuoYiConfig#getImportPath             -> settings.RuoYiSection.import_path
RuoYiConfig#getAvatarPath             -> settings.RuoYiSection.avatar_path
RuoYiConfig#getDownloadPath           -> settings.RuoYiSection.download_path
RuoYiConfig#getUploadPath             -> settings.RuoYiSection.upload_path

HttpServletRequest#getParameter       -> sys_profile_controller._request_parameters
```
