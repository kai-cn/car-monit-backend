"""大屏接口 控制器 单元测试.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenController.java

覆盖的重点（Mapper / Service 由各自文件覆盖）：

* 12 条路由全是 ``GET``，路径前缀 ``/manager/bigScreen``（**驼峰**），
  并且**一个权限点都没有** —— 空权限集 + 已登录也应 200；
* ``getSectionList`` 把 ``{"sectionCode": "all", "sectionName": "全部"}`` 手工插在首位；
* ``getTollList`` 的 ``type`` 是必填（缺失 → ``code 500`` + Spring 原文案），
  ``sectionCode`` 空白直接回**空数组**（不是全量），非空时先 ``deleteEnd`` 削
  **一个**尾逗号再切分，切分后整串含 ``"all"`` 则把列表清空；
* ``getCarLocation`` / ``getCarWarning`` 共用同一段入参规整：``sectionCode`` 含
  ``"all"`` 子串就清空，``type`` 非空时把 ``code`` 塞进对应编码字段，``code`` 空
  则塞 ``StationCapture`` / ``GantryCapture`` / ``ServiceAreaCapture``（魔法值）；
* ``getCarAudit`` 两个来源各自可能回 ``null``，为 ``null`` 时保留 VO 的**零初值**；
* ``getOrgList`` 只投影 ``orgCode`` / ``orgName`` 两列；
* ``incomeStatistic`` 的 ``queryDateType`` 空值默认盖成 ``"suo"``；
* ``list``（``/exceptRecordList``）逐行补 ``orgId`` 与 ``supplementaryStatus``。
"""

from __future__ import annotations

import importlib
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.base.domain.dwd_lczt_fwqjcxx import DwdLcztFwqjcxx
from app.base.domain.ods_szdn_gantry import OdsSzdnGantry
from app.base.domain.ods_szdn_section import OdsSzdnSection
from app.base.domain.ods_szdn_toll import OdsSzdnToll
from app.base.domain.ods_yhgl_v_base_org import OdsYhglVBaseOrg
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page
from app.config.exception_handlers import register_exception_handlers
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.manager.domain.car_except_record import CarExceptRecord
from app.manager.domain.vo.bigscreen.car_info_vo import CarInfoVO
from app.manager.domain.vo.bigscreen.car_statistics_vo import CarStatisticsVO
from app.manager.domain.vo.bigscreen.income_statistic_param import IncomeStatisticParam
from app.manager.domain.vo.bigscreen.top_ten_vo import TopTenVO

MODULE_NAME = "app.api.manager.bigscreen.big_screen_controller"

PREFIX = "/manager/bigScreen"

#: 逐条抄自 ``BigScreenController`` 的映射表 —— 12 条，全部 ``GET``。
ROUTE_TABLE: Set[Tuple[str, Tuple[str, ...]]] = {
    (f"{PREFIX}/carStatistics", ("GET",)),
    (f"{PREFIX}/carLocation", ("GET",)),
    (f"{PREFIX}/sectionList", ("GET",)),
    (f"{PREFIX}/tollGantryFwqList", ("GET",)),
    (f"{PREFIX}/carVoList", ("GET",)),
    (f"{PREFIX}/carAudit", ("GET",)),
    (f"{PREFIX}/carWarning", ("GET",)),
    (f"{PREFIX}/exceptionCar", ("GET",)),
    (f"{PREFIX}/topTen", ("GET",)),
    (f"{PREFIX}/orgList", ("GET",)),
    (f"{PREFIX}/incomeStatistic", ("GET",)),
    (f"{PREFIX}/exceptRecordList", ("GET",)),
}

#: 控制器里 12 个惰性协作访问器 —— 注入替身时逐个替换。
ACCESSORS = (
    "_car_info",
    "_car_confim_free",
    "_car_aduit_free",
    "_section",
    "_toll",
    "_gantry",
    "_fwqjcxx",
    "_car_warning_info",
    "_snapshot_flow",
    "_car_suspicious",
    "_base_org",
    "_car_except_record",
)

