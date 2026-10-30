"""通知公告表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysNoticeMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml

XML 里共 6 条 statement，本模块**全部迁移**（``deleteNoticeById`` 在 Java 侧
没有任何控制器调用，但按迁移原则第 4 条照留）。

``selectNoticeVo`` 的两个坑
---------------------------
1. ``cast(t.notice_content as char) as notice_content``
   ``notice_content`` 是 ``longtext``；MySQL 驱动把 ``longtext`` 直接读成 ``String``
   本来没问题，但这里显式 ``cast`` 成 ``char`` —— **照抄**，不要"简化"成
   ``t.notice_content``。差别体现在字符集/排序上，客户端看不出，但 SQL 文本是规范。
2. 列清单里**没有** ``params``，也没有 ``searchValue`` —— ``resultMap`` 也不声明它们，
   所以这两项永远不会从数据库带值回来（只由请求参数填）。

``selectNoticeList`` 的 ``<where>``
-----------------------------------
8 个 ``<if>``，判据分三类，不同类不能统一：

===============================  ==================================  ==========================
字段                              判据                                 传 ``""`` 时
===============================  ==================================  ==========================
``noticeTitle`` / ``noticeType``  ``!= null and != ''``                条件跳过
``status`` / ``bussId`` /
``bussName`` / ``noticeContent``
``createBy``                      **只有** ``!= null``                  条件生效（查空串作者）
``tenantId``                      **只有** ``!= null``                  条件生效
===============================  ==================================  ==========================

``tenantId`` 那一行还带了一个写死的兜底：``and (t.TENANT_ID = #{tenantId} or
t.TENANT_ID = 100)`` —— 也就是**永远能看到 100 号租户的数据**。这是 Java 原样
（100 是内置的"公共/平台"租户），不要改成纯等值。

注意列名大小写：这两处写的是 ``TENANT_ID``，而投影里是 ``t.tenant_id``。
MySQL 在 Linux 上**列名不区分大小写**，所以能跑；换个严格大小写的库就会炸。
照抄。

``order by t.create_time desc``
-------------------------------
这条语句**自带** ``order by``，分页时不会追加客户端排序列
（见 :mod:`app.common.core.page.page_helper` 的 ``_has_order_by`` 分支与
``COMPATIBILITY.md`` §25.6）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_notice import SysNotice
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysNoticeMapper.xml -> ``<sql id="selectNoticeVo">``.
SELECT_NOTICE_VO = """
        select t.notice_id,
               t.notice_title,
               t.notice_type,
               cast(t.notice_content as char) as notice_content,
               t.status,
               t.create_by,
               t.create_time,
               t.update_by,
               t.update_time,
               t.remark,
               t.buss_id,
               t.buss_name,
               t.tenant_id
        from sys_notice t
