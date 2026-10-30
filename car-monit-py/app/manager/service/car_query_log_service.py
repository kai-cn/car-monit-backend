"""查询日志 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarQueryLogService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarQueryLogServiceImpl.java

逐字模板：无缓存、无额外校验。``save`` / ``delete`` 全部委托给
:class:`~app.manager.service.manager_service.ManagerCrudService`。
"""

from __future__ import annotations

from typing import Optional

from app.manager.domain.car_query_log import CarQueryLog
from app.manager.mapper.car_query_log_mapper import CarQueryLogMapper
from app.manager.service.manager_service import ManagerCrudService


class CarQueryLogService(ManagerCrudService):
    """Java: ``class CarQueryLogServiceImpl extends ServiceImpl<CarQueryLogMapper, CarQueryLog>``."""

    mapper_cls = CarQueryLogMapper

    # Java: void queryLog(String queryCondition, String modelType, String menuPiont)
    def query_log(
        self, query_condition: str, model_type: str, menu_point: str
    ) -> None:
        """查询 / 导出日志落库.

        Java 没有 try-catch —— 取不到登录用户或写库失败就往上抛（导出接口因此会
        先写日志再干活，日志失败整单失败）。照抄。
        """
        from app.common.utils.security_utils import get_login_user, get_user_real_name

        user = get_login_user().user
        car_query_log = CarQueryLog()
        # Java: user.getUserId().toString()
        car_query_log.user_id = str(user.user_id)
        car_query_log.user_name = get_user_real_name()
        car_query_log.user_ip = user.login_ip
        car_query_log.model_type = model_type
        car_query_log.menu_point = menu_point
        car_query_log.query_condition = query_condition
        self.save(car_query_log)


_SERVICE: Optional[CarQueryLogService] = None


def get_car_query_log_service() -> CarQueryLogService:
    """Java: ``@Autowired ICarQueryLogService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarQueryLogService()
    return _SERVICE


def reset_car_query_log_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarQueryLogService",
    "get_car_query_log_service",
    "reset_car_query_log_service",
]
