"""MyBatis-Plus ``BaseMapper`` 的等价实现（``base`` / ``manager`` / ``flow`` 共用）。

# Migrated from: com.baomidou.mybatisplus.core.mapper.BaseMapper
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/config/MyBatisPlusHandlerConfig.java

为什么需要这一层
----------------
``base`` / ``manager`` / ``flow`` 三个包的 Service 都是
``extends ServiceImpl<XxxMapper, Xxx>``，除了 XML 里的自定义语句，还会调
``BaseMapper`` 自带的四个方法：

======================  ==========================================  ============================
Java                    SQL 形态                                    Python
======================  ==========================================  ============================
``insert(entity)``      ``INSERT INTO t (非 null 列) VALUES (...)``  :meth:`PlusMapper.insert`
``updateById(entity)``  ``UPDATE t SET 非 null 列 WHERE id=? AND    :meth:`PlusMapper.update_by_id`
                        del_flag='0'``
``deleteById(id)``      ``UPDATE t SET del_flag='1' WHERE id=? AND  :meth:`PlusMapper.delete_by_id`
                        del_flag='0'``（``@TableLogic`` 的逻辑删除）
``selectById(id)``      ``SELECT 全部列 WHERE id=? AND del_flag='0'`` :meth:`PlusMapper.select_by_id`
======================  ==========================================  ============================

本工程**没有**用到 ``Wrappers`` / ``lambdaQuery`` / ``saveBatch`` / ``updateBatchById``
（已全量 grep 确认），所以这一层只有上面四个方法，不要凭空补。

字段策略是 ``NOT_NULL``
-----------------------
MyBatis-Plus 默认 ``FieldStrategy.NOT_NULL``：值为 ``null`` 的字段**不进 SQL**，
交给数据库默认值。所以"把某列改成 null"用 ``updateById`` 是**做不到**的 ——
Java 一样做不到，照抄。

四个填充列（``MetaObjectHandler``）
-----------------------------------
``insertFill`` 依次填 ``createTime`` / ``createBy`` / ``epsId`` / ``tenantId``；
``updateFill`` 填 ``updateTime`` / ``updateBy``。已经赋值的字段不覆盖。

``tenantId`` 的守卫条件写的是 **``epsId == null``**（第 53 行），而 ``epsId``
是**填之前**读出来的局部变量 —— 也就是说：

* 调用方没传 ``epsId`` -> ``epsId`` 被自动填上，``tenantId`` **也**会被填；
* 调用方自己传了 ``epsId`` -> ``tenantId`` **不填**（哪怕它是 null）。

这是 Java 原代码的笔误（本意大概是 ``tenantId == null``），但线上行为就是它，
这里照抄，见 :class:`MetaObjectFiller`。
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Type, TypeVar

from sqlalchemy import text

from app.common.utils import security_utils as SecurityUtils
from app.config.database import session_scope

E = TypeVar("E", bound=Any)

#: Java: ``@TableLogic(value = "0", delval = "1")`` —— 存在=0、删除=1。
LOGIC_NOT_DELETED = "0"
LOGIC_DELETED = "1"

#: ``<update id="deleteXxxById">update t set del_flag = '1' ...`` 里的列名。
LOGIC_DELETE_COLUMN = "del_flag"


class MetaObjectFiller:
    """Java: ``MyBatisPlusHandlerConfig implements MetaObjectHandler``.

    Java 的 ``setFieldValByName`` 内部有 ``metaObject.hasSetter(name)`` 守卫，
    所以**实体上没有这一列时是空操作**（``ods_*`` / ``dwd_*`` 这些表既没
    ``create_time`` 也没 ``tenant_id``）。这里用 ``hasattr`` 照抄这个语义。
    """

    @staticmethod
    def insert_fill(entity: Any) -> None:
        """Java: ``insertFill(MetaObject)`` —— 顺序与源码一致。"""
        if _readable(entity, "create_time") is None and hasattr(entity, "create_time"):
            entity.create_time = datetime.now()
        if _readable(entity, "create_by") is None and hasattr(entity, "create_by"):
            user_id = SecurityUtils.get_user_id()
            if user_id is not None:
                entity.create_by = user_id
        # 注意：这一句必须在 eps_id 被填之前求值（见模块文档的 tenantId 陷阱）。
        original_eps_id = _readable(entity, "eps_id")
        if original_eps_id is None and hasattr(entity, "eps_id"):
            eps_id = SecurityUtils.get_eps_id()
            if eps_id is not None:
                entity.eps_id = eps_id
        if original_eps_id is None and hasattr(entity, "tenant_id"):
            tenant_id = SecurityUtils.get_tenant_id()
            if tenant_id is not None:
                entity.tenant_id = tenant_id

    @staticmethod
    def update_fill(entity: Any) -> None:
        """Java: ``updateFill(MetaObject)``."""
        if _readable(entity, "update_time") is None and hasattr(entity, "update_time"):
            entity.update_time = datetime.now()
        if _readable(entity, "update_by") is None and hasattr(entity, "update_by"):
            user_id = SecurityUtils.get_user_id()
            if user_id is not None:
                entity.update_by = user_id


def _readable(entity: Any, name: str) -> Any:
    """``getFieldValByName`` 的等价：字段不存在时返回 ``None``。"""
    return getattr(entity, name, None)


class PlusMapper:
    """Java: ``interface XxxMapper extends BaseMapper<Xxx>`` 的公共部分。

    子类只需要声明 ``table`` / ``entity_cls`` / ``columns``。
    """

    #: 物理表名（Java: ``@TableName("...")``）。
    table: str = ""
    #: 对应实体类（``select_by_id`` 用来回填）。
    entity_cls: Type[Any] | None = None
    #: 表里**本实体声明**的列（snake_case），顺序与 Java 字段声明顺序一致。
    #: ``insert`` / ``update_by_id`` 会按这个顺序拼 SQL。
    columns: Tuple[str, ...] = ()
    #: 主键列名（``@TableId``）。
    id_column: str = "id"
    #: ``@TableId(type = ...)``：``ASSIGN_UUID`` 在 ``insert`` 时生成 32 位 hex；
    #: ``ASSIGN_ID`` 生成 19 位雪花号（全局 ``id-type: ASSIGN_ID``，见 application.yml）；
    #: ``INPUT`` / ``AUTO`` 交由调用方或数据库提供。
    id_type: str = "ASSIGN_UUID"
    #: 逻辑删除列（``@TableLogic``）；``None`` 表示这张表没有逻辑删除。
    logic_delete_column: Optional[str] = "del_flag"

    # ---------------------------------------------------------------- insert

    def insert(self, entity: E) -> int:
        """Java: ``BaseMapper.insert(T entity)`` —— 主键由 ``ASSIGN_UUID`` / ``ASSIGN_ID`` 生成后回写。"""
        if not getattr(entity, self.id_column, None):
            if self.id_type == "ASSIGN_UUID":
                # Java: IdType.ASSIGN_UUID -> IdWorker.get32UUID()，32 位小写 hex。
                setattr(entity, self.id_column, _assign_uuid())
            elif self.id_type == "ASSIGN_ID":
                # Java: IdType.ASSIGN_ID -> IdWorker.nextId()，19 位雪花号（字符串形态）。
                setattr(entity, self.id_column, _assign_snowflake())
        MetaObjectFiller.insert_fill(entity)

        table_columns: List[str] = [self.id_column]
        placeholders: List[str] = [":id"]
        params: Dict[str, Any] = {"id": getattr(entity, self.id_column, None)}
        mapping = self._column_mapping()
        for column in self.columns:
            if column == self.id_column:
                continue
            value = getattr(entity, _attribute_for(column, mapping), None)
            if value is None:
                continue
            table_columns.append(column)
            placeholders.append(f":{column}")
            params[column] = value

        sql = (
            f"insert into {self.table} ({', '.join(table_columns)}) "
            f"values ({', '.join(placeholders)})"
        )
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # ----------------------------------------------------------- updateById

    def update_by_id(self, entity: E) -> int:
        """Java: ``BaseMapper.updateById(T entity)`` —— 非 null 列 + 逻辑删除条件。"""
        MetaObjectFiller.update_fill(entity)

        sets: List[str] = []
        params: Dict[str, Any] = {"id": getattr(entity, self.id_column, None)}
        mapping = self._column_mapping()
        for column in self.columns:
            if column == self.id_column:
                continue
            value = getattr(entity, _attribute_for(column, mapping), None)
            if value is None:
                continue
            sets.append(f"{column} = :{column}")
            params[column] = value

        sql = f"update {self.table} set {', '.join(sets)} where {self._id_where()}"
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # ------------------------------------------------------------ deleteById

    def delete_by_id(self, entity_id: Any) -> int:
        """Java: ``BaseMapper.deleteById`` —— 有 ``@TableLogic`` 时是**逻辑**删除。"""
        if self.logic_delete_column is None:
            sql = f"delete from {self.table} where {self.id_column} = :id"
            with session_scope() as session:
                return session.execute(text(sql), {"id": entity_id}).rowcount or 0
        sql = (
            f"update {self.table} set {self.logic_delete_column} = '{LOGIC_DELETED}' "
            f"where {self._id_where()}"
        )
        with session_scope() as session:
            return session.execute(text(sql), {"id": entity_id}).rowcount or 0

    # ------------------------------------------------------------ selectById

    def select_by_id(self, entity_id: Any) -> Optional[Any]:
        """Java: ``BaseMapper.selectById`` —— 只查本实体声明过的列。"""
        selected = ", ".join([self.id_column, *[c for c in self.columns if c != self.id_column]])
        sql = f"select {selected} from {self.table} where {self._id_where()}"
        with session_scope() as session:
            result = session.execute(text(sql), {"id": entity_id})
            keys = list(result.keys())
            row = result.first()
        if row is None:
            return None
        values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
        return (self.entity_cls or dict)(**values)

    # --------------------------------------------------------------- helpers

    def _id_where(self) -> str:
        if self.logic_delete_column is None:
            return f"{self.id_column} = :id"
        return f"{self.id_column} = :id and {self.logic_delete_column} = '{LOGIC_NOT_DELETED}'"

    def _column_mapping(self) -> Dict[str, str]:
        """列名 -> 属性名。默认两者同名（``table-underline: true`` 已由手写列名吸收）。"""
        return {}


def _attribute_for(column: str, mapping: Mapping[str, str]) -> str:
    return mapping.get(column, column)


def _assign_uuid() -> str:
    """Java: MyBatis-Plus ``IdWorker.get32UUID()`` —— 32 位、无连字符、小写。"""
    return uuid.uuid4().hex


#: Java: ``Sequence.twepoch = 1288834974657L``（2010-11-04T01:42:54.657Z）。
_SNOWFLAKE_EPOCH = 1288834974657
#: ``IdWorker`` 是 synchronized 的；这里用同一把锁保证单实例内单调递增。
_SNOWFLAKE_LOCK = threading.Lock()
#: 最近一次生成的时间戳 / 序列号。
_LAST_TIMESTAMP = -1
_LAST_SEQUENCE = 0


def _assign_snowflake() -> str:
    """Java: MyBatis-Plus ``IdWorker.nextId()`` 的雪花号（19 位十进制字符串）。

    位宽与 MP 一致：``41 位毫秒 | 5 位 datacenterId | 5 位 workerId | 12 位序列``，
    datacenterId / workerId 固定取 0（单实例部署）。**具体数值不可比**（时间相关），
    只保证：19 位、全局唯一、随时间递增。
    """
    global _LAST_TIMESTAMP, _LAST_SEQUENCE

    with _SNOWFLAKE_LOCK:
        timestamp = int(time.time() * 1000)
        if timestamp < _LAST_TIMESTAMP:
            # 时钟回拨：Java 侧会抛异常，这里退化成沿用上一毫秒等待序列。
            timestamp = _LAST_TIMESTAMP
        if timestamp == _LAST_TIMESTAMP:
            _LAST_SEQUENCE = (_LAST_SEQUENCE + 1) & 0xFFF
            if _LAST_SEQUENCE == 0:
                # 同毫秒 4096 个用尽 -> 等下一毫秒（Java 的 tilNextMillis）。
                while timestamp <= _LAST_TIMESTAMP:
                    timestamp = int(time.time() * 1000)
        else:
            _LAST_SEQUENCE = 0
        _LAST_TIMESTAMP = timestamp
        value = ((timestamp - _SNOWFLAKE_EPOCH) << 22) | _LAST_SEQUENCE
        return str(value)


# --------------------------------------------------------------------------- 共享语句
#
# ``base`` 包里二十多份 XML 的 ``deleteXxxById`` / ``deleteXxxByIds`` / ``truncateTable``
# 是同一段 SQL 的复制粘贴（``update t set del_flag = '1' where id in (...)``）。
# 三个小函数把它们集中在这里，Mapper 只声明表名与主键列，避免 20 份手写 SQL 各自漂移。


def logic_delete_by_id(table: str, id_column: str, entity_id: Any) -> int:
    """Java: ``<update id="deleteXxxById">update t set del_flag = '1' where id = #{id}``."""
    sql = f"update {table} set {LOGIC_DELETE_COLUMN} = '{LOGIC_DELETED}' where {id_column} = :id"
    with session_scope() as session:
        return session.execute(text(sql), {"id": entity_id}).rowcount or 0


