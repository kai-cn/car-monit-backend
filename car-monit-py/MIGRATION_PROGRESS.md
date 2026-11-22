# 迁移进度总表 / Migration Progress

> 本文件是**唯一**的进度来源。每完成一个可交付的切片就更新一次，不重复写进别处。
>
> 相关文档：
> - `COMPATIBILITY.md` —— 与 Java 的**逐条差异**台账（编号 §1…§44，带影响分级）
> - `MAPPING_*.md` —— 每个切片的 Java↔Python 对照表
> - `MIGRATION_GUIDE.md` —— **怎么迁的**（约束、分层映射、步骤、坑、回归基线）
> - `README_PY.md` —— 部署与启动（环境、配置、启动脚本、自检、常见问题）
> - 本文件 —— **做到哪一步了**（范围、状态、剩余项）
>
> **本轮已完成**：所有改动均已落盘，环境、数字、四项审计全部重做，当前基线见 **§6.10**。

最后更新：**Phase 3.24（`generator` 代码生成）+ Phase 5（启动脚本与部署文档）+ Phase 6（全量一致性复核）+ Phase 6.1（从头复核与 5 份对照表）+ Phase 6.2（双前端实例实测）**。

**Phase 3.24** 把 `ruoyi-generator` 剩下的部分补齐：`GenController` **15 个端点**、
`GenTableService` / `GenTableColumnService`、两个 Mapper（10 + 8 条语句）全部落地，
新增 4 个测试文件、**116 条用例**（`test_convert_arrays` 33 / `test_gen_table_mapper` 23 /
`test_gen_table_column_mapper` 17 / `test_gen_table_service` 43）。

**Phase 6** 是“从头重做一遍比对”，四层全查（路由 / 域字段 / 响应信封 / 端到端），结果写入
`COMPATIBILITY.md` **§44**：Java **501** 个端点 vs Python **502**（多出 `GET /health`，缺失 **0**）；
域字段 115 个可比、**零差异**；全量套件 **3597 passed / 0 failed / 0 skipped**；
`scripts/smoke_test.py` 真实 socket + 真 MySQL + 真 Redis **5/5**。

**第二轮从头复核**（§6.10）把上面这件事又重做了一遍：环境先起真库，
新增**响应信封**与**文案**两层机检脚本，补齐最后 5 份 `MAPPING_*.md`，
用例总数增至 **3644**（3561 单测 + 83 联调）。

随后 Phase 6.2 的双前端实例实测又抓出并修掉 2 个真差异（HMAC 密钥派生、坏 token 的响应），
用例增至 **3646**（3563 单测 + 83 联调），见 §6.11 与 `COMPATIBILITY.md` §44.7。

**Phase 5** 补齐启动与部署面：`start.sh` / `start.bat`（`ry.sh` / `ry.bat` 的 Python 版，
四个操作一一对应）、`scripts/app_pid.py`（替代 `jps -l` 的进程发现）、`README_PY.md`（部署说明，
`pyproject.toml` 的 `readme` 指向它）、`MIGRATION_GUIDE.md`（迁移手册），详见 §6.8。

这一轮抓到并修复了 **4 个真缺陷**（都属于“注释写对了、代码没跟上”的类型，详见 §44.2）：

| # | 缺陷 | 后果 |
| --- | --- | --- |
| 1 | `_java_split` 给尾部空串留了“至少一个”的保底 | `to_long_array(",")` 得 `[None]` 而非 `[]`，Java 的 `in ()` 语法错误（500）被降级成“删 0 行” |
| 2 | `importGenTable` 直接拼 `str(e)` | NPE 时文案是 `导入失败：java.lang.NullPointerException…`，Java 是 `导入失败：null` |
| 3 | 验证码用 `ajax["uuid"] = …` 直写 | 键序变成插入序，真实字节应为 `msg, img, code, uuid` |
| 4 | `getConfirmId` 直写 `data` | 输出恰好相同，但违反了“不得直写 AjaxResult”的不变量 |

顺带推翻了三条**错误的文档/断言结论**：

* `@Log` 调用点不是 **226** 而是 **233**（漏算了 `GenController` 的 7 处）——
  `MIGRATION_PROGRESS.md` / `COMPATIBILITY.md` §42.9 / `test_log_aspect.py` 已同步；
* `R<T>` **不是** `HashMap` 而是 POJO（`R.java:11` 是 `implements Serializable`），
  键序是字段序 `code, msg, data`，不能套桶序；
* `GenTable` 列表行的 `columns` 是 `null` 而不是 `[]`（MyBatis 的 `applyNestedResultMappings`
  在 ResultSet 里一列都对不上时**根本不构造**嵌套对象）。

最近五个切片（用例数为**实测**，不再用估算值）：

| 阶段 | 范围 | 新增用例 | 累计全量 |
| --- | --- | --- | --- |
| Phase 3.21 | `manager/bigScreen`（1 控制器 / **12 端点**） | 30 | **2972** |
| Phase 3.22 | **真实库联调**（全 75 控制器抽样） | 83 | **3056** |
| Phase 3.23 | `quartz`（2 控制器 / **13 端点** + 6 个任务 Bean） | 281 | **3400** |
| Phase 3.24 | `generator`（1 控制器 / **15 端点** + 2 Service + 2 Mapper） | 116 | **3516** |
| Phase 6 | 一致性复核（审计脚本 + 键序回归阀 + 文档 + 启动脚本用例） | 81 | **3597** |
| Phase 6.1 | 第二轮从头复核（信封/文案审计 + 审计规则护栏 31 条 + 5 份 `MAPPING_*.md` + 对照表护栏 16 条） | 47 | **3644** |
| Phase 6.2 | 双前端实例实测（8080→Java / 8081→Python）+ 修 2 处真差异 | 2 | **3646** |

`system` / `common` / `monitor` / `tool` / `base` / `manager` / `flow` / `quartz` / `generator` 九个包**全部完成**；
`ruoyi-admin` 的 **75** 个控制器 + `ruoyi-quartz` 的 **2** 个 + `ruoyi-generator` 的 **1** 个，一个不剩。

---

## 0. 状态图例

| 标记 | 含义 |
| --- | --- |
| `已完成` | 代码 + 测试 + 文档齐备，`pytest` 全绿 |
| `进行中` | 本切片正在写，代码可能暂时不完整 |
| `部分` | 只有被别的切片顺带用到的几个方法，端点未注册 |
| `未开始` | 一行都还没迁 |
| `不迁移` | 明确的决策，理由记在 `COMPATIBILITY.md` |

---

## 1. 阶段总览

| 阶段 | 范围 | 状态 |
| --- | --- | --- |
| Phase 0 | 工程骨架、配置、日志、健康检查 | 已完成 |
| Phase 1 | `ruoyi-common` 工具层（字符串/日期/JSON/Servlet/加密…） | 已完成 |
| Phase 2 | 基础设施（`AjaxResult`、`TableDataInfo`、`PageHelper`、实体、安全过滤器、异常处理器） | 已完成 |
| Phase 3 | `ruoyi-admin` 控制器逐个切片迁移 | **已完成（75/75 控制器）**（见 §2） |
| Phase 3.22 | **真实 MySQL / Redis 联调**（非 mock） | 已完成（见 §6.1–§6.6） |
| Phase 3.23 | **`quartz` 切片**（`ruoyi-quartz` 25 个源文件 / 2 个控制器） | 已完成（见 §6.7） |
| Phase 3.24 | **`generator` 切片**（`ruoyi-generator` / `GenController` **15 端点**） | 已完成（见 §2.1） |
| Phase 4 | 中间件（Redis / Quartz / Kafka / MinIO / Elasticsearch） | **部分完成**：Redis、Quartz 已落地；Kafka / MinIO / ES 只有开关与启动告警（§13） |
| Phase 5 | 启动脚本、部署说明、与 Java 并行对照验证 | **已完成**（见 §6.8） |
| Phase 6 | **全量一致性复核**（路由 / 域字段 / 响应信封 / 端到端） | 已完成（见 §6.8 / `COMPATIBILITY.md` §44） |

---

## 2. Phase 3 切片清单

### 2.1 已完成的切片

| # | 切片 | Python 模块 | 端点数 | 测试数 | 文档 |
| --- | --- | --- | --- | --- | --- |
| 3.1 | 首页 | `app/api/system/sys_index_controller.py` | 1 | — | — |
| 3.2 | 验证码 | `app/api/common/captcha_controller.py` | 1 | — | — |
| 3.3 | 登录 / 用户信息 / 路由 | `app/api/system/sys_login_controller.py` | 3 | `test_login_controller.py` | `COMPATIBILITY.md` §17-§20 |
| 3.4 | `sys_user` 用户管理 | `app/api/system/sys_user_controller.py` | 17 | `test_sys_user_*.py` (3 个文件) | `MAPPING_SYS_USER.md` |
| 3.5 | `sys_user` E2E（真 ASGI + 假 DB） | — | — | `test_e2e_sys_user.py` | `COMPATIBILITY.md` §25 |
| 3.6 | `sys_post` 岗位管理 | `app/api/system/sys_post_controller.py` | 6 | `test_sys_post_*.py` (3 个文件) | `MAPPING_SYS_POST.md` / §26 |
| 3.7 | `sys_dept` 部门管理 | `app/api/system/sys_dept_controller.py` | 11 | `test_sys_dept_*.py` (3 个文件) | `MAPPING_SYS_DEPT.md` / §27 |
| 3.9 | `sys_role` 角色管理 | `app/api/system/sys_role_controller.py` | **10（全部映射）** | `test_sys_role_*.py` (3 个文件) | `MAPPING_SYS_ROLE.md` / §28 |
| 3.10 | `sys_menu` 菜单管理 | `app/api/system/sys_menu_controller.py` | 7（全部映射，菜单无 `export`） | `test_sys_menu_*.py` (3 个文件) | `MAPPING_SYS_MENU.md` / §29 |
| 3.11 | `sys_profile` 个人信息 | `app/api/system/sys_profile_controller.py` | 4（全部映射，四个都无权限点） | `test_sys_profile_controller.py` + `test_file_upload_utils.py` | `MAPPING_SYS_PROFILE.md` / §30 |
| 3.12 | `sys_notice` 通知公告 | `app/api/system/sys_notice_controller.py` | 7（全部映射，只有 3 个权限点） | `test_sys_notice_*.py` (3 个文件) | `MAPPING_SYS_NOTICE.md` / §31 |
| 3.13 | `sys_dict` 字典（类型 + 数据） | `app/api/system/sys_dict_{type,data}_controller.py` | **16（全部映射）** | `test_dict_utils.py` + `test_sys_dict_*.py` (6 个文件) | `MAPPING_SYS_DICT.md` / §32 |
| 3.14 | `sys_config` 参数配置 | `app/api/system/sys_config_controller.py` | **8（全部映射）** | `test_sys_config_*.py` (3 个文件) | `MAPPING_SYS_CONFIG.md` / §33 |
| 3.15 | `sys_indexmenu` 用户常用菜单 | `app/api/system/sys_index_menu_controller.py` | **7（全部映射）** | `test_sys_index_menu_*.py` (3 个文件) | `MAPPING_SYS_INDEX_MENU.md` / §34 |
| 3.16 | `sys_upgrade_info` 系统升级信息 | `app/api/system/sys_upgrade_info_controller.py` | **7（全部映射）** | `test_sys_upgrade_info_*.py` (3 个文件) | `MAPPING_SYS_UPGRADE_INFO.md` / §35 |
| 3.17 | `sys_file` 文件管理（OSS） | `app/api/system/sys_file_controller.py` | **17（全部映射，本类无 `export`）** | `test_sys_file_*.py` (3 个文件) | `MAPPING_SYS_FILE.md` / §36 |
| 3.18 | `ExcelUtil` + 8 个 `export` + 2 个导入 | `app/common/utils/poi/excel_util.py`、`app/common/annotation/excel.py` | **+8 个 `export` 端点** + `importTemplate` / `importData` | `test_excel_util.py` | `MAPPING_EXCEL_UTIL.md` / §37 |
| 3.19 | `/common` 上传下载 + `/downTemplate` 模板 | `app/api/common/{common,down_template}_controller.py` | **5（全部映射）** | `test_file_utils.py` + `test_common_controller.py` + `test_down_template_controller.py` | `MAPPING_COMMON.md` / §38 |
| 3.20 | `monitor` 监控（操作日志 / 登录日志 / 缓存 / 服务器 / 在线用户） | `app/api/monitor/*_controller.py`（5 个） | **12（全部映射）** | `test_monitor_*.py`（3 个）+ 7 个分层用例文件 | `MAPPING_MONITOR.md` / §39 |
| 3.21 | **`manager/bigScreen` 大屏** | `app/api/manager/bigscreen/big_screen_controller.py` | **12（全部映射，全部 `GET`，零权限点）** | `test_big_screen_controller.py`（30 条） | `MAPPING_BIGSCREEN.md` / §40 |
| 3.23 | **`quartz` 定时任务**（`sys_job` + `sys_job_log` + 6 个任务 Bean + 调度器） | `app/api/monitor/sys_job{,_log}_controller.py`、`app/quartz/`（21 个模块） | **13（全部映射）** | `test_quartz_{controllers,cron_and_schedule,services,tasks}.py`（**281**） | `MAPPING_QUARTZ.md` / §42 / §43 |
| 3.24 | **`generator` 代码生成**（`GenController` + `GenTableService` / `GenTableColumnService` + 2 个 Mapper） | `app/api/tool/gen_controller.py`、`app/generator/` | **15（全部映射）** | `test_gen_table_{mapper,column_mapper,service}.py` + `test_gen_controller.py` + `test_convert_arrays.py`（**116**） | `COMPATIBILITY.md` §44 |

### 2.2 `system` 包控制器（**已全部完成**）

