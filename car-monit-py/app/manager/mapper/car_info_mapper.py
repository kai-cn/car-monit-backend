"""车辆信息 Mapper.

# Migrated from: com/ruoyi/manager/mapper/CarInfoMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/manager/CarInfoMapper.xml

标准 ``manager`` 模板：62 条 ``<if>`` + ``order by t.create_time desc,t.id``。

三条模板表达不了的部分（手工补）
--------------------------------
1. ``selectCarInfoVo`` 后面还拼了 ``,concat(sd.dept_name, ' ', su.nick_name)
   createInfo`` —— 别名列**不在** ``resultMap`` 里，但 MyBatis 的
   ``autoMappingBehavior=PARTIAL`` 会按属性名把它自动映射到 ``createInfo`` 上，
   所以响应里有值（见 :func:`~app.base.mapper.ods_sql.map_row`）。
2. ``WHERE`` 里紧跟固定前缀的是一段 ``not exists``（把「有异常记录且全部已处理」
   的车牌排除掉），已并进 ``where_prefix``。
3. 最后一条 ``<if test="flag != null and flag == 'noTrack'">`` 是多行子查询，
   生成器判据不支持 —— 用 ``fragment_before(None, ...)`` 补在 ``order by`` 前。

另外 3 条语句不在模板里：``getCarLocation`` / ``selectCarVoList`` /
``isExitsCar``。``selectCarVoList`` 多选的 ``t.id`` 与 ``t.escaped_type_name``
在 ``CarInfoVO`` 上没有对应属性，MyBatis 直接丢弃，所以响应只有 4 个字段。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.base.mapper.ods_sql import If, map_row
from app.common.utils.common_util import is_not_blank
from app.config.database import session_scope
from app.manager.domain.car_info import CarInfo
from app.manager.domain.vo.bigscreen.car_info_vo import CarInfoVO
from app.manager.domain.vo.bigscreen.car_location_param import CarLocationParam
from app.manager.domain.vo.bigscreen.car_location_vo import CarLocationVO
from app.manager.mapper.manager_mapper import ManagerListMapper

#: Java: ``<sql id="selectCarInfoVo">``
SELECT_CAR_INFO_VO = """
        t.id,
        t.car_no,
        t.car_type,
        t.car_vehicle,
        t.car_num,
        t.escaped_type,
        t.escaped_type_name,
        t.escaped_amount,
        t.escaped_num,
        t.return_amount,
        t.total_amount,
        t.charge_amount,
        t.dif_amount,
        t.auit_org_id,
        t.auit_org_name,
        t.is_white,
        t.white_remark,
        t.file_ids,
        t.brand,
        t.plate_color,
        t.plate_type,
        t.car_color,
        t.data_source,
        t.data_source_name,
        t.last_pass_time,
        t.last_pass_picture,
        t.last_pass_type,
        t.last_pass_address,
        t.last_pass_longitude,
        t.last_pass_latitude,
        t.last_pass_cardirection,
        t.road_section_id,
        t.section_code,
        t.road_section_name,
        t.next_pass_time,
        t.next_pass_type,
        t.next_pass_address,
        t.next_pass_longitude,
        t.next_pass_latitude,
        t.track_id,
        t.org_id,
        t.org_code,
        t.org_name,
        t.gantry_code,
        t.road_code,
        t.road_name,
        t.toll_code,
        t.toll_name,
        t.link_name,
        t.link_phone,
        t.fwqbm,
        t.fwqmc,
        t.back_col1,
        t.back_col2,
        t.remark,
        t.status,
        t.sort,
        t.eps_id,
        t.del_flag,
        t.create_by,
        t.create_time,
        t.update_by,
        t.update_time,
        t.tenant_id
