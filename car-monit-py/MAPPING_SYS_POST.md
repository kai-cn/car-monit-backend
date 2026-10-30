# MAPPING_SYS_POST.md — `sys_post` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §26。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectPostList` → `select_post_list`，`postCode` → `post_code`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysPostService` + `SysPostServiceImpl`）
  在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysPostController.java` | `app/api/system/sys_post_controller.py` | 7 个映射，已迁 6 个（`export` 除外） |
| `ruoyi-system/.../service/ISysPostService.java`<br>`ruoyi-system/.../service/impl/SysPostServiceImpl.java` | `app/system/service/sys_post_service.py` | 接口 + 实现合并为 `SysPostService`，11 个方法全部迁完 |
| `ruoyi-system/.../mapper/SysPostMapper.java`<br>`ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml` | `app/system/mapper/sys_post_mapper.py` | 接口 + XML 合并：XML 的每条 statement 变成一个模块级 SQL 常量 |
| `ruoyi-system/.../mapper/SysUserPostMapper.java` + XML | `app/system/mapper/sys_user_post_mapper.py` | 本切片只用 `countUserPostById` |
| `ruoyi-system/.../domain/SysPost.java` | `app/system/domain/sys_post.py` | 6 个业务字段 + `BaseEntity`；含 `POST_CONSTRAINTS` |
| `ruoyi-common/.../core/domain/BaseEntity.java` | `app/common/core/domain/base_entity.py` | `createBy` / `updateBy` / `remark` / `params` ... |
| `ruoyi-common/.../constant/UserConstants.java` | `app/common/constant/user_constants.py` | `NOT_UNIQUE_OLD = "1"` / `UNIQUE_OLD = "0"` |
| `ruoyi-common/.../core/controller/BaseController.java` | `app/common/core/controller/base_controller.py` | 本切片新增共用 `parse_id_array` |
| `javax.validation.constraints.*`（`@NotBlank` / `@Size`） | `app/common/utils/bean_validation.py` | **新增的桥接层**，见 §5 |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-framework/.../web/service/PermissionService.java`（`@ss.hasPermi`） | `app/framework/web/service/permission_service.py` | `@pre_authorize_permi("...")` |
| `ruoyi-framework/.../aspectj/LogAspect.java` | **未迁移** | 因此不写 `sys_oper_log`，见 COMPATIBILITY §26.2 |
| `pagehelper-spring-boot-starter`（`PageHelper.startPage`） | `app/common/core/page/page_helper.py` | `start_page()` / `take_page()` / `select_page()` |
| `ruoyi-common/.../utils/SecurityUtils.java` | `app/common/utils/security_utils.py` | 只用到 `get_username()`（填 `create_by` / `update_by`） |
| `ruoyi-common/.../utils/ExcelUtil.java` | **未迁移** | `export` 因此不注册，见 COMPATIBILITY §26.1 |
| `Hibernate Validator`（`MethodArgumentNotValidException`） | `bean_validation.validate()` + `RuntimeError` 处理器 | 见 §5 与 COMPATIBILITY §26.3 |

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_post_mapper.py` | 23 | SQL 文本 / 动态 `<if>` / `<set>` / `<foreach>` / 投影 / 分页 |
| Service | `tests/test_sys_post_service.py` | 27 | 转发目标 / `"0"`·`"1"` 翻译 / `-1` 哨兵 / 已分配整批拒绝 |
| Controller | `tests/test_sys_post_controller.py` | 44 | 路由表 / 权限标识 / 校验先于权限 / 四条文案 / 分页信封 |

合计 **94** 条；全量套件 **722 passed**。

Java 侧 **没有任何 `src/test`**，所以上表没有"Java 对应用例"列 ——
这些用例是照着 Java 源码逐行推导出来的，不是移植过来的。

---

## 2. 控制器：7 个映射逐条对照

前缀都是 `/system/post`。`权限` 列是 `@PreAuthorize("@ss.hasPermi(...)")` 的值；
写 `登录` 表示没有注解，只要求通过认证。

| # | Java 方法 | Python 函数 | HTTP + 路径 | 权限 |
|---|---|---|---|---|
| 1 | `list(SysPost post)` | `list_posts(post: PostParam)` | `GET /system/post/list` | `system:post:list` |
| 2 | `export(SysPost post)` | **未迁移** | — | `system:post:export` |
| 3 | `getInfo(Long postId)` | `get_info(post_id: int)` | `GET /system/post/{postId}` | `system:post:query` |
| 4 | `add(SysPost post)` | `add(post: ValidPost)` | `POST /system/post` | `system:post:add` |
| 5 | `edit(SysPost post)` | `edit(post: ValidPost)` | `PUT /system/post` | `system:post:edit` |
| 6 | `remove(Long[] postIds)` | `remove(post_ids: str)` | `DELETE /system/post/{postIds}` | `system:post:remove` |
| 7 | `optionselect()` | `optionselect()` | `GET /system/post/optionselect` | 登录 |

### 2.1 形参绑定的两套写法

| Java 形参 | 绑定来源 | Python |
|---|---|---|
| `SysPost post`（**无**注解） | query string | `PostParam = Annotated[SysPost, Depends(_query_post)]` |
| `@Validated @RequestBody SysPost post` | JSON body | `ValidPost = Annotated[SysPost, Depends(_validated_post)]` |
| `@PathVariable Long postId` | 路径 | `post_id: int`（FastAPI 直接转换） |
| `@PathVariable Long[] postIds` | 路径，逗号分隔 | `post_ids: str` + `parse_id_array(post_ids)` |

`remove` 的 Java 形参是数组，Spring 的 `StringToArrayConverter` 会按 `,` 切开逐个转 `Long`。
FastAPI 没有数组路径参数，所以收成 `str` 再交给 `parse_id_array`（与 `sys_user` 同款）。

### 2.2 声明顺序：为什么 `/list` 必须写在 `/{post_id}` 之前

FastAPI **按注册顺序**匹配，`/system/post/list` 若排在 `/system/post/{post_id}` 之后，
会被当成 `post_id = "list"`，随后在 `int` 转换处炸掉。Spring 的 `AntPathMatcher`
优先匹配字面量，所以两侧结果一致 —— 但 Python 侧必须靠**书写顺序**保证。
`tests/test_sys_post_controller.py::TestRouteTable::test_literal_paths_come_before_the_path_variable`
是这条约束的防回退阀。

---

## 3. 服务层：`ISysPostService` / `SysPostServiceImpl`

11 个方法全部迁移。8 个是一行转发，真正有逻辑的只有 `checkPost*Unique` 与 `deletePostByIds`。

| # | Java | Python | 备注 |
|---|---|---|---|
| 1 | `selectPostList(SysPost post)` | `select_post_list` | 分页由调用方 `start_page()` + mapper `take_page()` |
| 2 | `selectPostAll()` | `select_post_all` | `optionselect` 用，不分页 |
| 3 | `selectPostById(Long postId)` | `select_post_by_id` | 无行返回 `None` |
| 4 | `selectPostListByUserId(Long userId)` | `select_post_list_by_user_id` | 返回 **id 列表**，不是实体 |
| 5 | `selectPostsByUserName(String userName)` | `select_posts_by_user_name` | 返回实体列表 |
| 6 | `checkPostNameUnique(SysPost post)` | `check_post_name_unique` | 返回 `"0"`/`"1"` 字符串 |
| 7 | `checkPostCodeUnique(SysPost post)` | `check_post_code_unique` | 同上 |
| 8 | `countUserPostById(Long postId)` | `count_user_post_by_id` | **换 mapper**：走 `SysUserPostMapper` |
| 9 | `deletePostById(Long postId)` | `delete_post_by_id` | 直接删，**不**校验占用 |
| 10 | `deletePostByIds(Long[] postIds)` | `delete_post_by_ids` | 逐个校验占用，任一占用则整批拒 |
| 11 | `insertPost(SysPost post)` | `insert_post` | mapper 会回写 `post_id` |
| 12 | `updatePost(SysPost post)` | `update_post` | 动态 `<set>` |

### 3.1 `-1L` 哨兵

```java
Long postId = StringUtils.isNull(post.getPostId()) ? -1L : post.getPostId();
SysPost info = postMapper.checkPostNameUnique(post.getPostName());
if (StringUtils.isNotNull(info) && info.getPostId().longValue() != postId.longValue()) {
    return UserConstants.NOT_UNIQUE_OLD;
}
return UserConstants.UNIQUE_OLD;
```

"新增"没有 id，就折成 `-1`，于是"库里没有同名的"和"同名的就是我这一行"走同一分支。
用 `-1` 而不是 `0`：MySQL 自增从 1 开始，`0` 在某些 ORM 里会被当成"未设置"。

Python 侧逐字保留，包括返回值是**字符串** `"1"`/`"0"`（不是 `bool`）这一点。

### 3.2 `deletePostByIds` 的两处顺序

```python
for post_id in post_ids:
    post = self.select_post_by_id(post_id)          # ① 先查
    if self.count_user_post_by_id(post_id) > 0:     # ② 再查占用
        raise CustomException(f"{post.post_name}已分配,不能删除")
