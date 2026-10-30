"""模板下载 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/DownTemplateController.java

**1** 个映射
------------
=================  ==============================  ==========
Java               Method / Path                    权限
=================  ==============================  ==========
``downExcel``      GET ``/downTemplate/{type}``    **无**
=================  ==============================  ==========

``SecurityConfig`` 里没有任何规则匹配 ``/downTemplate/**``，所以落到
``anyRequest().authenticated()`` —— **登录即可**，不查权限点。

``type`` -> 模板文件的白名单
---------------------------
===========================  =====================================
type                         模板
===========================  =====================================
``goodsFkApplyDetail``       ``importGoodsFkApplyDetail.xlsx``
``goodsRkApplyDetail``       ``importGoodsRkApplyDetail.xlsx``
``planListDetail``           ``importPlanListDetail.xlsx``
``importPsbz``               ``importPsbz.xlsx``
``importSupplierAnnualScore``  ``importSupplierAnnualScore.xlsx``
``carinfo``                  ``importCar.xlsx``
``carExcept``                ``importCarExcept.xlsx``
其他（含未知）                ``templates/down``（**是个目录**，读不到 -> 异常）
===========================  =====================================

未知 ``type`` **不会**报 404：``url`` 保持初值 ``"templates/down"``，``TemplateExportParams``
加载失败 -> ``catch`` 里 ``printStackTrace`` -> 返回 ``null`` -> **200 + 空 body**，
而且**没有任何响应头**（``setContentType`` / ``setHeader`` 都在 try 里、在异常点之后）。

``AjaxResult`` 返回值永远是 ``null``
-----------------------------------
方法签名是 ``public AjaxResult``，但方法体最后一句就是 ``return null``。写字节是直接
往 ``HttpServletResponse`` 的流里写的。Spring 对 ``null`` 返回值走
``HttpEntityMethodProcessor``/``RequestResponseBodyMethodProcessor`` 的
"returnValue == null -> 直接 return"，**不会**覆盖已经写好的响应。

Python 侧等价物：直接用 :class:`starlette.responses.Response` 装字节。

``easypoi`` 的 ``TemplateExportParams(url, true)`` + 空 ``HashMap``
-----------------------------------------------------------------
扫描全部 sheet、用空数据渲染模板，然后把 workbook 写出去。本项目这 7 个模板里
**没有任何** ``${...}`` 占位符（已逐格核对），所以"渲染"等于"原样输出"。
因此 Python 侧直接返回**模板原始字节** —— 内容与 Java 完全一致，而且不会像
``openpyxl`` 重写那样丢掉数据校验 / 表单控件（``importCarExcept.xlsx`` 的
"基础表请勿改动" sheet 就是给下拉框用的）。

模板位置：Java 是 classpath ``templates/down/``，Python 是 ``config/templates/down/``
（``config/`` 是 classpath 的镜像，见 :data:`app.settings.CONFIG_DIR`）。
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from fastapi import APIRouter
from starlette.responses import Response

from app.settings import CONFIG_DIR

logger = logging.getLogger("app.api.common.down_template_controller")

router = APIRouter(prefix="/downTemplate", tags=["down-template"])

#: Java: ``String url = "templates/down";`` —— 也就是 **classpath 根** 下的相对路径
TEMPLATE_DIR = "templates/down"

#: ``type`` -> 模板文件名。**顺序与 Java 的 if/else 链一致**（虽然查表不依赖顺序，
#: 但保持一致便于逐行 diff）。
TEMPLATE_BY_TYPE: Dict[str, str] = {
    "goodsFkApplyDetail": "importGoodsFkApplyDetail.xlsx",
    "goodsRkApplyDetail": "importGoodsRkApplyDetail.xlsx",
    "planListDetail": "importPlanListDetail.xlsx",
    "importPsbz": "importPsbz.xlsx",
    "importSupplierAnnualScore": "importSupplierAnnualScore.xlsx",
    "carinfo": "importCar.xlsx",
    "carExcept": "importCarExcept.xlsx",
}

#: Java: ``response.setContentType("application/octet-stream;charset=UTF-8")``
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream;charset=UTF-8"


def resolve_template_path(type_: str) -> str:
    """``type`` -> 磁盘路径. 未知 ``type`` 时返回**目录**路径（Java 同样如此）.

    返回目录路径而不是抛异常，是为了让"读文件失败"发生在与 Java 完全相同的位置
    （``ExcelExportUtil.exportExcel`` 里）。
    """
    relative = TEMPLATE_DIR
    file_name: Optional[str] = TEMPLATE_BY_TYPE.get(type_)
    if file_name is not None:
        relative = relative + "/" + file_name
    #: ``config/`` 是 classpath 根：``templates/down/x.xlsx`` -> ``config/templates/down/x.xlsx``
    return os.path.join(str(CONFIG_DIR), *relative.split("/"))


@router.get("/{type}", response_model=None)
def down_excel(type: str) -> Response:
    """通过 type 下载模板. Java: ``@GetMapping("/{type}") public AjaxResult downExcel(...)``.

    失败（未知 ``type`` / 模板文件缺失）时回 **200 + 空 body + 无响应头**，与 Java 一致。
    """
    path = resolve_template_path(type)
    try:
        with open(path, "rb") as template:
            content = template.read()
    except Exception:  # noqa: BLE001 - Java: catch (Exception e) { e.printStackTrace(); }
        # Java 是 ``e.printStackTrace()``（写 System.err，不经过日志框架）
        logger.error("模板下载失败: type=%s", type, exc_info=True)
        return Response(content=b"")

    return Response(
        content=content,
        headers={
            "Content-Type": OCTET_STREAM_CONTENT_TYPE,
            # Java: response.setHeader("Content-Disposition", "attachment") —— **没有 filename**
            "Content-Disposition": "attachment",
        },
    )


__all__ = [
    "OCTET_STREAM_CONTENT_TYPE",
    "TEMPLATE_BY_TYPE",
    "TEMPLATE_DIR",
    "router",
    "down_excel",
    "resolve_template_path",
]
