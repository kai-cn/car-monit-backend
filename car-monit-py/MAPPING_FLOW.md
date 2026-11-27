# MAPPING_FLOW.md — 审批流（`com.ruoyi.web.controller.flow`） Java ↔ Python 对照表

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
| Java 控制器 | 7 | `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/` 下全部 `*Controller.java` |
| 端点 | 55 | 方法级注解展开后的条数（`value = {...}` 会展开成多条），与 `scripts/audit_endpoints.py` 的 Java 侧计数同源 |
| Python 控制器模块 | 7 | `app/api/flow/` |
| Domain 对照行 | 8 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Mapper 对照行 | 8 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Service 对照行 | 7 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| Util 对照行 | 1 | 按 `# Migrated from:` 反查到的 Java 文件行数（Mapper 的接口与 XML 分别计） |
| 测试 | 55 | 见 §5 |

## 2. 要点

1. 只有 `FlowNameController` 带 `@PreAuthorize`（`flow:flowname:*`），其余 6 个控制器共 48 个端点**完全没有权限点**（只受登录保护）—— Java 原文如此，不是漏搬。
2. 写操作都带 `@Log`，`title` 各不相同：我的申请 / 流程_当前节点 / 审核历史记录 / 系统消息处理人 / 系统内部消息 / 流程名称 / 流程节点。
3. 路径变量名不统一（`{ids}` / `{mid}` / `{billOid}` / `{id}`），Python 照抄；FastAPI 按名字取值，改名字会直接 422。
4. `FlowMessageInfoController` 的四个 `list*` 在 Python 里换成了可读名（`list_pending` / `list_messages` / `list_done` / `list_finished`），路径不变。

## 3. 文件级对照

### 3.1 api（7 行）

| Java | Python |
|---|---|
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowApplyInfoController.java` | `app/api/flow/flow_apply_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowCurrentNodeController.java` | `app/api/flow/flow_current_node_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowListController.java` | `app/api/flow/flow_list_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageDisposeController.java` | `app/api/flow/flow_message_dispose_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java` | `app/api/flow/flow_message_info_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowNameController.java` | `app/api/flow/flow_name_controller.py` |
| `ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowTemplateController.java` | `app/api/flow/flow_template_controller.py` |

### 3.2 domain（8 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/EntrustInfo.java` | `app/flow/domain/entrust_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowApplyInfo.java` | `app/flow/domain/flow_apply_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowCurrentNode.java` | `app/flow/domain/flow_current_node.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowList.java` | `app/flow/domain/flow_list.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageDispose.java` | `app/flow/domain/flow_message_dispose.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageInfo.java` | `app/flow/domain/flow_message_info.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowName.java` | `app/flow/domain/flow_name.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowTemplate.java` | `app/flow/domain/flow_template.py` |

### 3.3 mapper（8 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowApplyInfoMapper.java` | `app/flow/mapper/flow_apply_info_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowCurrentNodeMapper.java` | `app/flow/mapper/flow_current_node_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowListMapper.java` | `app/flow/mapper/flow_list_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/*.java` | `app/flow/mapper/flow_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowMessageDisposeMapper.java` | `app/flow/mapper/flow_message_dispose_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowMessageInfoMapper.java` | `app/flow/mapper/flow_message_info_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowNameMapper.java` | `app/flow/mapper/flow_name_mapper.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/mapper/FlowTemplateMapper.java` | `app/flow/mapper/flow_template_mapper.py` |

### 3.4 service（7 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowApplyInfoServiceImpl.java` | `app/flow/service/flow_apply_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowCurrentNodeServiceImpl.java` | `app/flow/service/flow_current_node_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowListServiceImpl.java` | `app/flow/service/flow_list_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowMessageDisposeServiceImpl.java` | `app/flow/service/flow_message_dispose_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowMessageInfoServiceImpl.java` | `app/flow/service/flow_message_info_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowNameServiceImpl.java` | `app/flow/service/flow_name_service.py` |
| `ruoyi-system/src/main/java/com/ruoyi/flow/service/impl/FlowTemplateServiceImpl.java` | `app/flow/service/flow_template_service.py` |

### 3.5 util（1 行）

| Java | Python |
|---|---|
| `ruoyi-system/src/main/java/com/ruoyi/flow/util/FlowConstant.java` | `app/flow/util/flow_constant.py` |

## 4. 控制器端点（55 个）

### 4.1 `FlowApplyInfoController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/flow/applyinfo/{ids}` | `—` | 我的申请 / DELETE |
| `export` | `—` | GET `/flow/applyinfo/export` | `—` | 我的申请 / EXPORT |
| `list` | `—` | GET `/flow/applyinfo/list` | `—` | — |
| `listAll` | `—` | GET `/flow/applyinfo/listAll` | `flow:applyinfo:list` | — |
| `getInfo` | `—` | GET `/flow/applyinfo/{id}` | `—` | — |
| `add` | `—` | POST `/flow/applyinfo` | `—` | 我的申请 / INSERT |
| `edit` | `—` | PUT `/flow/applyinfo` | `—` | 我的申请 / UPDATE |

