"""门架抓拍流水增强查询服务（跨月份分表）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/service/enhanced/SnapshotFlowEnhancedService.java

Java 语义
---------
MySQL 侧按 ``ods_rt_szdn_snapshot_flow_yyyyMM`` 分表存抓拍流水（定时任务从 GaussDB
同步过来）。``queryPage`` 的策略：

1. 时间范围校验（超过当前时间 -> 直接返回空）；
2. 用 :class:`~app.base.sharding.sharding_table_util.ShardingTableUtil` 算出涉及的
   分表名；
3. 逐表统计总数（当前月精确 COUNT，历史月走 ``INFORMATION_SCHEMA`` 近似计数）；
4. 按全局 offset 跨表取数、合并；
5. 按 ``snapshottime`` 倒序返回。

三个必须照抄的怪异点
--------------------
1. **成功路径不设 ``code`` / ``msg``**：``queryFromShardingTables`` 返回的是一个
   **新建**的 ``TableDataInfo``，只 ``setRows`` / ``setTotal``。所以此时响应体是
   ``{"total": N, "rows": [...], "code": 0, "msg": null}`` —— 不是
   ``code=200`` / ``"查询成功"``。这不是笔误，见源码 178-285 行。
2. **``queryPage`` 自己吞掉所有异常**：``catch (Exception e)`` -> 空列表 + total 0。
   因此控制器里"失败就降级到 forest 代理"的那段 ``catch`` 是**死代码**，
   Python 侧同样保留这个结构（不删）。
3. **方向判空用的是 ``direction != null``**（``Integer`` 字段），所以
   ``direction=0`` 会真的参与过滤；其余字符串字段是 ``!= null and != ''``。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, List, Optional

from app.base.mapper.ods_rt_szdn_snapshot_flow_addcode_mapper import (
    OdsRtSzdnSnapshotFlowAddcodeMapper,
)
from app.base.sharding.sharding_table_util import ShardingTableUtil
from app.common.core.page.table_data_info import TableDataInfo
from app.common.utils.common_util import is_blank, is_not_blank

#: Java: ``private static final`` 的 ``SimpleDateFormat("yyyy-MM-dd HH:mm:ss")``
_DATETIME_PATTERN = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger(__name__)


class SnapshotFlowEnhancedService:
    """Java: ``@Service public class SnapshotFlowEnhancedService``."""

    def __init__(self, mapper: Optional[OdsRtSzdnSnapshotFlowAddcodeMapper] = None) -> None:
        self._mapper = mapper if mapper is not None else OdsRtSzdnSnapshotFlowAddcodeMapper()

    # Java: public TableDataInfo queryPage(OdsRtSzdnSnapshotFlowAddcode queryParam)
    def query_page(self, query_param: Any) -> TableDataInfo:
        result = TableDataInfo()
        result.set_code(200)
        result.set_msg("查询成功")

        # 步骤1: 时间参数校验
        if not self._validate_time_range(query_param):
            logger.warning("【时间校验】查询时间范围无效或超过当前时间，返回空数据")
            result.set_rows([])
            result.set_total(0)
            return result

        # 步骤2: 执行MySQL分表查询
        logger.info(
            "【分表查询】开始查询，时间范围: %s 至 %s",
            query_param.apply_time1,
            query_param.apply_time2,
        )
        try:
            result = self._query_from_sharding_tables(query_param)
        except Exception as exc:  # noqa: BLE001 —— Java: catch (Exception e)
            logger.error("【分表查询】查询失败: %s", exc)
            result.set_rows([])
            result.set_total(0)
        return result

    # Java: private boolean validateTimeRange(OdsRtSzdnSnapshotFlowAddcode queryParam)
    def _validate_time_range(self, query_param: Any) -> bool:
        apply_time1: Optional[str] = query_param.apply_time1
        apply_time2: Optional[str] = query_param.apply_time2

        # 如果时间参数为空，返回true（由上层判断）
        if is_blank(apply_time1) and is_blank(apply_time2):
            return True

        now = datetime.now()
        try:
            # 确保日期格式完整（添加时分秒）
            if apply_time1 is not None and len(apply_time1) == 10:
                apply_time1 = apply_time1 + " 00:00:00"
            if apply_time2 is not None and len(apply_time2) == 10:
                apply_time2 = apply_time2 + " 23:59:59"

            # 校验开始时间
            if is_not_blank(apply_time1):
                start_time = datetime.strptime(apply_time1, _DATETIME_PATTERN)
                if start_time > now:  # Java: startTime.after(now)
                    logger.warning("【时间校验】开始时间 %s 超过当前时间", apply_time1)
                    return False

            # 校验结束时间
            if is_not_blank(apply_time2):
                end_time = datetime.strptime(apply_time2, _DATETIME_PATTERN)
                if end_time > now:
                    logger.warning("【时间校验】结束时间 %s 超过当前时间", apply_time2)
                    return False

            # 校验时间范围逻辑
            if is_not_blank(apply_time1) and is_not_blank(apply_time2):
                start_time = datetime.strptime(apply_time1, _DATETIME_PATTERN)
                end_time = datetime.strptime(apply_time2, _DATETIME_PATTERN)
                if start_time > end_time:
                    logger.warning(
                        "【时间校验】开始时间 %s 大于结束时间 %s", apply_time1, apply_time2
                    )
                    return False
        except ValueError as exc:
            # Java: catch (ParseException e) -> return false
            logger.error("【时间校验】日期解析失败: %s", exc)
            return False
        return True

    # Java: private TableDataInfo queryFromShardingTables(OdsRtSzdnSnapshotFlowAddcode)
    def _query_from_sharding_tables(self, query_param: Any) -> TableDataInfo:
        result = TableDataInfo()
        all_list: List[Any] = []
        total = 0

        # 步骤1: 根据时间范围获取所有涉及的分表名列表
        table_names = ShardingTableUtil.get_table_names_by_date_range(
            query_param.apply_time1, query_param.apply_time2
        )
        logger.info(
            "【分表查询】需要查询的分表数量: %s, 表名列表: %s", len(table_names), table_names
        )

        # 步骤2: 获取当前月份表名（用于判断是否需要精确计数）
        current_month_table = ShardingTableUtil.get_table_name_by_date(datetime.now())

        # 步骤3: 遍历所有分表，统计总记录数（优化版）
        for table_name in table_names:
            try:
                if table_name == current_month_table:
                    # 当前月份表：数据可能还在写入，使用精确COUNT
                    count = self._mapper.select_sharding_count(table_name, query_param)
                    logger.info("【分表统计】表 %s (当前月) 精确记录数: %s", table_name, count)
                else:
                    # 历史月份表：数据稳定，使用近似计数
                    count = self._get_approximate_count(table_name, query_param)
                    logger.info("【分表统计】表 %s (历史月) 近似记录数: %s", table_name, count)
                total += count
            except Exception as exc:  # noqa: BLE001 —— 表不存在时跳过
                logger.warning("【分表统计】表 %s 不存在或查询失败: %s", table_name, exc)

        # 步骤4: 计算分页参数
        page_num = query_param.page_num if query_param.page_num is not None else 1
        page_size = query_param.page_size if query_param.page_size is not None else 10
        offset = (page_num - 1) * page_size  # 全局偏移量
        logger.info("【分页参数】页码: %s, 每页大小: %s, 全局偏移量: %s", page_num, page_size, offset)

        # 如果总记录数小于偏移量，直接返回空数据
        if total <= offset:
            logger.info("【分表查询】总记录数 %s <= 偏移量 %s，返回空数据", total, offset)
            result.set_rows(all_list)
            result.set_total(total)
            return result

        # 步骤5: 跨分表分页查询
        remaining = page_size  # 还需要获取的记录数
        current_offset = offset  # 当前表内的偏移量

        for table_name in table_names:
            if remaining <= 0:
                break
            try:
                # 获取当前表的记录数（精确计数，因为分页需要准确判断）
                table_count = self._mapper.select_sharding_count(table_name, query_param)

                # 如果全局偏移量超过当前表的记录数，跳过当前表
                if current_offset >= table_count:
                    current_offset -= table_count
                    logger.debug(
                        "【分页查询】跳过表 %s (offset=%s >= 表记录数=%s)",
                        table_name,
                        current_offset + table_count,
                        table_count,
                    )
                    continue

                logger.debug(
                    "【分页查询】从表 %s 获取数据，偏移量: %s, 需要数量: %s",
                    table_name,
                    current_offset,
                    remaining,
                )
                table_list = self._mapper.select_sharding_list(
                    table_name, query_param, current_offset
                )

                # 计算实际获取的数量（Java: Math.min(...)）
                take = min(len(table_list), remaining)
                all_list.extend(table_list[:take])
                remaining -= take
                current_offset = 0  # 下一个表从0开始

                logger.info("【分页查询】表 %s 获取了 %s 条数据，剩余需要获取: %s", table_name, take, remaining)
            except Exception as exc:  # noqa: BLE001
                logger.warning("【分页查询】表 %s 查询失败: %s", table_name, exc)

        # 步骤6: 按抓拍时间倒序排序（确保跨分表数据的时间顺序正确）
        # Java: Comparator.comparing(getSnapshottime).reversed() —— snapshottime 为空会 NPE，
        # Python 侧把 None 排在最后（等价于"空值不参与排序"的实用近似）。
        all_list.sort(key=lambda item: (item.snapshottime is None, item.snapshottime), reverse=True)

        result.set_rows(all_list)
        result.set_total(total)
        logger.info("【分表查询完成】总记录数: %s, 当前页数据量: %s", total, len(all_list))
        return result

    # Java: private long getApproximateCount(String tableName, OdsRtSzdnSnapshotFlowAddcode)
    def _get_approximate_count(self, table_name: str, query_param: Any) -> int:
        if self._has_extra_filters(query_param):
            # 如果有额外过滤条件，需要执行精确COUNT
            logger.debug("【近似计数】存在额外过滤条件，使用精确COUNT")
            return self._mapper.select_sharding_count(table_name, query_param)

        try:
            approx_count = self._mapper.get_table_approximate_count(table_name)
            if approx_count is not None and approx_count > 0:
                logger.debug("【近似计数】表 %s 的近似行数: %s", table_name, approx_count)
                return approx_count
        except Exception as exc:  # noqa: BLE001
            logger.warning("【近似计数】获取表 %s 近似行数失败: %s", table_name, exc)

        # 降级到精确COUNT
        return self._mapper.select_sharding_count(table_name, query_param)

    # Java: private boolean hasExtraFilters(OdsRtSzdnSnapshotFlowAddcode queryParam)
    @staticmethod
    def _has_extra_filters(query_param: Any) -> bool:
        return (
            is_not_blank(query_param.platenumber)
            or is_not_blank(query_param.deviceid)
            or is_not_blank(query_param.gantrycode)
            or is_not_blank(query_param.section_code_str)
            or query_param.direction is not None
            or is_not_blank(query_param.platecolor)
            or is_not_blank(query_param.cartype)
            or is_not_blank(query_param.datasource)
        )

    # Java: public List<OdsRtSzdnSnapshotFlowAddcode> queryListForExport(...)
    def query_list_for_export(self, query_param: Any) -> List[Any]:
        """导出的列表查询 —— 不做分页限制。

        注意 XML 的 ``LIMIT #{offset}, #{pageSize}`` 判据是
        ``pageNum != null and pageSize != null``；控制器已把两者补成 1/10，
        所以导出**仍会被 ``pageSize`` 截断**（Java 原样如此，照抄）。
        """
        all_list: List[Any] = []
        table_names = ShardingTableUtil.get_table_names_by_date_range(
            query_param.apply_time1, query_param.apply_time2
        )
        for table_name in table_names:
            try:
                table_list = self._mapper.select_sharding_list(table_name, query_param, 0)
                all_list.extend(table_list)
            except Exception as exc:  # noqa: BLE001
                logger.warning("【导出查询】表 %s 查询失败: %s", table_name, exc)

        all_list.sort(key=lambda item: (item.snapshottime is None, item.snapshottime), reverse=True)
        return all_list


_SERVICE: Optional[SnapshotFlowEnhancedService] = None


def get_snapshot_flow_enhanced_service() -> SnapshotFlowEnhancedService:
    """Java: ``@Autowired SnapshotFlowEnhancedService``（Spring 单例）。"""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SnapshotFlowEnhancedService()
    return _SERVICE


def reset_snapshot_flow_enhanced_service() -> None:
    """Test helper: drop the cached singleton so a fake mapper can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SnapshotFlowEnhancedService",
    "get_snapshot_flow_enhanced_service",
    "reset_snapshot_flow_enhanced_service",
]
