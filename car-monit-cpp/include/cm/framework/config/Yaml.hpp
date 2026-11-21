#pragma once
// 极简 YAML 子集解析器（对应 Spring Boot 的 application.yml 使用范围）
//
// 支持：缩进映射、`- ` 序列、内联数组 [a, b]、内联映射 {k: v}、单/双引号、行内注释、空文档。
// 不支持：锚点/别名（& / *）、多文档（--- / ...）、块标量（| / >）、Tab 缩进。
//
// ⚠️ 不支持的语法**不会静默当成普通值**：parse() 会通过 warnings 出参逐条报告
//    （含行号），AppConfig::load 会把它打出来。这样配置写复杂了能立刻发现，
//    而不是"读到了缺省值却以为生效了"。
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace cm::yaml {

struct Node {
    enum class Type { Null, Scalar, Map, Seq };
    Type type{Type::Null};
    std::string scalar;
    std::map<std::string, Node> map;
    std::vector<Node> seq;

    bool isNull() const { return type == Type::Null; }
    bool isMap() const { return type == Type::Map; }
    bool isSeq() const { return type == Type::Seq; }
    bool isScalar() const { return type == Type::Scalar; }

    std::string asString(const std::string& def = "") const {
        if (type == Type::Scalar) return scalar;
        return def;
    }
    long long asInt(long long def = 0) const {
        if (type != Type::Scalar) return def;
        try { return std::stoll(scalar); } catch (...) { return def; }
    }
    bool asBool(bool def = false) const {
        if (type != Type::Scalar) return def;
        std::string v;
        for (char c : scalar) v.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        if (v == "true" || v == "yes" || v == "on" || v == "1") return true;
        if (v == "false" || v == "no" || v == "off" || v == "0") return false;
        return def;
    }

    /** 以 a.b.c 路径读取（不存在返回 nullptr） */
    const Node* find(const std::string& path) const {
        const Node* cur = this;
        size_t start = 0;
        while (start <= path.size()) {
            size_t dot = path.find('.', start);
            std::string key = path.substr(start, dot == std::string::npos ? std::string::npos : dot - start);
            if (!cur->isMap()) return nullptr;
            auto it = cur->map.find(key);
            if (it == cur->map.end()) return nullptr;
            cur = &it->second;
            if (dot == std::string::npos) break;
            start = dot + 1;
        }
        return cur;
    }

    std::string getString(const std::string& path, const std::string& def = "") const {
        const Node* n = find(path);
        return n ? n->asString(def) : def;
    }
    long long getInt(const std::string& path, long long def = 0) const {
        const Node* n = find(path);
        return n ? n->asInt(def) : def;
    }
    bool getBool(const std::string& path, bool def = false) const {
        const Node* n = find(path);
        return n ? n->asBool(def) : def;
    }
};

/** 解析文本；warnings 非空时收集"遇到了不支持的语法"的说明（含行号） */
Node parse(const std::string& text, std::vector<std::string>* warnings = nullptr);
Node parseFile(const std::string& path, std::vector<std::string>* warnings = nullptr);

} // namespace cm::yaml
