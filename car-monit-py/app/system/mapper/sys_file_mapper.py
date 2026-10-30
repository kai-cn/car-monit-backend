"""文件管理 mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/mapper/SysFileMapper.java
# Migrated from: ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml

XML 里共 9 条 statement，本模块**全部迁移**。

``selectSysFileList`` 的 ``where`` 是硬编码的
--------------------------------------------
``where t.del_flag = '0'`` 写死在 XML 里，后面 11 个 ``<if>`` 各自带 ``and``，**没有**
``<where>`` 标签 —— 所以条件片段不带前导 ``AND``，统一用 ``and`` 连接（与
:mod:`app.system.mapper.sys_upgrade_info_mapper` 同一形态）。

11 个条件的判据分两类：

=============================================================  ==================
字段                                                            判据
=============================================================  ==================
``id`` / ``fileName`` / ``bucketName`` / ``original`` /          ``!= null and != ''``
``type`` / ``bussType`` / ``bussName`` / ``createUser`` /
``updateUser``
``fileSize`` / ``tenantId``                                      ``!= null``
=============================================================  ==================

``id`` 是 ``Long``，``!= ''`` 这一半在 Java 的 OGNL 里对数字等价于"恒真"，所以**实际**
只有"非 null"这一个判据（Python 侧 ``value == ""`` 对 ``int`` 永远不成立，自然一致）。
``fileName`` / ``bucketName`` / ``bussName`` 用 ``like concat('%', ?, '%')``，其余用 ``=``。

11 个条件的**顺序与 XML 完全一致**（``id`` → ``fileName`` → ``bucketName`` → ``original``
→ ``type`` → ``fileSize`` → ``bussType`` → ``bussName`` → ``createUser`` → ``updateUser``
→ ``tenantId``），所以拼出的 SQL 与 MyBatis 逐字相同 —— 见 :data:`_LIST_CONDITIONS`。

``order by t.create_time desc,t.id`` 是**自带**的 —— 不会追加客户端排序列，前端点表头
排序对这张表不生效。

``selectSysFileByIds`` 多带一个 ``createUserName``
--------------------------------------------------
只有这一条 select 会 ``left join sys_user t2 on t.create_user = t2.user_id and
t2.del_flag='0'``，把 ``t2.nick_name`` 别名为 ``createUserName``。于是：

* 按逗号串批量查能拿到"创建人姓名"，按 id 查 / 列表查拿不到（``null``）；
* 因为 ``create_user`` 是 **String** 而 ``sys_user.user_id`` 是 **bigint**，MySQL 会做
  隐式类型转换 —— 非数字的 ``create_user`` 会被转成 0 而不是报错（原样照抄）。

``insertSysFile`` 的 ``useGeneratedKeys``
-----------------------------------------
XML 写了 ``useGeneratedKeys="true" keyProperty="id"``，MyBatis 会把自增主键回写进
``sysFile.id``。但 service 在插入前已经赋了 snowflake id，所以**实际永不触发**；
Python 侧仍然实现回写（只在 ``entity.id is None`` 时），保持与 XML 同形。

``deleteSysFileByIdNew`` 是**唯一**的物理删除
---------------------------------------------
``delete from sys_file where id = #{id}`` —— 调用点有两个：``fileLogId``（"先删后增"，
把已有 id 的记录物理删掉再插一条新的）与 ``updateCAFile``（先删 3001 再把它改成 3001）。

``updateCAFile`` 把主键写死成 3001
----------------------------------
``update sys_file set id = 3001 where id = #{id}`` —— 注意 ``#{id}`` 是**参数对象**里的
``id``，不是方法声明里的类型（Mapper 接口写的是 ``updateCAFile(SysFile sysFile)``，
XML 的 ``parameterType`` 却写成 ``Long``，属于既有不一致，不影响运行）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import text

from app.common.core.page.page_helper import PageList, select_page, take_page
from app.config.database import session_scope
from app.system.domain.sys_file import SysFile
from app.system.mapper.sys_user_role_mapper import _in_clause

#: Verbatim from SysFileMapper.xml -> ``<sql id="selectSysFileVo">``（14 列）。
SELECT_SYS_FILE_VO = (
    "t.id, t.file_name, t.bucket_name, t.original, t.type, t.file_size, t.buss_type, "
    "t.buss_name, t.create_user, t.create_time, t.update_user, t.update_time, "
    "t.del_flag, t.tenant_id"
)

#: ``insertSysFile`` 的 ``<trim>`` 分支，顺序与 XML 一致；14 列全是 ``!= null``。
_INSERT_COLUMNS: Tuple[str, ...] = (
    "id",
    "file_name",
    "bucket_name",
    "original",
    "type",
    "file_size",
    "buss_type",
    "buss_name",
    "create_user",
    "create_time",
    "update_user",
    "update_time",
    "del_flag",
    "tenant_id",
)

#: ``updateSysFile`` 的 ``<trim prefix="SET">`` 分支；**没有** ``id``（在 ``where`` 里）。
_UPDATE_COLUMNS: Tuple[str, ...] = (
    "file_name",
    "bucket_name",
    "original",
    "type",
    "file_size",
    "buss_type",
    "buss_name",
    "create_user",
    "create_time",
    "update_user",
    "update_time",
    "del_flag",
    "tenant_id",
)

#: ``resultMap="SysFileResult"`` 的列 -> 属性（14 个），外加 join 出来的 ``createUserName``。
_COLUMN_TO_FIELD: Dict[str, str] = {
    "id": "id",
    "file_name": "file_name",
    "bucket_name": "bucket_name",
    "original": "original",
    "type": "type",
    "file_size": "file_size",
    "buss_type": "buss_type",
    "buss_name": "buss_name",
    "create_user": "create_user",
    "create_time": "create_time",
    "update_user": "update_user",
    "update_time": "update_time",
    "del_flag": "del_flag",
    "tenant_id": "tenant_id",
    # selectSysFileByIds: ``t2.nick_name createUserName``
    "createusername": "create_user_name",
}

#: ``selectSysFileList`` 的 11 个 ``<if>``，**顺序与 XML 完全一致**。
#:
#: ``(属性, 列, 运算符, 空串是否跳过)`` —— 最后一位对应 XML 判据里的 ``and x != ''``：
#: ``file_size`` / ``tenant_id`` 只判 ``!= null``。
_LIST_CONDITIONS: Tuple[Tuple[str, str, str, bool], ...] = (
    ("id", "t.id", "=", True),
    ("file_name", "t.file_name", "like", True),
    ("bucket_name", "t.bucket_name", "like", True),
    ("original", "t.original", "=", True),
    ("type", "t.type", "=", True),
    ("file_size", "t.file_size", "=", False),
    ("buss_type", "t.buss_type", "=", True),
    ("buss_name", "t.buss_name", "like", True),
    ("create_user", "t.create_user", "=", True),
    ("update_user", "t.update_user", "=", True),
    ("tenant_id", "t.tenant_id", "=", False),
)

#: ``selectSysFileList`` 的投影列（顺序即 ``selectSysFileVo`` 的列顺序）。
_LIST_COLUMNS: Tuple[str, ...] = _INSERT_COLUMNS

#: ``selectSysFileByIds`` 的投影列 = 14 列 + ``createUserName``。
_BY_IDS_COLUMNS: Tuple[str, ...] = _LIST_COLUMNS + ("createUserName",)


class SysFileMapper:
    """Java: ``interface SysFileMapper``."""

    # Java: List<SysFile> selectSysFileByIds(String[] ids)
    def select_sys_file_by_ids(self, ids: Sequence[Any]) -> List[SysFile]:
        """``<foreach collection="array">`` —— 空数组会拼出 ``in ()``（SQL 语法错误）。"""
        clause, params = _in_clause("t.id", ids, "p")
        sql = (
            f"select {SELECT_SYS_FILE_VO},\nt2.nick_name createUserName\n"
            "from sys_file t\n"
            "left join sys_user t2 on t.create_user = t2.user_id and t2.del_flag='0'\n"
            f"where {clause}\n"
            "order by t.id"
        )
        with session_scope() as session:
            result = session.execute(text(sql), params)
            keys = list(result.keys())
            rows = result.all()
        return [_map_file(row, keys) for row in rows]

    # Java: SysFile selectSysFileById(Long id)
    def select_sys_file_by_id(self, id: Any) -> Optional[SysFile]:
        """**没有** ``del_flag`` 过滤 —— 软删除的行也能查到。"""
        sql = f"select {SELECT_SYS_FILE_VO}\nfrom sys_file t\nwhere t.id = :id"
        with session_scope() as session:
            result = session.execute(text(sql), {"id": id})
            keys = list(result.keys())
            rows = result.all()
        if not rows:
            return None
        return _map_file(rows[0], keys)

    # Java: List<SysFile> selectSysFileList(SysFile sysFile)
    def select_sys_file_list(self, entity: SysFile) -> List[SysFile]:
        """控制器在调用前已 ``startPage()``，分页点在这条 select 上。"""
        data_sql, params = _build_file_list_sql(entity)
        count_sql = f"select count(0) from ({data_sql}) table_count"
        page = take_page()
        with session_scope() as session:
            page_list: PageList = select_page(session, count_sql, data_sql, params, page)
        mapped = [_map_file(row, list(_LIST_COLUMNS)) for row in page_list]
        return PageList(
            mapped,
            total=page_list.total,
            page_num=page_list.page_num,
            page_size=page_list.page_size,
        )

    # Java: int insertSysFile(SysFile sysFile)
    def insert_sys_file(self, entity: SysFile) -> int:
        """动态列插入；``useGeneratedKeys`` 的回写只在 ``entity.id is None`` 时生效。"""
        columns: List[str] = []
        names: List[str] = []
        params: Dict[str, Any] = {}

        for attribute in _INSERT_COLUMNS:
            value = getattr(entity, attribute)
            if value is None:
                continue
            columns.append(attribute)
            names.append(f":{attribute}")
            params[attribute] = value

        sql = f"insert into sys_file ({','.join(columns)}) values ({','.join(names)})"
        with session_scope() as session:
            result = session.execute(text(sql), params)
            # Java: useGeneratedKeys="true" keyProperty="id"
            if entity.id is None and getattr(result, "lastrowid", None):
                entity.id = int(result.lastrowid)
            return result.rowcount or 0

    # Java: int updateSysFile(SysFile sysFile)
    def update_sys_file(self, entity: SysFile) -> int:
        sql, params = _build_update_sql(entity)
        with session_scope() as session:
            return session.execute(text(sql), params).rowcount or 0

    # Java: int deleteSysFileById(Long id)
    def delete_sys_file_by_id(self, id: Any) -> int:
        """软删除。"""
        with session_scope() as session:
            result = session.execute(
                text("update sys_file set del_flag = '1' where id = :id"), {"id": id}
            )
            return result.rowcount or 0

    # Java: int deleteSysFileByIds(Long[] ids)
    def delete_sys_file_by_ids(self, ids: Sequence[Any]) -> int:
        """软删除。``<foreach collection="array">`` —— 空数组会拼出 ``in ()``。"""
        clause, params = _in_clause("id", ids, "p")
        with session_scope() as session:
            result = session.execute(
                text(f"update sys_file set del_flag = '1' where {clause}"), params
            )
            return result.rowcount or 0

    # Java: int deleteSysFileByIdNew(Long id)
    def delete_sys_file_by_id_new(self, id: Any) -> int:
        """**物理删除**（``delete from``）—— 本模块唯一的硬删除。"""
        with session_scope() as session:
            result = session.execute(text("delete from  sys_file  where id = :id"), {"id": id})
            return result.rowcount or 0

    # Java: int updateCAFile(SysFile sysFile)
    def update_ca_file(self, entity: SysFile) -> int:
        """把主键改成写死的 3001（XML: ``set id = 3001 where id = #{id}``）。"""
        with session_scope() as session:
            result = session.execute(
                text("update sys_file set id = 3001 where id = :id"),
                {"id": entity.id},
            )
            return result.rowcount or 0


