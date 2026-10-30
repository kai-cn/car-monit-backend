"""交易流水（门架）控制器 —— Forest 代理直通.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java

**2** 个映射
------------
=====================  ==============================  ===========================
Java                   Method / Path                   权限点
=====================  ==============================  ===========================
``list``               GET ``/list``                   ``base:feeGantry:list``
``getInfo``            GET ``/{bigId}``                **无**（登录即可）
=====================  ==============================  ===========================

**没有** ``startPage()``
------------------------
数据不落本地库：``list`` 把实体原样当 query 传给 Forest 接口
``GET {vehicleMonitor.baseUrl}/base/feeGantry/list``，由上游分页。所以：

* 这里**不**调 ``start_page()``；
* 缺省值（``pageNum=1`` / ``pageSize=10``）是控制器自己补的，补完立刻发出；
* 返回的 ``TableDataInfo`` 是**上游的响应体原样转回**（``rows`` 里是裸 ``Map``，
  不转成 ``OdsLwzxsfsjFeeGantryFusion01``，Java 也没有转）。

``getInfo`` 同理，直接透传上游 JSON。

休眠代码
--------
Java 还 ``@Autowired`` 了 ``IOdsLwzxsfsjFeeGantryFusion01Service`` 和整个 ``export``
端点，**两者都没被用到**：前者没有任何调用点，后者整段被注释掉。按迁移规则保留说明，
不生成代码（本地库语句 ``selectOdsLwzxsfsjFeeGantryFusion01List`` 仍在
:mod:`app.base.mapper.ods_lwzxsfsj_fee_gantry_fusion01_mapper` 里）。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.base.domain.ods_lwzxsfsj_fee_gantry_fusion01 import OdsLwzxsfsjFeeGantryFusion01
from app.base.service.forest.http_ods_lwzxsfsj_fee_gantry_fusion01_service import (
    HttpOdsLwzxsfsjFeeGantryFusion01Service,
)
from app.common.core.controller.base_controller import bind_query_params
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.framework.web.service.permission_service import pre_authorize_permi

router = APIRouter(prefix="/base/feeGantry", tags=["base-fee-gantry"])


def _query(request: Request) -> OdsLwzxsfsjFeeGantryFusion01:
    """Java: 形参 ``OdsLwzxsfsjFeeGantryFusion01 q``（无 ``@RequestBody``）—— query 绑定."""
    return bind_query_params(OdsLwzxsfsjFeeGantryFusion01, request.query_params)


#: 查询条件实体（同时也是 Forest 的 ``@Query`` 对象）。
FeeGantryParam = Annotated[OdsLwzxsfsjFeeGantryFusion01, Depends(_query)]


def _client() -> HttpOdsLwzxsfsjFeeGantryFusion01Service:
    """Java: ``@Resource HttpOdsLwzxsfsjFeeGantryFusion01Service``.

    客户端的四个方法都是 ``@staticmethod``（Forest 的接口实现也是无状态的），
    所以这里没有需要缓存的单例，保留函数只为让调用点与 Java 逐行对齐。
    """
    return HttpOdsLwzxsfsjFeeGantryFusion01Service()


@router.get("/list", response_model=None)
@pre_authorize_permi("base:feeGantry:list")
def list_fee_gantries(query: FeeGantryParam) -> TableDataInfo:
    """查询交易流水列表. Java: ``@GetMapping("/list")``."""
    # 当前页面
    if query.page_num is None:
        query.page_num = 1
    # 分页大小
    if query.page_size is None:
        query.page_size = 10
    return _client().get_ods_lwzxsfsj_fee_gantry_fusion01_page(query)


@router.get("/{big_id}", response_model=None)
def get_info(big_id: str) -> AjaxResult:
    """获取交易流水详细信息. Java: ``@GetMapping(value = "/{bigId}")``."""
    return AjaxResult.success_data(_client().select_ods_lwzxsfsj_fee_gantry_fusion01_by_id(big_id))


__all__ = ["router", "FeeGantryParam", "get_info", "list_fee_gantries"]