#: 各方法的默认返回值 —— 列表方法不能回 ``None``（控制器里有推导式）。
_DEFAULTS: Dict[str, Any] = {
    "select_list_new": [],
    "select_car_vo_list": [],
    "select_car_warning_info_list_limit100": [],
    "select_list_limit10": [],
    "get_top_ten": [],
    "select_org_list": [],
    "select_list": [],
    "get_car_statistics": [],
    "income_statistic": [],
    "car_location": [],
    "select_org_id": None,
    "count_by_car_id": 0,
    "get_car_audit": None,
    "get_car_confirm": None,
}


def _module() -> Any:
    return importlib.import_module(MODULE_NAME)


def _build_app(router: Any, permissions: Optional[Set[str]] = None) -> FastAPI:
    """带假 JWT 的应用：中间件直接把登录用户塞进 ``SecurityContextHolder``."""
    application = FastAPI()
    register_exception_handlers(application)

    @application.middleware("http")
    async def _fake_jwt(request: Any, call_next: Any) -> Any:
        SecurityContextHolder.get_context().set_authentication(
            UsernamePasswordAuthenticationToken(
                LoginUser(
                    user=SysUser(user_id=2, user_name="ry"),
                    permissions={"*:*:*"} if permissions is None else permissions,
                ),
                None,
                [],
            )
        )
        return await call_next(request)

    application.include_router(router)
    return application


@pytest.fixture(autouse=True)
def _clean_context() -> Any:
    SecurityContextHolder.clear_context()
    clear_page()
    yield
    _module().reset_big_screen_controller()
    SecurityContextHolder.clear_context()
    clear_page()


class _FakeService:
    """记录调用参数的替身 —— 任意方法名都可用，返回值按 ``_DEFAULTS`` 兜底."""

    def __init__(self, **results: Any) -> None:
        self.results: Dict[str, Any] = dict(_DEFAULTS)
        self.results.update(results)
        self.calls: List[Tuple[str, Tuple[Any, ...]]] = []

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)

        def _call(*args: Any, **_kwargs: Any) -> Any:
            self.calls.append((name, args))
            return self.results.get(name, _DEFAULTS.get(name))

        return _call

    def called(self, name: str) -> List[Tuple[Any, ...]]:
        return [args for called_name, args in self.calls if called_name == name]


def _inject(monkeypatch: Any, **overrides: Any) -> Dict[str, _FakeService]:
    """``_inject(monkeypatch, toll=fake)`` -> 把 ``fake`` 挂到 ``_toll()`` 上.

    未点名的访问器共用一个空替身（键 ``"*"``），这样测试可以顺带断言"没被碰到".
    """
    module = _module()
    module.reset_big_screen_controller()
    fallback = _FakeService()
    fakes: Dict[str, _FakeService] = {"*": fallback}
    for name in ACCESSORS:
        key = name[1:]
        fake = overrides.get(key, fallback)
        fakes[key] = fake
        monkeypatch.setattr(module, name, lambda _fake=fake: _fake)
    return fakes


def _client(fakes: Dict[str, _FakeService], permissions: Optional[Set[str]] = None) -> TestClient:
    return TestClient(_build_app(_module().router, permissions))


# --------------------------------------------------------------------------- 路由表


def test_the_route_table_matches_the_java_mappings() -> None:
    router = _module().router

    registered = {(route.path, tuple(sorted(route.methods))) for route in router.routes}

    assert registered == ROUTE_TABLE


def test_every_endpoint_is_a_plain_get() -> None:
    """``@GetMapping`` 12 个 —— 没有 POST / PUT / DELETE，也没有路径变量."""
    router = _module().router

    assert all(route.methods == {"GET"} for route in router.routes)
    assert all("{" not in route.path for route in router.routes)


