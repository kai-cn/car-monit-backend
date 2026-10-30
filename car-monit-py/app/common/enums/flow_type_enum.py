"""Flow status enum.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/FlowTypeEnum.java

Java 侧由 Lombok ``@Getter`` + ``@AllArgsConstructor`` 生成三件套访问器：

    getCode()        -> ``int``      （注意是基本类型 int，不是 Integer）
    getCodeString()  -> ``String``
    getInfo()        -> ``String``

调用点大多是 ``FlowTypeEnum.APPROVE.getCode() + ""``（拼成字符串再与
``flow_apply_info.flow_status`` 比较），所以 :meth:`get_code` 必须返回 ``int``，
拼接语义才与 Java 一致；**不要**把它改成 :meth:`get_code_string`。
"""

from __future__ import annotations

from enum import Enum


class FlowTypeEnum(Enum):
    """流程状态（对应 ``flow_status`` 列）. """

    # Java: SUBMIT(1, "1", "起草中")
    SUBMIT = (1, "1", "起草中")
    # Java: APPROVE(2, "2", "审批中")
    APPROVE = (2, "2", "审批中")
    # Java: END(3, "3", "审批通过")
    END = (3, "3", "审批通过")
    # Java: RETURN(4, "4", "退回修改")
    RETURN = (4, "4", "退回修改")
    # Java: STOP(5, "5", "审批拒绝")
    STOP = (5, "5", "审批拒绝")

    def __init__(self, code: int, code_string: str, info: str) -> None:
        #: Java: ``private final int code``
        self.code = code
        #: Java: ``private final String codeString``
        self.code_string = code_string
        #: Java: ``private final String info``
        self.info = info

    # Java: public int getCode()
    def get_code(self) -> int:
        return self.code

    # Java: public String getCodeString()
    def get_code_string(self) -> str:
        return self.code_string

    # Java: public String getInfo()
    def get_info(self) -> str:
        return self.info


__all__ = ["FlowTypeEnum"]
