# MAPPING_SYS_UPGRADE_INFO.md — `sys_upgrade_info` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §35。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectSysUpgradeInfoNewest` → `select_sys_upgrade_info_newest`。
- 接口与实现（`ISysUpgradeInfoService` + `SysUpgradeInfoServiceImpl`）在 Python 里合并成一个类。
- 本切片**没有引入新的基础设施**：实体基类 `BaseUuidEntity`、`session_scope`、分页、
  `AjaxResult` 全部复用 Phase 3.15 已有的实现。唯一新增的公共件是
  `base_controller.parse_str_array`（见 §2.5）。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysUpgradeInfoController.java` | `app/api/system/sys_upgrade_info_controller.py` | **新建**；**7 个映射，迁移 6 个**（`export` 缺 `ExcelUtil`） |
| `ruoyi-system/.../service/ISysUpgradeInfoService.java`<br>`ruoyi-system/.../service/impl/SysUpgradeInfoServiceImpl.java` | `app/system/service/sys_upgrade_info_service.py` | **新建**；6 个方法，其中 **3 个直接返回 `AjaxResult`** |
| `ruoyi-system/.../mapper/SysUpgradeInfoMapper.java`<br>`ruoyi-system/.../resources/mapper/system/SysUpgradeInfoMapper.xml` | `app/system/mapper/sys_upgrade_info_mapper.py` | **新建**；7 个方法 ↔ 7 条 statement，**严格 1:1** |
| `ruoyi-system/.../domain/SysUpgradeInfo.java` | `app/system/domain/sys_upgrade_info.py` | **新建**；3 个自有字段 + `BaseUuidEntity`，**零校验注解** |
| `ruoyi-admin/.../RuoYiApplication.java`（`@SpringBootApplication` 扫描） | `app/main.py` | **改了一处**：`include_router(sys_upgrade_info_router)` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `BaseController#startPage()` | `base_controller.start_page()` | 只有 `list` 调用 |
| `BaseController#getDataTable(List)` | `base_controller.get_data_table(rows)` | 有 `.total` 就用它，否则 `len(rows)` |
| `@PathVariable String[] ids` | `base_controller.parse_str_array(raw)` | **本切片新增**：逗号串 → `List[str]`，**不**转 `int` |
| 无注解实体参数 `SysUpgradeInfo` | `bind_query_params(SysUpgradeInfo, request.query_params)` | 无 `@RequestBody` 即按 query string 绑定（`list` / `newest`） |
| `@RequestBody SysUpgradeInfo` | 直接写成 FastAPI 的 pydantic 形参 | `add` / `edit`；**没有** `@Validated` |
| `@PreAuthorize("@ss.hasPermi(...)")` | **没有** | 整个控制器**一个权限点都没有**，见 §2.2 |
| `@Log(title = "系统升级信息", ...)` | **未迁移** | 不写 `sys_oper_log`，见 §35.3 |
| `SecurityUtils#getTenantId()` | `security_utils.get_tenant_id()` | `list` 在**控制器**里盖；`saveSysUpgradeInfo` 新增时也盖 |
| `SecurityUtils#getUserId()` | `security_utils.get_user_id()` | 四个审计列 |
| `SecurityUtils#getEpsId()` | `security_utils.get_eps_id()` | 新增时写 `eps_id`（= `sysUser.deptId`） |
| `StringUtils.getUUID()` | `string_utils.get_uuid()` | 32 位、无连字符 |
| `DateUtils.getTimestamp()` | `date_utils.get_timestamp()` | 毫秒截断；`curDate` 取一次 |
| `StringUtils.isNotEmpty(String)` | `string_utils.is_not_empty(value)` | `saveSysUpgradeInfo` 判"有没有 id"（会 trim） |
| `AjaxResult.success(msg, data)` | `AjaxResult.success_message_data(msg, data)` | `"操作成功！"` 是全角叹号 |
| `AjaxResult.success(data)` | `AjaxResult.success_data(data)` | `data=None` 时键整个消失 |

### 1.3 测试