def test_no_endpoint_declares_a_permission_point(monkeypatch: Any) -> None:
    """Java 类上没有任何 ``@PreAuthorize`` —— 空权限集 + 已登录也应全部 200."""
    fakes = _inject(monkeypatch)
    client = _client(fakes, permissions=set())

    for path, _methods in sorted(ROUTE_TABLE):
        params = {"type": "1", "sectionCode": "SD01"} if path.endswith("tollGantryFwqList") else {}
        assert client.get(path, params=params).json()["code"] == 200, path


# --------------------------------------------------------------------------- 路段


def test_section_list_prepends_the_all_option(monkeypatch: Any) -> None:
    section = _FakeService(
        select_list_new=[OdsSzdnSection(section_code="SD01", section_name="沪宁段")]
    )
    body = _client(_inject(monkeypatch, section=section)).get(f"{PREFIX}/sectionList").json()

    assert body["data"] == [
        {"sectionCode": "all", "sectionName": "全部"},
        {"sectionCode": "SD01", "sectionName": "沪宁段"},
    ]
    # 查的是"空条件"，即全量（不是 null）
    assert isinstance(section.calls[-1][1][0], OdsSzdnSection)


# --------------------------------------------------------------------------- 收费站 / 门架 / 服务区


def test_toll_list_requires_the_type_parameter(monkeypatch: Any) -> None:
    """Java: ``@RequestParam String type`` 必填 -> ``code 500`` + Spring 原文案."""
    fakes = _inject(monkeypatch)

    body = _client(fakes).get(f"{PREFIX}/tollGantryFwqList", params={"sectionCode": "SD01"}).json()

    assert body["code"] == 500
    assert body["msg"] == _module().MISSING_TYPE_MESSAGE


def test_toll_list_returns_an_empty_array_for_a_blank_section(monkeypatch: Any) -> None:
    """``sectionCode`` 空白 -> 空数组（不是全量），并且**不查库**."""
    toll = _FakeService(select_list_new=[OdsSzdnToll(toll_code="T1", toll_name="站一")])
    fakes = _inject(monkeypatch, toll=toll)
    client = _client(fakes)

    assert client.get(f"{PREFIX}/tollGantryFwqList", params={"type": "1"}).json()["data"] == []
    assert (
        client.get(f"{PREFIX}/tollGantryFwqList", params={"type": "1", "sectionCode": " "}).json()[
            "data"
        ]
        == []
    )
    assert toll.calls == []


def test_toll_list_drops_one_trailing_comma_then_splits(monkeypatch: Any) -> None:
    toll = _FakeService()

    _client(_inject(monkeypatch, toll=toll)).get(
        f"{PREFIX}/tollGantryFwqList", params={"type": "1", "sectionCode": "SD01,SD02,"}
    )

    assert toll.calls[-1][1][0].section_code_list == ["SD01", "SD02"]


def test_toll_list_only_strips_a_single_trailing_comma(monkeypatch: Any) -> None:
    """``deleteEnd`` 只削**一个**尾逗号，剩下的空段由 ``split`` 自己丢掉."""
    toll = _FakeService()

    _client(_inject(monkeypatch, toll=toll)).get(
        f"{PREFIX}/tollGantryFwqList", params={"type": "1", "sectionCode": "SD01,,"}
    )

    assert toll.calls[-1][1][0].section_code_list == ["SD01"]


def test_all_in_the_section_list_empties_the_filter(monkeypatch: Any) -> None:
    """整串里只要含 ``"all"`` 就把列表清空 -> SQL 的 ``<if>`` 不生效（= 全量）."""
    toll = _FakeService()

    _client(_inject(monkeypatch, toll=toll)).get(
        f"{PREFIX}/tollGantryFwqList", params={"type": "1", "sectionCode": "SD01,all"}
    )

    assert toll.calls[-1][1][0].section_code_list == []


