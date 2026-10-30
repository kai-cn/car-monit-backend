"""``SysNoticeService`` -- 服务层对实体的**覆盖**行为.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysNoticeServiceImpl.java

这一层真正值得测的只有三处覆盖
------------------------------
``insertNotice`` / ``updateNotice`` / ``addDeliveryTimeAbnormal`` 都会**改写**
调用方刚填好的字段。它们看起来像笔误，但都是 Java 原样：

* ``insertNotice`` 把控制器写的 ``createBy = userName`` 换成 ``userId`` 的字符串 ——
  所以 ``sys_notice.create_by`` 里存的是 ``"7"`` 而不是 ``"admin"``；
* 同一个方法把 ``noticeType`` **强制**成 ``"1"``，前端传 ``"2"``（公告）也会变通知；
* ``updateNotice`` 同样把 ``updateBy`` 换成 ``userId``；
* ``addDeliveryTimeAbnormal`` 在"已存在"分支里**丢弃**入参上的全部改动。

这些如果被"顺手修正"，接口不会报错，只是库里少了一列、或者多出一条重复公告。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

import pytest

from app.system.domain.sys_notice import SysNotice
from app.system.service import sys_notice_service as service_module
from app.system.service.sys_notice_service import (
    SysNoticeService,
    get_notice_service,
    reset_notice_service,
)

# --------------------------------------------------------------------------- fakes


class _FakeMapper:
    """Records every call; ``select_notice_list`` also captures the query entity."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysNotice] = []
        self.by_id_result: Optional[SysNotice] = None
        self.insert_result = 1
        self.update_result = 1
        self.delete_result = 1
        self.lastrowid = 42

    def select_notice_list(self, notice: SysNotice) -> List[SysNotice]:
        self.calls.append(("select_notice_list", notice.model_copy(deep=True)))
        return self.list_result

    def select_notice_by_id(self, notice_id: int) -> Optional[SysNotice]:
        self.calls.append(("select_notice_by_id", notice_id))
        return self.by_id_result

    def insert_notice(self, notice: SysNotice) -> int:
        self.calls.append(("insert_notice", notice.model_copy(deep=True)))
        notice.notice_id = self.lastrowid
        return self.insert_result

    def update_notice(self, notice: SysNotice) -> int:
        self.calls.append(("update_notice", notice.model_copy(deep=True)))
        return self.update_result

    def delete_notice_by_id(self, notice_id: int) -> int:
        self.calls.append(("delete_notice_by_id", notice_id))
        return self.delete_result

    def delete_notice_by_ids(self, notice_ids: Sequence[int]) -> int:
        self.calls.append(("delete_notice_by_ids", list(notice_ids)))
        return self.delete_result

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def security(monkeypatch: pytest.MonkeyPatch) -> Any:
    """固定登录态：``userId = 7``、``userName = "admin"``、``tenantId = 3``。"""
    monkeypatch.setattr(service_module.SecurityUtils, "get_user_id", lambda: 7)
    monkeypatch.setattr(service_module.SecurityUtils, "get_tenant_id", lambda: 3)
    monkeypatch.setattr(service_module.SecurityUtils, "get_username", lambda: "admin")
    reset_notice_service()
    yield
    reset_notice_service()


@pytest.fixture
def mapper() -> _FakeMapper:
    return _FakeMapper()


@pytest.fixture
def service(mapper: _FakeMapper) -> SysNoticeService:
    return SysNoticeService(mapper=mapper)


# --------------------------------------------------------------------------- 只读转发


