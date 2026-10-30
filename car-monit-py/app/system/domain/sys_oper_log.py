# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysOperLog.java
"""操作日志记录 sys_oper_log / operation audit record.

写入方是 ``LogAspect``（本工程见 :mod:`app.framework.aspectj.log_aspect`），读取方是
``/monitor/operlog`` 的列表、导出、删除与清空。本模块只关心"读"的一面，但字段、
列宽、``readConverterExp`` 都与 Java 逐字一致，因为导出直接用它们。

``businessTypes`` 是**查询专用**的数组字段
------------------------------------------
Java 的 ``private Integer[] businessTypes`` **不落库**（``insertOperlog`` 里没有它），
只服务于列表接口的"业务类型 in (...)"条件。它在 JSON 里以 ``businessTypes: null``
出现（Jackson 默认序列化所有 getter）。

``operTime`` 的序列化格式与 ``BaseEntity`` 不同
----------------------------------------------
``operTime`` 带 ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``，所以是**字符串**；
而 ``BaseEntity`` 的 ``createTime`` / ``updateTime`` 也是同格式（见基类）。
两处都要写成字符串 —— 漏掉任何一个，前端表格里就会变成时间戳数字。

``status`` / ``businessType`` / ``operatorType`` 都是 ``Integer``
---------------------------------------------------------------
与 ``SysLogininfor.status``（``String``）**不是**同一类型。字典翻译用的是
``readConverterExp``，它按字符串比对：``"0"`` 能翻译成 ``"正常"``，但库里若存的是
``0`` 也照样能命中（``ExcelUtil`` 在比对前会 ``Convert.toStr``）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, List, Optional

from pydantic import field_serializer, field_validator

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity
from app.common.utils.json_utils import format_date_time, parse_date_time


class SysOperLog(BaseEntity):
    """Java: ``SysOperLog extends BaseEntity``."""

    #: 日志主键
    oper_id: Optional[int] = None
    #: 操作模块
    title: Optional[str] = None
    #: 业务类型（0其它 1新增 2修改 3删除 …）
    business_type: Optional[int] = None
    #: 业务类型数组 —— **查询用**，不落库、不插入
    business_types: Optional[List[int]] = None
    #: 请求方法（Java 全类名 + 方法名）
    method: Optional[str] = None
    #: 请求方式（GET / POST …）
    request_method: Optional[str] = None
    #: 操作类别（0其它 1后台用户 2手机端用户）
    operator_type: Optional[int] = None
    #: 操作人员
    oper_name: Optional[str] = None
    #: 部门名称
    dept_name: Optional[str] = None
    #: 请求url
    oper_url: Optional[str] = None
    #: 操作地址
    oper_ip: Optional[str] = None
    #: 操作地点
    oper_location: Optional[str] = None
    #: 请求参数
    oper_param: Optional[str] = None
    #: 返回参数
    json_result: Optional[str] = None
    #: 操作状态（0正常 1异常）
    status: Optional[int] = None
    #: 错误消息
    error_msg: Optional[str] = None
    #: 操作时间 -- Java ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    oper_time: Optional[datetime] = None

    #: ``@Excel`` 注解表，**顺序与 Java 字段声明顺序逐字一致**（共 16 列）。
    #: ``businessTypes`` 没有注解，所以不是一列 —— 导出时看不到它。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("oper_id", Excel(name="操作序号", cell_type=ColumnType.NUMERIC)),
        ("title", Excel(name="操作模块")),
        (
            "business_type",
            Excel(
                name="业务类型",
                read_converter_exp="0=其它,1=新增,2=修改,3=删除,4=授权,5=导出,6=导入,7=强退,8=生成代码,9=清空数据",
            ),
        ),
        ("method", Excel(name="请求方法")),
        ("request_method", Excel(name="请求方式")),
        ("operator_type", Excel(name="操作类别", read_converter_exp="0=其它,1=后台用户,2=手机端用户")),
        ("oper_name", Excel(name="操作人员")),
        ("dept_name", Excel(name="部门名称")),
        ("oper_url", Excel(name="请求地址")),
        ("oper_ip", Excel(name="操作地址")),
        ("oper_location", Excel(name="操作地点")),
        ("oper_param", Excel(name="请求参数")),
        ("json_result", Excel(name="返回参数")),
        ("status", Excel(name="状态", read_converter_exp="0=正常,1=异常")),
        ("error_msg", Excel(name="错误消息")),
        (
            "oper_time",
            Excel(name="操作时间", width=30, date_format="yyyy-MM-dd HH:mm:ss"),
        ),
    )

    @field_serializer("oper_time")
    def _serialize_oper_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        """Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``."""
        return format_date_time(value)

    @field_validator("oper_time", mode="before")
    @classmethod
    def _parse_oper_time(cls, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        return parse_date_time(value)


__all__ = ["SysOperLog"]