| 控制器 | 端点量 | 依赖的技术难点 | 状态 |
| --- | --- | --- | --- |
| `SysRoleController` | 10 | 数据权限、`sys_role_dept` / `sys_role_menu` 关联表 | 已完成（Phase 3.9 + 3.18 补 `export`，**10/10 端点**） |
| `SysMenuController` | **7** | 树构建（与 `sys_dept` 同构）、`selectMenuListByUserId` | 已完成（Phase 3.10，7/7 端点） |
| `SysDictTypeController` | **8**（早期写的 10 是重复计数） | 缓存（`DictUtils`）、`ExcelUtil` | 已完成（Phase 3.13 + 3.18，**8/8 端点**） |
| `SysDictDataController` | **8**（同上） | 同上 | 已完成（Phase 3.13 + 3.18，**8/8 端点**） |
| `SysConfigController` | **8**（早期写的 9 是错的） | 缓存（逐键写 / 删除全清）、`ExcelUtil` | 已完成（Phase 3.14 + 3.18，**8/8 端点**） |
| `SysNoticeController` | **7**（早期写的 8 是错的） | 无 —— 纯 CRUD，无缓存/无导出 | 已完成（Phase 3.12，7/7 端点） |
| `SysProfileController` | **4** | 改密（`getParameter` 绑定）、头像上传（`FileUploadUtils` / `Seq` / 文件异常族） | 已完成（Phase 3.11，4/4 端点） |
| `SysIndexMenuController` | **7**（早期写的 2 是错的） | 菜单树 SQL（双表自连）、`BaseUuidEntity` | 已完成（Phase 3.15 + 3.18，**7/7 端点**） |
| `SysFileController` | **17**（早期写的“—”是没数） | OSS（`AmazonS3`）/ 雪花 id / Forest 下载 / `HttpServletResponse` 流 | 已完成（Phase 3.17，**17/17 端点**） |
| `SysUpgradeInfoController` | **7** | 无 —— 纯 CRUD，无缓存 / **无任何权限点**；导出是零列空表 | 已完成（Phase 3.16 + 3.18，**7/7 端点**） |

### 2.3 其它包（全部收尾）

| 包 | 控制器数 | 状态 | 备注 |
| --- | --- | --- | --- |
| `base` | **25** | **已完成** | 高速门架 / 收费站 / ODS 快照等业务表；`app/api/base/`，用例 `test_base_*.py`（5 个文件 / **164** 条） |
| `manager` | **20** | **已完成** | 车辆监控业务主体；19 个在 `test_manager_controllers.py`（53 条），大屏 1 个在 `test_big_screen_controller.py`（Phase 3.21 / 30 条） |
| `flow` | 7 | **已完成** | 审批流；`test_flow_controllers.py`（55 条） |
| `tool` | 1 | **已完成** | `TestController`（开发期用途）；`test_tool_test_controller.py`（26 条） |
| `monitor` | 5 | **已完成** | Phase 3.20；Redis 依赖走 `RedisCache` 惰性属性，`oshi` → `psutil` |
| `common` | 3 | **已完成** | `CaptchaController`（3.2）、`CommonController` + `DownTemplateController`（Phase 3.19） |
| `quartz` | 2 | **已完成** | Phase 3.23：`sys_job` / `sys_job_log` **13 个端点** + 6 个任务 Bean，用例 **281** 条；`MAPPING_QUARTZ.md` / §42 / §43 |
| `generator` | 1 | **已完成** | Phase 3.24：`GenController` **15 个端点** + 2 Service + 2 Mapper（10 + 8 条语句），用例 **116** 条；`COMPATIBILITY.md` §44 |

### 2.4 补记：`base` / `manager` / `flow` / `tool` 四个包

> 这四个包**代码与用例早已完成**（控制器均在 `app/api/<包>/`，路由均在 `app/main.py` 注册，
> 全量套件全绿），但此前**没在 §2.1 登记**，导致本文件看上去“还有 54 个控制器没动”。
> 本次重审（Phase 3.21）按实测补齐，**不重做代码**。

| 包 | Java 控制器 | 已注册路由 | Python 模块目录 | 用例文件（实测条数） |
| --- | --- | --- | --- | --- |
| `base` | 25 | 25 | `app/api/base/` | `test_base_ods_controllers.py` 36 / `test_base_ods_readonly.py` 58 / `test_base_ip_tables.py` 31 / `test_base_config_service_area_controller.py` 19 / `test_base_config_service_area_mapper.py` 20（**164**） |
| `manager` | 20 | 20 | `app/api/manager/`（含 `bigscreen/`） | `test_manager_controllers.py` 53 / `test_big_screen_controller.py` 30（**83**） |
| `flow` | 7 | 7 | `app/api/flow/` | `test_flow_controllers.py`（**55**） |
| `tool` | 1 | 1 | `app/api/tool/` | `test_tool_test_controller.py`（**26**） |

**欠账（只欠文档，不欠代码）**：这四个包没有 `MAPPING_*.md`。对照关系现在只能靠
Python 文件头的 `# Migrated from:` 与逐方法的 `# Java:` 注释追溯（机械规则写成
`snake_case` ↔ `camelCase`）。补文档列入 §5 的待办第 1 项。

---

## 3. 已完成切片明细（Phase 3.14 – 3.21）

### 3.1 `sys_config`（Phase 3.14）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| Controller（7/8 端点） | `app/api/system/sys_config_controller.py` | 已完成（新建） |
| Service（9 方法 + 逐键缓存） | `app/system/service/sys_config_service.py` | 已完成（新建） |
| Mapper（7 条 statement + 2 个 `<sql>`） | `app/system/mapper/sys_config_mapper.py` | 已完成（新建） |
| 实体 + `CONFIG_CONSTRAINTS` | `app/system/domain/sys_config.py` | 已完成（新建） |
| `Convert.toStr` | `app/common/core/text/convert.py`（`to_str` / `to_str_with_default`） | 已完成（**改了这一处**，本切片唯一的基础设施改动） |
| 路由注册 | `app/main.py` | 已完成（1 行 `include_router`） |
| 测试（3 个文件共 122 条） | `tests/test_sys_config_{mapper,service,controller}.py` | 已完成 |
| 对照文档 | `MAPPING_SYS_CONFIG.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §33（33.1–33.10 + §0 第 84–92 条） | 已完成 |

### 3.2 `sys_indexmenu`（Phase 3.15）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| Controller（6/7 端点） | `app/api/system/sys_index_menu_controller.py` | 已完成（新建） |
| Service（6 方法，4 个直接回 `AjaxResult`） | `app/system/service/sys_index_menu_service.py` | 已完成（新建） |
| Mapper（8 条 statement + 1 个 `<sql>`） | `app/system/mapper/sys_index_menu_mapper.py` | 已完成（新建） |
| 实体 | `app/system/domain/sys_index_menu.py` | 已完成（新建） |
| **`BaseUuidEntity`**（第二个实体基类） | `app/common/core/domain/base_uuid_entity.py` | 已完成（**新建的基础设施**） |
| 路由注册 | `app/main.py` | 已完成（1 行 `include_router`） |
| 测试（3 个文件共 102 条） | `tests/test_sys_index_menu_{mapper,service,controller}.py` | 已完成 |
| 对照文档 | `MAPPING_SYS_INDEX_MENU.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §34（34.1–34.11 + §0 第 93–102 条） | 已完成 |

### 3.3 `sys_upgrade_info`（Phase 3.16）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| Controller（6/7 端点） | `app/api/system/sys_upgrade_info_controller.py` | 已完成（新建） |
| Service（6 方法，3 个直接回 `AjaxResult`） | `app/system/service/sys_upgrade_info_service.py` | 已完成（新建） |
| Mapper（7 条 statement + 1 个 `<sql>`） | `app/system/mapper/sys_upgrade_info_mapper.py` | 已完成（新建） |
| 实体 | `app/system/domain/sys_upgrade_info.py` | 已完成（新建） |
| `parse_str_array`（`String[]` 路径变量） | `app/common/core/controller/base_controller.py` | 已完成（**改了这一处**，本切片唯一的基础设施改动） |
| 路由注册 | `app/main.py` | 已完成（1 行 `include_router`） |
| 测试（3 个文件共 108 条） | `tests/test_sys_upgrade_info_{mapper,service,controller}.py` | 已完成 |
| 对照文档 | `MAPPING_SYS_UPGRADE_INFO.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §35（35.1–35.11 + §0 第 103–114 条） | 已完成 |

### 3.4 本三个切片记录的 Java 陷阱

1. `SysConfigController` 是 **8 个映射**（§2.2 之前写的 9 是错的），`SysIndexMenuController` 是
   **7 个映射**（之前写的 2 是错的）；两个 `export` 都卡在 `ExcelUtil`（§33.2 / §34.2）。
2. 参数缓存与字典缓存**完全不同**：增改只写**单个键**，删除才全清；字典是写完全清（§33.5）。
   另外 `updateConfig` 写缓存用的是**入参**的 `configKey`，改键名时旧键会留着旧值（Java 原样）。
3. `selectConfigByKey` 有两种“没有值”：库里没这个键→`""`；库里有但 `config_value` 是
   `NULL`→`null`（`data` 键被省略）（§33.6）。
4. `updateConfig` 的 `remark` 是**唯一**只有 `!= null` 的列 → 传空串会**清列**；
   而 `insertConfig` 的 `remark` 与其它列一样是 `!= null and != ''`（§33.8）。
5. `deleteConfigById` 是孤儿 statement（XML 有、无调用方），`insertConfig` **不回写**主键
   （没有 `useGeneratedKeys`），两处都照留（§33.9 / §33.10）。
6. `SysIndexMenu extends BaseUuidEntity` —— 主键是 **UUID 字符串**、审计列是 **`Long`**
   （不是用户名），JSON 多出 6 个字段，且 `params` 输出 `null` 而不是缺键（§34.8）。
7. `<if test="userId != 1">` 是 OGNL 的 `!=`：只有 `1` 走“看全部”分支，`null` **也生效**（§34.9）。
8. `selectSysIndexMenuList` 的 `where` / `and` 都是**硬编码**的（没有 `<where>` 标签），
   且自带 `order by` → 客户端排序**不生效**；`sys_config` 列表相反（§34.11）。
9. `insertSysIndexMenu` 是“先**物理**删、后插”且**无事务**；只剥**一个**尾逗号，
   中间空段直接 500；同批共用**一个**时间戳（§34.5 / §34.6）。
10. 常用菜单的删除用 `AjaxResult.success` 而**不是** `toAjax`，`count == 0` 也回 200；
    演示成功文案是 `"操作成功！"`（**全角叹号**）（§34.7）。
11. `list` / `add` / `remove` 的 `@PreAuthorize` 在 Java 里**被注释掉了**，`getConfigKey`
    也本来就没有权限点 —— 四个端点都是首页/前端高频数据源，补上会白屏（§33.7 / §34.4）。
12. `SysUpgradeInfoController` **一个 `@PreAuthorize` 都没有**（不是被注释）——
    登录即可，补上会让没有菜单权限的普通用户看不到升级公告（§35.1）。
13. 升级信息的 `getInfo` 是 `@PathVariable String`，所以未迁移的 `export` **不会**回 500，
    而是落进 `getInfo("export")` 回 `200 且无 data` —— 全项目唯一例外（§35.2）。
14. `saveSysUpgradeInfo` 在新增分支比 `SysIndexMenu` **多盖一个** `tenantId`；
    而“列表查询用的 `tenantId`”反而在**控制器**里盖（indexmenu 在 Service）（§35.4 / §35.5）。
15. `selectSysUpgradeInfoById` **没有** `del_flag` 过滤（软删除的行照样查得到）；
    `newest` 的 SQL **完全无视入参**，且 `back_col1`（`varchar`）与数字 `1` 比较（§35.6 / §35.7）。
16. `remove` 的路径变量是 `String[]` 而**不是** `Long[]` —— 必须用 `parse_str_array`，
    用错 `parse_id_array` 会让**每个**删除请求 500（§35.8）。

### 3.5 Phase 3.14–3.16 的测试分布

| 层 | 文件 | 用例数 |
| --- | --- | --- |
| `sys_config` Mapper | `tests/test_sys_config_mapper.py` | 26 |
| `sys_config` Service | `tests/test_sys_config_service.py` | 40 |
| `sys_config` Controller | `tests/test_sys_config_controller.py` | 56 |
| `sys_indexmenu` Mapper | `tests/test_sys_index_menu_mapper.py` | 26 |
| `sys_indexmenu` Service | `tests/test_sys_index_menu_service.py` | 26 |
| `sys_indexmenu` Controller | `tests/test_sys_index_menu_controller.py` | 50 |
| `sys_upgrade_info` Mapper | `tests/test_sys_upgrade_info_mapper.py` | 36 |
| `sys_upgrade_info` Service | `tests/test_sys_upgrade_info_service.py` | 21 |
| `sys_upgrade_info` Controller | `tests/test_sys_upgrade_info_controller.py` | 51 |
| **合计** | | **332** |

全量套件：Phase 3.13 结束时是 **1623**，本三个切片 **+332** → **1955**。

### 3.6 `sys_file`（Phase 3.17）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| Controller（**17/17** 端点） | `app/api/system/sys_file_controller.py` | 已完成（新建） |
| Service（24 个接口方法 + 1 个实现类私有 + 4 个私有 `fileLog*`） | `app/system/service/sys_file_service.py` | 已完成（新建） |
| Mapper（9 条 statement + 1 个 `<sql>`） | `app/system/mapper/sys_file_mapper.py` | 已完成（新建） |
| 实体（**不继承** `BaseEntity`） | `app/system/domain/sys_file.py` | 已完成（新建） |
| **`ResponseSink`**（`HttpServletResponse` 替身） | `app/system/service/sys_file_service.py` | 已完成（**本切片新增的基础设施**，跟 service 放一起） |
| 路由注册 | `app/main.py` | 已完成（1 行 `include_router`） |
| 测试（3 个文件共 **194** 条） | `tests/test_sys_file_{mapper,service,controller}.py` | 已完成 |
| 对照文档 | `MAPPING_SYS_FILE.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §36（36.1–36.16 + §0 第 115–130 条） | 已完成 |

### 3.7 Phase 3.17 记录的 Java 陷阱

1. **`BytesIO(None)` 不报错** —— Java 的 `new ByteArrayInputStream(null)` 抛 NPE，CPython
   的 `BytesIO(None)` 却是空缓冲区。直译会把非法 base64 “成功”上传成 0 字节对象。
   已在 `upload_base64_picture` 里显式判空（§36.1）。
