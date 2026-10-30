"""岗位表 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysPostMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml

XML 里共 10 条 statement，本模块**全部迁移**（``sys_user`` 切片先迁了 3 条，
``sys_post`` 切片补齐剩下 7 条）。

``selectPostVo`` 有意思的地方
----------------------------
它声明的列是 ``post_id, post_code, post_name, post_sort, status, create_by,
create_time, remark`` —— **没有** ``update_by`` / ``update_time``。于是
``SysPost.updateBy`` 永远是 ``null``，JSON 里照样输出 ``"updateBy":null``。
``resultMap`` 声明了这两列只是"允许映射"，``<sql>`` 不 select 就不会有值。
所有走 ``selectPostVo`` 的语句（list / all / byId / checkUnique×2）都继承这个行为，
**不要**顺手把两列补进投影 —— 前端"修改时间"列会因此从空变成有值。

动态 SQL 与 Java 的对应
-----------------------
=============  ==========================================================
XML 片段         Python
=============  ==========================================================
``<where>``     :func:`_build_post_list_sql` 用 ``where a and b`` 拼接
``<set>``       :func:`_build_update_sql` 用 ``, `` 拼接并补 ``update_time``
``<foreach>``   :func:`app.system.mapper.sys_user_role_mapper._in_clause`
=============  ==========================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_post import SysPost
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysPostMapper.xml -> ``<sql id="selectPostVo">``.
SELECT_POST_VO = """
        select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark 
		from sys_post
"""

#: Verbatim from SysPostMapper.xml -> ``<select id="selectPostAll">``.
_SELECT_POST_ALL = SELECT_POST_VO

#: Verbatim from SysPostMapper.xml -> ``<select id="selectPostById">`` 的 where.
_SELECT_POST_BY_ID_WHERE = "where post_id = :post_id"

#: Verbatim from SysPostMapper.xml -> ``<select id="selectPostListByUserId">``.
_SELECT_POST_LIST_BY_USER_ID = """
		select p.post_id
        from sys_post p
	        left join sys_user_post up on up.post_id = p.post_id
	        left join sys_user u on u.user_id = up.user_id
	    where u.user_id = :user_id
"""

#: Verbatim from SysPostMapper.xml -> ``<select id="selectPostsByUserName">``.
_SELECT_POSTS_BY_USER_NAME = """
		select p.post_id, p.post_name, p.post_code
		from sys_post p
			 left join sys_user_post up on up.post_id = p.post_id
			 left join sys_user u on u.user_id = up.user_id
		where u.user_name = :user_name