| 层 | Python 测试文件 | 函数数 → 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_upgrade_info_mapper.py` | 35 → **36** | 硬编码 `where t.del_flag = '0'` + 7 个 `<if>` 的判据与顺序 / byId **无** `del_flag` 过滤 / `newest` 无视入参 + `back_col1 = 1` + `LIMIT 1` / insert 无 `useGeneratedKeys` / update 只有 `!= null`（`""` 清列）/ 两条软删除 |
| Service | `tests/test_sys_upgrade_info_service.py` | 19 → **21** | `isNotEmpty` 三态走新增 / 新增时**多盖** `tenantId` / 改时不回填 `createTime` / 全角叹号 / `count == 0` 仍 200 / 孤儿方法 `deleteSysUpgradeInfoById` |
| Controller | `tests/test_sys_upgrade_info_controller.py` | 48 → **51** | 6 条路由与注册顺序 / **零权限点** / `list` 覆盖 `tenantId` / `remove` 用 `parse_str_array` / `export` 落进 `String` 的 `/{id}` 且回 200 无 `data` |

合计 **108** 条（36 + 21 + 51）。加上 Phase 3.14 的 122 条与 3.15 的 102 条，全量从
**1847** 到 **1955**。

---

## 2. 控制器：7 个映射

### 2.1 端点逐条对照

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list` | `list_upgrade_infos` | GET `/system/upgradeInfo/list` | **无** |
| `newest` | `newest` | GET `/system/upgradeInfo/newest` | **无** |
| `export` | —（未迁移） | GET `/system/upgradeInfo/export` | **无** |
| `getInfo` | `get_info` | GET `/system/upgradeInfo/{id}` | **无** |
| `add` | `add` | POST `/system/upgradeInfo` | **无** |
| `edit` | `edit` | PUT `/system/upgradeInfo` | **无** |
| `remove` | `remove` | DELETE `/system/upgradeInfo/{ids}` | **无** |

### 2.2 一个 `@PreAuthorize` 都没有

这与 `sys_index_menu`（两个权限点）、`sys_config`（五个）都不同：Java 源码里本控制器
**根本没有写** `@PreAuthorize`，不是被注释掉。

所以本模块的鉴权强度只有 `SecurityConfig` 的 `anyRequest().authenticated()`：**登录即可**，
不查权限点。

> **不要"顺手补上"**。补了会让没有"系统升级信息"菜单权限的普通用户看不到升级公告 ——
> 这个接口是登录页/首页弹窗的数据源。

### 2.3 注册顺序，以及 `export` 为什么不会 500

`/list` 与 `/newest` **必须**排在 `/{id}` 之前。这里的 `/{id}` 声明成 `String`（主键是
UUID），它能吃掉**任何**单段路径：

| 请求 | 落到 | 结果 |
|---|---|---|
| `GET /system/upgradeInfo/list` | `list` | `TableDataInfo` |
| `GET /system/upgradeInfo/newest` | `newest` | `AjaxResult` |
| `GET /system/upgradeInfo/export` | **`get_info("export")`** | `{"code":200,"msg":"操作成功"}` —— **没有 `data` 键** |
| `GET /system/upgradeInfo/abc` | `get_info("abc")` | 同上，**不会** 500 |

其它模块（`sys_config` / `sys_dict` / `sys_indexmenu` …）的 `/{id}` 是 `Long`，
所以未迁移的 `export` 会 `int("export")` 失败 → `HTTP 200 + code 500`。**本模块是唯一例外**，
因为类型转换根本不会发生。Java 下这里返回的是
`{"code":200,"msg":"操作成功","data":{"fileName":...}}`（`ExcelUtil.exportExcel` 的返回体，
文件本身走 response 下载）—— 状态码相同，信封不同。

### 2.4 `list` 在控制器里盖 `tenantId`

```java
// Java
startPage();
sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
```

客户端传的 `?tenantId=xxx` 会被**登录上下文**覆盖，SQL 的 `<if test="tenantId != null">`
因此总是生效（除非登录用户的 `tenantId` 是 `null`）。

对照：`sys_index_menu` 把"覆盖用户 id"放在 **Service**，本模块放在 **控制器**，Service
只是纯转发。两处位置不同是照抄 Java 的结果，不是笔误。

### 2.5 `remove` 的 `String[]` 与新增的 `parse_str_array`

Java 声明 `@PathVariable String[] ids`（**其它模块都是 `Long[]`**），Spring 按逗号切分。

Python 用 :func:`app.common.core.controller.base_controller.parse_str_array`：

| 输入 | `parse_str_array` | 若误用 `parse_id_array` |
|---|---|---|
| `"1d3f0b9c..."` | `["1d3f0b9c..."]` | `ValueError` → 500 |
| `"u-1,u-2"` | `["u-1", "u-2"]` | 500 |
| `"u-1,,u-2"` | `["u-1", "", "u-2"]` | 500（中间空段 `int("")`） |

即：**用错这个助手，所有删除请求都会 500。**

### 2.6 `add` / `edit` 都没有 `@Validated`

与 Java 一致，两个端点只写 `@RequestBody`。因此：

