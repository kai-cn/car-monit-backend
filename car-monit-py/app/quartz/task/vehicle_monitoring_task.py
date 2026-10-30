"""车辆监控基础信息同步 bean（``@Component("vehicleMonitoringTask")``）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java

7 个方法，形状**完全一致**（这是本类最值得注意的地方）::

    List<Xxx> list = httpBaseInfoApiService.getXxxList();   // 上游 listAll（全量）
    this.xxxService.truncateTable();                        // 清表
    this.xxxService.saveBatch(list);                        // 全量插入

线上 ``sys_job`` 里 7 条全都配上了（组 ``DEFAULT``）::

    vehicleMonitoringTask.syncTollBoothInfoInfo   -> dwd_lczt_sfsjcxx   （收费所）
    vehicleMonitoringTask.syncOrgInfo             -> ods_yhgl_v_base_org（机构）
    vehicleMonitoringTask.syncTollStationInfo     -> ods_szdn_toll      （收费站）
    vehicleMonitoringTask.syncGantryInfo          -> ods_szdn_gantry    （门架）
    vehicleMonitoringTask.syncSfzjcxxInfoInfo     -> dwd_lczt_sfzjcxx   （收费站基础信息位置）
    vehicleMonitoringTask.syncServiceAreaInfoInfo -> dwd_lczt_fwqjcxx   （服务区）
    vehicleMonitoringTask.syncSectionInfo         -> ods_szdn_section   （路段，**多一步写缓存**）

三个必须照抄的细节
------------------
1. **``syncSectionInfo`` 多一步**：插完之后 ``redisCache.setCacheList(Constants.SECTION_LIST, list)``。
   其余 6 个方法**不**碰缓存。这里写进去的是**刚刚插入的那份 ``list``**，不是重新查库。
2. **``truncateTable`` 是 ``@Update`` 绕开 MP 的全表删除拦截**（Java 注释里写了
   ``Prohibition of full table deletion``）—— 所以是 ``TRUNCATE``，不是 ``DELETE``：
   DDL、隐式提交、不可回滚。
3. **先 truncate 后 insert**，中间没有事务保护时（§28.3）失败会留下空表 ——
   这正是 Java ``@Transactional`` 想挡的东西。

方法名里的 ``InfoInfo``
-----------------------
``syncTollBoothInfoInfo`` / ``syncSfzjcxxInfoInfo`` / ``syncServiceAreaInfoInfo`` 的
**双** ``Info`` 是 Java 原文的拼写（``getTollBoothInfoList`` + ``Info``）。线上
``sys_job.invoke_target`` 一字不差地这么写着，改名会让任务全部报
``NoSuchMethodException``。**不要"顺手修正"**。
"""

from __future__ import annotations

from typing import Any, Optional

from app.base.service.forest.http_base_info_api_service import HttpBaseInfoApiService
from app.common.constant.constants import SECTION_LIST
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache

#: Java: ``@Component("vehicleMonitoringTask")``
BEAN_NAME = "vehicleMonitoringTask"


