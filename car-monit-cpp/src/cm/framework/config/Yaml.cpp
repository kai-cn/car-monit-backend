#include "cm/framework/config/Yaml.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <sstream>

namespace cm::yaml {

namespace {

struct Line {
    int indent{0};
    std::string text;
};

std::string rtrim(const std::string& s) {
    size_t e = s.size();
    while (e > 0 && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
    return s.substr(0, e);
}

std::string stripComment(const std::string& s) {
    bool in_single = false, in_double = false;
    for (size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == '\'' && !in_double) in_single = !in_single;
        else if (c == '"' && !in_single) in_double = !in_double;
        else if (c == '#' && !in_single && !in_double) {
            if (i == 0 || std::isspace(static_cast<unsigned char>(s[i - 1]))) return rtrim(s.substr(0, i));
        }
    }
    return rtrim(s);
}

std::string unquote(const std::string& v) {
    if (v.size() >= 2 && v.front() == '"' && v.back() == '"') {
        std::string out;
        for (size_t i = 1; i + 1 < v.size(); ++i) {
            if (v[i] == '\\' && i + 2 < v.size()) {
                char n = v[i + 1];
                if (n == 'n') out.push_back('\n');
                else if (n == 't') out.push_back('\t');
                else out.push_back(n);
                ++i;
            } else {
                out.push_back(v[i]);
            }
        }
        return out;
    }
    if (v.size() >= 2 && v.front() == '\'' && v.back() == '\'') {
        return v.substr(1, v.size() - 2);
    }
    return v;
}

std::vector<std::string> splitInline(const std::string& body) {
    std::vector<std::string> out;
    std::string cur;
    bool in_single = false, in_double = false;
    for (char c : body) {
        if (c == '\'' && !in_double) in_single = !in_single;
        else if (c == '"' && !in_single) in_double = !in_double;
        if (c == ',' && !in_single && !in_double) {
            out.push_back(cur);
            cur.clear();
        } else {
            cur.push_back(c);
        }
    }
    if (!cur.empty() || !out.empty()) out.push_back(cur);
    for (auto& s : out) {
        size_t b = 0, e = s.size();
        while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
        while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
        s = unquote(s.substr(b, e - b));
    }
    return out;
}

Node parseScalarOrInline(const std::string& raw) {
    std::string v = raw;
    // trim
    size_t b = 0, e = v.size();
    while (b < e && std::isspace(static_cast<unsigned char>(v[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(v[e - 1]))) --e;
    v = v.substr(b, e - b);

    Node n;
    if (v.empty()) return n;
    if (v.front() == '[' && v.back() == ']') {
        n.type = Node::Type::Seq;
        for (const auto& item : splitInline(v.substr(1, v.size() - 2))) {
            if (item.empty()) continue;
            Node c;
            c.type = Node::Type::Scalar;
            c.scalar = unquote(item);
            n.seq.push_back(std::move(c));
        }
        return n;
    }
    if (v.front() == '{' && v.back() == '}') {
        n.type = Node::Type::Map;
        for (const auto& item : splitInline(v.substr(1, v.size() - 2))) {
            auto colon = item.find(':');
            if (colon == std::string::npos) continue;
            n.map[unquote(item.substr(0, colon))] = parseScalarOrInline(item.substr(colon + 1));
        }
        return n;
    }
    n.type = Node::Type::Scalar;
    n.scalar = unquote(v);
    return n;
}

bool isSeqLine(const std::string& t) { return t == "-" || (t.size() > 1 && t[0] == '-' && t[1] == ' '); }

struct Parser {
    std::vector<Line> lines;

    Node parseBlock(size_t& i, int indent) {
        if (i >= lines.size()) return Node{};
        if (isSeqLine(lines[i].text)) return parseSeq(i, indent);
        return parseMap(i, indent);
    }

    Node parseMap(size_t& i, int indent) {
        Node node;
        node.type = Node::Type::Map;
        while (i < lines.size() && lines[i].indent == indent && !isSeqLine(lines[i].text)) {
            std::string line = lines[i].text;
            auto colon = findKeyColon(line);
            if (colon == std::string::npos) { ++i; continue; }
            std::string key = unquote(line.substr(0, colon));
            std::string rest = line.substr(colon + 1);
            ++i;
            if (rest.empty()) {
                if (i < lines.size() && lines[i].indent > indent) {
                    node.map[key] = parseBlock(i, lines[i].indent);
                } else {
                    node.map[key] = Node{};
                }
            } else {
                node.map[key] = parseScalarOrInline(rest);
            }
        }
        return node;
    }

    Node parseSeq(size_t& i, int indent) {
        Node node;
        node.type = Node::Type::Seq;
        while (i < lines.size() && lines[i].indent == indent && isSeqLine(lines[i].text)) {
            std::string rest = lines[i].text.substr(1);
            // trim leading spaces
            while (!rest.empty() && rest.front() == ' ') rest.erase(rest.begin());
            int item_indent = indent + 2;
            ++i;
            if (rest.empty()) {
                if (i < lines.size() && lines[i].indent > indent) {
                    node.seq.push_back(parseBlock(i, lines[i].indent));
                } else {
                    node.seq.push_back(Node{});
                }
                continue;
            }
            auto colon = findKeyColon(rest);
            if (colon != std::string::npos) {
                // 序列里的映射项
                Node item;
                item.type = Node::Type::Map;
                std::string key = unquote(rest.substr(0, colon));
                std::string value = rest.substr(colon + 1);
                if (value.empty()) {
                    if (i < lines.size() && lines[i].indent > indent) item.map[key] = parseBlock(i, lines[i].indent);
                    else item.map[key] = Node{};
                } else {
                    item.map[key] = parseScalarOrInline(value);
                }
                // 后续同级映射字段
                while (i < lines.size() && lines[i].indent >= item_indent && !isSeqLine(lines[i].text)) {
                    if (lines[i].indent > item_indent) break;
                    std::string l = lines[i].text;
                    auto c2 = findKeyColon(l);
                    if (c2 == std::string::npos) { ++i; continue; }
                    std::string k2 = unquote(l.substr(0, c2));
                    std::string v2 = l.substr(c2 + 1);
                    ++i;
                    if (v2.empty()) {
                        if (i < lines.size() && lines[i].indent > item_indent) item.map[k2] = parseBlock(i, lines[i].indent);
                        else item.map[k2] = Node{};
                    } else {
                        item.map[k2] = parseScalarOrInline(v2);
                    }
                }
                node.seq.push_back(std::move(item));
            } else {
                node.seq.push_back(parseScalarOrInline(rest));
            }
        }
        return node;
    }

    static size_t findKeyColon(const std::string& s) {
        bool in_single = false, in_double = false;
        for (size_t i = 0; i < s.size(); ++i) {
            char c = s[i];
            if (c == '\'' && !in_double) in_single = !in_single;
            else if (c == '"' && !in_single) in_double = !in_double;
            else if (c == ':' && !in_single && !in_double) {
                if (i + 1 == s.size() || s[i + 1] == ' ' || s[i + 1] == '\t') return i;
            }
        }
        return std::string::npos;
    }
};

} // namespace

Node parse(const std::string& text) {
    Parser p;
    std::istringstream is(text);
    std::string raw;
    bool first = true;
    while (std::getline(is, raw)) {
        if (first) {
            if (raw.size() >= 3 && static_cast<unsigned char>(raw[0]) == 0xEF &&
                static_cast<unsigned char>(raw[1]) == 0xBB && static_cast<unsigned char>(raw[2]) == 0xBF) {
                raw = raw.substr(3);
            }
            first = false;
        }
        if (!raw.empty() && raw.back() == '\r') raw.pop_back();
        std::string no_comment = stripComment(raw);
        if (no_comment.empty()) continue;
        int indent = 0;
        for (char c : no_comment) {
            if (c == ' ') ++indent;
            else if (c == '\t') indent += 2;
            else break;
        }
        std::string text_part = no_comment.substr(no_comment.find_first_not_of(" \t"));
        p.lines.push_back({indent, text_part});
    }
    if (p.lines.empty()) return Node{};
    size_t i = 0;
    return p.parseBlock(i, p.lines[0].indent);
}

Node parseFile(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return Node{};
    std::ostringstream os;
    os << in.rdbuf();
    return parse(os.str());
}

} // namespace cm::yaml
