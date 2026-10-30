"""服务区基础信息.

# Migrated from: com/ruoyi/base/domain/DwdLcztFwqjcxx.java

字段顺序、类型、``@JsonFormat`` 形态与 Java 源文件逐行对应（Jackson 与
pydantic 都按声明顺序输出字段）。
"""

from __future__ import annotations

from typing import ClassVar, List, Optional

from app.common.annotation.excel import Excel, ExcelFields
from app.common.core.domain.domain_model import DomainModel


class DwdLcztFwqjcxx(DomainModel):
    """Java: ``com.ruoyi.base.domain.DwdLcztFwqjcxx``."""

    agent_pk: Optional[str] = None
    yxtzj: Optional[str] = None
    fwqbm: Optional[str] = None
    fwqmc: Optional[str] = None
    wd: Optional[str] = None
    fxmc: Optional[str] = None
    fxdm: Optional[str] = None
    jd: Optional[str] = None
    sslxbh: Optional[str] = None
    sslxmc: Optional[str] = None
    ssldbh: Optional[str] = None
    ssldmc: Optional[str] = None
    sczhkgs: Optional[str] = None
    sczhszgs: Optional[str] = None
    ssglzxbm: Optional[str] = None
    ssglzxmc: Optional[str] = None
    xzqhmc: Optional[str] = None
    yyrq: Optional[str] = None
    cws: Optional[str] = None
    sfszlkk: Optional[str] = None
    cdzs: Optional[str] = None
    sfcyfw: Optional[str] = None
    sftgzsfw: Optional[str] = None
    sftgqxfw: Optional[str] = None
    sftgcsfw: Optional[str] = None
    sftgjyfw: Optional[str] = None
    mj: Optional[str] = None
    sftgcshfw: Optional[str] = None
    xzqhdm: Optional[str] = None
    synx: Optional[str] = None
    lyxt: Optional[str] = None
    load_time: Optional[str] = None
    all_col_pk: Optional[str] = None
    #: 路线数组 —— ``@TableField(exist = false)``，只做查询入参，不进 SQL 的 select 列表
    section_code_list: Optional[List[str]] = None

    #: ``@Excel`` 注解表（顺序 = Java ``getDeclaredFields()`` 顺序）。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("yxtzj", Excel(name="源系统主键")),
        ("fwqbm", Excel(name="服务区编码")),
        ("fwqmc", Excel(name="服务区名称")),
        ("wd", Excel(name="纬度")),
        ("fxmc", Excel(name="方向名称")),
        ("fxdm", Excel(name="方向代码")),
        ("jd", Excel(name="经度")),
        ("sslxbh", Excel(name="所属路线编号")),
        ("sslxmc", Excel(name="所属路线名称")),
        ("ssldbh", Excel(name="所属路段编号")),
        ("ssldmc", Excel(name="所属路段名称")),
        ("sczhkgs", Excel(name="所处桩号(K格式)")),
        ("sczhszgs", Excel(name="所处桩号(数值格式)")),
        ("ssglzxbm", Excel(name="所属管理中心编码")),
        ("ssglzxmc", Excel(name="所属管理中心名称")),
        ("xzqhmc", Excel(name="行政区划名称")),
        ("yyrq", Excel(name="营业日期")),
        ("cws", Excel(name="车位数")),
        ("sfszlkk", Excel(name="是否设置了卡口")),
        ("cdzs", Excel(name="充电桩数")),
        ("sfcyfw", Excel(name="是否餐饮服务")),
        ("sftgzsfw", Excel(name="是否提供住宿服务")),
        ("sftgqxfw", Excel(name="是否提供汽修服务")),
        ("sftgcsfw", Excel(name="是否提供超市服务")),
        ("sftgjyfw", Excel(name="是否提供加油服务")),
        ("mj", Excel(name="面积(平方米)")),
        ("sftgcshfw", Excel(name="是否提供厕所服务")),
        ("xzqhdm", Excel(name="行政区划代码")),
        ("synx", Excel(name="使用年限")),
        ("lyxt", Excel(name="来源系统")),
        ("load_time", Excel(name="加载日期")),
        ("all_col_pk", Excel(name="全字段MD5")),
    )


__all__ = ["DwdLcztFwqjcxx"]