"""

#: Verbatim from SysPostMapper.xml -> ``<select id="checkPostNameUnique">``.
_CHECK_POST_NAME_UNIQUE_WHERE = "where post_name=:post_name limit 1"

#: Verbatim from SysPostMapper.xml -> ``<select id="checkPostCodeUnique">``.
_CHECK_POST_CODE_UNIQUE_WHERE = "where post_code=:post_code limit 1"

#: Verbatim from SysPostMapper.xml -> ``<delete id="deletePostById">``.
_DELETE_POST_BY_ID = "delete from sys_post where post_id = :post_id"

#: ``insertPost`` 的可选列，顺序与 XML 一致（``post_id`` 单独处理，判据是 ``!= 0``）。
_INSERT_POST_COLUMNS: Tuple[Tuple[str, str], ...] = (
    ("post_code", "post_code"),
    ("post_name", "post_name"),
    ("post_sort", "post_sort"),
    ("status", "status"),
    ("remark", "remark"),
    ("create_by", "create_by"),
)

#: ``updatePost`` 的 ``<set>`` 分支，顺序与 XML 一致。
#: 第三项 ``require_text`` 对应 ``!= null and != ''``；``remark`` 只有 ``!= null``。
_UPDATE_POST_COLUMNS: Tuple[Tuple[str, str, bool], ...] = (
    ("post_code", "post_code", True),
    ("post_name", "post_name", True),
    ("post_sort", "post_sort", True),
    ("status", "status", True),
    ("remark", "remark", False),
    ("update_by", "update_by", True),
)

#: ``selectPostVo`` 实际投影的列（``resultMap="SysPostResult"`` 的子集）。
_POST_COLUMNS = ("post_id", "post_code", "post_name", "post_sort", "status", "create_by", "create_time", "remark")


class SysPostMapper:
    """Java: ``interface SysPostMapper``."""

    # Java: List<SysPost> selectPostList(SysPost post)
    def select_post_list(self, post: SysPost) -> List[SysPost]:
        """岗位列表（分页点在 ``startPage()`` 之后的第一条 select，即这里）。"""
        data_sql, params = _build_post_list_sql(post)
        # PageHelper 的 count 策略：把原语句包成子查询再 count。
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_post(row, list(_POST_COLUMNS)) for row in page_list]
        return PageList(mapped, total=page_list.total, page_num=page_list.page_num, page_size=page_list.page_size)

    # Java: List<SysPost> selectPostAll()
    def select_post_all(self) -> List[SysPost]:
        with session_scope() as session:
            result = session.execute(text(_SELECT_POST_ALL))
            keys = list(result.keys())
            return [_map_post(row, keys) for row in result.all()]

    # Java: SysPost selectPostById(Long postId)
    def select_post_by_id(self, post_id: int) -> Optional[SysPost]:
        """``selectOne`` 语义：无行时返回 ``None``（Java 返回 ``null``）。"""
        sql = SELECT_POST_VO + " " + _SELECT_POST_BY_ID_WHERE
        with session_scope() as session:
            result = session.execute(text(sql), {"post_id": post_id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_post(rows[0], keys)

    # Java: List<Integer> selectPostListByUserId(Long userId)
    def select_post_list_by_user_id(self, user_id: int) -> List[int]:
        """这返回的是**岗位 id 列表**，不是 ``SysPost``（``resultType="Integer"``）。"""
        with session_scope() as session:
            result = session.execute(text(_SELECT_POST_LIST_BY_USER_ID), {"user_id": user_id})
            return [row[0] for row in result.all()]

    # Java: List<SysPost> selectPostsByUserName(String userName)
    def select_posts_by_user_name(self, user_name: str) -> List[SysPost]:
        with session_scope() as session:
            result = session.execute(text(_SELECT_POSTS_BY_USER_NAME), {"user_name": user_name})
            keys = list(result.keys())
            return [_map_post(row, keys) for row in result.all()]

    # Java: SysPost checkPostNameUnique(String postName)
    def check_post_name_unique(self, post_name: str) -> Optional[SysPost]:
        sql = SELECT_POST_VO + " " + _CHECK_POST_NAME_UNIQUE_WHERE
        return self._select_one(sql, {"post_name": post_name})

    # Java: SysPost checkPostCodeUnique(String postCode)
    def check_post_code_unique(self, post_code: str) -> Optional[SysPost]:
        sql = SELECT_POST_VO + " " + _CHECK_POST_CODE_UNIQUE_WHERE
        return self._select_one(sql, {"post_code": post_code})

    # Java: int insertPost(SysPost post)  -- useGeneratedKeys="true" keyProperty="postId"
    def insert_post(self, post: SysPost) -> int:
        """动态列插入；回写 ``post.post_id``（MyBatis ``keyProperty`` 的等价物）。

        ``create_time`` 在 XML 里是**无条件**的一列（``sysdate()``），所以列清单永远非空。
        """
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        # Java: <if test="postId != null and postId != 0">post_id,</if>
        if post.post_id is not None and post.post_id != 0:
            columns.append("post_id")
            names.append(":post_id")
            params["post_id"] = post.post_id

        for attribute, column in _INSERT_POST_COLUMNS:
            value = getattr(post, attribute)
            if value is None or value == "":
                continue
            columns.append(column)
            names.append(f":{attribute}")
            params[attribute] = value

        columns.append("create_time")
        names.append("sysdate()")

        sql = f"insert into sys_post({','.join(columns)})values({','.join(names)})"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            post.post_id = result.lastrowid
            return result.rowcount or 0

    # Java: int updatePost(SysPost post)
    def update_post(self, post: SysPost) -> int:
        sql, params = _build_update_sql(post)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deletePostById(Long postId)
    def delete_post_by_id(self, post_id: int) -> int:
        with session_scope() as session:
            return session.execute(text(_DELETE_POST_BY_ID), {"post_id": post_id}).rowcount or 0

    # Java: int deletePostByIds(Long[] postIds)
    def delete_post_by_ids(self, post_ids: Sequence[int]) -> int:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（Java 同样是语法错）。"""
        clause, params = _in_clause("post_id", post_ids, "p")
        with session_scope() as session:
            return session.execute(text(f"delete from sys_post where {clause}"), params).rowcount or 0

    def _select_one(self, sql: str, params: Mapping[str, Any]) -> Optional[SysPost]:
        with session_scope() as session:
            result = session.execute(text(sql), dict(params))
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_post(rows[0], keys)