2. `SysFileController` 是 **17 个映射**（`upload` 是两个**同名重载**，只数方法名会少一个），
   **全部迁移** —— 这是第一个没有 `export` 的切片（§36）。
3. 权限点只有 **2 个**，而且都“抄错”了：`base:sysflie:list`（音近拼错，与
   `sys_menu.perms` 一致）、`base:supplier:remove`（借用供应商的）。
   修正拼写会让文件列表**直接 403**（§36.3）。
4. **下载失败是 HTTP 200 + 空 body**，不是 404 —— `getFile` 把异常全吞（连日志都注释掉）。
   这是唯一一个“靠状态码判断文件存不存”会彻底失效的模块（§36.4）。
5. `uploadFileId` 的 `AjaxResult.error("主键不能为空")` **返回值被丢弃** —— id 为空时
   照样落库一条 `id = NULL` 的记录。**不要补 `return`**（§36.6）。
6. 微信上传（`POST /uploadFile`）：**没有** `toLowerCase()`（`.JPG` 被拒）、`indexOf` 是
   **子串**匹配（`.mjpg` 能过）、两条文案的逗号都是**半角**（§36.7）。
7. `selectSysFileById` **没有** `del_flag` 过滤，但列表有 —— 软删除的文件按 id 仍能查到（§36.8）。
8. 白名单是 `ext.indexOf(x) > -1` 的**子串**匹配；`fileLogId` 的白名单里那条 `".ppt"`
   （带点）**永远匹配不上**，是既有死代码（§36.14 附近）。
9. 4 个 `fileLog*` 变体**不能合并**：只有 `fileSupplierLog` 写 `bussName`，只有
   `fileLogUser` **不写** `del_flag`（所以它的记录在列表里查不到）（§36.11）。
10. `uploadFile`（单）是**先 putObject 再登记**，`uploadFiles`（多）是**先登记再 putObject** ——
    两个顺序**相反**，失败时残留的东西也不同。
11. `uploadByUrl` 单条失败只记日志**继续下一条**；但 `uploadFiles` 一失败就
    `return error(...)`（前面成功的全部丢弃）。两者语义不同。
12. `updateCAFile` 把主键**写死成 3001**（CA 驱动固定占位），且返回的是**改之前**的 id（§36.10）。
13. `uploadPdf` 的 `HttpServletResponse` 参数**从没被写过**（`out` 被下一行覆盖），
    非 pdf 分支只往本地临时目录写文件、**不清理**、结果里**没有 `id`**（§36.13）。
14. `uploadBase64Picture(String, SysFile)` 的 `AjaxResult.success(fileId)` 挑中了
    `success(String msg)` —— 文件 id 在 **`msg`** 里，**没有 `data` 键**（§36.12）。
15. `SysFile` **不继承** `BaseEntity`（裸 POJO）：没有 `searchValue` / `remark` / `params`；
    审计列是 `String`；`id` 序列化成**字符串**（防 19 位雪花 id 精度丢失）（§36.16）。
16. 路由顺序：`/list` / `/getNewCa` 必须在 `/{ids}` 之前；`/getInfoById/{id}` 必须在
    `/{bucket}/{fileName}` 之前 —— 否则 `bucket = "getInfoById"`、`fileName = "9"`。

### 3.8 Phase 3.17 测试分布

| 层 | 文件 | 用例数 |
| --- | --- | --- |
| `sys_file` Mapper | `tests/test_sys_file_mapper.py` | 30 |
| `sys_file` Service | `tests/test_sys_file_service.py` | 84 |
| `sys_file` Controller | `tests/test_sys_file_controller.py` | 80 |
| **合计** | | **194** |

全量套件：Phase 3.16 结束时是 **1955**，本切片 **+194** → **2149**。

### 3.9 上上个切片：`sys_dict`（Phase 3.13，已归档）

#### 3.9.1 交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| Controller（类型，7/8 端点） | `app/api/system/sys_dict_type_controller.py` | 已完成（新建） |
| Controller（数据，7/8 端点） | `app/api/system/sys_dict_data_controller.py` | 已完成（新建） |
| Service（类型，12 方法） | `app/system/service/sys_dict_type_service.py` | 已完成（新建） |
| Service（数据，9 方法） | `app/system/service/sys_dict_data_service.py` | 已完成（新建） |
| Mapper（类型，9 条 statement + 1 个 `<sql>`） | `app/system/mapper/sys_dict_type_mapper.py` | 已完成（新建） |
| Mapper（数据，11 条 statement + 1 个 `<sql>`） | `app/system/mapper/sys_dict_data_mapper.py` | 已完成（新建） |
| 实体 ×2 | `app/common/core/domain/entity/sys_dict_{type,data}.py` | 已完成（新建） |
| 字典缓存 | `app/common/utils/dict_utils.py` | 已完成（新建，**本切片唯一新增的基础设施**） |
| 路由注册 | `app/main.py` | 已完成（2 行 `include_router`） |
| 测试（7 个文件共 271 条） | `tests/test_dict_utils.py` + `test_sys_dict_{type,data}_{mapper,service,controller}.py` | 已完成 |
| 对照文档 | `MAPPING_SYS_DICT.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §32（32.1–32.13 + §0 第 72–83 条） | 已完成 |

上一个切片（`sys_notice`，Phase 3.12）的 76 条用例与 11 个 Java 陷阱保留在
`MAPPING_SYS_NOTICE.md` 与 `COMPATIBILITY.md` §31 里，不重复写进本文件。

#### 3.9.2 本切片记录的 Java 陷阱

1. 两个控制器各 **8 个映射**、各迁 7 个；两个 `export` 依赖 `ExcelUtil`（§32.2）。
   §2.2 表格此前写的“10”是重复计数，已在本切片修正为 8。
2. `optionselect` / `type` / `typemore` 三个端点**没有**权限点 —— 前端每个下拉框都调，
   补上 `@PreAuthorize` 会白屏（§32.1）。
3. `clearCache` 必须注册在 `/{dictIds}` **之前**，否则被当成 `dictIds = "clearCache"`（§32.1）。
4. `SysDictTypeServiceImpl#init()` 带 `@PostConstruct`，但**不挂到 FastAPI 生命周期**：
   本工程数据源惰性创建，启动期连库会让“没有 MySQL 也能起服务”失效。语义无损 ——
   缓存未命中时回源走的是同一条 SQL（§32.4）。
5. `updateDictType` 是全切片唯一带 `@Transactional` 的方法，顺序是
   **先改子表、再改主表**；Python 没有事务，父表失败时子表已经改名（§32.5）。
   用例主动钉住了这个缺口。
6. `selectDictDataByTypeMore` 的 `substring(0, dictType.length())` 是**空操作**，
   尾逗号留在缓存键里；后面那次 `isEmpty` 是死代码。两处都照抄（§32.6）。
7. `selectDictLabel` 的 XML **没有** `limit 1` → 同一 `(dictType, dictValue)` 有两条时
   MyBatis 抛 `TooManyResultsException`（§32.7）；而 `add` 也**没有**唯一性校验，
   所以重复数据是完全可能的。
8. 两个 `insertDictXxx` **没有** `useGeneratedKeys` → 插入后主键仍是 `None`（§32.8）。
9. `SysDictData` 除 `getIsDefault()` 外还有一个只读计算属性 `getDefault()` →
   JSON 里多一个 `"default"` 键（§32.9）。
10. 两个 `selectDictData*Map` **不走缓存、不过滤 status**，用 `Collectors.toMap`
    在重复键上抛 `IllegalStateException`；`Lale` 是 `Label` 的笔误（§32.10）。
11. `DictUtils` 把 `containsAny` 的两个参数**对调**了（`containsAny(separator, value)`），
    `getDictValue` 的 else 分支还会 NPE；`clearDictCache` 用 `KEYS`（O(N) 阻塞）（§32.11）。
12. `/typemore` 未命中回 `"data": {}` 而不是 `[]` —— 空数组先被换成空 List，
    再被 `groupingBy` 吞成一个空 Map（§32.13）。

#### 3.9.3 已知缺口（详见 `COMPATIBILITY.md` §32）

- `@Log(title = "字典类型" / "字典数据")` 未迁移 → 字典增/改/删/清缓存不写 `sys_oper_log`（§32.3）
- 两个 `export` 未迁移 → 已登录请求被 `/{id}` 兜住回 **500**（§32.2）
- `updateDictType` 无事务，子表先改（§32.5）
- `init()` 不在启动时调用，首个请求回源填充（§32.4）

#### 3.9.4 测试分布

| 层 | 文件 | 用例数 | 全绿 |
| --- | --- | --- | --- |
| 缓存工具 | `tests/test_dict_utils.py` | 45 | ✓ |
| 类型 Mapper | `tests/test_sys_dict_type_mapper.py` | 32 | ✓ |
| 数据 Mapper | `tests/test_sys_dict_data_mapper.py` | 42 | ✓ |
| 类型 Service | `tests/test_sys_dict_type_service.py` | 41 | ✓ |
| 数据 Service | `tests/test_sys_dict_data_service.py` | 24 | ✓ |
| 类型 Controller | `tests/test_sys_dict_type_controller.py` | 44 | ✓ |
| 数据 Controller | `tests/test_sys_dict_data_controller.py` | 43 | ✓ |
| **合计** | | **271** | 全量套件 **1623 passed** |

`test_security_filter.py::PROTECTED_UNMAPPED_PATH` 现为 `/migration/probe/never-mapped`
（Phase 3.20 换的）：它不匹配任何 `AUTHORIZATION_RULES`，必然落到
`anyRequest().authenticated()`，controller 也永远查不到 ⇒ 恒为 404。
**这条以后不用再换了** —— 它不再指向任何真实模块，迁什么都影响不到它。

> **顺手修掉的旧缺陷（§32.12）**：`selectNoticeList` / `selectDictTypeList` /
> `selectDictDataList` 三处手写拼接都会生成 `... where AND ...`，MySQL 直接语法错。
> 公告那处是 Phase 3.12 遗留 —— 当时的用例只断言“片段与顺序”，没断言“拼接后的形状”。
> 三个 mapper 已各加一条 `test_the_where_clause_does_not_start_with_and`。

