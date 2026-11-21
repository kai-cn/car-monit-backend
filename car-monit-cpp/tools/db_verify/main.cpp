// 参数绑定 vs 手工拼接：真库对照验证工具（一次性验收用，默认不参与构建）
//
// 用法：
//   set CM_VERIFY_DB_HOST=127.0.0.1
//   set CM_VERIFY_DB_PORT=33309
//   set CM_VERIFY_DB_USER=root
//   set CM_VERIFY_DB_PASS=
//   set CM_VERIFY_DB_NAME=cm_bind_verify_20261107
//   carmonit_db_verify
//
// 对每个矩阵项：同一份种子数据，分别用「旧写法（Db::lit 拼接字面量）」和
// 「新写法（cm::db::bind 绑定）」执行语义等价的查询，比较结果集是否一致；
// 再对写入路径做回读比较（含 DECIMAL 标度、19 位整数、超长文本）。
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

#include "cm/common/utils/Logger.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/db/Param.hpp"

using cm::db::Db;
using cm::db::Params;
using cm::db::Result;

namespace {

int g_pass = 0;
int g_fail = 0;

std::string env(const char* k, const std::string& def = "") {
    const char* v = std::getenv(k);
    return v ? std::string(v) : def;
}

void report(bool ok, const std::string& name, const std::string& detail) {
    if (ok) {
        ++g_pass;
        std::cout << "[PASS] " << name << "  " << detail << "\n";
    } else {
        ++g_fail;
        std::cout << "[FAIL] " << name << "  " << detail << "\n";
    }
}

void exec(const std::string& sql) {
    if (!Db::instance().execute(sql)) {
        std::cout << "[WARN] 执行失败: " << sql << "\n";
    }
}

long long insertRow(const std::string& sql) {
    long long id = -1;
    Db::instance().execute(sql, nullptr, &id);
    return id;
}

/** 执行查询并返回某一列的值列表（按出现顺序） */
std::vector<std::string> column(const std::string& sql, const std::string& col) {
    Result r;
    std::vector<std::string> out;
    if (!Db::instance().query(sql, r)) {
        out.push_back("<QUERY_ERROR>");
        return out;
    }
    for (const auto& row : r.rows) {
        auto v = row.get(col);
        out.push_back(v ? *v : std::string("<NULL>"));
    }
    return out;
}

std::vector<std::string> columnBound(const std::string& sql, const std::string& col) {
    Result r;
    std::vector<std::string> out;
    if (!Db::instance().query(sql, r)) {
        out.push_back("<QUERY_ERROR>");
        return out;
    }
    for (const auto& row : r.rows) {
        auto v = row.get(col);
        out.push_back(v ? *v : std::string("<NULL>"));
    }
    return out;
}

std::string join(const std::vector<std::string>& v) {
    std::string s;
    for (size_t i = 0; i < v.size(); ++i) {
        if (i) s += "|";
        s += v[i];
    }
    return "[" + s + "]";
}

/** 矩阵项：同一个查询，用旧拼接写法与新绑定写法各跑一次，比较结果 */
void compareQuery(const std::string& name, const std::string& literalSql, const std::string& boundSqlTemplate) {
    const auto lit = column(literalSql, "id");
    // 绑定写法：模板里放 cm::db::bind(...) 令牌
    std::string boundSql = boundSqlTemplate;
    const auto bnd = columnBound(boundSql, "id");
    const bool noErr = (lit.empty() || lit.front() != "<QUERY_ERROR>") &&
                       (bnd.empty() || bnd.front() != "<QUERY_ERROR>");
    const bool ok = (lit == bnd) && noErr;
    report(ok, name, "literal=" + join(lit) + " bound=" + join(bnd));
}

void reset() {
    exec("TRUNCATE TABLE t_probe");
}

void seedBasics() {
    reset();
    // 注意：这里必须用「令牌 API」（cm::db::bind(v)，不带 Params 参数）。
    // 显式 Params 版本若在同一条表达式里连续 bind 多个值，C++ 对操作数的求值顺序
    // 不作保证，参数顺序会错位 —— 令牌 API 按 SQL 文本位置解析，天然有序。
    exec("INSERT INTO t_probe (name, tags, note, amount, big, created) VALUES (" +
         cm::db::bind(std::string("云A云")) + "," + cm::db::bind(std::string("1,2,3")) + "," +
         cm::db::bind(std::string("中文备注")) + "," + cm::db::bind(std::string("116.500")) + "," +
         cm::db::bind(1234567890123456789LL) + "," +
         cm::db::bind(std::string("2024-01-15 10:00:00")) + ")");
    exec("INSERT INTO t_probe (name, tags, note, amount, big, created) VALUES (" +
         cm::db::bind(std::string("🚗abc")) + "," + cm::db::bind(std::string("9")) + "," +
         cm::db::bind(std::string("emoji")) + "," + cm::db::bind(std::string("0.001")) + "," +
         cm::db::bind(9007199254740993LL) + "," +
         cm::db::bind(std::string("2024-02-01 00:00:00")) + ")");
    exec("INSERT INTO t_probe (name, tags, note) VALUES (" +
         cm::db::bind(std::string("A'B\"C\\D")) + "," + cm::db::bind(std::string("")) + "," +
         cm::db::bindNull() + ")");
    exec("INSERT INTO t_probe (name, tags, note) VALUES (" + cm::db::bindNull() + "," +
         cm::db::bind(std::string("null-row")) + "," + cm::db::bind(std::string("")) + ")");
    // LIKE 元字符行
    exec("INSERT INTO t_probe (name) VALUES (" + cm::db::bind(std::string("a%b_c")) + ")");
    exec("INSERT INTO t_probe (name) VALUES (" + cm::db::bind(std::string("axbxc")) + ")");
    // 超长文本（60000，TEXT 上限 65535 字节内）
    exec("INSERT INTO t_probe (name, note) VALUES (" + cm::db::bind(std::string("longtext")) + "," +
         cm::db::bind(std::string(60000, 'x')) + ")");
}

void matrixLiteralVsBound() {
    // 1) 中文
    compareQuery("中文等值", "SELECT id FROM t_probe WHERE name = '云A云'",
                 "SELECT id FROM t_probe WHERE name = " +
                     cm::db::bind(std::string("云A云")));
    // 2) emoji（4 字节 UTF-8）
    compareQuery("emoji 等值", "SELECT id FROM t_probe WHERE name = '🚗abc'",
                 "SELECT id FROM t_probe WHERE name = " +
                     cm::db::bind(std::string("🚗abc")));
    // 3) 单双引号与反斜杠：旧写法必须经 Db::lit 转义
    {
        const std::string raw = "A'B\"C\\D";
        compareQuery("引号/反斜杠 等值",
                     "SELECT id FROM t_probe WHERE name = " + Db::lit(raw),
                     "SELECT id FROM t_probe WHERE name = " + cm::db::bind(raw));
    }
    // 3b) 注入串：两种写法都不得命中额外行
    {
        const std::string inj = "x' OR '1'='1";
        compareQuery("注入串不放大结果",
                     "SELECT id FROM t_probe WHERE name = " + Db::lit(inj),
                     "SELECT id FROM t_probe WHERE name = " + cm::db::bind(inj));
    }
    // 4) LIKE 含 % 与 _
    compareQuery("LIKE 含 %", "SELECT id FROM t_probe WHERE name like concat('%', " +
                                  Db::lit(std::string("a%b")) + ", '%')",
                 "SELECT id FROM t_probe WHERE name like concat('%', " +
                     cm::db::bind(std::string("a%b")) + ", '%')");
    compareQuery("LIKE 含 _", "SELECT id FROM t_probe WHERE name like " + Db::lit(std::string("a_b_c")),
                 "SELECT id FROM t_probe WHERE name like " + cm::db::bind(std::string("a_b_c")));
    // 5) find_in_set
    compareQuery("find_in_set 命中", "SELECT id FROM t_probe WHERE find_in_set(" +
                                         Db::lit(std::string("2")) + ", tags)",
                 "SELECT id FROM t_probe WHERE find_in_set(" +
                     cm::db::bind(std::string("2")) + ", tags)");
    compareQuery("find_in_set 不命中", "SELECT id FROM t_probe WHERE find_in_set(" +
                                          Db::lit(std::string("7")) + ", tags)",
                 "SELECT id FROM t_probe WHERE find_in_set(" +
                     cm::db::bind(std::string("7")) + ", tags)");
    // 6) 日期区间两端（date_format 形式，与 CrudEngine rangeExpr 一致）
    {
        const std::string b = "2024-01-15", e = "2024-01-15";
        compareQuery("日期区间（同日两端）",
                     "SELECT id FROM t_probe WHERE date_format(created,'%Y%m%d') >= date_format(" +
                         Db::lit(b) + ",'%Y%m%d') and date_format(created,'%Y%m%d') <= date_format(" +
                         Db::lit(e) + ",'%Y%m%d')",
                     "SELECT id FROM t_probe WHERE date_format(created,'%Y%m%d') >= date_format(" +
                         cm::db::bind(b) + ",'%Y%m%d') and date_format(created,'%Y%m%d') <= date_format(" +
                         cm::db::bind(e) + ",'%Y%m%d')");
        compareQuery("日期区间（跨月）",
                     "SELECT id FROM t_probe WHERE date_format(created,'%Y%m%d') >= date_format(" +
                         Db::lit(std::string("2024-01-01")) + ",'%Y%m%d') and date_format(created,'%Y%m%d') <= date_format(" +
                         Db::lit(std::string("2024-02-29")) + ",'%Y%m%d')",
                     "SELECT id FROM t_probe WHERE date_format(created,'%Y%m%d') >= date_format(" +
                         cm::db::bind(std::string("2024-01-01")) + ",'%Y%m%d') and date_format(created,'%Y%m%d') <= date_format(" +
                         cm::db::bind(std::string("2024-02-29")) + ",'%Y%m%d')");
    }
    // 7) IN 多值与空列表
    {
        std::vector<long long> ids{1, 2};
        std::vector<long long> empty;
        compareQuery("IN 多值", "SELECT id FROM t_probe WHERE id IN (1, 2)",
                     "SELECT id FROM t_probe WHERE id IN " + cm::db::bindIn(ids));
        compareQuery("IN 空列表", "SELECT id FROM t_probe WHERE id IN (NULL)",
                     "SELECT id FROM t_probe WHERE id IN " + cm::db::bindIn(empty));
    }
    // 8) NULL vs 空串
    compareQuery("IS NULL 只命中 NULL 行", "SELECT id FROM t_probe WHERE name IS NULL",
                 "SELECT id FROM t_probe WHERE name IS NULL");
    compareQuery("= 空串只命中空串行", "SELECT id FROM t_probe WHERE name = ''",
                 "SELECT id FROM t_probe WHERE name = " + cm::db::bind(std::string("")));
    compareQuery("note 空串 vs NULL 区分", "SELECT id FROM t_probe WHERE note = ''",
                 "SELECT id FROM t_probe WHERE note = " + cm::db::bind(std::string("")));
    // 9) 19 位雪花
    compareQuery("19 位 BIGINT 等值", "SELECT id FROM t_probe WHERE big = 1234567890123456789",
                 "SELECT id FROM t_probe WHERE big = " +
                     cm::db::bind(1234567890123456789LL));
    // 正好超过 double 精度（2^53+1）
    compareQuery("2^53+1 精度不丢", "SELECT id FROM t_probe WHERE big = 9007199254740993",
                 "SELECT id FROM t_probe WHERE big = " +
                     cm::db::bind(9007199254740993LL));
    // 10) DECIMAL
    compareQuery("DECIMAL 116.500 等值", "SELECT id FROM t_probe WHERE amount = 116.500",
                 "SELECT id FROM t_probe WHERE amount = " +
                     cm::db::bind(std::string("116.500")));
    compareQuery("DECIMAL 0.001 等值", "SELECT id FROM t_probe WHERE amount = 0.001",
                 "SELECT id FROM t_probe WHERE amount = " +
                     cm::db::bind(std::string("0.001")));
}

void roundtripChecks() {
    // 写入后回读：DECIMAL 标度、19 位整数、超长文本、NULL/空串
    Result r;
    if (!Db::instance().query("SELECT amount, big, CHAR_LENGTH(note) AS nlen, note IS NULL AS isnul, "
                              "name FROM t_probe WHERE name = '云A云'",
                              r) || r.rows.empty()) {
        report(false, "回读中文行", "查询失败或行为空");
        return;
    }
    const auto& row = r.rows.front();
    report(row.str("amount") == "116.500", "DECIMAL 标度保留", "amount=" + row.str("amount"));
    report(row.str("big") == "1234567890123456789", "19 位整数回读无损", "big=" + row.str("big"));

    Result r2;
    Db::instance().query("SELECT CHAR_LENGTH(note) AS nlen FROM t_probe WHERE name = 'longtext'", r2);
    const std::string nlen = r2.rows.empty() ? "" : r2.rows.front().str("nlen");
    report(nlen == "60000", "超长文本 60k 往返", "char_length=" + nlen);

    Result r3;
    Db::instance().query(
        "SELECT (SELECT COUNT(*) FROM t_probe WHERE name IS NULL) AS nulls,"
        " (SELECT COUNT(*) FROM t_probe WHERE name = '') AS empties", r3);
    if (!r3.rows.empty()) {
        const std::string nulls = r3.rows.front().str("nulls");
        const std::string empties = r3.rows.front().str("empties");
        report(nulls == "1" && empties == "0", "NULL 与空串写入区分",
               "nulls=" + nulls + " empties=" + empties);
    }

    // 反斜杠/引号串回读原样
    Result r4;
    Db::instance().query("SELECT name FROM t_probe WHERE id = 3", r4);
    const std::string nm = r4.rows.empty() ? "" : r4.rows.front().str("name");
    report(nm == "A'B\"C\\D", "引号/反斜杠回读原样", "name=" + nm);
}

/** 三场景 QPS/P99：拼接（literal）vs 绑定（bound） */
struct Bench {
    std::string name;
    std::string litSql;
    std::string boundSql;
    int iterations;
};

void benchOne(const Bench& b) {
    auto run = [&](bool bound) {
        std::vector<double> us;
        us.reserve(b.iterations);
        for (int i = 0; i < b.iterations; ++i) {
            const auto t0 = std::chrono::steady_clock::now();
            Result r;
            if (bound)
                Db::instance().query(b.boundSql, r);
            else
                Db::instance().query(b.litSql, r);
            const auto t1 = std::chrono::steady_clock::now();
            us.push_back(std::chrono::duration<double, std::micro>(t1 - t0).count());
        }
        std::sort(us.begin(), us.end());
        const double total = std::accumulate(us.begin(), us.end(), 0.0);
        const double p99 = us[static_cast<size_t>(us.size() * 0.99)];
        const double qps = us.size() / (total / 1e6);
        return std::make_pair(qps, p99);
    };
    // 预热（让 PREPARE 缓存命中，测稳态）
    { Result r; Db::instance().query(b.boundSql, r); }
    { Result r; Db::instance().query(b.litSql, r); }
    const auto lit = run(false);
    const auto bnd = run(true);
    char buf[256];
    std::snprintf(buf, sizeof(buf), "%s: 拼接 QPS=%.1f P99=%.1fus | 绑定 QPS=%.1f P99=%.1fus | 比值=%.2fx",
                  b.name.c_str(), lit.first, lit.second, bnd.first, bnd.second,
                  bnd.first / lit.first);
    report(true, "BENCH", buf);
}

void benchmark() {
    const int N = 3000;
    {
        Bench b{"简单查询", "SELECT id FROM t_probe WHERE name = '云A云'",
                "SELECT id FROM t_probe WHERE name = " + cm::db::bind(std::string("云A云")), N};
        benchOne(b);
    }
    {
        Bench b{"5 个条件",
                "SELECT id FROM t_probe WHERE name like concat('%','云','%') and tags like concat('%','1','%')"
                " and big >= 1 and created >= '2024-01-01 00:00:00' and note is not null",
                "SELECT id FROM t_probe WHERE name like concat('%'," + cm::db::bind(std::string("云")) +
                    ",'%') and tags like concat('%'," + cm::db::bind(std::string("1")) +
                    ",'%') and big >= " + cm::db::bind(1LL) + " and created >= " +
                    cm::db::bind(std::string("2024-01-01 00:00:00")) + " and note is not null",
                N};
        benchOne(b);
    }
    {
        Bench b{"分页 count+data",
                "SELECT id FROM t_probe WHERE name is not null ORDER BY id LIMIT 0,10",
                "SELECT id FROM t_probe WHERE name is not null ORDER BY id LIMIT 0,10", N};
        benchOne(b);
    }
}

} // namespace

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);  // 崩溃时也要看到已输出的诊断行
    cm::log::Logger::instance().init("logs", "info");

    cm::db::DbConfig cfg;
    cfg.host = env("CM_VERIFY_DB_HOST", "127.0.0.1");
    cfg.port = std::stoi(env("CM_VERIFY_DB_PORT", "33309"));
    cfg.user = env("CM_VERIFY_DB_USER", "root");
    cfg.password = env("CM_VERIFY_DB_PASS", "");
    cfg.database = env("CM_VERIFY_DB_NAME", "cm_bind_verify_20261107");

    Db::instance().init(cfg, 1, 1, 4, 3000, 64);
    if (!Db::instance().ready()) {
        std::cout << "[FATAL] Db 未就绪\n";
        return 2;
    }
    {
        Result r;
        if (!Db::instance().query("SELECT 1", r)) {
            std::cout << "[FATAL] 无法执行 SELECT 1\n";
            return 2;
        }
    }
    std::cout << "=== 目标库: " << cfg.host << ":" << cfg.port << "/" << cfg.database << " ===\n";

    // 诊断：直接用一条连接跑 PREPARE 路径，把驱动侧错误原样打出来
    {
        auto conn = Db::instance().pool().borrow();
        if (conn) {
            cm::db::Params p;
            const std::string sql = "SELECT ? AS v";
            p.push_back(cm::db::Param{cm::db::ParamKind::Text, "诊断中文"});
            Result dr;
            const bool ok = conn->queryPrepared(sql, p, dr);
            std::cout << "[DIAG] queryPrepared ok=" << (ok ? 1 : 0)
                      << " lastError=" << conn->lastError()
                      << " rows=" << dr.rows.size() << "\n";
            std::cout << "[DIAG] preparedCacheSize=" << conn->preparedCacheSize()
                      << " serverStmtLimit=" << conn->serverPreparedStmtLimit() << "\n";
            Db::instance().pool().release(conn);
        }
    }

    seedBasics();
    matrixLiteralVsBound();
    roundtripChecks();

    std::cout << "\n=== 性能（每场景 " << 3000 << " 次，单连接，已预热） ===\n";
    benchmark();

    std::cout << "\n通过 " << g_pass << " / 失败 " << g_fail << "\n";
    return g_fail == 0 ? 0 : 1;
}
