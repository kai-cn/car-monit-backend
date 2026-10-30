"""Parity tests for the JSON wire format of the migrated domain entities.

Every expectation here was produced by running Jackson 2.11.4 (the version Spring Boot
2.5.15 resolves) against a stand-in for the Java classes -- see the docstring of
:mod:`app.common.utils.json_utils` for the measurements. When one of these tests looks
surprising it is because Java is surprising, not because the test is wrong.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.entity import SysDept, SysMenu, SysRole, SysUser
from app.common.core.domain.model import LoginUser
from app.common.utils import json_utils
from app.system.domain.sys_post import SysPost

#: A ``datetime`` column holding ``2025-10-23 13:25:09.123``. The JDBC driver reads it in
#: the server zone (``serverTimezone=GMT+8``), so the instant is ``2025-10-23T05:25:09.123Z``.
DB_WALL_CLOCK = datetime(2025, 10, 23, 13, 25, 9, 123000)
DB_INSTANT_MILLIS = 1761197109123

#: ``@JsonFormat`` renders that instant back in the **JVM zone** (``+08:00``) -- measured
#: against the running ``ruoyi-admin.jar``: a ``create_time`` column holding
#: ``2021-05-06 00:36:40`` is served as ``"2021-05-06 00:36:40"``. ``Jackson2ObjectMapperBuilder``
#: gives the mapper the JVM default zone, so the read side (``serverTimezone=GMT+8``) and
#: the write side cancel out and the stored wall clock survives unchanged.
DB_JSON_CREATE_TIME = "2025-10-23 13:25:09"

#: The string form drops the milliseconds: the pattern is ``yyyy-MM-dd HH:mm:ss`` with no
#: ``SSS``. Parsing a rendered string therefore can never return the original sub-second
#: value -- in Java the same column value comes back as ``13:25:09`` too.
DB_WALL_CLOCK_SECOND = datetime(2025, 10, 23, 13, 25, 9)

#: The instant the Jackson probe actually constructed: ``new Date(1761225909123L)`` is
#: ``2025-10-23T13:25:09Z``, i.e. ``21:25:09`` in ``Asia/Shanghai`` -- and ``21:25:09`` is
#: what Jackson printed. Proof that ``@JsonFormat`` renders in the JVM zone, not in UTC.
PROBE_INSTANT_MILLIS = 1761225909123
PROBE_JSON_CREATE_TIME = "2025-10-23 21:25:09"


class TestJsonUtils:
    def test_format_date_time_keeps_the_wall_clock(self) -> None:
        assert json_utils.format_date_time(DB_WALL_CLOCK) == DB_JSON_CREATE_TIME
        # Round-tripping the probe's instant reproduces Jackson's exact string.
        probe_wall_clock = json_utils.from_epoch_millis(PROBE_INSTANT_MILLIS)
        assert json_utils.format_date_time(probe_wall_clock) == PROBE_JSON_CREATE_TIME
        assert json_utils.format_date_time(None) is None

    def test_to_epoch_millis_uses_the_server_zone(self) -> None:
        # A naive datetime is a wall clock; the instant it denotes is fixed by serverTimezone.
        assert json_utils.to_epoch_millis(DB_WALL_CLOCK) == DB_INSTANT_MILLIS

    def test_epoch_millis_round_trip(self) -> None:
        assert json_utils.from_epoch_millis(DB_INSTANT_MILLIS) == DB_WALL_CLOCK
        assert json_utils.to_epoch_millis(json_utils.from_epoch_millis(DB_INSTANT_MILLIS)) == DB_INSTANT_MILLIS

    def test_epoch_millis_is_exact_for_sub_millisecond_input(self) -> None:
        # Float arithmetic (timestamp() * 1000) truncates to ...998 here; integer math does not.
        value = datetime(2025, 10, 23, 13, 25, 9, 123999)
        assert json_utils.to_epoch_millis(value) == DB_INSTANT_MILLIS

    def test_parse_date_time_accepts_jackson_shapes(self) -> None:
        # Both directions use the Jackson zone (UTC), so the wall clock survives -- but only
        # to the second, because the pattern has no SSS.
        assert json_utils.parse_date_time(DB_JSON_CREATE_TIME) == DB_WALL_CLOCK_SECOND
        # Epoch millis, by contrast, are exact.
        assert json_utils.parse_date_time(DB_INSTANT_MILLIS) == DB_WALL_CLOCK
        # A date-only value is read as midnight in the Jackson zone -- which is the same
        # +08:00 the entity layer uses, so nothing shifts.
        assert json_utils.parse_date_time("2025-10-23") == datetime(2025, 10, 23, 0, 0)
        assert json_utils.parse_date_time(None) is None
        assert json_utils.parse_date_time("") is None

    def test_parse_date_time_normalises_offsets_to_the_server_zone(self) -> None:
        # 05:25:09Z is 13:25:09 in +08:00.
        assert json_utils.parse_date_time("2025-10-23T05:25:09Z") == datetime(2025, 10, 23, 13, 25, 9)

    def test_parse_date_time_rejects_garbage(self) -> None:
        with pytest.raises(ValueError):
            json_utils.parse_date_time("not-a-date")


class TestBaseEntityWireFormat:
    def test_search_value_is_never_serialized(self) -> None:
        entity = BaseEntity(search_value="secret")
        assert "searchValue" not in entity.to_json_dict()

    def test_search_value_cannot_be_injected_from_the_request_body(self) -> None:
        # Java @JsonIgnore blocks deserialization as well; accepting it would let a caller
        # supply its own ${params.dataScope} splice.
        entity = BaseEntity.model_validate({"searchValue": "1=1", "remark": "r"})
        assert entity.search_value is None
        assert entity.remark == "r"

    def test_empty_params_is_omitted(self) -> None:
        # Java @JsonInclude(NON_EMPTY) on BaseEntity.params.
        assert "params" not in BaseEntity().to_json_dict()

    def test_populated_params_is_emitted(self) -> None:
        entity = BaseEntity(params={"beginTime": "2025-01-01"})
        assert entity.to_json_dict()["params"] == {"beginTime": "2025-01-01"}

    def test_create_time_uses_json_format(self) -> None:
        entity = BaseEntity(create_time=DB_WALL_CLOCK, update_time=DB_WALL_CLOCK)
        data = entity.to_json_dict()
        assert data["createTime"] == DB_JSON_CREATE_TIME
        assert data["updateTime"] == DB_JSON_CREATE_TIME

    def test_create_time_accepts_string_and_millis(self) -> None:
        assert BaseEntity(createTime=DB_JSON_CREATE_TIME).create_time == DB_WALL_CLOCK_SECOND
        assert BaseEntity(createTime=DB_INSTANT_MILLIS).create_time == DB_WALL_CLOCK

    def test_null_fields_are_emitted(self) -> None:
        # Jackson's default inclusion is ALWAYS, so nulls are not stripped.
        data = BaseEntity().to_json_dict()
        assert data["remark"] is None
        assert data["createBy"] is None


class TestSysUserWireFormat:
    def test_password_is_write_only(self) -> None:
        user = SysUser.model_validate({"userId": 2, "userName": "ry", "password": "$2a$10$HASH"})
        # Accepted on input (Java @JsonProperty) ...
        assert user.password == "$2a$10$HASH"
        # ... but never leaves the process (Java @JsonIgnore).
        assert "password" not in user.to_json_dict()

    def test_admin_is_a_virtual_property(self) -> None:
        # Java has no "admin" field: `public boolean isAdmin()` makes Jackson emit one.
        assert SysUser(user_id=1, user_name="admin").to_json_dict()["admin"] is True
        assert SysUser(user_id=2, user_name="ry").to_json_dict()["admin"] is False
        assert SysUser().to_json_dict()["admin"] is False

    def test_static_is_admin_mirrors_java(self) -> None:
        assert SysUser.is_admin(1) is True
        assert SysUser.is_admin(2) is False
        assert SysUser.is_admin(None) is False

    def test_login_date_serializes_as_iso_text(self) -> None:
        # ``loginDate`` has no ``@JsonFormat`` in Java, so Spring Boot's mapper writes it
        # with ``StdDateFormat``: ISO-8601, **three** fraction digits and a colon-separated
        # offset. ``createTime`` keeps the ``@JsonFormat`` pattern. Measured on the running
        # jar: ``"2024-05-17T14:15:52.000+08:00"``.
        data = SysUser(user_id=1, login_date=DB_WALL_CLOCK, create_time=DB_WALL_CLOCK).to_json_dict()
        assert data["loginDate"] == "2025-10-23T13:25:09.123+08:00"
        assert isinstance(data["loginDate"], str)
        assert data["createTime"] == DB_JSON_CREATE_TIME
        assert isinstance(data["createTime"], str)

    def test_phonenumber_keeps_java_spelling(self) -> None:
        assert "phonenumber" in SysUser().to_json_dict()
        assert "phoneNumber" not in SysUser().to_json_dict()

    def test_pj_flag_is_primitive_and_defaults_to_zero(self) -> None:
        assert SysUser().to_json_dict()["pjFlag"] == 0

    def test_unknown_properties_are_ignored(self) -> None:
        # Spring Boot disables FAIL_ON_UNKNOWN_PROPERTIES; Java answers 200, it never 400s.
        user = SysUser.model_validate({"userName": "ry", "somethingNew": 1})
        assert user.user_name == "ry"

    def test_nested_dept_and_roles_use_camel_case(self) -> None:
        user = SysUser(
            user_id=2,
            dept=SysDept(dept_id=100, dept_name="研发部门"),
            roles=[SysRole(role_id=2, role_name="普通角色")],
        )
        data = user.to_json_dict()
        assert data["dept"]["deptId"] == 100
        assert data["dept"]["deptName"] == "研发部门"
        assert data["roles"][0]["roleName"] == "普通角色"


class TestSysRoleWireFormat:
    def test_primitive_booleans_are_always_present(self) -> None:
        data = SysRole(role_id=2).to_json_dict()
        assert data["flag"] is False
        assert data["menuCheckStrictly"] is False
        assert data["deptCheckStrictly"] is False


class TestSysDeptWireFormat:
    def test_children_defaults_to_empty_list_not_null(self) -> None:
        # Java initialises `children = new ArrayList<>()`, so a leaf node emits [].
        assert SysDept(dept_id=100).to_json_dict()["children"] == []

    def test_quirky_column_names_survive(self) -> None:
        data = SysDept(tree_leavel=2, order_num="1", is_zbzg="1").to_json_dict()
        assert data["treeLeavel"] == 2  # Java's spelling, not "treeLevel"
        assert data["orderNum"] == "1"  # a varchar, not an int
        assert data["isZbzg"] == "1"


class TestJacksonScalarCoercion:
    """varchar 列在 Java 里是 ``String``，Jackson 默认把数字/布尔强转成字符串。

    前端用 ``el-input-number`` 绑定的排序列发的是 JSON 数字；假如 Python 这边
    拒绝 ``int -> str``，同一个请求会从 200 变成 ``code 500``。
    """

    def test_a_number_is_accepted_for_a_string_column(self) -> None:
        assert SysDept(order_num=1).order_num == "1"
        assert SysRole(role_sort=2).role_sort == "2"
        assert SysPost(post_sort=3).post_sort == "3"
        assert SysMenu(order_num=4).order_num == "4"

    def test_a_boolean_becomes_java_lowercase(self) -> None:
        # Java: String.valueOf(true) 与 Jackson 都是小写
        assert SysDept(order_num=True).order_num == "true"

    def test_none_and_strings_pass_through(self) -> None:
        assert SysDept(order_num=None).order_num is None
        assert SysDept(order_num="7").order_num == "7"

    def test_a_number_arriving_in_camel_case_is_accepted(self) -> None:
        # 前端只会发 JSON（camelCase）
        assert SysPost.model_validate({"postSort": 9}).post_sort == "9"


class TestLoginUserWireFormat:
    def test_permissions_round_trip(self) -> None:
        login_user = LoginUser(
            token="uuid-1",
            login_time=DB_INSTANT_MILLIS,
            expire_time=DB_INSTANT_MILLIS + 7_200_000,
            permissions={"system:user:list", "*:*:*"},
            user=SysUser(user_id=1, user_name="admin"),
        )
        payload = login_user.model_dump_json()
        restored = LoginUser.model_validate_json(payload)
        assert restored.token == "uuid-1"
        assert restored.login_time == DB_INSTANT_MILLIS
        assert restored.permissions == {"system:user:list", "*:*:*"}
        assert restored.user is not None and restored.user.user_name == "admin"

    def test_username_is_derived_from_the_nested_user(self) -> None:
        login_user = LoginUser(user=SysUser(user_name="admin"))
        assert login_user.username == "admin"
        assert login_user.get_username() == "admin"
        assert LoginUser().username is None

    def test_timestamps_stay_integers(self) -> None:
        # Java declares them as Long millis, not Date, so no formatting may happen.
        data = LoginUser(login_time=DB_INSTANT_MILLIS, expire_time=DB_INSTANT_MILLIS).to_json_dict()
        assert data["loginTime"] == DB_INSTANT_MILLIS
        assert data["expireTime"] == DB_INSTANT_MILLIS

    def test_permissions_serialize_as_a_list(self) -> None:
        data = LoginUser(permissions={"b", "a"}).to_json_dict()
        assert data["permissions"] == ["a", "b"]

    def test_user_id_helpers(self) -> None:
        login_user = LoginUser(user=SysUser(user_id=1, dept_id=103))
        assert login_user.get_user_id() == 1
        assert login_user.get_dept_id() == 103
        assert login_user.is_admin() is True
        assert LoginUser().get_user_id() is None
        assert LoginUser().is_admin() is False