def logic_delete_by_ids(table: str, id_column: str, entity_ids: Sequence[Any]) -> int:
    """Java: ``... where id in <foreach collection="array" open="(" ...>``.

    空数组时 MyBatis 生成 ``where id in ()`` —— MySQL 直接报语法错误；这条边界
    在 Java 侧就是 500，这里保持同样的失败方式（``:id0`` 一个都没有 -> 非法 SQL）。
    """
    placeholders = ", ".join(f":id{index}" for index in range(len(entity_ids)))
    params = {f"id{index}": value for index, value in enumerate(entity_ids)}
    sql = (
        f"update {table} set {LOGIC_DELETE_COLUMN} = '{LOGIC_DELETED}' "
        f"where {id_column} in ({placeholders})"
    )
    with session_scope() as session:
        return session.execute(text(sql), params).rowcount or 0


def truncate_table(table: str) -> int:
    """Java: ``<update id="truncateTable">truncate table t``."""
    with session_scope() as session:
        return session.execute(text(f"truncate table {table}")).rowcount or 0


__all__ = [
    "PlusMapper",
    "MetaObjectFiller",
    "LOGIC_DELETED",
    "LOGIC_NOT_DELETED",
    "logic_delete_by_id",
    "logic_delete_by_ids",
    "truncate_table",
]