"""

#: Verbatim from SysNoticeMapper.xml -> ``<select id="selectNoticeById">`` 的 where.
_SELECT_NOTICE_BY_ID_WHERE = "where t.notice_id = :notice_id"

#: Verbatim from SysNoticeMapper.xml -> ``<select id="selectNoticeList">`` 的排序.
_SELECT_NOTICE_LIST_ORDER_BY = "order by t.create_time desc"

#: Verbatim from SysNoticeMapper.xml -> ``<delete id="deleteNoticeById">``.
_DELETE_NOTICE_BY_ID = "delete from sys_notice where notice_id = :notice_id"

#: ``insertNotice`` 里**有** ``<if>`` 的列，顺序与 XML 一致。
#: ``create_time`` 不在表里：它是无条件的一列（``sysdate()``）。
_INSERT_NOTICE_COLUMNS: Tuple[str, ...] = (
    "notice_title",
    "notice_type",
    "notice_content",
    "status",
    "remark",
    "create_by",
    "buss_id",
    "buss_name",
    "tenant_id",
)

#: ``insertNotice`` 里判据是 ``!= null``（**不看**空串）的三列。
_INSERT_NOTICE_NULL_ONLY: Tuple[str, ...] = ("buss_id", "buss_name", "tenant_id")

#: ``updateNotice`` 的 ``<set>`` 分支，顺序与 XML 一致。
#: 第三项 ``require_text`` 对应 ``!= null and != ''``；``notice_content`` 只有 ``!= null``。
#: ``tenant_id`` **不在** 这里 —— 修改公告不会改租户。
_UPDATE_NOTICE_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("notice_title", "notice_title", True),
    ("notice_type", "notice_type", True),
    ("notice_content", "notice_content", False),
    ("status", "status", True),
    ("update_by", "update_by", True),
    ("buss_id", "buss_id", True),
    ("buss_name", "buss_name", True),
)

#: ``SysNoticeResult`` resultMap 声明的 13 列（顺序与 ``<resultMap>`` 一致）。
_NOTICE_COLUMNS: Tuple[str, ...] = (
    "notice_id",
    "notice_title",
    "notice_type",
    "notice_content",
    "status",
    "create_by",
    "create_time",
    "update_by",
    "update_time",
    "remark",
    "buss_id",
    "buss_name",
    "tenant_id",
)


class SysNoticeMapper:
    """Java: ``interface SysNoticeMapper``."""

    # Java: List<SysNotice> selectNoticeList(SysNotice notice)
    def select_notice_list(self, notice: SysNotice) -> List[SysNotice]:
        """公告列表（``startPage()`` 之后的第一条 select，分页点在这里）。"""
        data_sql, params = _build_notice_list_sql(notice)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_notice(row, list(_NOTICE_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: SysNotice selectNoticeById(Long noticeId)
    def select_notice_by_id(self, notice_id: int) -> Optional[SysNotice]:
        """``selectOne`` 语义：无行时返回 ``None``（Java 返回 ``null``）。"""
        sql = SELECT_NOTICE_VO + " " + _SELECT_NOTICE_BY_ID_WHERE
        with session_scope() as session:
            result = session.execute(text(sql), {"notice_id": notice_id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_notice(rows[0], keys)

    # Java: int insertNotice(SysNotice notice)  -- useGeneratedKeys="true" keyProperty="noticeId"
    def insert_notice(self, notice: SysNotice) -> int:
        """动态列插入；回写 ``notice.notice_id``（MyBatis ``keyProperty`` 的等价物）。

        与 ``sys_post`` 不同：这里**没有** ``notice_id`` 的 ``<if>``，
        所以入参带的 id 会被丢弃、永远由数据库自增生成。
        """
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute in _INSERT_NOTICE_COLUMNS:
            value = getattr(notice, attribute)
            if value is None:
                continue
            if attribute not in _INSERT_NOTICE_NULL_ONLY and value == "":
                continue
            columns.append(attribute)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into sys_notice ({','.join(columns)}) values ({','.join(names)})"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            notice.notice_id = result.lastrowid
            return result.rowcount or 0

    # Java: int updateNotice(SysNotice notice)
    def update_notice(self, notice: SysNotice) -> int:
        sql, params = _build_update_sql(notice)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteNoticeById(Long noticeId)
    def delete_notice_by_id(self, notice_id: int) -> int:
        with session_scope() as session:
            return session.execute(text(_DELETE_NOTICE_BY_ID), {"notice_id": notice_id}).rowcount or 0

    # Java: int deleteNoticeByIds(Long[] noticeIds)
    def delete_notice_by_ids(self, notice_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("notice_id", notice_ids, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_notice where {clause}"), params).rowcount or 0


def _build_notice_list_sql(notice: SysNotice) -> Tuple[str, Dict[str, Any]]:
    """``selectNoticeList`` 的 ``<where>`` + 固定的 ``order by``。

    条件判据严格照抄 OGNL 的 ``x != null and x != ''``（**不是** ``isBlank``），
    所以 ``noticeTitle = " "`` 会真的去 ``like '% %'``。

    片段**不带**前导 ``AND``：MyBatis 的 ``<where>`` 会吃掉首个 ``AND`` / ``OR``，
    这里直接把片段按顺序 ``and`` 拼接（否则会拼出非法的 ``where AND a``）。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    def text_equals(attribute: str, fragment: str) -> None:
        """``<if test="x != null and x != ''">``。"""
        value = getattr(notice, attribute, None)
        if value is None or value == "":
            return
        conditions.append(fragment.format(name=f":{attribute}"))
        params[attribute] = value

    def not_null(attribute: str, fragment: str) -> None:
        """``<if test="x != null">`` —— 空串也算"有值"。"""
        value = getattr(notice, attribute, None)
        if value is None:
            return
        conditions.append(fragment.format(name=f":{attribute}"))
        params[attribute] = value

    # 顺序与 XML 的 <if> 序列一致
    text_equals("notice_title", "t.notice_title like concat('%', {name}, '%')")
    text_equals("notice_type", "t.notice_type = {name}")
    not_null("create_by", "t.create_by = {name}")
    text_equals("status", "t.status = {name}")
    text_equals("buss_id", "t.buss_id = {name}")
    text_equals("buss_name", "t.buss_name like concat('%', {name}, '%')")
    # 100 是写死的"公共租户"，Java 原样
    not_null("tenant_id", "(t.TENANT_ID = {name} or t.TENANT_ID = 100)")
    text_equals("notice_content", "(t.notice_content = {name})")

    sql = SELECT_NOTICE_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    sql = sql + " " + _SELECT_NOTICE_LIST_ORDER_BY + "\n"
    return sql, params


def _build_update_sql(notice: SysNotice) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_notice set ... where notice_id = :notice_id``（Java: ``<set>``）。

    ``update_time = sysdate()`` 是**无条件**的，所以 ``<set>`` 永不为空。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in _UPDATE_NOTICE_COLUMNS:
        value = getattr(notice, attribute)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["notice_id"] = notice.notice_id

    sql = "update sys_notice set " + ", ".join(sets) + " where notice_id = :notice_id"
    return sql, params


def _map_notice(row: Any, keys: Sequence[str]) -> SysNotice:
    """One result row -> one ``SysNotice`` (Java: ``resultMap="SysNoticeResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields = {name: values[name] for name in _NOTICE_COLUMNS if name in values}
    return SysNotice(**fields)


__all__ = ["SysNoticeMapper", "SELECT_NOTICE_VO"]
