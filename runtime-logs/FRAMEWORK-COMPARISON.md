<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# LangGraph vs LangChain 实现异同点（car-monit AI Agent）

> 两个分支从 `car-monit-api-python`（提交 `9afbba20`）分叉，功能与 HTTP 契约完全一致，
> 仅 Agent 编排层不同。本文是"Java 开发快速上手"的对照说明。

## 1. 共同点（框架无关层，两个分支语义一致）

| 维度 | 说明 |
|---|---|
| 对外契约 | `POST /ai/agent/query`、`POST /ai/agent/confirm`、`GET /ai/agent/tools`、`GET /ai/agent/health`；响应字段 `answer/tool_calls/trace_id/rounds` 完全一致 |
| 工具层 | 同一套 5 个 `@tool`（query_snapshot/group_stats/submit_export/export_status/es_status），调同一批 V3 Service，车牌掩码 + 导出二次确认 |
| 配置 | `AI_AGENT_MODEL` / `AI_AGENT_API_KEY` / `AI_AGENT_BASE_URL` / `AI_AGENT_MAX_ROUNDS` / `AI_AGENT_TIMEOUT_SEC` / `AI_AGENT_ACCESS_TOKEN` |
| 鉴权 | `X-Agent-Key` fail-closed；空 token 配置 → 503；错误 → 403；Spring 错误体 |
| 测试 | `tests/ai_agent/` 同名同契约测试；FakeModel 无需真实 LLM key |
| CI | `.github/workflows/ai-agent-e2e.yml`，云 runner pytest + 真实 HTTP smoke |

## 2. 核心差异

| 维度 | LangGraph 分支 (`ai-agent-langgraph`) | LangChain 分支 (`ai-agent-langchain`) |
|---|---|---|
| 心智模型 | 显式状态机：State + Node + Edge | `Agent = Model + Harness`（声明式工厂） |
| 编排入口 | `build_graph()` → `StateGraph(AgentState)` + `ToolNode` + 条件边 | `create_agent(model, tools, response_format, middleware, state_schema, checkpointer)` |
| 核心文件 | `app/ai_agent/graph.py` + `state.py` | `app/ai_agent/agent.py` + `middleware.py` |
| 状态扩展 | 自定义 `AgentState`（TypedDict），字段 `tool_calls_count/error` | `AgentRuntimeState(AgentState)`，字段 `rounds/tool_records` |
| 循环保护 | `should_continue` 条件边 + `tool_calls_count >= max_rounds → error` | `recursion_limit` + `TraceMiddleware.wrap_tool_call` 轮次截断 |
| 可观测性 | 在 `call_model` / API 层记录 | `TraceMiddleware`（`before_agent`/`wrap_tool_call`/`after_agent`）AOP 风格 |
| 结构化输出 | 由 API 层从最终 AIMessage 提取 | 原生 `response_format=AgentAnswer` → `structured_response` |
| 会话记忆 | `InMemorySaver` + `get_graph()` 单例 | `InMemorySaver` + `get_agent()` 单例 |
| 适用场景 | 需要显式分支/人工审批/复杂流程控制 | 快速交付标准 ReAct 类助手，减少样板代码 |

## 3. 对 Java 开发者的类比

| LangGraph | Java 类比 | LangChain | Java 类比 |
|---|---|---|---|
| `StateGraph` | Activiti/Flowable 流程定义 | `create_agent` | Spring `@Bean` 工厂方法 |
| `node` | `TaskDelegate` | `middleware` | `HandlerInterceptor` / AOP `@Around` |
| `add_conditional_edges` | `ExclusiveGateway` | `response_format` | Jackson 反序列化目标 DTO |
| `ToolNode` | 工具执行器 Service | `AgentState` 扩展 | 继承框架 Context 加业务字段 |

## 4. 为什么两个分支都保留

LangChain v1 的 `create_agent` 底层就是 LangGraph：
* 简单 Agent 用 LangChain 更省代码；
* 需要细粒度控制时用 LangGraph 显式图；
* 两个分支共享工具/API/测试契约，验证"框架可替换"（参考 Java 分支 G6）。
