# MAPPING_TOOL.md — 开发脚手架（`com.ruoyi.web.controller.tool`） Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
>
> 表由 `scripts/gen_mapping_docs.py` 从源码生成（`# Migrated from:` 行 + 方法级注解 +
> `create_app()` 真正注册的路由），**手改会被下次生成覆盖**：要改就改代码，再重跑脚本。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md)。
>
> 阅读约定：
>
> - `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
>   逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
> - Python 用 `snake_case`，Java 用 `camelCase`，转换是机械的：
>   `selectJobList` → `select_job_list`。
> - `@Log` 列写成 `title / businessType`；`—` 表示 Java 侧没有该注解。
> - 权限点列写的是 `@PreAuthorize("@ss.hasPermi('...')")` 里的那个串；`—` 表示没有权限注解
>   （只受「登录」保护）。
> - 路径列写的是 **Java 的 URI 模板**；Python 侧路径变量按 PEP8 改成 snake_case
>   （`{jobId}` → `{job_id}`、`{IDs}` → `{ids}`），路由匹配结果不受影响。

---

## 1. 切片概况

| 项 | 数 | 依据 |
|---|---|---|
| Java 控制器 | 1 | `ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/` 下全部 `*Controller.java` |
| 端点 | 5 | 方法级注解展开后的条数（`value = {...}` 会展开成多条），与 `scripts/audit_endpoints.py` 的 Java 侧计数同源 |
| Python 控制器模块 | 1 | `app/api/tool/` |
| 测试 | 26 | 见 §5 |

## 2. 要点

1. `TestController` 是 RuoYi 自带的**演示用**控制器：不碰数据库、不碰 Redis，数据只在进程内存的 `LinkedHashMap<Integer, UserEntity>` 里。按迁移原则第 4 条「不擅自删除看似无用的 Java 代码」整块照搬，包括下面这些怪癖。
2. 5 个端点**全都没有权限点**：`SecurityConfig` 里没有一条规则命中 `/test/**`，落到 `anyRequest().authenticated()` —— 登录即可。
3. `POST /test/user/save` 的形参**没有** `@RequestBody`，Spring 按表单/query 绑定；发 JSON 会三个字段全 `null` 并回 `{"code":500,"msg":"用户ID不能为空"}`。照搬。
4. `PUT /test/user/update` 的形参**有** `@RequestBody`，读 JSON。两个写端点绑定方式不同，**不是不一致，是 Java 原文**。
5. 列表顺序是**插入顺序**（`LinkedHashMap`），`put` 已存在的键只改值、不动位置。

## 3. 文件级对照

### 3.1 api（1 行）

| Java | Python |
|---|---|
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java` | `app/api/tool/test_controller.py` |

## 4. 控制器端点（5 个）

### 4.1 `TestController`（5 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `delete` | `—` | DELETE `/test/user/{userId}` | `—` | — |
| `userList` | `—` | GET `/test/user/list` | `—` | — |
| `getUser` | `—` | GET `/test/user/{userId}` | `—` | — |
| `save` | `—` | POST `/test/user/save` | `—` | — |
| `update` | `—` | PUT `/test/user/update` | `—` | — |

## 5. 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_tool_test_controller.py` | **26** | 5 个端点：无权限点的鉴权边界、save 的表单绑定、内存 Map 的插入顺序与覆盖语义 |
| 合计 | — | **26** | — |

用例数取自 `pytest --collect-only`（含参数化展开）。全量套件当前 **3646** 条（3563 单测 + 83 条真实 MySQL/Redis 联调），见 `MIGRATION_PROGRESS.md` §6.10。
