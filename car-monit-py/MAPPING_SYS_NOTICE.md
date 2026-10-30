# MAPPING_SYS_NOTICE.md — `sys_notice` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §31。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `addDeliveryTimeAbnormal` → `add_delivery_time_abnormal`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysNoticeService` +
  `SysNoticeServiceImpl`）在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。
- **本切片没有新增任何基础设施**：公告只有纯 CRUD，不涉及上传、导出、缓存。
  全部 4 个 Python 文件都是新建的，但都是"照抄"，没有为它改动任何已有模块
  （唯一的例外是 `main.py` 多了一行 `include_router`）。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysNoticeController.java` | `app/api/system/sys_notice_controller.py` | **新建**；**7 个映射，全部迁移**（本模块 Java 侧没有 `export`） |
| `ruoyi-system/.../service/ISysNoticeService.java`<br>`ruoyi-system/.../service/impl/SysNoticeServiceImpl.java` | `app/system/service/sys_notice_service.py` | **新建**；7 个方法合并成一个 `SysNoticeService` 类 |
| `ruoyi-system/.../mapper/SysNoticeMapper.java`<br>`ruoyi-system/.../resources/mapper/system/SysNoticeMapper.xml` | `app/system/mapper/sys_notice_mapper.py` | **新建**；6 个方法 ↔ 6 条 statement，**严格 1:1** |
| `ruoyi-system/.../domain/SysNotice.java` | `app/system/domain/sys_notice.py` | **新建**；8 个自有字段 + `BaseEntity` 6 个，**零校验注解** |
| `ruoyi-framework/.../config/SecurityConfig.java` | `app/framework/config/security_config.py` | **未改动**；`/system/notice/view/**` → `AccessMode.ANONYMOUS` 早已在规则表里 |
| `ruoyi-system/.../service/ISysFileService.java` | **无对应物** | `SysNoticeServiceImpl` 注入了它，但唯一使用点（富文本图片上传）在 Java 里**被注释掉了** —— 依赖是死的，不迁 |
| `ruoyi-admin/.../RuoYiApplication.java`（`@SpringBootApplication` 扫描） | `app/main.py` | **改了一处**：`include_router(sys_notice_router)` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `BaseController#startPage()` | `base_controller.start_page()` | 写 `PageDomain` 到 `ContextVar`，**不**发 SQL |
| `BaseController#getDataTable(List)` | `base_controller.get_data_table(rows)` | 有 `.total` 就用它，否则 `len(rows)` |
| `BaseController#toAjax(int)` | `base_controller.to_ajax(rows)` | `rows > 0` → `success()`，否则 `error()`（`"操作失败"`） |
| `BaseController#getUsername()` | `security_utils.get_username()` | 控制器写 `createBy` / `updateBy` 用它 |
| `SecurityUtils#getUserId()` / `#getTenantId()` | `security_utils.get_user_id()` / `get_tenant_id()` | 服务层**覆盖**上面那两个值时用它（§31.5） |
| `@PathVariable Long[] noticeIds` | `base_controller.parse_id_array(raw)` | 逗号串 → `List[int]` |
| `@Migration` 无注解实体参数 `SysNotice notice` | `bind_query_params(SysNotice, request.query_params)` | 无 `@RequestBody` 即按 query string 绑定（§2.1） |
| `@Validated @RequestBody SysNotice` | 直接形参 `notice: SysNotice` | **故意不包 `validate()`** —— 实体零约束（§31.7） |
| `@PreAuthorize("@ss.hasPermi(...)")` | `@pre_authorize_permi("system:notice:...")` | 只有 3 处；`list` / `listquery` / `getInfo` 都没有 |
| `@Log(title = "通知公告", ...)` | **未迁移** | 不写 `sys_oper_log`，见 §31.2 |
| `AjaxResult.success(Object)` | `AjaxResult.success_data(data)` | `data is None` 时**整个键省略**（与 Java `isNotNull` 判断一致） |

### 1.3 测试

| 层 | Python 测试文件 | 函数数 → 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_notice_mapper.py` | 28 → **28** | 8 个 `<if>` 的三类判据与顺序 / `or t.TENANT_ID = 100` 兜底 / `cast(... as char)` / `order by` 自带的后果 / insert 无 `notice_id` 列 / insert↔update 的判据不对称 / `tenant_id` 不可更新 |
| Service | `tests/test_sys_notice_service.py` | 17 → **17** | `noticeType` 强制 `"1"` / `createBy`、`updateBy` 被换成 `userId` / `tenantId` 盖章 / 富文本钩子已删 / `addDeliveryTimeAbnormal` 两条分支与"入参不被改写" |
| Controller | `tests/test_sys_notice_controller.py` | 30 → **32** | 7 条路由与注册顺序 / 只有 3 个权限点 / `listquery` 强制 `status="0"` / `/view/**` 与 `/{id}` 同源 / 无校验（5 条） |

合计 **77** 条（28 + 17 + 32，其中 1 条是 Phase 3.13 补的回归用例）；
Phase 3.12 交付时是 76 条、全量 **1351 passed**
（Phase 3.11 结束时是 1273，本切片 +76，角色列表补分页 +2）。

> Phase 3.13 又给 mapper 文件补了 1 条
> `test_the_where_clause_does_not_start_with_and` —— 本节列表页的 SQL 拼接当时会生成
> `... where AND ...`（MySQL 语法错），属 Phase 3.12 遗留，修法见
> [COMPATIBILITY.md](COMPATIBILITY.md) §32.12。所以现在是 28 条、全量 1623。

---

## 2. 控制器：7 个映射

### 2.1 端点逐条对照

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list(SysNotice notice)` | `list_notices(notice)` | GET `/system/notice/list` | 无（注解被注释） |
| `listquery(SysNotice notice)` | `listquery(notice)` | GET `/system/notice/listquery` | 无 |
| `getInfo(@PathVariable Long noticeId)` | `get_info(notice_id)` | GET `/system/notice/{notice_id}` | 无 |
| `getViewInfo(@PathVariable Long noticeId)` | `get_view_info(notice_id)` | GET `/system/notice/view/{notice_id}` | **匿名** |
| `add(@Validated @RequestBody SysNotice)` | `add(notice)` | POST `/system/notice` | `system:notice:add` |
| `edit(@Validated @RequestBody SysNotice)` | `edit(notice)` | PUT `/system/notice` | `system:notice:edit` |
| `remove(@PathVariable Long[] noticeIds)` | `remove(notice_ids)` | DELETE `/system/notice/{notice_ids}` | `system:notice:remove` |

### 2.2 注册顺序（不是装饰性的）

FastAPI 按**注册顺序**匹配，Spring 的 `AntPathMatcher` 优先字面量。为了两边同结果，
模块里的声明顺序是：

```
/list  →  /listquery  →  /view/{notice_id}  →  /{notice_id}  →  POST ""  →  PUT ""  →  DELETE /{notice_ids}
```

把 `/list` 挪到 `/{notice_id}` 之后，`GET /system/notice/list` 会被当成
`notice_id = "list"` 而在 `int` 转换处 422。`/view/{id}` 有两段，理论上不会被单段的
`/{id}` 吃掉，但仍然前置，保持"字面量在前"的一致规则。

### 2.3 查询参数绑定

`GET /list` 与 `/listquery` 的形参在 Java 里是**没有注解的实体**，Spring 用
`WebDataBinder` 按名字绑定请求参数。Python 用 `bind_query_params(SysNotice, query_params)`：

| Java 字段 | query 参数名 | Python 属性 |
|---|---|---|
| `noticeTitle` | `noticeTitle` | `notice_title` |
| `noticeType` | `noticeType` | `notice_type` |
| `status` | `status` | `status` |
| `createBy` | `createBy` | `create_by` |
| `bussId` / `bussName` | 同名 | `buss_id` / `buss_name` |
| `tenantId` | `tenantId` | `tenant_id` |
| `noticeContent` | `noticeContent` | `notice_content` |
| `params[beginTime]`（用不到） | — | 本模块 XML **没有** 时间范围条件 |

`pageNum` / `pageSize` / `orderByColumn` / `isAsc` 走的是 `start_page()` 那条通道
（见 `page_helper`），**不**在实体上。

---

## 3. Service：7 个方法

### 3.1 方法对照

| Java（`ISysNoticeService`） | Python | 说明 |
|---|---|---|
| `selectNoticeById(Long)` | `select_notice_by_id(notice_id)` | 一行转发；查不到返回 `None` |
| `selectNoticeList(SysNotice)` | `select_notice_list(notice)` | 一行转发；**分页点在 mapper** |
| `insertNotice(SysNotice)` | `insert_notice(notice)` | 3 处覆盖（§3.2） |
| `updateNotice(SysNotice)` | `update_notice(notice)` | 覆盖 `updateBy`；富文本钩子已注释 |
| `deleteNoticeById(Long)` | `delete_notice_by_id(notice_id)` | Java 侧无调用方，照搬 |
| `deleteNoticeByIds(Long[])` | `delete_notice_by_ids(notice_ids)` | 物理删除 |
| `addDeliveryTimeAbnormal(SysNotice)` | `add_delivery_time_abnormal(notice)` | **死代码**，返回 `Long`（公告 id） |

### 3.2 三处"服务层覆盖控制器"

```
控制器 add   : notice.createBy = userName("admin")
服务层 insert: notice.noticeType  = "1"          ← 强制
               notice.createBy    = userId("1")   ← 覆盖上面那句
               notice.tenantId    = 当前租户
```

`updateNotice` 只做最后一点的一半：`updateBy = userId`（不改租户）。
`addDeliveryTimeAbnormal` 走的是 mapper 直连，所以四行赋值是**手写补齐**的
（`createBy` / `tenantId` / `noticeType` / `status="0"`）。

**这三个覆盖都不许"修正"** —— 库里历史数据全是这个形状，改了会立刻出现
"新数据是 admin、老数据是 1"的混合状态。

---

## 4. Mapper：6 条 statement

### 4.1 语句对照

| XML `<select>/<insert>/<update>/<delete>` | Python |
|---|---|
| `<sql id="selectNoticeVo">` | `SELECT_NOTICE_VO`（模块常量，逐字照抄含缩进） |
| `<select id="selectNoticeById">` | `select_notice_by_id()` |
| `<select id="selectNoticeList">` | `select_notice_list()` ← **分页点** |
| `<insert id="insertNotice">` | `insert_notice()` |
| `<update id="updateNotice">` | `update_notice()` |
| `<delete id="deleteNoticeById">` | `delete_notice_by_id()` |
| `<delete id="deleteNoticeByIds">` | `delete_notice_by_ids()` |

接口方法数 = statement 数 = **6**，本模块没有"XML 有、接口无"的孤儿语句
（对比 `sys_menu` 的两条孤儿，见 §29.8）。

### 4.2 `selectNoticeList` 的 8 个 `<if>` 与三类判据

| 顺序 | 字段 | 判据 | 传 `""` 时 | 片段 |
|---|---|---|---|---|
| 1 | `noticeTitle` | `!= null and != ''` | 跳过 | `t.notice_title like concat('%', ?, '%')` |
| 2 | `noticeType` | `!= null and != ''` | 跳过 | `t.notice_type = ?` |
| 3 | `createBy` | **只有** `!= null` | **生效** | `t.create_by = ?` |
| 4 | `status` | `!= null and != ''` | 跳过 | `t.status = ?` |
| 5 | `bussId` | `!= null and != ''` | 跳过 | `t.buss_id = ?` |
| 6 | `bussName` | `!= null and != ''` | 跳过 | `t.buss_name like concat('%', ?, '%')` |
| 7 | `tenantId` | **只有** `!= null` | **生效** | `(t.TENANT_ID = ? or t.TENANT_ID = 100)` |
| 8 | `noticeContent` | `!= null and != ''` | 跳过 | `(t.notice_content = ?)` |

三个要点：

1. **`createBy` / `tenantId` 不判空串** —— 与其它 6 个字段不同。设计上是"按 id 过滤"，
   而 id 字段不该有"空串"语义。
2. **`tenantId` 带写死的 `or = 100`** —— 100 是内置的"公共/平台"租户，任何租户都能看到它
   的数据。这是 Java 原样，**不是** 数据范围过滤。
3. **`noticeContent` 用等值不用 like** —— 它是整段富文本，`like` 会变成全表扫且几乎不会命中。

顺序不能重排：`<where>` 里 `AND` 连接的顺序影响执行计划，虽然结果集相同，
但保持与 XML 一致便于逐行 diff。

### 4.3 `insertNotice` / `updateNotice` 的判据不对称（两处，方向相反）

| 字段 | insert 判据 | update 判据 |
|---|---|---|
| `noticeTitle` / `noticeType` / `status` / `remark` | `!= null and != ''` | `!= null and != ''` |
| `noticeContent` | `!= null and != ''` | **只有** `!= null` |
| `bussId` / `bussName` | **只有** `!= null` | `!= null and != ''` |
| `tenantId` | **只有** `!= null` | **不存在这一列** |
| `createBy` | `!= null and != ''` | — |
| `updateBy` | — | `!= null and != ''` |
| `createTime` / `updateTime` | 无条件 `sysdate()` | 无条件 `sysdate()` |

对应 Python 的两个常量：

```python
_INSERT_NOTICE_COLUMNS   = ("notice_title", "notice_type", "notice_content", "status",
                            "remark", "create_by", "buss_id", "buss_name", "tenant_id")
_INSERT_NOTICE_NULL_ONLY = ("buss_id", "buss_name", "tenant_id")          # 只看 != null

_UPDATE_NOTICE_COLUMNS = (   # (attribute, column, require_text)
    ("notice_title",   "notice_title",   True),
    ("notice_type",    "notice_type",    True),
    ("notice_content", "notice_content", False),   # 只有 != null
    ("status",         "status",         True),
    ("update_by",      "update_by",      True),
    ("buss_id",        "buss_id",        True),
    ("buss_name",      "buss_name",      True),
)   # tenant_id 不在其中
```

### 4.4 主键与自增

| 语句 | 主键处理 |
|---|---|
| `insertNotice` | `useGeneratedKeys="true" keyProperty="noticeId"` → `notice.notice_id = result.lastrowid` |
| `updateNotice` | `where notice_id = #{noticeId}`（`notice_id` 为空时 SQL 里是 `null`，永远匹配不到） |
| `deleteNoticeByIds` | `<foreach open="(" separator="," close=")">` → `_in_clause(...)`；空数组拼出 `in ()`，MySQL 语法错（Java 一样） |

`insertNotice` **没有** `notice_id` 的 `<if>`（对比 `insertPost` 有 `postId != 0` 的判据）：
入参带的 id 会被直接丢弃，永远由自增生成。

### 4.5 `cast(t.notice_content as char)`

投影里这一列写的是 `cast(t.notice_content as char) as notice_content`。
`notice_content` 是 `longtext`，驱动本来就能读成 `String`，这个 `cast` 在功能上多余 ——
但它是 SQL 规范的一部分（字符集/排序/NULL 处理上并非完全等价），**照抄，不要简化**。

---

## 5. `SysNotice` 实体

| Java 字段 | 列 | Python | 类型 | 备注 |
|---|---|---|---|---|
| `noticeId` | `notice_id` | `notice_id` | `Optional[int]` | 自增主键 |
| `noticeTitle` | `notice_title` | `notice_title` | `Optional[str]` | **无** `@NotBlank` |
| `noticeType` | `notice_type` | `notice_type` | `Optional[str]` | `1` 通知 / `2` 公告；新增时被强制成 `"1"` |
| `noticeContent` | `notice_content` | `notice_content` | `Optional[str]` | `longtext`；无长度上限 |
| `status` | `status` | `status` | `Optional[str]` | `0` 正常 / `1` 关闭 |
| `bussId` | `buss_id` | `buss_id` | `Optional[str]` | 业务 id（到货异常场景存收消息人 userId） |
| `bussName` | `buss_name` | `buss_name` | `Optional[str]` | 业务名称 |
| `tenantId` | `tenant_id` | `tenant_id` | `Optional[int]` | 列表 SQL 额外放行 `100` |
| `createBy` / `createTime` | 同名 | `create_by` / `create_time` | 继承 `BaseEntity` | 存的是 **userId 字符串** |
| `updateBy` / `updateTime` | 同名 | `update_by` / `update_time` | 继承 `BaseEntity` | 同上 |
| `remark` | `remark` | `remark` | 继承 `BaseEntity` | |
| `params` | — | `params` | 继承 `BaseEntity` | 为空时 JSON 里不出现 |

**约束表**：没有。`POST_CONSTRAINTS` / `DEPT_CONSTRAINTS` 那种东西本模块不存在，
因为 Java 实体上一个校验注解都没有 —— 见 §31.7。

---

## 6. 行号速查（改代码前先看这张表）

| 要改什么 | 去哪 |
|---|---|
| 端点路径 / 权限点 / 注册顺序 | `app/api/system/sys_notice_controller.py` 顶部 docstring + `router` 声明 |
| `listquery` 的 `status="0"` | `listquery()` 函数体（两行） |
| 服务层的三个覆盖 | `app/system/service/sys_notice_service.py` 的 `insert_notice` / `update_notice` |
| `<if>` 判据 / SQL 文本 | `app/system/mapper/sys_notice_mapper.py` 的 `_build_notice_list_sql` 与两个常量元组 |
| 投影列 / resultMap | 同文件的 `SELECT_NOTICE_VO` 与 `_NOTICE_COLUMNS` |
| 实体字段 / JSON 名 | `app/system/domain/sys_notice.py` |
| 路由是否挂上 | `app/main.py` 的 `include_router(sys_notice_router)` |
| 匿名放行规则 | `app/framework/config/security_config.py` 的 `AUTHORIZATION_RULES` |
| 行为差异说明 | [COMPATIBILITY.md](COMPATIBILITY.md) §31 |
