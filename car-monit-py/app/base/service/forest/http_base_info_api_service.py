"""基础信息同步接口（上游车辆监控服务）—— Forest 客户端.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/forest/HttpBaseInfoApiService.java

Java 原文是 7 个 ``@Get`` 的接口声明，方法体由 Forest 生成::

    @BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
    public interface HttpBaseInfoApiService {
        @Get("/base/org/listAll")     List<OdsYhglVBaseOrg>  getOrgInfoList();
        @Get("/base/section/listAll") List<OdsSzdnSection>    getSectionInfoList();
        @Get("/base/gantry/listAll")  List<OdsSzdnGantry>     getGantryInfoList();
        @Get("/base/fwqjcxx/listAll") List<DwdLcztFwqjcxx>    getServiceAreaInfoList();
        @Get("/base/sfsjcxx/listAll") List<DwdLcztSfsjcxx>    getTollBoothInfoList();
        @Get(url = "/base/sfzjcxx/listAll") List<DwdLcztSfzjcxx> getSfzjcxxInfoList();
        @Get("/base/toll/listAll")    List<OdsSzdnToll>       getTollStationInfoList();
    }

七个接口**都没有参数**（没有 ``@Query`` / ``@Var``），所以请求是裸 GET。

与 ``HttpSysUtilApiService`` 的两个差别
---------------------------------------
1. ``baseURL`` 末尾**没有** ``/base`` —— 每个 ``@Get`` 路径自己带 ``/base`` 前缀。
2. 返回值是 ``List<Xxx>`` 而不是 ``TableDataInfo``，对应上游的 ``listAll`` 全量接口。
   上游返回的不是 JSON 数组时，Java 的 Jackson 反序列化会抛异常 ⇒ 这里抛
   :class:`~app.base.service.forest.forest_client.ForestException`，不静默降级成空列表
   （降级会把 ``truncateTable()`` 之后本该失败的任务变成"成功清表"，是数据事故）。

调用点只有 :mod:`app.quartz.task.vehicle_monitoring_task` 的 7 个 ``syncXxxInfo``：
取全量 -> ``truncateTable()`` -> ``saveBatch(list)``。
"""

from __future__ import annotations

from typing import List, Type, TypeVar

from app.base.domain.dwd_lczt_fwqjcxx import DwdLcztFwqjcxx
from app.base.domain.dwd_lczt_sfsjcxx import DwdLcztSfsjcxx
from app.base.domain.dwd_lczt_sfzjcxx import DwdLcztSfzjcxx
from app.base.domain.ods_szdn_gantry import OdsSzdnGantry
from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.domain.ods_yhgl_v_base_org import OdsYhglVBaseOrg
from app.base.service.forest.forest_client import ForestException, forest_get
from app.settings import get_settings

T = TypeVar("T")


def _base_url() -> str:
    return get_settings().vehicle_monitor.base_url


def _get_entities(path: str, entity_cls: Type[T]) -> List[T]:
    """``@Get(path) List<Xxx>`` —— 拉取全量并逐行反序列化成实体.

    ``model_validate`` 同时接受 camelCase（上游 Jackson 风格）与 snake_case 键名；
    与 ``resultMap`` 不同，它**不会**把库里多出来的列静默丢掉 —— 上游多给字段也没关系，
    ``DomainModel`` 是 ``extra="ignore"``，与 Jackson 的 ``FAIL_ON_UNKNOWN_PROPERTIES``
    在本工程里的实际取值（默认 true，但 Forest 的转换器关掉了它）一致。
    """
    payload = forest_get(_base_url(), path)
    if not isinstance(payload, list):
        # Java: Jackson 把对象反序列化成 List 失败 -> ForestRuntimeException -> code 500
        raise ForestException(
            f"响应不是 JSON 数组: {path} -> {type(payload).__name__}"
        )
    return [row if isinstance(row, entity_cls) else entity_cls.model_validate(row) for row in payload]


class HttpBaseInfoApiService:
    """Java: ``interface HttpBaseInfoApiService``."""

    # Java: List<OdsYhglVBaseOrg> getOrgInfoList()
    @staticmethod
    def get_org_info_list() -> List[OdsYhglVBaseOrg]:
        return _get_entities("/base/org/listAll", OdsYhglVBaseOrg)

    # Java: List<OdsSzdnSection> getSectionInfoList()
    @staticmethod
    def get_section_info_list() -> List[OdsSzdnSection]:
        return _get_entities("/base/section/listAll", OdsSzdnSection)

    # Java: List<OdsSzdnGantry> getGantryInfoList()
    @staticmethod
    def get_gantry_info_list() -> List[OdsSzdnGantry]:
        return _get_entities("/base/gantry/listAll", OdsSzdnGantry)

    # Java: List<DwdLcztFwqjcxx> getServiceAreaInfoList()
    @staticmethod
    def get_service_area_info_list() -> List[DwdLcztFwqjcxx]:
        return _get_entities("/base/fwqjcxx/listAll", DwdLcztFwqjcxx)

    # Java: List<DwdLcztSfsjcxx> getTollBoothInfoList()
    @staticmethod
    def get_toll_booth_info_list() -> List[DwdLcztSfsjcxx]:
        return _get_entities("/base/sfsjcxx/listAll", DwdLcztSfsjcxx)

    # Java: List<DwdLcztSfzjcxx> getSfzjcxxInfoList()
    @staticmethod
    def get_sfzjcxx_info_list() -> List[DwdLcztSfzjcxx]:
        return _get_entities("/base/sfzjcxx/listAll", DwdLcztSfzjcxx)

    # Java: List<OdsSzdnToll> getTollStationInfoList()
    @staticmethod
    def get_toll_station_info_list() -> List[OdsSzdnToll]:
        return _get_entities("/base/toll/listAll", OdsSzdnToll)


__all__ = ["HttpBaseInfoApiService"]