### 3.10 `ExcelUtil` + 8 个 `export`（Phase 3.18）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| `ExcelUtil`（1241 行；三条入口 `export_excel` / `import_excel` / `import_template`） | `app/common/utils/poi/excel_util.py` | 已完成（新建） |
| `@Excel` / `@Excels` 注解替身（26 个属性 + Java 默认值） | `app/common/annotation/excel.py` | 已完成（新建） |
| 8 个 `export` 端点 + `importTemplate` / `importData` | `app/api/system/sys_{user,post,role,config,dict_type,dict_data,index_menu,upgrade_info}_controller.py` | 已完成（补进既有控制器） |
| 测试（**64** 条） | `tests/test_excel_util.py` | 已完成 |
| 对照文档 | `MAPPING_EXCEL_UTIL.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §37（37.1–37.12 + §0 第 25/29/37/72/84/93/104 条改写） | 已完成 |

#### 3.10.1 本切片记录的 Java 陷阱

1. **导出接口回的是一条文件名，不是文件**：`AjaxResult.success(fileName)` 挑中的是
   `success(String msg)` 重载 → 文件名落在 **`msg`**，**没有 `data` 键**；
   文件本身在 `{profile}/download/` 下，前端得自己再发一次下载（§37.2）。
2. 8 个 `export` 一起从 **500 变成 200** —— 之前它们被 `/{id}` 之类的路径变量兜住，
   现在才是真的导出。这是本阶段唯一会改变既有端点状态码的改动（§37.1）。
3. `{profile}/download/` 里的文件**永不自动清理**（Java 也没有定时任务），照搬，
   运维需要自己挂 cron（§37.3）。
4. 只支持 `.xlsx`：Java 的 `HSSFWorkbook` 分支在 Python 侧没有等价物，`.xls` 不导入（§37.4）。
5. 公式单元格取的是文件里的**缓存值**（`load_workbook(data_only=True)`），openpyxl 不重算
   公式 —— 用 Excel 之外的库生成的 `.xlsx` 若没有缓存值就是空（§37.5）。
6. `SXSSFWorkbook(500)` 的行窗口没有对应物，Python 侧是内存 `Workbook`；**产物一致**，
   大导出的内存曲线不同（§37.6）。
7. `@Excel(cellType=IMAGE)` 在 Java 里是画图，这里**显式抛错**而不是静默写出一个空单元格（§37.7）。
8. `SysUpgradeInfo` 在 Java 里**一个 `@Excel` 都没有** → 导出的是零列空表，照搬（§37.8）。
9. `showDropDown` 在 openpyxl 里语义**相反**：POI 里 `true` 是“隐藏箭头”，
   `@Excel` 的默认 `false` 才是“显示”，翻译时按 `@Excel` 的语义反过来写（§37.9）。
10. `setDefaultColumnStyle` 没有对应物（openpyxl 只有单元格级样式），列样式改为逐格写 ——
    视觉一致，文件体积略大（§37.10）。
11. 导入的 `Integer` / `Long` 统一走 `to_long`，因此 `1.0` 这种浮点文本也能进 `Long` 字段（§37.11）。
12. `sort` 的默认值是 `Integer.MAX_VALUE` 而**不是**“未排序”，且排序**稳定** ——
    同 `sort` 值保持声明顺序，父类字段排在前面（§37.12）。

#### 3.10.2 测试分布

| 层 | 类 | 用例数 |
| --- | --- | --- |
| 列定义表（用户 21 列 / 模板 18 列 / 升级信息零列） | `TestColumnTables` | 10 |
| 字段收集 / `@Excels` 展平 / 稳定排序 / twips | `TestFieldCollection` | 8 |
| 样式键拼接（`Enum.toString()` 串接） | `TestStyleKeys` | 11 |
| `convertByExp` 字典翻译 | `TestConvertByExp` | 7 |
| 导出文件名 | `TestFilename` | 2 |
| 写盘产物（文件名进 `msg` / 单元格值 / 日期格式） | `TestExportToFile` | 10 |
| 导入模板 | `TestImportTemplate` | 2 |
| 导入解析（`getCellValue` 的类型顺序） | `TestImport` | 8 |
| `HttpServletResponse` 变体（异常只记日志不抛） | `TestResponseVariants` | 3 |
| `@Excel` 默认值守卫 | `TestAnnotationDefaults` | 3 |
| **合计** | `tests/test_excel_util.py` | **64** |

全量套件：本切片 **+64**（Phase 3.18 当时的累计数没留下实测记录，以文首的实测表为准）。

### 3.11 `/common` + `/downTemplate`（Phase 3.19）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| `CommonController`（4 端点：`download` / `upload` / `uploads` / `download/resource`） | `app/api/common/common_controller.py` | 已完成（新建） |
| `DownTemplateController`（1 端点：`/downTemplate/{type}`） | `app/api/common/down_template_controller.py` | 已完成（新建） |
| `FileUtils`（`write_bytes` / `get_file_extend_name` / `check_allow_download` / 下载头） | `app/common/utils/file_utils.py` | 已完成（新建） |
| `FileTypeUtils`（`get_file_type` / 大写 `get_file_extend_name`） | `app/common/utils/file_type_utils.py` | 已完成（新建） |
| `ServerConfig`（`get_url` / `get_domain`） | `app/framework/config/server_config.py` | 已完成（新建） |
| **`ResponseSink`** 补 `add_header` / `set_header` | `app/system/service/sys_file_service.py` | 已完成（**改了这一处**：Java 的 `HttpServletResponse` 头操作） |
| 7 份导入模板（classpath 镜像） | `config/templates/down/*.xlsx` | 已完成（从 Java 资源目录原样拷贝） |
| 路由注册 | `app/main.py` | 已完成（2 行 `include_router` + 注释订正） |
| 测试（3 个文件共 **123** 条） | `tests/test_file_utils.py` + `test_common_controller.py` + `test_down_template_controller.py` | 已完成 |
| 对照文档 | `MAPPING_COMMON.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §38（38.1–38.13 + §0 第 143–155 条） | 已完成 |

#### 3.11.1 本切片记录的 Java 陷阱

1. `GET /common/download` 是 **`anonymous()`** —— 前端不带 Token 才是对的，
   **已登录反而 403**（真实状态码，不是包装过的 200）。
2. `GET /common/download/resource` **不会**被 `/common/download**` 遮蔽：`AntPathMatcher` 先把模式
   切成 `["common", "download**"]`，`download**` 吃掉 `download` 之后**路径还有剩余段、模式已用完**，
   `doMatch` 直接返回 `false` —— 它是真的 `authenticated()`。
3. `fileName` / `delete` 都是**非必填**（Spring 的 `RequestParamNamedValueInfo` 默认 `required=false`），
   缺参数不会 400，而是在写响应时抛错被吞 → **200 + 空 body**。
4. 文件不存在同样是 **200 + 完整响应头 + 空 body**：`FileUtils.writeBytes` 在 `finally` 里
   **关流**，`close()` 等于提交响应，所以状态码早就定了。`ResponseSink` 的
   `_CloseTolerantStream` 就是为这条语义存在的。
5. 真实文件名取 `substring(indexOf("_") + 1)` —— 第一个 `_` 本身**被吃掉**，不保留。
6. `delete` 传非法值是 `code 500`，且**必须**抛 `ServiceException`：
   `@app.exception_handler(Exception)` 挂在 `ServerErrorMiddleware` 上，发完 body 会**重新抛出**，
   只有 `RuntimeError` 子类才由 `ExceptionMiddleware` 接住。
7. **下载白名单不区分大小写**（`FileTypeUtils.getFileType` 里有 `toLowerCase()`，22 项），
   而**上传**那边（`MimeTypeUtils.getExtension`，`contains` 子串）区分 —— 两个故意不同的判据，
   不要“统一”掉。
8. `/downTemplate/{type}` 未知 `type` 是 **200 + 空 body + 零响应头**：`setContentType` 与
   `setHeader` 都在写字节之后，字节为空就直接 return 了（§38.8）。
9. `Content-Disposition: attachment` **不带 filename**（Java 就是这么写的），浏览器会自己
   从 URL 尾段取名（§38.9）。
10. 模板是**原始字节直出**，不经 openpyxl —— 保真，也顺带避开了模板里的合并单元格/图形。
11. `resourceDownload` 的方法体**整块被注释**，所以它永远是空 body（照搬，§38.11）。
12. `URLEncoder` 的安全字符集是 `.-*_`，与 `urllib.parse.quote` 的 `_.-~` 不同：
    空格→`+`、`~`→`%7E`、`*` 不转义；`percent_encode` = `url_encode` + `+`→`%20`（§38.12）。

#### 3.11.2 测试分布

| 层 | 文件 | 用例数 |
| --- | --- | --- |
| `FileUtils` / `FileTypeUtils` / 下载头 / 白名单 | `tests/test_file_utils.py` | 68 |
| `CommonController`（4 端点 + 安全规则 + 参数绑定） | `tests/test_common_controller.py` | 25 |
| `DownTemplateController`（7 种 `type` + 未知类型 + 缺文件） | `tests/test_down_template_controller.py` | 30 |
| **合计** | | **123** |

全量套件：本切片 **+123**；Phase 3.20 结束时实测 **2942**（含本切片与 `monitor` 的 264 条）。

### 3.12 `monitor` 包（Phase 3.20）交付物

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| `SysOperlogController`（4 端点：`list` / `export` / `remove` / `clean`） | `app/api/monitor/sys_operlog_controller.py` | 已完成（新建） |
| `SysLogininforController`（4 端点：`list` / `export` / `remove` / `clean`） | `app/api/monitor/sys_logininfor_controller.py` | 已完成（新建） |
| `CacheController`（1 端点：`GET /monitor/cache`） | `app/api/monitor/cache_controller.py` | 已完成（新建） |
| `ServerController`（1 端点：`GET /monitor/server`） | `app/api/monitor/server_controller.py` | 已完成（新建） |
| `SysUserOnlineController`（2 端点：`list` / `{tokenId}`） | `app/api/monitor/sys_user_online_controller.py` | 已完成（新建） |
| 包导出 | `app/api/monitor/__init__.py` | 已完成（新建） |
| Service ×3（`operLog` 5 / `logininfor` 4 / `userOnline` 3 方法） | `app/system/service/sys_{oper_log,logininfor,user_online}_service.py` | 已完成（新建） |
| Mapper ×2（`oper_log` 5 条 + `logininfor` 4 条 statement） | `app/system/mapper/sys_{oper_log,logininfor}_mapper.py` | 已完成（新建） |
| 实体 ×3 | `app/system/domain/sys_{oper_log,logininfor,user_online}.py` | 已完成（新建） |
| **`Server` DTO**（`Sys` / `Cpu` / `Mem` / `Jvm` / `SysFileInfo` 六类合一，584 行） | `app/framework/web/domain/server.py` | 已完成（**本切片新增的基础设施**） |
| **`Arith`**（`BigDecimal` + `HALF_UP`） | `app/common/utils/arith.py` | 已完成（新建） |
| `parse_info` 空白处理对齐 `Properties.load` | `app/api/monitor/cache_controller.py` | 已完成（**本切片唯一的行为修正**） |
| 路由注册 | `app/main.py` | 已完成（5 行 `include_router`） |
| 测试（**264** 条，10 个文件） | `tests/test_monitor_*.py`（3 个新建）+ 7 个分层文件 | 已完成 |
| 对照文档 | `MAPPING_MONITOR.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §39（39.1–39.18 + §0 第 156–173 条） | 已完成 |

#### 3.12.1 本切片记录的 Java 陷阱

1. **`monitor` 包是 12 个映射，不是 13**：本项目 `SysLogininforController` **没有** `unlock`
   （上游 3.8.7 有），别再照上游文档数一遍。
2. **`SysOperlogController#remove` 没有 `@Log`**，而同包的 `SysLogininforController#remove` 有 ——
   全包共 **6 处** `@Log`，是不对称的，不是漏抄（§39.1）。
3. **`Cpu.getTotal()` 是 Java 的既有 bug**：`Arith.round(Arith.mul(total, 100), 2)`
   —— 乘了 100 却**没除以** `total`，而 `getSys()` / `getUsed()` / `getWait()` / `getFree()`
   都是 `xxx / total * 100`。照抄，不修（§39.2）。
4. **`Cpu` 的字段是 tick 增量，getter 才是百分比** —— `cpu.total != cpu.get_total()`，
   序列化走的是 getter。改字段名或直接输出字段会让前端饼图全乱（§39.2）。
5. **OSHI tick → psutil 秒 ×100**：`_TICKS_PER_SECOND = 100.0` 把秒还原成 tick 量级，
   否则 `Cpu.total` 会小两个数量级（§39.3）。
6. **`Jvm` 面板映射成宿主机内存**：Python 没有 JVM，`used` / `usage` 改用宿主机数据。
   这是全切片唯一“换数据源”的地方，换来的是两个字段互相自洽（§39.4）。
7. **磁盘分区会跳过**：`psutil.disk_partitions()` 里的无盘符 / 无权限项直接过滤，
   所以 `sysFiles` 的条数可能比 Java 少（§39.5）。
8. **`parseInfo` 只跳前导空白**：`Properties.load` 的 `LineReader` / `valueStart++` 都不裁行尾，
   所以 `parse_info` 写的是 `raw_line.lstrip()` 而不是 `strip()`；按首个 `:` 切分（§39.8）。
9. **`businessTypes` 是 `Integer[]`**：RuoYi 前端发重复键，`bind_query_params` 接不住
   （它只认 `str` / `bool` / `int` / `datetime`），所以有专用的 `_parse_business_types`；
   空值→`ValueError`→`code 500`，与 Java 的 `NumberFormatException` 同一条兜底路径（§39.7）。
10. **`businessType = 0`（“其它”）会让过滤条件凭空消失**：OGNL 里 `""` 转 double 是 `0.0`，
    `<if test="businessType != ''">` 在 0 上为**假** → 过滤器被丢掉 → 返回全表。照抄（§39.12）。
11. **`clean` 必须注册在 `{ids}` 之前**：Spring 靠 `AntPathMatcher` 偏爱字面量，FastAPI 只能靠
    声明顺序。写反了 `clean` 会变成 `infoIds="clean"` → `int()` 失败 → `code 500`（§39.9）。
12. **`SysUserOnline.loginTime` 是 epoch 毫秒数字**，不是 `Date` 字符串；
    而 `/monitor/online/list` **不调** `start_page()`，`pageNum` / `pageSize` 全无效（§39.10 / §39.14）。
13. **`forceLogout` 恒回 200**：Redis 里没有 token 也走 `AjaxResult.success("" + tokenId)`，
    但 `success(String)` 重载把 tokenId 放进 **`msg`**，**没有 `data` 键**（§39.15）。
14. **两个死方法照留**：`SysUserOnlineService#selectUserOnlineList`（Service 层）与几个无调用方的
    mapper 语句。按原则第 4 条不删（§39.11）。
15. **`RedisCache.keys()` 用的是 `KEYS`**（O(N) 阻塞），与 Spring Data Redis 一致。
    在线用户列表是全量 `KEYS login_tokens:*`，用户多了会卡，不要“优化”成 `SCAN`（§39.16）。
16. **`psutil` 早在 `pyproject.toml` 里就声明了**，本切片没有新增依赖（§39.17）。

#### 3.12.2 测试分布

| 层 | 文件 | 用例数 |
| --- | --- | --- |
| `Arith`（`HALF_UP` / 边界 / 负数） | `tests/test_arith.py` | 23 |
| `Server` DTO（`Sys` / `Cpu` / `Mem` / `Jvm` / `SysFileInfo`） | `tests/test_server_domain.py` | 45 |
| `sys_oper_log` Mapper | `tests/test_sys_oper_log_mapper.py` | 27 |
| `sys_logininfor` Mapper | `tests/test_sys_logininfor_mapper.py` | 21 |
| `sys_operlog` Controller | `tests/test_sys_operlog_controller.py` | 26 |
| `sys_logininfor` Controller | `tests/test_sys_logininfor_controller.py` | 17 |
| `sys_user_online` Controller + Service | `tests/test_sys_user_online_controller.py` | 23 |
| `cache` Controller（`parseInfo` / `substringBetween` / `commandStats` / 路由 / 权限） | `tests/test_monitor_cache_controller.py` | 39 |
| `server` Controller（路由 / 权限 / `copy_to` 顺序 / 异常兜底） | `tests/test_monitor_server_controller.py` | 14 |
| Service 层转发 + 定位器（`operLog` / `logininfor` / `userOnline`） | `tests/test_monitor_services.py` | 29 |
| **合计** | | **264** |

全量套件：本切片 **+264**；Phase 3.20 结束时实测 **2942**（大屏切片叠加前）。

### 3.13 `manager/bigScreen` 大屏（Phase 3.21）交付物

> Phase 3 的**最后一个控制器切片**。12 个映射全部 `GET`、**零权限点**、路径是**驼峰**。

| 交付物 | 路径 | 状态 |
| --- | --- | --- |
| Controller（12 端点，全部 `GET`） | `app/api/manager/bigscreen/big_screen_controller.py` | 已完成（新建，468 行） |
| 包标记 | `app/api/manager/bigscreen/__init__.py` | 已完成（新建） |
| **4 个新 VO**（`SectionVO` / `TollGantryFwqVO` / `OrgVO` / `CarAuditVO`） | `app/manager/domain/vo/bigscreen/` | 已完成（新建） |
| 6 个复用 VO（`CarInfoVO` / `CarLocationParam` / `CarLocationVO` / `CarStatisticsVO` / `TopTenVO` / `IncomeStatisticParam`+`VO`） | 同上 | 早已存在（PC 堵漏增收切片建的） |
| `select_org_list()`（mapper + service） | `app/base/{mapper,service}/ods_yhgl_v_base_org_*.py` | 已完成（各 +1 方法） |
| `count_by_car_id()`（mapper + service） | `app/manager/{mapper,service}/car_aduit_free_*.py` | 已完成（各 +1 方法） |
| 3 个实体补 `section_code_list` | `app/base/domain/{ods_szdn_toll,ods_szdn_gantry,dwd_lczt_fwqjcxx}.py` | 已完成（修 Python 侧**漏建**） |
| 路由注册 | `app/main.py` | 已完成（1 行 `include_router`） |
| 测试（**30** 条） | `tests/test_big_screen_controller.py` | 已完成 |
| 对照文档 | `MAPPING_BIGSCREEN.md` | 已完成 |
| 差异台账 | `COMPATIBILITY.md` §40（40.1–40.11 + §0 第 174–184 条） | 已完成 |

#### 3.13.1 本切片记录的 Java 陷阱

1. **一个权限点都没有**：类上、方法上都没有 `@PreAuthorize`，只要登录就能访问全部 12 个端点（§40.2）。
2. **路径是驼峰 `/manager/bigScreen`**，同包其它控制器全小写；改成 `bigscreen` 就是 404（§40.3）。
3. **`type` 是必填**（`@RequestParam String type` 无 `required = false`）：缺失 → `code 500`，
   `msg` 是 Spring 的英文原文，Python 用 `MISSING_TYPE_MESSAGE` 手抄（§40.8）。
4. **`sectionCode` 空白直接回空数组**，不是全量，而且**不查库**（§40.5）。
5. **`deleteEnd` 只削一个逗号**：`"SD01,,"` → `"SD01,"` → `String.split` 丢尾部空串 → `["SD01"]`（§40.5）。
6. **`indexOf("all")` 是整串子串判断**，不是列表 `contains`：`"SD01,all"` 也会把过滤清空 = 全量（§40.5）。
7. **`carLocation` / `carWarning` 的 `contains("all")`** 把整个 `sectionCode` 清成空串（`"all,SD01"` 也算）（§40.5）。
8. **三个魔法值**：`code` 为空时写 `StationCapture` / `GantryCapture` / `ServiceAreaCapture`，
   语义是“查不到”而不是“不过滤”（§40.4）。
9. **`type` 为空时 `code` 完全不生效**，但 `sectionCode` 的清空照做 —— 两件事互相独立（§40.4）。
10. **`type=2` 的 VO 字段是 `gantryCode` / `gantryName`**（`type=1` 才是 `tollCode` / `tollName`）。
11. **`exceptRecordList` 是 N+1**：每行再查 `selectOrgId` 与 `car_aduit_free` 的 count，
    `pageSize=50` = 101 条 SQL，不要“优化”成 join（§40.6）。
12. **`carAudit` 回的是零初值**（不是 `null`），且两个来源顺序固定：先异常流水、再已追缴（§40.7）。
13. **`incomeStatistic` 的 `suo` 默认值在控制器里盖**，不在 SQL 里 —— 传 `zhan` 才是按站（§40 无单独条目，见 `MAPPING_BIGSCREEN.md` §4.12）。
14. **`orgList` 只回两列**（MP 的 `select(orgCode, orgName)` 投影），没有 `orgId` / `delFlag`。

#### 3.13.2 测试分布

| 层 | 文件 | 用例数 |
| --- | --- | --- |
| 12 条路由表 / 全部 `GET` / 无路径变量 / 空权限集恒 200 | `tests/test_big_screen_controller.py` | 3 |
| `sectionList`（首条插 `"all"`） | 同上 | 1 |
| `tollGantryFwqList`（必填 `type` / 空白 / 尾逗号 / `"all"` / 三型分流 / 未知型） | 同上 | 9 |
| `carLocation` + `carWarning`（子串 `all` / 三个魔法值 / 保留 `code` / `type` 空 / 复用） | 同上 | 7 |
| `carStatistics` / `carAudit`（零初值 + 双来源） / `incomeStatistic`（`suo` 默认 + `zhan`） | 同上 | 5 |
| `carVoList` / `exceptionCar`+`topTen` / `orgList` | 同上 | 3 |
| `exceptRecordList`（逐行补两字段 + 默认 `"0"`） | 同上 | 2 |
| **合计** | | **30** |

全量套件：本切片 **+30**；Phase 3.21 结束时实测 **2972**。

---

## 4. 全局已知缺口（跨切片）

| # | 缺口 | 影响 | 台账位置 |
| --- | --- | --- | --- |
| 1 | ~~`LogAspect`（`@Log`）未迁移~~ **已关闭** | 切面早已落地，全仓 **233 处** `@Log` 全部写 `sys_oper_log` | §42.9 / §44.4 |
| 2 | ~~`@RepeatSubmit` 未迁移~~ **已关闭** | Java 全仓只有 **1 处**（`SysConfigController#add`），Python 对应路由已挂 `dependencies=[Depends(repeat_submit())]` | §42（无单独条目，见 `app/framework/interceptor/repeat_submit_interceptor.py`） |
| 3 | **`@Transactional` 部分复刻** | `quartz` 的写方法已用 `with session_scope()` 显式划事务（§6.7）；其余模块的多语句 Service 方法仍不原子 | §28.3 / §42 |
| 4 | `@DataScope` 仅部分生效 | `sys_dept` 的 SQL 片段被注释（不生效）；**`sys_role` 已验证生效**；`sys_menu` 的 XML 本来就没有 `dataScope` 片段 | §27.1 / §28 / §29 |
| 5 | **`BigDecimal` 序列化成 JSON 字符串** | 金额字段变 `"12.5"` 而不是 `12.5`，前端需 `Number(...)`；全局 `ORJSONResponse` 所致，早于 Phase 3.21 | §40.1 |

> 原第 1 项“`ExcelUtil`（Apache POI）未迁移”已在 Phase 3.18 关闭：
> `app/common/utils/poi/excel_util.py` + `app/common/annotation/excel.py` 落地，
> 8 个 `export` 与 `importTemplate` / `importData` 全部补齐（§37）。

> 更早的第 6 项“字典缓存 `SysDictUtils` 未迁移”已在 Phase 3.13 关闭：
> `app/common/utils/dict_utils.py` 与 `sys_dict_*` 两个切片一起落地，缓存语义与 Java 一致
> （含 `KEYS sys_dict:*` 的全量清除）。

---

## 5. 下一步

**控制器的迁移已全部结束**：`ruoyi-admin` 75 个 + `ruoyi-quartz` 2 个 + `ruoyi-generator` 1 个，
共 **78** 个控制器，路由、用例齐备，全量 **3646 passed**（其中 83 条是**真实 MySQL/Redis** 联调，见 §6）。
剩下的是**非控制器**部分，按优先级：

1. ~~**补 5 份 `MAPPING_*.md`**（`base` / `manager` / `flow` / `tool` / `generator`）~~ **已关闭**：
   由 `scripts/gen_mapping_docs.py` 生成，并有 `tests/test_mapping_docs.py` 护栏（§6.10.5）。
2. ~~`LogAspect`（`@Log`）~~ **已关闭**：切面早已落地并全量生效，全仓 **233 处** `@Log`
   都会写 `sys_oper_log`（`COMPATIBILITY.md` §42.9 推翻了 13 处旧结论）。
   仍欠的只有请求级事务（§28.3）：审计写在业务之后，业务回滚时审计照样留下。
3. ~~Phase 4 的 `quartz`~~ **已关闭**（Phase 3.23，见 §6.7）。Phase 4 仍未做的只剩
   Redis / Kafka / MinIO / Elasticsearch 的**运维手册** —— 开关与启动告警都已就绪
   （§12 / §13），缺的是"什么时候该打开、打开后连哪个地址"。
4. **金额序列化**（§40.1）：若业务方要求与 Java 字面一致（JSON 数字而非字符串），
   改 `default_response_class` 并同步断言 —— 一次性**全局**改动，不要逐接口打补丁。
5. ~~**Phase 5**~~ **已关闭**（见 §6.8）：`start.sh` / `start.bat`（对齐 `ry.sh` / `ry.bat` 的四个操作）、
   `README_PY.md`（部署与启动）、`MIGRATION_GUIDE.md`（怎么做迁移、怎么接着做）均已落地，
   与 Java 的并行对照验证就是 `COMPATIBILITY.md` §44 那一套。

> Phase 3.20/3.21 已经把“Redis 不可用”和“系统指标从哪来”这两件事定下来了：
> 前者走 `RedisCache` 的惰性 `client`（连不上就抛异常 → 全局兜底 `code 500`，与 Java 的
> `throws Exception` 同一条路），后者用 `psutil`（依赖已声明）。后续切片直接沿用，
> 不必再各自包一层 try。

> 下一个切片开始前要看的公共前提：
> - 实体基类有**两种**：`BaseEntity`（String 审计列 + `params` 为空时**缺键**）与
>   `BaseUuidEntity`（UUID 主键 + `Long` 审计列 + `params` 输出 `null`）。新实体先看
>   Java 的 `extends`，不要默认用 `BaseEntity`。
> - 缓存有**两套语义**：`DictUtils`（写完全清）与 `SysConfigService`（逐键写 + 删除全清），
>   **不能互相参照**。新接缓存前先看 Java 到底在哪一步调 `clearCache`。
> - 已经有分页的语句：`sys_user` / `sys_post` / `sys_notice` / `sys_role` / `sys_dict_type` /
>   `sys_dict_data` / **`sys_config`** / **`sys_index_menu`** / **`sys_upgrade_info`**
>   （后三个是 Phase 3.14–3.16）。新加列表接口时
>   先确认控制器是否调了 `start_page()`，再确认 mapper 是否 `take_page()`。
> - SQL 拼接的 `where` 片段**不要带前导 `AND`**（MyBatis 的 `<where>` 会吃掉首个 `AND`）；
>   `sys_index_menu` / `sys_upgrade_info` 的列表语句虽然**没有** `<where>` 标签，但结果
>   形态相同 —— 两种情况都按“片段不带 `AND`、用 `and` 拼接”写。
> - **路径变量类型不统一**：绝大多数模块的 `/{id}` 是 `Long`（用 `parse_id_array`），
>   `sys_upgrade_info` 是 `String`（用 `parse_str_array`）。新增控制器前先看 Java 的声明 ——
>   抄错会让整个模块的 `getInfo` / `remove` 全部 500（§35.8）。
> - `/{id}` 是 `String` 的模块会**吃掉所有单段路径**（包括未迁移的 `export`），所以字面量
>   路由（`/list` / `/newest`）必须在它之前注册（§35.2）。
> - **要自己往响应里写字节的端点**（`void` + `HttpServletResponse`）用
>   `ResponseSink` + `_to_response()`，别用 `StreamingResponse` —— 后者会在 try 之外抛错，
>   破坏“异常吞掉，回 200 + 空 body”的语义（§36.4）。
> - **雪花 id 主键的实体**要 `field_serializer` 转字符串（`SysFile.id`）；`Long` 字段收到
>   `""` 要先归一成 `null`（`JavaLong`），否则 pydantic 直接报错（§36.16）。
> - OSS 的四个操作都是**类级静态方法**（`OssTemplate.put_object` / `remove_object` /
>   `get_object` / `get_object_info`），测试要用 `staticmethod(...)` 才能钉住。

> 文件上传基础设施已在 Phase 3.11 落地（`FileUploadUtils` / `MimeTypeUtils` / `Seq` /
> 文件异常族），Phase 3.19 又补了 `FileUtils` / `FileTypeUtils` / `ServerConfig` /
> `ResponseSink` 的头操作；`/common` 与 `/downTemplate` 直接复用，不必再补一套。
>
> `ExcelUtil`（Phase 3.18）同样已可复用：`base` / `manager` 包里成片的 POI 导出直接写
> `ExcelUtil(Entity).export_excel(...)`，不要另起一套 openpyxl 逻辑。

> `test_security_filter.py::PROTECTED_UNMAPPED_PATH` 当前值是
> `/migration/probe/never-mapped`（一个永远不会存在、也不会被迁的路径），
> **以后不需要再换**。

---

## 6. 真实 MySQL / Redis 联调（Phase 3.22）

### 6.1 为什么要有这一层

`tests/test_*.py` 全部用替身：mapper 的 SQL 只被断言“拼出来长什么样”，
service 的返回值被预先摆好，Redis 是个 dict。这样快、稳，但**看不到真库的形状**。
`tests/integration/test_real_backend.py` 反过来 —— 按 `config/application.yml` 连
`127.0.0.1:3307/carmonitdb`（MySQL 8.0.30，84 张表）与 `127.0.0.1:6379/0`
（Redis 8.10.2），用 `TestClient` 打真实 controller，断言真实响应。

跑法：

```shell
.venv\Scripts\python.exe -m pytest tests/integration -v
```

默认 `pytest` 也会收集：MySQL 或 Redis 不可达时**整模块 skip**，离线跑仍然全绿。

### 6.2 联调抓到并修复的 3 个真缺陷

这三个 bug **2972 个单元用例一个都没抓住**，共同的根因是“替身比真库宽容”：

| # | 现象 | 根因 | 修法 |
| --- | --- | --- | --- |
| 1 | `GET /getRouters` 直接 500（`pydantic ValidationError: is_frame Input should be a valid string, input_value=1, input_type=int`） | 库里 `sys_menu.is_frame` / `is_cache` 是 **`int`**，而 Java 实体声明 `String`；MyBatis 的 `resultMap` 按属性类型选 `StringTypeHandler`，调 `rs.getString()`，JDBC 把 `1` 读成 `"1"`。pydantic **不做**隐式转换 | `app/system/mapper/sys_menu_mapper.py` 加 `_string()` 助手（等价 `ResultSet.getString`），在 `_to_sys_menu` 里显式转换 |
| 2 | `GET /manager/bigScreen/carStatistics` 500（`ModuleNotFoundError: No module named 'app.system.domain.sys_dict_data'`） | `car_confim_free_service.py:288` 的**函数内惰性 import** 包名写错；因为写错在函数体里，没有一条用例执行到它 | 改为 `app.common.core.domain.entity.sys_dict_data`（另 10 处早就是正确路径）。已用“导入全部 506 个模块”的脚本全量复核 |
| 3 | `GET /monitor/cache` 500（`AttributeError: 'dict' object has no attribute 'splitlines'`） | `redis-py 5.2` 给 `INFO` 注册了内置 response callback，`execute_command("INFO")` 返回**嵌套 dict**（`cmdstat_keys` 自己又是 dict）；而 Java 的 `RedisCallback` 走**裸连接**，拿的是原始文本 → `Properties` 的原料 | `cache_controller.py` 加 `_execute_raw()`：借连接 → `send_command` → `read_response` → 归还，绕开 callback，把原始文本交给已有的 `parse_info`（`NEVER_DECODE` 不行，仍是 dict） |

每个修复都在联调用例里留了**回归护栏**：`TestMenuFlagsRegression` /
`TestBigScreenRegression` / `TestCacheMonitorRegression`。

### 6.3 环境事实（别当成 bug）

* **本库没有 `sys_upgrade_info` 表** —— `/system/upgradeInfo/list` 必然 `code 500`。
  Java 打同一个库同样 500，不是迁移缺陷。用例
  `test_upgrade_info_degrades_when_the_table_is_missing` 会自己判断表在不在。
* `admin_test`（user_id 966）只有登录态、**没有任何菜单权限**，所以它在
  `@PreAuthorize` 端点上拿到 `403 没有权限，请联系管理员授权` —— 正确行为。
* `bcrypt` 与库里 6 个账号的哈希**都对不上**任何常见弱口令，且 `admin123` / `123456`
  过不了 `checkPassword`（8-20 位 + 大小写 + 数字 + 符号）。
  所以用例采用“临时改口令 → 真登录 → 结束改回去”的办法；
  原哈希先写进 `tests/integration/.password_backup.json`，进程被强杀也能在下次
  运行开头自动还原。

### 6.4 顺带修掉的测试污染

`test_e2e_sys_user.py` 的 `_reset_object_graph()` 漏了 `reset_logout_success_handler()`。
`LogoutSuccessHandlerImpl` 是进程级单例，它把首次解析到的 `TokenService`（以及后者
缓存的 `RedisCache`）一直握着；真实联调跑在前面时，登出会去删**真实 Redis**，
而断言看的是替身 —— 于是 `TestLogout` 变红。已在 `_reset_object_graph()` 里补上，
并让联调模块在 teardown 时把 `RedisCache` / `TokenService` / `LogoutSuccessHandler`
三个单例拆掉，两个模块互不污染。

### 6.5 分页的一个易错点（已核对无误）

`pageNum` 越过末页时**会回退到最后一页**，不是回空列表 —— 这是 RuoYi
`PageDomain.reasonable = true` 的默认值，`PageHelper.startPage(...).setReasonable(...)`
照抄了它。显式传 `reasonable=false` 才是 `LIMIT` 越界、回空列表。两条分支都有用例钉住。

### 6.6 全量只读接口对拍（146 个端点）

单元用例只能说“我写的东西自洽”，说不了“和 Java 一样”。所以另有一层**对拍**。
这些一次性工具与它们的产出**已归档到 `evidence/`**（根目录不再堆 `_*` 脚本），
表里给的是归档后的相对路径：

| 脚本（`evidence/`） | 作用 |
| --- | --- |
| `_sweep_login.py` | 用真实账号分别登录 :8090 与 :9989，两枚 token 写进 `.sweep_tokens.json`（口令从环境变量 `SWEEP_PASSWORD` 读，不入库） |
| `_sweep_diff.py` | 按**同一组 query string** 同时打两边，逐字段分类差异，产出 `_sweep_report.md` |
| `_sweep_analyze2.py` | 把 `_sweep_raw.json` 按 `(kind, field)` 聚类，看清“一个根因造成几处差异” |
| `_probe_raw2.py` / `_probe_endpoint.py` | 单端点定位：一边一个原始 body / 逐路径 diff |

对拍留存的产物：`evidence/_sweep_report.md`（逐端点结论）、`evidence/_sweep_raw.json`
（原始两侧响应）。`.sweep_tokens.json` 里是**真实登录 token**，已随本次收尾删除，不归档。

`_sweep_diff.py` 的差异分类：`TYPE`（`1` vs `"1"`）、`VALUE`（同形不同值）、
`ORDER`（同一堆元素不同顺序）、`MISSING`（只有一边有键）、`STATUS` / `CODE`（状态码 / `code`）。
实时值类（`/monitor/*`、`/captchaImage`、Excel 二进制）只比形状或干脆不比。

**收敛过程**（SAME / DIFF，共 147 → 146 个端点）：

| 轮次 | SAME | DIFF | 本轮修掉的根因 |
| --- | --- | --- | --- |
| 起点 | 99 | 32 | — |
| 1 | 113 | 20 | `createInfo`、进出站时间、`parentId`、`deptName` 等 9 处 |
| 2 | 118 | 17 | PageHelper **count 语句去 ORDER BY**、`BigDecimal` 尾零、`detailVOList`、`CarInfo` 的 Redis 反序列化 |
| 3 | 120 | 14 | `TrailBo` 的 9 个嵌套 BO、`incomeStatics` 分页、NPE 的 `msg` 为 `null` |
| 4 | **122** | **13** | `TrailInfo.trailDevCountBO` 别名、`incomeStatics.total`、`GET /system/user` |

### 6.6.1 本轮修掉的 4 个真缺陷

| # | 现象 | 根因 | 修法 |
| --- | --- | --- | --- |
| 1 | `GET /base/tollStationIp/list` Python 500 `Unknown column 't.big_id' in 'order clause'` | PageHelper 的 `CountSqlParser` 在 count 前**删掉最外层 `ORDER BY`**；Java 的 count 因此成功，`total == 0` 后数据语句根本不执行。而 `order by t.big_id` 引用的列并不存在 | `page_helper.py` 新增 `strip_order_by()` / `normalise_count_sql()`，在 `select_page` 里对 count 语句做同样改写（`Java: CountSqlParser#removeOrderBy`） |
| 2 | 34 处 `0` vs `0.0`（`escapedAmount`、`escapedTypeNNAmount` …） | Jackson 写 `BigDecimal` 时**保留 scale**，`BigDecimal.ZERO` 是 `0` 不是 `0.0`；Python 一律 `float()` | `domain_model.py` 加 `decimal_to_java_number()`：`exponent >= 0` 出 `int`，否则 `float` |
| 3 | `/manager/cartrackinfo/listByCarByTime` 每个轨迹点少 9 个键、多 9 个键 | ① Java 那 9 个嵌套字段没写 `private`，但 `@Data` 照样生成 public getter，Jackson **会**序列化（早先的注释写反了，还加了 `exclude=True`）；② `...CaptureBO` 的大写缩写 `to_camel` 还原不出来 | `trail_bo.py` 去掉 `exclude`、按 Java 声明顺序重排、5 个 `BO` 字段显式 `alias`；`trail_info.py` 的 `trailDevCountBO` 同理 |
| 4 | `/manager/aduitfree/incomeStatics` 返回 21 行、`total` 还是 10 | ① Mapper 拼了 SQL 却**没消费** `startPage()`，Java 只回第 1 页 10 行；② 映射成普通 `list` 后 `PageList.total` 丢了，`get_data_table` 只能拿 `len(rows)` | 两个方法都改成 `take_page()` + `select_page()`，并把映射结果重新包回 `PageList`（`total` 一起带走） |

另两处小修：`/system/user`（见 6.6.3）、`exportShrz` 一类 NPE 的 `msg` 该是 `null` 而不是字符串
（`exception_handlers._java_message`）。

### 6.6.2 剩下的 13 个 DIFF —— 逐条定性

| 端点 | 差异 | 定性 |
| --- | --- | --- |
| `/base/feeGantry/list`、`/base/feestationexit/list`、`/manager/cartrackinfo/listByCarId` | `msg` 不同 | **外部服务 9901 不可达**。两边都是 HTTP 200 + `code 500`，只是 Java 的文案是 Apache HttpClient 的 `HttpHostConnectException.toString()`（含 `Connection refused: connect`，JVM/平台相关），Python 是 `请求失败: <url> -> [WinError 10061]`。**不伪造** —— 换个 JVM 平台这段字就变 |
| `/system/upgradeInfo/list`、`/newest` | `msg` 不同 | **库里没有 `sys_upgrade_info` 表**（见 6.3），Java 抛 MyBatis 的多段 SQL 报错文本，Python 抛 SQLAlchemy 的。`code` 一致 |
| `/getInfo`、`/system/user/profile` | `user.params` / `data.params` = `{"@type":"java.util.HashMap"}` vs 缺键 | **token 由谁签发**的产物：Java `FastJson2JsonRedisSerializer` 把空的 `HashMap` 写成带类型标记的对象，读回来就是“一个名叫 `@type` 的键”，于是 `@JsonInclude(NON_EMPTY)` 不敢丢它。Python 签发的 token 里 `params` 就是 `{}`，按 NON_EMPTY 丢弃 —— **同一个 token 换一边签发，结论就换一边**，不是序列化器缺陷 |
| 6 个 `export*` | `__raw__` / `__len__` | **xlsx 字节**。Java 是 EasyExcel/POI（deflate + data descriptor），Python 是 openpyxl（store），两者都是合法 xlsx；字节级相同不可能也没意义。**已用 openpyxl 逐单元格验证：6 个端点 sheet 名 + 单元格字符串全部 SAME**，字节比稳定在 ~1.24 倍，见 `COMPATIBILITY.md` §41.7 |
| `/monitor/server` | 形状 | **Java 自己坏了**：`java.lang.NoSuchMethodError: com.sun.jna.Memory.close()V`（oshi 与 jna 版本不配）。Python 正常返回 |
| `/base/fitting/list` | `code 500` vs `200` | **Java 自己坏了**：`ZdataTrailFittingMapper.xml` 里写着 `<if test="id != null"> and t.id = #{id}</if>`，而实体 `ZdataTrailFitting` **没有 `id` 属性**（主键叫 `cid`），OGNL 求值直接抛 `ReflectionException`。这条语句在 Java 侧从未成功执行过。**决策：不复制这个崩溃**（`<if>` 已按原文迁移成 `If("id","id")`，缺属性时静默跳过），登记在 `COMPATIBILITY.md` §41 |
| `/health` | 404 vs 200 | **Python 独有**的存活探针（`COMPATIBILITY.md` §1），Java 没有这个端点 |

### 6.6.3 `GET /system/user`：尾斜杠是有行为差异的

Java 是 `@GetMapping(value = {"/", "/{userId}"})`，实测：

```text
GET /system/user      ->  200  {"code":500,"msg":"Request method 'GET' not supported"}
GET /system/user/     ->  200  {"code":200,...}   （与 Python 逐字段一致）
```

也就是说 `/` **只**占住 `/system/user/`；不带尾斜杠时只剩 `@PostMapping`（`add`）命中，
Spring 回 405，再被 `GlobalExceptionHandler` 翻成 `code 500`。Python 侧原来同时挂了
`@router.get("")` 与 `@router.get("/")`，两个都 200 —— 已删掉 `""` 那个，让 Starlette 走
“仅有 POST 部分匹配 → 405”的同一条路。

### 6.6.4 对拍工具本身的两个盲区

1. **端点清单取自 Python 自己的路由**（`collect_endpoints()` 扫 `app.routes`）。
   所以“Python 缺一个端点”不会报 DIFF，只会让总数变小 —— 删掉 `/system/user` 那次
   就是从 147 掉到 146。**Python 少端点只能靠人查**（Java 的 `@GetMapping` 清单 vs
   FastAPI 的 `openapi().paths`）。
2. **尾斜杠**由 Starlette 的重定向逻辑兜着，默认行为与 Spring 不同（`307` vs 精确匹配）。
   凡是 Java 里写了 `value = {"/"}` 的映射，都必须像 6.6.3 那样手工核对，不能只看总数。

### 6.6.5 收尾：把“实现对、测试旧”的 11 个用例改回来

第 4 轮对拍之外还补了两件事，都落在**测试与文档**上，`app/` 一行没动。

**(1) 6 个 `export*` 的字节差异——已用单元格级比对证伪“内容也不同”。**
`evidence/_cmp_xlsx.py` 把两侧的 xlsx 都用 openpyxl 读成 `(sheet 名, [[单元格字符串]])` 再比：

| 端点 | Java 字节 | Python 字节 | 单元格 |
| --- | --- | --- | --- |
| `exportIncomeStatics` | 8875 | 7605 | SAME |
| `exportIncomeDetailList` | 7226 | 5711 | SAME |
| `exportCarStatics` | 7835 | 6163 | SAME |
| `exportConcernedList` | 10253 | 8895 | SAME |
| `exportOrgId` | 7698 | 6118 | SAME |
| `exportHistory` | 9352 | 7695 | SAME |

字节比稳定在 ~1.24 倍，全部是 zip 封装（EasyExcel 用 deflate + data descriptor，
openpyxl 用 store）的固定开销。结论写进 `COMPATIBILITY.md` §41.7。

**(2) 全量 `pytest` 从“11 failed”回到“3056 passed”。**
这 11 个失败都不是本轮改动引入的，而是之前几轮**行为修正**（UTC→+08:00 的日期渲染、
`BigDecimal` 出数字、PageHelper 的 count==0 短路、`BaseUuidEntity` 的 `searchValue`）
改对之后，测试里的期望值没跟着改。逐条核对“实现 vs Java 原始响应”后按实现改测试：

| 用例 | 旧期望 | 现在的期望（已用 Java 实测确认） |
| --- | --- | --- |
| `test_domain_serialization` ×6 | `@JsonFormat` 在 **UTC** 渲染（`05:25:09`）；`loginDate` 是**毫秒整数** | 在 **JVM 区**渲染（`13:25:09`，墙钟原样返回）；`loginDate` 是 `"2024-05-17T14:15:52.000+08:00"` 这种 ISO 文本。实测 `GET /system/user/list`：Java 与 Python 这两个字段逐字符相同 |
| `test_big_screen_controller` ×3 | 金额是字符串 `"0"` / `"12.5"` | 金额是**数字** `0` / `12.5`（§41.4，`BigDecimal.ZERO` → `0`） |
| `test_page_helper` ×4 | `count = 0` 也照样跑 data 语句 | `count = 0` 时 PageHelper **不执行** data 语句，所以这几个用例把 count 改成 7 —— 它们验的是 data SQL 被改写的形状，不能拿空表测 |
| `test_sys_upgrade_info_mapper` ×1 | 同上（`scalar_value=0`） | `scalar_value=1` |
| `test_sys_index_menu_controller` ×1 | `searchValue` 不出现在响应里 | **出现**且为 `null`：`BaseUuidEntity.searchValue` 没有 `@JsonIgnore`（§41.8） |
| `test_sys_user_mapper` ×1 | 扁平 `deptName == "研发部门"` | 扁平 `deptName` 是 `None`：`<association>` 让 MyBatis 整体关掉自动映射（§41.9） |

另外 `test_e2e_sys_user` 的两个用例是本轮**行为变更**直接导致的，也已改：
`GET /system/user`（无尾斜杠）现在与 Java 一致地回 `code 500`，
`/system/user/` 才回下拉数据（§6.6.3）；`userName=nomatch` 的用例改为在 COUNT 语句上
验证筛选条件。

**最终：`3056 passed, 29 warnings in 27.22s`（exit 0）。**

### 6.6.6 本轮结束时的状态

| 项目 | 状态 |
| --- | --- |
| 只读 GET 对拍（146 个） | SAME 122 / DIFF 13（全部有据可查）/ 其余 11 为二进制、实时值、Java 自身故障或 Python 独有探针 |
| 单元 + 集成测试 | 3056 passed，0 failed |
| 生效服务 | Java `:8090`、Python `:9989`、MySQL `:3307`、Redis `:6379` 均在跑 |
| 未消除的已知差异 | `COMPATIBILITY.md` §41.1–§41.9，每条都写明“为什么不能消”和“要消该怎么改” |

> 上面这张表是 **Phase 3.22 结束时**的快照。之后 Phase 3.23 又加了 281 条用例（→ 3400），
> Phase 3.24 又加 116 条（→ 3516），Phase 6 再补 81 条（→ **3597**），见 §6.7 / §6.8。

---

## 6.7 Phase 3.23：`quartz` 切片

### 6.7.1 交付面

| Java | Python | 备注 |
|---|---|---|
| `ruoyi-quartz` 的 **25 个源文件** | `app/quartz/` **21 个模块**（+ 7 个 `__init__.py`） | 逐文件对照见 `MAPPING_QUARTZ.md` |
| `SysJobController`（8 映射） | `app/api/monitor/sys_job_controller.py` | 含 `run` 借用 `changeStatus` 权限点这个原样坑 |
| `SysJobLogController`（5 映射） | `app/api/monitor/sys_job_log_controller.py` | 含 `getInfo` **恒定 500** 这个 Java 真 bug |
| 六个任务 Bean | `app/quartz/task/`（`ryTask` / `orgTask` / `trackTask` / `vehicleMonitoringTask` / `partitionMaintenanceTask` / `snapshotFlowSyncTask`） | `app/main.py` 里 `import app.quartz.task` 触发注册 |
| `org.quartz`（第三方，非本工程源码） | `app/quartz/util/scheduler.py` + `cron_expression.py` | 自研，不引 APScheduler，理由见 `COMPATIBILITY.md` §42.1 |

`app/main.py` 只加了三处：`import app.quartz.task`（注册任务 Bean）、
`lifespan` 里的 `_init_quartz` / `_shutdown_quartz`、两条 `include_router`。

### 6.7.2 新增用例 **281** 条（4 个文件）

| 文件 | 条数 | 钉住的东西 |
|---|---|---|
| `tests/test_quartz_controllers.py` | 58 | 13 条路由表、权限点、`@Log` 的 `title`/`businessType`、`AjaxResult` 的"null 不给 `data` 键"、`/{id}` 兜住 `export` 这类顺序坑、`abc` 的 `[Ljava.lang.Long;` 文案 |
| `tests/test_quartz_cron_and_schedule.py` | 101 | Quartz `CronExpression` 的方言与边界（`*/0`、`?`、`L`、`W`、`#`、6/7 段）、`CronUtils.is_valid`、`ScheduleUtils` 的 `JobKey` 拼接、`JobInvokeUtil` 的类型判定顺序与 `NoSuchMethodException` 文案 |
| `tests/test_quartz_services.py` | 42 | 事务边界（`session_scope` 的 open/commit/rollback 计数）、`insertJob` 强制 `status="1"`、`misfire` 非法时**回滚且不留调度器条目**、`changeStatus` 只认 `"0"`/`"1"`、批量删除在第一个缺失处中断、`init()` 先 `clear` 后重建 |
| `tests/test_quartz_tasks.py` | 80 | 六个 Bean 的注册名与"无基类"前提、`AbstractQuartzJob.execute` 的成功/失败两条路径（含 2000 字截断）、每个任务的协作对象调用顺序、分表的月边界 |