### 4.2 `FlowCurrentNodeController`（10 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/flow/currentnode/{ids}` | `—` | 流程_当前节点 / DELETE |
| `export` | `—` | GET `/flow/currentnode/export` | `—` | 流程_当前节点 / EXPORT |
| `getInfoByBillId` | `—` | GET `/flow/currentnode/getInfoByBillId/{billOid}` | `—` | — |
| `list` | `—` | GET `/flow/currentnode/list` | `—` | — |
| `getInfo` | `—` | GET `/flow/currentnode/{id}` | `—` | — |
| `add` | `—` | POST `/flow/currentnode` | `—` | 流程_当前节点 / INSERT |
| `submitEntrustFlow` | `—` | POST `/flow/currentnode/submitEntrustFlow` | `—` | — |
| `submitReturn` | `—` | POST `/flow/currentnode/submitReturn` | `—` | — |
| `edit` | `—` | PUT `/flow/currentnode` | `—` | 流程_当前节点 / UPDATE |
| `saveFlowAuit` | `—` | PUT `/flow/currentnode/saveFlowAuit` | `—` | — |

### 4.3 `FlowListController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/flow/flowlist/{ids}` | `—` | 审核历史记录 / DELETE |
| `export` | `—` | GET `/flow/flowlist/export` | `—` | 审核历史记录 / EXPORT |
| `list` | `—` | GET `/flow/flowlist/list` | `—` | — |
| `listnew` | `—` | GET `/flow/flowlist/listnew` | `—` | — |
| `getInfo` | `—` | GET `/flow/flowlist/{id}` | `—` | — |
| `add` | `—` | POST `/flow/flowlist` | `—` | 审核历史记录 / INSERT |
| `edit` | `—` | PUT `/flow/flowlist` | `—` | 审核历史记录 / UPDATE |

### 4.4 `FlowMessageDisposeController`（8 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `removeFlowMessage` | `—` | DELETE `/flow/messagedispose/delmes/{mid}` | `—` | — |
| `szzdFlowMessage` | `—` | DELETE `/flow/messagedispose/szzdmes/{mid}` | `—` | — |
| `remove` | `—` | DELETE `/flow/messagedispose/{ids}` | `—` | 系统消息处理人 / DELETE |
| `export` | `—` | GET `/flow/messagedispose/export` | `—` | 系统消息处理人 / EXPORT |
| `list` | `—` | GET `/flow/messagedispose/list` | `—` | — |
| `getInfo` | `—` | GET `/flow/messagedispose/{id}` | `—` | — |
| `add` | `—` | POST `/flow/messagedispose` | `—` | 系统消息处理人 / INSERT |
| `edit` | `—` | PUT `/flow/messagedispose` | `—` | 系统消息处理人 / UPDATE |

### 4.5 `FlowMessageInfoController`（8 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/flow/messageinfo/{ids}` | `—` | 系统内部消息 / DELETE |
| `export` | `—` | GET `/flow/messageinfo/export` | `—` | 系统内部消息 / EXPORT |
| `exportShrz` | `—` | GET `/flow/messageinfo/exportShrz` | `—` | 导出审核日志 / EXPORT |
| `list` | `—` | GET `/flow/messageinfo/list` | `—` | — |
| `listxx` | `—` | GET `/flow/messageinfo/listxx` | `—` | — |
| `listyb` | `—` | GET `/flow/messageinfo/listyb` | `—` | — |
| `listyj` | `—` | GET `/flow/messageinfo/listyj` | `—` | — |
| `getInfo` | `—` | GET `/flow/messageinfo/{id}` | `—` | — |

### 4.6 `FlowNameController`（8 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/flow/flowname/{ids}` | `flow:flowname:remove` | 流程名称 / DELETE |
| `export` | `—` | GET `/flow/flowname/export` | `flow:flowname:export` | 流程名称 / EXPORT |
| `list` | `—` | GET `/flow/flowname/list` | `flow:flowname:list` | — |
| `listQuery` | `—` | GET `/flow/flowname/listQuery` | `—` | — |
| `getInfo` | `—` | GET `/flow/flowname/{id}` | `flow:flowname:query` | — |
| `add` | `—` | POST `/flow/flowname` | `flow:flowname:add` | 流程名称 / INSERT |
| `tbFlow` | `—` | POST `/flow/flowname/tbFlow` | `flow:flowname:edit` | 同步其他单位的工作流 / UPDATE |
| `edit` | `—` | PUT `/flow/flowname` | `flow:flowname:edit` | 流程名称 / UPDATE |

### 4.7 `FlowTemplateController`（7 个映射）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `remove` | `—` | DELETE `/flow/flowtemplate/{ids}` | `—` | 流程节点 / DELETE |
| `export` | `—` | GET `/flow/flowtemplate/export` | `—` | 流程节点 / EXPORT |
| `flowlist` | `—` | GET `/flow/flowtemplate/flowlist` | `—` | — |
| `list` | `—` | GET `/flow/flowtemplate/list` | `—` | — |
| `getInfo` | `—` | GET `/flow/flowtemplate/{id}` | `—` | — |
| `add` | `—` | POST `/flow/flowtemplate` | `—` | 流程节点 / INSERT |
| `edit` | `—` | PUT `/flow/flowtemplate` | `—` | 流程节点 / UPDATE |

## 5. 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_flow_controllers.py` | **55** | 55 条端点逐条契约：路径、权限点、响应信封、参数校验 |
| 合计 | — | **55** | — |

用例数取自 `pytest --collect-only`（含参数化展开）。全量套件当前 **3646** 条（3563 单测 + 83 条真实 MySQL/Redis 联调），见 `MIGRATION_PROGRESS.md` §6.10。
