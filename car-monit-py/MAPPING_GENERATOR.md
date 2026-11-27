# MAPPING_GENERATOR.md — 代码生成（`com.ruoyi.generator`） Java ↔ Python 对照表

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
| Java 控制器 | 1 | `ruoyi-generator/src/main/java/com/ruoyi/generator/controller/` 下全部 `*Controller.java` |
| 端点 | 15 | 方法级注解展开后的条数（`value = {...}` 会展开成多条），与 `scripts/audit_endpoints.py` 的 Java 侧计数同源 |
| Python 控制器模块 | 1 | `app/api/tool/` |
| Domain 对照行 | 8 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Mapper 对照行 | 2 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Service 对照行 | 4 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Util 对照行 | 4 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| 测试 | 153 | 见 §5 |

## 2. 要点

1. `GenController` 在 **`ruoyi-generator` 模块**（不在 `ruoyi-admin`），但路径挂在 `/tool/gen` 下 —— 与 `ruoyi-admin` 的 `TestController` 同属 `/tool` 前缀。
2. 两处路径变量**拼写就是 `talbleId`**（`GET /tool/gen/{talbleId}`、`GET /tool/gen/column/{talbleId}`）—— Java 原文的错别字，照抄不改；Python 侧只是改成了 `{talble_id}`。
3. `download` 与 `batchGenCode` 在 Java 里返回 `void`：zip 直接写响应流，Python 返回 `Response`（`audit_envelopes` 的 `void → Response` 之一）。
4. 15 个映射里 12 个带 `@PreAuthorize`；`all/list`、`getColumnList`、`getAllColumnList` 三个**没有**（登录即可）。`/{talbleId}` 必须**最后注册** —— 否则会把 `/list`、`/batchGenCode` 当成 id，在 `int()` 处 500。
5. 模板引擎没引 Apache Velocity，而是 `app/generator/util/velocity_engine.py` 的自研解释器（理由见 `COMPATIBILITY.md`）；`VelocityUtils` 的上下文拼装逐行照搬。

## 3. 文件级对照

### 3.1 api（1 行）

| Java | Python |
|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java` | `app/api/tool/gen_controller.py` |

### 3.2 domain（8 行）

| Java | Python |
|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/DictionaryInfo.java` | `app/generator/domain/dictionary_info.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenColumnDialog.java` | `app/generator/domain/gen_column_dialog.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTable.java` | `app/generator/domain/gen_table.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTableColumn.java` | `app/generator/domain/gen_table_column.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateRichTextInfo.java` | `app/generator/domain/generate_rich_text_info.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateUploadInfo.java` | `app/generator/domain/generate_upload_info.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/domain/LinkTableField.java` | `app/generator/domain/link_table_field.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/enumeration/LinkTableFiledTypeEnum.java` | `app/generator/domain/link_table_field.py` |

### 3.3 mapper（2 行）

| Java | Python |
|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableColumnMapper.java` | `app/generator/mapper/gen_table_column_mapper.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableMapper.java` | `app/generator/mapper/gen_table_mapper.py` |

### 3.4 service（4 行）

| Java | Python |
|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableColumnService.java` | `app/generator/service/gen_table_column_service.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableColumnServiceImpl.java` | `app/generator/service/gen_table_column_service.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableService.java` | `app/generator/service/gen_table_service.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java` | `app/generator/service/gen_table_service.py` |

### 3.5 util（4 行）

| Java | Python |
|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/enumeration/LinkTableFiledTypeEnum.java` | `app/generator/util/enumeration/link_table_filed_type_enum.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java` | `app/generator/util/gen_utils.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityInitializer.java` | `app/generator/util/velocity_engine.py` |
| `ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityUtils.java` | `app/generator/util/velocity_utils.py` |

### 3.6 config（1 行）

| Java | Python |
|---|---|
| `ruoyi-generator/src/main/java/com/ruoyi/generator/config/GenConfig.java` | `app/generator/config/gen_config.py` |

## 4. 控制器端点（15 个）

### 4.1 `GenController`（15 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/tool/gen/{tableIds}` | `tool:gen:remove` | 代码生成 / DELETE |
| `getAllGenerateTableList` | `—` | GET `/tool/gen/all/list` | `—` | — |
| `batchGenCode` | `—` | GET `/tool/gen/batchGenCode` | `tool:gen:code` | 代码生成 / GENCODE |
| `columnList` | `—` | GET `/tool/gen/column/{talbleId}` | `tool:gen:list` | — |
| `dataList` | `—` | GET `/tool/gen/db/list` | `tool:gen:list` | — |
| `download` | `—` | GET `/tool/gen/download/{tableName}` | `tool:gen:code` | 代码生成 / GENCODE |
| `genCode` | `—` | GET `/tool/gen/genCode/{tableName}` | `tool:gen:code` | 代码生成 / GENCODE |
| `genList` | `—` | GET `/tool/gen/list` | `tool:gen:list` | — |
| `preview` | `—` | GET `/tool/gen/preview/{tableId}` | `tool:gen:preview` | — |
| `synchDb` | `—` | GET `/tool/gen/synchDb/{tableName}` | `tool:gen:edit` | 代码生成 / UPDATE |
| `getInfo` | `—` | GET `/tool/gen/{talbleId}` | `tool:gen:query` | — |
| `getAllColumnList` | `—` | POST `/tool/gen/getAllColumnList` | `—` | — |
| `getColumnList` | `—` | POST `/tool/gen/getColumnList` | `—` | — |
| `importTableSave` | `—` | POST `/tool/gen/importTable` | `tool:gen:list` | 代码生成 / IMPORT |
| `editSave` | `—` | PUT `/tool/gen` | `tool:gen:edit` | 代码生成 / UPDATE |

## 5. 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_gen_controller.py` | **70** | 15 个端点：权限点、`@Log`、`talbleId` 拼写、`download`/`batchGenCode` 写流 |
| Mapper | `tests/test_gen_table_mapper.py` | **23** | `GenTableMapper` 10 条 statement 的 SQL 形状 |
| Mapper | `tests/test_gen_table_column_mapper.py` | **17** | `GenTableColumnMapper` 8 条 statement 的 SQL 形状 |
| Service | `tests/test_gen_table_service.py` | **43** | 五个 `init*` 的顺序、三段校验、导入的包装异常 |
| 合计 | — | **153** | — |

用例数取自 `pytest --collect-only`（含参数化展开）。全量套件当前 **3646** 条（3563 单测 + 83 条真实 MySQL/Redis 联调），见 `MIGRATION_PROGRESS.md` §6.10。