@pytest.mark.parametrize(
    ("type_", "accessor", "rows", "expected"),
    [
        ("1", "toll", [OdsSzdnToll(toll_code="T1", toll_name="站一")], ["T1", "站一"]),
        ("2", "gantry", [OdsSzdnGantry(gantry_code="G1", gantry_name="门架一")], ["G1", "门架一"]),
        ("3", "fwqjcxx", [DwdLcztFwqjcxx(fwqbm="F1", fwqmc="服务区一")], ["F1", "服务区一"]),
    ],
)
def test_toll_list_maps_each_type_to_its_own_source(
    monkeypatch: Any, type_: str, accessor: str, rows: List[Any], expected: List[str]
) -> None:
    fake = _FakeService(select_list_new=rows)
    fakes = _inject(monkeypatch, **{accessor: fake})

    body = _client(fakes).get(
        f"{PREFIX}/tollGantryFwqList", params={"type": type_, "sectionCode": "SD01"}
    ).json()

    assert body["data"] == [{"type": type_, "code": expected[0], "name": expected[1]}]
    assert len(fake.called("select_list_new")) == 1
    # 另外两个数据源一次都没碰
    assert all(fakes[key].calls == [] for key in ("toll", "gantry", "fwqjcxx") if key != accessor)


def test_toll_list_ignores_an_unknown_type(monkeypatch: Any) -> None:
    fakes = _inject(monkeypatch)

    body = _client(fakes).get(
        f"{PREFIX}/tollGantryFwqList", params={"type": "9", "sectionCode": "SD01"}
    ).json()

    assert body["data"] == []
    assert all(fakes[key].calls == [] for key in ("toll", "gantry", "fwqjcxx"))


# --------------------------------------------------------------------------- 地图描点 / 预警


def test_car_location_clears_a_section_code_containing_all(monkeypatch: Any) -> None:
    """``"all" in sectionCode`` —— 是**子串**判断，``"all,SD01"`` 也会被清空."""
    car_info = _FakeService(car_location=[])

    _client(_inject(monkeypatch, car_info=car_info)).get(
        f"{PREFIX}/carLocation", params={"sectionCode": "all,SD01"}
    )

    assert car_info.calls[-1][1][0].section_code == ""


@pytest.mark.parametrize(
    ("type_", "field", "expected"),
    [
        ("1", "toll_code", "StationCapture"),
        ("2", "gantry_code", "GantryCapture"),
        ("3", "fwqbm", "ServiceAreaCapture"),
    ],
)
def test_car_location_fills_the_magic_capture_code(
    monkeypatch: Any, type_: str, field: str, expected: str
) -> None:
    car_info = _FakeService(car_location=[])

    _client(_inject(monkeypatch, car_info=car_info)).get(
        f"{PREFIX}/carLocation", params={"type": type_, "code": ""}
    )

    assert getattr(car_info.calls[-1][1][0], field) == expected


def test_car_location_keeps_a_supplied_code(monkeypatch: Any) -> None:
    car_info = _FakeService(car_location=[])

    _client(_inject(monkeypatch, car_info=car_info)).get(
        f"{PREFIX}/carLocation", params={"type": "1", "code": "T9"}
    )

    assert car_info.calls[-1][1][0].toll_code == "T9"


def test_car_location_ignores_the_code_when_type_is_blank(monkeypatch: Any) -> None:
    car_info = _FakeService(car_location=[])

    _client(_inject(monkeypatch, car_info=car_info)).get(
        f"{PREFIX}/carLocation", params={"code": "T9"}
    )

    param = car_info.calls[-1][1][0]
    assert param.toll_code is None
    assert param.gantry_code is None
    assert param.fwqbm is None


def test_car_warning_reuses_the_same_normalisation(monkeypatch: Any) -> None:
    warning = _FakeService(select_car_warning_info_list_limit100=[])

    _client(_inject(monkeypatch, car_warning_info=warning)).get(
        f"{PREFIX}/carWarning", params={"type": "2", "sectionCode": "all"}
    )

    param = warning.calls[-1][1][0]
    assert param.section_code == ""
    assert param.gantry_code == "GantryCapture"


# --------------------------------------------------------------------------- 统计


