"""车辆轨迹 / 可疑车辆同步 bean（``@Component("trackTask")``）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/TrackTask.java

6 个方法，其中 5 个是**真业务**、1 个（``syncHistoryTrackNoCar``）方法体整段被注释。
线上 ``sys_job`` 表里引用的是前三个::

    trackTask.syncCurrentTrack    0 0/3 * * * ?     每 3 分钟
    trackTask.syncSuspiciousCar   0 0 5 * * ?       每天 05:00
    trackTask.syncHistoryTrack    0 0 6 * * ?       每天 06:00

四个协作 Bean
-------------
======================================  ==================================================
Java                                    Python
======================================  ==================================================
``ICarTrackInfoService``                :class:`~app.manager.service.car_track_info_service.CarTrackInfoService`
``ICarSuspiciousService``               :class:`~app.manager.service.car_suspicious_service.CarSuspiciousService`
``IGeometryService``                    :class:`~app.base.service.geometry_service.GeometryService`
``ICarExceptRecordService``             :class:`~app.manager.service.car_except_record_service.CarExceptRecordService`
======================================  ==================================================

日志文案里的 ``new Date()``
---------------------------
Java 写的是 ``log.info("...！" + new Date())``，即 ``java.util.Date#toString()`` 的
``Thu Oct 29 11:05:31 CST 2026`` 形状。用 :func:`~app.common.utils.date_utils.java_date_to_string`
逐字符复刻 —— 否则排查问题时两边的日志对不上时间格式。

``@Transactional`` 的落点
-------------------------
Java 给**每个**方法都挂了 ``@Transactional(rollbackFor = Exception.class)``，事务边界
覆盖"一个 task 方法 = 一次调度触发"。Python 侧不开显式事务（各 Service 内部自带
``session_scope``），与全项目一致的差异见 ``COMPATIBILITY.md`` §28.3。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.base.domain.trail_info import TrailInfo
from app.common.utils.date_utils import java_date_to_string
from app.manager.domain.car_except_record import CarExceptRecord
from app.config.database import transactional

logger = logging.getLogger(__name__)

#: Java: ``@Component("trackTask")``
BEAN_NAME = "trackTask"


class TrackTask:
    """Java: ``class TrackTask``（``@Slf4j @Component("trackTask")``）."""

    def __init__(
        self,
        car_track_info_service: Optional[Any] = None,
        car_suspicious_service: Optional[Any] = None,
        geometry_service: Optional[Any] = None,
        car_except_record_service: Optional[Any] = None,
    ) -> None:
        # 允许测试注入替身；生产走下面的惰性单例属性。
        self._car_track_info_service_override = car_track_info_service
        self._car_suspicious_service_override = car_suspicious_service
        self._geometry_service_override = geometry_service
        self._car_except_record_service_override = car_except_record_service

    # ------------------------------------------------------------ 协作 Bean

    # Java: @Autowired private ICarTrackInfoService carTrackInfoService;
    @property
    def car_track_info_service(self) -> Any:
        if self._car_track_info_service_override is not None:
            return self._car_track_info_service_override
        from app.manager.service.car_track_info_service import get_car_track_info_service

        return get_car_track_info_service()

    # Java: @Autowired private ICarSuspiciousService carSuspiciousService;
    @property
    def car_suspicious_service(self) -> Any:
        if self._car_suspicious_service_override is not None:
            return self._car_suspicious_service_override
        from app.manager.service.car_suspicious_service import get_car_suspicious_service

        return get_car_suspicious_service()

    # Java: @Autowired private IGeometryService geometryService;
    @property
    def geometry_service(self) -> Any:
        if self._geometry_service_override is not None:
            return self._geometry_service_override
        from app.base.service.geometry_service import get_geometry_service

        return get_geometry_service()

    # Java: @Autowired private ICarExceptRecordService carExceptRecordService;
    @property
    def car_except_record_service(self) -> Any:
        if self._car_except_record_service_override is not None:
            return self._car_except_record_service_override
        from app.manager.service.car_except_record_service import (
            get_car_except_record_service,
        )

        return get_car_except_record_service()

    # ------------------------------------------------------------ 任务

    # Java: @Transactional public void syncCurrentTrack()
    @transactional
    def sync_current_track(self) -> None:
        """车辆实时轨迹同步（每三分钟）: ``0 0/3 * * * ?``."""
        logger.info("车俩实时轨迹同步开始同步！%s", java_date_to_string())
        self.car_track_info_service.sync_current_track()
        logger.info("车俩实时轨迹同步结束同步！%s", java_date_to_string())

    # Java: @Transactional public void syncSuspiciousCar()
    @transactional
    def sync_suspicious_car(self) -> None:
        """可疑车辆同步（每天凌晨 5 点）: ``0 0 5 * * ?``.

        ``trailInfoList`` 是一个**空** ``ArrayList``，传进去之后 Java 侧也不会读它
        （``syncSuspiciousCar`` 内部把入参覆盖掉了）。照抄 —— 不要改成 ``None``。
        """
        logger.info("可疑车俩数据同步开始同步！%s", java_date_to_string())
        trail_info_list: list[TrailInfo] = []
        self.car_suspicious_service.sync_suspicious_car("redis", trail_info_list)
        logger.info("可疑车俩数据同步结束同步！%s", java_date_to_string())

    # Java: @Transactional public void syncHistoryTrack()
    @transactional
    def sync_history_track(self) -> None:
        """车辆历史轨迹同步（每天凌晨 6 点）: ``0 0 6 * * ?``.

        顺序**不能**颠倒：先同步轨迹，再刷新 ``lxfx='1'`` 的几何缓存
        （``geometryService.updateRedisList()``），否则缓存里是上一次的桩号。
        """
        logger.info("车俩历史轨迹同步开始同步！%s", java_date_to_string())
        self.car_track_info_service.sync_history_track()
        # 更新缓存数据
        self.geometry_service.update_redis_list()
        logger.info("车俩历史轨迹同步结束同步！%s", java_date_to_string())

    # Java: @Transactional public void saveCarExcept()
    @transactional
    def save_car_except(self) -> None:
        """车辆逃费数据更新（每天凌晨 7 点）: ``0 0 7 * * ?``.

        传的是 ``new CarExceptRecord()``（**空实体**）—— 方法内部把它当查询条件用。
        """
        logger.info("车辆逃费数据更新开始！%s", java_date_to_string())
        self.car_except_record_service.save_car_except(CarExceptRecord())
        logger.info("车辆逃费数据更新结束！%s", java_date_to_string())

    # Java: @Transactional public void syncHistoryTrackNoCar()
    @transactional
    def sync_history_track_no_car(self) -> None:
        """车辆历史轨迹同步（每 10 分钟）: ``0 0/10 * * * ?`` —— **空方法体**.

        Java 原文整段被注释::

            // log.info("车俩历史轨迹同步开始同步！"+new Date());
            // carTrackInfoService.syncHistoryTrackNoCar();
            // log.info("车俩历史轨迹同步结束同步！"+new Date());

        ``CarTrackInfoService.sync_history_track_no_car`` 本身已迁移（供其它调用点使用），
        只是这个任务**不调**它。
        """

    # Java: @Transactional public void changeCarSuspicious()
    @transactional
    def change_car_suspicious(self) -> None:
        """可疑车辆迁移（每天 21:00）: ``0 0 21 * * ?`` —— 与可疑车辆同步的日志同款文案.

        注意 Java 的**结束**日志写的是 ``"可疑车辆迁移同步！"``（**没有**"结束"二字），
        与前几个方法不同，照抄。
        """
        logger.info("可疑车辆迁移开始同步！%s", java_date_to_string())
        self.car_suspicious_service.change_car_suspicious()
        logger.info("可疑车辆迁移同步！%s", java_date_to_string())


__all__ = ["BEAN_NAME", "TrackTask"]
