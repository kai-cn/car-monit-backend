# -*- coding: utf-8 -*-

"""
@description 历史脚本 fake_model_v2.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python fake_model_v2.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

LangChain 官方 ``FakeListChatModel`` 只返回字符串，无法让 Agent 真正调用工具。


本类继承 ``SimpleChatModel``（官方测试基类），覆盖 ``_generate`` 返回带


``tool_calls`` 的 ``AIMessage``，这样 LangGraph/LangChain 的 agent 循环会按官方路径执行。





【Java 对照】JUnit ``@MockBean ChatModel`` 的 thenReturn 序列。
"""
from __future__ import annotations



from typing import Any, Iterator, Optional



from langchain_core.callbacks import CallbackManagerForLLMRun

from langchain_core.language_models.chat_models import SimpleChatModel

from langchain_core.messages import AIMessage, BaseMessage

from langchain_core.outputs import ChatGeneration, ChatResult





class FakeAgentModel(SimpleChatModel):

    """按预定序列返回 AIMessage（可含 tool_calls）的假模型。



    ``responses`` 每项可以是：

    * ``str`` → AIMessage(content=字符串)

    * ``AIMessage`` → 原样返回（用于注入 tool_calls）

    """



    responses: list[Any]

    i: int = 0



    @property

    def _llm_type(self) -> str:

        return "fake-agent-model"



    def _generate(

        self,

        messages: list[BaseMessage],

        stop: Optional[list[str]] = None,

        run_manager: Optional[CallbackManagerForLLMRun] = None,

        **kwargs: Any,

    ) -> ChatResult:

        item = self.responses[self.i % len(self.responses)]

        self.i += 1

        msg = item if isinstance(item, AIMessage) else AIMessage(content=str(item))

        return ChatResult(generations=[ChatGeneration(message=msg)])



    def _call(self, *args: Any, **kwargs: Any) -> str:

        item = self.responses[self.i % len(self.responses)]

        self.i += 1

        return item if isinstance(item, str) else str(getattr(item, "content", ""))