- 空 body `{}` 会被接受（字段全 `None`），由 Service 走**新增**分支；
- 本模块**不建** `*_CONSTRAINTS` 表（对比 `sys_config` / `sys_user`）；
- `PUT` 没有 `id` 时**不会报错**，Service 会当成新增插一条新记录。

---

## 3. Service：6 个方法

### 3.1 方法对照

| Java | Python | 返回 |
|---|---|---|
| `selectSysUpgradeInfoById(String id)` | `select_sys_upgrade_info_by_id(id)` | `SysUpgradeInfo \| None` |
| `selectSysUpgradeInfoList(SysUpgradeInfo)` | `select_sys_upgrade_info_list(entity)` | `List[SysUpgradeInfo]` |
| `selectSysUpgradeInfoNewest(SysUpgradeInfo)` | `select_sys_upgrade_info_newest(entity)` | `SysUpgradeInfo \| None` |
| `saveSysUpgradeInfo(SysUpgradeInfo)` | `save_sys_upgrade_info(entity)` | `AjaxResult` |
| `deleteSysUpgradeInfoByIds(String[] ids)` | `delete_sys_upgrade_info_by_ids(ids)` | `AjaxResult` |
| `deleteSysUpgradeInfoById(String id)` | `delete_sys_upgrade_info_by_id(id)` | `AjaxResult` —— **孤儿方法** |

### 3.2 三个方法直接返回 `AjaxResult`，`count == 0` 也是成功

| 方法 | 返回 |
|---|---|
| `save_sys_upgrade_info` | `success("操作成功！", id)` —— **全角叹号** |
| `delete_sys_upgrade_info_by_ids` | `success(count)` |
| `delete_sys_upgrade_info_by_id` | `success(count)` |

用的是 `AjaxResult.success`，**不是** `toAjax`。改成 `toAjax` 会把"删一个不存在的 id"
从 `200` 变成 `500`。

### 3.3 `saveSysUpgradeInfo` 与 `SysIndexMenu` 的两处差异

同样是 `extends BaseUuidEntity`、同样"有 id 就改、没 id 就新增"，但：

| 差异 | `SysUpgradeInfo` | `SysIndexMenu` |
|---|---|---|
| 新增时盖 `tenantId` | **盖** `SecurityUtils.getTenantId()` | **不盖**（只盖 `epsId`） |
| 改的时候 | 只动 `updateBy` / `updateTime` | 只动 `updateBy` / `updateTime`（相同） |

漏掉 `tenantId` 不会报错，只会让新建的升级公告对**同租户的其他人**不可见（列表按
`tenant_id` 等值过滤）。

判据是 `StringUtils.isNotEmpty(id)`：`None` / `""` / `"   "` 都算"没有 id"，走新增并生成
新 UUID。

### 3.4 `deleteSysUpgradeInfoById` 是孤儿方法

接口声明了、实现也有，但**控制器只调 `ByIds`**。按迁移原则第 4 条照留并标注，不删。
它的行为与 `ByIds` 一致（软删除、`count == 0` 也 200），也照写了测试。

---

## 4. Mapper：7 条 statement

### 4.1 方法对照

| Java（XML `id`） | Python |
|---|---|
| `selectSysUpgradeInfoVo`（`<sql>`） | `SELECT_SYS_UPGRADE_INFO_VO` 常量 |
| `selectSysUpgradeInfoById` | `select_sys_upgrade_info_by_id` |
| `selectSysUpgradeInfoList` | `select_sys_upgrade_info_list` |
| `selectSysUpgradeInfoNewest` | `select_sys_upgrade_info_newest` |
| `insertSysUpgradeInfo` | `insert_sys_upgrade_info` |
| `updateSysUpgradeInfo` | `update_sys_upgrade_info` |
| `deleteSysUpgradeInfoById` | `delete_sys_upgrade_info_by_id` |
| `deleteSysUpgradeInfoByIds` | `delete_sys_upgrade_info_by_ids` |

VO 的 11 列（顺序即 SQL 顺序）：
`t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag, t.create_by, t.create_time,
t.update_by, t.update_time, t.tenant_id`。

### 4.2 列表 SQL：硬编码 `where` + 7 个 `<if>`

XML 里**没有** `<where>` 标签，第一行就是 `where t.del_flag = '0'`，后面每个 `<if>` 自带
`and`。所以 Python 侧条件片段**不带**前导 `AND`，统一用 `"\nand "` 连接。

| 字段 | Java 判据 | `""` | `None` |
|---|---|---|---|
| `id` / `ver` / `info` / `backCol1` | `!= null and != ''` | **跳过** | 跳过 |
| `epsId` / `tenantId` / `createBy` | `!= null` | **发出去** | 跳过 |

