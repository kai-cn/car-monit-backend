"""预警规则 Service 业务层处理.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/ICarWarningRuleService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarWarningRuleServiceImpl.java

``save`` / ``delete`` 之后无条件调用 :meth:`cache_warning_rule`（Java 的
``cacheWarningRule()``）—— 先按 ``Constants.CAR_WARNING_RULE + "*"`` 删掉旧键，
再按 (通知人员, 通知方式) 重新聚合预警范围 id。

``cacheWarningRule`` 的三处"看起来像 bug 但照抄"的地方
------------------------------------------------------
1. 键名是 ``car_warning_rule:<userId>type<noticeType>``（``type`` 前**没有**分隔符）；
2. 同一个 key 已有值时**追加**而不是覆盖 —— 所以重复保存会让列表里出现重复的路段 id；
3. 只有 ``noticeUserId`` / ``noticeRangeId`` / ``noticeType`` **三者都非空**的规则
   才进缓存；``noticeType`` 为 ``null`` 时键名会变成 ``"...typenull"``（
   ``CommonUtil.isNull`` 的语义），不会 NPE。
"""

from __future__ import annotations

from typing import Any, List, Optional

from app.common.constant.constants import CAR_WARNING_RULE
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils.common_util import delete_end, is_not_blank, is_null
from app.manager.domain.car_warning_rule import CarWarningRule
from app.manager.mapper.car_warning_rule_mapper import CarWarningRuleMapper
from app.manager.service.manager_service import ManagerCrudService


class CarWarningRuleService(ManagerCrudService):
    """Java: ``class CarWarningRuleServiceImpl extends ServiceImpl<CarWarningRuleMapper, CarWarningRule>``."""

    mapper_cls = CarWarningRuleMapper

    def __init__(
        self, mapper: Any = None, redis_cache: Optional[RedisCache] = None
    ) -> None:
        super().__init__(mapper)
        self._redis_cache = redis_cache

    @property
    def redis_cache(self) -> RedisCache:
        """Java: ``@Autowired private RedisCache redisCache``."""
        if self._redis_cache is None:
            self._redis_cache = get_redis_cache()
        return self._redis_cache

    def after_change(self) -> None:
        """Java: ``cacheWarningRule();`` —— save / delete 之后都会调用。"""
        self.cache_warning_rule()

    # Java: private void cacheWarningRule()
    def cache_warning_rule(self) -> None:
        redis_cache = self.redis_cache
        # 1. 先删除
        keys = redis_cache.keys(CAR_WARNING_RULE + "*")
        if keys:
            for key in keys:
                redis_cache.delete_object(key)
        # 2. 回源查全量（``selectCarWarningRuleList(new CarWarningRule())``）
        rule_list: List[CarWarningRule] = self.select_list(CarWarningRule())
        if not rule_list:
            return
        for rule in rule_list:
            # Java: StringUtils.isNoneBlank(noticeUserId, noticeRangeId, noticeType)
            if not (
                is_not_blank(rule.notice_user_id)
                and is_not_blank(rule.notice_range_id)
                and is_not_blank(rule.notice_type)
            ):
                continue
            notice_type = is_null(rule.notice_type)  # 预警方式
            # Java: CommonUtil.deleteEnd(x).split(",") —— 空串 split 得到 [""]
            user_ids = delete_end(rule.notice_user_id).split(",")
            notice_range_ids = delete_end(rule.notice_range_id).split(",")
            for raw_user_id in user_ids:
                user_id = is_null(raw_user_id)
                if not is_not_blank(user_id) or len(notice_range_ids) <= 0:
                    continue
                # Java: Constants.CAR_WARNING_RULE + userId + "type" + noticeType
                redis_key = f"{CAR_WARNING_RULE}{user_id}type{notice_type}"
                old_object = redis_cache.get_cache_object(redis_key)
                rule_list_value: List[str] = []
                if old_object is not None:
                    rule_list_value = list(old_object)
                for notice_range_id in notice_range_ids:
                    rule_list_value.append(is_null(notice_range_id))
                redis_cache.set_cache_object(redis_key, rule_list_value)


_SERVICE: Optional[CarWarningRuleService] = None


def get_car_warning_rule_service() -> CarWarningRuleService:
    """Java: ``@Autowired ICarWarningRuleService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CarWarningRuleService()
    return _SERVICE


def reset_car_warning_rule_service() -> None:
    """Test helper: drop the cached singleton so a fake can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "CarWarningRuleService",
    "get_car_warning_rule_service",
    "reset_car_warning_rule_service",
]