"""

#: ``resultMap`` 的 65 列。
RESULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "car_no",
    "car_type",
    "car_vehicle",
    "car_num",
    "escaped_type",
    "escaped_type_name",
    "escaped_amount",
    "escaped_num",
    "return_amount",
    "total_amount",
    "charge_amount",
    "dif_amount",
    "auit_org_id",
    "auit_org_name",
    "is_white",
    "white_remark",
    "file_ids",
    "brand",
    "plate_color",
    "plate_type",
    "car_color",
    "data_source",
    "data_source_name",
    "last_pass_time",
    "last_pass_picture",
    "last_pass_type",
    "last_pass_address",
    "last_pass_longitude",
    "last_pass_latitude",
    "last_pass_cardirection",
    "road_section_id",
    "section_code",
    "road_section_name",
    "next_pass_time",
    "next_pass_type",
    "next_pass_address",
    "next_pass_longitude",
    "next_pass_latitude",
    "track_id",
    "track_josn",
    "org_id",
    "org_code",
    "org_name",
    "gantry_code",
    "road_code",
    "road_name",
    "toll_code",
    "toll_name",
    "link_name",
    "link_phone",
    "fwqbm",
    "fwqmc",
    "back_col1",
    "back_col2",
    "remark",
    "status",
    "sort",
    "eps_id",
    "del_flag",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "tenant_id",
)

#: ``selectCarInfoList`` 的 62 条 ``<if>``（顺序照抄 XML）。
CONDITIONS: Tuple[If, ...] = (
    If("id", "id"),
    If("car_no", "car_no"),
    If("car_type", "car_type"),
    If("car_vehicle", "car_vehicle"),
    If("car_num", "car_num", null_only=True),
    If("escaped_type", "escaped_type", like=True),
    If("escaped_type_name", "escaped_type_name", like=True),
    If("escaped_amount", "escaped_amount", null_only=True),
    If("escaped_num", "escaped_num", null_only=True),
    If("return_amount", "return_amount", null_only=True),
    If("total_amount", "total_amount", null_only=True),
    If("charge_amount", "charge_amount", null_only=True),
    If("dif_amount", "dif_amount", null_only=True),
    If("auit_org_id", "auit_org_id"),
    If("auit_org_name", "auit_org_name", like=True),
    If("is_white", "is_white"),
    If("white_remark", "white_remark"),
    If("file_ids", "file_ids"),
    If("brand", "brand"),
    If("plate_color", "plate_color"),
    If("plate_type", "plate_type"),
    If("car_color", "car_color"),
    If("data_source", "data_source"),
    If("data_source_name", "data_source_name", like=True),
    If("last_pass_time", "last_pass_time", null_only=True),
    If("last_pass_picture", "last_pass_picture"),
    If("last_pass_type", "last_pass_type"),
    If("last_pass_address", "last_pass_address"),
    If("last_pass_longitude", "last_pass_longitude"),
    If("last_pass_latitude", "last_pass_latitude"),
    If("last_pass_cardirection", "last_pass_cardirection"),
    If("road_section_id", "road_section_id"),
    If("section_code", "section_code"),
    If("road_section_name", "road_section_name", like=True),
    If("next_pass_time", "next_pass_time", null_only=True),
    If("next_pass_type", "next_pass_type"),
    If("next_pass_address", "next_pass_address"),
    If("next_pass_longitude", "next_pass_longitude"),
    If("next_pass_latitude", "next_pass_latitude"),
    If("org_id", "org_id"),
    If("org_code", "org_code"),
    If("org_name", "org_name", like=True),
    If("gantry_code", "gantry_code"),
    If("road_code", "road_code"),
    If("road_name", "road_name", like=True),
    If("toll_code", "toll_code"),
    If("toll_name", "toll_name", like=True),
    If("link_name", "link_name", like=True),
    If("link_phone", "link_phone"),
    If("fwqbm", "fwqbm"),
    If("fwqmc", "fwqmc"),
    If("back_col1", "back_col1"),
    If("back_col2", "back_col2"),
    If("status", "status"),
    If("sort", "sort", null_only=True),
    If("eps_id", "eps_id", null_only=True),
    If("tenant_id", "tenant_id", null_only=True),
    If("create_by", "create_by", null_only=True),
    If("car_no_query", "car_no", like=True),
    If(
        "apply_time1",
        "create_time",
        template="and t.create_time >= STR_TO_DATE({p},'%Y-%m-%d')",
    ),
    If(
        "apply_time2",
        "create_time",
        template="and t.create_time < date_add(STR_TO_DATE({p},'%Y-%m-%d'), interval 1 day)",
    ),
    If(
        "create_info",
        "sd.dept_name",
        template="and sd.dept_name like concat('%', {p}, '%')",
    ),
)


class CarInfoMapper(ManagerListMapper):
    """Java: ``interface CarInfoMapper extends BaseMapper<CarInfo>``."""

    table = "car_info"
    select_vo = SELECT_CAR_INFO_VO
    entity_cls = CarInfo
    result_columns = RESULT_COLUMNS
    conditions = CONDITIONS
    from_clause = "car_info t left join sys_user su on su.user_id = t.create_by left join sys_dept sd on t.eps_id = sd.dept_id"
    where_prefix = "t.del_flag = '0' and not exists ( select 1 from (select t1.car_no, sum(case when t1.status = '0' then 1 else 0 end) except_num, count(1) count_num from car_except_record t1 where t1.del_flag = '0' group by t1.car_no ) k where t.car_no = k.car_no and k.count_num > 0 and k.except_num = 0 )"
    #: Java: ``,concat(sd.dept_name, ' ', su.nick_name) createInfo``（由自动映射落到实体属性）
    select_suffix = ",concat(sd.dept_name, ' ', su.nick_name) createInfo"
    #: Java: ``selectCarInfoById`` 的 ``,t.track_josn``
    detail_suffix = ",t.track_josn"

    # Java: <if test="flag != null and flag == 'noTrack'"> ... </if>
    def fragment_before(
        self, anchor: Optional[str], query: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """XML 最后一条 ``<if>``：只保留「没有轨迹点」的车。"""
        if anchor is not None:
            return "", {}
        flag = getattr(query, "flag", None)
        if flag is None or flag != "noTrack":
            return "", {}
        return (
            "and not exists ( select 1 from zdata_trail_tracks tr "
            "where tr.plate_key = t.car_no )",
            {},
        )

    # Java: CarInfo selectCarInfoById(String id)
    def select_by_id(self, entity_id: Any) -> Optional[CarInfo]:
        """详情语句 —— ``from car_info t``（**不带** join，也不带 ``del_flag``）。"""
        sql = (
            f"select {self.select_vo}{self.detail_suffix} from car_info t "
            f"where t.id = :id"
        )
        with session_scope() as session:
            row = session.execute(text(sql), {"id": entity_id}).first()
        if row is None:
            return None
        # ``track_josn`` 也在 resultMap 里，所以能映射进去（列表语句不选它）
        return map_row(CarInfo, RESULT_COLUMNS, row)

    # Java: List<CarLocationVO> getCarLocation(CarLocationParam param)
    def get_car_location(self, param: CarLocationParam) -> List[CarLocationVO]:
        """大屏地图描点（当前未被调用 —— Service 已改成读 Redis；照抄保留）。"""
        sql = (
            "select t.id, t.car_no, t.car_type, t.last_pass_longitude as lonStr, "
            "t.last_pass_latitude as latStr, t.status from car_info t "
            "WHERE t.del_flag = '0' and t.status = '1'"
        )
        params: Dict[str, Any] = {}
        # 4 个编码条件**全部**打的是 t.gantry_code（Java 原文如此）
        for name in ("fwqbm", "gantry_code", "toll_code", "road_code"):
            value = getattr(param, name, None)
            if is_not_blank(value):
                sql += f" and t.gantry_code like concat('%', :{name}, '%')"
                params[name] = value
        if is_not_blank(param.escaped_type):
            sql += " and t.escaped_type like concat('%', :escaped_type, '%')"
            params["escaped_type"] = param.escaped_type
        if is_not_blank(param.car_no_query):
            sql += " and t.car_no like concat('%', :car_no_query, '%')"
            params["car_no_query"] = param.car_no_query

        with session_scope() as session:
            rows = session.execute(text(sql), params).all()
        result: List[CarLocationVO] = []
        for row in rows:
            values = dict(row._mapping)
            vo = CarLocationVO()
            vo.id = values.get("id")
            vo.car_no = values.get("car_no")
            vo.car_type = values.get("car_type")
            vo.lon_str = values.get("lonStr")
            vo.lat_str = values.get("latStr")
            vo.status = values.get("status")
            result.append(vo)
        return result

    # Java: List<CarInfoVO> selectCarVoList()
    def select_car_vo_list(self) -> List[CarInfoVO]:
        """大屏：重点车辆库统计 前 10 条。"""
        sql = (
            "select t.id, t.car_no, t.car_type, t.escaped_type, "
            "t.escaped_type_name, t.escaped_amount from car_info t "
            "WHERE t.del_flag = '0' order by t.create_time desc,t.id limit 10"
        )
        with session_scope() as session:
            rows = session.execute(text(sql)).all()
        result: List[CarInfoVO] = []
        for row in rows:
            values = dict(row._mapping)
            # ``id`` / ``escaped_type_name`` 在 CarInfoVO 上没有属性 -> 丢弃
            result.append(
                CarInfoVO(
                    car_no=values.get("car_no"),
                    car_type=values.get("car_type"),
                    escaped_type=values.get("escaped_type"),
                    escaped_amount=values.get("escaped_amount"),
                )
            )
        return result

    # Java: int isExitsCar(CarInfoVO vo) —— 判断车辆是否存在
    def is_exits_car(self, vo: Any) -> int:
        sql = "select count(1) from car_info t where t.del_flag = '0' and t.car_no = :car_no"
        params: Dict[str, Any] = {"car_no": getattr(vo, "car_no", None)}
        entity_id = getattr(vo, "id", None)
        if is_not_blank(entity_id):
            sql += " and t.id != :id"
            params["id"] = entity_id
        with session_scope() as session:
            return int(session.execute(text(sql), params).scalar() or 0)

__all__ = [
    "CarInfoMapper",
    "CONDITIONS",
    "RESULT_COLUMNS",
    "SELECT_CAR_INFO_VO",
]