> 后三个字段是 `Long`，Spring 会把空串转成 `null`，所以正常链路里看不到"发空串"；
> 但判据确实只有 `!= null`，`0` 是**会**发出去的（测试钉住了这两点）。

`order by t.create_time desc,t.id` 是**自带**的：

- 不会追加客户端的 `orderByColumn` —— 前端点表头排序对这张表**不生效**；
- 分页时 `select_page` 检测到已有 `order by` 就跳过追加（否则 MySQL 语法错）。

### 4.3 `selectSysUpgradeInfoById` 没有 `del_flag` 过滤

```sql
select <include refid="selectSysUpgradeInfoVo"/> from sys_upgrade_info t where t.id = #{id}
```

与列表（始终带 `del_flag = '0'`）**不对称**：被软删除的记录仍能按 id 查到。照抄。

影响：`GET /system/upgradeInfo/{已删除的id}` 会返回整条记录，而不是空信封。

### 4.4 `selectSysUpgradeInfoNewest` 的三个特殊点

1. `resultType` 而不是 `resultMap` —— 靠 `mapUnderscoreToCamelCase` 自动映射；11 个属性名
   与列名一一对得上，结果一致。
2. SQL **完全无视入参**：Java 声明了 `SysUpgradeInfo sysUpgradeInfo`，但语句里没有一个
   `#{...}`。传 `?ver=9.9.9` 与不传结果相同。
3. `back_col1` 是 `varchar`，却和数字 `1` 比较（MySQL 隐式转换）；`ORDER BY t.UPDATE_TIME`
   用大写列名。两处都照抄。

效果：只有 `del_flag = '0'` 且 `back_col1` 值为 `"1"` 的行参选，按 `update_time` 取最新一条，
`limit 1`。

### 4.5 `insert` / `update` 的列

| 语句 | 列数 | 判据 | 备注 |
|---|---|---|---|
| `insertSysUpgradeInfo` | **11**（`id` … `tenant_id`） | 全部 `!= null` | **没有** `useGeneratedKeys`；全 `None` 会拼出 `insert into sys_upgrade_info () values ()` |
| `updateSysUpgradeInfo` | **10**（无 `id`） | 全部 `!= null` | 传 `""` 会**清列**；`id` 只出现在 `where` 里 |

`""` 的区别只体现在**列表查询**（`!= null and != ''`），不体现在 insert/update。

### 4.6 两条 delete 都是软删除

```sql
update sys_upgrade_info set del_flag = '1' where id = :id
update sys_upgrade_info set del_flag = '1' where id in (:p0, :p1)
```

整个 XML 里**没有** `delete from`。`<foreach>` 空数组会拼出 `in ()`（Java 同样是语法错），
照抄不额外防护。

---

## 5. 实体：`SysUpgradeInfo extends BaseUuidEntity`

### 5.1 3 个自有字段

| Java 字段 | Python | 类型 | 说明 |
|---|---|---|---|
| `ver` | `ver` | `Optional[str]` | 版本 |
| `info` | `info` | `Optional[str]` | 更新信息（Python 侧不是保留字） |
| `backCol1` | `back_col1` | `Optional[str]` | 备用字段1；`newest` 用它筛"最新日志" |

### 5.2 继承来的基类字段（照抄，不要删）

`id`（UUID 字符串）、`epsId`、`delFlag`、`deptSubCode`、`tenantId`、`sort`、`remark`、
`flag`、`createBy` / `createTime` / `updateBy` / `updateTime`、`params`、`searchValue`。

`params` 在 `BaseUuidEntity` 里**没有** `@JsonInclude(NON_EMPTY)`，所以 JSON 里是
`"params": null`（而 `BaseEntity` 的实例会整键消失）。

### 5.3 零校验注解

`add` / `edit` 只写了 `@RequestBody`，连 `@Validated` 都没有，所以本模块**不建**
`*_CONSTRAINTS`。字段长度、非空全部由数据库决定。

---

## 6. 未迁移 / 未对齐

| 项 | 原因 | 影响 |
|---|---|---|
| `export`（`ExcelUtil`） | Excel 工具未迁移 | `GET .../export` 落进 `getInfo("export")`，回 200 且无 `data`。**不报错**，见 §2.3 |
| `@Log(title = "系统升级信息", ...)` | 操作日志切面未迁移 | 不写 `sys_oper_log` |
| `@Transactional` | 见 COMPATIBILITY §28.3 | 每条 SQL 独立提交 |
| `@Validated` | Java 本来就没有 | 无差异 |