class VehicleMonitoringTask:
    """Java: ``class VehicleMonitoringTask``（``@Log4j @Component("vehicleMonitoringTask")``）."""

    def __init__(
        self,
        http_base_info_api_service: Optional[Any] = None,
        ods_szdn_section_service: Optional[Any] = None,
        ods_yhgl_v_base_org_service: Optional[Any] = None,
        ods_szdn_gantry_service: Optional[Any] = None,
        ods_szdn_toll_service: Optional[Any] = None,
        dwd_lczt_sfzjcxx_service: Optional[Any] = None,
        dwd_lczt_fwqjcxx_service: Optional[Any] = None,
        dwd_lczt_sfsjcxx_service: Optional[Any] = None,
        redis_cache: Optional[RedisCache] = None,
    ) -> None:
        # Java: @Resource private HttpBaseInfoApiService httpBaseInfoApiService;
        # Java 有 7 个 @Autowired Service + 1 个 RedisCache，全部允许测试注入。
        self._http_base_info_api_service_override = http_base_info_api_service
        self._ods_szdn_section_service_override = ods_szdn_section_service
        self._ods_yhgl_v_base_org_service_override = ods_yhgl_v_base_org_service
        self._ods_szdn_gantry_service_override = ods_szdn_gantry_service
        self._ods_szdn_toll_service_override = ods_szdn_toll_service
        self._dwd_lczt_sfzjcxx_service_override = dwd_lczt_sfzjcxx_service
        self._dwd_lczt_fwqjcxx_service_override = dwd_lczt_fwqjcxx_service
        self._dwd_lczt_sfsjcxx_service_override = dwd_lczt_sfsjcxx_service
        self._redis_cache_override = redis_cache

    # ------------------------------------------------------------ 协作 Bean

    # Java: @Resource private HttpBaseInfoApiService httpBaseInfoApiService;
    @property
    def http_base_info_api_service(self) -> Any:
        # Forest 接口在 Python 里是一组静态方法，没有实例状态。
        return self._http_base_info_api_service_override or HttpBaseInfoApiService

    # Java: @Autowired private IOdsSzdnSectionService odsSzdnSectionService;
    @property
    def ods_szdn_section_service(self) -> Any:
        if self._ods_szdn_section_service_override is not None:
            return self._ods_szdn_section_service_override
        from app.base.service.ods_szdn_section_service import get_ods_szdn_section_service

        return get_ods_szdn_section_service()

    # Java: @Autowired private IOdsYhglVBaseOrgService odsYhglVBaseOrgService;
    @property
    def ods_yhgl_v_base_org_service(self) -> Any:
        if self._ods_yhgl_v_base_org_service_override is not None:
            return self._ods_yhgl_v_base_org_service_override
        from app.base.service.ods_yhgl_v_base_org_service import (
            get_ods_yhgl_v_base_org_service,
        )

        return get_ods_yhgl_v_base_org_service()

    # Java: @Autowired private IOdsSzdnGantryService odsSzdnGantryService;
    @property
    def ods_szdn_gantry_service(self) -> Any:
        if self._ods_szdn_gantry_service_override is not None:
            return self._ods_szdn_gantry_service_override
        from app.base.service.ods_szdn_gantry_service import get_ods_szdn_gantry_service

        return get_ods_szdn_gantry_service()

    # Java: @Autowired private IOdsSzdnTollService odsSzdnTollService;
    @property
    def ods_szdn_toll_service(self) -> Any:
        if self._ods_szdn_toll_service_override is not None:
            return self._ods_szdn_toll_service_override
        from app.base.service.ods_szdn_toll_service import get_ods_szdn_toll_service

        return get_ods_szdn_toll_service()

    # Java: @Autowired private IDwdLcztSfzjcxxService dwdLcztSfzjcxxService;
    @property
    def dwd_lczt_sfzjcxx_service(self) -> Any:
        if self._dwd_lczt_sfzjcxx_service_override is not None:
            return self._dwd_lczt_sfzjcxx_service_override
        from app.base.service.dwd_lczt_sfzjcxx_service import get_dwd_lczt_sfzjcxx_service

        return get_dwd_lczt_sfzjcxx_service()

    # Java: @Autowired private IDwdLcztFwqjcxxService dwdLcztFwqjcxxService;
    @property
    def dwd_lczt_fwqjcxx_service(self) -> Any:
        if self._dwd_lczt_fwqjcxx_service_override is not None:
            return self._dwd_lczt_fwqjcxx_service_override
        from app.base.service.dwd_lczt_fwqjcxx_service import get_dwd_lczt_fwqjcxx_service

        return get_dwd_lczt_fwqjcxx_service()

    # Java: @Autowired private IDwdLcztSfsjcxxService dwdLcztSfsjcxxService;
    @property
    def dwd_lczt_sfsjcxx_service(self) -> Any:
        if self._dwd_lczt_sfsjcxx_service_override is not None:
            return self._dwd_lczt_sfsjcxx_service_override
        from app.base.service.dwd_lczt_sfsjcxx_service import get_dwd_lczt_sfsjcxx_service

        return get_dwd_lczt_sfsjcxx_service()

    # Java: @Autowired private RedisCache redisCache;
    @property
    def redis_cache(self) -> RedisCache:
        if self._redis_cache_override is not None:
            return self._redis_cache_override
        return get_redis_cache()

    # ------------------------------------------------------------ 7 个同步方法

    # Java: @Transactional public void syncOrgInfo()
    def sync_org_info(self) -> None:
        """同步机构信息 -> ``ods_yhgl_v_base_org``."""
        rows = self.http_base_info_api_service.get_org_info_list()
        self.ods_yhgl_v_base_org_service.truncate_table()
        self.ods_yhgl_v_base_org_service.save_batch(rows)

    # Java: @Transactional public void syncSectionInfo()
    def sync_section_info(self) -> None:
        """同步路段信息 -> ``ods_szdn_section``，**并刷新 Redis ``SECTION_LIST``**.

        Java 注释解释了为什么 ``truncateTable`` 要用 ``@Update`` 注解写原生 SQL::

            // 清空数据  mybatis-plus 安全机制 会对delete语句没有where条件的进行拦截
            // 抛出 Prohibition of full table deletion
            // 使用 注解 @Update  绕够MP的安全检测
            this.odsSzdnSectionService.truncateTable();
            // 全量新增数据
            this.odsSzdnSectionService.saveBatch(list);
            redisCache.setCacheList(Constants.SECTION_LIST, list);

        写缓存的顺序在**最后** —— 插入失败就不会污染缓存。
        """
        rows = self.http_base_info_api_service.get_section_info_list()
        self.ods_szdn_section_service.truncate_table()
        self.ods_szdn_section_service.save_batch(rows)
        self.redis_cache.set_cache_list(SECTION_LIST, rows)

    # Java: @Transactional public void syncGantryInfo()
    def sync_gantry_info(self) -> None:
        """同步门架信息 -> ``ods_szdn_gantry``."""
        rows = self.http_base_info_api_service.get_gantry_info_list()
        self.ods_szdn_gantry_service.truncate_table()
        self.ods_szdn_gantry_service.save_batch(rows)

    # Java: @Transactional public void syncServiceAreaInfoInfo()
    def sync_service_area_info_info(self) -> None:
        """同步服务区信息 -> ``dwd_lczt_fwqjcxx``（方法名双 ``Info``，Java 原文）."""
        rows = self.http_base_info_api_service.get_service_area_info_list()
        self.dwd_lczt_fwqjcxx_service.truncate_table()
        self.dwd_lczt_fwqjcxx_service.save_batch(rows)

    # Java: @Transactional public void syncTollBoothInfoInfo()
    def sync_toll_booth_info_info(self) -> None:
        """同步收费所信息 -> ``dwd_lczt_sfsjcxx``（方法名双 ``Info``，Java 原文）."""
        rows = self.http_base_info_api_service.get_toll_booth_info_list()
        self.dwd_lczt_sfsjcxx_service.truncate_table()
        self.dwd_lczt_sfsjcxx_service.save_batch(rows)

    # Java: @Transactional public void syncSfzjcxxInfoInfo()
    def sync_sfzjcxx_info_info(self) -> None:
        """同步收费站基础信息位置 -> ``dwd_lczt_sfzjcxx``（方法名双 ``Info``，Java 原文）."""
        rows = self.http_base_info_api_service.get_sfzjcxx_info_list()
        self.dwd_lczt_sfzjcxx_service.truncate_table()
        self.dwd_lczt_sfzjcxx_service.save_batch(rows)

    # Java: @Transactional public void syncTollStationInfo()
    def sync_toll_station_info(self) -> None:
        """同步收费站信息 -> ``ods_szdn_toll``（这个**没有**双 ``Info``）."""
        rows = self.http_base_info_api_service.get_toll_station_info_list()
        self.ods_szdn_toll_service.truncate_table()
        self.ods_szdn_toll_service.save_batch(rows)


__all__ = ["BEAN_NAME", "VehicleMonitoringTask"]