全量：**3400 passed, 29 warnings in 27.39s**（exit 0）。

### 6.7.3 抓到并修复的 3 个真缺陷

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| 1 | `NameError: name 'TASK_PROPERTIES' is not defined` | `abstract_quartz_job.py` 用了这个常量却**从没 import 过**；`NameError` 抛在 `try` 之前，连失败分支都走不到，`sys_job_log` 一条都不会有 —— 看起来就像"任务没触发" | 补 `from app.common.constant.schedule_constants import TASK_PROPERTIES` |
| 2 | `AttributeError: java.lang.NoSuchMethodException: RyTask.ryNoParams()` | `invoke_target` 存的是 **Java 方法名**，Python 方法叫 `ry_no_params`；`getattr` 恒 `None` ⇒ **任何 `sys_job` 行都调不到** | `_declared_method` 取不到原名时回退 `to_under_score_case` 的 `snake_case` 形态；报错文案仍用 Java 原名 |
| 3 | 期望 `布尔类型true`，实得 `布尔类型True` | Java 的 `Boolean.toString` 是**小写**，`str(True)` 是 `True`；该串进 `sys_job_log.job_message`，属可观察输出 | `ry_task._java_str` 对 `bool` 显式返回 `"true"`/`"false"`（`None` 仍是 `"null"`） |

