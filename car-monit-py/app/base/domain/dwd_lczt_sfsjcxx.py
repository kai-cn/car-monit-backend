"""收费站基础信息.

# Migrated from: com/ruoyi/base/domain/DwdLcztSfsjcxx.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class DwdLcztSfsjcxx(DomainModel):
    """Java: ``com.ruoyi.base.domain.DwdLcztSfsjcxx``."""

    agent_pk: Optional[str] = None
    yxtzj: Optional[str] = None
    sfsbm: Optional[str] = None
    sfsmc: Optional[str] = None
    jd: Optional[str] = None
    wd: Optional[str] = None
    sslxbh: Optional[str] = None
    sslxmc: Optional[str] = None
    ssldbh: Optional[str] = None
    ssldmc: Optional[str] = None
    sczh_k: Optional[str] = None
    sczh_n: Optional[str] = None
    ssglzxbm: Optional[str] = None
    ssglzxmc: Optional[str] = None
    lyxt: Optional[str] = None
    load_time: Optional[str] = None
    all_col_pk: Optional[str] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("yxtzj", Excel(name="源系统主键")),
        ("sfsbm", Excel(name="收费所编码")),
        ("sfsmc", Excel(name="收费所名称")),
        ("jd", Excel(name="经度")),
        ("wd", Excel(name="纬度")),
        ("sslxbh", Excel(name="所属路线编号")),
        ("sslxmc", Excel(name="所属路线名称")),
        ("ssldbh", Excel(name="所属路段编号")),
        ("ssldmc", Excel(name="所属路段名称")),
        ("sczh_k", Excel(name="所处桩号(K格式)")),
        ("sczh_n", Excel(name="所处桩号(数值格式)")),
        ("ssglzxbm", Excel(name="所属管理中心编码")),
        ("ssglzxmc", Excel(name="所属管理中心名称")),
        ("lyxt", Excel(name="来源系统")),
        ("load_time", Excel(name="加载日期")),
        ("all_col_pk", Excel(name="全字段MD5")),
    )


__all__ = ["DwdLcztSfsjcxx"]
