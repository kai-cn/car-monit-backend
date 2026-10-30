"""恒达（HenDa）桩号 -> 经纬度服务.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IHenDaService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/HenDaServiceImpl.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/IHenDaApi.java

Java 语义
---------
``getPileToLonLat(roadCode, pile, direction)`` 调恒达的
``${hendaUrl}/getLonLatByPos``，把 GeoServer 的图层查询包成:

* ``layerName = "rdlinelong"``
* ``filter    = "lxbh='<roadCode>'  and gxfx = '<direction>'"``（注意 ``'`` 后是**两个空格**）
* ``m         = pile``

再带 ``appid`` / ``nonce`` / ``signature`` / ``timestamp`` 四个签名参数。
**任何异常都吞掉并返回 ``None``** —— 源码注释是"防止线程中断 如果报错就跳过这个经纬度"。

三个照抄点
----------
1. ``nonce`` 是 ``System.currentTimeMillis()`` 的字符串；``timestamp`` 是
   ``yyyyMMddHHmmss``。
2. 请求参数 ``params`` 是 **JSON 串先 `URLEncoder.encode` 一次**，Forest 发请求时
   又会编码一次。Python 侧先把 JSON 串 ``quote_plus`` 一次，再交给 httpx 编码，
   线上形态一致。
3. 返回 ``{"longitude": data.x, "latitude": data.y}``，两者都是**字符串**
   （``getString``）；``data`` 缺失时 Java NPE -> 被吞 -> ``None``。
"""

from __future__ import annotations

import json
import time
import urllib.parse
from datetime import datetime
from typing import Any, Dict, Optional

from app.base.service.forest.forest_client import forest_get
from app.base.util.encrypt_utils import EncryptUtils
from app.settings import get_settings

#: Java: ``@Get(url = "${hendaUrl}/getLonLatByPos", connectTimeout = 30000)``
_HENDA_CONNECT_TIMEOUT_MS = 30000


class HenDaService:
    """Java: ``class HenDaServiceImpl implements IHenDaService``."""

    def __init__(self) -> None:
        settings = get_settings()
        self._appid: str = settings.hengda.appid
        self._secret_key: str = settings.hengda.secret
        # Java: ``@Get(url = "${hendaUrl}/getLonLatByPos")`` —— ``hendaUrl`` 来自
        # ``forest.variables``（application.yml 里 ``forest.variables.hendaUrl``）。
        self._base_url: str = settings.forest.variables.get("hendaUrl", "")

    # Java: JSONObject getPileToLonLat(String roadCode, String pile, String direction)
    def get_pile_to_lon_lat(
        self, road_code: Optional[str], pile: Optional[str], direction: Optional[str]
    ) -> Optional[Dict[str, Optional[str]]]:
        try:
            params: Dict[str, Any] = {
                "layerName": "rdlinelong",
                # Java: "lxbh='" + roadCode + "'  and gxfx = '" + direction + "'"
                "filter": f"lxbh='{_java_string(road_code)}'  and gxfx = '{_java_string(direction)}'",
                "m": pile,
            }

            # Java: Calendar.getInstance().getTimeInMillis()
            nonce = str(int(time.time() * 1000))
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            signature = EncryptUtils.get_ciphertext(self._appid, self._secret_key, nonce, timestamp)

            # Java: URLEncoder.encode(mapper.writeValueAsString(map), "utf8")
            map_str = urllib.parse.quote_plus(
                json.dumps(params, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
            )

            payload = forest_get(
                self._base_url,
                "/getLonLatByPos",
                {
                    "params": map_str,
                    "appid": self._appid,
                    "nonce": nonce,
                    "signature": signature,
                    "timestamp": timestamp,
                },
                connect_timeout_ms=_HENDA_CONNECT_TIMEOUT_MS,
            )

            # Java: JSONObject jsonObject = lonLatByPos.getJSONObject("data");
            data = payload.get("data") if isinstance(payload, dict) else None
            # Java 在 data 为 null 时 NPE（被本方法的 catch 吞掉）
            if not isinstance(data, dict):
                return None

            # Java: rtn.put("longitude", jsonObject.getString("x"));
            return {
                "longitude": None if data.get("x") is None else str(data.get("x")),
                "latitude": None if data.get("y") is None else str(data.get("y")),
            }
        except Exception:  # noqa: BLE001 —— Java: catch (Exception e) { return null; }
            # 防止线程中断 如果报错就跳过这个经纬度
            return None


def _java_string(value: Optional[str]) -> str:
    """Java 字符串拼接时 ``null`` 会渲染成字面量 ``"null"``。"""
    return "null" if value is None else value


_SERVICE: Optional[HenDaService] = None


def get_hen_da_service() -> HenDaService:
    """Java: ``@Autowired IHenDaService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = HenDaService()
    return _SERVICE


def reset_hen_da_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = ["HenDaService", "get_hen_da_service", "reset_hen_da_service"]
