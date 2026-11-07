"""轨迹数据 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/IZdataTrailTracksService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/ZdataTrailTracksServiceImpl.java

``base`` 包里**唯一**带业务逻辑的 Service：``carTrackQuery``（``/base/trailtracks``
的控制器并不调用它，真正的调用方是 ``manager`` 包的
``CarTrackInfoController``）。为了不让 t5 阶段回头改这里，先在 ``base`` 里迁完。

``carTrackQuery`` 的四个容易踩空的分支
--------------------------------------
1. ``isCylx`` 取的是 ``CommonUtil.isNull(...).equals("1")`` —— 也就是 **null 会先变成
   ``""``**，再跟 ``"1"`` 比较。所以 ``null`` / ``""`` 都走 ``else`` 分支，不会 NPE。
2. ``isCylx == "1"`` 时**先**调 ``getCyly``。若结果为空（``null`` 或 size == 0），
   ``list`` 保持为 Service 开头建的那个**空 ``ArrayList``**，``getHistoryTrail``
   **根本不会被调用** —— 于是"常用路线"查不到时返回空列表，而不是"退化成普通查询"。
   这个不对称是原样保留的行为，别"修"。
3. ``getCyly`` 是 ``startPage()`` 之后的第一条 select，所以**被分页**；
   紧接着的 ``getHistoryTrail`` 不再分页（PageHelper 的 ThreadLocal 已被消费）。
4. ``getUuid()`` 为 ``null`` 时 ``map.containsKey(null)`` 为假 —— 只有命中通行次数
   的记录才会被改写成 ``"车牌(通行N次)"``。``plateKey`` 为 null 时会拼成
   ``"null(通行N次)"``（Java 字符串拼接语义），照抄。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.base.domain.zdata_trail_tracks import ZdataTrailTracks
from app.base.mapper.zdata_trail_tracks_mapper import ZdataTrailTracksMapper
from app.common.utils.common_util import is_null
from app.common.utils.string_utils import is_not_blank
from app.config.database import transactional


class ZdataTrailTracksService:
    """Java: ``class ZdataTrailTracksServiceImpl``."""

    def __init__(self, mapper: Optional[ZdataTrailTracksMapper] = None) -> None:
        self._mapper = mapper or ZdataTrailTracksMapper()

    # Java: ZdataTrailTracks selectZdataTrailTracksById(String uuid)
    def select_by_id(self, uuid: str) -> Optional[ZdataTrailTracks]:
        return self._mapper.select_by_id(uuid)

    # Java: List<ZdataTrailTracks> selectZdataTrailTracksList(ZdataTrailTracks x)
    def select_list(self, query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
        return self._mapper.select_list(query)

    # Java: List<ZdataTrailTracks> carTrackQuery(ZdataTrailTracks x)
    def car_track_query(self, query: ZdataTrailTracks) -> List[ZdataTrailTracks]:
        """车辆历史轨迹查询（含"常用路线"与经纬度字符串 -> 小数转换）。"""
        result: List[ZdataTrailTracks] = []

        # Java: CommonUtil.isNull(getIsCylx()) -> null 变 ""，所以永远不会 NPE。
        is_cylx = is_null(query.is_cylx)
        if is_cylx == "1":
            cy_list = self._mapper.get_cyly(query)
            if cy_list is not None and len(cy_list) > 0:
                # Java: setUuidList(cylist.stream().map(getUuid).collect(toList()))
                query.uuid_list = [item.uuid for item in cy_list]
                # Java: Collectors.toMap(ZdataTrailTracks::getUuid, ::getPassCount)
                pass_map: Dict[Optional[str], Optional[int]] = {
                    item.uuid: item.pass_count for item in cy_list
                }
                result = self._mapper.get_history_trail(query)
                if result is not None and len(result) > 0:
                    for row in result:
                        # Java: map.containsKey(uuId) —— null 不作为键命中。
                        if row.uuid is not None and row.uuid in pass_map:
                            row.plate_key = (
                                f"{row.plate_key}(通行{pass_map[row.uuid]}次)"
                            )
        else:
            # 普通查询（"常用路线"查不到时**不会**走到这里，见模块文档第 2 条）。
            result = self._mapper.get_history_trail(query)

        for row in result:
            # Java: new BigDecimal(String) —— 非法数值抛 NumberFormatException -> 500。
            if is_not_blank(row.start_lon):
                row.start_lon_dec = float(row.start_lon)
            if is_not_blank(row.strat_lat):
                row.strat_lat_dec = float(row.strat_lat)
            if is_not_blank(row.end_lon):
                row.end_lon_dec = float(row.end_lon)
            if is_not_blank(row.end_lat):
                row.end_lat_dec = float(row.end_lat)

        return result

    # Java: int removeRealData(List<String> carNoList)
    def remove_real_data(self, car_no_list: List[str]) -> int:
        return self._mapper.remove_real_data(car_no_list)

    # Java: boolean saveBatch(Collection<ZdataTrailTracks> entityList)
    @transactional
    def save_batch(self, entity_list: List[ZdataTrailTracks]) -> bool:
        """MP 的 ``saveBatch`` —— 逐条插入（与逐条 ``insert`` 等价）。"""
        for entity in entity_list:
            self._mapper.insert(entity)
        return True


_SERVICE: Optional[ZdataTrailTracksService] = None


def get_zdata_trail_tracks_service() -> ZdataTrailTracksService:
    """Java: ``@Autowired IZdataTrailTracksService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ZdataTrailTracksService()
    return _SERVICE


def reset_zdata_trail_tracks_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "ZdataTrailTracksService",
    "get_zdata_trail_tracks_service",
    "reset_zdata_trail_tracks_service",
]