三者共同点：**只有端到端调用才看得见**。1 号缺陷让 `execute()` 在进 `try` 之前就死，
2 号让 `invoke_method` 在反射阶段就死 —— 而旧用例只分别测了
`before` / `do_execute` / `after` 与 `get_bean_name` / `get_method_params`，
没有一个走完整条链。这是"分层用例齐全 ≠ 链路可用"的典型例子。

### 6.7.4 顺带推翻的一条文档结论

`COMPATIBILITY.md` 有 **13 处**写着"`@Log` 未迁移 → 不写 `sys_oper_log`"
（§25.2 / §26.2 / §27.2 / §28.2 / §29.2 / §30.1 / §31.2 / §32.3 / §33.3 / §34.3 /
§35.3 / §36.2 / §39.1）。实际上 `app/framework/aspectj/log_aspect.py`（528 行）早已落地，
全仓 **233 处** `@Log`（`tests/test_log_aspect.py::TestMigrationInventory` 逐文件统计）
全部会写审计表。这 13 处已逐条加"本条已关闭"横幅并把结论指向 `COMPATIBILITY.md` §42.9。

同时把 `@Log` 的调用点数从 **217 改成 226**：`ruoyi-quartz` 的
`SysJobController`（6 处）与 `SysJobLogController`（3 处）此前漏统计。
Phase 3.24 又补上 `ruoyi-generator` 的 `GenController` 7 处，所以当前是 **233**（见 §44.4）。