def test_car_statistics_passes_the_bound_query_through(monkeypatch: Any) -> None:
    confim = _FakeService(get_car_statistics=[CarStatisticsVO(escaped_type="10", number=3)])

    body = _client(_inject(monkeypatch, car_confim_free=confim)).get(
        f"{PREFIX}/carStatistics", params={"orgCode": "ORG-1"}
    ).json()

    assert body["data"] == [
        # ``BigDecimal`` 出的是 JSON **数字**并保留 scale（``BigDecimal.ZERO`` -> ``0``），
        # 见 COMPATIBILITY §41.4。
        {"escapedType": "10", "escapedTypeName": None, "number": 3, "escapedAmount": 0}
    ]
    assert isinstance(confim.calls[-1][1][0], IncomeStatisticParam)
    assert confim.calls[-1][1][0].org_code == "ORG-1"


def test_car_audit_keeps_the_zero_initialisers(monkeypatch: Any) -> None:
    """两个来源都回 ``null`` -> 响应体是 VO 的**零初值**，不是 ``null``."""
    fakes = _inject(monkeypatch)

    body = _client(fakes).get(f"{PREFIX}/carAudit").json()

    assert body["data"] == {
        "totalCount": 0,
        "finishedCount": 0,
        "totalAmount": 0,
        "finishedAmount": 0,
    }


def test_car_audit_maps_both_sources(monkeypatch: Any) -> None:
    ad = _FakeService(
        get_car_audit=CarStatisticsVO(number=7, escaped_amount=Decimal("12.5"))
    )
    cf = _FakeService(
        get_car_confirm=CarStatisticsVO(number=2, escaped_amount=Decimal("3.25"))
    )
    fakes = _inject(monkeypatch, car_aduit_free=ad, car_confim_free=cf)

    body = _client(fakes).get(f"{PREFIX}/carAudit", params={"orgId": "5"}).json()

    assert body["data"] == {
        "totalCount": 7,
        "finishedCount": 2,
        "totalAmount": 12.5,
        "finishedAmount": 3.25,
    }
    # 顺序固定：先异常流水，再确认追缴
    assert [name for name, _ in ad.calls + cf.calls] == ["get_car_audit", "get_car_confirm"]


def test_income_statistic_defaults_to_suo(monkeypatch: Any) -> None:
    ad = _FakeService(income_statistic=[])

    _client(_inject(monkeypatch, car_aduit_free=ad)).get(f"{PREFIX}/incomeStatistic")

    assert ad.calls[-1][1][0].query_date_type == "suo"


def test_income_statistic_keeps_zhan(monkeypatch: Any) -> None:
    ad = _FakeService(income_statistic=[])

    _client(_inject(monkeypatch, car_aduit_free=ad)).get(
        f"{PREFIX}/incomeStatistic", params={"queryDateType": "zhan"}
    )

    assert ad.calls[-1][1][0].query_date_type == "zhan"


# --------------------------------------------------------------------------- 列表类


def test_car_vo_list_is_a_plain_passthrough(monkeypatch: Any) -> None:
    car_info = _FakeService(select_car_vo_list=[CarInfoVO(car_no="京A12345")])

    body = _client(_inject(monkeypatch, car_info=car_info)).get(f"{PREFIX}/carVoList").json()

    assert body["data"] == [
        {"carNo": "京A12345", "carType": None, "escapedType": None, "escapedAmount": None}
    ]


def test_exception_car_and_top_ten_are_passthrough(monkeypatch: Any) -> None:
    suspicious = _FakeService(select_list_limit10=[{"carNo": "京A1"}])
    snapshot = _FakeService(get_top_ten=[TopTenVO(road_code="R1", rank=1, rate="100")])
    fakes = _inject(monkeypatch, car_suspicious=suspicious, snapshot_flow=snapshot)
    client = _client(fakes)

    assert client.get(f"{PREFIX}/exceptionCar").json()["data"] == [{"carNo": "京A1"}]
    assert client.get(f"{PREFIX}/topTen").json()["data"] == [
        {"roadCode": "R1", "sectionName": None, "carNum": None, "rank": 1, "rate": "100"}
    ]


