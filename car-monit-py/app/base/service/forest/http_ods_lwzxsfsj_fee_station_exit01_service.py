"""收费站出口流水 —— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpOdsLwzxsfsjFeeStationExit01Service.java

Java 原文::

    @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
    public interface HttpOdsLwzxsfsjFeeStationExit01Service {
        @Get("/feestationexit/list")     JSONObject get...Page(@Query q);
        @Get("/feestationexit/{bigId}")  JSONObject select...ById(@Var String bigId);
    }

两处与其它三个客户端不同
------------------------
1. ``baseURL`` 末尾**多带了 ``/base``**，所以注解里的路径是 ``/feestationexit/...``；
   拼出来的地址与 ``/base/feestationexit/...`` 相同。
2. 返回类型是 hutool 的 ``JSONObject``（不是强类型实体）—— 控制器自己检查
   ``code == 200``，所以这里直接把解析后的 ``dict`` 交回去，不做任何校验。

``JSONObject`` 会把 **值为 null 的成员整个丢掉**，这条会一路透到 HTTP 响应里：
实测 ``/base/feestationexit/list`` 的 Java 响应一行都没有 null 键，而强类型实体的
``/manager/carinfo/list`` 两端都照发 111 个 null 键 —— 差别只在这个客户端。
所以解析完先递归删掉 null 成员，再交出去。
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional

from app.base.service.forest.forest_client import forest_get, to_query_params
from app.settings import get_settings


def _drop_null_members(value: Any) -> Any:
    """Java: hutool ``JSONObject`` 的 null 成员丢弃语义（含嵌套）."""
    if isinstance(value, MutableMapping):
        for key in [k for k, v in value.items() if v is None]:
            del value[key]
        for item in value.values():
            _drop_null_members(item)
        return value
    if isinstance(value, list):
        for item in value:
            _drop_null_members(item)
        return value
    return value


class HttpOdsLwzxsfsjFeeStationExit01Service:
    """Java: ``interface HttpOdsLwzxsfsjFeeStationExit01Service``."""

    # Java: JSONObject getOdsLwzxsfsjFeeStationExit01Page(@Query ... q)
    @staticmethod
    def get_ods_lwzxsfsj_fee_station_exit01_page(entity: Any) -> Optional[Mapping[str, Any]]:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url + "/base",
            "/feestationexit/list",
            to_query_params(entity),
        )
        return _drop_null_members(payload) if isinstance(payload, Mapping) else None

    # Java: JSONObject selectOdsLwzxsfsjFeeStationExit01ById(@Var("bigId") String bigId)
    @staticmethod
    def select_ods_lwzxsfsj_fee_station_exit01_by_id(big_id: str) -> Optional[Mapping[str, Any]]:
        payload = forest_get(
            get_settings().vehicle_monitor.base_url + "/base", f"/feestationexit/{big_id}"
        )
        return _drop_null_members(payload) if isinstance(payload, Mapping) else None


__all__ = ["HttpOdsLwzxsfsjFeeStationExit01Service"]
