"""Flow business type enum.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/enums/FlowBusinessTypeEnum.java

对应 ``flow_name.flow_business_type`` 列。Java 侧 ``code`` 是 ``Integer``（包装类型，
**不是** ``FlowTypeEnum`` 的 ``int``），因此这里保留 ``int`` 值但方法名沿用
``get_code()``；由于该枚举在本工程里只被注释引用（``FlowName#flowBusinessType`` 的
javadoc），Python 侧同样只作类型说明，不参与任何判断。
"""

from __future__ import annotations

from enum import Enum


class FlowBusinessTypeEnum(Enum):
    """流程业务类型."""

    # Java: WORKFLOW(1, "1", "工作流类型")
    WORKFLOW = (1, "1", "工作流类型")
    # Java: BUSINESS(2, "2", "业务流类型")
    BUSINESS = (2, "2", "业务流类型")

    def __init__(self, code: int, code_string: str, info: str) -> None:
        #: Java: ``private final Integer code``
        self.code = code
        #: Java: ``private final String codeString``
        self.code_string = code_string
        #: Java: ``private final String info``
        self.info = info

    # Java: public Integer getCode()
    def get_code(self) -> int:
        return self.code

    # Java: public String getCodeString()
    def get_code_string(self) -> str:
        return self.code_string

    # Java: public String getInfo()
    def get_info(self) -> str:
        return self.info


__all__ = ["FlowBusinessTypeEnum"]