return self._mapper.delete_post_by_ids(post_ids)    # ③ 一条 delete 处理整批
```

- ①→② 的顺序**不能换**：异常文案用的是 `post.getPostName()`，它来自 ①。
  若岗位不存在，Java 会在 `post.getPostName()` 处 NPE；Python 同样是
  `AttributeError: 'NoneType' object has no attribute 'post_name'`，两者都是 500。
- 命中第一个已分配的岗位就抛出，**后面的 id 连查都不查**；
- 循环里从不删单条，最后一次性 `delete ... where post_id in (...)`。

### 3.3 依赖注入

Java 是 `@Autowired` 两个 mapper 字段；Python 是构造函数两个可选参数 +
模块级单例（`get_post_service()` / `reset_post_service()`）。
测试直接 `SysPostService(fake_post_mapper, fake_user_post_mapper)`。

---

## 4. Mapper 层

### 4.1 `SysPostMapper`（11 条 statement + 1 个 `<sql>` 片段）

| XML 片段 | Python | 备注 |
|---|---|---|
| `<sql id="selectPostVo">` | `SELECT_POST_VO` | 逐字照抄，含行尾空格与制表符 |
| `selectPostList` | `select_post_list` | PageHelper：`count` 包子查询 + `LIMIT` |
| `selectPostAll` | `select_post_all` | 复用 `selectPostVo` |
| `selectPostById` | `select_post_by_id` | `selectPostVo` + `where post_id = ?` |
| `selectPostListByUserId` | `select_post_list_by_user_id` | `resultType="Integer"`，返回 id |
| `selectPostsByUserName` | `select_posts_by_user_name` | 三列投影 |
| `checkPostNameUnique` | `check_post_name_unique` | `limit 1` |
| `checkPostCodeUnique` | `check_post_code_unique` | `limit 1` |
| `insertPost` | `insert_post` | 动态列 + `sysdate()` + `lastrowid` 回写 |
| `updatePost` | `update_post` | 动态 `<set>` + 无条件 `update_time` |
| `deletePostById` | `delete_post_by_id` | |
| `deletePostByIds` | `delete_post_by_ids` | `<foreach>` → `in (:p0, :p1, ...)` |

### 4.2 `selectPostList` 的三个 `<if>`

顺序 fixed：`postCode` → `status` → `postName`，用 `and` 连接。

**判据是 OGNL 的 `x != null and x != ''`，不是 `isBlank`。**
所以 `postCode = " "`（一个空格）会真的去 `like '% %'`。这一点很容易写错：
项目里的 `string_utils.is_not_empty()` 照抄的是 RuoYi 的 `StringUtils.isEmpty`，
它会**先 `trim`**，于是 `is_not_empty(" ")` 是 `False` —— 用它就会漏掉这个条件。
`_build_post_list_sql` 因此改用与 `sys_user_mapper._build_user_list_sql` 相同的
`value is None or value == ""` 判据。

### 4.3 投影：`update_by` / `update_time` 永远是 `null`

`selectPostVo` 只select 了 8 列：

```
post_id, post_code, post_name, post_sort, status, create_by, create_time, remark
```

`resultMap="SysPostResult"` 里的 `update_by` / `update_time` 没有对应列，因此
**每一条岗位响应里这两个字段都是 `null`**（`AjaxResult` 里由 Jackson 输出，
不会被省略 —— `BaseEntity` 上没有 `@JsonInclude`）。这不是漏写，改动前先看 XML。

### 4.4 分页

| Java | Python |
|---|---|
| `startPage()` 把 `pageNum`/`pageSize` 放进 `ThreadLocal` | `start_page()` 放进 `ContextVar` |
| `PageInterceptor` 拦截**第一条** select | `take_page()` 取一次即清空 |
| `select count(0) from (<原语句>) table_count` | 同左（先执行 count，再执行 data） |
| 追加 `limit ?, ?` | `select_page(...)` 追加 `LIMIT offset, size` |

---

## 5. Bean Validation：`@NotBlank` / `@Size` 的桥接

### 5.1 为什么 `SysPost` 需要、`SysUser` 不需要

`SysUser` 的 `@NotBlank` / `@Size` 在 Java 源码里被**整段注释掉**了，所以那边不做校验。
`SysPost` 的注解是**生效的**：

```java
@NotBlank(message = "岗位编码不能为空")
@Size(min = 0, max = 64, message = "岗位编码长度不能超过64个字符")
public String getPostCode() { return postCode; }