def _build_file_list_sql(entity: SysFile) -> Tuple[str, Dict[str, Any]]:
    """``selectSysFileList`` 的 ``where``；**自带** ``order by``（照抄）。"""
    conditions: List[str] = ["t.del_flag = '0'"]
    params: Dict[str, Any] = {}

    for attribute, column, operator, skip_empty in _LIST_CONDITIONS:
        value = getattr(entity, attribute)
        if value is None or (skip_empty and value == ""):
            continue
        if operator == "like":
            # Java: like concat('%', #{x}, '%')
            conditions.append(f"{column} like concat('%', :{attribute}, '%')")
        else:
            conditions.append(f"{column} = :{attribute}")
        params[attribute] = value

    sql = (
        f"select {SELECT_SYS_FILE_VO}\n"
        "from sys_file t\n"
        "where " + "\nand ".join(conditions) + "\n"
        "order by t.create_time desc,t.id"
    )
    return sql, params


def _build_update_sql(entity: SysFile) -> Tuple[str, Dict[str, Any]]:
    """拼 ``update sys_file set ... where id = :id``（Java: ``<trim prefix="SET">``）。

    13 个 set 全是 ``!= null``（**没有** ``!= ''`` 的特例），所以传空串会**清列**。
    """
    sets: List[str] = []
    params: Dict[str, Any] = {}
    for attribute in _UPDATE_COLUMNS:
        value = getattr(entity, attribute)
        if value is None:
            continue
        sets.append(f"{attribute} = :{attribute}")
        params[attribute] = value

    params["id"] = entity.id
    sql = "update sys_file set " + ",".join(sets) + " where id = :id"
    return sql, params


def _map_file(row: Any, keys: Sequence[str]) -> SysFile:
    """One result row -> one ``SysFile`` (Java: ``resultMap="SysFileResult"``)."""
    values: Mapping[str, Any] = {label: row[keys.index(label)] for label in keys}
    fields: Dict[str, Any] = {}
    for label, value in values.items():
        attribute = _COLUMN_TO_FIELD.get(str(label).lower())
        if attribute is not None:
            fields[attribute] = value
    return SysFile(**fields)


__all__ = ["SysFileMapper", "SELECT_SYS_FILE_VO"]