def test_org_list_projects_exactly_two_columns(monkeypatch: Any) -> None:
    org = _FakeService(
        select_org_list=[
            OdsYhglVBaseOrg(org_code="O1", org_name="一所"),
            OdsYhglVBaseOrg(org_code="O2", org_name="二所"),
        ]
    )

    body = _client(_inject(monkeypatch, base_org=org)).get(f"{PREFIX}/orgList").json()

    assert body["data"] == [
        {"orgCode": "O1", "orgName": "一所"},
        {"orgCode": "O2", "orgName": "二所"},
    ]


# --------------------------------------------------------------------------- 异常流水


def test_except_record_list_enriches_every_row(monkeypatch: Any) -> None:
    """逐行补 ``orgId``，并在 ``car_aduit_free`` 里数到 > 0 条时置 ``"1"``."""
    rows = [
        CarExceptRecord(id="E1", car_id="C1", car_no="京A1"),
        CarExceptRecord(id="E2", car_id="C2", car_no="京A2"),
    ]
    record = _FakeService(select_list=rows)
    confim = _FakeService(select_org_id="ORG-9")

    class _CountingService(_FakeService):
        """只有 ``C1`` 有补缴记录 —— 逐行判断，不是整表判断."""

        def count_by_car_id(self, car_id: Optional[str]) -> int:
            self.calls.append(("count_by_car_id", (car_id,)))
            return 1 if car_id == "C1" else 0

    ad = _CountingService()

    fakes = _inject(monkeypatch, car_except_record=record, car_confim_free=confim, car_aduit_free=ad)

    body = _client(fakes).get(f"{PREFIX}/exceptRecordList", params={"carNo": "京A"}).json()

    assert body["code"] == 200
    assert body["msg"] == "查询成功"
    assert body["total"] == 2
    assert [row["orgId"] for row in body["rows"]] == ["ORG-9", "ORG-9"]
    assert [row["supplementaryStatus"] for row in body["rows"]] == ["1", "0"]
    # 分页入参按 Spring 的实体绑定进来（没有 @RequestBody）
    assert record.calls[-1][1][0].car_no == "京A"


def test_except_record_list_uses_batch_queries(monkeypatch: Any) -> None:
    """P2-1：批量方法可用时不再逐行调用 ``select_org_id`` / ``count_by_car_id``."""
    rows = [
        CarExceptRecord(id="E1", car_id="C1", car_no="京A1"),
        CarExceptRecord(id="E2", car_id="C2", car_no="京A2"),
    ]
    confim = _FakeService(select_org_ids={("C1", "E1"): "ORG-1", ("C2", "E2"): None})

    class _BatchCount(_FakeService):
        def count_by_car_ids(self, car_ids: Any) -> Dict[str, int]:
            self.calls.append(("count_by_car_ids", (list(car_ids),)))
            return {"C1": 2}

    ad = _BatchCount()
    fakes = _inject(
        monkeypatch,
        car_except_record=_FakeService(select_list=rows),
        car_confim_free=confim,
        car_aduit_free=ad,
    )

    body = _client(fakes).get(f"{PREFIX}/exceptRecordList").json()

    assert [row["orgId"] for row in body["rows"]] == ["ORG-1", None]
    assert [row["supplementaryStatus"] for row in body["rows"]] == ["1", "0"]
    assert confim.called("select_org_id") == []
    assert ad.called("count_by_car_id") == []
    assert ad.called("count_by_car_ids")[0][0] == ["C1", "C2"]


def test_except_record_list_keeps_the_default_status(monkeypatch: Any) -> None:
    rows = [CarExceptRecord(id="E1", car_id="C1")]
    record = _FakeService(select_list=rows)

    body = _client(_inject(monkeypatch, car_except_record=record)).get(
        f"{PREFIX}/exceptRecordList"
    ).json()

    assert body["rows"][0]["supplementaryStatus"] == "0"
    assert body["rows"][0]["orgId"] is None
