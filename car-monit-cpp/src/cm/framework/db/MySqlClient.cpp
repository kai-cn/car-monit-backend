// MySQL wire protocol 客户端实现（文本协议）
//
// 参考协议文档: https://dev.mysql.com/doc/dev/mysql-server/latest/PAGE_PROTOCOL.html
// 支持:
//   * Handshake v10
//   * mysql_native_password / caching_sha2_password（fast auth + RSA full auth）
//   * COM_QUERY 文本协议、多结果集、OK/ERR/EOF 解析
//   * 显式事务
#include "cm/framework/db/MySqlClient.hpp"

#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/common/utils/crypto/Rsa.hpp"
#include "cm/framework/net/Os.hpp"

#include <cerrno>
#include <chrono>
#include <cstring>
#include <iostream>

namespace cm::db {
namespace {

// --- capability flags -------------------------------------------------------
constexpr uint32_t CLIENT_LONG_PASSWORD = 0x00000001;
constexpr uint32_t CLIENT_FOUND_ROWS = 0x00000002;
constexpr uint32_t CLIENT_LONG_FLAG = 0x00000004;
constexpr uint32_t CLIENT_CONNECT_WITH_DB = 0x00000008;
constexpr uint32_t CLIENT_PROTOCOL_41 = 0x00000200;
constexpr uint32_t CLIENT_TRANSACTIONS = 0x00002000;
constexpr uint32_t CLIENT_SECURE_CONNECTION = 0x00008000;
constexpr uint32_t CLIENT_MULTI_STATEMENTS = 0x00010000;
constexpr uint32_t CLIENT_MULTI_RESULTS = 0x00020000;
constexpr uint32_t CLIENT_PLUGIN_AUTH = 0x00080000;
constexpr uint32_t CLIENT_PLUGIN_AUTH_LENENC_CLIENT_DATA = 0x00200000;

// --- server status flags ----------------------------------------------------
constexpr uint16_t SERVER_MORE_RESULTS_EXISTS = 0x0008;

constexpr uint8_t MYSQL_CHARSET_UTF8MB4 = 45; // utf8mb4_general_ci

uint32_t rd32(const std::string& p, size_t off) {
    if (off + 4 > p.size()) return 0;
    return static_cast<uint32_t>(static_cast<uint8_t>(p[off])) |
           (static_cast<uint32_t>(static_cast<uint8_t>(p[off + 1])) << 8) |
           (static_cast<uint32_t>(static_cast<uint8_t>(p[off + 2])) << 16) |
           (static_cast<uint32_t>(static_cast<uint8_t>(p[off + 3])) << 24);
}
uint16_t rd16(const std::string& p, size_t off) {
    if (off + 2 > p.size()) return 0;
    return static_cast<uint16_t>(static_cast<uint8_t>(p[off]) |
                                 (static_cast<uint16_t>(static_cast<uint8_t>(p[off + 1])) << 8));
}
void wr16(std::string& out, uint16_t v) {
    out.push_back(static_cast<char>(v & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
}
void wr32(std::string& out, uint32_t v) {
    out.push_back(static_cast<char>(v & 0xff));
    out.push_back(static_cast<char>((v >> 8) & 0xff));
    out.push_back(static_cast<char>((v >> 16) & 0xff));
    out.push_back(static_cast<char>((v >> 24) & 0xff));
}

/** 读取 length-encoded integer，返回读取长度（0 表示失败） */
size_t readLenencInt(const std::string& p, size_t off, uint64_t& out) {
    if (off >= p.size()) return 0;
    uint8_t first = static_cast<uint8_t>(p[off]);
    if (first < 0xfb) {
        out = first;
        return 1;
    }
    if (first == 0xfc) {
        if (off + 3 > p.size()) return 0;
        out = static_cast<uint64_t>(rd16(p, off + 1));
        return 3;
    }
    if (first == 0xfd) {
        if (off + 4 > p.size()) return 0;
        out = static_cast<uint64_t>(static_cast<uint8_t>(p[off + 1])) |
              (static_cast<uint64_t>(static_cast<uint8_t>(p[off + 2])) << 8) |
              (static_cast<uint64_t>(static_cast<uint8_t>(p[off + 3])) << 16);
        return 4;
    }
    if (first == 0xfe) {
        if (off + 9 > p.size()) return 0;
        out = static_cast<uint64_t>(rd32(p, off + 1)) |
              (static_cast<uint64_t>(rd32(p, off + 5)) << 32);
        return 9;
    }
    return 0; // 0xfb = NULL, 0xff = err
}

void writeLenencInt(std::string& out, uint64_t v) {
    if (v < 0xfb) {
        out.push_back(static_cast<char>(v));
    } else if (v <= 0xffff) {
        out.push_back(static_cast<char>(0xfc));
        wr16(out, static_cast<uint16_t>(v));
    } else if (v <= 0xffffff) {
        out.push_back(static_cast<char>(0xfd));
        out.push_back(static_cast<char>(v & 0xff));
        out.push_back(static_cast<char>((v >> 8) & 0xff));
        out.push_back(static_cast<char>((v >> 16) & 0xff));
    } else {
        out.push_back(static_cast<char>(0xfe));
        wr32(out, static_cast<uint32_t>(v & 0xffffffff));
        wr32(out, static_cast<uint32_t>((v >> 32) & 0xffffffff));
    }
}

void writeLenencStr(std::string& out, const std::string& s) {
    writeLenencInt(out, s.size());
    out += s;
}

std::string sha1(const std::string& in) { return cm::crypto::sha1(in); }
std::string sha256(const std::string& in) { return cm::crypto::sha256(in); }
std::string xorBytes(const std::string& a, const std::string& b) {
    std::string r = a;
    for (size_t i = 0; i < r.size() && i < b.size(); ++i) r[i] = static_cast<char>(r[i] ^ b[i]);
    return r;
}

/** mysql_native_password: SHA1(pwd) XOR SHA1(scramble + SHA1(SHA1(pwd))) */
std::string nativePassword(const std::string& password, const std::string& scramble) {
    if (password.empty()) return "";
    std::string s1 = sha1(password);
    std::string s2 = sha1(s1);
    std::string s3 = sha1(scramble + s2);
    return xorBytes(s1, s3);
}

/** caching_sha2_password: SHA256(pwd) XOR SHA256(SHA256(SHA256(pwd)) + scramble) */
std::string cachingSha2Password(const std::string& password, const std::string& scramble) {
    if (password.empty()) return "";
    std::string s1 = sha256(password);
    std::string s2 = sha256(s1);
    std::string s3 = sha256(s2 + scramble);
    return xorBytes(s1, s3);
}

/** RSA-OAEP(SHA1) 加密 (password XOR scramble)，输出 PEM 公钥可解密的密文 */
std::string rsaEncryptPassword(const std::string& password, const std::string& scramble,
                               const std::string& pem) {
    std::string plain = password;
    // 密码与 scramble 循环异或
    for (size_t i = 0; i < plain.size(); ++i) plain[i] = static_cast<char>(plain[i] ^ scramble[i % scramble.size()]);
    plain.push_back('\0');

    std::string err;
    std::string out;
    if (!cm::crypto::rsaOaepEncryptPem(pem, plain, out, &err)) {
        std::fprintf(stderr, "[mysql] RSA full-auth 失败: %s\n", err.c_str());
        return "";
    }
    return out;
}

std::string sqlState(const std::string& payload) {
    if (payload.size() >= 9 && payload[3] == '#') return payload.substr(4, 5);
    return "HY000";
}
std::string errMessage(const std::string& payload) {
    size_t off = (payload.size() >= 9 && payload[3] == '#') ? 9 : 3;
    return payload.substr(off);
}

} // namespace

MySqlConnection::~MySqlConnection() { close(); }

void MySqlConnection::setError(const std::string& msg, int err) {
    last_error_ = msg;
    last_errno_ = err;
}

bool MySqlConnection::connect(const DbConfig& cfg) {
    close();
    std::string err;
    cm::net::Fd fd = cm::net::connectTcp(cfg.host, cfg.port, cfg.connectTimeoutMs, &err);
    if (!cm::net::isValid(fd)) {
        setError(err.empty() ? "连接 MySQL 失败 " + cfg.host : err);
        return false;
    }
    fd_ = cm::net::toStorage(fd);
    // 连上之后切换到读写超时
    cm::net::setTimeout(fd, cfg.socketTimeoutMs);
    cm::net::setNoDelay(fd);

    if (!handshake(cfg)) {
        close();
        return false;
    }
    return true;
}

void MySqlConnection::close() {
    if (cm::net::validStorage(fd_)) {
        cm::net::closeTcp(cm::net::fromStorage(fd_));
        fd_ = cm::net::kInvalidStorage;
    }
    in_tx_ = false;
    seq_ = 0;
}

bool MySqlConnection::sendPacket(const std::string& payload) {
    // MySQL 包头 4 字节：3 字节长度 + 1 字节序号；超过 0xffffff 需要拆多包，
    // 且恰好等于 0xffffff 时必须再补一个 0 长度包（协议规定）
    size_t pos = 0;
    size_t chunk_count = 0;
    do {
        size_t chunk = payload.size() - pos;
        if (chunk > 0xffffff) chunk = 0xffffff;
        std::string header(4, '\0');
        header[0] = static_cast<char>(chunk & 0xff);
        header[1] = static_cast<char>((chunk >> 8) & 0xff);
        header[2] = static_cast<char>((chunk >> 16) & 0xff);
        header[3] = static_cast<char>(seq_++ & 0xff);
        const std::vector<cm::net::Chunk> parts{
            {header.data(), header.size()}, {payload.data() + pos, chunk}};
        std::string werr;
        if (!cm::net::writeChunks(handle(), parts, &werr)) {
            setError("发送 MySQL 数据包失败: " + werr);
            return false;
        }
        ++chunk_count;
        pos += chunk;
    } while (pos < payload.size());
    if ((payload.size() % 0xffffff) == 0) {
        // 长度是 0xffffff 的整数倍：补发一个空包表示结束
        std::string header(4, '\0');
        header[3] = static_cast<char>(seq_++ & 0xff);
        std::string werr;
        if (!cm::net::writeChunks(handle(), {{header.data(), header.size()}}, &werr)) {
            setError("发送 MySQL 结束包失败: " + werr);
            return false;
        }
    }
    (void)chunk_count;
    return true;
}

bool MySqlConnection::recvPacket(std::string& payload) {
    payload.clear();
    for (;;) {
        unsigned char header[4];
        size_t got = 0;
        while (got < 4) {
            const long r = cm::net::readSome(handle(), header + got, 4 - got);
            if (r <= 0) {
                setError("读取 MySQL 数据包头失败: " + cm::net::lastError());
                return false;
            }
            got += static_cast<size_t>(r);
        }
        size_t len = static_cast<size_t>(header[0]) | (static_cast<size_t>(header[1]) << 8) |
                     (static_cast<size_t>(header[2]) << 16);
        seq_ = static_cast<uint8_t>(header[3] + 1);
        if (len == 0) return true;
        size_t start = payload.size();
        payload.resize(start + len);
        got = 0;
        while (got < len) {
            const long r = cm::net::readSome(handle(), &payload[start + got], len - got);
            if (r <= 0) {
                setError("读取 MySQL 数据包失败: " + cm::net::lastError());
                return false;
            }
            got += static_cast<size_t>(r);
        }
        if (len < 0xffffff) break;
    }
    return true;
}

bool MySqlConnection::handshake(const DbConfig& cfg) {
    std::string pkt;
    if (!recvPacket(pkt)) return false;
    if (!pkt.empty() && static_cast<uint8_t>(pkt[0]) == 0xff) {
        int err = static_cast<int>(rd16(pkt, 1));
        setError(errMessage(pkt), err);
        return false;
    }
    if (pkt.size() < 1 + 1) {
        setError("非法的 MySQL 握手包");
        return false;
    }
    uint8_t protocol = static_cast<uint8_t>(pkt[0]);
    if (protocol != 10) {
        setError("不支持的 MySQL 协议版本: " + std::to_string(protocol));
        return false;
    }
    size_t off = 1;
    size_t z = pkt.find('\0', off);
    if (z == std::string::npos) z = pkt.size();
    std::string serverVersion = pkt.substr(off, z - off);
    (void)serverVersion;
    off = z + 1;
    if (off + 4 > pkt.size()) {
        setError("MySQL 握手包被截断");
        return false;
    }
    thread_id_ = rd32(pkt, off);
    off += 4;
    scramble_ = pkt.substr(off, 8);
    off += 8;
    off += 1; // filler
    uint16_t capLow = rd16(pkt, off);
    off += 2;
    uint8_t plugin = 0;
    if (off < pkt.size()) off += 1; // charset
    if (off + 2 <= pkt.size()) off += 2; // status
    uint32_t caps = capLow;
    if (off + 2 <= pkt.size()) caps |= (static_cast<uint32_t>(rd16(pkt, off)) << 16);
    off += 2;
    uint8_t scrambleLen = 0;
    if (off < pkt.size()) {
        scrambleLen = static_cast<uint8_t>(pkt[off]);
        off += 1;
    }
    off += 10; // reserved
    if (caps & CLIENT_SECURE_CONNECTION) {
        size_t part2Len = scrambleLen > 8 ? static_cast<size_t>(scrambleLen - 8) : 13;
        if (part2Len < 13 && caps & CLIENT_PLUGIN_AUTH) part2Len = 13;
        if (off + part2Len > pkt.size()) part2Len = pkt.size() - std::min(off, pkt.size());
        std::string part2 = pkt.substr(off, part2Len);
        while (!part2.empty() && part2.back() == '\0') part2.pop_back();
        scramble_ += part2;
        off += part2Len;
    }
    if (caps & CLIENT_PLUGIN_AUTH) {
        size_t end = pkt.find('\0', off);
        if (end == std::string::npos) end = pkt.size();
        std::string pluginName = pkt.substr(off, end - off);
        if (pluginName == "caching_sha2_password") plugin = 1;
        else if (pluginName == "mysql_native_password") plugin = 0;
        else plugin = 2;
        off = end + 1;
    }
    return authenticate(cfg, plugin, scramble_);
}

bool MySqlConnection::authenticate(const DbConfig& cfg, uint8_t plugin, const std::string& scramble) {
    uint32_t caps = CLIENT_LONG_PASSWORD | CLIENT_LONG_FLAG | CLIENT_PROTOCOL_41 | CLIENT_TRANSACTIONS |
                    CLIENT_SECURE_CONNECTION | CLIENT_MULTI_STATEMENTS | CLIENT_MULTI_RESULTS |
                    CLIENT_PLUGIN_AUTH | CLIENT_PLUGIN_AUTH_LENENC_CLIENT_DATA;
    if (!cfg.database.empty()) caps |= CLIENT_CONNECT_WITH_DB;

    std::string auth;
    const char* pluginName = "mysql_native_password";
    if (plugin == 1) {
        auth = cachingSha2Password(cfg.password, scramble);
        pluginName = "caching_sha2_password";
    } else if (plugin == 0) {
        auth = nativePassword(cfg.password, scramble);
        pluginName = "mysql_native_password";
    } else {
        setError("暂不支持的认证插件");
        return false;
    }

    std::string p;
    wr32(p, caps);
    wr32(p, 16 * 1024 * 1024); // max packet
    p.push_back(static_cast<char>(MYSQL_CHARSET_UTF8MB4));
    p.append(23, '\0');
    p += cfg.user;
    p.push_back('\0');
    writeLenencStr(p, auth);
    if (!cfg.database.empty()) {
        p += cfg.database;
        p.push_back('\0');
    }
    p += pluginName;
    p.push_back('\0');

    if (!sendPacket(p)) return false;

    for (; ;) {
        std::string rsp;
        if (!recvPacket(rsp)) return false;
        if (rsp.empty()) continue;
        uint8_t first = static_cast<uint8_t>(rsp[0]);
        if (first == 0x00) {
            return true; // OK
        }
        if (first == 0xff) {
            int err = static_cast<int>(rd16(rsp, 1));
            setError(errMessage(rsp) + " (sqlstate=" + sqlState(rsp) + ")", err);
            return false;
        }
        if (first == 0xfe) {
            // auth switch request
            size_t z = rsp.find('\0', 1);
            if (z == std::string::npos) {
                setError("非法 auth switch 包");
                return false;
            }
            std::string newPlugin = rsp.substr(1, z - 1);
            std::string newScramble = rsp.substr(z + 1);
            while (!newScramble.empty() && newScramble.back() == '\0') newScramble.pop_back();
            std::string resp;
            if (newPlugin == "caching_sha2_password") {
                resp = cachingSha2Password(cfg.password, newScramble);
                plugin = 1;
            } else {
                resp = nativePassword(cfg.password, newScramble);
                plugin = 0;
            }
            scramble_ = newScramble;
            if (!sendPacket(resp)) return false;
            continue;
        }
        if (first == 0x01) {
            // AuthMoreData
            if (rsp.size() >= 2 && static_cast<uint8_t>(rsp[1]) == 0x03) {
                continue; // fast auth success，紧接着 OK
            }
            if (rsp.size() >= 2 && static_cast<uint8_t>(rsp[1]) == 0x04) {
                // 需要完整认证：请求服务端公钥
                std::string req(1, '\x02');
                if (!sendPacket(req)) return false;
                std::string keyPkt;
                if (!recvPacket(keyPkt)) return false;
                if (keyPkt.empty() || static_cast<uint8_t>(keyPkt[0]) != 0x01) {
                    setError("获取 MySQL RSA 公钥失败");
                    return false;
                }
                std::string pem = keyPkt.substr(1);
                std::string enc = rsaEncryptPassword(cfg.password, scramble_, pem);
                if (enc.empty()) {
                    setError("RSA 加密密码失败");
                    return false;
                }
                if (!sendPacket(enc)) return false;
                continue;
            }
            setError("未知的 MySQL 认证响应");
            return false;
        }
        setError("未知的 MySQL 认证包: " + std::to_string(first));
        return false;
    }
}

bool MySqlConnection::readOkOrErr(std::string& payload, Result& out) {
    if (payload.empty()) {
        setError("MySQL 返回空数据包");
        return false;
    }
    uint8_t first = static_cast<uint8_t>(payload[0]);
    if (first == 0xff) {
        int err = static_cast<int>(rd16(payload, 1));
        setError(errMessage(payload), err);
        return false;
    }
    if (first == 0x00) {
        size_t off = 1;
        uint64_t affected = 0, insertId = 0;
        size_t n = readLenencInt(payload, off, affected);
        off += n;
        n = readLenencInt(payload, off, insertId);
        off += n;
        out.affectedRows = static_cast<long long>(affected);
        out.insertId = static_cast<long long>(insertId);
        uint16_t status = 0;
        if (off + 2 <= payload.size()) status = rd16(payload, off);
        off += 2;
        off += 2; // warnings
        if (off < payload.size()) out.info = payload.substr(off);
        last_errno_ = 0;
        return true;
    }
    return false;
}

bool MySqlConnection::readResult(Result& out, bool& more_results) {
    more_results = false;
    std::string pkt;
    if (!recvPacket(pkt)) return false;
    if (pkt.empty()) {
        setError("MySQL 返回空结果");
        return false;
    }
    uint8_t first = static_cast<uint8_t>(pkt[0]);
    if (first == 0xff) {
        int err = static_cast<int>(rd16(pkt, 1));
        setError(errMessage(pkt), err);
        return false;
    }
    if (first == 0x00) {
        if (!readOkOrErr(pkt, out)) return false;
        // OK 包可能包含 more_results
        if (pkt.size() >= 5) {
            size_t off = 1;
            uint64_t v;
            off += readLenencInt(pkt, off, v);
            off += readLenencInt(pkt, off, v);
            if (off + 2 <= pkt.size()) more_results = (rd16(pkt, off) & SERVER_MORE_RESULTS_EXISTS) != 0;
        }
        return true;
    }
    if (first == 0xfb) {
        // LOCAL INFILE 请求（不支持）
        setError("不支持 LOCAL INFILE");
        return false;
    }

    // 结果集：先读列数量
    uint64_t colCount = 0;
    size_t n = readLenencInt(pkt, 0, colCount);
    if (n == 0) {
        setError("非法的结果集列数");
        return false;
    }
    std::vector<std::string> cols;
    cols.reserve(static_cast<size_t>(colCount));
    for (uint64_t i = 0; i < colCount; ++i) {
        std::string colPkt;
        if (!recvPacket(colPkt)) return false;
        if (!colPkt.empty() && static_cast<uint8_t>(colPkt[0]) == 0xff) {
            setError(errMessage(colPkt), static_cast<int>(rd16(colPkt, 1)));
            return false;
        }
        // column definition 41: catalog, schema, table, org_table, name, org_name, ...
        size_t off = 0;
        std::string colName;
        for (int f = 0; f < 6; ++f) {
            uint64_t len = 0;
            size_t got = readLenencInt(colPkt, off, len);
            if (got == 0) break;
            off += got;
            if (off + len > colPkt.size()) len = colPkt.size() - off;
            if (f == 4) colName = colPkt.substr(off, static_cast<size_t>(len));
            off += static_cast<size_t>(len);
        }
        cols.push_back(colName);
    }
    // EOF 包（未启用 CLIENT_DEPRECATE_EOF 时存在）
    std::string eof;
    if (!recvPacket(eof)) return false;
    if (!eof.empty() && static_cast<uint8_t>(eof[0]) == 0xfe) {
        // EOF/OK
    } else if (!eof.empty() && static_cast<uint8_t>(eof[0]) == 0x00) {
        // 有些服务端直接返回 OK（DEPRECATE_EOF），此处已经消费完
    } else {
        setError("结果集列定义后缺少终止包");
        return false;
    }
    if (!(eof.empty()) && static_cast<uint8_t>(eof[0]) == 0xff) {
        setError(errMessage(eof), static_cast<int>(rd16(eof, 1)));
        return false;
    }

    out.rows.clear();
    for (;;) {
        std::string rowPkt;
        if (!recvPacket(rowPkt)) return false;
        if (rowPkt.empty()) continue;
        uint8_t b = static_cast<uint8_t>(rowPkt[0]);
        if (b == 0xfe && rowPkt.size() < 9) {
            // EOF
            if (rowPkt.size() >= 5) more_results = (rd16(rowPkt, 3) & SERVER_MORE_RESULTS_EXISTS) != 0;
            break;
        }
        if (b == 0xff) {
            setError(errMessage(rowPkt), static_cast<int>(rd16(rowPkt, 1)));
            return false;
        }
        std::vector<std::optional<std::string>> vals;
        vals.reserve(cols.size());
        size_t off = 0;
        bool ok = true;
        for (size_t c = 0; c < cols.size(); ++c) {
            if (off >= rowPkt.size()) {
                vals.emplace_back(std::nullopt);
                continue;
            }
            uint8_t v = static_cast<uint8_t>(rowPkt[off]);
            if (v == 0xfb) {
                vals.emplace_back(std::nullopt);
                off += 1;
            } else {
                uint64_t len = 0;
                size_t got = readLenencInt(rowPkt, off, len);
                if (got == 0) {
                    ok = false;
                    break;
                }
                off += got;
                if (off + len > rowPkt.size()) len = rowPkt.size() - off;
                vals.emplace_back(rowPkt.substr(off, static_cast<size_t>(len)));
                off += static_cast<size_t>(len);
            }
        }
        if (!ok) {
            setError("解析结果行失败");
            return false;
        }
        out.rows.emplace_back(cols, std::move(vals));
    }
    return true;
}

bool MySqlConnection::query(const std::string& sql, Result& out) {
    if (!cm::net::validStorage(fd_)) {
        setError("MySQL 连接未建立");
        return false;
    }
    out = Result{};
    seq_ = 0;
    std::string payload(1, '\x03'); // COM_QUERY
    payload += sql;
    if (!sendPacket(payload)) return false;

    Result current;
    bool more = false;
    if (!readResult(current, more)) return false;
    // 消费所有后续结果集（multi statements）
    while (more) {
        Result next;
        bool m2 = false;
        if (!readResult(next, m2)) return false;
        current = std::move(next);
        more = m2;
    }
    out = std::move(current);
    return true;
}

bool MySqlConnection::execute(const std::string& sql, long long* affected, long long* insertId) {
    Result r;
    if (!query(sql, r)) return false;
    if (affected) *affected = r.affectedRows;
    if (insertId) *insertId = r.insertId;
    return true;
}

bool MySqlConnection::begin() {
    Result r;
    if (!query("START TRANSACTION", r)) return false;
    in_tx_ = true;
    return true;
}
bool MySqlConnection::commit() {
    Result r;
    if (!query("COMMIT", r)) return false;
    in_tx_ = false;
    return true;
}
bool MySqlConnection::rollback() {
    Result r;
    if (!query("ROLLBACK", r)) return false;
    in_tx_ = false;
    return true;
}

bool MySqlConnection::ping() {
    if (!cm::net::validStorage(fd_)) return false;
    seq_ = 0;
    std::string payload(1, '\x0e'); // COM_PING
    if (!sendPacket(payload)) return false;
    std::string pkt;
    if (!recvPacket(pkt)) return false;
    if (!pkt.empty() && static_cast<uint8_t>(pkt[0]) == 0x00) return true;
    if (!pkt.empty() && static_cast<uint8_t>(pkt[0]) == 0xff) {
        setError(errMessage(pkt), static_cast<int>(rd16(pkt, 1)));
    }
    return false;
}

// ---------------------------------------------------------------------------
// ConnectionPool
// ---------------------------------------------------------------------------

ConnectionPool::ConnectionPool(DbConfig cfg, int initial, int minIdle, int maxActive, int maxWaitMs)
    : cfg_(std::move(cfg)), min_idle_(minIdle), max_active_(maxActive <= 0 ? 8 : maxActive),
      max_wait_ms_(maxWaitMs <= 0 ? 60000 : maxWaitMs) {
    if (min_idle_ > max_active_) min_idle_ = max_active_;
    int want = std::max(initial, min_idle_);
    for (int i = 0; i < want; ++i) {
        auto c = create();
        if (c) idle_.push_back(std::move(c));
    }
}

ConnectionPool::~ConnectionPool() {
    closed_.store(true);
    cv_.notify_all();
    std::lock_guard<std::mutex> lk(mu_);
    for (auto& c : idle_) {
        if (c) c->close();
    }
    idle_.clear();
}

std::shared_ptr<MySqlConnection> ConnectionPool::create() {
    auto c = std::make_shared<MySqlConnection>();
    if (!c->connect(cfg_)) return nullptr;
    total_.fetch_add(1);
    return c;
}

void ConnectionPool::destroy(std::shared_ptr<MySqlConnection> conn) {
    if (conn) conn->close();
    total_.fetch_sub(1);
}

std::shared_ptr<MySqlConnection> ConnectionPool::borrow(int timeoutMs) {
    if (timeoutMs < 0) timeoutMs = max_wait_ms_;
    std::unique_lock<std::mutex> lk(mu_);
    auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeoutMs);
    for (;;) {
        if (closed_.load()) return nullptr;
        while (!idle_.empty()) {
            auto c = idle_.back();
            idle_.pop_back();
            if (c && c->isOpen() && c->ping()) {
                active_.fetch_add(1);
                return c;
            }
            // 失效连接：销毁后继续尝试
            if (c) {
                destroy(c);
            }
        }
        if (total_.load() < max_active_) {
            auto c = create();
            if (c) {
                active_.fetch_add(1);
                return c;
            }
            // 创建失败：如果已有连接可用则重试，否则失败
            if (total_.load() > 0) {
                if (cv_.wait_until(lk, deadline) == std::cv_status::timeout) return nullptr;
                continue;
            }
            return nullptr;
        }
        if (cv_.wait_until(lk, deadline) == std::cv_status::timeout) {
            return nullptr;
        }
    }
}

void ConnectionPool::release(std::shared_ptr<MySqlConnection> conn) {
    if (!conn) return;
    if (conn->inTransaction()) conn->rollback();
    std::lock_guard<std::mutex> lk(mu_);
    active_.fetch_sub(1);
    if (closed_.load() || !conn->isOpen()) {
        if (conn) destroy(conn);
        cv_.notify_one();
        return;
    }
    idle_.push_back(std::move(conn));
    cv_.notify_one();
}

bool ConnectionPool::query(const std::string& sql, Result& out) {
    auto c = borrow();
    if (!c) {
        out = Result{};
        return false;
    }
    bool ok = c->query(sql, out);
    release(c);
    return ok;
}

bool ConnectionPool::execute(const std::string& sql, long long* affected, long long* insertId) {
    auto c = borrow();
    if (!c) return false;
    bool ok = c->execute(sql, affected, insertId);
    release(c);
    return ok;
}

bool ConnectionPool::pingAll() {
    std::lock_guard<std::mutex> lk(mu_);
    if (total_.load() <= 0) return false;
    bool all = true;
    for (auto& c : idle_) {
        if (c && !c->ping()) all = false;
    }
    return all;
}

int ConnectionPool::idleCount() const {
    std::lock_guard<std::mutex> lk(mu_);
    return static_cast<int>(idle_.size());
}

} // namespace cm::db
