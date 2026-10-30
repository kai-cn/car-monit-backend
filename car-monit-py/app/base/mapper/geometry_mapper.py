"""几何对象.

# Migrated from: com/ruoyi/base/mapper/GeometryMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml

生成器模板：``list`` / ``{pk}`` / 单行删除 / 批量删除，外加一条手写语句
``syncAllGeometry``（几何数据的增量补齐，见文件末尾）。
``<if>`` 判据逐条照抄（``!= ''`` -> 空串跳过）。
"""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import text

from app.base.mapper.plus_mapper import logic_delete_by_id, logic_delete_by_ids
from app.base.domain.geometry import Geometry
from app.base.mapper.ods_sql import If, OdsListMapper, map_row
from app.config.database import session_scope

#: Verbatim from ``<sql>``（注意 ``t.`` 前缀）。
SELECT_GEOMETRY_VO = """
        t.id,
        t.lxbh,
        t.lxfx,
        t.qdzh,
        t.zdzh,
        t.paths
    
"""

#: resultMap 声明的 6 列（**SQL 列名**，即行键）。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "lxbh",
    "lxfx",
    "qdzh",
    "zdzh",
    "paths",
)

#: ``selectGeometryList`` 的 6 条 ``<if>``。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("lxbh", "lxbh"),
    If("lxfx", "lxfx"),
    If("qdzh", "qdzh", null_only=True),
    If("zdzh", "zdzh", null_only=True),
    If("paths", "paths"),
)


class GeometryMapper(OdsListMapper):
    """Java: ``interface GeometryMapper``."""

    table = "geometry"
    select_vo = SELECT_GEOMETRY_VO
    entity_cls = Geometry
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    order_by = "lxbh,t.qdzh"
    detail_column = "id"
    #: Java: ``@TableId(value = "id", type = IdType.INPUT)``（Integer 主键，由调用方给）
    id_type = "INPUT"

    # Java: int deleteGeometryByIds(Integer[] IDs)
    def delete_geometry_by_ids(self, entity_ids):
        return logic_delete_by_ids(self.table, "id", entity_ids)

    # Java: int deleteGeometryById(Integer ID)
    def delete_geometry_by_id(self, entity_id) -> int:
        return logic_delete_by_id(self.table, "id", entity_id)

    # Java: List<Geometry> syncAllGeometry()
    def sync_all_geometry(self) -> List[Geometry]:
        """XML 原文：以 ``geometry_copy1`` 为基准，找出当前表**还没补到末桩号**的路线。

        返回的 ``qdzh`` 是 ``ifnull(t2.zdzh, t1.qdzh)``（别名列），其余字段为
        ``null`` —— 与 ``resultMap`` 只映射 3 列一致。
        """
        sql = (
            "select t1.lxbh, t1.lxfx, IFNULL(t2.zdzh,t1.qdzh) qdzh "
            "from (select lxbh, lxfx, min(qdzh) qdzh, max(zdzh) zdzh "
            "      FROM geometry_copy1 group by lxbh, lxfx) t1 "
            "left join (select lxbh, lxfx, min(qdzh) qdzh, max(zdzh) zdzh "
            "           FROM geometry group by lxbh, lxfx) t2 "
            "on t1.lxbh = t2.lxbh and t1.lxfx = t2.lxfx "
            "where t2.zdzh is null or t2.zdzh < t1.zdzh "
            "order by t1.lxbh"
        )
        with session_scope() as session:
            rows = session.execute(text(sql)).all()
        return [map_row(Geometry, ("lxbh", "lxfx", "qdzh"), row) for row in rows]


__all__ = ["GeometryMapper", "RESULT_COLUMNS", "CONDITIONS"]