class TestReadOnlyPassThrough:
    def test_select_notice_list_forwards_the_entity(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        mapper.list_result = [SysNotice(notice_id=1)]

        rows = service.select_notice_list(SysNotice(status="0"))

        assert [row.notice_id for row in rows] == [1]
        assert mapper.of("select_notice_list")[0][1].status == "0"

    def test_select_notice_by_id_returns_none_when_absent(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        assert service.select_notice_by_id(404) is None
        assert mapper.of("select_notice_by_id") == [("select_notice_by_id", 404)]


# --------------------------------------------------------------------------- insertNotice


class TestInsertNotice:
    def test_notice_type_is_forced_to_one(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        """前端传 ``"2"``（公告）也会被写成 ``"1"``（通知）。"""
        notice = SysNotice(notice_title="标题", notice_type="2")

        service.insert_notice(notice)

        assert notice.notice_type == "1"
        assert mapper.of("insert_notice")[0][1].notice_type == "1"

    def test_create_by_is_overwritten_with_the_user_id(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        """控制器写的 ``userName`` 在这里被换成 ``userId`` —— 与其它模块不一致。"""
        notice = SysNotice(notice_title="标题", create_by="admin")

        service.insert_notice(notice)

        assert notice.create_by == "7"
        assert mapper.of("insert_notice")[0][1].create_by == "7"

    def test_the_current_tenant_is_stamped(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        notice = SysNotice(notice_title="标题", tenant_id=999)

        service.insert_notice(notice)

        assert notice.tenant_id == 3

    def test_the_mapper_result_is_returned(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        mapper.insert_result = 1

        assert service.insert_notice(SysNotice(notice_title="标题")) == 1


# --------------------------------------------------------------------------- updateNotice


class TestUpdateNotice:
    def test_update_by_is_overwritten_with_the_user_id(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        notice = SysNotice(notice_id=1, notice_title="标题", update_by="admin")

        service.update_notice(notice)

        assert notice.update_by == "7"

    def test_the_rich_text_hook_is_gone(self, service: SysNoticeService) -> None:
        """Java 里"处理富文本图片"那一段被注释掉了 —— 内容原样下传。"""
        notice = SysNotice(notice_id=1, notice_content='<img src="data:image/png;base64,AAA">')

        service.update_notice(notice)

        assert notice.notice_content == '<img src="data:image/png;base64,AAA">'

    def test_the_mapper_result_is_returned(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        mapper.update_result = 0

        assert service.update_notice(SysNotice(notice_id=1)) == 0


# --------------------------------------------------------------------------- 删除


class TestDelete:
    def test_delete_notice_by_id(self, service: SysNoticeService, mapper: _FakeMapper) -> None:
        """Java 侧没有调用方，但方法本身照搬。"""
        mapper.delete_result = 1

        assert service.delete_notice_by_id(4) == 1

    def test_delete_notice_by_ids_forwards_the_list(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        mapper.delete_result = 2

        assert service.delete_notice_by_ids([1, 2]) == 2
        assert mapper.of("delete_notice_by_ids") == [("delete_notice_by_ids", [1, 2])]


# --------------------------------------------------------------------------- addDeliveryTimeAbnormal


class TestAddDeliveryTimeAbnormal:
    def test_it_inserts_when_nothing_matches(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        mapper.list_result = []
        mapper.lastrowid = 77
        notice = SysNotice(notice_title="到货异常", buss_id="9", create_by="admin")

        notice_id = service.add_delivery_time_abnormal(notice)

        assert notice_id == 77
        inserted = mapper.of("insert_notice")[0][1]
        assert inserted.create_by == "7"
        assert inserted.tenant_id == 3
        assert inserted.notice_type == "1"
        assert inserted.status == "0"

    def test_it_returns_the_existing_id_without_inserting(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        mapper.list_result = [SysNotice(notice_id=55, buss_id="9")]

        notice_id = service.add_delivery_time_abnormal(SysNotice(notice_title="到货异常", buss_id="9"))

        assert notice_id == 55
        assert mapper.of("insert_notice") == []

    def test_the_input_entity_is_left_untouched_when_a_match_exists(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        """Java 是 ``notice = sysNoticeList.get(0)``（改局部变量），入参不被改写。"""
        mapper.list_result = [SysNotice(notice_id=55)]
        notice = SysNotice(notice_title="到货异常", status=None, create_by=None)

        service.add_delivery_time_abnormal(notice)

        assert notice.status is None
        assert notice.create_by is None

    def test_the_list_query_receives_the_raw_entity(
        self, service: SysNoticeService, mapper: _FakeMapper
    ) -> None:
        """去重判断完全依赖入参当条件 —— 调用方传什么就查什么。"""
        mapper.list_result = [SysNotice(notice_id=1)]

        service.add_delivery_time_abnormal(SysNotice(buss_id="9", notice_content="异常"))

        query = mapper.of("select_notice_list")[0][1]
        assert query.buss_id == "9"
        assert query.notice_content == "异常"


# --------------------------------------------------------------------------- 单例


class TestSingleton:
    def test_get_notice_service_returns_a_process_wide_instance(self) -> None:
        reset_notice_service()

        first = get_notice_service()
        second = get_notice_service()

        assert first is second

    def test_reset_drops_the_cached_instance(self) -> None:
        reset_notice_service()
        first = get_notice_service()

        reset_notice_service()

        assert get_notice_service() is not first
