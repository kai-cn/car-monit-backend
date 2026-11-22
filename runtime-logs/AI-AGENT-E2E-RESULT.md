# AI Agent 云 runner E2E 验收结果（LangGraph / LangChain）

> 日期：2026-11-21 · run `44776021567`（`.github/workflows/ai-agent-e2e.yml`，master 默认分支 dispatch）
> 触发：`framework=both`，两个 matrix job 并发执行

## 1. 流程合规性
1. 从 `car-monit-api-python`（`9afbba20`）创建 `ai-agent-langgraph` / `ai-agent-langchain` 两个分支；
2. 先写设计 + spec 文档，独立只读会话两轮审阅：第一轮 8 项 BLOCKED → 修订 → 最终 **APPROVED**；
3. 审阅通过后才按 spec 实现；
4. 云 runner E2E 实测完成。

## 2. 云 runner 结果
| 分支 | job | pytest | 覆盖率 | 真实 HTTP smoke |
|---|---|---|---|---|
| `ai-agent-langgraph` | `136425935186` | 12 passed | **77.60%**（门禁 70%） | `AI_AGENT_SMOKE_OK` |
| `ai-agent-langchain` | `136425934565` | 12 passed | **76.15%**（门禁 70%） | `AI_AGENT_SMOKE_OK` |

凭据安全：`CI_AI_AGENT_TOKEN` / `JWT_SECRET` / `HENGDA_SECRET` 以仓库 Secret 注入 step 级 env，
云日志中显示 `***`；LLM key 为空 → FakeModel，无外部 API 调用。

## 3. 实现要点（对照 Java 参考 springAi / agentScope2java）
* 共享层：工具目录（`GET /ai/agent/tools`）、车牌掩码、导出二次确认、审计记录、
  fail-closed 鉴权、Spring 错误体；与参考分支 G1–G6 中的 G2/G3/G4/G5/G6 对齐；
* 差异层：LangGraph 用显式 `StateGraph` + `ToolNode` + 条件边；
  LangChain 用 v1 `create_agent` + `state_schema` + middleware；
* 对外 HTTP 契约完全一致（`AgentQueryResponse` 字段 `answer/tool_calls/trace_id/rounds`）；
* 详见 `docs/ai-agent/FRAMEWORK-COMPARISON.md`。

## 4. 包升级
AI 依赖取 2026-11 当前稳定线：`langchain>=1.5,<2.0`、`langgraph>=1.0,<2.0`、
`langchain-openai>=1.8,<2.0`、`pydantic>=2.7,<3.0`；以 extras `ai` +
`requirements-ai.txt` 声明，不破坏原 110 业务路由。

## 5. 未做（如实记录）
* 未接真实 LLM（CI 用 FakeModel）；生产需配置 `AI_AGENT_API_KEY` 与 `AI_AGENT_BASE_URL`；
* SSE 流式事件（Java 参考分支 G1）未在本轮实现；当前为同步 `POST /chat` 等价接口；
* `InMemorySaver` 仅单实例；生产换 `PostgresSaver`/Redis 会话存储。
