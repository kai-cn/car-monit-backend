#include "cm/base/repository/SnapshotFlowRepository.hpp"

#include <algorithm>
#include <map>

#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/framework/db/Db.hpp"

namespace cm::base::repository {
namespace {

/** 62 列，顺序与 ShardingSnapshotFlowMapper.xml 的 baseColumns / insertBatchToTable 完全一致 */
const std::vector<std::string> kColumns = {
    "big_id",          "lon",            "lat",             "deviceip",
    "siteid",          "laneid",         "snapshottimeunix", "snapshottime",
    "receivedtimeunix", "receivedtime",  "platenumber",     "platecolor",
    "platecolorcode",  "platetype",      "platetypecode",   "plateconfidence",
    "carbrand",        "carcolor",       "carcolorcode",    "cartype",
    "cartypecode",     "cardirection",   "snappicturepath", "smallpicturepath",
    "plategnssstatus", "gpsinfo",        "deviceid",        "devicename",
    "devicetype",      "gantrycode",     "gantryname",      "roadcode",
    "roadname",        "sectioncode",    "sectionname",     "tollcode",
    "tollname",        "orgcode",        "orgname",         "direction",
    "datasource",      "carclass",       "gantryid",        "smallsideimage",
    "headimageheight", "sidescenetypecode", "sidescenetype", "tailimagewidth",
    "envstate",        "headscenetypecode", "headscenetype", "sidedrivingdirectioncode",
    "sidedrivingdirection", "sideimageheight", "speed",    "tailplateimage",
    "headdrivingdirectioncode", "headdrivingdirection", "laneidcode", "carlength",
    "imagelevel",      "cameratype"};

/** JSON 字段名：big_id 在实体里是 bigId，其余列名即字段名 */
const char* jsonFieldFor(const std::string& column) {
    if (column == "big_id") return "bigId";
    return nullptr;  // 调用方回退到列名
}

bool isDateColumn(const std::string& column) {
    return column == "snapshottime" || column == "receivedtime";
}

/** 毫秒时间戳 -> +08:00 的 "yyyy-MM-dd HH:mm:ss"（JDBC setTimestamp 的等价文本） */
std::string msToDateTime(long long ms) {
    return cm::utils::DateUtils::formatInZone(ms, 8 * 3600, "%Y-%m-%d %H:%M:%S");
}

void bindJson(cm::db::Params& p, const Json& v, const std::string& column) {
    if (v.is_null()) {
        cm::db::bindNull(p);
        return;
    }
    if (isDateColumn(column)) {
        if (v.is_number_integer()) {
            cm::db::bind(p, msToDateTime(v.get<long long>()));
            return;
        }
        if (v.is_string()) {
            cm::db::bind(p, v.get<std::string>());
            return;
        }
    }
    if (v.is_string()) {
        cm::db::bind(p, v.get<std::string>());
    } else if (v.is_number_integer()) {
        cm::db::bind(p, v.get<long long>());
    } else if (v.is_number_unsigned()) {
        cm::db::bind(p, v.get<unsigned long long>());
    } else if (v.is_number_float()) {
        cm::db::bind(p, v.get<double>());
    } else if (v.is_boolean()) {
        cm::db::bind(p, v.get<bool>());
    } else {
        //   对象/数组：Java 侧不会出现（实体字段都是标量），按文本兜底
        cm::db::bind(p, v.dump());
    }
}

const Json* fieldOf(const Json& row, const std::string& column) {
    if (!row.is_object()) return nullptr;
    if (const char* alias = jsonFieldFor(column)) {
        if (row.contains(alias)) return &row[alias];
    }
    if (row.contains(column)) return &row[column];
    return nullptr;
}

} // namespace

SnapshotFlowRepository& SnapshotFlowRepository::instance() {
    static SnapshotFlowRepository r;
    return r;
}

const std::vector<std::string>& SnapshotFlowRepository::columns() { return kColumns; }

bool SnapshotFlowRepository::isKnownTableName(const std::string& table) {
    if (table == kActiveTable) return true;
    const std::string prefix = kTablePrefix;
    if (table.size() != prefix.size() + 6) return false;
    if (table.compare(0, prefix.size(), prefix) != 0) return false;
    for (size_t i = prefix.size(); i < table.size(); ++i) {
        if (table[i] < '0' || table[i] > '9') return false;
    }
    return true;
}

std::optional<std::string> SnapshotFlowRepository::monthTableForRow(const Json& row) {
    const Json* v = fieldOf(row, "snapshottime");
    if (v == nullptr || v->is_null()) return std::nullopt;
    if (v->is_number_integer()) {
        const long long ms = v->get<long long>();
        return std::string(kTablePrefix) + cm::utils::DateUtils::formatInZone(ms, 8 * 3600, "%Y%m");
    }
    if (v->is_string()) {
        const std::string s = v->get<std::string>();
        if (s.size() >= 7 && s[4] == '-') {
            return std::string(kTablePrefix) + s.substr(0, 4) + s.substr(5, 2);
        }
        auto tp = cm::utils::DateUtils::parseDate(s);
        if (tp) {
            return std::string(kTablePrefix) +
                   cm::utils::DateUtils::format(*tp, "%Y%m");
        }
    }
    return std::nullopt;
}

bool SnapshotFlowRepository::tableExists(const std::string& table) {
    if (!isKnownTableName(table)) return false;
    cm::db::Params p;
    cm::db::bind(p, table);
    const auto n = cm::db::Db::instance().scalar(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() "
        "AND TABLE_NAME = ?",
        p);
    return n && *n != "0";
}

bool SnapshotFlowRepository::createTableIfMissing(const std::string& table) {
    if (!isKnownTableName(table)) {
        LOG_ERROR("SnapshotFlow", "拒绝创建非法表名: " + table);
        return false;
    }
    // 与 Java createShardingTable 完全一致（表名来自白名单，可直接拼接）
    return cm::db::Db::instance().execute("CREATE TABLE IF NOT EXISTS " + table + " LIKE " +
                                          kActiveTable);
}

std::vector<std::string> SnapshotFlowRepository::listShardingTables() {
    std::vector<std::string> out;
    cm::db::Result r;
    cm::db::Params p;
    const std::string sql =
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() "
        "AND TABLE_NAME LIKE CONCAT(?, '%') ORDER BY TABLE_NAME DESC";
    cm::db::bind(p, std::string(kTablePrefix));
    if (!cm::db::Db::instance().query(sql, p, r)) return out;
    for (const auto& row : r.rows) {
        if (auto v = row.get("TABLE_NAME")) out.push_back(*v);
    }
    return out;
}

bool SnapshotFlowRepository::batchInsert(const std::string& table, const std::vector<Json>& rows,
                                         std::string& err) {
    if (rows.empty()) return true;
    if (!isKnownTableName(table)) {
        err = "非法表名: " + table;
        return false;
    }
    std::string colList;
    for (size_t i = 0; i < kColumns.size(); ++i) {
        if (i) colList += ",";
        colList += kColumns[i];
    }
    std::string sql = "INSERT INTO " + table + " (" + colList + ") VALUES ";
    cm::db::Params params;
    params.reserve(rows.size() * kColumns.size());
    for (size_t r = 0; r < rows.size(); ++r) {
        if (r) sql += ",";
        sql += "(";
        for (size_t c = 0; c < kColumns.size(); ++c) {
            if (c) sql += ",";
            sql += "?";
            const Json* v = fieldOf(rows[r], kColumns[c]);
            if (v == nullptr) {
                cm::db::bindNull(params);
            } else {
                bindJson(params, *v, kColumns[c]);
            }
        }
        sql += ")";
    }
    if (!cm::db::Db::instance().execute(sql, params)) {
        err = "批量插入失败: " + table;
        return false;
    }
    return true;
}

bool SnapshotFlowRepository::insertGroupedByMonth(const std::vector<Json>& rows, int* inserted,
                                                  std::string& err) {
    std::map<std::string, std::vector<Json>> grouped;
    for (const auto& row : rows) {
        auto table = monthTableForRow(row);
        if (!table) {
            err = "缺少合法的 snapshottime，无法路由分表";
            return false;
        }
        grouped[*table].push_back(row);
    }
    int count = 0;
    for (auto& kv : grouped) {
        if (!createTableIfMissing(kv.first)) {
            err = "创建分表失败: " + kv.first;
            return false;
        }
        // 单批过大时按 500 行切分，避免 max_allowed_packet
        const size_t kChunk = 500;
        for (size_t i = 0; i < kv.second.size(); i += kChunk) {
            const size_t end = std::min(i + kChunk, kv.second.size());
            std::vector<Json> chunk(kv.second.begin() + static_cast<std::ptrdiff_t>(i),
                                    kv.second.begin() + static_cast<std::ptrdiff_t>(end));
            if (!batchInsert(kv.first, chunk, err)) return false;
            count += static_cast<int>(chunk.size());
        }
    }
    if (inserted) *inserted = count;
    return true;
}

bool SnapshotFlowRepository::deleteById(const std::string& bigId) {
    std::vector<std::string> tables{kActiveTable};
    for (const auto& t : listShardingTables()) {
        if (t != kActiveTable) tables.push_back(t);
    }
    bool ok = true;
    for (const auto& table : tables) {
        if (!isKnownTableName(table)) continue;
        cm::db::Params p;
        cm::db::bind(p, bigId);
        if (!cm::db::Db::instance().execute("DELETE FROM " + table + " WHERE big_id = ?", p)) {
            ok = false;
        }
    }
    return ok;
}

std::optional<std::string> SnapshotFlowRepository::maxSnapshottime(const std::string& table) {
    if (!isKnownTableName(table)) return std::nullopt;
    return cm::db::Db::instance().scalar("SELECT MAX(snapshottime) FROM " + table);
}

} // namespace cm::base::repository