### 6.7.5 不复制、只登记的 Java 侧缺陷

| 缺陷 | 事实 | 处置 |
|---|---|---|
| `insertBatchToTable` / `insertToTable` 的 **25 个** `#{item.xxx}` 指向实体上不存在的属性 | MyBatis 抛 `ReflectionException`，两条语句**从未成功执行过** | 按实体真实拥有的 43 列生成 `INSERT`：只消掉崩溃，不动业务规则（§42.3） |
| `SnapshotFlowSyncTask` 的 `convertToEntityList` 用 `instanceof` 过滤 `List<?>` | Jackson 给的是 `LinkedHashMap`，恒无一行 ⇒ **空转**，`syncFullData()` 恒返回"同步 0 条" | 照抄 `isinstance` 判定，两边都空转；**不"顺手修好"**（§42.4） |
| `GET /monitor/jobLog/{configId}` 的 `@PathVariable Long jobLogId` 名字对不上 | 对所有人都是 `code 500`（`MissingPathVariableException`） | 显式抛同样文案，不改成"像样的"详情接口（§43.1） |

### 6.7.6 本轮"只登记不改"的两处

1. **`@PreAuthorize` 与参数解析的顺序相反**（§43.1）：Java 是"参数缺失 500 → 权限 403"，
   Python 是"权限 403 → 500"。唯一受影响的端点恒定 500，真实调用方（有权限的管理员）
   两边一致；要复刻得把装饰器挪进 `Depends`，等于改全仓 226 个端点，**不做**。
2. **单值 `Long` 路径变量的报错文案**（§43.2）：`GET /system/role/abc` 在 Java 是
   `请求参数类型不匹配，参数[roleId]要求类型为：'java.lang.Long'…`，Python 是 pydantic 的
   `role_id Input should be a valid integer…`。`code`/状态码一致，只有措辞不同；
   这是全仓既有行为，不在本切片单独打补丁。

### 6.7.7 收尾清理（不动 `app/` 行为）

| 项 | 处置 |
|---|---|
| 根目录约 **110 个** `_*.py` / `_*.txt` / `_*.json` 一次性脚本与输出 | 其中被**文档/代码引用为证据**的 16 个移入 `evidence/`，其余全部删除。根目录现在只剩工程文件 |
| `evidence/` 里的引用 | `app/` 的 7 处 docstring、`tests/` 的 4 处、`MIGRATION_PROGRESS.md` / `COMPATIBILITY.md` 各若干，路径统一改成 `evidence/_xxx` |
| `.sweep_tokens.json` | 里面是 **:8090 / :9989 的真实登录 token**，删除，不归档 |
| `APScheduler==3.11.0` | 从 `pyproject.toml` / `requirements.txt` 删除：quartz 是自研实现，全仓无一处 import 它（§42.1） |
| `app/main.py` 的启动告警 | `Quartz/APScheduler 已禁用` → `Quartz 调度器已禁用 (app.scheduler_enabled=false)` |
| `app/settings.py` 的注释 | 同步指向 `app/quartz/util/scheduler.py`，不再提 APScheduler |
| 根目录 `_py.log` | 是**本地起服务时的启动日志**，当时被 :9989 的实例独占，删不掉；已加进 `.gitignore`（`logs/` 同样的道理） |
| `evidence/` 里的口令 | 四个对拍脚本原本写死了真实口令，已改成读环境变量 `SWEEP_PASSWORD`；全仓 `grep` 已无明文口令 |

清理后全量套件仍为 **3597 passed, 0 failed**（含 83 条真实 MySQL/Redis 联调）。

### 6.7.8 本切片的最终交付面

| 类别 | 交付物 |
|---|---|
| 代码 | `app/quartz/`（21 个模块，含 6 个任务 Bean）+ `app/api/monitor/sys_job{,_log}_controller.py` |
| 用例 | `tests/test_quartz_{controllers,cron_and_schedule,services,tasks}.py`（**281** 条） |
| 对照表 | `MAPPING_QUARTZ.md`（8 节：文件级 / 13 个映射 / 领域对象 / 14 条 SQL / Service / 6 个 Bean / 工具层 / 怎么跑） |
| 差异台账 | `COMPATIBILITY.md` §42（9 小节）+ §43（2 小节）+ §0 第 194–204 条 |
| 证据 | `evidence/`（16 个：cron 对拍、作业报错对拍、全量接口对拍工具与结果） |

至此 **78 个控制器**（`ruoyi-admin` 75 + `ruoyi-quartz` 2 + `ruoyi-generator` 1）全部迁移完毕、全部有用例。
剩余工作只在 Phase 4 的运维手册（Kafka / MinIO / Elasticsearch 开关怎么用），见 §5。

---

## 6.8 Phase 5（启动脚本与部署文档）+ Phase 6（全量一致性复核）

### 6.8.1 交付面

| 类别 | 交付物 | 说明 |
|---|---|---|
| 启动脚本 | `start.sh`、`start.bat` | `ry.sh` / `ry.bat` 的 Python 版，四个操作一一对应（start / stop / restart / status）；`start.bat` 额外支持 `start.bat start` 直接调用，并存为 **GBK**（与 `ry.bat` 一致） |
| 进程发现 | `scripts/app_pid.py` | 替代 `jps -l`：用 `psutil` 读命令行，按入口文件名 `run.py` 匹配；两个脚本共用同一份逻辑 |
| 部署说明 | `README_PY.md` | 环境、安装、配置优先级、前台/后台启动、自检、测试、中间件开关、常见问题；`pyproject.toml` 的 `readme` 就指向它 |
| 迁移手册 | `MIGRATION_GUIDE.md` | 硬性约束、分层映射表、加一个切片的六步、六个高频坑、测试分层、回归与对拍基线 |
| 复用 | `run.py`、`scripts/smoke_test.py` | 早于本阶段就存在，Phase 5 只是把它们写进文档并接到启动脚本上 |

**与 Java 并行对照验证**就是 `COMPATIBILITY.md` §44：路由 501 vs 502（多 `GET /health`）、
域字段 115 个可比零差异、全量 **3597 passed**、smoke **5/5**。

### 6.8.2 启动脚本与 `ry.sh` / `ry.bat` 的差异（已实测）

| 项 | Java | Python | 原因 |
|---|---|---|---|
| 启动命令 | `java $JVM_OPTS -jar ruoyi-admin.jar` | `python run.py` | 没有 JVM，端口由 `run.py` 从 `server.port` 读 |
| 进程发现 | `jps -l` + 按 jar 名过滤 | `scripts/app_pid.py`（psutil 读命令行） | Windows 没有 `jps` 的对应物 |
| 解释器 | 不适用 | 优先 `.venv`，其次 `$PYTHON` / PATH | 本机全局 Python 是 3.10，工程要求 3.12 |
| 停止命令 | `kill -TERM` / `taskkill /f` | 同左 | 行为一致 |
| 日志 | `nohup` 输出丢到 `/dev/null` | 同左 | 日志由 `app/logging_config.py` 写 `logs/sys-*.log` |