def _build_post_list_sql(post: SysPost) -> Tuple[str, Dict[str, Any]]:
    """``selectPostList`` 的 ``<where>``：三个 ``<if>``，用 ``and`` 连接。

    与 ``<where>`` 的差别只有文本：Java 拼出 ``WHERE a AND b``，这里拼 ``where a and b``。

    条件判据严格照抄 MyBatis OGNL 的 ``x != null and x != ''`` —— **不是** ``isBlank``，
    所以 ``postCode = " "``（单个空格）会真的去 ``like '% %'``。
    注意不能换成 :func:`app.common.utils.string_utils.is_not_empty`：那个实现照抄的是
    RuoYi 的 ``StringUtils.isEmpty``，它会先 ``trim``，单个空格会被判成空串而漏掉条件。
    这里与 :func:`app.system.mapper.sys_user_mapper._build_user_list_sql` 的
    ``eq`` / ``contains`` 保持同一判据。
    """
    conditions: List[str] = []
    params: Dict[str, Any] = {}

    def eq(attribute: str, column: str) -> None:
        """``<if test="x != null and x != ''">`` —— 数值字段实际等价于只判 ``None``。"""
        value = getattr(post, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{column} = :{attribute}")
        params[attribute] = value

    def contains(attribute: str, column: str) -> None:
        value = getattr(post, attribute, None)
        if value is None or value == "":
            return
        conditions.append(f"{column} like concat('%', :{attribute}, '%')")
        params[attribute] = value

    # 顺序与 XML 的 <if> 序列一致：postCode -> status -> postName。
    contains("post_code", "post_code")
    eq("status", "status")
    contains("post_name", "post_name")

    sql = SELECT_POST_VO
    if conditions:
        sql = sql + " where " + " and ".join(conditions) + "\n"
    return sql, params


def _build_update_sql(post: SysPost) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_post set ... where post_id = :post_id``（Java: ``<set>``）。

    ``update_time = sysdate()`` 是**无条件**的，所以 ``<set>`` 永不为空 ——
    即使所有 ``<if>`` 都不命中，SQL 依然合法（Java 也一样）。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute, column, require_text in _UPDATE_POST_COLUMNS:
        value = getattr(post, attribute)
        if value is None:
            continue
        if require_text and value == "":
            continue
        sets.append(f"{column} = :{attribute}")
        params[attribute] = value

    sets.append("update_time = sysdate()")
    params["post_id"] = post.post_id

    sql = "update sys_post set " + ", ".join(sets) + " where post_id = :post_id"
    return sql, params


def _map_post(row: Any, keys: Sequence[str]) -> SysPost:
    """One result row -> one ``SysPost`` (Java: ``resultMap="SysPostResult"``).

    只映射投影里出现过的列：``selectPostsByUserName`` 只 select 三列，
    其余字段保持 ``None``（与 ``resultMap`` 拿不到列时一致）。
    """
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields = {name: values[name] for name in _POST_COLUMNS if name in values}
    return SysPost(**fields)


__all__ = ["SysPostMapper", "SELECT_POST_VO"]
