"""分表查询的计数策略（P2-2 修复：过滤条件不能走批量近似值）."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from app.base.service.enhanced.snapshot_flow_enhanced_service import (
    SnapshotFlowEnhancedService,
)


def _query(**overrides: Any) -> SimpleNamespace:
    values: Dict[str, Any] = {
        "apply_time1": "2026-01-01",
        "apply_time2": "2026-03-01",
        "page_num": 1,
        "page_size": 10,
        "platenumber": None,
        "deviceid": None,
        "gantrycode": None,
        "section_code_str": None,
        "direction": None,
        "platecolor": None,
        "cartype": None,
        "datasource": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _Mapper:
    def __init__(self, exact: int = 5, approx_batch: Optional[Dict[str, int]] = None) -> None:
        self.exact = exact
        self.approx_batch = approx_batch or {}
        self.count_calls: List[str] = []
        self.batch_calls = 0
        self.approx_calls: List[str] = []

    def select_sharding_count(self, table_name: str, _query_param: Any) -> int:
        self.count_calls.append(table_name)
        return self.exact

    def get_table_approximate_counts(self, _table_names: List[str]) -> Dict[str, int]:
        self.batch_calls += 1
        return dict(self.approx_batch)

    def get_table_approximate_count(self, table_name: str) -> int:
        self.approx_calls.append(table_name)
        return 999

    def select_sharding_list(self, table_name: str, _query_param: Any, _offset: int) -> List[Any]:
        return []


@pytest.fixture(autouse=True)
def _sharding_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.base.sharding import sharding_table_util as util_module

    monkeypatch.setattr(
        util_module.ShardingTableUtil,
        "get_table_names_by_date_range",
        staticmethod(lambda _a, _b: ["t1", "t2", "t3"]),
    )
    # 返回一个不在列表里的"当前月"，让三张表都走历史分支。
    monkeypatch.setattr(
        util_module.ShardingTableUtil,
        "get_table_name_by_date",
        staticmethod(lambda _when: "t_current"),
    )


def test_filtered_query_never_uses_batch_approximation() -> None:
    """带过滤条件时 total 必须来自精确 COUNT，不能用整表近似行数（回归 P2-2）."""
    mapper = _Mapper(exact=5, approx_batch={"t1": 100, "t2": 100, "t3": 100})
    service = SnapshotFlowEnhancedService(mapper=mapper)

    result = service._query_from_sharding_tables(_query(platenumber="闽A12345"))

    assert result.get_total() == 15
    assert mapper.batch_calls == 0
    assert mapper.approx_calls == []


def test_unfiltered_query_uses_batch_approximation() -> None:
    """无过滤条件时才允许用一次批量近似计数."""
    mapper = _Mapper(exact=5, approx_batch={"t1": 2, "t2": 3, "t3": 4})
    service = SnapshotFlowEnhancedService(mapper=mapper)

    result = service._query_from_sharding_tables(_query())

    assert result.get_total() == 9
    assert mapper.batch_calls == 1
    assert mapper.approx_calls == []