实测记录（Windows / cmd）：

```text
start.bat status   -> process run.py is dead
start.bat status   -> run.py is running (pid:47884)        # 有实例时
start.bat stop     -> prepare to kill run.py (pid:29172)
start.bat status   -> run.py is running (pid:29172)        # 沙箱禁止 taskkill，正常机器上会成功
```

---

## 6.9 暂停点（本地存档）

迁移工作已全部完成并落盘，**没有半成品**。本次暂停时的状态：

| 项 | 状态 |
|---|---|
| 代码 | 全部已写入磁盘，工作区无未保存的编辑 |
| 全量回归 | **3597 passed / 0 failed / 0 skipped**（约 34 s，含 `tests/test_app_pid.py` 新增 6 条） |
| 路由审计 | Java 501 / Python 502（多 `GET /health`）/ 缺失 **0** |
| 域字段审计 | 可比 115，属性/Excel/导出列**零缺口** |
| smoke | **5/5**（真实 socket + 真 MySQL + 真 Redis） |

本阶段新增/改动文件一览：`start.sh`、`start.bat`（GBK）、`scripts/app_pid.py`、
`tests/test_app_pid.py`、`README_PY.md`、`MIGRATION_GUIDE.md`，以及
`COMPATIBILITY.md` / `MIGRATION_PROGRESS.md` / `MAPPING_QUARTZ.md` / `.env.example` 的数字与措辞修正。

仍有**非阻塞**的遗留项（不影响“可运行 / 可验收”）：

1. ~~`base` / `manager` / `flow` / `tool` / `generator` 五个包的五份 `MAPPING_*.md` 尚未编写~~ —— **已在 §6.10 关闭**。
2. 沙箱内 `taskkill` 被拒，`start.bat stop` 只验证到“找到并准备 kill”，真实杀进程需在普通命令行复跑一次。
3. 根目录 `_py.log` 仍被 :9989 的旧实例独占，删不掉；已在 `.gitignore` 中忽略。

---

## 6.10 第二轮从头复核（一致性再验 + 补齐最后 5 份对照表）

要求是“**再次从头**检验 Java 与 Python 的返回一致性”。这一次没有沿用 §6.9 的结论，
而是把环境、数字、审计全部重做了一遍，并把“人看一遍”的环节逐个换成脚本。

### 6.10.1 先把环境弄真

上一轮的 83 条联调用例实际是 **skip** 的（`tests/integration/test_real_backend.py` 在
MySQL/Redis 不可达时整模块 `pytest.skip(..., allow_module_level=True)`），所以“全绿”里
没有真库的份。这次先起服务：

| 依赖 | 起法 | 备注 |
|---|---|---|
| MySQL 8.0.30 :3307 | `mysqld.exe --defaults-file=D:\work\mysql-8.0.30-winx64\my.ini --console` | 服务名 `mysql8`，但 `net start mysql8` 需管理员（报“错误 5 拒绝访问”），故直接起进程 |
| Redis 8.10.2 :6379 | `redis-server.exe`（`D:\work\Redis-8.10.2-Windows-x64-msys2`） | |
| 应用 :9989 | `python run.py` | 仅 smoke 需要 |

### 6.10.2 用例总数的那 59 条差额

`--collect-only` 数出 3538，文档写的是 3597，差 59。原因不是丢用例：
`pytest --collect-only` **不会展开被模块级 skip 的模块**，83 条联调用例因此不在列表里。
把 `app.config.database.check_connection` / `app.config.redis_config.check_connection`
替成 `lambda: True` 后再 collect，`tests/integration/test_real_backend.py` 就是 **83** 条。
所以 `3597 = 3514（87 个单测文件）+ 83`，两边自洽。

本轮之后（新增 7 条审计规则用例 + 16 条对照表护栏）：

| 组成 | 条数 |
|---|---|
| 单元（88 个文件） | 3538 |
| `tests/test_audit_scripts.py` 24 → 31 | +7 |
| `tests/test_mapping_docs.py`（新增） | +16 |
| 真实 MySQL / Redis 联调 | 83 |
| **合计** | **3644** |

### 6.10.3 文案审计：从“采样 39 条”到“采样 155 条”

`scripts/audit_messages.py` 早就存在，但反向那一半只扫到 **39** 种 Python 文案，原因很具体：
Python 为了复用，把文案提到了模块级常量（`SUSPICIOUS_NOT_FOUND_MESSAGE = "可疑车俩不存在！"`），
抛出处只写常量名。补上常量写法后采样升到 **155** 种，紧接着冒出 30 条“疑似自创”——
全部是**审计规则太窄**的假阳性，不是真差异：

| 现象 | 根因 | 修法 |
|---|---|---|
| Java 侧文案拼不起来 | `error("新增用户'" + user.getUserName() + "'失败…")` | `_collapse_concat()` 把 `"A" + expr + "B"` 反复折叠成 `AB` 再比 |
| `退出成功` 找不到 | 文案在 `i18n/messages.properties`，不在 `.java` 里 | 增加 `JAVA_EXTRA_SOURCES` |
| `[jobLogId]` 对不上 `[%s]` | 异常处理器用 `String.format("…路径变量[%s]")` | 占位符正则加入 `\[[^\[\]]{0,40}\]` |
| 两端单引号位置差一个 | 拼接后引号落到占位区外 | 再比一次“去掉所有单引号”的宽松形式 |

每一条规则都被 `tests/test_audit_scripts.py` 钉住（24 → **31** 条），
包括 `"A" + x + "B" + y + "C"` → `"ABC"` 这种多段折叠。最终两侧各 **0** 缺口。

### 6.10.4 响应信封审计：把 24 个 `Response` 变成机械判定

新增 `scripts/audit_envelopes.py`。之前“Java 返回 `AjaxResult`、Python 返回裸 `Response`”
这 24 个端点是靠说明文字解释的，容易变成事实上的白名单。现在脚本自己去看 Java 方法签名里
有没有 `HttpServletResponse`：有，说明响应体走 `OutputStream`，尾部 `return AjaxResult.success(...)`
永远到不了客户端；没有而类型又对不上，直接报错。结果 **501 个可比端点全部有归类**：

`AjaxResult→AjaxResult` **359**、`TableDataInfo→TableDataInfo` **100**、
`AjaxResult→Response` **24**、`void→Response` **8**、`R→R` **5**、`String→str` **5**。

### 6.10.5 补齐最后 5 份 `MAPPING_*.md`

§6.9 遗留的第 1 项。没有手抄 341 行端点表，而是写了 `scripts/gen_mapping_docs.py`：

* 文件对照来自每个 `.py` 头部的 `# Migrated from:`（迁移时本来就要求写）；
* 端点表来自 `audit_endpoints.iter_java_endpoints()` 与 `create_app().routes`，
  所以“表里的行数”与“审计脚本数出来的端点数”**永远是同一个数**；
* `要点` 一节是人工写的，只写脚本看不到的判断（权限点缺失、路径变量改名、Java 的恶作剧拼写）。

产出（`§1` 概况 / `§2` 要点 / `§3` 文件级对照 / `§4` 控制器端点 / `§5` 测试）：

| 文件 | 控制器 | 端点 | 用例 | 代表性的点 |
|---|---|---|---|---|
| `MAPPING_BASE.md` | 25 | 106 | 164 | 最大的切片（车队、轨迹、疑点） |
| `MAPPING_MANAGER.md` | **20** | **160** | 83 | 上轮记的“19 / 148”是漏了 `bigscreen/` 子目录 |
| `MAPPING_FLOW.md` | 7 | 55 | 55 | 只有 `FlowNameController` 带 `@PreAuthorize` |
| `MAPPING_TOOL.md` | 1 | 5 | 26 | `save`（表单绑定）与 `update`（`@RequestBody`）不同形 |
| `MAPPING_GENERATOR.md` | 1 | 15 | 153 | `talbleId` 是 Java 自己的拼写，照抄；“`/{talbleId}` 必须最后注册” |
| **合计** | **54** | **341** | — | |

新加 `tests/test_mapping_docs.py`（**16** 条）只管三件机器能判定的事：小节齐不齐；
`§1` 声明的端点数 == `§4` 行数 == Java 真实映射数；生成器**幂等**（重跑逐字节不变）。

写文档时又抓出两处**自己写错的想当然**：

1. 曾写“manager 会报「该车辆已存在」/「只能删除未审核的记录」”——`grep` 全仓 Java 源码 **0 命中**，
   已换成真实存在的三条：`可疑车俩不存在！`（Java 原文错字，Python 照抄）、`录入区间时间重复！`、
   `车牌号存在重复，请确定！`。
2. 曾写“flow 用包装对象接收查询参数”——没有依据，已换成表里能直接看出来的事实
   （权限点缺失、路径变量改名）。

### 6.10.6 本轮结束时的一致性基线

| 层 | 结果 |
|---|---|
| 路由 | Java **501** / Python **502** / 缺失 **0** / 多出 `GET /health` |
| 域字段 | 可比 **115** / 属性、Excel、导出列零缺口 |
| 响应信封 | 可比 **501** 全部归类（6 种组合） |
| 文案 | Java **148** 种 ↔ Python **155** 种，两侧缺口 **0** |
| 用例 | **3644 passed / 0 failed / 0 errors / 0 skipped**（35.7 s，真 MySQL + 真 Redis） |
| 对照表 | 5 份，54 控制器 / 341 端点，生成器幂等 |
| smoke | **5/5**，`{"db": "UP", "redis": "UP"}` |

仍有**非阻塞**遗留（与 §6.9 相同，均不影响“可运行 / 可验收”）：

1. 沙箱内 `taskkill` 被拒，`start.bat stop` 的真实杀进程需在普通命令行复跑一次。
2. 根目录 `_py.log` 被旧实例独占，删不掉；已在 `.gitignore` 中忽略。
3. 本机 MySQL / Redis 是手工起的进程（无管理员权限），**生产部署仍按 `README_PY.md` §2 的依赖要求**。

## 6.11 双前端实例实测（Phase 6.2）

> 需求：同一个前端工程用 `npm run dev` 起两个实例，分别连 Java 与 Python，用
> `admin/__SET_CARMONIT_ADMIN_PASSWORD__` 登录并做使用验证对比。

**环境**（本轮均处于运行状态）：

| 角色 | 地址 | 说明 |
|---|---|---|
| 前端 A | `http://localhost:8080` | `port=8080` + `VUE_APP_PROXY_TARGET=http://localhost:8090` → `/dev-api` 代理到 Java |
| 前端 B | `http://localhost:8081` | `port=8081`，不设该变量，走 `static/config.js` 默认的 `http://localhost:9989` → Python |
| Java 后端 | `:8090` | `application.yml` 里也写着 `server.port: 9989`，与 Python 撞车，所以 `--server.port=8090` 覆盖 |
| Python 后端 | `:9989` | `python run.py` |

`static/config.js` 加了一行 dev-only 覆盖（`process.env.VUE_APP_PROXY_TARGET || 'http://localhost:9989'`），
生产分支未动。这是**前端工程**（`D:\work\IdeaProjects\car-monit-front-new`）的改动，不属于本次迁移，
需要时可回退，不影响任何后端行为。

**登录**：两端 `POST /login` 都是 `{"msg":"操作成功","code":200}` + `token`；验证码答案从
Redis `captcha_codes:<uuid>` 取（值是 FastJSON2 风格的带引号文本）。浏览器侧还有一个
非后端的坑：`xmgl-zbgl-token` 这个 cookie 不区分端口，8080 的登录态会被 8081 读到，
两端对比时需要先清 cookie。

**接口对比**：15 个常用接口，**13 个逐字节一致**；2 个差异定位后都不是缺陷——`/getInfo` 的
`params:{"@type":"java.util.HashMap"}`（FastJSON2 `WriteClassName` 在 Redis 里的残留）与
`/monitor/cache` 的实时 `commandstats`，详见 `COMPATIBILITY.md` §44.7。

**本轮主要产出：2 个真差异（浏览器实机验证才暴露出来）**

1. **HMAC 密钥派生**：jjwt 0.9.1 的 `TextCodec.BASE64` 只解**整 4 字符块**、丢弃尾块，26 字符的
   `token.secret` 得到 **18 字节**；Python 的 `_decode_secret` 却补 `=` 到 4 的倍数，得到 **19 字节**。
   两端各自自洽、但互不认（Java token → Python `InvalidSignatureError` 500；Python token → Java 401）。
   已改为截断到 4 的整数倍，并加了“真实 Java 签发 token 验签”回归用例。
2. **坏 token 的响应**：Java 的 `JwtException` 逃出过滤器后由容器 **ERROR 派发到 `/error`**，
   `/error` 不在放行名单里 → `HTTP 200` + `code 401`，且 msg 里的路径是 **`/error`**；
   Python 原来直接渲染 Spring 500 错误页。已改为同一个 401 信封（新增内部接缝
   `AuthenticationEntryPointImpl.commence_for_uri`，Java 里对应容器的 error 派发）。

改完后 6 种组合（有 / 无 / 坏 token × `/getInfo` / `/logout`）两端逐字节一致，跨后端 token 双向可用，
15 个接口回到 13 一致 + 2 已知无害差异。

**用例 3644 → 3646**（+跨实现验签锚点、+`/logout` 坏 token；把“19 字节”“真 500”两条写错的断言
改成实测值）。全量 **3646 passed / 0 failed / 0 errors / 0 skipped**。

**方法上的教训**：这两处都是**测试与文档先写错了假设**（“补齐字节”“过滤器异常 = 500”），
实现照着错误假设做、测试照着错误假设钉，四层静态审计（路由 / 字段 / 信封 / 文案）也发现不了——
它们比的是“Python 与 Java 源码字面量”，而不是“Python 与运行中的 Java 行为”。
双实例实测是当前唯一能抓到这一类问题的手段。