@NotBlank(message = "岗位名称不能为空")
@Size(min = 0, max = 50, message = "岗位名称长度不能超过50个字符")
public String getPostName() { return postName; }

@NotBlank(message = "显示顺序不能为空")   // 注意：没有 @Size
public String getPostSort() { return postSort; }
```

不迁的话，少一个 `postName` 的请求在 Java 里是
`{"code":500,"msg":"岗位名称不能为空"}`，在 Python 里会**插入一行 NULL**。

### 5.2 实现位置

| Java | Python |
|---|---|
| 注解挂在 getter 上 | `app/system/domain/sys_post.py` 的 `POST_CONSTRAINTS`（同文件、同顺序） |
| Hibernate Validator 遍历约束 | `bean_validation.validate(entity, constraints)` |
| `MethodArgumentNotValidException` | `BeanValidationError(RuntimeError)` |
| `fieldError.getDefaultMessage()` | 直接用约束对象里的中文文案 |

为什么不用 pydantic 的 `Field(...)`：pydantic 的校验消息是英文的
（`String should have at most 50 characters`），而 Java 那边回的是注解里的中文，
逐字对齐只能自己带文案。

### 5.3 为什么校验写成 `Depends` 而不是函数体第一行

Spring MVC 的真实顺序是：

```
安全过滤器链(401) -> 路由匹配 -> 反序列化 + 校验(500) -> @PreAuthorize(403) -> 方法体
```

`@PreAuthorize` 挂在 CGLIB 代理上，只在 `doInvoke` 阶段触发，而参数解析
（`resolveArgument` → `validateIfApplicable`）发生在 `invokeForRequest` 的开头。

Python 侧 `pre_authorize_permi` 是**装饰器**，它的检查天然在函数体之前。
把 `validate(...)` 写成函数体第一行，就会变成"没权限的人先撞 403"，
顺序与 Spring 相反：

| 场景 | Spring | 函数体第一行（错） | `Depends`（对） |
|---|---|---|---|
| 未登录 + 缺 `postName` | 500 岗位名称不能为空 | 403 | **500 岗位名称不能为空** |
| 未登录 + 合法 body | 403 | 403 | 403 |

FastAPI 的 `Depends` 在调用端点函数**之前**解析，正好补回 Spring 的位置。
代价是 `pre_authorize_permi` 必须保留原函数签名（`_keep_target_signature`），
否则 `Annotated[SysPost, Depends(...)]` 会在反射时退化成 query 参数
（那是 COMPATIBILITY §25.4 记过的坑）。

回归用例：
`tests/test_sys_post_controller.py::TestValidationRunsBeforePermission`（10 条：
8 条以“未登录 + 非法 body”驱动并断言 `code == 500`，另 2 条是对照组）。

### 5.4 多字段同时违规时报哪条

Java 的 `MethodArgumentNotValidException#getBindingResult().getFieldError()`
取 `BindingResult` 里的**第一个**错误，顺序由约束的声明顺序决定。
`POST_CONSTRAINTS` 按 `getPostCode` → `getPostName` → `getPostSort` 排列，
所以 `{}` 空对象回的是"岗位编码不能为空"。

