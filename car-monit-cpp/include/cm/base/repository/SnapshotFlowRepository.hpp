#pragma once
// 门架抓拍流水的分表读写（对应 Java 的 OdsRtSzdnSnapshotFlowAddcodeMapper +
// ShardingSnapshotFlowMapper + ShardingTableUtil + ShardingSphere 路由）。
//
// 分表规则（与 Java 一致）：按 snapshottime 的月份，表名 = 前缀 + "_" + yyyyMM，
// 逻辑表 ods_rt_szdn_snapshot_flow 由 ShardingSphere 路由；C++ 没有中间件，
// 因此在仓储层显式分组后逐表写入。建表 DDL 与 Java 完全一致：
//   CREATE TABLE IF NOT EXISTS <t> LIKE ods_rt_szdn_snapshot_flow_addcode
#include <optional>
#include <string>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::base::repository {

class SnapshotFlowRepository {
public:
    static SnapshotFlowRepository& instance();

    static constexpr const char* kActiveTable = "ods_rt_szdn_snapshot_flow_addcode";
    static constexpr const char* kTablePrefix = "ods_rt_szdn_snapshot_flow_";

    /** 表名是否来自白名单（活跃表或 <前缀><6 位数字>），防动态标识符注入 */
    static bool isKnownTableName(const std::string& table);

    /** 根据 snapshottime 推导分表名；缺失/非法返回 nullopt（对应 ShardingSphere 路由失败） */
    static std::optional<std::string> monthTableForRow(const Json& row);

    bool tableExists(const std::string& table);
    bool createTableIfMissing(const std::string& table);
    /** 对应 listShardingTables：前缀匹配，按表名倒序 */
    std::vector<std::string> listShardingTables();

    /** 全部业务列（62 列，与 ShardingSnapshotFlowMapper.xml 的 baseColumns 一致） */
    static const std::vector<std::string>& columns();

    /** 单表批量插入；rows 必须是同一月份（调用方负责分组） */
    bool batchInsert(const std::string& table, const std::vector<Json>& rows, std::string& err);

    /** 按 snapshottime 分组后批量插入（对应 ShardingSphere 的自动路由） */
    bool insertGroupedByMonth(const std::vector<Json>& rows, int* inserted, std::string& err);

    /** 对应 MyBatis-Plus removeById：无分片键 ⇒ 广播到活跃表 + 所有分表 */
    bool deleteById(const std::string& bigId);

    /** 对应 getMaxSnapshottime(tableName) */
    std::optional<std::string> maxSnapshottime(const std::string& table);

private:
    SnapshotFlowRepository() = default;
};

} // namespace cm::base::repository
