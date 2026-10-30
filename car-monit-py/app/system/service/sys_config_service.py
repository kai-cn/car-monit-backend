"""参数配置服务层.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysConfigService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysConfigServiceImpl.java

缓存的三个动作都与字典不同
--------------------------
字典是"写完全清、读未命中回源"；参数配置是**逐键维护**：

=============================  ==================================================
方法                           对缓存做什么
=============================  ==================================================
``selectConfigByKey``          读；空/未命中才回源，回源命中后**写回这一个键**
``insertConfig``               ``row > 0`` 时**写这一个键**（不是清空）
``updateConfig``               同上
``deleteConfigByIds``          ``count > 0`` 时**清空全部** ``sys_config:*``
``clearCache``                 清空全部
=============================  ==================================================

为什么增改是"写键"而删除是"清空"：删除时被删的键名在库里已经查不到了（Java 也没
在删除前收集键名），只能全清。照抄。

``init()`` 不挂到 FastAPI 生命周期
----------------------------------
Java 的 ``@PostConstruct init()`` 在容器启动后把整张 ``sys_config`` 灌进 Redis。
Python 侧**保留方法但不在启动时调用**，与 ``SysDictTypeServiceImpl#init()`` 同理：

1. 本工程的数据源是惰性创建的（``app.main``），启动期连库会让"没有 MySQL 也能起来
   做健康检查"这条能力失效；
2. 语义无损 —— ``selectConfigByKey`` 未命中时回源，读的是同一张表、同一个键。

需要手工预热时：

.. code-block:: python

    from app.system.service.sys_config_service import get_config_service
    get_config_service().init()

``selectConfigByKey`` 的返回值可能是 ``None``
---------------------------------------------
Java 的最后一行是 ``return StringUtils.EMPTY``（空串），但**上一行**
``return retConfig.getConfigValue()`` 返回的是库里的原值 —— 如果库里
``config_value`` 是 ``NULL``，拿到的就是 ``null``（不是空串）。Python 侧照抄：
命中行就返回 ``config_value``（可能是 ``None``），查不到才返回 ``""``。

``deleteConfigByIds`` 只保护 ``config_type = "Y"``
--------------------------------------------------
``StringUtils.equals(UserConstants.YES, config.getConfigType())`` ——
``"N"`` / ``""`` / ``null`` 全部放行。异常文案 **末尾带一个空格**：
``"内置参数【%1$s】不能删除 "``，照抄（客户端 trim 后看不出，但字符串比对会）。

类型不存在时（``selectConfigById`` 返回 ``None``）Java 会在
``config.getConfigType()`` 处 NPE -> 500，这里用 ``AttributeError`` 复刻。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from app.common.constant import user_constants as UserConstants
from app.common.constant.cache_constants import SYS_CONFIG_KEY
from app.common.core.redis.redis_cache import get_redis_cache
from app.common.core.text.convert import to_str
from app.common.exception.exceptions import CustomException
from app.common.utils.string_utils import is_not_empty
from app.system.domain.sys_config import SysConfig
from app.system.mapper.sys_config_mapper import SysConfigMapper


class SysConfigService:
    """Java: ``ISysConfigService`` (impl: ``SysConfigServiceImpl``)."""

    def __init__(self, config_mapper: Optional[SysConfigMapper] = None) -> None:
        self._config_mapper = config_mapper or SysConfigMapper()

    @property
    def config_mapper(self) -> SysConfigMapper:
        return self._config_mapper

    # Java: @PostConstruct public void init()
    def init(self) -> None:
        """把整张 ``sys_config`` 灌进缓存（Java 由 ``@PostConstruct`` 触发）。

        Python 侧不自动调用，理由见模块 docstring。手动作法::

            from app.system.service.sys_config_service import get_config_service
            get_config_service().init()
        """
        for config in self._config_mapper.select_config_list(SysConfig()):
            get_redis_cache().set_cache_object(self.get_cache_key(config.config_key), config.config_value)

    # Java: @DataSource(MASTER) SysConfig selectConfigById(Long configId)
    def select_config_by_id(self, config_id: int) -> Optional[SysConfig]:
        """Java 新建一个只带 id 的实体再走 ``selectConfig``（不是单独的 statement）。"""
        config = SysConfig(config_id=config_id)
        return self._config_mapper.select_config(config)

    # Java: String selectConfigByKey(String configKey)
    def select_config_by_key(self, config_key: Optional[str]) -> Optional[str]:
        """先读缓存；空/未命中回源，命中后写回。查不到返回 ``""``。"""
        cache = get_redis_cache()
        config_value = to_str(cache.get_cache_object(self.get_cache_key(config_key)))
        # Java: StringUtils.isNotEmpty —— 注意 RuoYi 的实现会 trim，"  " 也算空
        if is_not_empty(config_value):
            return config_value
        ret_config = self._config_mapper.select_config(SysConfig(config_key=config_key))
        if ret_config is not None:
            cache.set_cache_object(self.get_cache_key(config_key), ret_config.config_value)
            return ret_config.config_value
        return ""

    # Java: List<SysConfig> selectConfigList(SysConfig config)
    def select_config_list(self, config: SysConfig) -> List[SysConfig]:
        """分页由调用方的 ``startPage()`` + mapper 的 ``take_page`` 完成。"""
        return self._config_mapper.select_config_list(config)

    # Java: int insertConfig(SysConfig config)
    def insert_config(self, config: SysConfig) -> int:
        row = self._config_mapper.insert_config(config)
        if row > 0:
            get_redis_cache().set_cache_object(self.get_cache_key(config.config_key), config.config_value)
        return row

    # Java: int updateConfig(SysConfig config)
    def update_config(self, config: SysConfig) -> int:
        row = self._config_mapper.update_config(config)
        if row > 0:
            get_redis_cache().set_cache_object(self.get_cache_key(config.config_key), config.config_value)
        return row

    # Java: int deleteConfigByIds(Long[] configIds)
    def delete_config_by_ids(self, config_ids: Sequence[int]) -> int:
        """逐个体检"是不是内置参数"，有一条是就整批拒绝（库里一行都不动）。"""
        for config_id in config_ids:
            config = self.select_config_by_id(config_id)
            # Java: 没有判空 -> getConfigType() 处 NPE
            if UserConstants.YES == _none_guard(config).config_type:
                # Java: throw new CustomException("内置参数【" + key + "】不能删除 ") —— 末尾有空格
                raise CustomException(f"内置参数【{config.config_key}】不能删除 ")
        count = self._config_mapper.delete_config_by_ids(config_ids)
        if count > 0:
            self.clear_cache()
        return count

    # Java: void clearCache()
    def clear_cache(self) -> None:
        """``keys("sys_config:*")`` + 批量删。``KEYS`` 是 O(N) 阻塞命令（照抄）。"""
        cache = get_redis_cache()
        keys = cache.keys(f"{SYS_CONFIG_KEY}*")
        cache.delete_object(keys)

    # Java: String checkConfigKeyUnique(SysConfig config)
    def check_config_key_unique(self, config: SysConfig) -> str:
        """``"1"`` = 已存在，``"0"`` = 可用（``NOT_UNIQUE_OLD`` / ``UNIQUE_OLD``）。"""
        config_id = -1 if config.config_id is None else config.config_id
        info = self._config_mapper.check_config_key_unique(config.config_key)
        if info is not None and info.config_id != config_id:
            return UserConstants.NOT_UNIQUE_OLD
        return UserConstants.UNIQUE_OLD

    # Java: private String getCacheKey(String configKey)
    def get_cache_key(self, config_key: Optional[str]) -> str:
        """``Constants.SYS_CONFIG_KEY + configKey``。

        Java 的字符串拼接把 ``null`` 变成 ``"null"``（不是抛 NPE），所以键名会是
        ``"sys_config:null"``。Python 的 ``+`` 不允许 ``None``，这里显式复刻。
        """
        return SYS_CONFIG_KEY + ("null" if config_key is None else config_key)


def _none_guard(value):
    """Java 在这些位置没有判空，直接解引用 -> NPE（500）。这里让同样的 500 出现。"""
    if value is None:
        raise AttributeError("java.lang.NullPointerException: value is null")
    return value


_SERVICE: Optional[SysConfigService] = None


def get_config_service() -> SysConfigService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysConfigService()
    return _SERVICE


def reset_config_service() -> None:
    """Test helper: drop the cached service so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysConfigService",
    "get_config_service",
    "reset_config_service",
]