---

## 6. 实体字段：只列容易被改错的

| Java | Python | 类型 | 说明 |
|---|---|---|---|
| `Long postId` | `post_id` | `Optional[int]` | 主键，自增 |
| `String postCode` | `post_code` | `Optional[str]` | `@NotBlank` + `@Size(max=64)` |
| `String postName` | `post_name` | `Optional[str]` | `@NotBlank` + `@Size(max=50)` |
| `String postSort` | `post_sort` | `JavaString` | **varchar 列 + `String` 字段**，前端发数字要强转（§25.5） |
| `String status` | `status` | `Optional[str]` | `0` 正常 / `1` 停用 |
| `boolean flag` | `flag` | `bool = False` | **基本类型**，恒定输出 `"flag": false`，不落库 |

`postSort` 用 `JavaString` 而不是 `Optional[str]`：RuoYi 前端用 `el-input-number`
绑定排序列，提交的是 **JSON 数字**，Jackson 的 `CoercionAction.TryConvert` 会解成
`"1"`。pydantic 默认拒绝 `int -> str`，不处理的话合法请求会变成 `code 500`。

---

## 7. 逐行对照速查

```text
SysPostController#list          -> sys_post_controller.list_posts      (GET  /system/post/list)
SysPostController#getInfo       -> sys_post_controller.get_info        (GET  /system/post/{postId})
SysPostController#add           -> sys_post_controller.add             (POST /system/post)
SysPostController#edit          -> sys_post_controller.edit            (PUT  /system/post)
SysPostController#remove        -> sys_post_controller.remove          (DELETE /system/post/{postIds})
SysPostController#optionselect  -> sys_post_controller.optionselect    (GET  /system/post/optionselect)

SysPostServiceImpl#checkPostNameUnique -> SysPostService.check_post_name_unique
SysPostServiceImpl#checkPostCodeUnique -> SysPostService.check_post_code_unique
SysPostServiceImpl#deletePostByIds     -> SysPostService.delete_post_by_ids

SysPostMapper.xml#selectPostList -> SysPostMapper.select_post_list
SysPostMapper.xml#insertPost     -> SysPostMapper.insert_post
SysPostMapper.xml#updatePost     -> SysPostMapper.update_post
```
