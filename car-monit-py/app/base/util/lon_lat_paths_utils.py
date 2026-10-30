"""腾讯地图「驾车路线」调用工具（经纬度路径点计算）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/util/LonLatPathsUtils.java

Java 侧是 ``@Component`` + ``RestTemplate``；这里用 ``httpx`` 直接发 GET。

三处必须照抄的地方
------------------
1. **返回值是"字符串化的 JSON 数组"**（``JSONArray.toString()``），
   形如 ``[[113.1,23.2],[113.2,23.3]]`` —— 它被直接当成 ``Geometry.paths``
   存进数据库并写进 Redis，前端按 JSON 解析。所以这里也用 ``json.dumps``
   产出字符串，而不是 ``list``。
2. **``sig`` 的拼串**：键排序后逐个 ``key=value``，**每个非末位元素后面都补
   ``&``** —— 包括值为空、整段 ``key=value`` 被跳过的位置，因此可能出现
   ``&&`` 或结尾多余的 ``&``。这是原实现的既成事实，认证端已按此校验，照抄。
3. **任何异常都返回 ``None``**（Java 的 ``catch (Exception e) { return null; }``），
   由调用方决定降级路径。

``polyline`` 的前两个点是绝对坐标，之后是**累积增量**（除以 1e6），
所以解码循环从下标 2 开始且依赖 ``arr[i-2]``。
"""

from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.base.util.gps_util import gcj02_to_gps84, gps84_to_gcj02
from app.common.utils.string_utils import is_blank
from app.settings import get_settings

#: Java: ``private static final String key``
KEY = "UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6"
#: Java: ``private static final String secret``
SECRET = "M9yNPgh8FLp33A0plztTK5sehD6gMqny"
#: Java: ``private static final String url``
URL = "/ws/direction/v1/driving/"


def _set_scale_6(value: float) -> float:
    """``BigDecimal.valueOf(x).setScale(6, RoundingMode.HALF_UP).doubleValue()``."""
    return float(Decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


class LonLatPathsUtils:
    """Java: ``@Component public class LonLatPathsUtils``."""

    def __init__(self, tx_service_url: Optional[str] = None) -> None:
        # Java: ``@Value("${tx-service-url}") private String txServiceUrl;``
        self._tx_service_url = tx_service_url

    @property
    def tx_service_url(self) -> str:
        if self._tx_service_url is None:
            self._tx_service_url = get_settings().tx_service_url
        return self._tx_service_url

    # Java: public final String calcLonAndLatPaths(String curLon, String curLat,
    #         String nextLon, String nextLat, String heading, String waypoints)
    def calc_lon_and_lat_paths(
        self,
        cur_lon: str,
        cur_lat: str,
        next_lon: str,
        next_lat: str,
        heading: str,
        waypoints: str,
    ) -> Optional[str]:
        """计算经纬度路径点；失败返回 ``None``。"""
        try:
            # 转腾讯坐标系
            cur = gps84_to_gcj02(float(cur_lat), float(cur_lon))
            nxt = gps84_to_gcj02(float(next_lat), float(next_lon))

            from_point = f"{_set_scale_6(cur[0])},{_set_scale_6(cur[1])}"
            to_point = f"{_set_scale_6(nxt[0])},{_set_scale_6(nxt[1])}"

            # 请求腾讯 API
            result = self._get_lng_lat(
                from_point,
                to_point,
                heading,
                waypoints,
                KEY,
                self._sig(from_point, to_point, heading, waypoints),
            )
            if result is None:
                return None

            status = int(result.get("status") or 0)
            if status != 0:
                return None

            # 获取第一个路线
            routes = (result.get("result") or {}).get("routes") or []
            json_object = routes[0]

            # 提取数据并格式化
            polyline: List[Any] = json_object.get("polyline") or []
            arr: List[float] = [0.0] * len(polyline)
            arr[0] = float(polyline[0])
            arr[1] = float(polyline[1])
            for i in range(2, len(arr)):
                arr[i] = arr[i - 2] + float(polyline[i]) / 1000000

            rtn: List[List[float]] = []
            # 转换坐标系
            for i in range(0, len(arr), 2):
                gps = gcj02_to_gps84(arr[i], arr[i + 1])
                # 保留后6位
                gps = (_set_scale_6(gps[0]), _set_scale_6(gps[1]))
                # Java 这里把纬度/经度**交换**后放进数组 —— 前端按 [lon, lat] 消费
                rtn.append([gps[1], gps[0]])
            return json.dumps(rtn, separators=(",", ":"))
        except Exception:  # noqa: BLE001 - Java 原文 catch (Exception e) { return null; }
            return None

    def _get_lng_lat(
        self,
        from_point: str,
        to_point: str,
        heading: str,
        waypoints: str,
        key: str,
        sig: str,
    ) -> Optional[Dict[str, Any]]:
        """Java: ``private JSONObject getLngLat(...)``."""
        sb = [self.tx_service_url, URL, "?", "from=", from_point, "&to=", to_point]
        if not is_blank(heading):
            sb.extend(["&heading=", heading])
        if not is_blank(waypoints):
            sb.extend(["&waypoints=", waypoints])
        sb.extend(["&key=", key, "&sig=", sig])
        url = "".join(sb)
        response = httpx.get(url)
        return response.json()

    def _sig(self, from_point: str, to_point: str, heading: str, waypoints: str) -> str:
        """Java: ``private String sig(...)``."""
        param: Dict[str, str] = {}
        param["from"] = from_point
        param["to"] = to_point
        if not is_blank(heading):
            param["heading"] = heading
        if not is_blank(waypoints):
            param["waypoints"] = waypoints
        param["key"] = KEY

        array = sorted(param.keys())
        sb = [URL, "?"]
        for i, name in enumerate(array):
            if param[name].strip() != "":
                sb.extend([name, "=", param[name].strip()])
            # Java 原文对**每个**非末位元素都补 "&"，含被跳过的那一对
            if i < len(array) - 1:
                sb.append("&")
        sb.append(SECRET)
        return hashlib.md5("".join(sb).encode("utf-8")).hexdigest().lower()


__all__ = ["KEY", "SECRET", "URL", "LonLatPathsUtils"]
